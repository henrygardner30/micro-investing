# Micro-Investing Engine - Local Deployment

Automatically invest in ETFs using Alpaca fractional trading. This local deployment gives you full control over where and how your investing engine runs.

---

## Why Local Deployment?

- **Full Control:** Run on your computer, server, or Raspberry Pi
- **Cron Automation:** Schedule with cron jobs for automatic daily/weekly investing
- **Multiple Strategies:** Run several investment strategies simultaneously
- **Email Notifications:** Get alerts for investments and errors
- **Transaction Processing:** Process CSV files with purchase history
- **Maximum Customization:** Edit config.yml for unlimited flexibility

**Looking for serverless?** See [../lambda/README.md](../lambda/README.md) for AWS Lambda deployment.

---

## Quick Start

### 1. Install and Setup

```bash
# Navigate to local deployment
cd deployments/local/

# Run interactive setup (creates .env and config.yml)
python setup.py

# Test with simulation (no real trades)
python main.py simulate
```

### 2. Execute Investments

```bash
# Run once (executes configured strategies)
python main.py run

# Or simulate first to verify
python main.py simulate
```

### 3. Automate with Cron (Optional)

```bash
# Open cron editor
crontab -e

# Add line to run daily at 1 AM
0 1 * * * cd /full/path/to/deployments/local && /usr/bin/python3 main.py run >> /var/log/micro-investing.log 2>&1
```

More cron examples below.

---

## Requirements

