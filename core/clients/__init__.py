"""
Shared API clients for all deployments.

These clients work across local, Lambda, and any future deployment methods.
"""

from .alpaca import AlpacaTrader
from .thecardcaddie import RewardCalculator

__all__ = ['AlpacaTrader', 'RewardCalculator']

