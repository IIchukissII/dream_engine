"""Base email service interface."""

from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path


class EmailService(ABC):
    """Abstract base class for email services."""

    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content (optional fallback)

        Returns:
            True if sent successfully
        """
        pass

    async def send_verification_email(
        self,
        to: str,
        username: str,
        token: str,
        base_url: str
    ) -> bool:
        """Send email verification email.

        Args:
            to: User's email address
            username: User's username
            token: Verification token
            base_url: Base URL for verification link

        Returns:
            True if sent successfully
        """
        verify_url = f"{base_url}/auth/verify-email?token={token}"

        html_body = self._load_template('email_verification.html').format(
            username=username,
            verify_url=verify_url
        )

        text_body = f"""
Hello {username},

Please verify your email address by clicking the link below:

{verify_url}

This link will expire in 24 hours.

If you did not create an account, please ignore this email.

Best regards,
Storm-Logos Team
"""

        return await self.send_email(
            to=to,
            subject="Verify your email address",
            html_body=html_body,
            text_body=text_body
        )

    async def send_password_reset_email(
        self,
        to: str,
        username: str,
        token: str,
        base_url: str
    ) -> bool:
        """Send password reset email.

        Args:
            to: User's email address
            username: User's username
            token: Reset token
            base_url: Base URL for reset link

        Returns:
            True if sent successfully
        """
        reset_url = f"{base_url}/auth/reset-password?token={token}"

        html_body = self._load_template('password_reset.html').format(
            username=username,
            reset_url=reset_url
        )

        text_body = f"""
Hello {username},

You requested to reset your password. Click the link below to set a new password:

{reset_url}

This link will expire in 1 hour.

If you did not request a password reset, please ignore this email.

Best regards,
Storm-Logos Team
"""

        return await self.send_email(
            to=to,
            subject="Reset your password",
            html_body=html_body,
            text_body=text_body
        )

    async def send_welcome_email(
        self,
        to: str,
        username: str
    ) -> bool:
        """Send welcome email after registration.

        Args:
            to: User's email address
            username: User's username

        Returns:
            True if sent successfully
        """
        html_body = self._load_template('welcome.html').format(
            username=username
        )

        text_body = f"""
Welcome to Storm-Logos, {username}!

Your account has been created successfully. You can now start your journey of dream analysis and Jungian exploration.

Explore your dreams, discover archetypes, and gain insights into your unconscious mind.

Best regards,
Storm-Logos Team
"""

        return await self.send_email(
            to=to,
            subject="Welcome to Storm-Logos",
            html_body=html_body,
            text_body=text_body
        )

    def _load_template(self, template_name: str) -> str:
        """Load HTML template from templates directory."""
        template_path = Path(__file__).parent / 'templates' / template_name
        try:
            with open(template_path) as f:
                return f.read()
        except FileNotFoundError:
            # Return basic fallback template
            return self._get_fallback_template(template_name)

    def _get_fallback_template(self, template_name: str) -> str:
        """Get basic fallback template if file not found."""
        if 'verification' in template_name:
            return """
<!DOCTYPE html>
<html>
<head><style>body {{font-family: Arial, sans-serif; padding: 20px;}}</style></head>
<body>
<h2>Email Verification</h2>
<p>Hello {username},</p>
<p>Please verify your email address by clicking the button below:</p>
<p><a href="{verify_url}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
<p>Or copy this link: {verify_url}</p>
<p>This link expires in 24 hours.</p>
</body>
</html>
"""
        elif 'reset' in template_name:
            return """
<!DOCTYPE html>
<html>
<head><style>body {{font-family: Arial, sans-serif; padding: 20px;}}</style></head>
<body>
<h2>Password Reset</h2>
<p>Hello {username},</p>
<p>Click the button below to reset your password:</p>
<p><a href="{reset_url}" style="background: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
<p>Or copy this link: {reset_url}</p>
<p>This link expires in 1 hour.</p>
</body>
</html>
"""
        elif 'welcome' in template_name:
            return """
<!DOCTYPE html>
<html>
<head><style>body {{font-family: Arial, sans-serif; padding: 20px;}}</style></head>
<body>
<h2>Welcome to Storm-Logos!</h2>
<p>Hello {username},</p>
<p>Your account has been created successfully.</p>
<p>Start exploring your dreams and discovering the archetypes within.</p>
</body>
</html>
"""
        return "<p>{}</p>"
