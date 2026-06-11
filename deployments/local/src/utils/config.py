"""
Configuration Management

Loads and validates configuration from YAML files.
"""

import os
import re
import sys
import yaml
from typing import Dict

# Matches ${VAR_NAME} placeholders for environment-variable substitution.
_ENV_VAR_PATTERN = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}')


def expand_env_vars(value):
    """
    Function to recursively replace ${VAR} placeholders with environment values.
    Walks dicts, lists, and strings; non-strings are returned unchanged.
    Unset variables resolve to an empty string so downstream "not configured"
    checks fire cleanly instead of leaking the literal "${VAR}" placeholder.

    @PARAMS:
        - value -> config value to expand (dict, list, str, or scalar)
    """
    if isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    if isinstance(value, str):
        return _ENV_VAR_PATTERN.sub(lambda m: os.environ.get(m.group(1), ''), value)
    return value


def load_config(config_path: str) -> Dict:
    """
    Function to load and parse configuration settings from a YAML file.
    Returns a dictionary containing all configuration parameters, with any
    ${VAR} placeholders expanded from the environment.

    @PARAMS:
        - config_path -> path to YAML configuration file
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return expand_env_vars(config)

    except FileNotFoundError:
        print(f"Error: Config file '{config_path}' not found")
        print("Run: cp config.example.yml config.yml")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)