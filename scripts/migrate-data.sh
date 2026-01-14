#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
DOCKER_COMPOSE_DIR=${DOCKER_COMPOSE_DIR:-/home/deploy/dream_engine}
K8S_NAMESPACE=${K8S_NAMESPACE:-storm-logos}
BACKUP_DIR=${BACKUP_DIR:-./backups/$(date +%Y%m%d_%H%M%S)}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL from Docker Compose
backup_postgres_docker() {
    echo_info "Backing up PostgreSQL from Docker Compose..."

    cd "$DOCKER_COMPOSE_DIR"
    docker compose -f docker-compose.prod.yml exec -T postgres pg_dumpall -U storm_logos > "$BACKUP_DIR/postgres_backup.sql"

    echo_info "PostgreSQL backup saved to $BACKUP_DIR/postgres_backup.sql"
}

# Backup Neo4j from Docker Compose
backup_neo4j_docker() {
    echo_info "Backing up Neo4j from Docker Compose..."

    cd "$DOCKER_COMPOSE_DIR"

    # Stop Neo4j for consistent backup
    docker compose -f docker-compose.prod.yml exec -T neo4j neo4j stop || true
    sleep 5

    # Create tar archive of Neo4j data
    docker compose -f docker-compose.prod.yml exec -T neo4j tar -czvf /tmp/neo4j_backup.tar.gz /data

    # Copy backup out of container
    docker compose -f docker-compose.prod.yml cp neo4j:/tmp/neo4j_backup.tar.gz "$BACKUP_DIR/neo4j_backup.tar.gz"

    # Restart Neo4j
    docker compose -f docker-compose.prod.yml exec -T neo4j neo4j start || true

    echo_info "Neo4j backup saved to $BACKUP_DIR/neo4j_backup.tar.gz"
}

# Backup Redis from Docker Compose
backup_redis_docker() {
    echo_info "Backing up Redis from Docker Compose..."

    cd "$DOCKER_COMPOSE_DIR"

    # Trigger BGSAVE
    docker compose -f docker-compose.prod.yml exec -T redis redis-cli BGSAVE
    sleep 5

    # Copy RDB file
    docker compose -f docker-compose.prod.yml cp redis:/data/dump.rdb "$BACKUP_DIR/redis_dump.rdb"

    echo_info "Redis backup saved to $BACKUP_DIR/redis_dump.rdb"
}

# Restore PostgreSQL to Kubernetes
restore_postgres_k8s() {
    echo_info "Restoring PostgreSQL to Kubernetes..."

    local POSTGRES_POD=$(kubectl get pods -n "$K8S_NAMESPACE" -l app=postgres -o jsonpath='{.items[0].metadata.name}')

    if [ -z "$POSTGRES_POD" ]; then
        echo_error "PostgreSQL pod not found in namespace $K8S_NAMESPACE"
        exit 1
    fi

    # Copy backup to pod
    kubectl cp "$BACKUP_DIR/postgres_backup.sql" "$K8S_NAMESPACE/$POSTGRES_POD:/tmp/postgres_backup.sql"

    # Restore database
    kubectl exec -n "$K8S_NAMESPACE" "$POSTGRES_POD" -- psql -U storm_logos -f /tmp/postgres_backup.sql

    echo_info "PostgreSQL restored successfully!"
}

# Restore Neo4j to Kubernetes
restore_neo4j_k8s() {
    echo_info "Restoring Neo4j to Kubernetes..."

    local NEO4J_POD=$(kubectl get pods -n "$K8S_NAMESPACE" -l app=neo4j -o jsonpath='{.items[0].metadata.name}')

    if [ -z "$NEO4J_POD" ]; then
        echo_error "Neo4j pod not found in namespace $K8S_NAMESPACE"
        exit 1
    fi

    # Stop Neo4j
    kubectl exec -n "$K8S_NAMESPACE" "$NEO4J_POD" -- neo4j stop || true
    sleep 5

    # Copy backup to pod
    kubectl cp "$BACKUP_DIR/neo4j_backup.tar.gz" "$K8S_NAMESPACE/$NEO4J_POD:/tmp/neo4j_backup.tar.gz"

    # Extract backup
    kubectl exec -n "$K8S_NAMESPACE" "$NEO4J_POD" -- tar -xzvf /tmp/neo4j_backup.tar.gz -C /

    # Restart Neo4j
    kubectl exec -n "$K8S_NAMESPACE" "$NEO4J_POD" -- neo4j start

    echo_info "Neo4j restored successfully!"
}

