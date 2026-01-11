# Storm-Logos: Hetzner Cloud Deployment Analysis

## Executive Summary

This document analyzes the Storm-Logos project for production deployment on Hetzner Cloud, including infrastructure recommendations, cost estimates, and migration steps.

---

## 1. Current Resource Analysis

### Application Services

| Service | CPU Limit | RAM Limit | RAM Reserved | Purpose |
|---------|-----------|-----------|--------------|---------|
| API Gateway | 2 cores | 2 GB | 512 MB | FastAPI main service |
| Therapist | 2 cores | 2 GB | 512 MB | Therapy processing |
| Semantic | 1 core | 1 GB | 256 MB | Semantic analysis |
| Frontend | 0.5 core | 256 MB | - | React + Nginx |
| **Subtotal** | **5.5 cores** | **5.25 GB** | **1.25 GB** | |

### Database Services

| Service | CPU Limit | RAM Limit | Storage | Purpose |
|---------|-----------|-----------|---------|---------|
| PostgreSQL | 1 core | 1 GB | ~1 GB | Coordinates, users, sessions |
| Neo4j | 2 cores | 2-4 GB | ~2 GB | Graph (85K bonds, 154K edges) |
| Redis | 0.5 core | 512 MB | ~100 MB | Cache, sessions |
| **Subtotal** | **3.5 cores** | **3.5-5.5 GB** | **~3 GB** | |

### Data Volumes

| Data | Size | Notes |
|------|------|-------|
| Coordinates JSON | 11 MB | Pre-computed word embeddings |
| Gutenberg Corpus | 84 MB | Source texts for processing |
| Neo4j Data | ~500 MB | Graph database files |
| PostgreSQL Data | ~200 MB | Relational data |
| **Total** | **~800 MB** | Initial, grows with usage |

### Total Requirements

| Resource | Minimum | Recommended | High Availability |
|----------|---------|-------------|-------------------|
| vCPUs | 4 | 8 | 16 |
| RAM | 8 GB | 16 GB | 32 GB |
| Storage | 40 GB | 80 GB | 160 GB |

---

## 2. Hetzner Cloud Infrastructure Options

### Option A: Single Server (Development/Small Production)

**Server: CPX41 (8 vCPU, 16 GB RAM, 240 GB SSD)**

```
┌─────────────────────────────────────────────────────────┐
│                    CPX41 Server                         │
│                   (8 vCPU, 16GB)                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Nginx  │  │   API   │  │Therapist │  │ Semantic │  │
│  │  (SSL)  │  │         │  │          │  │          │  │
│  └────┬────┘  └────┬────┘  └────┬─────┘  └────┬─────┘  │
│       │            │            │             │         │
│  ┌────┴────────────┴────────────┴─────────────┴────┐   │
│  │              Docker Network                      │   │
│  └────┬─────────────┬─────────────┬────────────────┘   │
│       │             │             │                     │
│  ┌────┴────┐  ┌─────┴─────┐  ┌────┴────┐               │
│  │PostgreSQL│  │   Neo4j   │  │  Redis  │               │
│  └─────────┘  └───────────┘  └─────────┘               │
│                                                         │
│  [Volume: 80GB for data persistence]                    │
└─────────────────────────────────────────────────────────┘
```

**Cost: ~€30/month**

| Item | Cost/Month |
|------|------------|
| CPX41 Server | €28.79 |
| 80GB Volume | €3.84 |
| Snapshots (2x) | €2.00 |
| **Total** | **~€35** |

**Pros:**
- Simple setup
- Low cost
- Easy management

**Cons:**
- Single point of failure
- No horizontal scaling
- Downtime during updates

---

### Option B: Multi-Server (Recommended Production)

**Architecture: Separate compute and data tiers**

```
                    ┌─────────────────┐
                    │  Hetzner Cloud  │
                    │  Load Balancer  │
                    │    (€5.39/mo)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
       ┌──────┴──────┐ ┌─────┴─────┐ ┌──────┴──────┐
       │   CPX21     │ │   CPX21   │ │   CPX21     │
       │  App Node 1 │ │ App Node 2│ │  App Node 3 │
       │ (Optional)  │ │           │ │ (Optional)  │
       └──────┬──────┘ └─────┬─────┘ └──────┬──────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────┴────────┐
                    │  Private Network │
                    │   (172.16.0.0)   │
                    └────────┬────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
┌──────┴──────┐      ┌───────┴───────┐     ┌──────┴──────┐
│    CX22     │      │     CX32      │     │    CX21     │
│  PostgreSQL │      │    Neo4j      │     │    Redis    │
│   Primary   │      │   (4GB RAM)   │     │   Cache     │
└─────────────┘      └───────────────┘     └─────────────┘
```

