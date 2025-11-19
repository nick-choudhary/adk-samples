# Local Setup Guide - Outbound Automation System

Complete step-by-step guide for setting up the Outbound Automation System on your local machine.

## Table of Contents
- [Prerequisites](#prerequisites)
- [System Requirements](#system-requirements)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

## Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software

| Software | Minimum Version | Download Link |
|----------|----------------|---------------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| Docker | 24.0+ | [docker.com](https://www.docker.com/get-started) |
| Docker Compose | 2.20+ | [docs.docker.com](https://docs.docker.com/compose/install/) |
| Git | 2.40+ | [git-scm.com](https://git-scm.com/downloads) |

### Optional Tools

- **uv** (Python package manager): Faster alternative to pip
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- **PostgreSQL Client** (for database management):
  ```bash
  # macOS
  brew install postgresql@16

  # Ubuntu/Debian
  sudo apt-get install postgresql-client-16

  # Windows
  # Download from https://www.postgresql.org/download/windows/
  ```

## System Requirements

### Minimum Hardware Requirements

- **CPU**: 4 cores (Intel Core i5 or equivalent)
- **RAM**: 8 GB
- **Disk**: 20 GB free space
- **Network**: Stable internet connection

### Recommended Hardware Requirements

- **CPU**: 8+ cores (Intel Core i7/i9 or Apple M1/M2)
- **RAM**: 16 GB
- **Disk**: 50 GB SSD
- **Network**: High-speed internet (for API calls)

### Operating System Support

- macOS 12+ (Monterey or later)
- Ubuntu 20.04 LTS or later
- Windows 10/11 with WSL2
- Other Linux distributions with Docker support

## Installation Steps

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/google/adk-samples.git

# Navigate to the project directory
cd adk-samples/python/outbound-automation-system

# Verify you're in the correct directory
pwd
# Should output: .../adk-samples/python/outbound-automation-system
```

### Step 2: Install Backend Dependencies

#### Option A: Using uv (Recommended - Faster)

```bash
# Install dependencies
uv sync

# This will:
# - Create a virtual environment
# - Install all dependencies from pyproject.toml
# - Set up the project for development
```

#### Option B: Using pip

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

### Step 3: Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install

# This will install:
# - React and dependencies
# - TypeScript
# - Tailwind CSS
# - Development tools

# Return to root directory
cd ..
```

### Step 4: Verify Installation

```bash
# Check Python version
python --version
# Should output: Python 3.11.x or higher

# Check Node version
node --version
# Should output: v18.x.x or higher

# Check Docker
docker --version
# Should output: Docker version 24.x.x or higher

# Check Docker Compose
docker-compose --version
# Should output: Docker Compose version v2.x.x or higher
```

## Configuration

### Step 1: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Open .env in your favorite editor
nano .env  # or vim, code, etc.
```

### Step 2: Configure Google Cloud

#### Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your Project ID

#### Enable Required APIs

```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Enable required APIs
gcloud services enable \
  aiplatform.googleapis.com \
  cloudtasks.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com
```

#### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create outbound-system \
  --display-name="Outbound Automation System"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:outbound-system@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:outbound-system@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudtasks.enqueuer"

# Download service account key
gcloud iam service-accounts keys create \
  ~/.config/gcloud/outbound-service-account.json \
  --iam-account=outbound-system@$PROJECT_ID.iam.gserviceaccount.com
```

#### Update .env File

```bash
# Edit .env file
nano .env
```

Update the following values:
```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Step 3: Configure External Services

You'll need API keys for the following services. Don't worry - the system will work without them initially, but you'll need them for full functionality.

#### SendGrid (Email Sending)

1. Sign up at [SendGrid](https://sendgrid.com/)
2. Create an API key: Settings → API Keys → Create API Key
3. Add to `.env`:
   ```env
   SENDGRID_API_KEY=SG.your-api-key-here
   FROM_EMAIL=noreply@yourdomain.com
   FROM_NAME=Your Company
   ```

#### Twilio (SMS & Voice)

1. Sign up at [Twilio](https://www.twilio.com/)
2. Get your Account SID and Auth Token from dashboard
3. Purchase a phone number
4. Add to `.env`:
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your-auth-token
   TWILIO_PHONE_NUMBER=+1234567890
   ```

#### Apollo.io (Lead Database)

1. Sign up at [Apollo.io](https://www.apollo.io/)
2. Go to Settings → Integrations → API
3. Add to `.env`:
   ```env
   APOLLO_API_KEY=your-apollo-api-key
   ```

#### Hunter.io (Email Finding)

1. Sign up at [Hunter.io](https://hunter.io/)
2. Go to Dashboard → API → Keys
3. Add to `.env`:
   ```env
   HUNTER_API_KEY=your-hunter-api-key
   ```

#### Optional Services

These are optional but enhance functionality:

- **ZoomInfo**: Enterprise lead database
- **Clearbit**: Company enrichment
- **SerpAPI**: Google Search scraping
- **Twitter API**: Social signal extraction

### Step 4: Configure Database

The database will be automatically configured when using Docker Compose. For custom setups:

```env
# PostgreSQL Configuration
DATABASE_URL=postgresql://outbound_user:outbound_pass@localhost:5432/outbound_db

# Redis Configuration
REDIS_URL=redis://localhost:6379
```

## Database Setup

### Option 1: Using Docker Compose (Recommended)

The database will be automatically created and initialized when you run Docker Compose (see next section).

### Option 2: Manual Setup

If you prefer to run PostgreSQL and Redis manually:

#### Install PostgreSQL

```bash
# macOS
brew install postgresql@16
brew services start postgresql@16

# Ubuntu/Debian
sudo apt-get install postgresql-16
sudo systemctl start postgresql

# Windows
# Download installer from postgresql.org
```

#### Create Database

```bash
# Create database and user
psql postgres -c "CREATE DATABASE outbound_db;"
psql postgres -c "CREATE USER outbound_user WITH PASSWORD 'outbound_pass';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE outbound_db TO outbound_user;"
```

#### Initialize Database Schema

```bash
# Run initialization script
python scripts/init_database.py --sample-data

# This will:
# - Create all tables
# - Set up indexes
# - Create views
# - Insert sample templates
# - Insert sample data (if --sample-data flag is used)
```

#### Install Redis

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows
# Download from https://redis.io/download
```

## Running the Application

### Option 1: Using Docker Compose (Recommended)

This is the easiest way to get started. It will start all services automatically.

```bash
# Start all services
docker-compose up

# Or run in detached mode (background)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

This will start:
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Backend API**: http://localhost:8080
- **Frontend**: http://localhost:3000
- **Adminer** (Database UI): http://localhost:8081

### Option 2: Running Services Separately

For development, you may want to run services separately.

#### Terminal 1: Backend API

```bash
# Activate virtual environment (if using venv)
source venv/bin/activate

# Run backend with auto-reload
uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload

# Alternative: Use the built-in run command
python -m backend.main
```

#### Terminal 2: Frontend

```bash
# Navigate to frontend directory
cd frontend

# Start development server
npm start

# The frontend will open at http://localhost:3000
```

#### Terminal 3: Worker (Optional)

```bash
# Run background worker for job processing
python -m backend.worker
```

### Option 3: Production Mode

```bash
# Build production Docker image
docker build --target production -t outbound-system:latest .

# Run production container
docker run -p 8080:8080 --env-file .env outbound-system:latest
```

## Verification

### Step 1: Check Services Are Running

```bash
# Check Docker containers
docker-compose ps

# Should show all services as "Up"
```

### Step 2: Test Backend API

```bash
# Health check
curl http://localhost:8080/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "outbound-automation-api",
#   "version": "1.0.0",
#   "timestamp": "2025-01-15T10:30:00Z"
# }

# View API documentation
# Open in browser: http://localhost:8080/docs
```

### Step 3: Test Frontend

```bash
# Open frontend in browser
open http://localhost:3000

# Or manually navigate to: http://localhost:3000
```

You should see:
- Landing page with login/signup
- Dashboard (after login)
- Campaign management interface

### Step 4: Test Database Connection

```bash
# Test database
python scripts/init_database.py --validate-only

# Expected output:
# INFO - Validating database connection...
# INFO - Connected to PostgreSQL: PostgreSQL 16.x
# INFO - All 9 required tables exist
```

### Step 5: Create a Test Campaign

```bash
# Using curl (replace YOUR_TOKEN with actual JWT token)
curl -X POST http://localhost:8080/api/campaigns \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Campaign",
    "target_industries": ["Technology"],
    "target_titles": ["CEO", "CTO"],
    "company_size": "50-200",
    "geography": "United States",
    "sources": ["apollo"],
    "min_score": 70
  }'
```

Or use the web interface at http://localhost:3000

## Troubleshooting

### Common Issues

#### Issue: Docker containers won't start

**Solution**:
```bash
# Check Docker is running
docker ps

# Check Docker Compose version
docker-compose --version

# Remove old containers and volumes
docker-compose down -v

# Rebuild and start
docker-compose up --build
```

#### Issue: Database connection error

**Solution**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Test connection manually
psql postgresql://outbound_user:outbound_pass@localhost:5432/outbound_db
```

#### Issue: Port already in use

**Solution**:
```bash
# Find process using port 8080
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux

# Or change port in docker-compose.yml
ports:
  - "8081:8080"  # Use port 8081 instead
```

#### Issue: Python module not found

**Solution**:
```bash
# Reinstall dependencies
uv sync
# or
pip install -e .

# Verify installation
python -c "import google.adk; print('ADK installed')"
python -c "import fastapi; print('FastAPI installed')"
```

#### Issue: Frontend won't compile

**Solution**:
```bash
# Delete node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Clear cache
npm cache clean --force
npm install
```

#### Issue: Google Cloud authentication error

**Solution**:
```bash
# Verify service account exists
ls -la ~/.config/gcloud/outbound-service-account.json

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Add to .env file
echo "GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json" >> .env

# Test authentication
gcloud auth list
gcloud projects list
```

#### Issue: External API errors (SendGrid, Twilio, etc.)

**Solution**:
```bash
# Verify API keys in .env
cat .env | grep SENDGRID_API_KEY
cat .env | grep TWILIO_ACCOUNT_SID

# Test SendGrid API
curl -X POST https://api.sendgrid.com/v3/mail/send \
  -H "Authorization: Bearer $SENDGRID_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"personalizations":[{"to":[{"email":"test@example.com"}]}],"from":{"email":"noreply@yourdomain.com"},"subject":"Test","content":[{"type":"text/plain","value":"Test"}]}'

# For development, you can disable external services:
# Set in .env:
ENABLE_EMAIL=false
ENABLE_SMS=false
ENABLE_VOICE_CALLS=false
```

### Getting Help

If you encounter issues not covered here:

1. **Check logs**:
   ```bash
   docker-compose logs -f
   ```

2. **Check GitHub Issues**:
   - [ADK Samples Issues](https://github.com/google/adk-samples/issues)

3. **Ask in Discussions**:
   - [GitHub Discussions](https://github.com/google/adk-samples/discussions)

4. **Read the docs**:
   - [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
   - [API.md](./API.md) - API documentation
   - [DEPLOYMENT.md](../DEPLOYMENT.md) - Deployment guide

## Next Steps

Now that your local environment is set up:

1. **Explore the API**:
   - Open http://localhost:8080/docs
   - Try the interactive API documentation
   - Create test campaigns

2. **Read the documentation**:
   - [API Documentation](./API.md) - Complete API reference
   - [Examples](./EXAMPLES.md) - Real-world usage examples
   - [Architecture](../ARCHITECTURE.md) - System design

3. **Build your first campaign**:
   - Log in to http://localhost:3000
   - Create a new campaign
   - Configure lead extraction sources
   - Set up outreach sequences

4. **Customize templates**:
   - Edit email templates in the web UI
   - Create SMS templates
   - Test with sample leads

5. **Deploy to production**:
   - Read [DEPLOYMENT.md](../DEPLOYMENT.md)
   - Deploy to Google Cloud Run
   - Set up monitoring and alerts

## Development Tips

### Hot Reload

Both backend and frontend support hot reload in development mode:

- **Backend**: Changes to Python files automatically restart the server
- **Frontend**: Changes to React files automatically refresh the browser

### Database Management

Access the database UI:
- **Adminer**: http://localhost:8081
  - System: PostgreSQL
  - Server: postgres
  - Username: outbound_user
  - Password: outbound_pass
  - Database: outbound_db

### API Testing

Use the interactive API docs:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

Or use tools like:
- **Postman**: Import OpenAPI spec from http://localhost:8080/openapi.json
- **curl**: Command-line API testing
- **httpie**: User-friendly HTTP client

### Code Quality

Run linters and formatters:

```bash
# Backend
ruff check .
ruff format .
mypy backend/

# Frontend
cd frontend
npm run lint
npm run format
```

### Testing

Run tests:

```bash
# Backend tests
pytest tests/

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

---

**Need Help?** Open an issue on [GitHub](https://github.com/google/adk-samples/issues) or join our [Discussions](https://github.com/google/adk-samples/discussions).
