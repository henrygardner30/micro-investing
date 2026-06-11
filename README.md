<a href="https://www.thecardcaddie.com">
  <img src="assets/images/logo.png" alt="The Card Caddie Logo" width="40" align="left" style="margin-right: 15px;" />
</a>

# Micro-Investing Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Powered by Alpaca](https://img.shields.io/badge/Powered%20by-Alpaca-00C896)](https://alpaca.markets)
<a href="https://www.thecardcaddie.com"><img src="assets/images/logo.png" alt="Powered by The Card Caddie" height="20" /></a>

Invest your credit card rewards into the stock market, automatically. Supports other micro-investing strategies using Alpaca and fractional trading. This also serves as an introductory repo for programatic investing.

Project by [thecardcaddie.com](https://www.thecardcaddie.com).

<br clear="left"/>

## Getting Started

**Simple Setup (Recommended):**

```bash
./build.sh
```

This interactive script guides you through setup for either local or Lambda deployment.

---

**Or choose your deployment method manually:**

1. **For local deployment (run on your computer):**
   ```bash
   cd deployments/local/
   python setup.py
   ```

2. **For serverless deployment (AWS Lambda):**
   ```bash
   cd deployments/lambda/
   ./build.sh
   # Then follow lambda/README.md for AWS setup
   ```

**Not sure which to choose?**
- Local = Full control, runs on your machine, use cron for automation
- Lambda = Serverless, pay-per-execution, minimal setup, AWS handles everything

---

## Project Structure

```
micro-investing/
├── build.sh                       # Main build script (START HERE!)
├── core/                          # Shared code: orchestration, strategies, API clients
│   ├── engine.py                  # Shared orchestrator (build_plan / execute_plan)
│   ├── strategies/                # Investment strategies (add new ones here)
│   │   ├── base.py                # Abstract base class
│   │   ├── scheduled.py           # Example: scheduled investing
│   │   ├── round_up.py            # Example: round-up investing
│   │   └── credit_card_rewards.py # Example: credit card rewards investing
│   └── clients/                   # API clients
│       ├── alpaca.py              # Alpaca trading (uses REST API directly)
│       └── thecardcaddie.py       # The Card Caddie rewards calculator
│
├── deployments/
│   ├── local/                     # Local deployment
│   │   ├── main.py                # Entry point for local execution
│   │   ├── setup.py               # Interactive setup wizard
│   │   ├── requirements.txt       # Python dependencies
│   │   ├── tests/                 # Unit tests (pytest)
│   │   └── src/utils/             # Local-specific utilities
│   └── lambda/                    # AWS Lambda deployment
│       ├── lambda_function.py     # Lambda handler
│       ├── build.sh               # Lambda build script
│       ├── requirements.txt       # Lambda dependencies
│       └── utils/                 # Lambda-specific utilities
│
├── assets/                        # Images and static assets
│   └── images/                    # Logo and graphics
├── README.md                      # Main documentation
├── CONTRIBUTING.md                # Contributing guide
└── FAQ.md                         # Troubleshooting guide
```

### How It Works

All the investing logic lives in the shared engine (`core/engine.py`), so local
and Lambda behave identically:

1. **`build_plan`** runs every enabled strategy — validating each config,
   computing its investable amount, applying `min`/`max` daily limits, and
   combining the per-symbol allocations into a single plan.
2. **`execute_plan`** checks your Alpaca buying power, places the fractional
   orders (skipped in `simulate` mode), and records the run for stateful
   strategies (e.g. scheduled) — only after a real execution succeeds.

The deployment layers (`deployments/local/main.py` and
`deployments/lambda/lambda_function.py`) are thin adapters: they load
configuration and credentials, then handle logging, the ledger, and
notifications around those two engine calls.

---

## Deployment Options

### Local Deployment

**Best for:** Full control, cron jobs, local automation

- Runs on your computer or server
- Complete customization via config.yml
- Email notifications
- Multiple strategies simultaneously
- Transaction CSV processing

**Quick start:**
```bash
cd deployments/local/
python setup.py
python main.py simulate
```

**Documentation:** [deployments/local/README.md](deployments/local/README.md)

---

### AWS Lambda Deployment

**Best for:** Serverless, pay-per-execution, zero maintenance

- Automated cloud investing
- Approximately $0.00/month (depending on usage)
- No server management
- EventBridge scheduling or API Gateway triggers
- S3 ledger storage (optional)

**Quick start:**
```bash
cd deployments/lambda/
./build.sh
# Upload lambda-deployment.zip to AWS
```

**Documentation:** [deployments/lambda/README.md](deployments/lambda/README.md)

---

## Investment Strategies

Three built-in strategies (work in both deployments):

### 1. Scheduled Investment
Invest a fixed amount at regular intervals (daily, weekly, biweekly, monthly).

**Example:**
```yaml
strategies:
  - name: "daily_investment"
    type: scheduled
    amount: 5.00
    interval: daily
    allocation:
      VOO: 0.60
      QQQ: 0.40
```

### 2. Round Up
Round transactions to nearest dollar and invest the difference.

**Example:** $4.32 coffee = $0.68 invested

### 3. Credit Card Rewards
Invest based on credit card rewards percentages using The Card Caddie API.

**Example:** 3% back on dining = invest 3% of dining purchases

---

## Creating Custom Strategies

Create your own strategy by extending the base class in `core/strategies/`:

```python
# core/strategies/my_strategy.py
from .base import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("my_strategy")
    
    def supports_transactions(self):
        # True if strategy processes transaction data, False if config-based
        return False
    
    def calculate_investable_amount(self, config):
        # Your logic here
        amount = 10.0
        details = [{"info": "example"}]
        return (amount, details)
    
    def calculate_allocation(self, amount, config):
        # Split investment across stocks
        return {'VOO': amount * 0.6, 'QQQ': amount * 0.4}
    
    def validate_config(self, config):
        # Validate configuration
        return True

    # Optional: persist state only after a real execution succeeds.
    # Override this if your strategy must not repeat on simulate/failed runs.
    def commit_run(self, config):
        pass
```

The engine calls `commit_run` only after trades actually execute (never in
`simulate` mode or on insufficient funds), so stateful strategies advance
exactly once per real run. Stateless strategies can omit it.

**Use in local deployment:**
```yaml
# config.yml
strategies:
  - name: "my_custom"
    type: my_strategy
    enabled: true
```

**Use in Lambda deployment:**
Set as environment variable or pass via API Gateway.

---

## Requirements

- Python 3.8+
- Alpaca account (free paper trading or paid live trading)
- Optional: The Card Caddie API key (for credit card rewards strategy)
- Optional: Gmail account (for email notifications, local only)

---

## Documentation

### Deployment Guides
- **Local Deployment Guide:** [deployments/local/README.md](deployments/local/README.md)
- **Lambda Deployment Guide:** [deployments/lambda/README.md](deployments/lambda/README.md)

### Source Code
- **Engine (orchestration):** [core/engine.py](core/engine.py)
- **Strategy Source Code:** [core/strategies/](core/strategies/)
- **API Clients Source Code:** [core/clients/](core/clients/)

### Community & Support
- **FAQ & Troubleshooting:** [FAQ.md](FAQ.md) - Common issues and solutions
- **Contributing Guide:** [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute to this project
- **Security Policy:** [SECURITY.md](SECURITY.md) - Report vulnerabilities and security best practices

---

## Related Links

- **The Card Caddie:** [thecardcaddie.com](https://www.thecardcaddie.com) - Credit card rewards optimizer
- **Alpaca Markets:** [alpaca.markets](https://alpaca.markets) - Commission-free stock trading API

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

---

**Ready to start?** Choose your deployment and follow the setup guide!