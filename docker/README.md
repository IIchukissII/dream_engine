# Storm-Logos Docker Setup

Docker configurations for local development and production deployment.

## Quick Start

### Local Development

```bash
# From project root
cd docker

# Start all services
docker-compose -f docker-compose.local.yml --env-file ../.env up -d

# View logs
docker-compose -f docker-compose.local.yml logs -f

# Stop services
docker-compose -f docker-compose.local.yml down

# Stop and remove volumes (full reset)
docker-compose -f docker-compose.local.yml down -v
```

## Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.local.yml` | Local development with alternate ports |
| `docker-compose.prod.yml` | Production with SSL and security |
| `docker-compose.simple.yml` | Minimal setup (API + databases only) |

## Services

### Local Development Ports

| Service | Container | Internal | External |
|---------|-----------|----------|----------|
| API | storm-api-local | 8000 | **8001** |
| Frontend | storm-frontend-local | 80 | **3001** |
| PostgreSQL | storm-postgres-local | 5432 | **5433** |
| Neo4j HTTP | storm-neo4j-local | 7474 | **7476** |
| Neo4j Bolt | storm-neo4j-local | 7687 | **7689** |
| Redis | storm-redis-local | 6379 | **6380** |

External ports are offset to avoid conflicts with existing services.

## Environment Variables

Create `.env` in project root:

```bash
# Required - LLM API Keys
GROQ_API_KEY=gsk_your_key_here
ANTHROPIC_API_KEY=sk-ant-your_key_here  # Optional

# LLM Model
LLM_MODEL=groq:llama-3.3-70b-versatile

# Database passwords (for local dev)
# These are set in docker-compose.local.yml with defaults
```

## Building Images

```bash
# Build all images
docker-compose -f docker-compose.local.yml build

# Build specific service
docker-compose -f docker-compose.local.yml build api
docker-compose -f docker-compose.local.yml build frontend

# Build without cache (force rebuild)
docker-compose -f docker-compose.local.yml build --no-cache api
```

## Dockerfiles

| File | Description |
|------|-------------|
| `Dockerfile.api` | Python FastAPI backend |
| `Dockerfile.frontend` | React + Vite, served by Nginx |
| `Dockerfile.therapist` | Therapist service (if separate) |
| `Dockerfile.semantic` | Semantic processing service |

## Volume Mounts

### Local Development

```yaml
volumes:
  # Hot reload - code changes reflect immediately
  - ../storm_logos:/app/storm_logos
  # Environment file
  - ../.env:/app/.env:ro
```

### Persistent Data

```yaml
volumes:
  postgres_local:    # PostgreSQL data
  neo4j_local:       # Neo4j graph data
  redis_local:       # Redis cache
```

## Health Checks

All services include health checks:

```bash
# Check all service health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Expected output:
# storm-frontend-local    Up 5 minutes (healthy)
# storm-api-local         Up 5 minutes (healthy)
# storm-neo4j-local       Up 6 minutes (healthy)
# storm-redis-local       Up 6 minutes (healthy)
# storm-postgres-local    Up 6 minutes (healthy)
```

## Nginx Configuration

| File | Purpose |
|------|---------|
| `nginx.conf` | Standard HTTP config with API proxy |
| `nginx.ssl.conf` | Production SSL/TLS config |

The frontend Nginx proxies `/api/*` requests to the API backend.

## Database Initialization

### PostgreSQL

Init scripts in `init-scripts/postgres/` run on first start:
- Creates tables for word coordinates
- Sets up user authentication tables

### Neo4j

After starting, import corpus data:

```bash
# From project root
source .venv/bin/activate
python infrastructure/scripts/neo4j_migrate.py import \
    --target-uri bolt://localhost:7689 \
    --target-password localdevpassword
```

## Troubleshooting

### Port Conflicts

If you see "port already in use" errors:

```bash
# Check what's using the port
lsof -i :5432  # PostgreSQL
lsof -i :7474  # Neo4j HTTP
lsof -i :7687  # Neo4j Bolt

# The local compose uses alternate ports (5433, 7476, 7689)
# to avoid conflicts
```

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.local.yml logs api

# Common issues:
# - Missing .env file: cp ../.env.example ../.env
# - Invalid API key: Check GROQ_API_KEY in .env
# - Port conflict: Check external ports aren't in use
```

### API Key Issues

```bash
# Verify API key is loaded in container
docker exec storm-api-local sh -c 'echo "Key length: ${#GROQ_API_KEY}"'
# Should show > 50 characters

# If key is missing, restart with env file:
docker-compose -f docker-compose.local.yml --env-file ../.env up -d api
```

### Database Connection Issues

```bash
# Test PostgreSQL
docker exec storm-postgres-local pg_isready -U postgres -d semantic

# Test Neo4j
curl http://localhost:7476

# Test Redis
docker exec storm-redis-local redis-cli ping
```

### Rebuild After Code Changes

```bash
# API changes - rebuild required for dependency changes
docker-compose -f docker-compose.local.yml build api
docker-compose -f docker-compose.local.yml up -d api

# Frontend changes - always rebuild
docker-compose -f docker-compose.local.yml build frontend
docker-compose -f docker-compose.local.yml up -d frontend
```

## Production Deployment

See `docker-compose.prod.yml` for production configuration.

Key differences from local:
- Standard ports (80, 443, 5432, 7687)
- SSL/TLS enabled
- No volume mounts for code (uses built images)
- Required environment variables (no defaults)
- Resource limits

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# With specific .env file
docker-compose -f docker-compose.prod.yml --env-file /path/to/.env.prod up -d
```

## Useful Commands

```bash
# Enter container shell
docker exec -it storm-api-local bash
docker exec -it storm-neo4j-local bash

# View real-time logs
docker-compose -f docker-compose.local.yml logs -f api

# Check resource usage
docker stats

# Prune unused images/containers
docker system prune -a
```
