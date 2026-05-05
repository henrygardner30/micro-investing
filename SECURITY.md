# Security Policy

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please report it privately:

1. **Email:** Send details to the maintainers via The Card Caddie contact form at https://www.thecardcaddie.com
2. **Subject Line:** Use "SECURITY: Micro-Investing Engine" in the subject
3. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)

### API Keys & Credentials

- **Never commit** API keys to version control
- Use the `.env` file for all sensitive credentials
- Rotate API keys regularly (every 90 days recommended)
- Use paper trading keys for testing, separate live trading keys for production
- Keep your `.env` file permissions restricted: `chmod 600 .env`

### Paper Trading First

- **Always test with paper trading** before using real money
- Verify all strategies work as expected in simulation mode
- Paper trading uses fake money and separate API keys from live trading

### AWS Lambda Security

If deploying to Lambda:
- Use AWS Secrets Manager or Parameter Store for production credentials
- Enable API Gateway authentication (API keys minimum, IAM auth recommended)
- Set appropriate IAM permissions (least privilege principle)
- Enable CloudWatch logging for audit trails
- Use VPC endpoints if accessing private resources

### Local Deployment Security

- Run the engine on a secure, trusted machine
- Keep Python and dependencies up to date
- Use virtual environments to isolate dependencies
- Review cron logs regularly for suspicious activity
- Secure your transaction CSV files (they contain financial data)

### Network Security

- Only use HTTPS endpoints (never HTTP)
- Verify SSL certificates are valid
- Be cautious of man-in-the-middle attacks on public Wi-Fi
- Consider using a VPN for additional security

## Known Security Considerations

### API Rate Limiting

The current implementation does not include rate limiting for external API calls. Heavy usage may trigger rate limits from:
- Alpaca Markets API
- The Card Caddie API

**Mitigation:** Use reasonable transaction volumes and avoid rapid repeated executions.

### Transaction Data Privacy

Transaction CSV files contain sensitive financial information:
- Keep CSV files in `.gitignore` directories
- Don't share transaction data publicly
- Securely delete old transaction files
- Consider encrypting CSV files at rest

### Alpaca API Permissions

The Alpaca API keys used have full trading permissions:
- They can execute real trades with real money (if using live keys)
- Protect these keys as you would protect cash
- Never share or expose these keys
- Revoke and regenerate if compromised

## Dependency Security

We use minimal dependencies to reduce attack surface:
- `python-dotenv`: Environment variable management
- `PyYAML`: Configuration parsing
- `requests`: HTTP client for API calls

### Keeping Dependencies Updated

Check for security updates regularly:
```bash
pip list --outdated
pip install --upgrade python-dotenv PyYAML requests
```

Consider using tools like:
- `pip-audit` for vulnerability scanning
- Dependabot for automated dependency updates
- `safety` for known vulnerability checks

## Out of Scope

The following are **not** considered security vulnerabilities:

- Issues that require physical access to the user's machine
- Social engineering attacks
- Issues in third-party APIs (Alpaca, The Card Caddie) - report those to the respective services
- Losses due to incorrect strategy configuration (this is user responsibility)
- Market volatility or investment losses (inherent to trading)
- Issues in dependencies (report to upstream projects)

## Responsible Disclosure

We follow responsible disclosure principles:

1. **Report privately** to allow time for a fix
2. **Coordinate** disclosure timing with maintainers
3. **Avoid exploitation** of discovered vulnerabilities
4. **Allow time** for users to update (typically 90 days)

## Security Updates

Security updates will be:
- Released as soon as possible after verification
- Announced in GitHub Releases with `[SECURITY]` tag
- Documented with CVE IDs if applicable
- Backported to supported versions if critical

## Questions?

If you have questions about security but haven't found a vulnerability, feel free to:
- Open a GitHub Discussion
- Ask in a GitHub Issue (for non-sensitive topics)
- Contact the maintainers

---

**Thank you for helping keep the Micro-Investing Engine secure!**

