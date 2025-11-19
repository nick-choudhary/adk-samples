#!/bin/bash

################################################################################
# Outbound Automation System - Automated Deployment Script
################################################################################
#
# This script automates deployment to:
#   - Google Cloud Run (recommended)
#   - Google Kubernetes Engine (GKE)
#   - Local Docker
#
# Usage:
#   ./deployment/deploy.sh [environment] [platform]
#
# Examples:
#   ./deployment/deploy.sh production cloudrun
#   ./deployment/deploy.sh staging gke
#   ./deployment/deploy.sh development local
#
# Requirements:
#   - gcloud CLI installed and authenticated
#   - Docker installed
#   - kubectl configured (for GKE)
#
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="${1:-production}"
PLATFORM="${2:-cloudrun}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Configuration
SERVICE_NAME="outbound-automation-api"
IMAGE_NAME="outbound-system"
REGION="${REGION:-us-central1}"

################################################################################
# Helper Functions
################################################################################

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

print_banner() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║        Outbound Automation System Deployment              ║"
    echo "║                                                            ║"
    echo "║  Environment: $ENVIRONMENT"
    echo "║  Platform:    $PLATFORM"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    log_success "Docker is installed"

    # Check gcloud for cloud deployments
    if [[ "$PLATFORM" == "cloudrun" ]] || [[ "$PLATFORM" == "gke" ]]; then
        if ! command -v gcloud &> /dev/null; then
            log_error "gcloud CLI is not installed. Please install it first."
            exit 1
        fi
        log_success "gcloud CLI is installed"

        # Check authentication
        if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
            log_error "Not authenticated with gcloud. Run: gcloud auth login"
            exit 1
        fi
        log_success "Authenticated with gcloud"
    fi

    # Check kubectl for GKE
    if [[ "$PLATFORM" == "gke" ]]; then
        if ! command -v kubectl &> /dev/null; then
            log_error "kubectl is not installed. Please install it first."
            exit 1
        fi
        log_success "kubectl is installed"
    fi
}

load_environment_config() {
    log_info "Loading environment configuration..."

    # Load environment-specific config
    ENV_FILE="$PROJECT_ROOT/.env.$ENVIRONMENT"

    if [[ -f "$ENV_FILE" ]]; then
        log_info "Loading config from $ENV_FILE"
        set -a
        source "$ENV_FILE"
        set +a
    else
        log_warning "Environment file $ENV_FILE not found. Using .env"
        if [[ -f "$PROJECT_ROOT/.env" ]]; then
            set -a
            source "$PROJECT_ROOT/.env"
            set +a
        else
            log_error "No .env file found. Please create one."
            exit 1
        fi
    fi

    # Validate required variables
    if [[ -z "${GOOGLE_CLOUD_PROJECT:-}" ]]; then
        log_error "GOOGLE_CLOUD_PROJECT is not set in environment file"
        exit 1
    fi

    log_success "Environment configuration loaded"
    log_info "Project: $GOOGLE_CLOUD_PROJECT"
}

build_docker_image() {
    log_info "Building Docker image..."

    cd "$PROJECT_ROOT"

    # Determine image tag
    if [[ "$ENVIRONMENT" == "production" ]]; then
        IMAGE_TAG="latest"
    else
        IMAGE_TAG="$ENVIRONMENT"
    fi

    # Add commit SHA for versioning
    GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
    FULL_IMAGE_TAG="${IMAGE_TAG}-${GIT_SHA}"

    log_info "Image tag: $FULL_IMAGE_TAG"

    # Build image
    docker build \
        --target production \
        --platform linux/amd64 \
        -t "${IMAGE_NAME}:${FULL_IMAGE_TAG}" \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        -f Dockerfile \
        .

    log_success "Docker image built: ${IMAGE_NAME}:${FULL_IMAGE_TAG}"
}

