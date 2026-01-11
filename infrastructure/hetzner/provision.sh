#!/bin/bash
# =============================================================================
# STORM-LOGOS HETZNER CLOUD PROVISIONING SCRIPT
# =============================================================================
# This script provisions the complete infrastructure on Hetzner Cloud
#
# Prerequisites:
#   - hcloud CLI installed: https://github.com/hetznercloud/cli
#   - HCLOUD_TOKEN environment variable set
#   - SSH key added to Hetzner Cloud
#
# Usage:
#   export HCLOUD_TOKEN="your_token_here"
#   ./provision.sh [environment]
#
# Environments: dev, staging, prod (default: prod)
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================
ENV="${1:-prod}"
PROJECT_NAME="storm-logos"
LOCATION="fsn1"  # Falkenstein, Germany (cheapest EU location)

# Server configuration based on environment
case "$ENV" in
  dev)
    SERVER_TYPE="cpx21"      # 3 vCPU, 4GB RAM - €14.39/mo
    VOLUME_SIZE=40
    ;;
  staging)
    SERVER_TYPE="cpx31"      # 4 vCPU, 8GB RAM - €19.19/mo
    VOLUME_SIZE=60
    ;;
  prod)
    SERVER_TYPE="cpx41"      # 8 vCPU, 16GB RAM - €28.79/mo
    VOLUME_SIZE=80
    ;;
  *)
    echo "Unknown environment: $ENV"
    echo "Usage: $0 [dev|staging|prod]"
    exit 1
    ;;
esac

SERVER_NAME="${PROJECT_NAME}-${ENV}"
VOLUME_NAME="${PROJECT_NAME}-data-${ENV}"
FIREWALL_NAME="${PROJECT_NAME}-fw-${ENV}"
NETWORK_NAME="${PROJECT_NAME}-net-${ENV}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# PREREQUISITE CHECKS
# =============================================================================
check_prerequisites() {
  log_info "Checking prerequisites..."

  if ! command -v hcloud &> /dev/null; then
    log_error "hcloud CLI not found. Install from: https://github.com/hetznercloud/cli"
    exit 1
  fi

  if [ -z "${HCLOUD_TOKEN:-}" ]; then
    log_error "HCLOUD_TOKEN environment variable not set"
    echo "Get your token from: https://console.hetzner.cloud/projects/*/security/tokens"
    exit 1
  fi

  # Test token
  if ! hcloud server list &> /dev/null; then
    log_error "Invalid HCLOUD_TOKEN or API error"
    exit 1
  fi

  log_info "Prerequisites OK"
}

# =============================================================================
# SSH KEY
# =============================================================================
setup_ssh_key() {
  log_info "Setting up SSH key..."

  SSH_KEY_NAME="${PROJECT_NAME}-deploy"
  SSH_KEY_FILE="$HOME/.ssh/${SSH_KEY_NAME}"

  # Check if key exists in Hetzner
  if hcloud ssh-key describe "$SSH_KEY_NAME" &> /dev/null; then
    log_info "SSH key '$SSH_KEY_NAME' already exists in Hetzner"
  else
    # Generate new key if doesn't exist locally
    if [ ! -f "$SSH_KEY_FILE" ]; then
      log_info "Generating new SSH key..."
      ssh-keygen -t ed25519 -f "$SSH_KEY_FILE" -N "" -C "${PROJECT_NAME}-deploy"
    fi

    # Upload to Hetzner
    log_info "Uploading SSH key to Hetzner..."
    hcloud ssh-key create --name "$SSH_KEY_NAME" --public-key-from-file "${SSH_KEY_FILE}.pub"
  fi
}

