#!/bin/bash
# =============================================================================
# STORM-LOGOS DOCKER STARTUP SCRIPT
# =============================================================================
# Usage:
#   ./start.sh              # Start with full microservices
#   ./start.sh simple       # Start simple deployment
#   ./start.sh dev          # Start for development (with hot reload)
#   ./start.sh stop         # Stop all services
#   ./start.sh logs         # View logs
#   ./start.sh status       # Check service status
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check for .env file
check_env() {
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            log_warn ".env file not found. Copying from .env.example..."
            cp .env.example .env
            log_warn "Please edit .env with your API keys before starting."
            exit 1
        else
            log_error ".env file not found!"
            exit 1
        fi
    fi
}

# Start full microservices deployment
start_full() {
    log_info "Starting Storm-Logos (full microservices)..."
    check_env
    docker-compose up -d
    log_success "Services started!"
    echo ""
    echo "Services:"
    echo "  - API:        http://localhost:8000"
    echo "  - Frontend:   http://localhost:3000"
    echo "  - Therapist:  http://localhost:8001"
    echo "  - Semantic:   http://localhost:8002"
    echo "  - Neo4j:      http://localhost:7474"
    echo "  - PostgreSQL: localhost:5432"
    echo ""
    echo "Use './start.sh logs' to view logs"
}

# Start simple deployment
start_simple() {
    log_info "Starting Storm-Logos (simple deployment)..."
    check_env
    docker-compose -f docker-compose.simple.yml up -d
    log_success "Services started!"
    echo ""
    echo "Services:"
    echo "  - API:        http://localhost:8000"
    echo "  - Frontend:   http://localhost:3000"
    echo "  - Neo4j:      http://localhost:7474"
    echo "  - PostgreSQL: localhost:5432"
}

# Start for development
start_dev() {
    log_info "Starting Storm-Logos (development mode)..."
    check_env

    # Start only databases
    docker-compose -f docker-compose.simple.yml up -d postgres neo4j

    log_success "Databases started!"
    echo ""
    echo "Databases running:"
    echo "  - Neo4j:      http://localhost:7474"
    echo "  - PostgreSQL: localhost:5432"
    echo ""
    echo "Start API manually with:"
    echo "  cd .. && uvicorn storm_logos.services.api.main:app --reload --port 8000"
    echo ""
    echo "Start frontend with:"
    echo "  cd ../services/frontend-react && npm run dev"
}

# Stop all services
stop() {
    log_info "Stopping all services..."
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.simple.yml down 2>/dev/null || true
    log_success "Services stopped."
}

# View logs
logs() {
    SERVICE=${2:-""}
    if [ -n "$SERVICE" ]; then
        docker-compose logs -f "$SERVICE"
    else
        docker-compose logs -f
    fi
}

# Check status
status() {
    log_info "Service Status:"
    echo ""
    docker-compose ps 2>/dev/null || docker-compose -f docker-compose.simple.yml ps 2>/dev/null
}

# Build images
build() {
    log_info "Building Docker images..."
    docker-compose build
    log_success "Images built!"
}

# Clean up
clean() {
    log_warn "This will remove all containers, volumes, and images..."
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --rmi all
        docker-compose -f docker-compose.simple.yml down -v --rmi all
        log_success "Cleanup complete."
    fi
}

# Main
case "${1:-full}" in
    full)
        start_full
        ;;
    simple)
        start_simple
        ;;
    dev)
        start_dev
        ;;
    stop)
        stop
        ;;
    logs)
        logs "$@"
        ;;
    status)
        status
        ;;
    build)
        build
        ;;
    clean)
        clean
        ;;
    *)
        echo "Storm-Logos Docker Manager"
        echo ""
        echo "Usage: $0 {full|simple|dev|stop|logs|status|build|clean}"
        echo ""
        echo "Commands:"
        echo "  full    - Start full microservices deployment"
        echo "  simple  - Start simple deployment (API + Frontend + DBs)"
        echo "  dev     - Start only databases for local development"
        echo "  stop    - Stop all services"
        echo "  logs    - View logs (optionally specify service name)"
        echo "  status  - Check service status"
        echo "  build   - Build Docker images"
        echo "  clean   - Remove all containers, volumes, and images"
        ;;
esac
