"""Configuration loader for Lambda"""

import os
import json
from typing import Dict

def load_config() -> Dict:
    """
    Load configuration from environment variables.
    Expects STRATEGY_CONFIG as JSON string.
    
    @PARAMS: None
    """
    # try to load strategy config from env
    config_str = os.getenv('STRATEGY_CONFIG', '{}')
    
    try:
        config = json.loads(config_str)
    except:
        config = {}
    
    # set defaults if not provided
    if 'strategies' not in config:
        config['strategies'] = [{
            'name': 'default_scheduled',
            'type': 'scheduled',
            'enabled': True,
            'amount': 10.0,
            'interval': 'biweekly',
            'allocation': {'VOO': 0.6, 'QQQ': 0.4}
        }]
    
    return config