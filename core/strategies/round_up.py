"""
Round Up Investment Strategy

Rounds up each transaction to the nearest dollar and invests the spare change.
Does not require any external API keys for reward calculation.
"""

import csv
import sys
from math import ceil
from typing import Dict, List, Tuple
from .base import BaseStrategy

class RoundUpStrategy(BaseStrategy):
    """
    Strategy that rounds up each transaction to the nearest dollar and invests the spare change.
    
    Perfect for:
    - Micro-investing without needing complex reward calculations
    - Simple spare change accumulation
    """
    
    def __init__(self):
        super().__init__("round_up")
    
    def supports_transactions(self) -> bool:
        """
        Round up strategy processes transaction data.
        """
        return True

    def calculate_allocation(self, amount: float, config: Dict) -> Dict[str, float]:
        """
        Function to split the total investable amount proportionally across stocks based on predefined percentages.
        Returns a dictionary mapping each stock symbol to its dollar amount.
        
        @PARAMS:
            - amount -> Total dollar amount to invest for this round-up run
            - config -> Configuration dict containing 'allocation' with symbol: weight pairs
        """
        allocation = config.get('allocation', {})
        allocation_amounts = {}
        
        for symbol, weight in allocation.items():
            allocation_amounts[symbol] = amount * weight
        
        return allocation_amounts
    
    def validate_config(self, config: Dict) -> bool:
        """
        Function to validate that the strategy configuration for round-up investments is correct.
        Checks for valid 'allocation'.
        Returns True if configuration is valid, False otherwise.
        
        @PARAMS:
            - config -> Strategy configuration dictionary
        """
        allocation = config.get('allocation', {})
        if not allocation:
            print(f"Error: Strategy '{self.name}' requires 'allocation' to be defined.")
            return False
        
        total_weight = sum(allocation.values())
        if abs(total_weight - 1.0) > 0.01:
            print(f"Error: Allocation for strategy '{self.name}' must sum to 1.0 (got {total_weight:.2f})")
            return False
        
        return True

    def calculate_investable_from_csv(self, csv_path: str, calculator=None) -> Tuple[float, List[Dict]]:
        """
        Function to process transactions from csv and calculate total investable amount using round-up method.
        Returns a tuple of (total_investable_amount, list_of_transaction_details).

        @PARAMS:
            - csv_path -> path to csv file with columns: date, amount (required), card (optional), merchant (optional)
            - calculator -> not used for round-up strategy
        """
        total_investable = 0.0
        transaction_details = []

        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    date = row.get('date', '')
                    amount_str = row.get('amount', '0')
                    
                    try:
                        amount = float(amount_str)
                    except ValueError:
                        print(f"Skipping invalid amount: {amount_str}")
                        continue

                    if not date or amount <= 0:
                        continue

                    # calculate round up
                    rounded = ceil(amount)
                    round_up_amount = rounded - amount

                    if round_up_amount > 0:
                        total_investable += round_up_amount
                        
                        transaction_details.append({
                            'date': date,
                            'amount': amount,
                            'rounded': rounded,
                            'round_up': round_up_amount,
                            'card': row.get('card', 'N/A'),
                            'merchant': row.get('merchant', 'N/A')
                        })

                        print(f"{date} | ${amount:7.2f} -> ${rounded:7.2f} | Round up: ${round_up_amount:.2f}")

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Transaction file '{csv_path}' not found") from e
        except Exception as e:
            raise RuntimeError(f"Error processing CSV file '{csv_path}': {e}") from e

        return total_investable, transaction_details

    def calculate_investable_amount(self, config: Dict) -> Tuple[float, List[Dict]]:
        """
        Function to determine the total investable amount for the current run based on the round-up strategy's logic.
        This method calls the CSV processing helper.
        Returns a tuple of (total_investable_amount, list_of_transaction_details).

        @PARAMS:
            - config -> Strategy-specific configuration dictionary, must contain 'csv_file'.
        """
        csv_path = config.get('csv_file')
        if not csv_path:
            print(f"Error: Strategy '{self.name}' requires 'csv_file' to be specified in its configuration.")
            return 0.0, []
        return self.calculate_investable_from_csv(csv_path)
    
    def process_transactions(self, transactions: List[Dict]) -> Tuple[float, List[Dict]]:
        """
        Function to process a list of transaction dictionaries (for API Gateway/Lambda use).
        Returns tuple of (total_investable_amount, transaction_details).
        
        @PARAMS:
            - transactions -> List of transaction dicts with 'amount' field
        """
        total = 0.0
        details = []
        
        for txn in transactions:
            try:
                amount = float(txn.get('amount', 0))
                if amount <= 0:
                    continue
                
                rounded = ceil(amount)
                round_up = rounded - amount
                
                if round_up > 0:
                    total += round_up
                    details.append({
                        'date': txn.get('date', ''),
                        'merchant': txn.get('merchant', 'Unknown'),
                        'amount': amount,
                        'rounded': rounded,
                        'round_up': round_up
                    })
            except Exception as e:
                # Log error but continue processing other transactions
                print(f"Warning: Failed to process transaction: {e}")
                continue
        
        return (total, details)