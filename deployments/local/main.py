"""
Micro-Investing Engine

Automatically invests based on custom strategies using Alpaca fractional trading.
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

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
    from strategies import STRATEGY_REGISTRY
    from clients import RewardCalculator, AlpacaTrader
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
    
    # process each enabled strategy
    all_investable_amount = 0.0
    combined_allocation_amounts = defaultdict(float)
    executed_strategies_names = []
    # (instance, config) pairs to commit once trades have actually executed,
    # so stateful strategies (e.g. scheduled) only advance on a real run.
    pending_commits = []
    
    # loop through each strategy in the config
    for strategy_conf in strategies_config:
        strategy_name = strategy_conf.get('name', 'Unnamed Strategy')
        strategy_type = strategy_conf.get('type')
        strategy_enabled = strategy_conf.get('enabled', True)
        
        # skip if the strategy is disabled
        if not strategy_enabled:
            print(f"Skipping disabled strategy: {strategy_name}")
            continue
        
        if strategy_type not in STRATEGY_REGISTRY:
            print(f"Error: Unknown strategy type '{strategy_type}' for strategy '{strategy_name}'")
            continue
        
        # get the strategy class from the registry
        StrategyClass = STRATEGY_REGISTRY[strategy_type]
        strategy_instance = StrategyClass()
        
        print(f"\n[{strategy_name}] Processing strategy: {strategy_type}")
        
        # validate the strategy config
        if not strategy_instance.validate_config(strategy_conf):
            print(f"Error: Configuration for strategy '{strategy_name}' is invalid. Skipping.")
            continue
        
        current_investable = 0.0
        
        ##### STRATEGY TYPES #####
        # calculate the investable amount based on credit card rewards strategy
        if strategy_type == 'credit_card_rewards':
            cardcaddie_api_key = os.getenv('THECARDCADDIE_API_KEY') or config.get('api', {}).get('key')
            if not cardcaddie_api_key:
                print(f"Error: Credit card rewards strategy '{strategy_name}' requires THECARDCADDIE_API_KEY")
                continue
            # calculate the reward using thecardcaddie api
            calculator = RewardCalculator(
                api_key=cardcaddie_api_key,
                base_url=config.get('api', {}).get('base_url', 'https://www.thecardcaddie.com')
            )
            # get the transaction data from the csv file
            csv_path = strategy_conf.get('csv_file', config['transactions'].get('csv_file'))
            if not csv_path:
                print(f"Error: 'csv_file' not specified for strategy '{strategy_name}'")
                continue
            current_investable, _ = strategy_instance.calculate_investable_from_csv(csv_path, calculator)
        
        # calculate the investable amount based on the round up strategy
        elif strategy_type == 'round_up':
            csv_path = strategy_conf.get('csv_file', config['transactions'].get('csv_file'))
            if not csv_path:
                print(f"Error: 'csv_file' not specified for strategy '{strategy_name}'")
                continue
            current_investable, _ = strategy_instance.calculate_investable_from_csv(csv_path)
        
        # calculate the investable amount based on the scheduled strategy
        elif strategy_type == 'scheduled':
            current_investable, _ = strategy_instance.calculate_investable_amount(strategy_conf)
        
        # calculate the investable amount based on the custom strategy
        else:
            current_investable, _ = strategy_instance.calculate_investable_amount(strategy_conf)
        
        # apply strategy limits
        min_investment = strategy_conf.get('min_daily_investment', 0.0)
        max_investment = strategy_conf.get('max_daily_investment', float('inf'))
        
        # skip if the investable amount is below the minimum investment
        if current_investable < min_investment:
            print(f"[{strategy_name}] Amount ${current_investable:.2f} below minimum (${min_investment:.2f}). Skipping.")
            continue
        
        # skip if the investable amount is above the maximum investment
        if current_investable > max_investment:
            print(f"[{strategy_name}] Amount exceeds maximum (${max_investment:.2f}). Capping at max.")
            current_investable = max_investment
        
        # update the total investable amount and allocation
        if current_investable > 0:
            all_investable_amount += current_investable
            current_allocation = strategy_instance.calculate_allocation(current_investable, strategy_conf)
            for symbol, amount in current_allocation.items():
                combined_allocation_amounts[symbol] += amount
            executed_strategies_names.append(strategy_name)
            pending_commits.append((strategy_instance, strategy_conf))
            print(f"[{strategy_name}] Investable amount: ${current_investable:.4f}")
            print(f"[{strategy_name}] Allocation: {', '.join([f'{s}: ${a:.2f}' for s, a in current_allocation.items()])}")
        else:
            print(f"[{strategy_name}] No investable amount for this run.")
    
    if all_investable_amount == 0:
        print("\nNo investable amount across all enabled strategies. Exiting.")
        sys.exit(0)
    
    print("\n" + "=" * 80)
    print(f"TOTAL INVESTABLE: ${all_investable_amount:.4f}")
    print("Combined Allocation:")
    for symbol, amount in combined_allocation_amounts.items():
        weight = (amount / all_investable_amount) * 100
        print(f"  {symbol}: ${amount:.2f} ({weight:.1f}%)")
    print("=" * 80)
    
    # check balance (always check, even in simulate mode to show what would happen)
    print("\nChecking Alpaca account balance...")
    trader = AlpacaTrader(
        api_key=alpaca_api_key,
        secret_key=alpaca_secret_key,
        paper=is_paper_trading
    )
    
    # get the account balance
    account = trader.get_account()
    buying_power = float(account['buying_power'])
    
    print(f"Available buying power: ${buying_power:.2f}")
    
    # skip if the buying power is less than the total investable amount
    if buying_power < all_investable_amount:
        shortfall = all_investable_amount - buying_power
        print(f"\nINSUFFICIENT FUNDS")
        print(f"Need: ${all_investable_amount:.2f}")
        print(f"Have: ${buying_power:.2f}")
        print(f"Shortfall: ${shortfall:.2f}")
        
        if simulate_mode:
            print("\n[SIMULATE] Would fail due to insufficient funds")
        else:
            print("\nPlease add funds to your Alpaca account and try again.")
            
            # send email notification if enabled (only in real mode)
            notifier = NotificationManager(config)
            if notifier.enabled:
                notifier.notify_insufficient_funds(
                    amount_needed=all_investable_amount,
                    buying_power=buying_power,
                    shortfall=shortfall
                )
                print("Email notification sent")
            
            # log as insufficient funds
            ledger = Ledger(config['execution'].get('ledger_file', 'data/ledger/ledger.csv'))
            ledger.log_run(all_investable_amount, combined_allocation_amounts, simulate_mode, "insufficient_funds", 
                          strategy_name=",".join(executed_strategies_names))
        sys.exit(1)
    
    print("Sufficient funds available")
    
    # execute trades (or simulate)
    if simulate_mode:
        print("\n[SIMULATE] Would execute these trades:")
        for symbol, amount in combined_allocation_amounts.items():
            print(f"  {symbol}: ${amount:.2f}")
        print()
    else:
        print("\nExecuting trades...")
        for symbol, amount in combined_allocation_amounts.items():
            trader.place_fractional_order(symbol, amount, dry_run=False)
        print()

        # record the run for any stateful strategies now that trades executed
        for strategy_instance, strategy_conf in pending_commits:
            strategy_instance.commit_run(strategy_conf)

        # send email notification if enabled (only for real executions)
        notifier = NotificationManager(config)
        if notifier.enabled:
            notifier.notify_investment_executed(
                amount=all_investable_amount,
                allocation=combined_allocation_amounts,
                strategy=",".join(executed_strategies_names)
            )
            print("Email notification sent")
    
    # log to ledger
    ledger = Ledger(config['execution'].get('ledger_file', 'data/ledger/ledger.csv'))
    ledger.log_run(all_investable_amount, combined_allocation_amounts, simulate_mode, "success", 
                   strategy_name=",".join(executed_strategies_names))
    
    if simulate_mode:
        print("[SIMULATE] Simulation complete! No trades were executed.")
    else:
        print("Run complete!")
    print(f"Logged to {config['execution'].get('ledger_file', 'data/ledger/ledger.csv')}")
    print("=" * 80)

if __name__ == "__main__":
    main()