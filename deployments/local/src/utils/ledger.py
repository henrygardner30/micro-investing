"""
Investment Ledger

Logs all investment runs to CSV for tracking and auditing.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict

class Ledger:
    """Logs investment runs to CSV"""
    
    def __init__(self, ledger_path: str):
        self.ledger_path = ledger_path
        self._ensure_ledger_exists()
    
    def _ensure_ledger_exists(self):
        """
        Function to create the ledger CSV file with headers if it doesn't already exist.
        """
        if not Path(self.ledger_path).exists():
            # ensure parent directory exists
            Path(self.ledger_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.ledger_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'strategy', 'amount', 'symbols', 'simulated', 'notes'])
    
    def log_run(self, amount: float, allocation: Dict[str, float], simulated: bool, notes: str = "", strategy_name: str = "round_up"):
        """
        Function to log an investment run to the CSV ledger for tracking and auditing purposes.
        Returns nothing (writes to file).
        
        @PARAMS:
            - amount        -> total dollar amount that was investable from rewards
            - allocation    -> mapping stock symbols to invested dollar amounts
            - simulated     -> boolean indicating if this was a simulation (true) or real execution (false)
            - notes         -> string with additional notes about this run (default: "")
            - strategy_name -> name of the strategy used
        """
        timestamp = datetime.now().astimezone().isoformat()
        symbols_str = ','.join([f"{sym}:{amt:.2f}" for sym, amt in allocation.items()])
        
        with open(self.ledger_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, strategy_name, amount, symbols_str, simulated, notes])