# =============================================================================
# FIREWALL
# =============================================================================
create_firewall() {
  log_info "Creating firewall..."

  if hcloud firewall describe "$FIREWALL_NAME" &> /dev/null; then
    log_warn "Firewall '$FIREWALL_NAME' already exists, skipping..."
    return
  fi

  hcloud firewall create --name "$FIREWALL_NAME"

  # Inbound rules
  log_info "Adding firewall rules..."

  # SSH (port 22)
  hcloud firewall add-rule "$FIREWALL_NAME" \
    --direction in \
    --protocol tcp \
    --port 22 \
    --source-ips 0.0.0.0/0 \
    --source-ips ::/0 \
    --description "SSH"

  # HTTP (port 80)
  hcloud firewall add-rule "$FIREWALL_NAME" \
    --direction in \
    --protocol tcp \
    --port 80 \
    --source-ips 0.0.0.0/0 \
    --source-ips ::/0 \
    --description "HTTP"

  # HTTPS (port 443)
  hcloud firewall add-rule "$FIREWALL_NAME" \
    --direction in \
    --protocol tcp \
    --port 443 \
    --source-ips 0.0.0.0/0 \
    --source-ips ::/0 \
    --description "HTTPS"

  # ICMP (ping)
  hcloud firewall add-rule "$FIREWALL_NAME" \
    --direction in \
    --protocol icmp \
    --source-ips 0.0.0.0/0 \
    --source-ips ::/0 \
    --description "Ping"

  log_info "Firewall created successfully"
}

# =============================================================================
# PRIVATE NETWORK
# =============================================================================
create_network() {
  log_info "Creating private network..."

  if hcloud network describe "$NETWORK_NAME" &> /dev/null; then
    log_warn "Network '$NETWORK_NAME' already exists, skipping..."
    return
  fi

  hcloud network create --name "$NETWORK_NAME" --ip-range 10.0.0.0/16

  # Add subnet
  hcloud network add-subnet "$NETWORK_NAME" \
    --type server \
    --network-zone eu-central \
    --ip-range 10.0.1.0/24

  log_info "Network created successfully"
}

# =============================================================================
# VOLUME
# =============================================================================
create_volume() {
  log_info "Creating volume (${VOLUME_SIZE}GB)..."

  if hcloud volume describe "$VOLUME_NAME" &> /dev/null; then
    log_warn "Volume '$VOLUME_NAME' already exists, skipping..."
    return
  fi

  hcloud volume create \
    --name "$VOLUME_NAME" \
    --size "$VOLUME_SIZE" \
    --location "$LOCATION" \
    --format ext4

  log_info "Volume created successfully"
}

# =============================================================================
# SERVER
# =============================================================================
create_server() {
  log_info "Creating server ($SERVER_TYPE)..."

  if hcloud server describe "$SERVER_NAME" &> /dev/null; then
    log_warn "Server '$SERVER_NAME' already exists"
    return
  fi

  # Create cloud-init user data
  CLOUD_INIT=$(cat <<'EOF'
#cloud-config
package_update: true
package_upgrade: true

packages:
  - docker.io
  - docker-compose
  - certbot
  - python3-certbot-nginx
  - fail2ban
  - ufw
  - htop
  - ncdu
  - vim

users:
  - name: deploy
    groups: docker, sudo
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ${SSH_PUBLIC_KEY}

write_files:
  - path: /etc/docker/daemon.json
    content: |
      {
        "log-driver": "json-file",
        "log-opts": {
          "max-size": "50m",
          "max-file": "5"
        },
        "storage-driver": "overlay2"
      }

runcmd:
  # Enable services
  - systemctl enable docker
  - systemctl start docker
  - systemctl enable fail2ban
  - systemctl start fail2ban

  # Configure firewall
  - ufw default deny incoming
  - ufw default allow outgoing
  - ufw allow 22/tcp
  - ufw allow 80/tcp
  - ufw allow 443/tcp
  - ufw --force enable

  # Create app directory
  - mkdir -p /opt/storm-logos
  - chown deploy:deploy /opt/storm-logos

  # Mount volume (will be attached separately)
  - mkdir -p /mnt/data
  - echo "Volume mount point created"
EOF
)

  # Get SSH public key
  SSH_PUBLIC_KEY=$(cat "$HOME/.ssh/${PROJECT_NAME}-deploy.pub" 2>/dev/null || echo "")

  # Replace placeholder in cloud-init
  CLOUD_INIT="${CLOUD_INIT//\$\{SSH_PUBLIC_KEY\}/$SSH_PUBLIC_KEY}"

  # Create server
  hcloud server create \
    --name "$SERVER_NAME" \
    --type "$SERVER_TYPE" \
    --image ubuntu-22.04 \
    --location "$LOCATION" \
    --ssh-key "${PROJECT_NAME}-deploy" \
    --firewall "$FIREWALL_NAME" \
    --network "$NETWORK_NAME" \
    --user-data "$CLOUD_INIT"

  log_info "Server created, waiting for it to be ready..."
  sleep 30

  # Attach volume
  log_info "Attaching volume..."
  hcloud volume attach "$VOLUME_NAME" --server "$SERVER_NAME" --automount

  log_info "Server created successfully"
}

