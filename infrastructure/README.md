# Storm-Logos Infrastructure

Deployment, migration, and operations scripts for Storm-Logos.

## Directory Structure

```
infrastructure/
├── scripts/
│   ├── neo4j_migrate.py    # Database migration tool
│   ├── deploy.sh           # Deployment automation
│   ├── test-local.sh       # Local testing suite
│   └── restore_neo4j.py    # Legacy restore script
├── hetzner/
│   └── provision.sh        # Hetzner Cloud provisioning
└── backups/
    └── backup.sh           # Automated backup script
```

## Data Migration

### neo4j_migrate.py

Portable migration tool for Neo4j semantic corpus data.

#### Export Data

```bash
# Export from source database
python infrastructure/scripts/neo4j_migrate.py export \
    --source-uri bolt://localhost:7687 \
    --source-password your_password \
    --export-dir ./data/migration

# Creates:
#   data/migration/books.csv    (27 books)
#   data/migration/bonds.csv    (85,157 bonds)
#   data/migration/follows.csv  (154,393 relationships)
```

#### Import Data

```bash
# Import to target database
python infrastructure/scripts/neo4j_migrate.py import \
    --target-uri bolt://localhost:7689 \
    --target-password localdevpassword \
    --export-dir ./data/migration
```

#### Full Migration

```bash
# Export + Import in one command
python infrastructure/scripts/neo4j_migrate.py migrate \
    --source-uri bolt://localhost:7687 \
    --source-password source_pass \
    --target-uri bolt://neo4j:7687 \
    --target-password target_pass
```

#### Verify Data

```bash
python infrastructure/scripts/neo4j_migrate.py verify \
    --uri bolt://localhost:7689 \
    --password localdevpassword
```

### Migration Files

Location: `data/migration/`

| File | Records | Description |
|------|---------|-------------|
| `books.csv` | 27 | Book metadata (id, title, author, genre) |
| `bonds.csv` | 85,157 | Semantic bonds (adj, noun, A, S, tau) |
| `follows.csv` | 154,393 | FOLLOWS relationships between bonds |

These files are portable and can be transferred to any environment.

## Deployment

### deploy.sh

Automated deployment script for remote servers.

```bash
# Build Docker images
./infrastructure/scripts/deploy.sh build

# Push to registry
./infrastructure/scripts/deploy.sh push

# Deploy to server
DEPLOY_HOST=your.server.com ./infrastructure/scripts/deploy.sh deploy

# Check status
DEPLOY_HOST=your.server.com ./infrastructure/scripts/deploy.sh status

# View logs
DEPLOY_HOST=your.server.com ./infrastructure/scripts/deploy.sh logs api

# Rollback
DEPLOY_HOST=your.server.com ./infrastructure/scripts/deploy.sh rollback

# Run migrations
DEPLOY_HOST=your.server.com ./infrastructure/scripts/deploy.sh migrate
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPLOY_HOST` | - | Remote server hostname |
| `DEPLOY_USER` | deploy | SSH username |
| `DEPLOY_PATH` | /opt/storm-logos | Installation path |
| `REGISTRY` | ghcr.io | Docker registry |
| `VERSION` | git SHA | Image version tag |

## Local Testing

### test-local.sh

Comprehensive local test suite.

```bash
# Quick tests (default)
./infrastructure/scripts/test-local.sh

# Full tests including rate limiting and dream analysis
./infrastructure/scripts/test-local.sh --full

# Cleanup after tests
./infrastructure/scripts/test-local.sh --cleanup
```

### Test Coverage

- Prerequisites (Docker, docker-compose, curl)
- Service startup and health checks
- PostgreSQL connectivity and tables
- Neo4j connectivity and data
- Redis connectivity
- API endpoints (health, auth, corpus)
- Rate limiting (full mode)
- Dream analysis (full mode, requires API key)

## Cloud Provisioning

### Hetzner Cloud

```bash
# Provision new server
./infrastructure/hetzner/provision.sh

# Requirements:
# - hcloud CLI installed and configured
# - SSH key uploaded to Hetzner
```

See [HETZNER_DEPLOYMENT.md](../HETZNER_DEPLOYMENT.md) for detailed guide.

### Server Options

| Provider | Plan | vCPU | RAM | Storage | Price |
|----------|------|------|-----|---------|-------|
| Hetzner | CPX41 | 8 | 16GB | 240GB | ~€28/mo |
| netcup | RS 2000 G12 | 6 | 16GB | 512GB | ~€12/mo |

## Backups

### backup.sh

Automated backup for all data stores.

```bash
# Run backup
./infrastructure/backups/backup.sh

# Creates timestamped backups:
#   backups/YYYYMMDD_HHMMSS/
#   ├── postgres.sql.gz
#   ├── neo4j/
#   └── app_data/
```

### Backup Schedule (Cron)

```bash
# Add to crontab for daily backups at 2 AM
0 2 * * * /opt/storm-logos/infrastructure/backups/backup.sh
```

### Restore from Backup

```bash
# PostgreSQL
gunzip -c backup/postgres.sql.gz | docker exec -i storm-postgres psql -U postgres -d semantic

# Neo4j
docker cp backup/neo4j/. storm-neo4j:/data/
docker restart storm-neo4j
```

## Database Migrations

### Alembic (PostgreSQL)

```bash
# Run migrations
python -m alembic -c storm_logos/migrations/alembic.ini upgrade head

# Create new migration
python -m alembic -c storm_logos/migrations/alembic.ini revision -m "description"

# Rollback
python -m alembic -c storm_logos/migrations/alembic.ini downgrade -1
```

### Migration Files

Location: `storm_logos/migrations/versions/`

| File | Description |
|------|-------------|
| `001_initial_schema.py` | Initial tables (users, sessions, coordinates) |
| `002_add_api_tracking.py` | API request logging, rate limiting |

## Monitoring

### Health Endpoints

| Endpoint | Description |
|----------|-------------|
| `/health` | Basic health check |
| `/health/ready` | Detailed readiness (all services) |
| `/health/live` | Liveness probe |
| `/metrics` | Prometheus metrics |

### Prometheus Metrics

```
storm_logos_requests_total
storm_logos_request_duration_seconds
storm_logos_active_sessions
storm_logos_bonds_total
```

### Log Aggregation

The API uses structured JSON logging for cloud aggregation:

```json
{
  "timestamp": "2026-01-11T14:30:00Z",
  "level": "INFO",
  "message": "Request processed",
  "request_id": "abc-123",
  "duration_ms": 45
}
```

## Security

### Production Checklist

- [ ] Change all default passwords
- [ ] Configure SSL/TLS certificates
- [ ] Enable rate limiting
- [ ] Set up firewall rules
- [ ] Configure CORS origins
- [ ] Use secrets management for API keys
- [ ] Enable audit logging
- [ ] Set up intrusion detection

### Environment Security

```bash
# Never commit .env files
# Use .env.example as template
cp .env.example .env

# Set proper permissions
chmod 600 .env

# Use environment-specific files
# .env.local, .env.staging, .env.production
```

## Troubleshooting

### Migration Issues

```bash
# Check source data
python infrastructure/scripts/neo4j_migrate.py verify \
    --uri bolt://localhost:7687 --password source_pass

# Check export files
wc -l data/migration/*.csv

# Verify import
python infrastructure/scripts/neo4j_migrate.py verify \
    --uri bolt://localhost:7689 --password target_pass
```

### Deployment Issues

```bash
# Check SSH connection
ssh deploy@your.server.com

# Check Docker on remote
ssh deploy@your.server.com "docker ps"

# Check logs
DEPLOY_HOST=your.server.com ./infrastructure/scripts/deploy.sh logs
```

### Service Recovery

```bash
# Restart specific service
docker-compose -f docker-compose.prod.yml restart api

# Full restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Check service health
curl http://localhost:8000/health/ready
```