push_to_gcr() {
    log_info "Pushing image to Google Container Registry..."

    # Configure Docker for GCR
    gcloud auth configure-docker --quiet

    # Tag for GCR
    GCR_IMAGE="gcr.io/${GOOGLE_CLOUD_PROJECT}/${IMAGE_NAME}:${FULL_IMAGE_TAG}"
    GCR_IMAGE_LATEST="gcr.io/${GOOGLE_CLOUD_PROJECT}/${IMAGE_NAME}:${IMAGE_TAG}"

    docker tag "${IMAGE_NAME}:${FULL_IMAGE_TAG}" "$GCR_IMAGE"
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "$GCR_IMAGE_LATEST"

    # Push to GCR
    docker push "$GCR_IMAGE"
    docker push "$GCR_IMAGE_LATEST"

    log_success "Image pushed to GCR: $GCR_IMAGE"
}

deploy_to_cloudrun() {
    log_info "Deploying to Cloud Run..."

    GCR_IMAGE="gcr.io/${GOOGLE_CLOUD_PROJECT}/${IMAGE_NAME}:${FULL_IMAGE_TAG}"

    # Deploy to Cloud Run
    gcloud run deploy "$SERVICE_NAME" \
        --image "$GCR_IMAGE" \
        --platform managed \
        --region "$REGION" \
        --allow-unauthenticated \
        --set-env-vars "ENVIRONMENT=$ENVIRONMENT" \
        --set-env-vars "GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT" \
        --set-secrets "DATABASE_URL=DATABASE_URL:latest" \
        --set-secrets "SENDGRID_API_KEY=SENDGRID_API_KEY:latest" \
        --set-secrets "TWILIO_AUTH_TOKEN=TWILIO_AUTH_TOKEN:latest" \
        --cpu 2 \
        --memory 2Gi \
        --min-instances 0 \
        --max-instances 100 \
        --timeout 300 \
        --concurrency 80 \
        --port 8080 \
        --project "$GOOGLE_CLOUD_PROJECT"

    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --platform managed \
        --region "$REGION" \
        --format 'value(status.url)' \
        --project "$GOOGLE_CLOUD_PROJECT")

    log_success "Deployed to Cloud Run: $SERVICE_URL"

    # Test health check
    log_info "Testing health check..."
    sleep 10  # Wait for service to be ready

    if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_warning "Health check failed. Service may still be starting up."
    fi

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                 Deployment Successful!                     ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Service URL:     $SERVICE_URL"
    echo "API Docs:        $SERVICE_URL/docs"
    echo "Health Check:    $SERVICE_URL/health"
    echo ""
}

