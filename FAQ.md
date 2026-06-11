# FAQ and Troubleshooting Guide

Common questions and solutions for the Micro-Investing Engine.

---

## Table of Contents

- [General Questions](#general-questions)
- [Setup Issues](#setup-issues)
- [Alpaca API Issues](#alpaca-api-issues)
- [Strategy Configuration](#strategy-configuration)
- [Transaction Processing](#transaction-processing)
- [Email Notifications](#email-notifications)
- [Cron Automation](#cron-automation)
- [AWS Lambda Deployment](#aws-lambda-deployment)
- [Error Messages](#error-messages)

---

## General Questions

### What's the difference between paper and live trading?

- **Paper trading:** Testing with fake money. Free, no risk, perfect for learning.
- **Live trading:** Real money, real trades. Requires a funded Alpaca account.

**Set in config.yml:**
```yaml
alpaca:
  paper: true   # false for live trading
```

**Note:** Paper and live trading use different API keys!

---

### Do I need paper trading before going live?

**Yes, highly recommended!** Always test with paper trading first to ensure:
- Your strategies work as expected
- Configuration is correct
- You understand the execution timing

---

### How much does this cost to run?

**Local deployment:** $0 (runs on your computer)

**Lambda deployment:** ~$0.00/month
- First 1M requests free (AWS Free Tier)
- Typical usage: 30-100 invocations/month
- S3 storage: pennies per month (optional)

**Alpaca trading:** Commission-free!

---

### Can I run multiple strategies at once?

**Yes!** All enabled strategies calculate independently, then amounts are combined for a single trade execution.

Example:
```yaml
strategies:
  - name: "daily"
    type: scheduled
    enabled: true
    amount: 5.00

  - name: "spare_change"
    type: round_up
    enabled: true
```

Both run, amounts are summed, one trade is executed.

---

## Setup Issues

### ERROR: Missing 'core/' directory

**Problem:** Can't find shared code directory.

**Solution:**
```bash
# Ensure you're in the correct directory
cd /path/to/micro-investing/deployments/local

# Verify core exists
ls ../../core/
# Should show: strategies/, clients/ and engine.py
```

**If core/ is missing:** Clone the full repository again.

---

### ModuleNotFoundError: No module named 'strategies'

**Problem:** Python can't find the core modules.

**Solutions:**

1. **Check your location:**
   ```bash
   pwd
   # Should end with: deployments/local
   ```

2. **Verify core/ exists:**
   ```bash
   ls ../../core/strategies/
   # Should show strategy files
   ```

3. **Run from correct directory:**
   ```bash
   cd /path/to/deployments/local
   python main.py simulate
   ```

---

### setup.py fails to create .env

**Problem:** Permission errors or file system issues.

**Solution:**
```bash
# Check write permissions
ls -la .env 2>/dev/null || echo ".env doesn't exist yet (OK)"

# Create manually if needed
touch .env
chmod 600 .env  # Secure permissions
nano .env  # Add your keys
```

---

## Alpaca API Issues

### Authentication failed / Invalid API keys

**Problem:** API keys are incorrect or expired.

**Solutions:**

1. **Check which keys you're using:**
   ```bash
   # Paper trading uses:
   ALPACA_API_KEY
   ALPACA_SECRET_KEY
   
   # Live trading uses:
   ALPACA_LIVE_API_KEY
   ALPACA_LIVE_SECRET_KEY
   ```

2. **Regenerate keys:**
   - Paper: https://app.alpaca.markets/paper/dashboard/overview
   - Live: https://app.alpaca.markets/dashboard/overview

3. **Verify in .env:**
   ```bash
   grep ALPACA .env
   # Should show your keys (not "your_key_here")
   ```

4. **Test connection:**
   ```bash
   python tests/test_alpaca.py
   ```

---

### Connection timed out

**Problem:** Network issues reaching Alpaca API.

**Solutions:**

1. **Check internet connection:**
   ```bash
   curl -I https://alpaca.markets
   ```

2. **VPN interference:**
   - Disconnect VPN and try again
   - Some VPNs block financial APIs

3. **Firewall blocking:**
   - Allow outbound HTTPS on port 443
   - Whitelist: `*.alpaca.markets`

4. **Alpaca status:**
   - Check: https://status.alpaca.markets

---

### Insufficient funds

**Problem:** Not enough buying power for investment.

**Solution:**

1. **Check your balance:**
   ```bash
   python tests/test_alpaca.py
   # Shows buying power
   ```

2. **Paper trading:**
   - Default: $100,000 paper money
   - Reset account if needed (Alpaca dashboard)

3. **Live trading:**
   - Deposit funds via ACH transfer
   - Takes 4-5 business days to settle

4. **Reduce investment amount:**
   ```yaml
   strategies:
     - name: "daily"
       amount: 1.00  # Lower amount
   ```

---

### Order rejected

**Problem:** Order didn't execute.

**Common causes:**

1. **Market closed:**
   - Stock market hours: 9:30 AM - 4:00 PM ET, Mon-Fri
   - Solution: Schedule trades during market hours

2. **Invalid symbol:**
   - Check ticker symbol is correct
   - Use uppercase: `VOO` not `voo`

3. **Fractional trading not supported:**
   - Most ETFs support fractional shares
   - Some individual stocks don't
   - Solution: Use popular ETFs (VOO, QQQ, VTI, SPY)

4. **Minimum order amount:**
   - Alpaca minimum: $1.00
   - Solution: Increase investment amount

---

## Strategy Configuration

### Strategy not found

**Problem:** `Unknown strategy: your_strategy`

**Solutions:**

1. **Check spelling:**
   ```yaml
   strategies:
     - name: "daily"
       type: scheduled  # Must match exactly
   ```

2. **Verify strategy exists:**
   ```bash
   ls ../../core/strategies/
   # Your strategy file should be listed
   ```

3. **Check class name:**
   ```python
   # File: scheduled.py
   class ScheduledStrategy(BaseStrategy):  # "Scheduled" -> "scheduled"
   ```

---

### Config validation failed

**Problem:** Invalid configuration for strategy.

**Solutions:**

1. **Check required fields:**
   ```yaml
   # Scheduled strategy requires:
   - name: "strategy_name"
     type: scheduled
     enabled: true
     amount: 5.00      # Required
     interval: daily   # Required
     allocation:       # Required
       VOO: 0.60
       QQQ: 0.40
   ```

2. **Allocation must sum to 1.0:**
   ```yaml
   allocation:
     VOO: 0.60  # 60%
     QQQ: 0.40  # 40%
     # Total: 100% ✓
   ```

3. **Valid intervals:**
   - `daily`
   - `weekly`
   - `biweekly`
   - `monthly`

---

### No strategies executed

**Problem:** "No investable amount from strategies"

**Causes:**

1. **All strategies disabled:**
   ```yaml
   strategies:
     - name: "daily"
       enabled: false  # Change to true
   ```

2. **Strategies returned $0:**
   - Check strategy logic
   - Verify input data (transactions CSV, etc.)

3. **Investment below minimum:**
   - Some strategies have `min_daily_investment`
   - Amount must exceed minimum to execute

---

## Transaction Processing

### CSV file not found

**Problem:** Can't find transaction CSV.

**Solution:**
```bash
# Check path in config.yml
cat config.yml | grep csv_file

# Verify file exists
ls -l data/transactions/transactions.csv

# Create if missing
mkdir -p data/transactions
cat > data/transactions/transactions.csv << 'EOF'
date,amount,card,merchant,category
2025-01-15,12.45,Chase Sapphire Preferred,Starbucks,
EOF
```

---

### CSV format errors

**Problem:** "Error parsing CSV" or incorrect processing.

**Required format:**
```csv
date,amount,card,merchant,category
2025-01-15,12.45,Chase Sapphire Preferred,Starbucks,
2025-01-16,89.99,Wells Fargo Active Cash,amazon.com,
```

**Rules:**
- Header row required
- Date format: `YYYY-MM-DD`
- Amount: decimal number (no $ symbol)
- Card: exact name (must be in The Card Caddie account for rewards strategy)
- Merchant: name or domain
- Category: optional (leave empty if unknown)

**Common issues:**

1. **Missing header:**
   ```csv
   # BAD - no header
   2025-01-15,12.45,Card,Merchant,

   # GOOD - has header
   date,amount,card,merchant,category
   2025-01-15,12.45,Card,Merchant,
   ```

2. **Extra quotes:**
   ```csv
   # BAD
   "2025-01-15","12.45","Card","Merchant",""

   # GOOD
   2025-01-15,12.45,Card,Merchant,
   ```

3. **Wrong date format:**
   ```csv
   # BAD
   01/15/2025,12.45,Card,Merchant,

   # GOOD
   2025-01-15,12.45,Card,Merchant,
   ```

---

### The Card Caddie API errors

**Problem:** Reward calculation failing.

**Solutions:**

1. **Check API key:**
   ```bash
   grep THECARDCADDIE_API_KEY .env
   # Should start with "cc_"
   ```

2. **Get API key:**
   - Log in: https://www.thecardcaddie.com
   - Go to: https://www.thecardcaddie.com/profile
   - Click "Generate API Key"
   - Add to `.env`

3. **Card not in account:**
   - Cards must be added to your Card Caddie account
   - Card name in CSV must match EXACTLY
   - Example: "Chase Sapphire Preferred" not "Chase Sapphire"

4. **Test API:**
   ```bash
   python tests/test_thecardcaddie.py
   ```

---

## Email Notifications

### Emails not sending

**Problem:** No notifications received.

**Solutions:**

1. **Check if enabled:**
   ```yaml
   notifications:
     enabled: true  # Must be true
   ```

2. **Verify Gmail setup:**
   - Must use Gmail App Password (not regular password)
   - 2FA must be enabled
   - Generate at: https://myaccount.google.com/apppasswords

3. **Check .env:**
   ```bash
   grep SMTP .env
   SMTP_USER=your@gmail.com
   SMTP_PASSWORD=abcd efgh ijkl mnop  # 16 characters
   ```

4. **Test notifications:**
   ```bash
   python tests/test_notifications.py
   ```

---

### "Login failed" email error

**Problem:** Gmail authentication failing.

**Solutions:**

1. **Use App Password, not regular password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Create new app password
   - Copy 16-character code
   - Paste in `.env` (remove spaces)

2. **Enable 2FA:**
   - Required for App Passwords
   - https://myaccount.google.com/security

3. **Check SMTP settings:**
   ```yaml
   notifications:
     smtp_server: smtp.gmail.com
     smtp_port: 587
   ```

---

## Cron Automation

### Cron job not running

**Problem:** Automated execution not happening.

**Solutions:**

1. **Check cron is installed:**
   ```bash
   which cron || which crond
   # Should show path to cron
   ```

2. **Verify cron entry:**
   ```bash
   crontab -l
   # Should show your entry
   ```

3. **Check full paths:**
   ```cron
   # BAD - relative paths
   0 1 * * * cd deployments/local && python main.py run

   # GOOD - full paths
   0 1 * * * cd /full/path/deployments/local && /usr/bin/python3 main.py run >> /var/log/micro-investing.log 2>&1
   ```

4. **Check logs:**
   ```bash
   tail -f /var/log/micro-investing.log
   # Or wherever you're logging
   ```

5. **Test cron command manually:**
   ```bash
   cd /full/path/deployments/local && /usr/bin/python3 main.py run
   ```

---

### Cron runs but fails

**Problem:** Cron executes but script errors.

**Solutions:**

1. **Environment variables:**
   - Cron doesn't load `.env` by default
   - Solution: Use full path to .env
   ```bash
   cd /path/to/local && source .env && python main.py run
   ```

2. **Python path:**
   - Use full path: `/usr/bin/python3`
   - Find with: `which python3`

3. **Working directory:**
   - Always `cd` to deployment directory first
   - Core imports won't work otherwise

4. **Check cron logs:**
   ```bash
   grep CRON /var/log/syslog  # Ubuntu/Debian
   grep CRON /var/log/cron    # CentOS/RHEL
   ```

---

## AWS Lambda Deployment

### Build script fails

**Problem:** `./build.sh` errors.

**Solutions:**

1. **Make executable:**
   ```bash
   chmod +x build.sh
   ./build.sh
   ```

2. **Install pip packages:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check core/ exists:**
   ```bash
   ls ../../core/
   # Must exist for build
   ```

---

### Lambda handler not found

**Problem:** "Cannot find module 'lambda_function'"

**Solution:**

1. **Check handler configuration:**
   ```
   Handler: lambda_function.lambda_handler
   ```

2. **Verify package structure:**
   ```bash
   unzip -l lambda-deployment.zip | grep lambda_function.py
   # Should be at root of zip
   ```

---

### Lambda timeout

**Problem:** Function times out before completing.

**Solutions:**

1. **Increase timeout:**
   - Default: 3 seconds
   - Increase to: 60-120 seconds
   - Lambda Configuration -> General -> Timeout

2. **Optimize strategy:**
   - Reduce transaction processing
   - Limit API calls

---

### Environment variables not set

**Problem:** "API keys not configured"

**Solution:**

1. **Add environment variables in Lambda:**
   - Configuration -> Environment variables
   - Add all required keys:
     - `ALPACA_API_KEY`
     - `ALPACA_SECRET_KEY`
     - `THECARDCADDIE_API_KEY` (if using)

2. **Use AWS Secrets Manager (advanced):**
   - Store keys securely
   - Grant Lambda access

---

## Error Messages

### "This is the first run. Please run setup.py"

**Solution:**
```bash
python setup.py
```

---

### "No 'strategies' defined in config.yml"

**Problem:** Config file is empty or malformed.

**Solution:**
```bash
# Copy example config
cp config.example.yml config.yml

# Or run setup again
python setup.py
```

---

### "Paper keys will NOT work with live trading"

**Problem:** Trying to use paper trading keys for live trading.

**Solution:**
- Generate separate live trading keys
- Add to `.env` as `ALPACA_LIVE_API_KEY` and `ALPACA_LIVE_SECRET_KEY`
- Set `paper: false` in config.yml

---

### "Failed to import from core/"

**Problem:** Core modules missing or corrupted.

**Solution:**
```bash
# Verify core directory
ls ../../core/strategies/
ls ../../core/clients/

# If missing, re-clone repository
git clone https://github.com/your-repo/micro-investing.git
```

---

## Still Having Issues?

### Enable Debug Logging

1. **In config.yml:**
   ```yaml
   execution:
     log_level: DEBUG  # More verbose
   ```

2. **Run with output:**
   ```bash
   python main.py run 2>&1 | tee debug.log
   ```

### Get Help

1. **Check existing issues:**
   - https://github.com/your-repo/micro-investing/issues

2. **Open new issue:**
   - Include error message
   - Include relevant config (remove API keys!)
   - Include Python version: `python --version`
   - Include OS: `uname -a` (Linux/Mac) or `systeminfo` (Windows)

3. **Provide context:**
   - What were you trying to do?
   - What did you expect to happen?
   - What actually happened?
   - Steps to reproduce

---

## Quick Reference

### Test Everything

```bash
# Test Alpaca connection
python tests/test_alpaca.py

# Test Card Caddie API
python tests/test_thecardcaddie.py

# Test email notifications
python tests/test_notifications.py

# Full simulation
python main.py simulate
```

### Common File Locations

```
deployments/local/
├── .env                    # Your API keys
├── config.yml              # Your configuration
├── data/
│   ├── transactions/       # Input transaction CSVs
│   └── ledger/             # Output investment logs
└── tests/                  # Test scripts
```

### Useful Commands

```bash
# View recent investments
tail data/ledger/ledger.csv

# Check cron schedule
crontab -l

# Test cron command manually
cd /path/to/local && python main.py run

# View Alpaca positions
python tests/test_alpaca.py

# Validate config syntax
python -c "import yaml; yaml.safe_load(open('config.yml'))"
```

---

**Can't find your issue? Open a GitHub issue or discussion!**