**Cost: ~€55-85/month**

| Component | Server Type | Cost/Month |
|-----------|-------------|------------|
| Load Balancer | LB11 | €5.39 |
| App Server 1 | CPX21 (3 vCPU, 4GB) | €14.39 |
| App Server 2 | CPX21 (optional) | €14.39 |
| PostgreSQL | CX22 (2 vCPU, 4GB) | €7.59 |
| Neo4j | CX32 (4 vCPU, 8GB) | €15.59 |
| Redis | CX21 (2 vCPU, 4GB) | €5.39 |
| Volumes (3x 20GB) | - | €2.88 |
| Backups | - | €3.00 |
| **Total (1 app)** | | **~€55** |
| **Total (2 apps)** | | **~€70** |

**Pros:**
- Separated concerns
- Can scale app tier independently
- Database servers dedicated
- Zero-downtime deployments possible

**Cons:**
- More complex setup
- Higher cost
- More servers to manage

---

### Option C: High Availability (Enterprise)

```
                         ┌─────────────┐
                         │   Floating  │
                         │     IP      │
                         └──────┬──────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
             ┌──────┴──────┐         ┌──────┴──────┐
             │ Load Balancer│         │Load Balancer│
             │   Primary    │         │   Standby   │
             └──────┬──────┘         └──────┬──────┘
                    │                       │
        ┌───────────┴───────────────────────┴───────────┐
        │                                               │
 ┌──────┴──────┐  ┌──────────┐  ┌──────────┐  ┌───────┴─────┐
 │  App Node 1 │  │App Node 2│  │App Node 3│  │  App Node 4 │
 │   (CPX21)   │  │  (CPX21) │  │  (CPX21) │  │   (CPX21)   │
 └──────┬──────┘  └────┬─────┘  └────┬─────┘  └──────┬──────┘
        │              │             │               │
        └──────────────┴─────────────┴───────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  Private Network  │
                    └─────────┬─────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
┌───┴───┐ ┌───────┐    ┌──────┴──────┐    ┌───────┐ ┌───┴───┐
│  PG   │ │  PG   │    │   Neo4j     │    │ Redis │ │ Redis │
│Primary│←│Replica│    │  (CCX23)    │    │Primary│←│Replica│
└───────┘ └───────┘    └─────────────┘    └───────┘ └───────┘
```

**Cost: ~€150-200/month**

---

## 3. Recommended Setup for Your Use Case

### **Recommendation: Option A (Single Server) to Start**

For initial production deployment, start with a single powerful server:

**Server: CPX41** (€28.79/month)
- 8 AMD vCPUs (dedicated)
- 16 GB RAM
- 240 GB NVMe SSD

**Additional:**
- 1x Volume 80GB for database persistence: €3.84/month
- Automated backups: €2.00/month
- Firewall: Free

**Total: ~€35/month**

This setup handles:
- ~100-500 concurrent therapy sessions
- ~10,000 daily API requests
- Full corpus of 85K bonds

---

## 4. Missing Components for Production

### Critical (Must Have)

| Component | Status | Action Required |
|-----------|--------|-----------------|
| SSL Certificates | ✅ Config ready | Generate with Let's Encrypt |
| Firewall Rules | ❌ Missing | Create Hetzner firewall |
| Backup Strategy | ⚠️ Partial | Add automated backups |
| Monitoring | ⚠️ Basic | Add Prometheus/Grafana or use Hetzner |
| Log Aggregation | ⚠️ Basic | Structured logging ready, need storage |
| Secrets Management | ⚠️ Basic | Currently .env files |

### Recommended (Should Have)

| Component | Status | Action Required |
|-----------|--------|-----------------|
| CI/CD Pipeline | ✅ Ready | GitHub Actions configured |
| Health Checks | ✅ Ready | /health/ready, /health/live |
| Rate Limiting | ✅ Ready | 60 req/min implemented |
| CORS Config | ✅ Ready | Environment configurable |
| Database Migrations | ❌ Missing | Add Alembic for PostgreSQL |
| Container Registry | ❌ Missing | Use Docker Hub or GitHub CR |

### Nice to Have

| Component | Status | Action Required |
|-----------|--------|-----------------|
| CDN | ❌ Missing | Cloudflare (free tier) |
| DDoS Protection | ❌ Missing | Cloudflare or Hetzner |
| APM (Application Performance) | ❌ Missing | Consider Sentry |
| Error Tracking | ❌ Missing | Consider Sentry |

