"""
Scheduled Investment Strategy

Invests a fixed amount on a regular schedule (daily, weekly, monthly).
No transaction data needed, perfect for dollar-cost averaging.
Uses JSON state file to track last run time per strategy.
"""

from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
from .base import BaseStrategy

# Define valid intervals
VALID_INTERVALS = ['daily', 'weekly', 'biweekly', 'monthly']

class ScheduledStrategy(BaseStrategy):
    """
    Strategy that invests a fixed amount on a regular schedule.
    
    Perfect for:
    - Dollar-cost averaging
    - Simple recurring investments
    - No transaction tracking needed
    
    Uses state storage (file or S3) to track when each strategy last ran.
    """
    
    def __init__(self, state_storage=None, state_file: str = None):
        super().__init__("scheduled")
        
        # Use custom storage if provided, otherwise default to file-based
        if state_storage is not None:
            self.storage = state_storage
        else:
            # Default: file-based storage for local deployment.
            # storage must be set to None BEFORE _ensure_state_file(), which
            # calls _save_state() and branches on self.storage.
            if state_file is None:
                state_file = "data/state/scheduled_state.json"
            self.storage = None  # Use file-based methods
            self.state_file = Path(state_file)
            self._ensure_state_file()
    
    def supports_transactions(self) -> bool:
        """
        Scheduled strategy does not process transactions.
        """
        return False
    
    def _ensure_state_file(self):
        """
        Function to ensure state file and directory exist.
        Creates empty state if file doesn't exist.
        """
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_file.exists():
            self._save_state({})
    
    def _load_state(self) -> Dict:
        """
        Function to load state from storage (file or S3).
        Returns dictionary of strategy_name -> last_run_timestamp.
        """
        if self.storage:
            # Use custom storage (e.g., S3 for Lambda)
            return self.storage.load()
        else:
            # Use file-based storage (local deployment)
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
    
    def _save_state(self, state: Dict):
        """
        Function to save state to storage (file or S3).
        
        @PARAMS:
            - state -> Dictionary of strategy_name -> last_run_timestamp
        """
        if self.storage:
            # Use custom storage (e.g., S3 for Lambda)
            self.storage.save(state)
        else:
            # Use file-based storage (local deployment)
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

    def _should_invest(self, strategy_name: str, interval: str) -> bool:
        """
        Function to determine if an investment should occur based on the interval and last run time.
        Checks JSON state to see if enough time has passed since last run.
        
        @PARAMS:
            - strategy_name -> The unique name of the scheduled strategy
            - interval -> The configured interval (daily, weekly, biweekly, monthly)
        """
        state = self._load_state()
        last_run_str = state.get(strategy_name)
        
        # First run for this strategy
        if not last_run_str:
            return True
        
        try:
            last_run = datetime.fromisoformat(last_run_str)
            now = datetime.now()
            days_since_last = (now - last_run).days
            
            # Check if enough time has passed based on interval
            if interval == 'daily':
                return days_since_last >= 1
            elif interval == 'weekly':
                return days_since_last >= 7
            elif interval == 'biweekly':
                return days_since_last >= 14
            elif interval == 'monthly':
                # Check if we're in a different month
                return (now.year > last_run.year) or (now.year == last_run.year and now.month > last_run.month)
            else:
                return False
        except (ValueError, TypeError):
            # Invalid timestamp, treat as first run
            return True

    def _mark_run(self, strategy_name: str):
        """
        Function to mark that a strategy has run by updating state with current timestamp.
        
        @PARAMS:
            - strategy_name -> The unique name of the scheduled strategy
        """
        state = self._load_state()
        state[strategy_name] = datetime.now().isoformat()
        self._save_state(state)

    def calculate_allocation(self, amount: float, config: Dict) -> Dict[str, float]:
        """
        Function to split investment amount proportionally across stock symbols.
        Returns a dictionary mapping each stock symbol to its dollar amount.
        
        @PARAMS:
            - amount -> total dollar amount to invest
            - config -> configuration dict containing 'allocation' with symbol: weight pairs
        """
        allocation = config.get('allocation', {})
        allocation_amounts = {}
        
        for symbol, weight in allocation.items():
            allocation_amounts[symbol] = amount * weight
        
        return allocation_amounts
    
    def validate_config(self, config: Dict) -> bool:
        """
        Function to validate that allocation percentages sum to 1.0 and config is valid.
        Returns true if valid configuration, false if errors found.
        
        @PARAMS:
            - config -> configuration dictionary that must contain 'allocation' dict
        """
        if 'name' not in config or not isinstance(config['name'], str) or not config['name']:
            print("Error: Scheduled strategy requires a 'name' field.")
            return False
        if 'amount' not in config or not isinstance(config['amount'], (int, float)) or config['amount'] <= 0:
            print(f"Error: Strategy '{self.name}' requires a positive 'amount' for scheduled investments.")
            return False
        if 'interval' not in config or config['interval'] not in VALID_INTERVALS:
            print(f"Error: Strategy '{self.name}' requires a valid 'interval'. Options: {', '.join(VALID_INTERVALS)}")
            return False
        
        allocation = config.get('allocation', {})
        if not allocation:
            print("Error: No allocation defined in config")
            return False
        
        total = sum(allocation.values())
        if abs(total - 1.0) > 0.01:
            print(f"Error: Allocation must sum to 1.0 (got {total:.2f})")
            return False
        
        return True

    def commit_run(self, config: Dict) -> None:
        """
        Record that this scheduled strategy executed, advancing the interval gate
        in _should_invest. Called by the caller only after a successful, real
        (non-simulated) execution.

        @PARAMS:
            - config -> strategy configuration containing the strategy 'name'
        """
        strategy_name = config.get('name', 'scheduled')
        self._mark_run(strategy_name)

    def calculate_investable_amount(self, config: Dict) -> Tuple[float, List[Dict]]:
        """
        Function to calculate investment amount based on schedule and last run.
        Returns tuple of (investment_amount, details_list).
        
        @PARAMS:
            - config -> strategy configuration with 'name', 'amount', and 'interval'
        """
        strategy_name = config.get('name', 'scheduled')
        amount = config.get('amount', 10.0)
        interval = config.get('interval', 'daily')
        
        # check if we should invest based on interval
        if not self._should_invest(strategy_name, interval):
            print(f"[{strategy_name}] Skipping - {interval} interval not yet elapsed")
            return (0.0, [])

        # NOTE: do NOT mark the run here. The run is recorded only once trades
        # are actually executed, via commit_run(). Marking at calculation time
        # would make a simulation or a failed/insufficient-funds execution
        # wrongly consume the interval.
        details = [{
            'type': 'scheduled',
            'strategy': strategy_name,
            'amount': amount,
            'interval': interval,
            'timestamp': datetime.now().isoformat()
        }]
        
        return (amount, details)

