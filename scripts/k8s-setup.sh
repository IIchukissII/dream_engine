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

# Check prerequisites
check_prerequisites() {
    echo_info "Checking prerequisites..."

    local missing=""

    if ! command -v kubectl &> /dev/null; then
        missing+=" kubectl"
    fi

    if ! command -v kustomize &> /dev/null; then
        if ! kubectl kustomize --help &> /dev/null; then
            missing+=" kustomize"
        fi
    fi

    if ! command -v helm &> /dev/null; then
        missing+=" helm"
    fi

    if [ -n "$missing" ]; then
        echo_error "Missing required tools:$missing"
        exit 1
    fi

    echo_info "All prerequisites met!"
}

# Install cert-manager
install_cert_manager() {
    echo_info "Installing cert-manager..."

    if kubectl get namespace cert-manager &> /dev/null; then
        echo_warn "cert-manager namespace already exists, skipping installation"
        return
    fi

    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

    echo_info "Waiting for cert-manager to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/cert-manager -n cert-manager
    kubectl wait --for=condition=available --timeout=300s deployment/cert-manager-webhook -n cert-manager
    kubectl wait --for=condition=available --timeout=300s deployment/cert-manager-cainjector -n cert-manager

    echo_info "cert-manager installed successfully!"
}

# Install NGINX Ingress Controller
install_nginx_ingress() {
    echo_info "Installing NGINX Ingress Controller..."

    if kubectl get namespace ingress-nginx &> /dev/null; then
        echo_warn "ingress-nginx namespace already exists, skipping installation"
        return
    fi

    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo update

    helm install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.service.type=LoadBalancer

    echo_info "Waiting for NGINX Ingress Controller to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/ingress-nginx-controller -n ingress-nginx

    echo_info "NGINX Ingress Controller installed successfully!"
}

# Install ArgoCD
install_argocd() {
    echo_info "Installing ArgoCD..."

    if kubectl get namespace argocd &> /dev/null; then
        echo_warn "argocd namespace already exists, skipping installation"
        return
    fi

    kubectl create namespace argocd
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

    echo_info "Waiting for ArgoCD to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
    kubectl wait --for=condition=available --timeout=300s deployment/argocd-repo-server -n argocd

    # Get initial admin password
    echo_info "ArgoCD installed successfully!"
    echo_info "Initial admin password:"
    kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
    echo ""
}

# Install ArgoCD Image Updater
install_argocd_image_updater() {
    echo_info "Installing ArgoCD Image Updater..."

    if kubectl get deployment argocd-image-updater -n argocd &> /dev/null; then
        echo_warn "ArgoCD Image Updater already installed, skipping"
        return
    fi

    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml

    echo_info "Waiting for ArgoCD Image Updater to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/argocd-image-updater -n argocd

    echo_info "ArgoCD Image Updater installed successfully!"
}

# Deploy Storm-Logos application
deploy_storm_logos() {
    local ENVIRONMENT=${1:-production}
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

    echo_info "Deploying Storm-Logos to $ENVIRONMENT environment..."

    # Create secrets first (if not exists)
    if ! kubectl get secret storm-logos-secrets -n storm-logos &> /dev/null; then
        echo_warn "storm-logos-secrets not found. Creating from template..."
        echo_warn "Please update the secrets with actual values!"
    fi

    # Apply kustomization
    if command -v kustomize &> /dev/null; then
        kustomize build "$PROJECT_ROOT/k8s/overlays/$ENVIRONMENT" | kubectl apply -f -
    else
        kubectl apply -k "$PROJECT_ROOT/k8s/overlays/$ENVIRONMENT"
    fi

    echo_info "Storm-Logos deployed successfully!"
}

# Deploy ArgoCD Applications
deploy_argocd_apps() {
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

    echo_info "Deploying ArgoCD Applications..."

    kubectl apply -f "$PROJECT_ROOT/k8s/argocd/application-production.yaml"

    echo_info "ArgoCD Applications deployed!"
    echo_info "Access ArgoCD UI to monitor deployments"
}

# Main setup function
setup_cluster() {
    echo_info "Starting Storm-Logos Kubernetes Setup..."
    echo ""

    check_prerequisites
    install_cert_manager
    install_nginx_ingress
    install_argocd
    install_argocd_image_updater

    echo ""
    echo_info "=== Cluster Setup Complete ==="
    echo ""
    echo_info "Next steps:"
    echo "  1. Update secrets in k8s/overlays/production/kustomization.yaml"
    echo "  2. Configure GHCR credentials for ArgoCD Image Updater"
    echo "  3. Deploy applications: ./scripts/k8s-setup.sh deploy production"
    echo "  4. Or deploy via ArgoCD: ./scripts/k8s-setup.sh argocd"
    echo ""
    echo_info "ArgoCD UI: kubectl port-forward svc/argocd-server -n argocd 8080:443"
    echo_info "Default username: admin"
}

# Show usage
usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  setup              - Install all cluster dependencies (cert-manager, nginx, argocd)"
    echo "  deploy <env>       - Deploy Storm-Logos to specified environment (production/staging)"
    echo "  argocd             - Deploy ArgoCD Application manifests"
    echo "  cert-manager       - Install only cert-manager"
    echo "  nginx              - Install only NGINX Ingress Controller"
    echo "  argocd-install     - Install only ArgoCD"
    echo "  image-updater      - Install only ArgoCD Image Updater"
    echo ""
    echo "Examples:"
    echo "  $0 setup                    # Full cluster setup"
    echo "  $0 deploy production        # Deploy to production"
    echo "  $0 deploy staging           # Deploy to staging"
    echo "  $0 argocd                   # Deploy ArgoCD apps for GitOps"
}

# Parse command
case "${1:-}" in
    setup)
        setup_cluster
        ;;
    deploy)
        deploy_storm_logos "${2:-production}"
        ;;
    argocd)
        deploy_argocd_apps
        ;;
    cert-manager)
        check_prerequisites
        install_cert_manager
        ;;
    nginx)
        check_prerequisites
        install_nginx_ingress
        ;;
    argocd-install)
        check_prerequisites
        install_argocd
        ;;
    image-updater)
        check_prerequisites
        install_argocd_image_updater
        ;;
    *)
        usage
        exit 1
        ;;
esac
