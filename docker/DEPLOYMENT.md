# Storm-Logos Deployment Guide

## Quick Start (Development)

```bash
cd docker

# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f api
```

## Production Deployment

### Prerequisites

1. **SSL Certificates** - Place in `./ssl/`:
   - `cert.pem` - SSL certificate
   - `key.pem` - Private key

2. **Environment Variables** - All secrets must be set (no defaults):
   ```bash
   GROQ_API_KEY=your_key
   ANTHROPIC_API_KEY=your_key
   POSTGRES_PASSWORD=strong_password
   NEO4J_PASSWORD=strong_password
   JWT_SECRET=$(openssl rand -hex 32)
   CORS_ORIGINS=https://yourdomain.com
   ```

### Deploy

```bash
cd docker

# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Check health
curl https://yourdomain.com/health/ready
```

## SSL Certificate Setup

### Option 1: Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy to ssl directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/key.pem
sudo chown $USER:$USER ./ssl/*.pem
```

### Option 2: Self-Signed (Development Only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem \
  -subj "/CN=localhost"
```

### Option 3: Cloud Provider

- **AWS**: Use ACM with Application Load Balancer
- **GCP**: Use Google-managed certificates
- **Azure**: Use Azure Front Door or Application Gateway

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key for LLM |
| `ANTHROPIC_API_KEY` | No | Anthropic API key (optional) |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password |
| `NEO4J_PASSWORD` | Yes | Neo4j password |
| `JWT_SECRET` | Yes | JWT signing secret (32+ chars) |
| `CORS_ORIGINS` | Yes | Allowed CORS origins (comma-separated) |
| `LLM_MODEL` | No | Default: `groq:llama-3.3-70b-versatile` |
| `LOG_LEVEL` | No | Default: `INFO` |
| `ENVIRONMENT` | No | `development`, `staging`, `production` |

## Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/health` | Basic health check |
| `/health/ready` | Readiness (checks DB connections) |
| `/health/live` | Liveness probe |
| `/metrics` | Prometheus metrics |

## Monitoring

### Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'storm-logos'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
```

### Available Metrics

- `storm_logos_postgres_up` - PostgreSQL connectivity (0/1)
- `storm_logos_neo4j_up` - Neo4j connectivity (0/1)
- `storm_logos_rate_limit_tracked_ips` - IPs being rate-limited
- `storm_logos_requests_last_minute` - Request count

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      replicas: 3
```

### Database Scaling

For production, consider:
- PostgreSQL: Use managed service (RDS, Cloud SQL)
- Neo4j: Use Neo4j Aura or self-hosted cluster
- Redis: Use managed service (ElastiCache, Memorystore)

## Backup

### PostgreSQL

```bash
docker exec storm-postgres pg_dump -U postgres semantic > backup.sql
```

### Neo4j

```bash
docker exec storm-neo4j neo4j-admin database dump neo4j --to-path=/backups/
```

## Troubleshooting

### Check Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Check Health

```bash
# Basic health
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/health/ready

# Metrics
curl http://localhost:8000/metrics
```

### Common Issues

1. **Database connection failed**
   - Check `POSTGRES_PASSWORD` and `NEO4J_PASSWORD` are set
   - Ensure databases are healthy: `docker-compose ps`

2. **Rate limit exceeded**
   - Default: 60 requests/minute per IP
   - Check `/metrics` for `storm_logos_rate_limit_tracked_ips`

3. **CORS errors**
   - Verify `CORS_ORIGINS` includes your frontend domain
   - Include protocol: `https://yourdomain.com`

4. **SSL certificate errors**
   - Check certificate files exist in `./ssl/`
   - Verify certificate chain is complete
