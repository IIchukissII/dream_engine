"""Redis-backed rate limiter for API endpoints.

Provides different rate limits for different endpoint categories:
- auth: 5 requests/minute (login, register)
- password_reset: 3 requests/hour
- general: 60 requests/minute

Also implements account lockout after failed login attempts.
"""

import os
import time
from typing import Optional, Tuple
from functools import wraps

import redis
from fastapi import HTTPException, Request, status


# Rate limit configurations: (max_requests, window_seconds)
RATE_LIMITS = {
    'auth': (5, 60),           # 5 per minute
    'password_reset': (3, 3600),  # 3 per hour
    'general': (60, 60),       # 60 per minute
}

# Account lockout settings
MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
LOCKOUT_DURATION = int(os.getenv('LOCKOUT_DURATION_MINUTES', '15')) * 60


class RateLimiter:
    """Redis-backed rate limiter."""

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

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request."""
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.client.host if request.client else 'unknown'

    def check_rate_limit(self, request: Request, category: str = 'general') -> Tuple[bool, dict]:
        """Check if request is within rate limit.

        Args:
            request: FastAPI request object
            category: Rate limit category ('auth', 'password_reset', 'general')

        Returns:
            (allowed, info) where info contains remaining requests and reset time
        """
        max_requests, window = RATE_LIMITS.get(category, RATE_LIMITS['general'])
        client_ip = self._get_client_ip(request)
        key = f"rate:{category}:{client_ip}"

        try:
            pipe = self.client.pipeline()
            now = time.time()
            window_start = now - window

            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Count current entries
            pipe.zcard(key)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Set expiry
            pipe.expire(key, window)

            results = pipe.execute()
            current_count = results[1]

            remaining = max(0, max_requests - current_count - 1)
            reset_time = int(now + window)

            info = {
                'limit': max_requests,
                'remaining': remaining,
                'reset': reset_time,
                'category': category,
            }

            if current_count >= max_requests:
                return False, info

            return True, info

        except redis.RedisError as e:
            # On Redis error, allow request (fail open)
            print(f"Rate limiter Redis error: {e}")
            return True, {'error': str(e)}

    def record_failed_login(self, username: str, request: Request) -> Tuple[bool, int]:
        """Record a failed login attempt.

        Args:
            username: The username that failed login
            request: FastAPI request object

        Returns:
            (is_locked, remaining_attempts)
        """
        client_ip = self._get_client_ip(request)
        key = f"login_attempts:{username}:{client_ip}"

        try:
            pipe = self.client.pipeline()
            pipe.incr(key)
            pipe.expire(key, LOCKOUT_DURATION)
            results = pipe.execute()

            attempts = results[0]
            remaining = max(0, MAX_LOGIN_ATTEMPTS - attempts)

            if attempts >= MAX_LOGIN_ATTEMPTS:
                # Set lockout
                lockout_key = f"lockout:{username}:{client_ip}"
                self.client.setex(lockout_key, LOCKOUT_DURATION, '1')
                return True, 0

            return False, remaining

        except redis.RedisError as e:
            print(f"Failed login recording error: {e}")
            return False, MAX_LOGIN_ATTEMPTS

    def is_locked_out(self, username: str, request: Request) -> Tuple[bool, int]:
        """Check if account is locked out.

        Returns:
            (is_locked, seconds_remaining)
        """
        client_ip = self._get_client_ip(request)
        lockout_key = f"lockout:{username}:{client_ip}"

        try:
            ttl = self.client.ttl(lockout_key)
            if ttl > 0:
                return True, ttl
            return False, 0
        except redis.RedisError:
            return False, 0

    def clear_login_attempts(self, username: str, request: Request):
        """Clear login attempts after successful login."""
        client_ip = self._get_client_ip(request)
        key = f"login_attempts:{username}:{client_ip}"
        lockout_key = f"lockout:{username}:{client_ip}"

        try:
            self.client.delete(key, lockout_key)
        except redis.RedisError:
            pass


# Singleton instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get singleton rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def rate_limit(category: str = 'general'):
    """Decorator for rate limiting endpoints.

    Usage:
        @app.get("/endpoint")
        @rate_limit('auth')
        async def endpoint(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            if request is None:
                # Try to find request in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request:
                limiter = get_rate_limiter()
                allowed, info = limiter.check_rate_limit(request, category)

                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Try again in {info.get('reset', 60) - int(time.time())} seconds.",
                        headers={
                            'X-RateLimit-Limit': str(info.get('limit', 0)),
                            'X-RateLimit-Remaining': str(info.get('remaining', 0)),
                            'X-RateLimit-Reset': str(info.get('reset', 0)),
                        }
                    )

            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator
