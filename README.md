# Storm-Logos

**Adaptive Semantic Generation System for Therapeutic AI**

An 8-layer system for dream analysis and therapy sessions using psychoanalytic principles, powered by LLMs (Groq/Claude) with semantic trajectory tracking in a 3D meaning space.

## Quick Start (Docker)

```bash
# 1. Clone and setup
cd dream_engine
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 2. Start all services
cd docker
docker-compose -f docker-compose.local.yml --env-file ../.env up -d

# 3. Restore corpus data (27 books, 85K+ bonds)
cd ..
source .venv/bin/activate
python infrastructure/scripts/neo4j_migrate.py import \
    --target-uri bolt://localhost:7689 \
    --target-password localdevpassword

# 4. Open the app
# Frontend: http://localhost:3001
# API Docs: http://localhost:8001/docs
# Neo4j:    http://localhost:7476
```

## Features

### Dream Analysis
Psychoanalytic dream interpretation with:
- Symbol extraction and archetype recognition (Shadow, Anima, Hero, etc.)
- Corpus resonance matching against Jung, Freud, mythology texts
- Semantic coordinate mapping (A=Affirmation, S=Sacred, τ=Abstraction)
- **Guest limit**: 3 free analyses per IP, unlimited for registered users

### Therapy Sessions
Interactive AI therapy with:
- Real-time emotional trajectory tracking
- Defense mechanism detection (minimization, intellectualization, irony)
- Session history and evolution profiles

### User Management
- JWT-based authentication (24-hour tokens)
- Email verification with secure tokens
- Password reset via email
- Rate limiting (5 auth requests/min, account lockout after 5 failed attempts)
- Superuser role for administrative actions

### Semantic Corpus
27 processed books with 85,157 semantic bonds:
- **Psychology**: Jung (5 books), Freud (6 books), Otto Rank
- **Mythology**: Homer, Ovid, Bulfinch, Frazer, Bible (KJV)
- **Literature**: Dostoevsky (4 books)
- **Admin only**: Adding new books requires superuser privileges

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite)                                    │
│  - Therapy chat, Dream analysis, Book library               │
├─────────────────────────────────────────────────────────────┤
│  API (FastAPI)                                              │
│  - Auth, Sessions, Dreams, Corpus endpoints                 │
├─────────────────────────────────────────────────────────────┤
│  Storm-Logos Engine (8 layers)                              │
│  - Semantic navigation, Metrics, Adaptive control           │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  - PostgreSQL (coordinates) + Neo4j (trajectories) + Redis  │
└─────────────────────────────────────────────────────────────┘
```

## Services

| Service | Local Port | Description |
|---------|------------|-------------|
| Frontend | 3001 | React UI with glassmorphism theme |
| API | 8001 | FastAPI with JWT auth |
| PostgreSQL | 5433 | Word coordinates, users |
| Neo4j | 7476 (HTTP), 7689 (Bolt) | Semantic graph, trajectories |
| Redis | 6380 | Session cache |

## Environment Variables

```bash
# Required
GROQ_API_KEY=gsk_...              # Get from console.groq.com
JWT_SECRET=your-secret-key        # Random 64-char hex string

# Optional
ANTHROPIC_API_KEY=sk-ant-...      # For Claude models
LLM_MODEL=groq:llama-3.3-70b-versatile

# Email (for verification/password reset)
EMAIL_SMTP_HOST=smtp.gmail.com    # Or your SMTP server
EMAIL_SMTP_PORT=465               # 465 for SSL, 587 for STARTTLS
EMAIL_USE_SSL=true
EMAIL_SMTP_USER=your@email.com
EMAIL_SMTP_PASSWORD=app-password
EMAIL_FROM_ADDRESS=noreply@yourdomain.com

# Access Control
SUPERUSER_USERS=admin,yourusername  # Comma-separated list
GUEST_DREAM_ANALYSIS_LIMIT=3        # Max analyses for guests
```

## API Endpoints

### Authentication
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/register` | POST | - | Create account (sends verification email) |
| `/auth/login` | POST | - | Get JWT token |
| `/auth/me` | GET | JWT | Get current user profile |
| `/auth/email/verify/{token}` | GET | - | Verify email address |
| `/auth/email/resend` | POST | JWT | Resend verification email |
| `/auth/password/forgot` | POST | - | Request password reset |
| `/auth/password/reset` | POST | - | Reset password with token |

### Dreams
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/dreams/analyze` | POST | Optional | Analyze a dream (guests: 3 max) |
| `/dreams/save` | POST | JWT | Save dream to collection |
| `/dreams/list` | GET | JWT | List saved dreams |

### Sessions
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/sessions/start` | POST | Optional | Start therapy session |
| `/sessions/{id}/message` | POST | Optional | Send message |
| `/sessions/{id}/end` | POST | Optional | End session |

### Corpus
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/corpus/books` | GET | - | List processed books |
| `/corpus/process` | POST | Superuser | Add book to corpus |

Full API documentation at `/docs` when running.

## Project Structure

```
dream_engine/
├── docker/                     # Docker configurations
│   ├── docker-compose.local.yml   # Local development
│   ├── docker-compose.prod.yml    # Production
│   ├── Dockerfile.api             # API image
│   └── Dockerfile.frontend        # Frontend image
├── infrastructure/             # Deployment & operations
│   ├── scripts/
│   │   ├── neo4j_migrate.py       # Data migration tool
│   │   ├── deploy.sh              # Deployment script
│   │   └── test-local.sh          # Local testing
│   ├── hetzner/                   # Cloud provisioning
│   └── backups/                   # Backup scripts
├── storm_logos/                # Core application
│   ├── services/
│   │   ├── api/                   # FastAPI backend
│   │   └── frontend-react/        # React frontend
│   ├── applications/              # Therapist, Analyzer
│   ├── data/                      # PostgreSQL, Neo4j clients
│   └── semantic/                  # Storm, Chain, Physics
├── data/
│   ├── gutenberg/                 # Source books (txt)
│   ├── migration/                 # Export CSVs for cloud
│   └── coordinates/               # Word coordinate data
└── requirements.txt
```

## Development

### Local Setup (without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Start services (requires local PostgreSQL, Neo4j, Redis)
uvicorn storm_logos.services.api.main:app --reload --port 8000

# Frontend
cd storm_logos/services/frontend-react
npm install && npm run dev
```

### Running Tests

```bash
# Run local test suite
./infrastructure/scripts/test-local.sh

# Full tests with cleanup
./infrastructure/scripts/test-local.sh --full --cleanup
```

## Data Migration

Export/import semantic corpus for cloud deployment:

```bash
# Export from source Neo4j
python infrastructure/scripts/neo4j_migrate.py export \
    --source-uri bolt://localhost:7687 \
    --source-password your_password

# Import to target Neo4j
python infrastructure/scripts/neo4j_migrate.py import \
    --target-uri bolt://neo4j:7687 \
    --target-password your_password

# Verify
python infrastructure/scripts/neo4j_migrate.py verify \
    --uri bolt://localhost:7689 \
    --password localdevpassword
```

## Cloud Deployment

See [HETZNER_DEPLOYMENT.md](HETZNER_DEPLOYMENT.md) for cloud deployment guide.

### Production Checklist

- [ ] Set strong passwords in `.env`
- [ ] Configure SSL certificates
- [ ] Set up automated backups
- [ ] Configure monitoring (Prometheus/Grafana)
- [ ] Run data migration

## Semantic Space

The system maps text to a 3D coordinate space:

| Axis | Name | Range | Meaning |
|------|------|-------|---------|
| A | Affirmation | -1 to +1 | bad ↔ good |
| S | Sacred | -1 to +1 | mundane ↔ elevated |
| τ | Tau | 0 to 5 | concrete ↔ abstract |

Example coordinates:
- "dark forest": A=+0.32, S=-0.01, τ=1.2
- "divine light": A=+0.85, S=+0.72, τ=3.8
- "simple chair": A=+0.10, S=-0.30, τ=0.5

## Corpus Statistics

| Category | Books | Bonds | Authors |
|----------|-------|-------|---------|
| Psychology | 12 | 56,781 | Jung, Freud, Rank |
| Mythology | 11 | 24,876 | Homer, Ovid, Frazer, Bulfinch |
| Literature | 4 | 16,084 | Dostoevsky |
| **Total** | **27** | **85,157** | - |

154,393 FOLLOWS edges connecting semantic bonds.

## Theory

Based on the RC-Model of semantic dynamics:

1. **Semantic Navigation**: Words exist in 3D space (A, S, τ)
2. **RC Dynamics**: State changes follow capacitor charge/discharge
3. **Chain Reaction**: Coherent sequences via resonance scoring
4. **Homeostasis**: Adaptive control maintains balance

## License

Research use only.

## Links

- [API Documentation](http://localhost:8001/docs) (when running)
- [Docker Setup](docker/README.md)
- [Infrastructure Guide](infrastructure/README.md)
- [Cloud Deployment](HETZNER_DEPLOYMENT.md)
