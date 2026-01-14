"""Auth Router: User registration, authentication, and account management."""

import logging
import os
from fastapi import APIRouter, HTTPException, status, Depends, Request

logger = logging.getLogger(__name__)

from ..models import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    PasswordResetRequest, PasswordReset, PasswordChange,
    EmailVerify, ProfileUpdate, MessageResponse
)
from ..deps import get_user_graph, create_token, get_current_user, SUPERUSER_USERS
from ..rate_limiter import get_rate_limiter
from ..tokens import get_token_service
from ...email import get_email_service

router = APIRouter(prefix="/auth", tags=["auth"])

# Base URL for email links
BASE_URL = os.getenv('BASE_URL', 'https://dream-engine.space')


def _user_to_response(user) -> UserResponse:
    """Convert User to UserResponse."""
    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        email_verified=user.email_verified,
        is_superuser=user.username.lower() in SUPERUSER_USERS,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


# =============================================================================
# REGISTRATION & LOGIN
# =============================================================================

@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate, request: Request):
    """Register a new user with email verification."""
    # Rate limiting
    limiter = get_rate_limiter()
    allowed, info = limiter.check_rate_limit(request, 'auth')
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later."
        )

    ug = get_user_graph()

    # Check if username exists
    existing = ug.get_user(data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check if email exists
    existing_email = ug.get_user_by_email(data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = ug.create_user(data.username, data.password, data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user"
        )

    # Send verification email (async, don't wait)
    try:
        token_service = get_token_service()
        verify_token = token_service.create_email_verification_token(user.user_id)

        email_service = get_email_service()
        await email_service.send_verification_email(
            to=data.email,
            username=data.username,
            token=verify_token,
            base_url=BASE_URL
        )
    except Exception as e:
        logger.warning(f"Failed to send verification email: {e}")
        # Don't fail registration if email fails

    # Create token
    token = create_token(user.user_id, user.username)

    return TokenResponse(
        access_token=token,
        user=_user_to_response(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, request: Request):
    """Login and get access token."""
    limiter = get_rate_limiter()

    # Rate limiting
    allowed, info = limiter.check_rate_limit(request, 'auth')
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    # Check account lockout
    is_locked, seconds_remaining = limiter.is_locked_out(data.username, request)
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account temporarily locked. Try again in {seconds_remaining // 60} minutes."
        )

    ug = get_user_graph()
    user = ug.authenticate(data.username, data.password)

    if not user:
        # Record failed attempt
        is_now_locked, remaining = limiter.record_failed_login(data.username, request)
        if is_now_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Too many failed attempts. Account locked for 15 minutes."
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid username or password. {remaining} attempts remaining."
        )

    # Clear failed attempts on successful login
    limiter.clear_login_attempts(data.username, request)

    token = create_token(user.user_id, user.username)

    return TokenResponse(
        access_token=token,
        user=_user_to_response(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info."""
    ug = get_user_graph()
    user = ug.get_user(current_user["username"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return _user_to_response(user)


# =============================================================================
# EMAIL VERIFICATION
# =============================================================================

@router.post("/email/verify", response_model=MessageResponse)
async def verify_email(data: EmailVerify):
    """Verify email address with token."""
    token_service = get_token_service()
    user_id = token_service.verify_email_token(data.token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    ug = get_user_graph()
    if not ug.verify_email(user_id):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )

    return MessageResponse(message="Email verified successfully")


@router.post("/email/resend", response_model=MessageResponse)
async def resend_verification(request: Request, current_user: dict = Depends(get_current_user)):
    """Resend email verification."""
    # Rate limit
    limiter = get_rate_limiter()
    allowed, _ = limiter.check_rate_limit(request, 'password_reset')
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )

    ug = get_user_graph()
    user = ug.get_user_by_id(current_user["user_id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.email_verified:
        return MessageResponse(message="Email already verified")

    if not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email address on file"
        )

    # Send verification email
    token_service = get_token_service()
    verify_token = token_service.create_email_verification_token(user.user_id)

    email_service = get_email_service()
    await email_service.send_verification_email(
        to=user.email,
        username=user.username,
        token=verify_token,
        base_url=BASE_URL
    )

    return MessageResponse(message="Verification email sent")


# =============================================================================
# PASSWORD RESET
# =============================================================================

@router.post("/password/forgot", response_model=MessageResponse)
async def forgot_password(data: PasswordResetRequest, request: Request):
    """Request password reset email."""
    # Rate limit
    limiter = get_rate_limiter()
    allowed, _ = limiter.check_rate_limit(request, 'password_reset')
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )

    ug = get_user_graph()
    user = ug.get_user_by_email(data.email)

    # Always return success to prevent email enumeration
    if not user:
        return MessageResponse(message="If that email exists, a reset link has been sent.")

    # Create reset token
    token_service = get_token_service()
    reset_token = token_service.create_password_reset_token(user.user_id)

    # Send reset email
    email_service = get_email_service()
    await email_service.send_password_reset_email(
        to=user.email,
        username=user.username,
        token=reset_token,
        base_url=BASE_URL
    )

    return MessageResponse(message="If that email exists, a reset link has been sent.")


@router.post("/password/reset", response_model=MessageResponse)
async def reset_password(data: PasswordReset):
    """Reset password with token."""
    token_service = get_token_service()
    user_id = token_service.verify_password_reset_token(data.token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    ug = get_user_graph()
    if not ug.update_password(user_id, data.new_password):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

    return MessageResponse(message="Password reset successfully")


@router.post("/password/change", response_model=MessageResponse)
async def change_password(data: PasswordChange, current_user: dict = Depends(get_current_user)):
    """Change password (requires current password)."""
    ug = get_user_graph()
    user = ug.get_user(current_user["username"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not user.verify_password(data.current_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Update password
    if not ug.update_password(user.user_id, data.new_password):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

    return MessageResponse(message="Password changed successfully")


# =============================================================================
# PROFILE MANAGEMENT
# =============================================================================

@router.put("/profile", response_model=UserResponse)
async def update_profile(data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update user profile."""
    ug = get_user_graph()

    if not ug.update_profile(
        current_user["user_id"],
        display_name=data.display_name,
        avatar_url=data.avatar_url
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

    # Get updated user
    user = ug.get_user_by_id(current_user["user_id"])
    return _user_to_response(user)


@router.delete("/profile", response_model=MessageResponse)
async def delete_account(current_user: dict = Depends(get_current_user)):
    """Delete user account (soft delete)."""
    # Note: Implement soft delete by setting deleted_at timestamp
    # For now, return not implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Account deletion not yet implemented"
    )
