"""
Alpaca Trading API Client

Handles fractional stock trading through Alpaca Markets.
Supports both paper trading (fake money) and live trading (real money).

Uses the Alpaca REST API directly via requests library.
API Documentation: https://docs.alpaca.markets/reference/
"""

import requests
from typing import Optional, Dict, Any

class AlpacaTrader:
    """
    Client for Alpaca Markets fractional trading.
    
    Supports:
    - Paper trading (testing with fake money)
    - Live trading (real money)
    - Fractional shares
    - Market orders
    """
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """
        Initialize Alpaca trading client.
        
        IMPORTANT: The 'paper' parameter only changes the API endpoint.
        You MUST provide the correct keys for the mode:
          - paper=True:  Provide paper trading keys
          - paper=False: Provide live trading keys (REAL MONEY!)
        
        The API calls are identical for both modes - only the endpoint differs.
        
        @PARAMS:
            - api_key    -> Alpaca API key (paper or live, depending on mode)
            - secret_key -> Alpaca secret key (paper or live, depending on mode)
            - paper      -> True for paper trading, False for live trading
        """
        self.paper = paper
        self.api_key = api_key
        self.secret_key = secret_key
        
        # The only difference: API endpoint URL
        if paper:
            self.base_url = "https://paper-api.alpaca.markets"
        else:
            self.base_url = "https://api.alpaca.markets"  # REAL MONEY!
        
        # Headers for API authentication
        self.headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a request to the Alpaca API.
        
        @PARAMS:
            - method   -> HTTP method (GET, POST, etc.)
            - endpoint -> API endpoint (e.g., "/v2/account")
            - data     -> Optional request body data
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Alpaca API request failed: {e}")
    
    def get_account(self) -> Dict[str, Any]:
        """
        Get account information.
        Returns account data as a dictionary.
        
        @PARAMS: None
        
        API Reference: https://docs.alpaca.markets/reference/getaccount-1
        """
        return self._make_request("GET", "/v2/account")
    
    def get_buying_power(self) -> float:
        """
        Get current buying power.
        Returns float of available buying power.
        
        @PARAMS: None
        """
        account = self.get_account()
        return float(account['buying_power'])
    
    def place_fractional_order(
        self,
        symbol: str,
        notional: float,
        dry_run: bool = False
    ) -> Optional[dict]:
        """
        Place a fractional buy order using dollar amount.
        Returns order object if successful, None if error.
        
        @PARAMS:
            - symbol   -> Stock symbol (e.g., "VOO", "QQQ")
            - notional -> Dollar amount to invest
            - dry_run  -> If True, only simulate the order
        
        API Reference: https://docs.alpaca.markets/reference/postorder
        """
        # Round to 2 decimal places (Alpaca requirement)
        notional_rounded = round(notional, 2)
        
        if notional_rounded < 1.0:
            print(f"[SKIP] {symbol}: ${notional_rounded:.2f} (below $1 minimum)")
            return None
        
        if dry_run:
            print(f"[DRY RUN] Would buy ${notional_rounded:.2f} of {symbol}")
            return {
                'symbol': symbol,
                'notional': notional_rounded,
                'status': 'simulated'
            }
        
        try:
            order_data = {
                "symbol": symbol,
                "notional": notional_rounded,
                "side": "buy",
                "type": "market",
                "time_in_force": "day"
            }
            
            order = self._make_request("POST", "/v2/orders", order_data)
            
            print(f"[ORDER] Submitted ${notional_rounded:.2f} of {symbol} (Order ID: {order['id']})")
            
            return {
                'symbol': symbol,
                'notional': notional_rounded,
                'order_id': order['id'],
                'status': order['status']
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to place order for {symbol}: {e}")
            return None