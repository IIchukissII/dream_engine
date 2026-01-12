"""Add user management tables and columns.

Revision ID: 003
Revises: 002
Create Date: 2026-01-12

Adds:
- Email verification columns
- Password reset columns
- Profile fields
- OAuth accounts table
- Refresh tokens table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user management columns to users table
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255),
        ADD COLUMN IF NOT EXISTS email_verification_expires TIMESTAMP,
        ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR(255),
        ADD COLUMN IF NOT EXISTS password_reset_expires TIMESTAMP,
        ADD COLUMN IF NOT EXISTS display_name VARCHAR(100),
        ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500),
        ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0,
        ADD COLUMN IF NOT EXISTS lockout_until TIMESTAMP,
        ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP,
        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP
    """)

    # OAuth accounts table (allow multiple providers per user)
    op.execute("""
        CREATE TABLE IF NOT EXISTS oauth_accounts (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            provider VARCHAR(50) NOT NULL,
            provider_user_id VARCHAR(255) NOT NULL,
            provider_email VARCHAR(255),
            access_token_encrypted TEXT,
            refresh_token_encrypted TEXT,
            token_expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(provider, provider_user_id),
            UNIQUE(user_id, provider)
        )
    """)

    # Refresh tokens table for JWT rotation
    op.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            token_hash VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            device_info VARCHAR(500),
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            revoked_at TIMESTAMP
        )
    """)

    # User tokens table (for email verification and password reset)
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_tokens (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            token_type VARCHAR(50) NOT NULL,
            token_hash VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(45)
        )
    """)

    # Indexes for performance
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(email_verified)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_oauth_provider ON oauth_accounts(provider, provider_user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_oauth_user ON oauth_accounts(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens_type ON user_tokens(user_id, token_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens_hash ON user_tokens(token_hash)")


def downgrade() -> None:
    # Drop tables
    op.execute("DROP TABLE IF EXISTS user_tokens CASCADE")
    op.execute("DROP TABLE IF EXISTS refresh_tokens CASCADE")
    op.execute("DROP TABLE IF EXISTS oauth_accounts CASCADE")

    # Remove columns from users table
    op.execute("""
        ALTER TABLE users
        DROP COLUMN IF EXISTS email_verified,
        DROP COLUMN IF EXISTS email_verification_token,
        DROP COLUMN IF EXISTS email_verification_expires,
        DROP COLUMN IF EXISTS password_reset_token,
        DROP COLUMN IF EXISTS password_reset_expires,
        DROP COLUMN IF EXISTS display_name,
        DROP COLUMN IF EXISTS avatar_url,
        DROP COLUMN IF EXISTS failed_login_attempts,
        DROP COLUMN IF EXISTS lockout_until,
        DROP COLUMN IF EXISTS password_changed_at,
        DROP COLUMN IF EXISTS deleted_at
    """)
