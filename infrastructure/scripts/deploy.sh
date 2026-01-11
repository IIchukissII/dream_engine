#!/bin/bash
# =============================================================================
# STORM-LOGOS DEPLOYMENT SCRIPT
# =============================================================================
# Handles building, deploying, and managing the application
#
# Usage:
#   ./deploy.sh [command] [options]
#
# Commands:
#   build       Build Docker images
#   push        Push images to registry
#   deploy      Deploy to server
#   rollback    Rollback to previous version
#   status      Check deployment status
#   logs        View logs
#   migrate     Run database migrations
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Docker registry (change for production)
REGISTRY="${REGISTRY:-ghcr.io}"
IMAGE_PREFIX="${IMAGE_PREFIX:-storm-logos}"
VERSION="${VERSION:-$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')}"

# Deployment target
DEPLOY_HOST="${DEPLOY_HOST:-}"
DEPLOY_USER="${DEPLOY_USER:-deploy}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/storm-logos}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# =============================================================================
# BUILD
# =============================================================================
cmd_build() {
  log_step "Building Docker images (version: $VERSION)..."

  cd "$PROJECT_ROOT"

  # Build API image
  log_info "Building API image..."
  docker build -t "${IMAGE_PREFIX}/api:${VERSION}" \
    -t "${IMAGE_PREFIX}/api:latest" \
    -f docker/Dockerfile.api .

  # Build Frontend image
  log_info "Building Frontend image..."
  docker build -t "${IMAGE_PREFIX}/frontend:${VERSION}" \
    -t "${IMAGE_PREFIX}/frontend:latest" \
    -f docker/Dockerfile.frontend .

  # Build Therapist image
  log_info "Building Therapist image..."
  docker build -t "${IMAGE_PREFIX}/therapist:${VERSION}" \
    -t "${IMAGE_PREFIX}/therapist:latest" \
    -f docker/Dockerfile.therapist .

  # Build Semantic image
  log_info "Building Semantic image..."
  docker build -t "${IMAGE_PREFIX}/semantic:${VERSION}" \
    -t "${IMAGE_PREFIX}/semantic:latest" \
    -f docker/Dockerfile.semantic .

  log_info "Build complete. Images:"
  docker images | grep "$IMAGE_PREFIX"
}

# =============================================================================
# PUSH
# =============================================================================
cmd_push() {
  log_step "Pushing images to registry..."

  for service in api frontend therapist semantic; do
    local image="${IMAGE_PREFIX}/${service}"

    log_info "Pushing ${image}:${VERSION}..."
    docker tag "${image}:${VERSION}" "${REGISTRY}/${image}:${VERSION}"
    docker tag "${image}:latest" "${REGISTRY}/${image}:latest"
    docker push "${REGISTRY}/${image}:${VERSION}"
    docker push "${REGISTRY}/${image}:latest"
  done

  log_info "Push complete"
}

# =============================================================================
# DEPLOY
# =============================================================================
cmd_deploy() {
  if [ -z "$DEPLOY_HOST" ]; then
    log_error "DEPLOY_HOST not set. Usage: DEPLOY_HOST=your.server.com ./deploy.sh deploy"
    exit 1
  fi

  log_step "Deploying to ${DEPLOY_HOST}..."

  # Create deployment package
  log_info "Creating deployment package..."
  local deploy_tar="/tmp/storm-logos-deploy-${VERSION}.tar.gz"

  tar -czf "$deploy_tar" \
    -C "$PROJECT_ROOT" \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='data/gutenberg' \
    docker \
    storm_logos/data/derived_coordinates.json \
    storm_logos/config \
    infrastructure \
    .env.example \
    requirements.txt

  # Upload to server
  log_info "Uploading to server..."
  scp "$deploy_tar" "${DEPLOY_USER}@${DEPLOY_HOST}:/tmp/"

  # Execute deployment on server
  log_info "Executing deployment..."
  ssh "${DEPLOY_USER}@${DEPLOY_HOST}" bash -s << REMOTE_SCRIPT
    set -euo pipefail

    echo "Extracting deployment package..."
    mkdir -p ${DEPLOY_PATH}
    cd ${DEPLOY_PATH}

    # Backup current deployment
    if [ -d docker ]; then
      echo "Backing up current deployment..."
      mv docker docker.backup.\$(date +%Y%m%d_%H%M%S) || true
    fi

    # Extract new deployment
    tar -xzf /tmp/storm-logos-deploy-${VERSION}.tar.gz

    # Check for .env file
    if [ ! -f .env ]; then
      echo "WARNING: .env file not found. Copying example..."
      cp .env.example .env
      echo "Please edit .env with production values!"
    fi

    # Pull latest images (if using registry)
    cd docker
    if [ -n "${REGISTRY:-}" ]; then
      echo "Pulling images from registry..."
      docker-compose -f docker-compose.prod.yml pull || true
    fi

    # Deploy with zero-downtime
    echo "Deploying services..."
    docker-compose -f docker-compose.prod.yml up -d --remove-orphans

    # Wait for health checks
    echo "Waiting for services to be healthy..."
    sleep 30

    # Check health
    curl -sf http://localhost:8000/health || {
      echo "Health check failed!"
      exit 1
    }

    echo "Deployment successful!"

    # Cleanup
    rm /tmp/storm-logos-deploy-${VERSION}.tar.gz
REMOTE_SCRIPT

  # Cleanup local
  rm "$deploy_tar"

  log_info "Deployment complete!"
}