---

## 5. Hetzner-Specific Configuration

### 5.1 Firewall Rules

```
Inbound Rules:
├── TCP 22   (SSH)      → Your IP only
├── TCP 80   (HTTP)     → 0.0.0.0/0 (redirect to HTTPS)
├── TCP 443  (HTTPS)    → 0.0.0.0/0
└── TCP 7474 (Neo4j UI) → Your IP only (optional)

Outbound Rules:
└── Allow all (for API calls to Groq/Anthropic)
```

### 5.2 Cloud-Init Script

```yaml
#cloud-config
package_update: true
package_upgrade: true

packages:
  - docker.io
  - docker-compose
  - certbot
  - fail2ban
  - ufw

runcmd:
  # Enable Docker
  - systemctl enable docker
  - systemctl start docker

  # Configure firewall
  - ufw default deny incoming
  - ufw default allow outgoing
  - ufw allow 22/tcp
  - ufw allow 80/tcp
  - ufw allow 443/tcp
  - ufw --force enable

  # Add deploy user
  - useradd -m -s /bin/bash -G docker deploy
```

### 5.3 Required Files to Create

1. **Hetzner Firewall Config** (via CLI or Console)
2. **Automated Backup Script**
3. **SSL Certificate Renewal Cron**
4. **Monitoring Stack (optional)**

---

## 6. Migration Checklist

### Pre-Migration

- [ ] Create Hetzner Cloud account
- [ ] Generate SSH keys for deployment
- [ ] Set up GitHub Container Registry or Docker Hub
- [ ] Rotate all API keys (Groq, Anthropic)
- [ ] Generate new JWT secret
- [ ] Create strong database passwords

### Server Setup

- [ ] Create CPX41 server in preferred location (Falkenstein/Nuremberg/Helsinki)
- [ ] Attach 80GB volume
- [ ] Configure firewall
- [ ] Set up DNS (A record pointing to server IP)
- [ ] Install Docker and Docker Compose
- [ ] Clone repository
- [ ] Configure .env with production values
- [ ] Generate SSL certificates with Let's Encrypt

### Deployment

- [ ] Build and push Docker images
- [ ] Start services with docker-compose.prod.yml
- [ ] Verify health checks pass
- [ ] Test all API endpoints
- [ ] Load corpus data into Neo4j
- [ ] Run initial therapy session test

### Post-Migration

- [ ] Set up automated backups
- [ ] Configure monitoring alerts
- [ ] Document runbook for operations
- [ ] Set up log rotation
- [ ] Performance baseline testing

---

## 7. Cost Summary

### Monthly Costs (Option A - Recommended Start)

| Item | Cost (EUR) |
|------|------------|
| CPX41 Server (8 vCPU, 16GB) | €28.79 |
| 80GB Volume | €3.84 |
| Automated Backups | €2.00 |
| Floating IP (optional) | €3.29 |
| **Total** | **€34.63 - €37.92** |

### Annual Cost

| Plan | Monthly | Annual | Savings |
|------|---------|--------|---------|
| Pay as you go | €35 | €420 | - |
| Reserved (12 months) | €30 | €360 | 14% |

### Comparison with Other Providers

| Provider | Equivalent | Monthly Cost |
|----------|------------|--------------|
| **Hetzner CPX41** | 8 vCPU, 16GB | **€29** |
| DigitalOcean | 8 vCPU, 16GB | $96 (~€88) |
| AWS EC2 t3.xlarge | 4 vCPU, 16GB | ~$120 (~€110) |
| Google Cloud e2-standard-4 | 4 vCPU, 16GB | ~$100 (~€92) |

**Hetzner is 3-4x cheaper than major cloud providers.**

---

## 8. Deployment Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| **1. Preparation** | Account setup, secrets rotation, DNS | 1 day |
| **2. Infrastructure** | Server creation, firewall, volumes | 2-4 hours |
| **3. Deployment** | Docker setup, SSL, app deployment | 4-6 hours |
| **4. Data Migration** | Corpus loading, database setup | 2-4 hours |
| **5. Testing** | Verification, load testing | 1 day |
| **6. Go-Live** | DNS switch, monitoring setup | 2-4 hours |
| **Total** | | **2-3 days** |

---

## 9. Next Steps

1. **Create missing infrastructure files** (Terraform/scripts)
2. **Set up container registry**
3. **Add database migration tooling**
4. **Create backup automation**
5. **Add monitoring stack**

Shall I proceed with creating these components?
