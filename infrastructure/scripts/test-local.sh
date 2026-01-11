#!/bin/bash
# =============================================================================
# STORM-LOGOS LOCAL TESTING SCRIPT
# =============================================================================
# Tests the complete local setup including:
#   - Docker services
#   - Database connectivity
#   - API endpoints
#   - Health checks
#   - Basic functionality
#
# Usage:
#   ./test-local.sh [--quick|--full]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results
PASSED=0
FAILED=0
WARNINGS=0

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; ((WARNINGS++)); }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; ((FAILED++)); }
log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASSED++)); }
log_test() { echo -e "${BLUE}[TEST]${NC} $1"; }

# =============================================================================
# PREREQUISITES CHECK
# =============================================================================
check_prerequisites() {
  log_test "Checking prerequisites..."

  # Docker
  if command -v docker &> /dev/null; then
    log_pass "Docker installed: $(docker --version | head -1)"
  else
    log_error "Docker not installed"
    exit 1
  fi

  # Docker Compose
  if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    log_pass "Docker Compose installed"
  else
    log_error "Docker Compose not installed"
    exit 1
  fi

  # curl
  if command -v curl &> /dev/null; then
    log_pass "curl installed"
  else
    log_error "curl not installed"
    exit 1
  fi

  # jq (optional but helpful)
  if command -v jq &> /dev/null; then
    log_pass "jq installed"
  else
    log_warn "jq not installed (optional)"
  fi
}

# =============================================================================
# START SERVICES
# =============================================================================
start_services() {
  log_test "Starting Docker services..."

  cd "$PROJECT_ROOT/docker"

  # Check if .env exists
  if [ ! -f "../.env" ]; then
    log_warn ".env file not found, creating from example..."
    cp ../.env.example ../.env
  fi

  # Start services
  docker-compose -f docker-compose.local.yml up -d

  log_info "Waiting for services to start..."
  sleep 10
}

# =============================================================================
# WAIT FOR SERVICES
# =============================================================================
wait_for_service() {
  local name="$1"
  local url="$2"
  local max_attempts="${3:-30}"
  local attempt=1

  log_test "Waiting for $name to be ready..."

  while [ $attempt -le $max_attempts ]; do
    if curl -sf "$url" &> /dev/null; then
      log_pass "$name is ready"
      return 0
    fi
    echo -n "."
    sleep 2
    ((attempt++))
  done

  echo ""
  log_error "$name failed to start after $max_attempts attempts"
  return 1
}

