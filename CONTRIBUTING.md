# Contributing to Micro-Investing Engine

Thank you for your interest in contributing! This guide will help you get started.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Creating Custom Strategies](#creating-custom-strategies)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Testing](#testing)

---

## Getting Started

This project uses a shared core architecture with deployment-specific adapters. The shared engine (`core/engine.py`) runs strategies and executes trades via two functions — `build_plan` (validate, compute amounts, apply min/max limits, combine allocations) and `execute_plan` (check funds, place orders, commit stateful runs). The local CLI and Lambda handler are thin adapters that wire up config, credentials, logging, the ledger, and notifications around those calls. Changes to the engine, strategies, or API clients automatically apply to both local and Lambda deployments.

### Quick Start

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/micro-investing.git
   cd micro-investing
   ```

2. **Set up local deployment for testing**
   ```bash
   cd deployments/local
   python setup.py
   ```

3. **Test your setup**
   ```bash
   python main.py simulate
   ```

---

## Project Structure

```
micro-investing/
├── core/                          # Shared code: orchestration, strategies, API clients
│   ├── engine.py                  # Shared orchestrator (build_plan / execute_plan)
│   ├── strategies/                # Investment strategies (add new ones here)
│   │   ├── base.py                # Abstract base class
│   │   ├── scheduled.py           # Example: scheduled investing
│   │   ├── round_up.py            # Example: round-up investing
│   │   └── credit_card_rewards.py # Example: credit card rewards investing
│   └── clients/                   # API clients
│       ├── alpaca.py
│       └── thecardcaddie.py
│
├── deployments/
│   ├── local/                     # Local deployment
│   │   ├── main.py                # Entry point for local execution
│   │   ├── setup.py               # Interactive setup wizard
│   │   ├── tests/                 # Unit tests (pytest)
│   │   └── src/utils/             # Local-specific utilities
│   └── lambda/                    # AWS Lambda deployment
│       ├── lambda_function.py     # Lambda handler
│       ├── build.sh               # Build script (bundles core/ incl. engine.py)
│       └── utils/                 # Lambda-specific utilities
│
├── assets/                        # Images and static assets
│   └── images/                    # Logo and graphics
├── README.md                      # Main documentation
├── CONTRIBUTING.md                # This file
└── FAQ.md                         # Troubleshooting guide
```

---

## Development Setup

### Prerequisites

- Python 3.8+
- pip
- Alpaca account (free paper trading)

### Install Dependencies

**For local deployment:**
```bash
cd deployments/local
pip install -r requirements.txt
```

**For Lambda deployment:**
```bash
cd deployments/lambda
pip install -r requirements.txt
```

### Environment Variables

Create `.env` in `deployments/local/`:

```bash
# Alpaca API Keys
ALPACA_API_KEY=your_paper_key
ALPACA_SECRET_KEY=your_paper_secret

# Optional: The Card Caddie
THECARDCADDIE_API_KEY=your_api_key

# Optional: Email notifications
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_app_password
```

---

## Creating Custom Strategies

Strategies live in `core/strategies/` and work across all deployments.

### Strategy Template

Create a new file in `core/strategies/your_strategy.py`:

```python
"""
Your Strategy Name

Brief description of what this strategy does.
"""

from typing import Dict, List, Tuple
from .base import BaseStrategy

class YourStrategy(BaseStrategy):
    """
    Strategy description here.
    """
    
    def __init__(self):
        super().__init__("your_strategy")
    
    def supports_transactions(self) -> bool:
        """
        Return True if strategy processes transaction data.
        Return False if strategy is config-based only.
        """
        return False  # or True
    
    def calculate_investable_amount(self, config: Dict) -> Tuple[float, List[Dict]]:
        """
        Calculate how much to invest based on strategy logic.
        
        @PARAMS:
            - config -> Strategy configuration dictionary
        
        Returns:
            - tuple of (investable_amount, details_list)
        """
        # Your logic here
        amount = 10.0
        details = [{"info": "example"}]
        return (amount, details)
    
    def calculate_allocation(self, amount: float, config: Dict) -> Dict[str, float]:
        """
        Determine how to split investment across assets.
        
        @PARAMS:
            - amount -> Total amount to invest
            - config -> Strategy configuration dictionary
        
        Returns:
            - dictionary mapping stock symbols to dollar amounts
        """
        allocation = config.get('allocation', {'VOO': 1.0})
        return {symbol: amount * weight for symbol, weight in allocation.items()}
    
    def validate_config(self, config: Dict) -> bool:
        """
        Validate that configuration is correct.
        
        @PARAMS:
            - config -> Strategy configuration dictionary
        
        Returns:
            - True if valid, False otherwise
        """
        # Add validation logic
        return True
```

### Auto-Registration

Strategies are automatically registered when they extend `BaseStrategy`. No manual registration needed! The engine then runs your strategy the same way in both deployments — config-based strategies are driven through `calculate_investable_amount`, and transaction (CSV) strategies through `calculate_investable_from_csv`.

### Persisting State (optional)

If your strategy must not repeat on a simulated or failed run (e.g. recurring/scheduled investing), override `commit_run(self, config)`. The engine calls it **only** after trades have actually executed — never in `simulate` mode or when funds are insufficient — so the run is recorded exactly once. Compute logic (e.g. `calculate_investable_amount`) must not record the run itself. See `ScheduledStrategy` for an example. Stateless strategies can ignore this.

### Using Your Strategy

**Local deployment** (`config.yml`):
```yaml
strategies:
  - name: "my_custom"
    type: your_strategy  # matches class name without "Strategy"
    enabled: true
    amount: 10.00  # or other config
```

**Lambda deployment** (environment variable):
```json
{"strategies":[{"name":"my_custom","type":"your_strategy","enabled":true}]}
```

---

## Submitting Changes

### Before You Submit

1. **Test locally:**
   ```bash
   cd deployments/local
   python main.py simulate
   ```

2. **Test strategy individually** (if applicable):
   ```bash
   python tests/test_your_strategy.py
   ```

3. **Check code style:**
   - Follow existing patterns
   - Use docstrings for all functions
   - Keep functions focused and clear

### Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-strategy-name
   ```

2. **Make your changes:**
   - Add your strategy to `core/strategies/`
   - Add tests if applicable
   - Update documentation

3. **Commit with clear messages:**
   ```bash
   git add core/strategies/your_strategy.py
   git commit -m "Add your_strategy for X investing"
   ```

4. **Push and create PR:**
   ```bash
   git push origin feature/your-strategy-name
   ```

5. **Describe your changes:**
   - What does the strategy do?
   - How is it configured?
   - Any dependencies or requirements?
   - Example configuration

---

## Areas for Contribution

We welcome contributions in these areas:

### New Strategies

- **Tax-loss harvesting:** Sell losing positions and invest proceeds
- **Momentum investing:** Invest based on stock performance trends
- **Dividend reinvestment:** Auto-reinvest dividends
- **Rebalancing:** Maintain target allocation percentages
- **Custom rules:** User-defined investment triggers

### Improvements

- **Additional brokerages:** Support for other APIs (Robinhood, Webull, etc.)
- **Better error handling:** Graceful degradation and recovery
- **Performance optimization:** Faster execution and lower resource usage
- **Better logging:** Structured logging with levels
- **UI/Dashboard:** Web interface for configuration and monitoring
- **Account Funding:** Automatic funding through ACH to a low-balanced account.

### Documentation

- **More examples:** Real-world strategy configurations
- **Video tutorials:** Setup and usage guides
- **Blog posts:** Strategy explanations and results
- **Translations:** Documentation in other languages

---

## Questions?

- **Issues:** Open an issue on GitHub
- **Discussions:** Start a discussion for feature ideas
- **Email:** Contact the maintainers

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**Thank you for contributing to Micro-Investing Engine!**