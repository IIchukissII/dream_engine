#!/bin/bash
# =============================================================================
# STORM-LOGOS AUTOMATED BACKUP SCRIPT
# =============================================================================
# Creates backups of PostgreSQL, Neo4j, and application data
#
# Usage:
#   ./backup.sh [full|postgres|neo4j|app]
#
# Cron example (daily at 3 AM):
#   0 3 * * * /opt/storm-logos/infrastructure/backups/backup.sh full >> /var/log/storm-logos-backup.log 2>&1
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================
BACKUP_TYPE="${1:-full}"
BACKUP_DIR="${BACKUP_DIR:-/mnt/data/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="storm-logos-${BACKUP_TYPE}-${DATE}"

# Docker container names
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-storm-postgres}"
NEO4J_CONTAINER="${NEO4J_CONTAINER:-storm-neo4j}"

# Database credentials (from environment or .env file)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

if [ -f "$PROJECT_ROOT/.env" ]; then
  source "$PROJECT_ROOT/.env"
fi

POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-semantic}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${RED}[ERROR]${NC} $1"; }

# =============================================================================
# SETUP
# =============================================================================
setup() {
  log_info "Setting up backup directory..."
  mkdir -p "$BACKUP_DIR"/{postgres,neo4j,app,temp}
  mkdir -p "$BACKUP_DIR/latest"
}

# =============================================================================
# POSTGRESQL BACKUP
# =============================================================================
backup_postgres() {
  log_info "Starting PostgreSQL backup..."

  local backup_file="$BACKUP_DIR/postgres/${BACKUP_NAME}.sql.gz"

  # Check if container is running
  if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    log_error "PostgreSQL container '$POSTGRES_CONTAINER' is not running"
    return 1
  fi

  # Create backup
  docker exec "$POSTGRES_CONTAINER" \
    pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists \
    | gzip > "$backup_file"

  local size=$(du -h "$backup_file" | cut -f1)
  log_info "PostgreSQL backup created: $backup_file ($size)"

  # Create latest symlink
  ln -sf "$backup_file" "$BACKUP_DIR/latest/postgres-latest.sql.gz"

  # Verify backup
  if gzip -t "$backup_file" 2>/dev/null; then
    log_info "PostgreSQL backup verified successfully"
  else
    log_error "PostgreSQL backup verification failed!"
    return 1
  fi
}

# =============================================================================
# NEO4J BACKUP
# =============================================================================
backup_neo4j() {
  log_info "Starting Neo4j backup..."

  local backup_file="$BACKUP_DIR/neo4j/${BACKUP_NAME}.dump"

  # Check if container is running
  if ! docker ps --format '{{.Names}}' | grep -q "^${NEO4J_CONTAINER}$"; then
    log_error "Neo4j container '$NEO4J_CONTAINER' is not running"
    return 1
  fi

  # Stop Neo4j for consistent backup (optional - can use online backup for Enterprise)
  log_info "Creating Neo4j dump..."

  # For Community Edition, we need to copy the data directory
  # First, create a temporary container to access the data
  docker exec "$NEO4J_CONTAINER" \
    neo4j-admin database dump neo4j --to-path=/tmp/ 2>/dev/null || {
      # Fallback: copy data directory directly
      log_warn "neo4j-admin dump failed, using data directory copy..."
      docker cp "${NEO4J_CONTAINER}:/data" "$BACKUP_DIR/temp/neo4j-data-${DATE}"
      tar -czf "$backup_file.tar.gz" -C "$BACKUP_DIR/temp" "neo4j-data-${DATE}"
      rm -rf "$BACKUP_DIR/temp/neo4j-data-${DATE}"
      backup_file="$backup_file.tar.gz"
    }

  # If dump succeeded, copy it out
  if docker exec "$NEO4J_CONTAINER" test -f /tmp/neo4j.dump 2>/dev/null; then
    docker cp "${NEO4J_CONTAINER}:/tmp/neo4j.dump" "$backup_file"
    docker exec "$NEO4J_CONTAINER" rm /tmp/neo4j.dump
  fi

  if [ -f "$backup_file" ] || [ -f "$backup_file.tar.gz" ]; then
    local actual_file="${backup_file}"
    [ -f "$backup_file.tar.gz" ] && actual_file="$backup_file.tar.gz"
    local size=$(du -h "$actual_file" | cut -f1)
    log_info "Neo4j backup created: $actual_file ($size)"
    ln -sf "$actual_file" "$BACKUP_DIR/latest/neo4j-latest.dump"
  else
    log_error "Neo4j backup failed!"
    return 1
  fi
}

# =============================================================================
# APPLICATION DATA BACKUP
# =============================================================================
backup_app() {
  log_info "Starting application data backup..."

  local backup_file="$BACKUP_DIR/app/${BACKUP_NAME}.tar.gz"

  # Backup important directories
  tar -czf "$backup_file" \
    -C "$PROJECT_ROOT" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='node_modules' \
    --exclude='.git' \
    storm_logos/sessions \
    storm_logos/config \
    .env \
    2>/dev/null || {
      log_warn "Some files could not be backed up (this may be normal)"
    }

  if [ -f "$backup_file" ]; then
    local size=$(du -h "$backup_file" | cut -f1)
    log_info "Application backup created: $backup_file ($size)"
    ln -sf "$backup_file" "$BACKUP_DIR/latest/app-latest.tar.gz"
  fi
}

