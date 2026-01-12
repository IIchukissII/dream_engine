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
        use_ssl: Optional[bool] = None
    ):
        """Initialize SMTP email service.

        Args:
            host: SMTP server host
            port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_address: Sender email address
            from_name: Sender display name
            use_ssl: Whether to use SSL (port 465) instead of STARTTLS (port 587)
        """
        self.host = host or os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
        self.port = port or int(os.getenv('EMAIL_SMTP_PORT', '465'))
        self.username = username or os.getenv('EMAIL_SMTP_USER', '')
        self.password = password or os.getenv('EMAIL_SMTP_PASSWORD', '')
        self.from_address = from_address or os.getenv('EMAIL_FROM_ADDRESS', 'noreply@storm-logos.com')
        self.from_name = from_name or os.getenv('EMAIL_FROM_NAME', 'Storm-Logos')
        # Default to SSL for port 465, STARTTLS for port 587
        if use_ssl is not None:
            self.use_ssl = use_ssl
        else:
            self.use_ssl = os.getenv('EMAIL_USE_SSL', str(self.port == 465)).lower() == 'true'

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
        if not self.host:
            print("Warning: SMTP host not configured, skipping email")
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

            # Build send kwargs
            send_kwargs = {
                'hostname': self.host,
                'port': self.port,
            }

            # Add authentication if credentials are provided
            if self.username and self.password:
                send_kwargs['username'] = self.username
                send_kwargs['password'] = self.password

            # Configure SSL/TLS
            if self.use_ssl:
                # Port 465: Use implicit SSL (SMTPS)
                send_kwargs['use_tls'] = True
                send_kwargs['start_tls'] = False
            elif self.username and self.password:
                # Port 587: Use STARTTLS
                send_kwargs['use_tls'] = False
                send_kwargs['start_tls'] = True
            else:
                # Local SMTP without auth - no encryption
                send_kwargs['use_tls'] = False
                send_kwargs['start_tls'] = False

            await aiosmtplib.send(message, **send_kwargs)

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
