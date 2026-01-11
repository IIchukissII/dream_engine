"""Add API tracking and audit tables.

Revision ID: 002
Revises: 001
Create Date: 2025-01-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # API request log for analytics
    op.execute("""
        CREATE TABLE IF NOT EXISTS api_requests (
            id BIGSERIAL PRIMARY KEY,
            request_id VARCHAR(36),
            user_id VARCHAR(100),
            endpoint VARCHAR(200) NOT NULL,
            method VARCHAR(10) NOT NULL,
            status_code INTEGER,
            duration_ms FLOAT,
            client_ip VARCHAR(45),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Audit log for important actions
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id BIGSERIAL PRIMARY KEY,
            user_id VARCHAR(100),
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(50),
            resource_id VARCHAR(100),
            details JSONB,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Rate limiting table
    op.execute("""
        CREATE TABLE IF NOT EXISTS rate_limits (
            id SERIAL PRIMARY KEY,
            client_key VARCHAR(100) NOT NULL,
            endpoint VARCHAR(200),
            request_count INTEGER DEFAULT 1,
            window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(client_key, endpoint)
        )
    """)

    # Indexes
    op.execute("CREATE INDEX IF NOT EXISTS idx_api_requests_user_id ON api_requests(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_api_requests_created_at ON api_requests(created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rate_limits_client ON rate_limits(client_key)")

    # Add user email column (optional)
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS email VARCHAR(255),
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true,
        ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS rate_limits CASCADE")
    op.execute("DROP TABLE IF EXISTS audit_log CASCADE")
    op.execute("DROP TABLE IF EXISTS api_requests CASCADE")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS email")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_active")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_admin")
