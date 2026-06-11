"""
Micro-Investing Engine

Automatically invests based on custom strategies using Alpaca fractional trading.
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# add core directory to path for shared strategies and clients
core_path = Path(__file__).parent.parent.parent / 'core'
if not core_path.exists():
    print("\nERROR: Missing 'core/' directory!")
    print("The shared code directory was not found at:", core_path)
    print("\nThis usually means:")
    print("  1. You're not running from the correct directory")
    print("  2. The repository was not cloned completely")
    print("\nPlease ensure you're in: deployments/local/")
    print("And the full repository structure is intact.")
    sys.exit(1)

sys.path.insert(0, str(core_path))

# import from shared core
try:
    from clients import RewardCalculator, AlpacaTrader
    from engine import build_plan, execute_plan
except ImportError as e:
    print(f"\nERROR: Failed to import from core/: {e}")
    print("Please ensure all files in core/ directory are intact.")
    sys.exit(1)

# import local-specific utilities
from src.utils import Ledger, load_config, NotificationManager

load_dotenv()

def check_first_run():
    """
    Function to check if this is the first run and guide user through setup.
    """
    env_path = Path('.env')
    
    if not env_path.exists():
        print("\n" + "=" * 70)
        print("  FIRST TIME SETUP NEEDED")
        print("=" * 70)
        print("\nNo configuration found. Run the setup script:")
        print("  python setup.py")
        print()
        return True
    
    alpaca_key = os.getenv('ALPACA_API_KEY', '')
    if not alpaca_key or alpaca_key.startswith('your_'):
        print("\n[WARNING] Alpaca API keys not configured")
        print("          Run: python setup.py")
        return True
    
    return False

def main():
    """
    Function to run the main micro-investing engine, processing strategies and executing trades.
    """
    parser = argparse.ArgumentParser(
        description="Micro-investing engine with multiple strategy support"
    )
    parser.add_argument(
        'mode',
        choices=['simulate', 'run'],
        help='Mode: simulate (dry run) or run (execute trades)'
    )
    parser.add_argument(
        '--config',
        default='config.yml',
        help='Path to config file (default: config.yml)'
    )
    
    args = parser.parse_args()
    simulate_mode = args.mode == 'simulate'
    
    if check_first_run():
        sys.exit(1)
    
    print("=" * 80)
    print("MICRO-INVESTING ENGINE")
    print("=" * 80)
    print(f"Mode: {'SIMULATE (No Trades Executed)' if simulate_mode else 'RUN (Execute Real Trades)'}")
    print()
    
    config = load_config(args.config)
    
    # get strategies from config
    strategies_config = config.get('strategies')
    if not strategies_config:
        print("Error: No 'strategies' defined in config.yml")
        sys.exit(1)
    
    # get alpaca keys
    alpaca_config = config.get('alpaca', {})
    is_paper_trading = alpaca_config.get('paper', True)
    if is_paper_trading:
        alpaca_api_key = os.getenv('ALPACA_API_KEY') or alpaca_config.get('api_key')
        alpaca_secret_key = os.getenv('ALPACA_SECRET_KEY') or alpaca_config.get('secret_key')

        if not alpaca_api_key or not alpaca_secret_key:
            print("Error: Paper trading requires ALPACA_API_KEY and ALPACA_SECRET_KEY")
            print("       Set them in your .env file (run: python setup.py)")
            sys.exit(1)

    # alpaca uses live api keys for real trading, different than paper trading keys
    else:
        alpaca_api_key = os.getenv('ALPACA_LIVE_API_KEY')
        alpaca_secret_key = os.getenv('ALPACA_LIVE_SECRET_KEY')

        if not alpaca_api_key or not alpaca_secret_key:
            print("Error: Live trading requires ALPACA_LIVE_API_KEY and ALPACA_LIVE_SECRET_KEY")
            sys.exit(1)
    
    # build the reward calculator once if any enabled strategy needs it
    calculator = None
    needs_calculator = any(
        s.get('type') == 'credit_card_rewards' and s.get('enabled', True)
        for s in strategies_config
    )
    if needs_calculator:
        cardcaddie_api_key = os.getenv('THECARDCADDIE_API_KEY') or config.get('api', {}).get('key')
        if cardcaddie_api_key:
            calculator = RewardCalculator(
                api_key=cardcaddie_api_key,
                base_url=config.get('api', {}).get('base_url', 'https://www.thecardcaddie.com')
            )
        else:
            print("[WARNING] A credit_card_rewards strategy is enabled but THECARDCADDIE_API_KEY "
                  "is not set; it will be skipped.")

    # run all enabled strategies through the shared engine
    csv_default = config.get('transactions', {}).get('csv_file')
    plan = build_plan(strategies_config, calculator=calculator, csv_default=csv_default)

    if plan.total_investable == 0:
        print("\nNo investable amount across all enabled strategies. Exiting.")
        sys.exit(0)

    print("\n" + "=" * 80)
    print(f"TOTAL INVESTABLE: ${plan.total_investable:.4f}")
    print("Combined Allocation:")
    for symbol, amount in plan.combined_allocation.items():
        weight = (amount / plan.total_investable) * 100
        print(f"  {symbol}: ${amount:.2f} ({weight:.1f}%)")
    print("=" * 80)

    ledger_file = config.get('execution', {}).get('ledger_file', 'data/ledger/ledger.csv')
    executed_names = ",".join(plan.executed_names)

    # check funds and execute (or simulate) through the shared engine.
    # In real mode execute_plan places the orders; in simulate mode it places none.
    print("\nChecking Alpaca account balance and submitting any orders...")
    trader = AlpacaTrader(
        api_key=alpaca_api_key,
        secret_key=alpaca_secret_key,
        paper=is_paper_trading
    )
    result = execute_plan(plan, trader, simulate=simulate_mode)
    print(f"Available buying power: ${result.buying_power:.2f}")

    # handle insufficient funds
    if result.status == 'insufficient_funds':
        print(f"\nINSUFFICIENT FUNDS")
        print(f"Need: ${plan.total_investable:.2f}")
        print(f"Have: ${result.buying_power:.2f}")
        print(f"Shortfall: ${result.shortfall:.2f}")

        if simulate_mode:
            print("\n[SIMULATE] Would fail due to insufficient funds")
        else:
            print("\nPlease add funds to your Alpaca account and try again.")

            # send email notification if enabled (only in real mode)
            notifier = NotificationManager(config)
            if notifier.enabled:
                notifier.notify_insufficient_funds(
                    amount_needed=plan.total_investable,
                    buying_power=result.buying_power,
                    shortfall=result.shortfall
                )
                print("Email notification sent")

            # log as insufficient funds
            ledger = Ledger(ledger_file)
            ledger.log_run(plan.total_investable, plan.combined_allocation, simulate_mode,
                           "insufficient_funds", strategy_name=executed_names)
        sys.exit(1)

    print("Sufficient funds available")

    if simulate_mode:
        print("\n[SIMULATE] Would execute these trades:")
        for symbol, amount in plan.combined_allocation.items():
            print(f"  {symbol}: ${amount:.2f}")
        print()
    else:
        # orders were placed by execute_plan above; send the success notification
        notifier = NotificationManager(config)
        if notifier.enabled:
            notifier.notify_investment_executed(
                amount=plan.total_investable,
                allocation=plan.combined_allocation,
                strategy=executed_names
            )
            print("Email notification sent")

    # log to ledger
    ledger = Ledger(ledger_file)
    ledger.log_run(plan.total_investable, plan.combined_allocation, simulate_mode,
                   "success", strategy_name=executed_names)

    if simulate_mode:
        print("[SIMULATE] Simulation complete! No trades were executed.")
    else:
        print("Run complete!")
    print(f"Logged to {ledger_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()