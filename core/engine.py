"""
Investment Engine

Shared, deployment-agnostic orchestration for running investment strategies.

Both the local CLI and the AWS Lambda handler call into this module so the core
logic - validating strategies, computing investable amounts, applying min/max
limits, combining allocations, checking funds, placing orders, and recording
stateful runs - lives in exactly one place.

Deployment-specific concerns (credential loading, ledger writing, email/SNS
notifications, HTTP response shaping) stay in the caller. The engine performs no
I/O beyond what the injected `trader`/`calculator`/strategies already do.

Two phases:
  build_plan(...)   -> InvestmentPlan   (decide what to invest, no trading)
  execute_plan(...) -> ExecutionResult  (check funds, place orders, commit runs)
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from strategies import STRATEGY_REGISTRY


@dataclass
class StrategyContribution:
    """One enabled strategy that produced a positive investable amount."""
    name: str
    type: str
    investable: float
    allocation: Dict[str, float]
    instance: object   # the BaseStrategy instance (kept for commit_run)
    config: Dict


@dataclass
class InvestmentPlan:
    """The combined result of running every enabled strategy for this run."""
    total_investable: float = 0.0
    combined_allocation: Dict[str, float] = field(default_factory=dict)
    contributions: List[StrategyContribution] = field(default_factory=list)

    @property
    def executed_names(self) -> List[str]:
        """Names of the strategies that contributed to this plan."""
        return [c.name for c in self.contributions]


@dataclass
class ExecutionResult:
    """The outcome of attempting to execute an InvestmentPlan."""
    status: str                       # 'success' | 'insufficient_funds'
    buying_power: float
    simulated: bool
    shortfall: float = 0.0
    orders: List[dict] = field(default_factory=list)


def _instantiate_strategy(strategy_type, strategy_class, state_storage):
    """
    Construct a strategy, injecting persistent state storage where the strategy
    supports it (currently only the scheduled strategy). Centralizes the one
    place this conditional needs to exist.

    @PARAMS:
        - strategy_type  -> registry key (e.g. 'scheduled')
        - strategy_class -> the BaseStrategy subclass from STRATEGY_REGISTRY
        - state_storage  -> optional storage backend for stateful strategies
    """
    if strategy_type == 'scheduled' and state_storage is not None:
        return strategy_class(state_storage=state_storage)
    return strategy_class()


def _calculate_investable(strategy, strategy_type, config, calculator, csv_default):
    """
    Compute the investable amount for a single strategy, routing transaction
    (CSV) strategies through calculate_investable_from_csv and config-driven
    strategies through calculate_investable_amount.

    Returns the dollar amount (0.0 if it cannot be computed).

    @PARAMS:
        - strategy      -> the strategy instance
        - strategy_type -> registry key
        - config        -> this strategy's config dict
        - calculator    -> reward calculator for credit_card_rewards (or None)
        - csv_default   -> fallback transactions CSV path when config omits one
    """
    if strategy_type == 'credit_card_rewards':
        if calculator is None:
            print(f"[{config.get('name', strategy_type)}] Skipping - credit_card_rewards "
                  f"requires a Card Caddie API key (THECARDCADDIE_API_KEY)")
            return 0.0
        csv_path = config.get('csv_file', csv_default)
        if not csv_path:
            print(f"[{config.get('name', strategy_type)}] Skipping - no 'csv_file' configured")
            return 0.0
        amount, _ = strategy.calculate_investable_from_csv(csv_path, calculator)
        return amount

    if strategy_type == 'round_up':
        csv_path = config.get('csv_file', csv_default)
        if not csv_path:
            print(f"[{config.get('name', strategy_type)}] Skipping - no 'csv_file' configured")
            return 0.0
        amount, _ = strategy.calculate_investable_from_csv(csv_path)
        return amount

    # scheduled and any custom config-driven strategies
    amount, _ = strategy.calculate_investable_amount(config)
    return amount


def build_plan(
    strategies_config: List[Dict],
    *,
    calculator=None,
    state_storage=None,
    csv_default: Optional[str] = None,
) -> InvestmentPlan:
    """
    Run every enabled strategy and combine their output into one InvestmentPlan.

    For each strategy: skip if disabled or of unknown type, validate its config,
    compute the investable amount, apply min/max daily limits, and (if positive)
    fold its allocation into the combined plan.

    @PARAMS:
        - strategies_config -> list of per-strategy config dicts
        - calculator        -> reward calculator for credit_card_rewards (or None)
        - state_storage     -> persistent state backend for stateful strategies
        - csv_default       -> fallback transactions CSV path for CSV strategies
    """
    plan = InvestmentPlan()
    combined: Dict[str, float] = defaultdict(float)

    for config in strategies_config:
        name = config.get('name', 'Unnamed Strategy')
        strategy_type = config.get('type')

        if not config.get('enabled', True):
            print(f"Skipping disabled strategy: {name}")
            continue

        if strategy_type not in STRATEGY_REGISTRY:
            print(f"Error: Unknown strategy type '{strategy_type}' for strategy '{name}'")
            continue

        strategy = _instantiate_strategy(strategy_type, STRATEGY_REGISTRY[strategy_type], state_storage)

        print(f"\n[{name}] Processing strategy: {strategy_type}")

        if not strategy.validate_config(config):
            print(f"Error: Configuration for strategy '{name}' is invalid. Skipping.")
            continue

        investable = _calculate_investable(strategy, strategy_type, config, calculator, csv_default)

        # apply per-strategy daily limits
        min_investment = config.get('min_daily_investment', 0.0)
        max_investment = config.get('max_daily_investment', float('inf'))

        if investable < min_investment:
            print(f"[{name}] Amount ${investable:.2f} below minimum (${min_investment:.2f}). Skipping.")
            continue

        if investable > max_investment:
            print(f"[{name}] Amount exceeds maximum (${max_investment:.2f}). Capping at max.")
            investable = max_investment

        if investable > 0:
            allocation = strategy.calculate_allocation(investable, config)
            plan.total_investable += investable
            for symbol, amount in allocation.items():
                combined[symbol] += amount
            plan.contributions.append(StrategyContribution(
                name=name,
                type=strategy_type,
                investable=investable,
                allocation=allocation,
                instance=strategy,
                config=config,
            ))
            print(f"[{name}] Investable amount: ${investable:.4f}")
            print(f"[{name}] Allocation: " + ", ".join(f"{s}: ${a:.2f}" for s, a in allocation.items()))
        else:
            print(f"[{name}] No investable amount for this run.")

    plan.combined_allocation = dict(combined)
    return plan


def execute_plan(plan: InvestmentPlan, trader, *, simulate: bool = False) -> ExecutionResult:
    """
    Attempt to execute an InvestmentPlan against the broker.

    Always checks buying power first. If funds are short, returns an
    'insufficient_funds' result without trading. Otherwise, in real mode, places
    a fractional order per symbol and then commits each contributing strategy's
    run (so stateful strategies advance only on a real execution). In simulate
    mode no orders are placed and nothing is committed.

    @PARAMS:
        - plan     -> the InvestmentPlan to execute
        - trader   -> broker client exposing get_buying_power() and
                      place_fractional_order(symbol, notional, dry_run)
        - simulate -> if True, do not place orders or commit runs
    """
    buying_power = trader.get_buying_power()

    if buying_power < plan.total_investable:
        return ExecutionResult(
            status='insufficient_funds',
            buying_power=buying_power,
            simulated=simulate,
            shortfall=plan.total_investable - buying_power,
        )

    orders: List[dict] = []
    if not simulate:
        for symbol, amount in plan.combined_allocation.items():
            result = trader.place_fractional_order(symbol, amount, dry_run=False)
            if result:
                orders.append(result)

        # record the run for any stateful strategies now that trades executed
        for contribution in plan.contributions:
            contribution.instance.commit_run(contribution.config)

    return ExecutionResult(
        status='success',
        buying_power=buying_power,
        simulated=simulate,
        orders=orders,
    )
