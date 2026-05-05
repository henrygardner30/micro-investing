"""
AWS Lambda Handler for Micro-Investing Engine

Supports two execution modes:
1. Scheduled (EventBridge trigger) - runs configured strategies
2. API Gateway (POST request) - processes transaction data on-demand

Note: strategies/ and clients/ are copied from core/ during build
"""

import json
import os
from datetime import datetime
from typing import Dict, Any

# imports from core/ (copied during build)
from strategies import STRATEGY_REGISTRY
from clients import AlpacaTrader, RewardCalculator

# lambda-specific utilities
from utils import save_to_ledger, load_config, get_state_storage

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda entry point for micro-investing engine.
    
    @PARAMS:
        - event   -> event data from EventBridge or API Gateway
        - context -> Lambda context object
    """
    print(f"Event: {json.dumps(event)}")
    
    # determine trigger source
    if 'source' in event and event['source'] == 'aws.events':
        # EventBridge scheduled trigger
        return handle_scheduled_run(event, context)
    elif 'httpMethod' in event or 'requestContext' in event or 'rawPath' in event:
        # API Gateway trigger (supports both REST API and HTTP API)
        return handle_api_request(event, context)
    elif 'transactions' in event or 'strategy' in event:
        # Direct invocation with transaction data (testing or direct Lambda invoke)
        # Wrap it in API Gateway format
        wrapped_event = {
            'body': event,
            'httpMethod': 'POST'
        }
        return handle_api_request(wrapped_event, context)
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Unknown event source',
                'received_keys': list(event.keys()),
                'tip': 'Expected EventBridge (source: aws.events) or API Gateway (httpMethod/requestContext) or direct transaction data'
            })
        }

def handle_scheduled_run(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle scheduled EventBridge trigger.
    Runs configured strategies from environment variables.
    
    @PARAMS:
        - event   -> EventBridge event
        - context -> Lambda context
    """
    print("Processing scheduled investment run...")
    
    try:
        # load configuration from environment variables
        config = load_config()
        
        # get alpaca credentials based on trading mode
        # IMPORTANT: ALPACA_PAPER env var MUST match your key type:
        #   - ALPACA_PAPER=true  -> Uses ALPACA_API_KEY/ALPACA_SECRET_KEY (paper keys)
        #   - ALPACA_PAPER=false -> Uses ALPACA_LIVE_API_KEY/ALPACA_LIVE_SECRET_KEY (live keys)
        # You CANNOT use paper keys for live trading or vice versa!
        is_paper = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
        
        if is_paper:
            # paper trading mode - uses paper trading keys
            alpaca_key = os.getenv('ALPACA_API_KEY')
            alpaca_secret = os.getenv('ALPACA_SECRET_KEY')
        else:
            # live trading mode - uses separate live trading keys (REAL MONEY!)
            alpaca_key = os.getenv('ALPACA_LIVE_API_KEY')
            alpaca_secret = os.getenv('ALPACA_LIVE_SECRET_KEY')
        
        if not alpaca_key or not alpaca_secret:
            mode = "paper" if is_paper else "live"
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Alpaca {mode} trading credentials not configured'})
            }
        
        # initialize alpaca client
        alpaca = AlpacaTrader(alpaca_key, alpaca_secret, paper=is_paper)
        
        # process strategies
        total_investable = 0.0
        combined_allocation = {}
        
        # initialize state storage for scheduled strategies
        state_storage = get_state_storage()
        
        # get strategies
        strategies = config.get('strategies', [])
        for strat_config in strategies:
            if not strat_config.get('enabled', True):
                continue
            
            strategy_type = strat_config['type']
            strategy_name = strat_config.get('name', strategy_type)
            
            if strategy_type not in STRATEGY_REGISTRY:
                print(f"Unknown strategy type: {strategy_type}")
                continue
            
            # initialize strategy (with state storage for scheduled)
            StrategyClass = STRATEGY_REGISTRY[strategy_type]
            if strategy_type == 'scheduled':
                strategy = StrategyClass(state_storage=state_storage)
            else:
                strategy = StrategyClass()
            
            # calculate investable amount
            amount, _ = strategy.calculate_investable_amount(strat_config)
            
            if amount > 0:
                total_investable += amount
                allocation = strategy.calculate_allocation(amount, strat_config)
                for symbol, amt in allocation.items():
                    combined_allocation[symbol] = combined_allocation.get(symbol, 0) + amt
        
        if total_investable == 0:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No investment needed at this time',
                    'amount': 0
                })
            }
        
        # check buying power
        buying_power = alpaca.get_buying_power()
        if buying_power < total_investable:
            error_msg = f"Insufficient funds: need ${total_investable:.2f}, have ${buying_power:.2f}"
            print(error_msg)
            
            # log insufficient funds
            save_to_ledger({
                'timestamp': datetime.now().isoformat(),
                'amount': total_investable,
                'allocation': combined_allocation,
                'status': 'insufficient_funds',
                'note': error_msg
            })
            
            return {
                'statusCode': 402,
                'body': json.dumps({'error': error_msg})
            }
        
        # execute trades
        results = []
        for symbol, amount in combined_allocation.items():
            result = alpaca.place_fractional_order(symbol, amount, dry_run=False)
            if result:
                results.append(result)
        
        # log to ledger
        save_to_ledger({
            'timestamp': datetime.now().isoformat(),
            'amount': total_investable,
            'allocation': combined_allocation,
            'status': 'success',
            'orders': results
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Investment executed successfully',
                'amount': total_investable,
                'allocation': combined_allocation,
                'orders': results
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_api_request(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle API Gateway POST request.
    Can process transactions OR run custom strategies without transaction data.
    
    @PARAMS:
        - event   -> API Gateway event with optional transaction data
        - context -> Lambda context
    """
    print("Processing API Gateway request...")
    
    try:
        # parse request body (handle both stringified and already-parsed JSON)
        raw_body = event.get('body', '{}')
        if isinstance(raw_body, str):
            body = json.loads(raw_body)
        else:
            # body is already parsed (e.g., from Lambda test console)
            body = raw_body if raw_body else {}
        
        transactions = body.get('transactions', [])
        strategy_config = body.get('config', {})
        
        # auto-detect strategy type if not specified
        strategy_type = body.get('strategy', '')
        if not strategy_type:
            # try to infer from transaction data
            if transactions:
                # check if transactions have 'card' field (credit card rewards)
                if any('card' in t for t in transactions):
                    strategy_type = 'credit_card_rewards'
                else:
                    # default to round_up for transactions without card data
                    strategy_type = 'round_up'
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'Missing strategy type',
                        'tip': 'Include "strategy" field in request body or provide transactions with card data'
                    })
                }
        
        # get alpaca credentials based on trading mode
        # IMPORTANT: ALPACA_PAPER env var MUST match your key type:
        #   - ALPACA_PAPER=true  -> Uses ALPACA_API_KEY/ALPACA_SECRET_KEY (paper keys)
        #   - ALPACA_PAPER=false -> Uses ALPACA_LIVE_API_KEY/ALPACA_LIVE_SECRET_KEY (live keys)
        # You CANNOT use paper keys for live trading or vice versa!
        is_paper = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
        
        if is_paper:
            # paper trading mode - uses paper trading keys
            alpaca_key = os.getenv('ALPACA_API_KEY')
            alpaca_secret = os.getenv('ALPACA_SECRET_KEY')
        else:
            # live trading mode - uses separate live trading keys (REAL MONEY!)
            alpaca_key = os.getenv('ALPACA_LIVE_API_KEY')
            alpaca_secret = os.getenv('ALPACA_LIVE_SECRET_KEY')
        
        if not alpaca_key or not alpaca_secret:
            mode = "paper" if is_paper else "live"
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Alpaca {mode} trading credentials not configured'})
            }
        
        # initialize alpaca client
        alpaca = AlpacaTrader(alpaca_key, alpaca_secret, paper=is_paper)
        
        # get strategy
        if strategy_type not in STRATEGY_REGISTRY:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown strategy: {strategy_type}'})
            }
        
        StrategyClass = STRATEGY_REGISTRY[strategy_type]
        strategy = StrategyClass()
        
        # calculate investable amount
        amount = 0.0
        details = []
        
        # Option 1: Transaction-based strategies (round_up, credit_card_rewards, custom strategies with transactions)
        if transactions:
            # check if this strategy supports transaction processing
            if strategy.supports_transactions():
                if strategy_type == 'credit_card_rewards':
                    # need The Card Caddie API client
                    cardcaddie_key = os.getenv('THECARDCADDIE_API_KEY')
                    if not cardcaddie_key:
                        return {
                            'statusCode': 400,
                            'body': json.dumps({'error': 'THECARDCADDIE_API_KEY required for credit_card_rewards strategy'})
                        }
                    calculator = RewardCalculator(cardcaddie_key)
                    amount, details = strategy.process_transactions(transactions, calculator)
                else:
                    amount, details = strategy.process_transactions(transactions)
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': f'Strategy {strategy_type} does not support transaction processing'})
                }
        
        # Option 2: Config-based strategies (scheduled, custom strategies without transactions)
        else:
            # use config from request body or defaults
            config_to_use = {
                'name': body.get('name', f'api_{strategy_type}'),
                'type': strategy_type,
                **strategy_config
            }
            
            # validate config
            if not strategy.validate_config(config_to_use):
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': f'Invalid configuration for strategy {strategy_type}'})
                }
            
            amount, details = strategy.calculate_investable_amount(config_to_use)
        
        if amount == 0:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No investable amount from transactions',
                    'amount': 0
                })
            }
        
        # get allocation from request or use defaults
        allocation_config = body.get('allocation', {'VOO': 0.6, 'QQQ': 0.4})
        allocation = {}
        for symbol, weight in allocation_config.items():
            allocation[symbol] = amount * weight
        
        # check buying power
        buying_power = alpaca.get_buying_power()
        if buying_power < amount:
            return {
                'statusCode': 402,
                'body': json.dumps({
                    'error': f'Insufficient funds: need ${amount:.2f}, have ${buying_power:.2f}'
                })
            }
        
        # execute trades
        results = []
        for symbol, amt in allocation.items():
            result = alpaca.place_fractional_order(symbol, amt, dry_run=False)
            if result:
                results.append(result)
        
        # log to ledger
        save_to_ledger({
            'timestamp': datetime.now().isoformat(),
            'amount': amount,
            'allocation': allocation,
            'status': 'success',
            'strategy': strategy_type,
            'orders': results
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Investment executed successfully',
                'amount': amount,
                'allocation': allocation,
                'orders': results
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }