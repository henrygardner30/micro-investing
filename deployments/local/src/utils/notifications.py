"""
Notification System

Sends email alerts for insufficient funds and investment execution.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from datetime import datetime
from textwrap import dedent

class NotificationManager:
    """
    Manages email notifications for investment events.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.notification_config = config.get('notifications', {})
        self.enabled = self.notification_config.get('enabled', False)
        
        # email settings
        self.email_to = self.notification_config.get('email_to', '')
        self.email_from = os.getenv('NOTIFICATION_EMAIL_FROM', self.notification_config.get('email_from', ''))
        self.smtp_server = os.getenv('SMTP_SERVER', self.notification_config.get('smtp_server', 'smtp.gmail.com'))
        self.smtp_port = int(os.getenv('SMTP_PORT', self.notification_config.get('smtp_port', 587)))
        self.smtp_user = os.getenv('SMTP_USER', self.notification_config.get('smtp_user', ''))
        self.smtp_password = os.getenv('SMTP_PASSWORD', self.notification_config.get('smtp_password', ''))
    
    def send_email(self, subject: str, body: str, html: bool = False) -> bool:
        """
        Function to send an email notification using smtp.
        Returns true if email sent successfully, false otherwise.

        @PARAMS:
            - subject -> subject line
            - body    -> body content (plain text or HTML)
            - html    -> if true, send as html email (default: false)
        """
        if not self.enabled:
            return False
        
        if not self.email_to or not self.smtp_user or not self.smtp_password:
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_from or self.smtp_user
            msg['To'] = self.email_to
            msg['Subject'] = subject
            
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"[NOTIFICATION] Email sent to {self.email_to}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to send email: {e}")
            return False
    
    def notify_insufficient_funds(self, amount_needed: float, buying_power: float, shortfall: float) -> bool:
        """
        Function to send notification when insufficient funds are detected.
        Returns True if notification sent successfully.

        @PARAMS:
            - amount_needed -> dollar amount needed to execute trades
            - buying_power  -> current Alpaca buying power
            - shortfall     -> amount of additional funds needed
        """
        if not self.enabled:
            return False
        
        timestamp = datetime.now().strftime('%Y-%m-%d %I:%M %p')
        
        subject = f"Micro-Investing: Insufficient Funds (${shortfall:.2f} needed)"
        
        body = dedent(f"""\
            Micro-Investing Engine - Insufficient Funds

            Investment paused due to insufficient buying power in your Alpaca account.

            Details:
            Amount Needed: ${amount_needed:.2f}
            Current Balance: ${buying_power:.2f}
            Shortfall: ${shortfall:.2f}

            Next Steps:
            1. Log in to your Alpaca account
            2. Transfer funds to cover the shortfall
            3. Wait for funds to settle (typically 4-5 business days for ACH)
            4. Rerun the engine: python main.py run

            Alpaca Funding: https://app.alpaca.markets/funding

            ---
            Time: {timestamp}
            Micro-Investing Engine
            thecardcaddie.com
            """)
        
        return self.send_email(subject, body)
    
    def notify_investment_executed(self, amount: float, allocation: Dict[str, float], strategy: str) -> bool:
        """
        Function to send notification when investment is successfully executed.
        Returns True if notification sent successfully.

        @PARAMS:
            - amount     -> total dollar amount invested
            - allocation -> mapping stock symbols to dollar amounts
            - strategy   -> name of strategy used 
        """
        if not self.enabled:
            return False
        
        timestamp = datetime.now().strftime('%Y-%m-%d %I:%M %p')
        
        subject = f"Micro-Investing: Investment Executed (${amount:.2f})"
        
        # build allocation breakdown
        allocation_text = "\n".join([f"  {symbol}: ${amt:.2f}" for symbol, amt in allocation.items()])
        
        body = dedent(f"""\
            Micro-Investing Engine - Investment Executed

            Your investment has been successfully executed!

            Investment Details:
            Total Amount: ${amount:.2f}
            Strategy: {strategy}

            Asset Allocation:
            {allocation_text}

            Trades have been submitted to Alpaca and should be filled shortly.

            View your portfolio: https://app.alpaca.markets/portfolio

            ---
            Time: {timestamp}
            Micro-Investing Engine
            thecardcaddie.com
            """)
        
        return self.send_email(subject, body)