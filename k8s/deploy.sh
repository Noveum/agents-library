#!/bin/bash

# Deployment script for AI Agents Library API on Kubernetes
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="agents-library"
IMAGE_NAME="agents-library"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker is installed (for building)
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we can connect to Kubernetes cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    cd "$(dirname "$0")/.."
    
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
    fi
    
    docker build -t "$FULL_IMAGE_NAME" .
    
    if [ -n "$REGISTRY" ]; then
        log_info "Pushing image to registry..."
        docker push "$FULL_IMAGE_NAME"
    fi
    
    log_success "Docker image built: $FULL_IMAGE_NAME"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace..."
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        kubectl apply -f k8s/namespace.yaml
        log_success "Namespace $NAMESPACE created"
    fi
}

# Create secrets
create_secrets() {
    log_info "Creating secrets..."
    
    # Check if secrets already exist
    if kubectl get secret agents-api-secrets -n "$NAMESPACE" &> /dev/null; then
        log_warning "Secrets already exist. Skipping creation."
        log_info "To update secrets, delete them first: kubectl delete secret agents-api-secrets -n $NAMESPACE"
        return
    fi
    
    # Prompt for API keys if not set as environment variables
    if [ -z "$OPENAI_API_KEY" ]; then
        read -p "Enter OpenAI API Key (or press Enter to skip): " OPENAI_API_KEY
    fi
    
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        read -p "Enter Anthropic API Key (or press Enter to skip): " ANTHROPIC_API_KEY
    fi
    
    if [ -z "$NOVEUM_API_KEY" ]; then
        read -p "Enter Noveum API Key (or press Enter to skip): " NOVEUM_API_KEY
    fi
    
    # Create secret
    kubectl create secret generic agents-api-secrets \
        --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
        --from-literal=ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \
        --from-literal=NOVEUM_API_KEY="${NOVEUM_API_KEY:-}" \
        --namespace="$NAMESPACE"
    
    log_success "Secrets created"
}

# Deploy application
deploy_app() {
    log_info "Deploying application..."
    
    # Update image in deployment
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
    fi
    
    # Apply ConfigMap
    kubectl apply -f k8s/configmap.yaml
    
    # Apply Deployment (with image substitution)
    sed "s|image: agents-library:latest|image: $FULL_IMAGE_NAME|g" k8s/deployment.yaml | kubectl apply -f -
    
    # Apply Service
    kubectl apply -f k8s/service.yaml
    
    # Apply HPA
    kubectl apply -f k8s/hpa.yaml
    
    log_success "Application deployed"
}

# Deploy ingress
deploy_ingress() {
    log_info "Deploying ingress..."
    
    # Check if ingress controller is available
    if kubectl get ingressclass &> /dev/null; then
        kubectl apply -f k8s/ingress.yaml
        log_success "Ingress deployed"
    else
        log_warning "No ingress controller found. Skipping ingress deployment."
        log_info "You can deploy ingress later with: kubectl apply -f k8s/ingress.yaml"
    fi
}

# Wait for deployment
wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    
    kubectl wait --for=condition=available --timeout=300s deployment/agents-api -n "$NAMESPACE"
    
    log_success "Deployment is ready"
}

# Show status
show_status() {
    log_info "Deployment status:"
    
    echo ""
    echo "Pods:"
    kubectl get pods -n "$NAMESPACE" -l app=agents-api
    
    echo ""
    echo "Services:"
    kubectl get services -n "$NAMESPACE"
    
    echo ""
    echo "Ingress:"
    kubectl get ingress -n "$NAMESPACE" 2>/dev/null || echo "No ingress found"
    
    echo ""
    echo "HPA:"
    kubectl get hpa -n "$NAMESPACE"
    
    # Get service URL
    SERVICE_IP=$(kubectl get service agents-api-service -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$SERVICE_IP" ]; then
        echo ""
        log_success "API is available at: http://$SERVICE_IP"
    else
        echo ""
        log_info "To access the API, use port forwarding:"
        log_info "kubectl port-forward service/agents-api-service 8000:80 -n $NAMESPACE"
        log_info "Then access: http://localhost:8000"
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up deployment..."
    
    kubectl delete -f k8s/ --ignore-not-found=true
    kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
    
    log_success "Cleanup completed"
}

# Main function
main() {
    case "${1:-deploy}" in
        "build")
            check_prerequisites
            build_image
            ;;
        "deploy")
            check_prerequisites
            build_image
            create_namespace
            create_secrets
            deploy_app
            deploy_ingress
            wait_for_deployment
            show_status
            ;;
        "update")
            check_prerequisites
            build_image
            deploy_app
            wait_for_deployment
            show_status
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  build    - Build Docker image only"
            echo "  deploy   - Full deployment (build + deploy)"
            echo "  update   - Update existing deployment"
            echo "  status   - Show deployment status"
            echo "  cleanup  - Remove all resources"
            echo "  help     - Show this help"
            echo ""
            echo "Environment variables:"
            echo "  IMAGE_TAG        - Docker image tag (default: latest)"
            echo "  REGISTRY         - Docker registry URL (optional)"
            echo "  OPENAI_API_KEY   - OpenAI API key"
            echo "  ANTHROPIC_API_KEY - Anthropic API key"
            echo "  NOVEUM_API_KEY   - Noveum API key"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