# =============================================================================
# OUTPUT
# =============================================================================
print_summary() {
  echo ""
  echo "============================================================================="
  echo "                    DEPLOYMENT SUMMARY"
  echo "============================================================================="
  echo ""

  SERVER_IP=$(hcloud server ip "$SERVER_NAME" 2>/dev/null || echo "N/A")

  echo "Environment:    $ENV"
  echo "Server:         $SERVER_NAME ($SERVER_TYPE)"
  echo "IP Address:     $SERVER_IP"
  echo "Volume:         $VOLUME_NAME (${VOLUME_SIZE}GB)"
  echo "Firewall:       $FIREWALL_NAME"
  echo "Network:        $NETWORK_NAME"
  echo "Location:       $LOCATION"
  echo ""
  echo "============================================================================="
  echo "                    NEXT STEPS"
  echo "============================================================================="
  echo ""
  echo "1. Wait ~2 minutes for cloud-init to complete"
  echo ""
  echo "2. SSH into the server:"
  echo "   ssh -i ~/.ssh/${PROJECT_NAME}-deploy deploy@${SERVER_IP}"
  echo ""
  echo "3. Clone and deploy:"
  echo "   cd /opt/storm-logos"
  echo "   git clone <your-repo-url> ."
  echo "   cp .env.example .env"
  echo "   # Edit .env with production values"
  echo "   cd docker"
  echo "   docker-compose -f docker-compose.prod.yml up -d"
  echo ""
  echo "4. Set up SSL certificate:"
  echo "   sudo certbot certonly --standalone -d yourdomain.com"
  echo "   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/ssl/cert.pem"
  echo "   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/ssl/key.pem"
  echo ""
  echo "5. Update DNS:"
  echo "   Add A record: yourdomain.com -> ${SERVER_IP}"
  echo ""
  echo "============================================================================="

  # Save deployment info
  cat > "deployment-${ENV}.info" <<EOINFO
SERVER_NAME=$SERVER_NAME
SERVER_IP=$SERVER_IP
SERVER_TYPE=$SERVER_TYPE
VOLUME_NAME=$VOLUME_NAME
FIREWALL_NAME=$FIREWALL_NAME
NETWORK_NAME=$NETWORK_NAME
LOCATION=$LOCATION
CREATED_AT=$(date -Iseconds)
EOINFO

  log_info "Deployment info saved to deployment-${ENV}.info"
}

# =============================================================================
# CLEANUP (for teardown)
# =============================================================================
cleanup() {
  log_warn "This will DELETE all resources for environment: $ENV"
  read -p "Are you sure? (yes/no): " confirm

  if [ "$confirm" != "yes" ]; then
    log_info "Aborted"
    exit 0
  fi

  log_info "Deleting server..."
  hcloud server delete "$SERVER_NAME" --ignore-missing || true

  log_info "Deleting volume..."
  hcloud volume delete "$VOLUME_NAME" --ignore-missing || true

  log_info "Deleting firewall..."
  hcloud firewall delete "$FIREWALL_NAME" --ignore-missing || true

  log_info "Deleting network..."
  hcloud network delete "$NETWORK_NAME" --ignore-missing || true

  log_info "Cleanup complete"
}

# =============================================================================
# MAIN
# =============================================================================
main() {
  echo "============================================================================="
  echo "       STORM-LOGOS HETZNER CLOUD PROVISIONING"
  echo "============================================================================="
  echo ""

  if [ "${2:-}" == "destroy" ]; then
    cleanup
    exit 0
  fi

  check_prerequisites
  setup_ssh_key
  create_firewall
  create_network
  create_volume
  create_server
  print_summary
}

main "$@"
