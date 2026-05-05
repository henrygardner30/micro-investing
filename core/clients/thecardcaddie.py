"""
The Card Caddie API Client

Calculates credit card rewards for transactions.
"""

import requests
from typing import Optional, Dict

class RewardCalculator:
    """
    Client for The Card Caddie reward calculation API.
    
    Calculates actual credit card rewards based on:
    - Card name
    - Merchant
    - Transaction amount
    - Category (optional)
    """
    
    def __init__(self, api_key: str, base_url: str = "https://www.thecardcaddie.com"):
        """
        Initialize The Card Caddie API client.
        
        @PARAMS:
            - api_key  -> The Card Caddie API key
            - base_url -> API base URL (default: https://www.thecardcaddie.com)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/api/v1/calculate-reward"
    
    def calculate_reward(
        self,
        card: str,
        merchant: str,
        amount: float,
        category: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Calculate reward for a transaction.
        Returns reward dict if successful, None if error.
        
        @PARAMS:
            - card     -> Credit card name (must match name in your Card Caddie account)
            - merchant -> Merchant name (e.g., "Starbucks", "amazon.com")
            - amount   -> Transaction amount in dollars
            - category -> Optional category override (e.g., "Dining", "Travel")
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "card": card,
            "merchant": merchant,
            "amount": amount
        }
        
        if category:
            payload["category"] = category
        
        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('reward')
            
            return None
            
        except Exception as e:
            print(f"Error calling The Card Caddie API: {e}")
            return None

