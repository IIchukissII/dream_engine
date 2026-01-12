"""SMTP email service implementation."""

import os
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import aiosmtplib

from .base import EmailService


class SMTPEmailService(EmailService):
    """Email service using SMTP."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_address: Optional[str] = None,
        from_name: Optional[str] = None,
        use_tls: bool = True
    ):
        """Initialize SMTP email service.

        Args:
            host: SMTP server host
            port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_address: Sender email address
            from_name: Sender display name
            use_tls: Whether to use TLS
        """
        self.host = host or os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
        self.port = port or int(os.getenv('EMAIL_SMTP_PORT', '587'))
        self.username = username or os.getenv('EMAIL_SMTP_USER', '')
        self.password = password or os.getenv('EMAIL_SMTP_PASSWORD', '')
        self.from_address = from_address or os.getenv('EMAIL_FROM_ADDRESS', 'noreply@storm-logos.com')
        self.from_name = from_name or os.getenv('EMAIL_FROM_NAME', 'Storm-Logos')
        self.use_tls = use_tls

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """Send an email via SMTP.

        Args:
            to: Recipient email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content (optional fallback)

        Returns:
            True if sent successfully
        """
        if not self.username or not self.password:
            print("Warning: SMTP credentials not configured, skipping email")
            return False

        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_address}>"
            message['To'] = to

            # Add plain text part (fallback)
            if text_body:
                text_part = MIMEText(text_body, 'plain', 'utf-8')
                message.attach(text_part)

            # Add HTML part
            html_part = MIMEText(html_body, 'html', 'utf-8')
            message.attach(html_part)

            # Send email
            if self.use_tls:
                await aiosmtplib.send(
                    message,
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    start_tls=True
                )
            else:
                await aiosmtplib.send(
                    message,
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password
                )

            print(f"Email sent successfully to {to}")
            return True

        except aiosmtplib.SMTPException as e:
            print(f"SMTP error sending email to {to}: {e}")
            return False
        except Exception as e:
            print(f"Error sending email to {to}: {e}")
            return False


class MockEmailService(EmailService):
    """Mock email service for testing."""

    def __init__(self):
        self.sent_emails = []

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """Store email instead of sending."""
        self.sent_emails.append({
            'to': to,
            'subject': subject,
            'html_body': html_body,
            'text_body': text_body
        })
        print(f"Mock email sent to {to}: {subject}")
        return True

    def get_last_email(self):
        """Get the last sent email."""
        return self.sent_emails[-1] if self.sent_emails else None

    def clear(self):
        """Clear sent emails."""
        self.sent_emails.clear()
