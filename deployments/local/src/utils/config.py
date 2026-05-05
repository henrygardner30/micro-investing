"""
Configuration Management

Loads and validates configuration from YAML files.
"""

import sys
import yaml
from typing import Dict

def load_config(config_path: str) -> Dict:
    """
    Function to load and parse configuration settings from a YAML file.
    Returns a dictionary containing all configuration parameters.
    
    @PARAMS:
        - config_path -> path to YAML configuration file
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config

    except FileNotFoundError:
        print(f"Error: Config file '{config_path}' not found")
        print("Run: cp config.example.yml config.yml")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)