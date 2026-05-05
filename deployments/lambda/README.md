# AWS Lambda Deployment

Serverless micro-investing engine that runs on AWS Lambda.

---

## Quick Start

1. **Build deployment package:**
   ```bash
   ./build.sh
   ```

2. **Create Lambda function** and upload `lambda-deployment.zip`

3. **Configure environment variables** (see below)

4. **Add S3 permissions** (for state/ledger storage)

5. **Set up triggers:**
   - EventBridge for scheduled runs
   - API Gateway for real-time transaction processing

---

## 1. Build Deployment Package

```bash
cd deployments/lambda
./build.sh
```

This creates `lambda-deployment.zip` (~10-15 MB).

---

## 2. Create Lambda Function

1. Go to [AWS Lambda Console](https://console.aws.amazon.com/lambda)
2. Click **Create function**
3. Configure:
   - **Name:** `micro-investing-engine`
   - **Runtime:** Python 3.9+
   - **Architecture:** x86_64

4. **Upload code:**
   - Code tab → **Upload from** → **.zip file**
   - Select `lambda-deployment.zip`

5. **Configure settings:**
   - **Handler:** `lambda_function.lambda_handler` (should be default)
   - **Timeout:** 30 seconds
   - **Memory:** 256 MB

---

## 3. Environment Variables

Set in: **Configuration → Environment variables**

### Required

```bash
# Alpaca API
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_PAPER=true  # Set to "false" for live trading (REAL MONEY)
```

### Optional (but recommended)

```bash
# S3 bucket for data storage (REQUIRED for scheduled strategies!)
STATE_S3_BUCKET=my-micro-investing       # Stores state in /state folder
S3_LEDGER_BUCKET=my-micro-investing      # Stores ledger in /ledger folder

# The Card Caddie API (for credit_card_rewards strategy)
THECARDCADDIE_API_KEY=cc_your_key_here

# Strategy config (for EventBridge scheduled runs only)
# See "Strategy Configuration" section below
STRATEGY_CONFIG={"strategies":[...]}
```

**Recommendation:** Use a **single S3 bucket** with separate folders for state and ledger. This simplifies management and reduces costs.

**Important:** If using scheduled strategies (daily/weekly investments via EventBridge), you **MUST** set `STATE_S3_BUCKET` to track when strategies last ran. Without it, the strategy will execute every time Lambda runs!

---

## 4. Add S3 Permissions

Required if using `STATE_S3_BUCKET` or `S3_LEDGER_BUCKET`.

### Create S3 Bucket

**Recommended:** Use a single bucket with separate folders for state and ledger:

### Add IAM Permissions

1. Go to Lambda → **Configuration** → **Permissions**
2. Click the **Execution role** name (opens IAM)
3. Click **Add permissions** → **Create inline policy**
4. Switch to **JSON** tab and paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-micro-investing/*"
    }
  ]
}
```

5. Click **Review policy**
6. Name: `MicroInvestingS3Policy`
7. Click **Create policy**

**⚠️ Replace `my-micro-investing`** with your actual bucket name!

### Set Environment Variables

Both should point to the **same bucket**:
```bash
STATE_S3_BUCKET=my-micro-investing
S3_LEDGER_BUCKET=my-micro-investing
```

The Lambda function automatically stores:
- State files in: `s3://my-micro-investing/state/`
- Ledger files in: `s3://my-micro-investing/ledger/`

---

## 5. Set Up Triggers

Choose one or both:

### Option A: EventBridge (Scheduled Runs)

For automated daily/weekly investing.

1. Lambda → **Configuration** → **Triggers** → **Add trigger**
2. Select **EventBridge (CloudWatch Events)**
3. Create new rule:
   - **Name:** `daily-investment`
   - **Schedule expression:** `cron(0 1 * * ? *)`  *(1 AM UTC daily)*
4. Click **Add**

**Common schedules:**
- Daily: `cron(0 1 * * ? *)`
- Weekly: `cron(0 1 ? * MON *)`
- Monthly: `cron(0 1 1 * ? *)`

**Note:** Scheduled strategies are configured via the `STRATEGY_CONFIG` environment variable (see below).

---

### Option B: API Gateway (Real-Time Transactions)

For processing transactions on-demand (credit card rewards, round-up, etc.).

#### Step 1: Create API Gateway

1. Lambda → **Configuration** → **Triggers** → **Add trigger**
2. Select **API Gateway**
3. Configure:
   - **Intent:** Create a new API
   - **API type:** REST API
   - **Security:** Open *(or API key for production)*
4. Click **Add**
5. **Copy the API endpoint URL** (you'll need this!)

#### Step 2: Set API Gateway Permissions

**For Open API (no auth):**
- No additional setup needed
- ⚠️ **Not recommended for production!** Anyone with the URL can call it.

**For API Key (recommended):**

1. After creating the trigger, click **View additional settings in API Gateway**
2. Go to **API Keys** in sidebar → **Create API Key**
   - Name: `micro-investing-key`
   - Save and copy the key
3. Go to **Usage Plans** → Select the auto-created plan
4. Click **Add API Key to Usage Plan** → Select your key
5. Click **Actions** → **Deploy API** → Stage: `default`

#### Step 3: Test Your API

```bash
# Without API key (if security = Open)
curl -X POST https://YOUR_API_URL/default/YOUR_FUNCTION_NAME \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "credit_card_rewards",
    "transactions": [
      {
        "date": "2025-01-15",
        "amount": 12.45,
        "card": "Chase Sapphire Preferred",
        "merchant": "Starbucks",
        "category": "Dining"
      }
    ],
    "allocation": {"VTI": 1.0}
  }'

# With API key
curl -X POST https://YOUR_API_URL/default/YOUR_FUNCTION_NAME \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{...}'
```

---

## Strategy Configuration

### EventBridge (Scheduled Strategies)

For scheduled strategies triggered by EventBridge, configure via the `STRATEGY_CONFIG` environment variable:

```json
{
  "strategies": [
    {
      "name": "daily_investment",
      "type": "scheduled",
      "enabled": true,
      "amount": 10.0,
      "interval": "daily",
      "allocation": {
        "VOO": 0.6,
        "QQQ": 0.4
      }
    }
  ]
}
```

**Minified (for Lambda env var):**
```
{"strategies":[{"name":"daily_investment","type":"scheduled","enabled":true,"amount":10.0,"interval":"daily","allocation":{"VOO":0.6,"QQQ":0.4}}]}
```

---

### API Gateway (Transaction-Based Strategies)

For strategies triggered via API Gateway POST requests:

#### Auto-Detection

The Lambda function will **auto-detect** the strategy type based on transaction data:
- **Has `card` field?** → Uses `credit_card_rewards`
- **No `card` field?** → Uses `round_up`

```json
{
  "transactions": [
    {
      "date": "2025-01-15",
      "amount": 12.45,
      "card": "Chase Sapphire Preferred",
      "merchant": "Starbucks"
    }
  ],
  "allocation": {"VTI": 1.0}
}
```
*Auto-detected as `credit_card_rewards` because of `card` field.*

#### Explicit Strategy

You can also explicitly specify the strategy:

```json
{
  "strategy": "round_up",
  "transactions": [
    {"date": "2025-01-15", "amount": 23.45},
    {"date": "2025-01-15", "amount": 67.89}
  ],
  "allocation": {"VOO": 0.6, "QQQ": 0.4}
}
```

#### Custom Strategies (No Transactions)

**Note:** The `config` parameter is for **non-transactional** strategies. Transaction-based strategies (`round_up`, `credit_card_rewards`) use the top-level `transactions` and `allocation` fields.

---

## API Reference

### Endpoint

```
POST https://your-api-gateway-url.amazonaws.com/default/your-function-name
```

### Headers

```
Content-Type: application/json
x-api-key: your-api-key  # If API key is enabled
```

### Request Body

**Transaction-based (credit card rewards):**
```json
{
  "strategy": "credit_card_rewards",  // Optional (auto-detected from 'card' field)
  "transactions": [
    {
      "date": "2025-01-15",
      "amount": 50.0,
      "card": "Chase Sapphire Preferred",
      "merchant": "Whole Foods",
      "category": "Groceries"
    }
  ],
  "allocation": {
    "VTI": 1.0
  }
}
```

### Response

**Success:**
```json
{
  "message": "Investment executed successfully",
  "amount": 1.25,
  "allocation": {
    "VTI": 1.25
  },
  "orders": [
    {
      "symbol": "VTI",
      "notional": 1.25,
      "status": "submitted",
      "order_id": "abc123..."
    }
  ]
}
```

**Error:**
```json
{
  "error": "Insufficient funds: need $10.00, have $5.00"
}
```

---

## Monitoring

### CloudWatch Logs

All executions log to CloudWatch automatically.

**View logs:**
1. Go to [CloudWatch Console](https://console.aws.amazon.com/cloudwatch)
2. Navigate to **Logs** → **Log groups**
3. Find `/aws/lambda/micro-investing-engine`

**Logs include:**
- Strategy execution details
- Investment amounts and orders
- Errors and warnings
- Ledger entries (JSON)

### CloudWatch Metrics

Monitor:
- **Invocations:** Number of executions
- **Duration:** Execution time
- **Errors:** Failed invocations

---

## Troubleshooting

### "Unknown event source" error

**Cause:** Lambda can't detect how it was invoked.

**Solution:** Ensure you're using a supported trigger:
- EventBridge (scheduled)
- API Gateway REST API
- API Gateway HTTP API
- Direct invocation (for testing)

### "Unknown strategy" error

**Cause:** Strategy type not specified or auto-detected.

**Solution:**
- For credit card rewards: Include `"card"` field in transactions
- For round up: Use transactions without `"card"` field
- Or explicitly set `"strategy": "round_up"` in request body

### S3 access denied

**Cause:** Lambda doesn't have S3 permissions.

**Solution:** Follow [Add S3 Permissions](#4-add-s3-permissions) section above.

### API Gateway 403 Forbidden

**Cause:** Missing or invalid API key.

**Solution:**
1. Get your API key from API Gateway console
2. Include header: `-H "x-api-key: YOUR_KEY"`
3. Or temporarily set Security to "Open" for testing

### Insufficient funds

**Cause:** Not enough buying power in Alpaca account.

**Solution:**
- Paper trading: Alpaca provides $100k automatically
- Live trading: Add funds to your account
- Check you're using the correct API keys (`ALPACA_PAPER` setting)

---

## Cost Estimate

**Daily scheduled investment:**
- ~30 executions/month
- ~$0.0003/month (basically free)
- Well within AWS free tier

**With S3 storage:**
- ~$0.01-0.05/month (ledger files are tiny)

**Total:** Under $1/month for most users.

---

## Security Notes

- **Never commit API keys** to version control
- **Use API keys** for production API Gateway endpoints
- **Test in paper mode** before switching to live trading
- **Monitor CloudWatch** for suspicious activity

---

## Support

- Main README: [/micro-investing/README.md](../../README.md)
- The Card Caddie: https://www.thecardcaddie.com
- Alpaca Trading: https://alpaca.markets

---

**Ready to deploy?** Run `./build.sh` and follow the steps above! 🚀