# =============================================================================
# CLEANUP OLD BACKUPS
# =============================================================================
cleanup_old_backups() {
  log_info "Cleaning up backups older than $RETENTION_DAYS days..."

  local count=0

  for dir in postgres neo4j app; do
    if [ -d "$BACKUP_DIR/$dir" ]; then
      while IFS= read -r -d '' file; do
        rm -f "$file"
        ((count++))
      done < <(find "$BACKUP_DIR/$dir" -type f -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    fi
  done

  log_info "Removed $count old backup files"
}

# =============================================================================
# UPLOAD TO REMOTE (Optional - S3/Hetzner Storage Box)
# =============================================================================
upload_to_remote() {
  # Hetzner Storage Box example (via SFTP/rsync)
  if [ -n "${STORAGE_BOX_USER:-}" ] && [ -n "${STORAGE_BOX_HOST:-}" ]; then
    log_info "Uploading to Hetzner Storage Box..."
    rsync -avz --progress \
      "$BACKUP_DIR/latest/" \
      "${STORAGE_BOX_USER}@${STORAGE_BOX_HOST}:./backups/storm-logos/"
    log_info "Remote upload complete"
  fi

  # AWS S3 example
  if [ -n "${S3_BUCKET:-}" ] && command -v aws &> /dev/null; then
    log_info "Uploading to S3..."
    aws s3 sync "$BACKUP_DIR/latest/" "s3://${S3_BUCKET}/storm-logos/latest/"
    log_info "S3 upload complete"
  fi
}

# =============================================================================
# STATUS/VERIFY
# =============================================================================
show_status() {
  echo ""
  echo "============================================================================="
  echo "                    BACKUP STATUS"
  echo "============================================================================="
  echo ""
  echo "Backup Directory: $BACKUP_DIR"
  echo ""

  echo "Latest Backups:"
  if [ -d "$BACKUP_DIR/latest" ]; then
    ls -lh "$BACKUP_DIR/latest/" 2>/dev/null || echo "  No backups found"
  fi

  echo ""
  echo "Backup Sizes by Type:"
  for dir in postgres neo4j app; do
    if [ -d "$BACKUP_DIR/$dir" ]; then
      local size=$(du -sh "$BACKUP_DIR/$dir" 2>/dev/null | cut -f1)
      local count=$(find "$BACKUP_DIR/$dir" -type f 2>/dev/null | wc -l)
      echo "  $dir: $size ($count files)"
    fi
  done

  echo ""
  echo "Disk Usage:"
  df -h "$BACKUP_DIR" 2>/dev/null | tail -1

  echo ""
  echo "============================================================================="
}

# =============================================================================
# RESTORE FUNCTIONS
# =============================================================================
restore_postgres() {
  local backup_file="${1:-$BACKUP_DIR/latest/postgres-latest.sql.gz}"

  if [ ! -f "$backup_file" ]; then
    log_error "Backup file not found: $backup_file"
    return 1
  fi

  log_warn "This will OVERWRITE the current PostgreSQL database!"
  read -p "Are you sure? (yes/no): " confirm
  [ "$confirm" != "yes" ] && { log_info "Aborted"; return 0; }

  log_info "Restoring PostgreSQL from $backup_file..."
  gunzip -c "$backup_file" | docker exec -i "$POSTGRES_CONTAINER" \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

  log_info "PostgreSQL restore complete"
}

restore_neo4j() {
  local backup_file="${1:-$BACKUP_DIR/latest/neo4j-latest.dump}"

  if [ ! -f "$backup_file" ]; then
    log_error "Backup file not found: $backup_file"
    return 1
  fi

  log_warn "This will OVERWRITE the current Neo4j database!"
  read -p "Are you sure? (yes/no): " confirm
  [ "$confirm" != "yes" ] && { log_info "Aborted"; return 0; }

  log_info "Restoring Neo4j from $backup_file..."

  # Stop Neo4j, restore, start
  docker stop "$NEO4J_CONTAINER"
  docker cp "$backup_file" "${NEO4J_CONTAINER}:/tmp/restore.dump"
  docker start "$NEO4J_CONTAINER"

  # Wait for startup and restore
  sleep 10
  docker exec "$NEO4J_CONTAINER" \
    neo4j-admin database load neo4j --from-path=/tmp/ --overwrite-destination=true 2>/dev/null || {
      log_warn "Automated restore failed, manual intervention may be required"
    }

  log_info "Neo4j restore complete"
}

# =============================================================================
# MAIN
# =============================================================================
main() {
  log_info "Starting backup process (type: $BACKUP_TYPE)..."

  setup

  case "$BACKUP_TYPE" in
    full)
      backup_postgres
      backup_neo4j
      backup_app
      ;;
    postgres)
      backup_postgres
      ;;
    neo4j)
      backup_neo4j
      ;;
    app)
      backup_app
      ;;
    status)
      show_status
      exit 0
      ;;
    restore-postgres)
      restore_postgres "${2:-}"
      exit 0
      ;;
    restore-neo4j)
      restore_neo4j "${2:-}"
      exit 0
      ;;
    *)
      echo "Usage: $0 [full|postgres|neo4j|app|status|restore-postgres|restore-neo4j]"
      exit 1
      ;;
  esac

  cleanup_old_backups
  upload_to_remote

  log_info "Backup process completed successfully"
  show_status
}

main "$@"
