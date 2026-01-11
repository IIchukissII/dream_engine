-- =============================================================================
-- STORM-LOGOS DATABASE SCHEMA
-- =============================================================================
-- PostgreSQL schema for semantic coordinates and learned data
-- =============================================================================

-- Word coordinates table (loaded from JSON)
CREATE TABLE IF NOT EXISTS word_coordinates (
    word VARCHAR(100) PRIMARY KEY,
    A FLOAT NOT NULL DEFAULT 0.0,
    S FLOAT NOT NULL DEFAULT 0.0,
    tau FLOAT NOT NULL DEFAULT 2.5,
    source VARCHAR(50) DEFAULT 'corpus',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bonds table (85K bonds with pre-computed A, S, tau from Neo4j)
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
);

-- Corpus bond vocabulary (6M+ bonds for lookup)
CREATE TABLE IF NOT EXISTS hyp_bond_vocab (
    bond VARCHAR(200) PRIMARY KEY,
    first_seen_order INTEGER,
    first_seen_book UUID,
    total_count INTEGER,
    book_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learned bonds from conversations
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
);

-- Learned words from conversations
CREATE TABLE IF NOT EXISTS learned_words (
    word VARCHAR(100) PRIMARY KEY,
    A FLOAT NOT NULL DEFAULT 0.0,
    S FLOAT NOT NULL DEFAULT 0.0,
    tau FLOAT NOT NULL DEFAULT 2.5,
    source VARCHAR(100) DEFAULT 'estimated',
    confidence FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(100) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100) REFERENCES users(user_id),
    mode VARCHAR(20) DEFAULT 'hybrid',
    status VARCHAR(20) DEFAULT 'active',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    summary TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bonds_noun ON bonds(noun);
CREATE INDEX IF NOT EXISTS idx_bonds_adj ON bonds(adj);
CREATE INDEX IF NOT EXISTS idx_bond_vocab_count ON hyp_bond_vocab(total_count DESC);
CREATE INDEX IF NOT EXISTS idx_learned_bonds_noun ON learned_bonds(noun);
CREATE INDEX IF NOT EXISTS idx_word_coordinates_source ON word_coordinates(source);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;
