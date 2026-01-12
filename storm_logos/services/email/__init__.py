"""Email service package."""

from .base import EmailService
from .smtp import SMTPEmailService

__all__ = ['EmailService', 'SMTPEmailService', 'get_email_service']


_email_service = None


def get_email_service() -> EmailService:
    """Get singleton email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = SMTPEmailService()
    return _email_service