# =============================================================================
# TEST POSTGRESQL
# =============================================================================
test_postgres() {
  log_test "Testing PostgreSQL..."

  # Check container
  if docker ps --format '{{.Names}}' | grep -q 'storm-postgres-local'; then
    log_pass "PostgreSQL container running"
  else
    log_error "PostgreSQL container not running"
    return 1
  fi

  # Check connection
  if docker exec storm-postgres-local pg_isready -U postgres -d semantic &> /dev/null; then
    log_pass "PostgreSQL accepting connections"
  else
    log_error "PostgreSQL not accepting connections"
    return 1
  fi

  # Check tables
  local table_count=$(docker exec storm-postgres-local \
    psql -U postgres -d semantic -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')

  if [ "${table_count:-0}" -gt 0 ]; then
    log_pass "PostgreSQL has $table_count tables"
  else
    log_warn "PostgreSQL has no tables (run migrations)"
  fi
}

# =============================================================================
# TEST NEO4J
# =============================================================================
test_neo4j() {
  log_test "Testing Neo4j..."

  # Check container
  if docker ps --format '{{.Names}}' | grep -q 'storm-neo4j-local'; then
    log_pass "Neo4j container running"
  else
    log_error "Neo4j container not running"
    return 1
  fi

  # Check HTTP interface
  if curl -sf http://localhost:7474 &> /dev/null; then
    log_pass "Neo4j HTTP interface accessible"
  else
    log_error "Neo4j HTTP interface not accessible"
    return 1
  fi

  # Check Bolt connection
  if curl -sf http://localhost:7474/db/neo4j/cluster/available &> /dev/null; then
    log_pass "Neo4j database available"
  else
    log_warn "Neo4j cluster endpoint not available (may be normal for Community Edition)"
  fi
}

# =============================================================================
# TEST REDIS
# =============================================================================
test_redis() {
  log_test "Testing Redis..."

  # Check container
  if docker ps --format '{{.Names}}' | grep -q 'storm-redis-local'; then
    log_pass "Redis container running"
  else
    log_error "Redis container not running"
    return 1
  fi

  # Check ping
  if docker exec storm-redis-local redis-cli ping | grep -q 'PONG'; then
    log_pass "Redis responding to ping"
  else
    log_error "Redis not responding"
    return 1
  fi
}

# =============================================================================
# TEST API
# =============================================================================
test_api() {
  log_test "Testing API..."

  local api_url="http://localhost:8000"

  # Wait for API
  wait_for_service "API" "$api_url/health" 60 || return 1

  # Basic health check
  local health=$(curl -sf "$api_url/health" 2>/dev/null)
  if echo "$health" | grep -q '"status"'; then
    log_pass "API health endpoint working"
  else
    log_error "API health endpoint failed"
    return 1
  fi

  # Detailed health check
  local ready=$(curl -sf "$api_url/health/ready" 2>/dev/null)
  if echo "$ready" | grep -q '"postgres"'; then
    log_pass "API ready endpoint working"

    # Check database connections
    if echo "$ready" | grep -q '"postgres": "healthy"'; then
      log_pass "API connected to PostgreSQL"
    else
      log_warn "API PostgreSQL connection issue"
    fi

    if echo "$ready" | grep -q '"neo4j": "healthy"'; then
      log_pass "API connected to Neo4j"
    else
      log_warn "API Neo4j connection issue"
    fi
  else
    log_error "API ready endpoint failed"
  fi

  # Metrics endpoint
  local metrics=$(curl -sf "$api_url/metrics" 2>/dev/null)
  if echo "$metrics" | grep -q 'storm_logos'; then
    log_pass "API metrics endpoint working"
  else
    log_warn "API metrics endpoint not working"
  fi

  # API docs
  if curl -sf "$api_url/docs" &> /dev/null; then
    log_pass "API docs accessible at $api_url/docs"
  else
    log_warn "API docs not accessible"
  fi
}

# =============================================================================
# TEST ENDPOINTS
# =============================================================================
test_endpoints() {
  log_test "Testing API endpoints..."

  local api_url="http://localhost:8000"

  # Root endpoint
  local root=$(curl -sf "$api_url/" 2>/dev/null)
  if echo "$root" | grep -q 'storm-logos'; then
    log_pass "Root endpoint returns service info"
  else
    log_error "Root endpoint failed"
  fi

  # Info endpoint
  local info=$(curl -sf "$api_url/info" 2>/dev/null)
  if echo "$info" | grep -q '"model"'; then
    log_pass "Info endpoint returns model info"
  else
    log_warn "Info endpoint issue"
  fi

  # Auth - Register (test user)
  local register=$(curl -sf -X POST "$api_url/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","password":"testpass123"}' 2>/dev/null)

  if echo "$register" | grep -q 'access_token\|already exists'; then
    log_pass "Auth register endpoint working"
  else
    log_warn "Auth register endpoint issue: $register"
  fi

  # Auth - Login
  local login=$(curl -sf -X POST "$api_url/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","password":"testpass123"}' 2>/dev/null)

  if echo "$login" | grep -q 'access_token'; then
    log_pass "Auth login endpoint working"

    # Extract token for further tests
    TOKEN=$(echo "$login" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
  else
    log_warn "Auth login endpoint issue"
    TOKEN=""
  fi

  # Corpus books endpoint
  local books=$(curl -sf "$api_url/corpus/books" 2>/dev/null)
  if echo "$books" | grep -q '"books"'; then
    log_pass "Corpus books endpoint working"
  else
    log_warn "Corpus books endpoint issue"
  fi
}

# =============================================================================
# TEST RATE LIMITING
# =============================================================================
test_rate_limiting() {
  log_test "Testing rate limiting..."

  local api_url="http://localhost:8000"

  # Make multiple rapid requests
  local count=0
  for i in {1..65}; do
    if curl -sf "$api_url/info" &> /dev/null; then
      ((count++))
    fi
  done

  if [ $count -lt 65 ]; then
    log_pass "Rate limiting is active (blocked after ~60 requests)"
  else
    log_warn "Rate limiting may not be working (all 65 requests succeeded)"
  fi
}

# =============================================================================
# FULL TEST
# =============================================================================
run_full_tests() {
  # Test dream analysis (requires API key)
  log_test "Testing dream analysis..."

  local api_url="http://localhost:8000"

  local dream_result=$(curl -sf -X POST "$api_url/dreams/analyze" \
    -H "Content-Type: application/json" \
    -d '{"dream":"I was walking through a dark forest and found a golden key."}' 2>/dev/null)

  if echo "$dream_result" | grep -q '"symbols"\|error'; then
    if echo "$dream_result" | grep -q '"symbols"'; then
      log_pass "Dream analysis endpoint working"
    else
      log_warn "Dream analysis returned error (may need API key): $(echo "$dream_result" | head -c 100)"
    fi
  else
    log_warn "Dream analysis endpoint not responding"
  fi
}

# =============================================================================
# CLEANUP
# =============================================================================
cleanup() {
  log_test "Cleaning up..."
  cd "$PROJECT_ROOT/docker"
  docker-compose -f docker-compose.local.yml down
  log_info "Services stopped"
}

# =============================================================================
# SUMMARY
# =============================================================================
print_summary() {
  echo ""
  echo "============================================================================="
  echo "                    TEST SUMMARY"
  echo "============================================================================="
  echo ""
  echo -e "  ${GREEN}PASSED:${NC}   $PASSED"
  echo -e "  ${RED}FAILED:${NC}   $FAILED"
  echo -e "  ${YELLOW}WARNINGS:${NC} $WARNINGS"
  echo ""

  if [ $FAILED -eq 0 ]; then
    echo -e "  ${GREEN}All critical tests passed!${NC}"
    echo ""
    echo "  Services are running at:"
    echo "    - API:     http://localhost:8000"
    echo "    - Docs:    http://localhost:8000/docs"
    echo "    - Metrics: http://localhost:8000/metrics"
    echo "    - Neo4j:   http://localhost:7474"
    echo ""
    echo "  To stop services: cd docker && docker-compose -f docker-compose.local.yml down"
  else
    echo -e "  ${RED}Some tests failed. Check logs above.${NC}"
  fi
  echo ""
  echo "============================================================================="

  return $FAILED
}

# =============================================================================
# MAIN
# =============================================================================
main() {
  local mode="${1:-quick}"

  echo "============================================================================="
  echo "       STORM-LOGOS LOCAL TESTING"
  echo "============================================================================="
  echo ""

  check_prerequisites
  start_services

  # Wait for all services
  wait_for_service "PostgreSQL" "localhost:5432" 30 || true
  wait_for_service "Neo4j" "http://localhost:7474" 60 || true
  wait_for_service "Redis" "localhost:6379" 30 || true

  # Run tests
  test_postgres
  test_neo4j
  test_redis
  test_api
  test_endpoints

  if [ "$mode" == "--full" ]; then
    test_rate_limiting
    run_full_tests
  fi

  print_summary

  if [ "${2:-}" == "--cleanup" ]; then
    cleanup
  fi
}

# Handle Ctrl+C
trap 'echo ""; log_warn "Interrupted"; exit 1' INT

main "$@"