deploy_to_gke() {
    log_info "Deploying to Google Kubernetes Engine..."

    GCR_IMAGE="gcr.io/${GOOGLE_CLOUD_PROJECT}/${IMAGE_NAME}:${FULL_IMAGE_TAG}"

    # Apply Kubernetes manifests
    K8S_DIR="$PROJECT_ROOT/deployment/kubernetes"

    if [[ ! -d "$K8S_DIR" ]]; then
        log_error "Kubernetes manifests directory not found: $K8S_DIR"
        exit 1
    fi

    # Update image in deployment.yaml
    sed -i.bak "s|IMAGE_PLACEHOLDER|$GCR_IMAGE|g" "$K8S_DIR/deployment.yaml"

    # Apply manifests
    kubectl apply -f "$K8S_DIR/namespace.yaml"
    kubectl apply -f "$K8S_DIR/configmap.yaml"
    kubectl apply -f "$K8S_DIR/secret.yaml"
    kubectl apply -f "$K8S_DIR/deployment.yaml"
    kubectl apply -f "$K8S_DIR/service.yaml"
    kubectl apply -f "$K8S_DIR/ingress.yaml"

    # Restore original deployment.yaml
    mv "$K8S_DIR/deployment.yaml.bak" "$K8S_DIR/deployment.yaml"

    # Wait for rollout
    log_info "Waiting for deployment to roll out..."
    kubectl rollout status deployment/outbound-system -n outbound-automation

    # Get service endpoint
    EXTERNAL_IP=$(kubectl get service outbound-system-service \
        -n outbound-automation \
        -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

    log_success "Deployed to GKE"

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                 Deployment Successful!                     ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "External IP:     $EXTERNAL_IP"
    echo "API Docs:        http://$EXTERNAL_IP/docs"
    echo ""
}

deploy_local() {
    log_info "Deploying locally with Docker Compose..."

    cd "$PROJECT_ROOT"

    # Stop existing containers
    docker-compose down

    # Build and start services
    docker-compose up -d --build

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10

    # Check health
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        log_success "Local deployment successful"
    else
        log_error "Health check failed. Check logs with: docker-compose logs"
        exit 1
    fi

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║              Local Deployment Successful!                  ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Backend API:     http://localhost:8080"
    echo "API Docs:        http://localhost:8080/docs"
    echo "Frontend:        http://localhost:3000"
    echo "Adminer:         http://localhost:8081"
    echo ""
    echo "View logs:       docker-compose logs -f"
    echo "Stop services:   docker-compose down"
    echo ""
}

setup_secrets() {
    log_info "Setting up secrets in Google Secret Manager..."

    # Create secrets if they don't exist
    secrets=(
        "DATABASE_URL"
        "SENDGRID_API_KEY"
        "TWILIO_AUTH_TOKEN"
        "APOLLO_API_KEY"
        "HUNTER_API_KEY"
    )

    for secret in "${secrets[@]}"; do
        # Check if secret exists
        if ! gcloud secrets describe "$secret" --project "$GOOGLE_CLOUD_PROJECT" &> /dev/null; then
            log_info "Creating secret: $secret"

            # Get value from environment
            value="${!secret:-}"

            if [[ -z "$value" ]]; then
                log_warning "Secret $secret not found in environment. Skipping."
                continue
            fi

            # Create secret
            echo -n "$value" | gcloud secrets create "$secret" \
                --data-file=- \
                --replication-policy="automatic" \
                --project "$GOOGLE_CLOUD_PROJECT"

            log_success "Created secret: $secret"
        else
            log_info "Secret $secret already exists"
        fi
    done
}

run_database_migrations() {
    log_info "Running database migrations..."

    # For Cloud Run, run migrations as a job
    if [[ "$PLATFORM" == "cloudrun" ]]; then
        gcloud run jobs execute db-migration \
            --region "$REGION" \
            --project "$GOOGLE_CLOUD_PROJECT" \
            --wait || log_warning "Migration job not configured"
    elif [[ "$PLATFORM" == "local" ]]; then
        docker-compose exec -T backend python scripts/init_database.py
    fi

    log_success "Database migrations completed"
}

################################################################################
# Main Deployment Flow
################################################################################

main() {
    print_banner

    # Validate arguments
    if [[ ! "$PLATFORM" =~ ^(cloudrun|gke|local)$ ]]; then
        log_error "Invalid platform: $PLATFORM. Must be 'cloudrun', 'gke', or 'local'"
        exit 1
    fi

    # Check prerequisites
    check_prerequisites

    # Load environment config
    load_environment_config

    # Build Docker image
    build_docker_image

    # Deploy based on platform
    case "$PLATFORM" in
        cloudrun)
            setup_secrets
            push_to_gcr
            deploy_to_cloudrun
            ;;
        gke)
            setup_secrets
            push_to_gcr
            deploy_to_gke
            ;;
        local)
            deploy_local
            ;;
        *)
            log_error "Unknown platform: $PLATFORM"
            exit 1
            ;;
    esac

    # Run migrations
    # run_database_migrations

    log_success "Deployment complete!"
}

################################################################################
# Script Entry Point
################################################################################

# Show usage if help flag is provided
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    echo "Usage: $0 [environment] [platform]"
    echo ""
    echo "Arguments:"
    echo "  environment    Environment to deploy (development, staging, production)"
    echo "  platform       Deployment platform (cloudrun, gke, local)"
    echo ""
    echo "Examples:"
    echo "  $0 production cloudrun     # Deploy to production Cloud Run"
    echo "  $0 staging gke             # Deploy to staging GKE"
    echo "  $0 development local       # Deploy locally with Docker Compose"
    echo ""
    exit 0
fi

# Run main function
main

exit 0