# =============================================================================
# ROLLBACK
# =============================================================================
cmd_rollback() {
  if [ -z "$DEPLOY_HOST" ]; then
    log_error "DEPLOY_HOST not set"
    exit 1
  fi

  log_step "Rolling back on ${DEPLOY_HOST}..."

  ssh "${DEPLOY_USER}@${DEPLOY_HOST}" bash -s << 'REMOTE_SCRIPT'
    set -euo pipefail
    cd /opt/storm-logos

    # Find latest backup
    BACKUP=$(ls -td docker.backup.* 2>/dev/null | head -1)
    if [ -z "$BACKUP" ]; then
      echo "No backup found!"
      exit 1
    fi

    echo "Rolling back to: $BACKUP"

    # Stop current
    cd docker
    docker-compose -f docker-compose.prod.yml down || true
    cd ..

    # Restore backup
    rm -rf docker
    mv "$BACKUP" docker

    # Start
    cd docker
    docker-compose -f docker-compose.prod.yml up -d

    echo "Rollback complete"
REMOTE_SCRIPT

  log_info "Rollback complete"
}

# =============================================================================
# STATUS
# =============================================================================
cmd_status() {
  if [ -n "$DEPLOY_HOST" ]; then
    log_step "Checking status on ${DEPLOY_HOST}..."
    ssh "${DEPLOY_USER}@${DEPLOY_HOST}" bash -s << 'REMOTE_SCRIPT'
      cd /opt/storm-logos/docker 2>/dev/null || { echo "Not deployed"; exit 0; }

      echo "=== Container Status ==="
      docker-compose -f docker-compose.prod.yml ps

      echo ""
      echo "=== Health Checks ==="
      curl -s http://localhost:8000/health/ready 2>/dev/null || echo "API: unreachable"

      echo ""
      echo "=== Resource Usage ==="
      docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
REMOTE_SCRIPT
  else
    log_step "Checking local status..."
    cd "$PROJECT_ROOT/docker"
    docker-compose ps
  fi
}

# =============================================================================
# LOGS
# =============================================================================
cmd_logs() {
  local service="${1:-}"

  if [ -n "$DEPLOY_HOST" ]; then
    ssh "${DEPLOY_USER}@${DEPLOY_HOST}" \
      "cd /opt/storm-logos/docker && docker-compose -f docker-compose.prod.yml logs -f $service"
  else
    cd "$PROJECT_ROOT/docker"
    docker-compose logs -f $service
  fi
}

# =============================================================================
# MIGRATE
# =============================================================================
cmd_migrate() {
  log_step "Running database migrations..."

  if [ -n "$DEPLOY_HOST" ]; then
    ssh "${DEPLOY_USER}@${DEPLOY_HOST}" bash -s << 'REMOTE_SCRIPT'
      cd /opt/storm-logos
      source .env

      # Run Alembic migrations
      docker exec storm-api python -m alembic -c storm_logos/migrations/alembic.ini upgrade head
REMOTE_SCRIPT
  else
    cd "$PROJECT_ROOT"
    source .env 2>/dev/null || true
    python -m alembic -c storm_logos/migrations/alembic.ini upgrade head
  fi

  log_info "Migrations complete"
}

# =============================================================================
# LOCAL DEVELOPMENT
# =============================================================================
cmd_dev() {
  log_step "Starting local development environment..."
  cd "$PROJECT_ROOT/docker"

  # Use simple compose for local dev
  docker-compose -f docker-compose.simple.yml up -d

  log_info "Development environment started"
  log_info "API: http://localhost:8000"
  log_info "API Docs: http://localhost:8000/docs"
  log_info "Neo4j: http://localhost:7474"

  echo ""
  log_info "To view logs: docker-compose -f docker-compose.simple.yml logs -f"
  log_info "To stop: docker-compose -f docker-compose.simple.yml down"
}

# =============================================================================
# HELP
# =============================================================================
cmd_help() {
  cat << EOF
Storm-Logos Deployment Script

Usage: ./deploy.sh [command] [options]

Commands:
  build         Build all Docker images
  push          Push images to registry
  deploy        Deploy to remote server
  rollback      Rollback to previous version
  status        Check deployment status
  logs [svc]    View logs (optionally for specific service)
  migrate       Run database migrations
  dev           Start local development environment
  help          Show this help message

Environment Variables:
  DEPLOY_HOST   Remote server hostname
  DEPLOY_USER   SSH user (default: deploy)
  DEPLOY_PATH   Deployment path (default: /opt/storm-logos)
  REGISTRY      Docker registry (default: ghcr.io)
  VERSION       Image version tag (default: git SHA)

Examples:
  ./deploy.sh build
  ./deploy.sh dev
  DEPLOY_HOST=storm.example.com ./deploy.sh deploy
  DEPLOY_HOST=storm.example.com ./deploy.sh logs api
EOF
}

# =============================================================================
# MAIN
# =============================================================================
main() {
  local cmd="${1:-help}"
  shift || true

  case "$cmd" in
    build)    cmd_build "$@" ;;
    push)     cmd_push "$@" ;;
    deploy)   cmd_deploy "$@" ;;
    rollback) cmd_rollback "$@" ;;
    status)   cmd_status "$@" ;;
    logs)     cmd_logs "$@" ;;
    migrate)  cmd_migrate "$@" ;;
    dev)      cmd_dev "$@" ;;
    help|--help|-h) cmd_help ;;
    *)
      log_error "Unknown command: $cmd"
      cmd_help
      exit 1
      ;;
  esac
}

main "$@"
