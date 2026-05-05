"""
Test Alpaca API connection and account details.

Supports both paper and live trading modes.

Usage:
    python tests/test_alpaca.py          # test paper trading (default)
    python tests/test_alpaca.py paper    # test paper trading
    python tests/test_alpaca.py live     # test live trading (real money)
"""

import requests
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add core to path for shared clients
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'core'))

load_dotenv()

def get_api_credentials(mode: str):
    """
    Function to get Alpaca API credentials based on trading mode.
    Returns tuple of (api_key, secret_key, base_url, mode_label) or (None, None, None, None) if keys not found.
    
    @PARAMS:
        - mode -> trading mode ('paper' or 'live')
    """
    if mode == 'paper':
        api_key = os.getenv('ALPACA_API_KEY')
        secret_key = os.getenv('ALPACA_SECRET_KEY')
        base_url = "https://paper-api.alpaca.markets"
        mode_label = "Paper Trading (Fake Money)"
        
        if not api_key or not secret_key:
            print("[ERROR] Paper trading API keys not set")
            print()
            print("Set these in your .env file:")
            print("  ALPACA_API_KEY=your_key")
            print("  ALPACA_SECRET_KEY=your_secret")
            print()
            print("Generate paper keys at:")
            print("  https://app.alpaca.markets/paper/dashboard/overview")
            return None, None, None, None
    
    # live mode
    else:
        api_key = os.getenv('ALPACA_LIVE_API_KEY')
        secret_key = os.getenv('ALPACA_LIVE_SECRET_KEY')
        base_url = "https://api.alpaca.markets"
        mode_label = "LIVE TRADING (REAL MONEY)"
        
        if not api_key or not secret_key:
            print("[ERROR] Live trading API keys not set")
            print()
            print("Paper keys (ALPACA_API_KEY) will NOT work with live trading.")
            print()
            print("Set these in your .env file:")
            print("  ALPACA_LIVE_API_KEY=your_key")
            print("  ALPACA_LIVE_SECRET_KEY=your_secret")
            print()
            print("Generate live keys at:")
            print("  https://app.alpaca.markets/dashboard/overview")
            return None, None, None, None
    
    return api_key, secret_key, base_url, mode_label

def test_account_info(api_key: str, secret_key: str, base_url: str) -> bool:
    """
    Function to test account connection and fetch account information.
    Returns true if successful, false otherwise.
    
    @PARAMS:
        - api_key    -> alpaca api key
        - secret_key -> alpaca secret key
        - base_url   -> alpaca api base url
    """
    print("\nTest 1: Fetching Account Information")
    print("-" * 70)
    
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key
    }
    
    try:
        response = requests.get(
            f"{base_url}/v2/account",
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            account = response.json()
            print("[SUCCESS] Account connected successfully!")
            print()
            print("Account Details:")
            print(f"  Buying Power: ${float(account.get('buying_power', 0)):,.2f}")
            print(f"  Cash: ${float(account.get('cash', 0)):,.2f}")
            print(f"  Portfolio Value: ${float(account.get('portfolio_value', 0)):,.2f}")
            print(f"  Account Status: {account.get('status', 'unknown')}")
            return True
        else:
            print(f"[ERROR] Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[ERROR] Connection timed out after 30 seconds")
        print()
        print("This could mean:")
        print("  - Network/firewall blocking Alpaca")
        print("  - VPN interfering with connection")
        print("  - Alpaca API is experiencing issues")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

def test_positions(api_key: str, secret_key: str, base_url: str) -> bool:
    """
    Function to test fetching current positions from Alpaca account.
    Returns true if successful, false otherwise.
    
    @PARAMS:
        - api_key    -> alpaca api key
        - secret_key -> alpaca secret key
        - base_url   -> alpaca api base url
    """
    print("\nTest 2: Fetching Positions")
    print("-" * 70)
    
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key
    }
    
    try:
        response = requests.get(
            f"{base_url}/v2/positions",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            positions = response.json()
            print(f"[SUCCESS] Positions fetched: {len(positions)} positions")
            
            if positions:
                print()
                print("Current Positions:")
                # show just the fist 5
                for pos in positions[:5]:
                    print(f"  {pos['symbol']}: {pos['qty']} shares @ ${pos['current_price']}")
                
                if len(positions) > 5:
                    print(f"  ... and {len(positions) - 5} more")
            else:
                print("  No positions currently held")
            
            return True
        else:
            print(f"[ERROR] Failed with status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("[ERROR] Connection timed out")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

def main():
    """
    Function to run Alpaca API connection tests.
    """
    parser = argparse.ArgumentParser(description="Test Alpaca API Connection")
    parser.add_argument('mode', nargs='?', default='paper', choices=['paper', 'live'],
                       help='Trading mode: paper (default) or live')
    
    args = parser.parse_args()
    mode = args.mode.lower()
    
    print("\n" + "=" * 70)
    print("ALPACA API CONNECTION TEST")
    print("=" * 70)
    
    # get credentials
    api_key, secret_key, base_url, mode_label = get_api_credentials(mode)
    
    if not api_key:
        return
    
    print()
    print(f"Mode: {mode_label}")
    print(f"Base URL: {base_url}")
    print()
    
    # run tests
    all_passed = True
    
    # test 1: account info
    if not test_account_info(api_key, secret_key, base_url):
        all_passed = False
    
    # test 2: positions
    if not test_positions(api_key, secret_key, base_url):
        all_passed = False
    
    # summary
    print()
    print("=" * 70)
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests failed. Check the errors above.")
    print("=" * 70)
    print()

if __name__ == "__main__":
    # check if API keys are set
    paper_key = os.getenv('ALPACA_API_KEY')
    live_key = os.getenv('ALPACA_LIVE_API_KEY')
    
    if not paper_key and not live_key:
        print("\n[WARNING] ERROR: Alpaca API keys not found!")
        print("   1. Sign up for Alpaca (free paper trading):")
        print("      https://app.alpaca.markets/signup")
        print("   2. Get your API keys from:")
        print("      https://app.alpaca.markets/paper/dashboard/overview")
        print("   3. Add them to your .env file:")
        print("      ALPACA_API_KEY=your_key")
        print("      ALPACA_SECRET_KEY=your_secret")
        print()
    else:
        main()