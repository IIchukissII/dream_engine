"""Initial schema - matches existing database structure.

Revision ID: 001
Revises:
Create Date: 2025-01-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Word coordinates table
    op.execute("""
        CREATE TABLE IF NOT EXISTS word_coordinates (
            word VARCHAR(100) PRIMARY KEY,
            A FLOAT NOT NULL DEFAULT 0.0,
            S FLOAT NOT NULL DEFAULT 0.0,
            tau FLOAT NOT NULL DEFAULT 2.5,
            source VARCHAR(50) DEFAULT 'corpus',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bonds table
    op.execute("""
        CREATE TABLE IF NOT EXISTS bonds (
            id SERIAL PRIMARY KEY,
            adj VARCHAR(100),
            noun VARCHAR(100) NOT NULL,
            A FLOAT NOT NULL DEFAULT 0.0,
            S FLOAT NOT NULL DEFAULT 0.0,
            tau FLOAT NOT NULL DEFAULT 2.5,
            variety INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(adj, noun)
        )
    """)

    # Corpus bond vocabulary
    op.execute("""
        CREATE TABLE IF NOT EXISTS hyp_bond_vocab (
            bond VARCHAR(200) PRIMARY KEY,
            first_seen_order INTEGER,
            first_seen_book UUID,
            total_count INTEGER,
            book_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Learned bonds from conversations
    op.execute("""
        CREATE TABLE IF NOT EXISTS learned_bonds (
            id SERIAL PRIMARY KEY,
            adj VARCHAR(100),
            noun VARCHAR(100) NOT NULL,
            A FLOAT NOT NULL DEFAULT 0.0,
            S FLOAT NOT NULL DEFAULT 0.0,
            tau FLOAT NOT NULL DEFAULT 2.5,
            source VARCHAR(100) DEFAULT 'conversation',
            confidence FLOAT DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            use_count INTEGER DEFAULT 1,
            UNIQUE(adj, noun)
        )
    """)

    # Learned words
    op.execute("""
        CREATE TABLE IF NOT EXISTS learned_words (
            word VARCHAR(100) PRIMARY KEY,
            A FLOAT NOT NULL DEFAULT 0.0,
            S FLOAT NOT NULL DEFAULT 0.0,
            tau FLOAT NOT NULL DEFAULT 2.5,
            source VARCHAR(100) DEFAULT 'estimated',
            confidence FLOAT DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Users table
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(100) PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    # Sessions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id VARCHAR(100) PRIMARY KEY,
            user_id VARCHAR(100) REFERENCES users(user_id),
            mode VARCHAR(20) DEFAULT 'hybrid',
            status VARCHAR(20) DEFAULT 'active',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            summary TEXT
        )
    """)

    # Create indexes
    op.execute("CREATE INDEX IF NOT EXISTS idx_bonds_noun ON bonds(noun)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_bonds_adj ON bonds(adj)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_bond_vocab_count ON hyp_bond_vocab(total_count DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_learned_bonds_noun ON learned_bonds(noun)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_word_coordinates_source ON word_coordinates(source)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS learned_words CASCADE")
    op.execute("DROP TABLE IF EXISTS learned_bonds CASCADE")
    op.execute("DROP TABLE IF EXISTS hyp_bond_vocab CASCADE")
    op.execute("DROP TABLE IF EXISTS bonds CASCADE")
    op.execute("DROP TABLE IF EXISTS word_coordinates CASCADE")