- **Python 3.8+**
- **Alpaca Account:**
  - Paper trading (free): [alpaca.markets/paper](https://app.alpaca.markets/paper/dashboard/overview)
  - Live trading (real money): [alpaca.markets](https://app.alpaca.markets/dashboard/overview)
- **Optional: The Card Caddie API key** (only for credit_card_rewards strategy)
  - Get at [thecardcaddie.com/profile](https://www.thecardcaddie.com/profile)
  - Note: Cards must be added to your Card Caddie account
- **Optional: Gmail** (for email notifications)

---

## Installation

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Run Setup Wizard

```bash
python setup.py
```

The setup wizard will:
- Create `.env` file with your API keys
- Generate `config.yml` with your chosen strategies
- Test connection to Alpaca
- Run a simulation

### Step 3: Customize (Optional)

Edit `config.yml` to adjust:
- Investment amounts
- Asset allocation
- Strategy parameters
- Notification settings

---

## Investment Strategies

### 1. Scheduled Investment

Invest a fixed amount at regular intervals. **Default strategy** - no transaction data needed.

**Configuration:**
```yaml
strategies:
  - name: "daily_investment"
    type: scheduled
    enabled: true
    amount: 5.00
    interval: daily  # Options: daily, weekly, biweekly, monthly
    allocation:
      VOO: 0.60      # 60% Vanguard S&P 500
      QQQ: 0.40      # 40% Invesco QQQ
```

**Perfect for:** Dollar-cost averaging, simple automated investing

---

### 2. Round Up

Round each transaction to the nearest dollar and invest the difference.

**Configuration:**
```yaml
strategies:
  - name: "spare_change"
    type: round_up
    enabled: true
    csv_file: data/transactions/transactions.csv
    min_daily_investment: 1.00
    max_daily_investment: 50.00
    allocation:
      VOO: 1.00
```

**Example:** $4.32 coffee = $0.68 invested

**Requires:** Transaction CSV file (format: date, amount, card, merchant, category)

---

### 3. Credit Card Rewards

Invest based on your credit card rewards percentages using The Card Caddie API.

**Configuration:**
```yaml
strategies:
  - name: "rewards"
    type: credit_card_rewards
    enabled: true
    csv_file: data/transactions/transactions.csv
    min_daily_investment: 1.00
    max_daily_investment: 100.00
    allocation:
      VTI: 1.00
```

**Example:** 3% back on dining = invest 3% of dining purchases

**Requires:**
- The Card Caddie API key
- Credit cards added to your Card Caddie account
- Transaction CSV file

---

## Configuration Reference

### config.yml Structure

```yaml
# Investment Strategies (can run multiple simultaneously)
strategies:
  - name: "strategy_name"
    type: scheduled  # or: round_up, credit_card_rewards
    enabled: true
    # ... strategy-specific settings

# Transaction Data (for round_up and credit_card_rewards)
transactions:
  csv_file: data/transactions/transactions.csv

# The Card Caddie API (only for credit_card_rewards strategy)
api:
  base_url: https://www.thecardcaddie.com
  key: ${THECARDCADDIE_API_KEY}

# Alpaca Brokerage
alpaca:
  api_key: ${ALPACA_API_KEY}
  secret_key: ${ALPACA_SECRET_KEY}
  paper: true  # false for live trading with real money

# Execution Settings
execution:
  ledger_file: data/ledger/ledger.csv
  log_level: INFO

# Email Notifications (optional)
notifications:
  enabled: false
  email_to: your@email.com
  smtp_server: smtp.gmail.com
  smtp_port: 587
  smtp_user: ${SMTP_USER}
  smtp_password: ${SMTP_PASSWORD}
```

---

## Transaction CSV Format

For `round_up` and `credit_card_rewards` strategies, provide transactions in this format:

**File:** `data/transactions/transactions.csv`

```csv
date,amount,card,merchant,category
2025-01-15,12.45,Chase Sapphire Preferred,Starbucks,
2025-01-15,89.99,Wells Fargo Active Cash,amazon.com,
2025-01-17,67.89,Fidelity Rewards,Target,Shopping
```

**Notes:**
- `category` is optional (system will look up merchant category if blank)
- Merchants can be names or domains
- One hard-to-identify merchant (like "Target") should include category

---

## Automation with Cron

### Get Your Full Path

```bash
cd /path/to/deployments/local
pwd  # Copy this output
```

### Open Cron Editor

```bash
crontab -e
```

### Add Cron Job

**Daily at 1 AM:**
```cron
0 1 * * * cd /your/full/path/deployments/local && /usr/bin/python3 main.py run >> /var/log/micro-investing.log 2>&1
```

**Daily at 9 AM:**
```cron
0 9 * * * cd /your/full/path/deployments/local && /usr/bin/python3 main.py run >> /var/log/micro-investing.log 2>&1
```

**Weekly on Monday at 1 AM:**
```cron
0 1 * * 1 cd /your/full/path/deployments/local && /usr/bin/python3 main.py run >> /var/log/micro-investing.log 2>&1
```

**Monthly on 1st at 1 AM:**
```cron
0 1 1 * * cd /your/full/path/deployments/local && /usr/bin/python3 main.py run >> /var/log/micro-investing.log 2>&1
```

**Cron Format:** `minute hour day month weekday command`

### Save and Exit

- **nano:** Ctrl+X, then Y, then Enter
- **vim:** Press Esc, type `:wq`, press Enter

---

## Email Notifications

Get notified about investment executions and errors.

### Setup

1. **Use Gmail App Password** (not your regular password)
   - Go to: https://myaccount.google.com/apppasswords
   - Generate 16-digit app password

2. **Add to .env:**
   ```bash
   SMTP_USER=your@gmail.com
   SMTP_PASSWORD=your_16_digit_app_password
   ```

3. **Enable in config.yml:**
   ```yaml
   notifications:
     enabled: true
     email_to: your@email.com
     smtp_server: smtp.gmail.com
     smtp_port: 587
     smtp_user: ${SMTP_USER}
     smtp_password: ${SMTP_PASSWORD}
   ```

### Notification Events

- Investment executed successfully
- Insufficient funds warning
- Strategy errors or failures

---

## Testing

Test your setup before executing real trades:

### Test Alpaca Connection

```bash
python tests/test_alpaca.py
```

### Test The Card Caddie API

```bash
python tests/test_thecardcaddie.py
```

### Test Email Notifications

```bash
python tests/test_notifications.py
```

### Simulate Investment Run

```bash
python main.py simulate
```

This shows what would happen without executing trades.

---

## File Structure

```
deployments/local/
├── main.py                    # Main entry point
├── setup.py                   # Interactive setup wizard
├── config.yml                 # Your configuration
├── config.example.yml         # Example configuration
├── requirements.txt           # Python dependencies
├── .env                       # API keys (you create this)
├── data/
│   ├── transactions/          # Your transaction CSVs
│   └── ledger/                # Investment history logs
├── tests/                     # Test scripts
└── src/
    └── utils/                 # Local-specific utilities
```

---

## Troubleshooting

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'strategies'`

**Fix:** The `core/` directory is missing. Ensure you cloned the full repo:
```bash
cd ../..  # Go to repo root
ls core/  # Should show strategies/, clients/ and engine.py
```

### API Key Issues

**Error:** `API keys not found in .env`

**Fix:** Run setup again:
```bash
python setup.py
```

### CSV Format Issues

**Error:** Transaction processing fails

**Fix:** Ensure CSV has headers and correct format:
```csv
date,amount,card,merchant,category
2025-01-15,12.45,Card Name,Merchant,
```

---

## Creating Custom Strategies

See the main README for full guide: [../../README.md](../../README.md)

**Quick example:**

1. Create `core/strategies/my_strategy.py`
2. Extend `BaseStrategy` class
3. Implement required methods
4. Add to `config.yml`

Your strategy will automatically be registered and available!

---

## Comparing to Lambda Deployment

| Feature | Local | Lambda |
|---------|-------|--------|
| Setup Complexity | Medium | High |
| Ongoing Costs | $0 (your computer) | ~$0.30/month |
| Maintenance | You manage | AWS manages |
| Customization | Maximum | High |
| Transaction Processing | CSV files | API Gateway |
| Notifications | Email (SMTP) | Email or S3 logs |
| Best For | Full control, learning | Set and forget |

---

## Next Steps

1. Run `python setup.py` if you haven't
2. Test with `python main.py simulate`
3. When ready: `python main.py run`
4. Set up cron for automation
5. Check `data/ledger/ledger.csv` for history

---

## Need Help?

- **Lambda deployment:** [../lambda/README.md](../lambda/README.md)
- **Main project docs:** [../../README.md](../../README.md)
- **Strategy source code:** [../../core/strategies/](../../core/strategies/)
- **The Card Caddie:** [thecardcaddie.com](https://www.thecardcaddie.com)
- **Alpaca API docs:** [alpaca.markets/docs](https://alpaca.markets/docs)

---

**Happy investing!**
