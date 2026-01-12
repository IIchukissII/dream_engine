"""Token service for email verification and password reset."""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple

import redis


class TokenService:
    """Redis-backed token service for verification and password reset."""

    # Token expiration times
    EMAIL_VERIFICATION_HOURS = 24
    PASSWORD_RESET_HOURS = 1

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        """Lazy Redis connection."""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )
        return self._client

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def create_email_verification_token(self, user_id: str) -> str:
        """Create and store an email verification token.

        Args:
            user_id: User's ID

        Returns:
            The raw token (send this to user)
        """
        token = self.generate_token()
        token_hash = self.hash_token(token)
        key = f"email_verify:{token_hash}"

        try:
            self.client.setex(
                key,
                timedelta(hours=self.EMAIL_VERIFICATION_HOURS),
                user_id
            )
        except redis.RedisError as e:
            print(f"Error storing email verification token: {e}")

        return token

    def verify_email_token(self, token: str) -> Optional[str]:
        """Verify an email verification token.

        Args:
            token: The raw token

        Returns:
            User ID if valid, None otherwise
        """
        token_hash = self.hash_token(token)
        key = f"email_verify:{token_hash}"

        try:
            user_id = self.client.get(key)
            if user_id:
                # Delete token after use
                self.client.delete(key)
                return user_id
        except redis.RedisError as e:
            print(f"Error verifying email token: {e}")

        return None

    def create_password_reset_token(self, user_id: str) -> str:
        """Create and store a password reset token.

        Args:
            user_id: User's ID

        Returns:
            The raw token (send this to user)
        """
        # Invalidate any existing reset tokens for this user
        self._invalidate_user_reset_tokens(user_id)

        token = self.generate_token()
        token_hash = self.hash_token(token)
        key = f"password_reset:{token_hash}"
        user_key = f"password_reset_user:{user_id}"

        try:
            pipe = self.client.pipeline()
            pipe.setex(key, timedelta(hours=self.PASSWORD_RESET_HOURS), user_id)
            pipe.setex(user_key, timedelta(hours=self.PASSWORD_RESET_HOURS), token_hash)
            pipe.execute()
        except redis.RedisError as e:
            print(f"Error storing password reset token: {e}")

        return token

    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify a password reset token.

        Args:
            token: The raw token

        Returns:
            User ID if valid, None otherwise
        """
        token_hash = self.hash_token(token)
        key = f"password_reset:{token_hash}"

        try:
            user_id = self.client.get(key)
            if user_id:
                # Delete token after use
                self.client.delete(key)
                self.client.delete(f"password_reset_user:{user_id}")
                return user_id
        except redis.RedisError as e:
            print(f"Error verifying password reset token: {e}")

        return None

    def _invalidate_user_reset_tokens(self, user_id: str):
        """Invalidate any existing password reset tokens for a user."""
        user_key = f"password_reset_user:{user_id}"
        try:
            existing_hash = self.client.get(user_key)
            if existing_hash:
                self.client.delete(f"password_reset:{existing_hash}")
                self.client.delete(user_key)
        except redis.RedisError:
            pass


# Singleton instance
_token_service: Optional[TokenService] = None


def get_token_service() -> TokenService:
    """Get singleton token service instance."""
    global _token_service
    if _token_service is None:
        _token_service = TokenService()
    return _token_service
