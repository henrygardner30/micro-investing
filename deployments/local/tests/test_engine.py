"""
Unit tests for the shared investment engine (core/engine.py).

build_plan and execute_plan are exercised with in-memory fakes - no network, no
files, no credentials. The scheduled strategy is used as the driver for
build_plan because it needs no CSV; an in-memory state store keeps it off disk.
"""

from engine import build_plan, execute_plan, InvestmentPlan, StrategyContribution


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #

class MemStorage:
    """In-memory stand-in for the scheduled strategy's state storage backend."""

    def __init__(self):
        self.data = {}

    def load(self):
        return dict(self.data)

    def save(self, state):
        self.data = dict(state)


class FakeTrader:
    """Minimal broker double recording the orders it is asked to place."""

    def __init__(self, buying_power, fail_symbols=()):
        self._buying_power = buying_power
        self.fail_symbols = set(fail_symbols)
        self.orders = []

    def get_buying_power(self):
        return self._buying_power

    def place_fractional_order(self, symbol, notional, dry_run=False):
        if symbol in self.fail_symbols:
            return None
        order = {"symbol": symbol, "notional": notional, "status": "filled"}
        self.orders.append(order)
        return order


class SpyStrategy:
    """Records commit_run() calls so we can assert when runs are committed."""

    def __init__(self):
        self.committed = []

    def commit_run(self, config):
        self.committed.append(config)


def _sched(name, amount=5.0, allocation=None, **extra):
    """Build a valid daily scheduled-strategy config, with optional overrides."""
    config = {
        "name": name,
        "type": "scheduled",
        "amount": amount,
        "interval": "daily",
        "allocation": allocation or {"VOO": 1.0},
    }
    config.update(extra)
    return config


# --------------------------------------------------------------------------- #
# build_plan
# --------------------------------------------------------------------------- #

def test_build_plan_combines_allocations_across_strategies():
    """Two enabled strategies sum into one total and a merged allocation map."""
    plan = build_plan(
        [_sched("a", amount=5.0, allocation={"VOO": 1.0}),
         _sched("b", amount=5.0, allocation={"QQQ": 1.0})],
        state_storage=MemStorage(),
    )
    assert plan.total_investable == 10.0
    assert plan.combined_allocation == {"VOO": 5.0, "QQQ": 5.0}
    assert plan.executed_names == ["a", "b"]


def test_build_plan_skips_disabled_strategy():
    """A strategy with enabled=False contributes nothing."""
    plan = build_plan([_sched("a", enabled=False)], state_storage=MemStorage())
    assert plan.total_investable == 0.0
    assert plan.contributions == []


def test_build_plan_skips_unknown_type():
    """An unregistered strategy type is skipped rather than raising."""
    plan = build_plan(
        [{"name": "x", "type": "does_not_exist", "enabled": True}],
        state_storage=MemStorage(),
    )
    assert plan.total_investable == 0.0


def test_build_plan_applies_minimum():
    """An amount below min_daily_investment is dropped from the plan."""
    plan = build_plan(
        [_sched("a", amount=5.0, min_daily_investment=10.0)],
        state_storage=MemStorage(),
    )
    assert plan.total_investable == 0.0
    assert plan.contributions == []


def test_build_plan_caps_at_maximum():
    """An amount above max_daily_investment is capped to the maximum."""
    plan = build_plan(
        [_sched("a", amount=5.0, max_daily_investment=3.0, allocation={"VOO": 1.0})],
        state_storage=MemStorage(),
    )
    assert plan.total_investable == 3.0
    assert plan.combined_allocation == {"VOO": 3.0}


def test_build_plan_skips_invalid_config():
    """A config that fails validate_config (allocation != 1.0) is skipped."""
    plan = build_plan(
        [_sched("a", allocation={"VOO": 0.5})],
        state_storage=MemStorage(),
    )
    assert plan.total_investable == 0.0
    assert plan.contributions == []


def test_build_plan_round_up_from_csv(tmp_path):
    """A round_up strategy is routed through the CSV path and totals spare change."""
    csv_file = tmp_path / "transactions.csv"
    csv_file.write_text("date,amount\n2026-01-01,4.25\n2026-01-02,10.10\n")

    plan = build_plan(
        [{
            "name": "spare_change",
            "type": "round_up",
            "enabled": True,
            "csv_file": str(csv_file),
            "allocation": {"VOO": 1.0},
        }],
    )

    # 0.75 (4.25 -> 5) + 0.90 (10.10 -> 11) = 1.65
    assert round(plan.total_investable, 2) == 1.65
    assert round(plan.combined_allocation["VOO"], 2) == 1.65


# --------------------------------------------------------------------------- #
# execute_plan
# --------------------------------------------------------------------------- #

def _plan_with_spy():
    """Return (plan, spy) for a $5 plan split across two symbols."""
    spy = SpyStrategy()
    plan = InvestmentPlan(
        total_investable=5.0,
        combined_allocation={"VOO": 3.0, "QQQ": 2.0},
        contributions=[StrategyContribution(
            name="s", type="scheduled", investable=5.0,
            allocation={"VOO": 3.0, "QQQ": 2.0}, instance=spy, config={"name": "s"},
        )],
    )
    return plan, spy


def test_execute_insufficient_funds_places_no_orders():
    """When buying power < total, returns insufficient_funds and trades nothing."""
    plan, spy = _plan_with_spy()
    trader = FakeTrader(buying_power=1.0)

    result = execute_plan(plan, trader, simulate=False)

    assert result.status == "insufficient_funds"
    assert result.shortfall == 4.0
    assert trader.orders == []
    assert spy.committed == []


def test_execute_simulate_places_no_orders_and_does_not_commit():
    """Simulate mode reports success but neither trades nor commits runs."""
    plan, spy = _plan_with_spy()
    trader = FakeTrader(buying_power=100.0)

    result = execute_plan(plan, trader, simulate=True)

    assert result.status == "success"
    assert result.simulated is True
    assert trader.orders == []
    assert spy.committed == []


def test_execute_real_places_orders_and_commits():
    """Real mode with sufficient funds places orders and commits each run."""
    plan, spy = _plan_with_spy()
    trader = FakeTrader(buying_power=100.0)

    result = execute_plan(plan, trader, simulate=False)

    assert result.status == "success"
    assert {o["symbol"] for o in trader.orders} == {"VOO", "QQQ"}
    assert len(result.orders) == 2
    assert spy.committed == [{"name": "s"}]
