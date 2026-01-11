# Storm-Logos Migration to netcup VPS 1000 G11

Migration plan for deploying Storm-Logos to netcup x86 VPS.

## Server Specifications

| Spec | Value |
|------|-------|
| Provider | netcup |
| Plan | VPS 1000 G11 (starter) |
| CPU | AMD EPYC, 4 vCores |
| RAM | 8 GB DDR5 ECC |
| Storage | ~250 GB NVMe |
| Architecture | x86_64 |
| OS | Ubuntu 24.04 LTS |
| Price | ~€5-8/month |
| Locations | Nuremberg, Vienna, Amsterdam, Manassas |

### Upgrade Path

| Plan | vCores | RAM | Storage | Price |
|------|--------|-----|---------|-------|
| VPS 1000 G11 | 4 | 8 GB | 250 GB | ~€5-8/mo |
| VPS 2000 G11 | 6 | 16 GB | 500 GB | ~€10/mo |
| VPS 3000 G11 | 10 | 24 GB | 750 GB | ~€12-17/mo |

Upgrade via netcup panel without data loss.

## Data Inventory

### Neo4j (Semantic Graph)

| Data | Records | Description |
|------|---------|-------------|
| Books | 27 | Processed corpus books |
| Bonds | 85,157 | Adjective-noun semantic units |
| FOLLOWS | 154,393 | Bond sequence relationships |
| CONTAINS | 112,137 | Book-to-bond relationships |

### PostgreSQL (Lookup Data)

| Table | Records | Description |
|-------|---------|-------------|
| hyp_bond_vocab | 6,042,021 | Hypothetical bond vocabulary |
| word_coordinates | 27,808 | Word A/S/tau coordinates |
| learned_bonds | 12 | User-learned bonds |

**Total: 6,421,555 records**

## Pre-Migration Checklist

### 1. Local Preparation

- [ ] Export all data using migration script
  ```bash
  source .venv/bin/activate
  python infrastructure/scripts/migrate.py export \
      --neo4j-uri bolt://localhost:7687 \
      --neo4j-password <source-password> \
      --pg-host localhost \
      --pg-port 5432 \
      --pg-password <pg-password>
  ```
- [ ] Verify export files exist in `data/migration/`:
  - `neo4j_books.csv` (27 records)
  - `neo4j_bonds.csv` (85,157 records)
  - `neo4j_follows.csv` (154,393 records)
  - `pg_hyp_bond_vocab.csv` (6M+ records) or use backup
  - `manifest.json` (export metadata)
- [ ] Prepare production `.env` file with real credentials
- [ ] Generate strong passwords for all services
- [ ] Obtain domain name (optional, can use IP initially)

### 2. Server Provisioning

- [ ] Order netcup VPS 1000 G11 (or G12)
- [ ] Select Ubuntu 24.04 LTS image
- [ ] Configure SSH key access
- [ ] Note server IP address
- [ ] Configure DNS A record (if using domain)

## Migration Steps

### Step 1: Initial Server Setup

```bash
# Connect to server
ssh root@<server-ip>

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
apt install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Create deploy user
useradd -m -s /bin/bash -G docker deploy
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
```

### Step 2: Firewall Configuration

```bash
# Install and configure UFW
apt install -y ufw

# Allow SSH
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable
ufw status
```

### Step 3: Deploy Application

```bash
# Switch to deploy user
su - deploy

# Clone repository
git clone https://github.com/IIchukissII/dream_engine.git
cd dream_engine

# Create production environment file
cp .env.example .env
nano .env  # Edit with production values
```

### Step 4: Production Environment Variables

Create `/home/deploy/dream_engine/.env`:

```bash
# LLM API Keys
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...  # Optional
LLM_MODEL=groq:llama-3.3-70b-versatile

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=semantic
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<strong-password-here>

# Neo4j (reduced memory for 8GB server)
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<strong-password-here>
NEO4J_HEAP_SIZE=1G
NEO4J_PAGECACHE_SIZE=512M

# Redis
REDIS_URL=redis://redis:6379/0

# API Security
JWT_SECRET=<generate-with-openssl-rand-hex-32>
CORS_ORIGINS=https://yourdomain.com

# Production settings
DEBUG=false
LOG_LEVEL=INFO
```

Generate secure passwords:
```bash
# Generate JWT secret
openssl rand -hex 32

# Generate database passwords
openssl rand -base64 24
```

### Step 5: Memory Tuning for 8GB Server

Update `docker-compose.prod.yml` Neo4j settings:

```yaml
neo4j:
  environment:
    - NEO4J_dbms_memory_heap_initial__size=1G
    - NEO4J_dbms_memory_heap_max__size=1G
    - NEO4J_dbms_memory_pagecache_size=512M
  deploy:
    resources:
      limits:
        memory: 2G
```

