"""
Shared investment strategies for all deployments.

These strategies work across local, Lambda, and any future deployment methods.
"""

from .base import BaseStrategy, STRATEGY_REGISTRY
from .scheduled import ScheduledStrategy
from .round_up import RoundUpStrategy
from .credit_card_rewards import CreditCardRewardsStrategy

__all__ = ['BaseStrategy', 'STRATEGY_REGISTRY', 'ScheduledStrategy', 'RoundUpStrategy', 'CreditCardRewardsStrategy']

