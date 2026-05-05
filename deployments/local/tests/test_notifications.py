"""
Test script for notification system.

Tests email notifications for investment events.

Usage:
    python tests/test_notifications.py
    python tests/test_notifications.py --test-email
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'core'))

from src.utils import NotificationManager, load_config

load_dotenv()

def test_configuration():
    """
    Function to check if notification configuration is set up correctly.
    Returns True if configured, False otherwise.
    
    @PARAMS: None
    """
    print("=" * 80)
    print("NOTIFICATION CONFIGURATION CHECK")
    print("=" * 80)
    print()
    
    config = load_config('config.yml')
    notifier = NotificationManager(config)
    
    print(f"Notifications Enabled: {notifier.enabled}")
    print(f"Email Address: {notifier.email_to}")
    print()
    
    if not notifier.enabled:
        print("[NOT CONFIGURED] Notifications are disabled")
        print()
        print("To enable:")
        print("  1. Edit config.yml:")
        print("     notifications:")
        print("       enabled: true")
        print("       email_to: your@email.com")
        print()
        print("  2. Set up email credentials in .env:")
        print("     SMTP_USER=your@gmail.com")
        print("     SMTP_PASSWORD=your-app-password")
        print()
        print("  3. Generate Gmail app password:")
        print("     https://myaccount.google.com/apppasswords")
        return False
    
    if not notifier.email_to:
        print("[ERROR] Email address not configured")
        print("        Set email_to in config.yml")
        return False
    
    if not notifier.smtp_user or not notifier.smtp_password:
        print("[ERROR] SMTP credentials not configured")
        print()
        print("Add to .env file:")
        print("  SMTP_USER=your@gmail.com")
        print("  SMTP_PASSWORD=your-16-digit-app-password")
        print()
        print("Generate Gmail app password:")
        print("  https://myaccount.google.com/apppasswords")
        return False
    
    print("[OK] Notification system configured")
    print()
    return True

def test_email():
    """
    Function to send a test email notification.
    Returns True if successful, False otherwise.
    
    @PARAMS: None
    """
    print("=" * 80)
    print("TEST EMAIL NOTIFICATION")
    print("=" * 80)
    print()
    
    config = load_config('config.yml')
    notifier = NotificationManager(config)
    
    if not notifier.enabled:
        print("[ERROR] Notifications not enabled")
        return False
    
    print(f"Sending test email to: {notifier.email_to}")
    print()
    
    subject = "Test: Micro-Investing Notifications"
    body = """Micro-Investing Engine - Test Notification

This is a test email to confirm that your notification system is working correctly.

If you received this email, your notifications are set up properly!

---
Micro-Investing Engine
thecardcaddie.com
"""
    
    success = notifier.send_email(subject, body)
    
    if success:
        print("[SUCCESS] Test email sent!")
        print(f"           Check your inbox: {notifier.email_to}")
    else:
        print("[FAILED] Could not send email")
        print("         Check your SMTP credentials in .env file")
    
    return success

def test_investment_notification():
    """
    Function to send a sample investment notification (simulates successful trade).
    Returns True if successful, False otherwise.
    
    @PARAMS: None
    """
    print("=" * 80)
    print("TEST INVESTMENT EXECUTED NOTIFICATION")
    print("=" * 80)
    print()
    
    config = load_config('config.yml')
    notifier = NotificationManager(config)
    
    if not notifier.enabled:
        print("[ERROR] Notifications not enabled")
        return False
    
    print("Sending sample 'investment executed' notification...")
    print()
    
    success = notifier.notify_investment_executed(
        amount=15.50,
        allocation={'VOO': 9.30, 'QQQ': 6.20},
        strategy='scheduled'
    )
    
    if success:
        print("[SUCCESS] Notification sent!")
        print(f"           Check your inbox: {notifier.email_to}")
    else:
        print("[FAILED] Could not send notification")
    
    return success

def test_insufficient_funds_notification():
    """
    Function to send a sample insufficient funds notification.
    Returns True if successful, False otherwise.
    
    @PARAMS: None
    """
    print("=" * 80)
    print("TEST INSUFFICIENT FUNDS NOTIFICATION")
    print("=" * 80)
    print()
    
    config = load_config('config.yml')
    notifier = NotificationManager(config)
    
    if not notifier.enabled:
        print("[ERROR] Notifications not enabled")
        return False
    
    print("Sending sample 'insufficient funds' notification...")
    print()
    
    success = notifier.notify_insufficient_funds(
        amount_needed=25.50,
        buying_power=15.00,
        shortfall=10.50
    )
    
    if success:
        print("[SUCCESS] Notification sent!")
        print(f"           Check your inbox: {notifier.email_to}")
    else:
        print("[FAILED] Could not send notification")
    
    return success

def main():
    """
    Function to run notification system tests.
    Returns nothing (executes side effects like sending emails).
    
    @PARAMS: None
    """
    parser = argparse.ArgumentParser(description="Test Notification System")
    parser.add_argument('--test-email', action='store_true', help='Send test email')
    parser.add_argument('--test-investment', action='store_true', help='Send test investment notification')
    parser.add_argument('--test-insufficient-funds', action='store_true', help='Send test insufficient funds notification')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("NOTIFICATION SYSTEM TEST")
    print("=" * 80)
    print()
    
    # Check configuration
    configured = test_configuration()
    
    if not configured:
        print("\n" + "=" * 80)
        print("SETUP INSTRUCTIONS")
        print("=" * 80)
        print()
        print("1. Configure notifications in config.yml:")
        print("   notifications:")
        print("     enabled: true")
        print("     email_to: your@email.com")
        print()
        print("2. Set up Gmail app password:")
        print("   https://myaccount.google.com/apppasswords")
        print()
        print("3. Add to .env:")
        print("   SMTP_USER=your@gmail.com")
        print("   SMTP_PASSWORD=your-16-digit-app-password")
        return
    
    print()
    
    # Run specific tests
    if args.test_email:
        test_email()
    elif args.test_investment:
        test_investment_notification()
    elif args.test_insufficient_funds:
        test_insufficient_funds_notification()
    else:
        # Default: test email
        print("Testing email notifications...")
        print()
        test_email()
        
        print("\n" + "=" * 80)
        print("To test other notification types:")
        print("  python tests/test_notifications.py --test-investment")
        print("  python tests/test_notifications.py --test-insufficient-funds")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # check if smtp credentials are set
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_user or not smtp_password:
        print("\n[WARNING] Email notifications not configured!")
        print("   1. Enable 2-factor authentication on your Google account")
        print("   2. Generate app password:")
        print("      https://myaccount.google.com/apppasswords")
        print("   3. Add to your .env file:")
        print("      SMTP_USER=your@gmail.com")
        print("      SMTP_PASSWORD=your-16-digit-app-password")
        print("   4. Enable in config.yml:")
        print("      notifications:")
        print("        enabled: true")
        print("        email_to: your@gmail.com")
        print()
    else:
        main()