# Restore Redis to Kubernetes
restore_redis_k8s() {
    echo_info "Restoring Redis to Kubernetes..."

    local REDIS_POD=$(kubectl get pods -n "$K8S_NAMESPACE" -l app=redis -o jsonpath='{.items[0].metadata.name}')

    if [ -z "$REDIS_POD" ]; then
        echo_error "Redis pod not found in namespace $K8S_NAMESPACE"
        exit 1
    fi

    # Stop Redis
    kubectl exec -n "$K8S_NAMESPACE" "$REDIS_POD" -c redis -- redis-cli SHUTDOWN NOSAVE || true
    sleep 2

    # Copy backup to pod
    kubectl cp "$BACKUP_DIR/redis_dump.rdb" "$K8S_NAMESPACE/$REDIS_POD:/data/dump.rdb" -c redis

    # Redis will restart automatically via K8s

    echo_info "Redis restored successfully!"
}

# Full backup from Docker Compose
backup_all_docker() {
    echo_info "Starting full backup from Docker Compose..."

    backup_postgres_docker
    backup_neo4j_docker
    backup_redis_docker

    echo_info "All backups completed! Files saved to: $BACKUP_DIR"
}

# Full restore to Kubernetes
restore_all_k8s() {
    if [ ! -d "$BACKUP_DIR" ]; then
        echo_error "Backup directory not found: $BACKUP_DIR"
        echo_error "Please specify BACKUP_DIR environment variable"
        exit 1
    fi

    echo_info "Starting full restore to Kubernetes from: $BACKUP_DIR"

    restore_postgres_k8s
    restore_neo4j_k8s
    restore_redis_k8s

    echo_info "All databases restored successfully!"
}

# Show usage
usage() {
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  backup-docker      - Backup all databases from Docker Compose"
    echo "  restore-k8s        - Restore all databases to Kubernetes"
    echo "  backup-postgres    - Backup only PostgreSQL from Docker"
    echo "  backup-neo4j       - Backup only Neo4j from Docker"
    echo "  backup-redis       - Backup only Redis from Docker"
    echo "  restore-postgres   - Restore only PostgreSQL to K8s"
    echo "  restore-neo4j      - Restore only Neo4j to K8s"
    echo "  restore-redis      - Restore only Redis to K8s"
    echo ""
    echo "Environment variables:"
    echo "  DOCKER_COMPOSE_DIR - Path to Docker Compose project (default: /home/deploy/dream_engine)"
    echo "  K8S_NAMESPACE      - Kubernetes namespace (default: storm-logos)"
    echo "  BACKUP_DIR         - Backup directory (default: ./backups/TIMESTAMP)"
    echo ""
    echo "Examples:"
    echo "  $0 backup-docker           # Backup from Docker Compose"
    echo "  BACKUP_DIR=./backups/20260114 $0 restore-k8s  # Restore specific backup"
}

# Parse command
case "${1:-}" in
    backup-docker)
        backup_all_docker
        ;;
    restore-k8s)
        restore_all_k8s
        ;;
    backup-postgres)
        backup_postgres_docker
        ;;
    backup-neo4j)
        backup_neo4j_docker
        ;;
    backup-redis)
        backup_redis_docker
        ;;
    restore-postgres)
        restore_postgres_k8s
        ;;
    restore-neo4j)
        restore_neo4j_k8s
        ;;
    restore-redis)
        restore_redis_k8s
        ;;
    *)
        usage
        exit 1
        ;;
esac
