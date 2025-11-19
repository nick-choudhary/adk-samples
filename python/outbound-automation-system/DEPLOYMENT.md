# Deployment Guide - Outbound Automation System

Complete guide for deploying the Outbound Automation System to production environments.

## Table of Contents
- [Overview](#overview)
- [Deployment Options](#deployment-options)
- [Prerequisites](#prerequisites)
- [Google Cloud Run Deployment](#google-cloud-run-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Database Setup](#database-setup)
- [Environment Configuration](#environment-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [Scaling & Performance](#scaling--performance)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Overview

The Outbound Automation System can be deployed to multiple platforms. We recommend **Google Cloud Run** for most use cases due to its simplicity, auto-scaling, and cost-effectiveness.

### Deployment Architecture

```
┌─────────────────────────────────────────────────────┐
│              Cloud Load Balancer                    │
│                 (HTTPS/SSL)                         │
└──────────────────┬──────────────────────────────────┘
                   │
    ┌──────────────┴──────────────┐
    │                             │
┌───▼──────────────┐   ┌──────────▼──────┐
│  Cloud Run API   │   │  Cloud Run UI   │
│  (Auto-scaling)  │   │  (Static Host)  │
└───┬──────────────┘   └─────────────────┘
    │
    ├──────────────────┬──────────────────┬────────────────┐
    │                  │                  │                │
┌───▼────────┐  ┌─────▼──────┐  ┌───────▼─────┐  ┌──────▼─────┐
│ Cloud SQL  │  │ Cloud Tasks │  │  BigQuery   │  │ Firestore  │
│(PostgreSQL)│  │ (Job Queue) │  │ (Analytics) │  │ (Sessions) │
└────────────┘  └────────────┘  └─────────────┘  └────────────┘
```

## Deployment Options

### Option 1: Google Cloud Run (Recommended)

**Best for**: Most use cases, especially startups and growing businesses

**Pros**:
- Fully managed (serverless)
- Auto-scaling (0 to 1000+ instances)
- Pay-per-use pricing
- Built-in load balancing
- Zero-downtime deployments
- Easy rollbacks

**Cons**:
- Cold starts (minimal with min instances)
- Request timeout limits (up to 60 minutes)

**Cost**: ~$50-500/month for typical usage

### Option 2: Google Kubernetes Engine (GKE)

**Best for**: Large enterprises, complex multi-service architectures

**Pros**:
- Full control over infrastructure
- Advanced networking options
- Multi-region deployments
- Custom autoscaling policies

**Cons**:
- More complex to manage
- Higher baseline costs
- Requires Kubernetes expertise

**Cost**: ~$300-2000/month minimum

### Option 3: Other Platforms

- **AWS ECS/Fargate**: Similar to Cloud Run
- **Azure Container Apps**: Similar to Cloud Run
- **Self-hosted**: Docker Compose on VMs

## Prerequisites

### 1. Google Cloud Account

Create a Google Cloud account and project:

```bash
# Create new project
gcloud projects create outbound-automation-prod --name="Outbound Automation Production"

# Set as default project
gcloud config set project outbound-automation-prod

# Enable billing (required)
# Go to: https://console.cloud.google.com/billing
```

### 2. Enable Required APIs

```bash
# Enable all required APIs
gcloud services enable \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  cloudtasks.googleapis.com \
  bigquery.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

### 3. Install Required Tools

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Install kubectl (for GKE)
gcloud components install kubectl

# Authenticate
gcloud auth login
gcloud auth configure-docker
```

### 4. Set Up Service Account

```bash
# Create service account
gcloud iam service-accounts create outbound-automation \
  --display-name="Outbound Automation Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding outbound-automation-prod \
  --member="serviceAccount:outbound-automation@outbound-automation-prod.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding outbound-automation-prod \
  --member="serviceAccount:outbound-automation@outbound-automation-prod.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding outbound-automation-prod \
  --member="serviceAccount:outbound-automation@outbound-automation-prod.iam.gserviceaccount.com" \
  --role="roles/cloudtasks.enqueuer"

gcloud projects add-iam-policy-binding outbound-automation-prod \
  --member="serviceAccount:outbound-automation@outbound-automation-prod.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Google Cloud Run Deployment

### Step 1: Set Up Secrets

Store sensitive credentials in Google Secret Manager:

```bash
# Database URL
echo -n "postgresql://user:pass@/db?host=/cloudsql/PROJECT:REGION:INSTANCE" | \
  gcloud secrets create DATABASE_URL --data-file=-

# SendGrid API Key
echo -n "SG.your-sendgrid-api-key" | \
  gcloud secrets create SENDGRID_API_KEY --data-file=-

# Twilio credentials
echo -n "your-twilio-auth-token" | \
  gcloud secrets create TWILIO_AUTH_TOKEN --data-file=-

# Apollo API Key
echo -n "your-apollo-api-key" | \
  gcloud secrets create APOLLO_API_KEY --data-file=-

# Hunter API Key
echo -n "your-hunter-api-key" | \
  gcloud secrets create HUNTER_API_KEY --data-file=-

# JWT Secret
openssl rand -base64 32 | \
  gcloud secrets create JWT_SECRET --data-file=-
```

### Step 2: Create Cloud SQL Database

```bash
# Create Cloud SQL instance
gcloud sql instances create outbound-db \
  --database-version=POSTGRES_16 \
  --tier=db-g1-small \
  --region=us-central1 \
  --root-password=CHOOSE_STRONG_PASSWORD \
  --storage-size=10GB \
  --storage-type=SSD \
  --backup-start-time=03:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=04

# Create database
gcloud sql databases create outbound_db \
  --instance=outbound-db

# Create user
gcloud sql users create outbound_user \
  --instance=outbound-db \
  --password=CHOOSE_STRONG_PASSWORD
```

### Step 3: Initialize Database

```bash
# Connect to Cloud SQL via proxy
cloud_sql_proxy -instances=outbound-automation-prod:us-central1:outbound-db=tcp:5432 &

# Run initialization script
export DATABASE_URL="postgresql://outbound_user:PASSWORD@localhost:5432/outbound_db"
python scripts/init_database.py --sample-data

# Stop proxy
pkill cloud_sql_proxy
```

### Step 4: Build and Deploy

#### Option A: Using Automated Script (Recommended)

```bash
# Create environment file for production
cp .env.example .env.production

# Edit with production values
nano .env.production

# Deploy to Cloud Run
./deployment/deploy.sh production cloudrun
```

#### Option B: Manual Deployment

```bash
# Set variables
PROJECT_ID="outbound-automation-prod"
REGION="us-central1"
SERVICE_NAME="outbound-automation-api"

# Build Docker image
docker build --target production -t gcr.io/$PROJECT_ID/outbound-system:latest .

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/outbound-system:latest

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/outbound-system:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
  --set-secrets DATABASE_URL=DATABASE_URL:latest \
  --set-secrets SENDGRID_API_KEY=SENDGRID_API_KEY:latest \
  --set-secrets TWILIO_AUTH_TOKEN=TWILIO_AUTH_TOKEN:latest \
  --set-secrets APOLLO_API_KEY=APOLLO_API_KEY:latest \
  --set-secrets JWT_SECRET=JWT_SECRET:latest \
  --add-cloudsql-instances $PROJECT_ID:$REGION:outbound-db \
  --cpu 2 \
  --memory 2Gi \
  --min-instances 1 \
  --max-instances 100 \
  --timeout 300 \
  --concurrency 80 \
  --port 8080
```

### Step 5: Configure Custom Domain

```bash
# Map custom domain
gcloud beta run domain-mappings create \
  --service outbound-automation-api \
  --domain api.yourdomain.com \
  --region us-central1

# Get verification record
gcloud beta run domain-mappings describe \
  --domain api.yourdomain.com \
  --region us-central1

# Add DNS records as shown
# Then verify
gcloud beta run domain-mappings verify \
  --domain api.yourdomain.com \
  --region us-central1
```

### Step 6: Set Up Cloud Tasks

```bash
# Create task queues
gcloud tasks queues create lead-extraction-queue \
  --max-concurrent-dispatches=100 \
  --max-dispatches-per-second=50 \
  --location=us-central1

gcloud tasks queues create outreach-queue \
  --max-concurrent-dispatches=200 \
  --max-dispatches-per-second=100 \
  --location=us-central1

gcloud tasks queues create enrichment-queue \
  --max-concurrent-dispatches=50 \
  --max-dispatches-per-second=25 \
  --location=us-central1
```

### Step 7: Verify Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe outbound-automation-api \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')

# Test health check
curl $SERVICE_URL/health

# Expected response:
# {"status":"healthy","service":"outbound-automation-api","version":"1.0.0"}

# Open API docs
open $SERVICE_URL/docs
```

## Kubernetes Deployment

### Step 1: Create GKE Cluster

```bash
# Create GKE cluster
gcloud container clusters create outbound-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-stackdriver-kubernetes

# Get credentials
gcloud container clusters get-credentials outbound-cluster \
  --zone us-central1-a
```

### Step 2: Create Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace outbound-automation

# Create secrets
kubectl create secret generic outbound-secrets \
  --from-literal=DATABASE_URL="postgresql://..." \
  --from-literal=SENDGRID_API_KEY="..." \
  --from-literal=TWILIO_AUTH_TOKEN="..." \
  --from-literal=APOLLO_API_KEY="..." \
  --from-literal=JWT_SECRET="..." \
  --namespace outbound-automation
```

### Step 3: Deploy Application

```bash
# Deploy using automated script
./deployment/deploy.sh production gke

# Or manually apply Kubernetes manifests
kubectl apply -f deployment/kubernetes/
```

### Step 4: Expose Service

```bash
# Create ingress for external access
kubectl apply -f deployment/kubernetes/ingress.yaml

# Get external IP
kubectl get ingress outbound-ingress \
  --namespace outbound-automation
```

## Database Setup

### Production Database Configuration

#### Cloud SQL Settings

```yaml
Instance:
  Tier: db-custom-4-16384  # 4 vCPU, 16 GB RAM
  Storage: 100 GB SSD
  Backups:
    Automated: Daily at 3:00 AM
    Retention: 7 days
    Point-in-time: Enabled
  High Availability: Enabled (regional)
  Maintenance Window: Sunday 4:00-5:00 AM
  Connection Limits: 100
```

#### Connection Pooling

```python
# In production, use connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

#### Read Replicas

For high-traffic applications, set up read replicas:

```bash
# Create read replica
gcloud sql instances create outbound-db-replica \
  --master-instance-name=outbound-db \
  --tier=db-g1-small \
  --region=us-central1
```

## Environment Configuration

### Environment Variables

Create `.env.production` file:

```env
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Google Cloud
GOOGLE_CLOUD_PROJECT=outbound-automation-prod
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true

# Database (via Secret Manager)
# DATABASE_URL is injected from secrets

# API URLs
API_BASE_URL=https://api.yourdomain.com
FRONTEND_URL=https://app.yourdomain.com

# CORS
CORS_ORIGINS=https://app.yourdomain.com,https://yourdomain.com

# Security
JWT_EXPIRATION=3600
SESSION_TIMEOUT=3600

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Features
ENABLE_LINKEDIN_EXTRACTION=true
ENABLE_VOICE_CALLS=true
ENABLE_SMS=true
ENABLE_EMAIL=true

# Monitoring
ENABLE_CLOUD_LOGGING=true
SENTRY_DSN=https://...@sentry.io/...
```

## Monitoring & Logging

### Cloud Monitoring Setup

```bash
# Create uptime check
gcloud monitoring uptime create outbound-api-health \
  --resource-type=uptime-url \
  --host=api.yourdomain.com \
  --path=/health \
  --check-interval=60s

# Create alert policy for errors
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s
```

### Log Aggregation

View logs in Cloud Console:

```bash
# View application logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=outbound-automation-api" \
  --limit 50 \
  --format json

# View error logs only
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit 50
```

### Metrics Dashboard

Key metrics to monitor:

- **Request Rate**: Requests per second
- **Error Rate**: Errors per minute
- **Response Time**: P50, P95, P99 latencies
- **CPU Usage**: Average and peak
- **Memory Usage**: Average and peak
- **Database Connections**: Active connections
- **Job Queue Depth**: Pending jobs in Cloud Tasks

### Alerting

Set up alerts for:

1. **High Error Rate**: Error rate > 5% for 5 minutes
2. **Slow Response Time**: P95 latency > 1s for 5 minutes
3. **High Memory Usage**: Memory > 80% for 10 minutes
4. **Failed Jobs**: Job failure rate > 10% for 15 minutes
5. **Database Connection Pool**: Connections > 80% for 5 minutes

## Scaling & Performance

### Auto-Scaling Configuration

#### Cloud Run

```bash
# Configure auto-scaling
gcloud run services update outbound-automation-api \
  --min-instances 2 \
  --max-instances 100 \
  --cpu 2 \
  --memory 2Gi \
  --concurrency 80 \
  --region us-central1
```

**Scaling triggers**:
- CPU utilization > 60%
- Memory utilization > 70%
- Request queue depth > 100

#### GKE Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: outbound-system-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: outbound-system
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Performance Optimization

1. **Database Connection Pooling**: Reuse connections
2. **Redis Caching**: Cache frequent queries
3. **CDN**: Use Cloud CDN for static assets
4. **Compression**: Enable gzip for API responses
5. **Async Processing**: Use Cloud Tasks for background jobs

## Security Considerations

### 1. API Security

```bash
# Enable Cloud Armor (DDoS protection)
gcloud compute security-policies create outbound-api-policy \
  --description "Security policy for Outbound API"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy outbound-api-policy \
  --expression "true" \
  --action "rate-based-ban" \
  --rate-limit-threshold-count 100 \
  --rate-limit-threshold-interval-sec 60 \
  --ban-duration-sec 600
```

### 2. Secret Management

- Use Google Secret Manager (never hardcode secrets)
- Rotate secrets regularly (every 90 days)
- Use IAM for access control
- Enable secret versioning

### 3. Network Security

```bash
# Configure VPC
gcloud compute networks create outbound-vpc \
  --subnet-mode=custom

# Create private subnet
gcloud compute networks subnets create outbound-subnet \
  --network=outbound-vpc \
  --region=us-central1 \
  --range=10.0.0.0/24

# Enable Private IP for Cloud SQL
gcloud sql instances patch outbound-db \
  --network=projects/PROJECT_ID/global/networks/outbound-vpc \
  --no-assign-ip
```

### 4. Compliance

- **GDPR**: Data retention policies, right to deletion
- **CCPA**: Privacy notices, opt-out mechanisms
- **CAN-SPAM**: Unsubscribe links, physical address
- **TCPA**: Consent tracking, DNC list

## Troubleshooting

### Issue: Cloud Run Service Won't Start

**Check logs**:
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

**Common causes**:
- Port mismatch (ensure app listens on port 8080)
- Missing environment variables
- Database connection issues
- Out of memory

### Issue: Database Connection Errors

**Check Cloud SQL status**:
```bash
gcloud sql instances describe outbound-db
```

**Verify connection**:
```bash
gcloud sql connect outbound-db --user=outbound_user
```

**Check connection limits**:
```sql
SELECT count(*) FROM pg_stat_activity;
```

### Issue: High Latency

**Check metrics**:
```bash
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_latencies"' \
  --interval-start-time=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval-end-time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
```

**Optimize**:
- Add database indexes
- Enable caching
- Increase instance size
- Add read replicas

### Issue: Jobs Not Processing

**Check Cloud Tasks queue**:
```bash
gcloud tasks queues describe lead-extraction-queue \
  --location=us-central1
```

**Purge stuck tasks**:
```bash
gcloud tasks queues purge lead-extraction-queue \
  --location=us-central1
```

## Cost Optimization

### Expected Costs (Monthly)

**Small deployment** (< 10K API requests/day):
- Cloud Run: $30
- Cloud SQL: $50
- Cloud Tasks: $10
- BigQuery: $20
- Total: ~$110/month

**Medium deployment** (100K API requests/day):
- Cloud Run: $150
- Cloud SQL: $150
- Cloud Tasks: $50
- BigQuery: $100
- Total: ~$450/month

**Large deployment** (1M API requests/day):
- Cloud Run: $500
- Cloud SQL: $500
- Cloud Tasks: $200
- BigQuery: $500
- Total: ~$1,700/month

### Cost Reduction Tips

1. **Use Cloud Run min-instances wisely**: Set to 0 for dev/staging
2. **Right-size Cloud SQL**: Start small, scale up as needed
3. **Enable BigQuery partition pruning**: Reduce query costs
4. **Use Cloud Storage lifecycle policies**: Auto-delete old files
5. **Set up budget alerts**: Get notified before overspending

```bash
# Create budget alert
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Monthly Budget" \
  --budget-amount=500 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

## Rollback Procedure

If deployment fails or has issues:

```bash
# Get previous revision
gcloud run revisions list \
  --service=outbound-automation-api \
  --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic outbound-automation-api \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=us-central1
```

## Backup & Disaster Recovery

### Database Backups

```bash
# Create on-demand backup
gcloud sql backups create \
  --instance=outbound-db \
  --description="Pre-deployment backup"

# Restore from backup
gcloud sql backups restore BACKUP_ID \
  --backup-instance=outbound-db \
  --backup-instance=outbound-db
```

### Export Data

```bash
# Export database to Cloud Storage
gcloud sql export sql outbound-db \
  gs://YOUR_BUCKET/backups/outbound-db-$(date +%Y%m%d).sql \
  --database=outbound_db
```

---

**Deployment Complete!**

Your Outbound Automation System is now live. Monitor the dashboard and check logs regularly.

**Next Steps**:
- Set up monitoring alerts
- Configure custom domain
- Enable SSL/HTTPS
- Test all API endpoints
- Load test with expected traffic

**Support**:
- GitHub Issues: https://github.com/google/adk-samples/issues
- Documentation: [ARCHITECTURE.md](./ARCHITECTURE.md), [API.md](./docs/API.md)