PostgreSQL tuning (optional):
```yaml
postgres:
  command: >
    postgres
    -c shared_buffers=256MB
    -c effective_cache_size=512MB
    -c work_mem=16MB
```

### Step 6: Build and Start Services

```bash
cd docker

# Build all images
docker compose -f docker-compose.prod.yml build

# Start all services
docker compose -f docker-compose.prod.yml up -d

# Check status
docker compose -f docker-compose.prod.yml ps

# Check memory usage
docker stats --no-stream
```

Expected memory usage (~5-6GB total):
| Service | Memory |
|---------|--------|
| Neo4j | ~1.5-2 GB |
| PostgreSQL | ~300 MB |
| API | ~200-400 MB |
| Frontend | ~50 MB |
| Redis | ~50 MB |

### Step 7: Import All Data

```bash
# Copy migration files to server (from local machine)
scp -r data/migration deploy@<server-ip>:~/dream_engine/data/
scp -r data/backup deploy@<server-ip>:~/dream_engine/data/
scp -r data/coordinates deploy@<server-ip>:~/dream_engine/data/

# On server: Import Neo4j + PostgreSQL data
cd ~/dream_engine
source .venv/bin/activate  # If using venv

python infrastructure/scripts/migrate.py import \
    --neo4j-uri bolt://localhost:7687 \
    --neo4j-password <neo4j-password> \
    --pg-host localhost \
    --pg-port 5432 \
    --pg-password <pg-password>

# Verify import
python infrastructure/scripts/migrate.py verify \
    --neo4j-uri bolt://localhost:7687 \
    --neo4j-password <neo4j-password> \
    --pg-host localhost \
    --pg-port 5432 \
    --pg-password <pg-password>

# Expected output:
# Neo4j:
#   books: 27
#   bonds: 85,157
#   follows: 154,393
#   contains: 112,137
# PostgreSQL:
#   hyp_bond_vocab: 6,042,021
#   word_coordinates: 27,808
#   learned_bonds: 12
```

### Step 8: SSL/TLS Setup (Optional)

Skip if testing with IP only. Add later when ready for production.

```bash
# Install Certbot
apt install -y certbot

# Stop frontend temporarily
docker compose -f docker-compose.prod.yml stop frontend

# Get certificate
certbot certonly --standalone -d yourdomain.com

# Copy certificates
mkdir -p docker/ssl
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/ssl/

# Restart frontend with SSL
docker compose -f docker-compose.prod.yml up -d frontend
```

### Step 9: Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# Check corpus loaded
curl http://localhost:8000/corpus/books | jq '.total'
# Expected: 27

# Test from external (replace with your IP)
curl http://<server-ip>:8000/health
```

## Post-Migration Tasks

### 1. Set Up Automated Backups

```bash
# Create backup directory
mkdir -p /home/deploy/backups

# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /home/deploy/dream_engine/infrastructure/backups/backup.sh >> /home/deploy/backups/backup.log 2>&1
```

### 2. Monitor Memory Usage

```bash
# Check if running low on memory
free -h
docker stats

# If consistently >80% memory used, consider upgrading to VPS 2000/3000
```

## Verification Checklist

After migration, verify each component:

- [ ] **API Health**: http://<server-ip>:8000/health returns OK
- [ ] **API Docs**: http://<server-ip>:8000/docs accessible
- [ ] **Neo4j Data**: Corpus has 27 books, 85K bonds
- [ ] **Memory**: Usage under 80% (~6.4GB)
- [ ] **Dream Analysis**: Test dream interpretation works
- [ ] **Auth**: Can register and login

## When to Upgrade

Upgrade to VPS 2000/3000 if:
- Memory consistently >80% used
- Response times degrading
- Need more concurrent users
- Adding more books to corpus

## Troubleshooting

### Out of Memory

```bash
# Check what's using memory
docker stats

# Reduce Neo4j heap if needed
# Edit docker-compose.prod.yml:
# NEO4J_dbms_memory_heap_max__size=768M

# Restart
docker compose -f docker-compose.prod.yml restart neo4j
```

### Services Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs api
docker compose -f docker-compose.prod.yml logs neo4j

# Check disk space
df -h
```

## Cost Summary

| Item | Cost |
|------|------|
| VPS 1000 G11 | ~€5-8/month |
| Domain (optional) | ~€10-15/year |
| SSL (Let's Encrypt) | Free |
| **Total** | **~€5-8/month** |

## Timeline

| Task | Duration |
|------|----------|
| Server provisioning | 30 min |
| Initial setup | 30 min |
| Build & deploy | 15 min |
| Import corpus | 15 min |
| Testing | 30 min |
| **Total** | **~2 hours** |

## References

- [netcup VPS G11](https://www.netcup.com/en/server/vps)
- [Docker Documentation](https://docs.docker.com/)
- [Neo4j Memory Configuration](https://neo4j.com/docs/operations-manual/current/performance/memory-configuration/)
