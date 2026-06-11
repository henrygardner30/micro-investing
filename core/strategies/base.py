"""
Base Investment Strategy

Abstract base class for all investment strategies.
Includes auto-registration for plugin-style strategy creation.
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional

# strategy registry - auto-populated by subclasses
STRATEGY_REGISTRY = {}

class BaseStrategy(ABC):
    """Abstract base class for investment strategies"""
    
    def __init__(self, name: str):
        self.name = name
    
    def __init_subclass__(cls, **kwargs):
        """
        Automatically register strategy subclasses.
        Any class that inherits from BaseStrategy is auto-registered.
        """
        super().__init_subclass__(**kwargs)
        # skip any private classes
        if not cls.__name__.startswith('_'):
            # register by strategy type name (snake_case from CamelCase)
            strategy_type = cls.__name__.replace('Strategy', '')
            # Convert CamelCase to snake_case (e.g., CreditCardRewards -> credit_card_rewards)
            
            strategy_type = re.sub('([a-z0-9])([A-Z])', r'\1_\2', strategy_type).lower()
            STRATEGY_REGISTRY[strategy_type] = cls
    
    @abstractmethod
    def supports_transactions(self) -> bool:
        """
        Function to indicate whether this strategy can process transaction data directly.
        Returns True if strategy supports transaction processing, False otherwise.
        """
        pass
    
    @abstractmethod
    def calculate_allocation(self, amount: float, config: Dict) -> Dict[str, float]:
        """
        Function to calculate how investment amount should be allocated across different assets.
        Returns a dictionary mapping stock symbols to dollar amounts.
        
        @PARAMS:
            - amount -> Total dollar amount available to invest
            - config -> Strategy configuration dictionary with allocation rules
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict) -> bool:
        """
        Function to validate that the strategy configuration is correct and usable.
        Returns True if configuration is valid, False otherwise.
        
        @PARAMS:
            - config -> Strategy configuration dictionary to validate
        """
        pass
    
    @abstractmethod
    def calculate_investable_amount(self, config: Dict) -> Tuple[float, List[Dict]]:
        """
        Function to determine the total investable amount for the current run based on the strategy's logic.
        Returns a tuple of (total_investable_amount, list_of_transaction_details or other relevant details).
        
        @PARAMS:
            - config -> Strategy-specific configuration dictionary.
        """
        pass

    def calculate_investable_from_csv(self, csv_path: str, calculator=None) -> Tuple[float, List[Dict]]:
        """
        Optional helper function for strategies that process transactions from a CSV file.
        Returns a tuple of (total_investable_amount, list_of_transaction_details).
        
        Strategies that do not use CSVs do not need to override this.
        
        @PARAMS:
            - csv_path -> Path to CSV file with transaction data
            - calculator -> Optional: An API calculator instance (e.g., RewardCalculator) if needed by the strategy
        """
        return (0.0, [])  # Default implementation for non-CSV strategies

    def commit_run(self, config: Dict) -> None:
        """
        Optional hook invoked by the caller AFTER trades for this run have been
        successfully executed with real money. It is never called in simulate
        mode, nor when execution is aborted (e.g. insufficient funds).

        Stateful strategies that gate themselves on past runs (e.g. scheduled /
        recurring investing) must override this to persist that the run
        completed. Calculating the investable amount must NOT itself record the
        run, otherwise a simulation or a failed execution would wrongly consume
        the interval. Stateless strategies need not override this.

        @PARAMS:
            - config -> the strategy's configuration dictionary for this run
        """
        return None  # Default: stateless strategies have nothing to commit

