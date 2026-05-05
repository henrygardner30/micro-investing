"""
Credit Card Rewards Investment Strategy

Calculates actual credit card rewards using The Card Caddie API and invests them.
Requires The Card Caddie API key and transaction data.
"""

import csv
import sys
from typing import Dict, List, Tuple
from .base import BaseStrategy

class CreditCardRewardsStrategy(BaseStrategy):
    """
    Strategy that calculates credit card rewards using The Card Caddie API and invests them.
    
    Perfect for:
    - Maximizing investments based on actual credit card reward rates
    - Requires The Card Caddie API key and transaction data
    """
    
    def __init__(self):
        super().__init__("credit_card_rewards")
    
    def supports_transactions(self) -> bool:
        """
        Credit card rewards strategy processes transaction data.
        """
        return True

    def calculate_allocation(self, amount: float, config: Dict) -> Dict[str, float]:
        """
        Function to split the total investable amount proportionally across stocks based on predefined percentages.
        Returns a dictionary mapping each stock symbol to its dollar amount.
        
        @PARAMS:
            - amount -> total dollar amount to invest for this rewards run
            - config -> configuration dict containing 'allocation' with symbol: weight pairs
        """
        allocation = config.get('allocation', {})
        allocation_amounts = {}
        
        for symbol, weight in allocation.items():
            allocation_amounts[symbol] = amount * weight
        
        return allocation_amounts
    
    def validate_config(self, config: Dict) -> bool:
        """
        Function to validate that the strategy configuration for credit card rewards is correct.
        Checks for valid 'allocation' and 'csv_file'.
        Returns True if configuration is valid, False otherwise.
        
        @PARAMS:
            - config -> strategy configuration dictionary
        """
        if 'csv_file' not in config or not isinstance(config['csv_file'], str) or not config['csv_file']:
            print(f"Error: Strategy '{self.name}' requires a 'csv_file' to be specified.")
            return False

        allocation = config.get('allocation', {})
        if not allocation:
            print(f"Error: Strategy '{self.name}' requires 'allocation' to be defined.")
            return False
        
        total_weight = sum(allocation.values())
        if abs(total_weight - 1.0) > 0.01:
            print(f"Error: Allocation for strategy '{self.name}' must sum to 1.0 (got {total_weight:.2f})")
            return False
        
        return True

    def calculate_investable_from_csv(self, csv_path: str, calculator) -> Tuple[float, List[Dict]]:
        """
        Function to process transactions from CSV and calculate total investable amount using The Card Caddie API.
        Returns a tuple of (total_investable_amount, list_of_transaction_details).

        @PARAMS:
            - csv_path -> path to csv file with columns: date, amount, card, merchant, category (optional)
            - calculator -> RewardCalculator instance for The Card Caddie API calls
        """
        total_investable = 0.0
        transaction_details = []

        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    date = row.get('date', '')
                    amount = float(row.get('amount', 0))
                    card = row.get('card', '')
                    merchant = row.get('merchant', '')
                    category = row.get('category', '')

                    if not all([date, amount, card, merchant]):
                        print(f"Skipping invalid row: {row}")
                        continue

                    # calculate reward using The Card Caddie API
                    reward = calculator.calculate_reward(card, merchant, amount, category if category else None)

                    if reward:
                        reward_value = reward['value']
                        total_investable += reward_value

                        transaction_details.append({
                            'date': date,
                            'card': card,
                            'merchant': merchant,
                            'amount': amount,
                            'reward_rate': reward['rate'],
                            'reward_value': reward_value,
                            'category_used': reward.get('category', 'N/A')
                        })

                        print(f"{date} | ${amount:7.2f} at {merchant:20} | "
                              f"{reward['rate']:4} -> ${reward_value:.4f}")
                    else:
                        print(f"{date} | ${amount:7.2f} at {merchant:20} | Failed to calculate")

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Transaction file '{csv_path}' not found") from e
        except Exception as e:
            raise RuntimeError(f"Error processing CSV file '{csv_path}': {e}") from e

        return total_investable, transaction_details

    def calculate_investable_amount(self, config: Dict) -> Tuple[float, List[Dict]]:
        """
        Function to determine the total investable amount for the current run based on the credit card rewards strategy's logic.
        This method calls the CSV processing helper and requires a RewardCalculator instance.
        Returns a tuple of (total_investable_amount, list_of_transaction_details).

        @PARAMS:
            - config -> strategy-specific configuration dictionary, must contain 'csv_file' and API details.
        """
        csv_path = config.get('csv_file')
        if not csv_path:
            print(f"Error: Strategy '{self.name}' requires 'csv_file' to be specified in its configuration.")
            return 0.0, []
        
        # Note: RewardCalculator is initialized in main.py and passed to calculate_investable_from_csv
        print(f"[{self.name}] Note: RewardCalculator is initialized in main.py and passed to calculate_investable_from_csv.")
        return 0.0, []
    
    def process_transactions(self, transactions: List[Dict], api_client) -> Tuple[float, List[Dict]]:
        """
        Function to process a list of transaction dictionaries using The Card Caddie API (for Lambda/API Gateway).
        Returns tuple of (total_investable_amount, transaction_details).
        
        @PARAMS:
            - transactions -> list of transaction dicts with 'card', 'merchant', 'amount' fields
            - api_client -> The Card Caddie API client instance
        """
        total = 0.0
        details = []
        
        for txn in transactions:
            try:
                card = txn.get('card', '')
                merchant = txn.get('merchant', '')
                amount = float(txn.get('amount', 0))
                category = txn.get('category', '')
                
                if not all([card, merchant, amount]):
                    continue
                
                # call The Card Caddie API
                reward = api_client.calculate_reward(card, merchant, amount, category if category else None)
                
                if reward:
                    reward_value = reward['value']
                    total += reward_value
                    details.append({
                        'date': txn.get('date', ''),
                        'card': card,
                        'merchant': merchant,
                        'amount': amount,
                        'reward': reward_value
                    })
            except Exception as e:
                # Log error but continue processing other transactions
                print(f"Warning: Failed to process transaction: {e}")
                continue
        
        return (total, details)