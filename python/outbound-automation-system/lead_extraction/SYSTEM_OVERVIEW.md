# Lead Extraction Agent System - Technical Overview

## System Architecture

The Lead Extraction System is a production-ready, multi-agent orchestration framework built with Google ADK that extracts, enriches, and scores B2B leads from multiple data sources.

### File Structure

```
lead_extraction/
├── __init__.py              # Package initialization and exports
├── agent.py                 # Main orchestrator and sub-agents (901 lines)
├── tools.py                 # All extraction tools and clients (1,220 lines)
├── example.py               # Comprehensive usage examples (394 lines)
├── README.md                # User documentation
├── SYSTEM_OVERVIEW.md       # This technical overview
└── sub_agents/
    └── __init__.py          # Sub-agent exports
```

**Total Code**: 2,707 lines of production-ready Python

---

## Core Components

### 1. tools.py - Data Sources & Utilities

#### Data Models
- **Lead**: Comprehensive lead data model with validation
- **LeadSource**: Enumeration of data sources
- **SearchCriteria**: Search parameters with filtering
- **Pydantic Validation**: Type-safe data handling

#### API Clients (with rate limiting & retry logic)
- **ApolloClient**: Apollo.io B2B database (275M+ contacts)
- **ZoomInfoClient**: ZoomInfo enterprise data
- **LinkedInClient**: LinkedIn Sales Navigator
- **GoogleSearchClient**: SerpAPI for Google Search
- **WebScraper**: Selenium-based web scraping
- **TwitterClient**: Twitter/X API v2
- **HunterIOClient**: Email finding and verification
- **ClearbitClient**: Company enrichment

#### Utilities
- **RateLimiter**: Token bucket algorithm for API rate limiting
- **LeadDeduplicator**: Multi-field deduplication
- **LeadScorer**: 0-100 quality scoring algorithm
- **FileImporter**: CSV/Excel import with mapping

#### Features
- Automatic retry with exponential backoff
- Rate limit detection and compliance
- Comprehensive error handling
- Phone number validation (international)
- Email validation and formatting
- Unique ID generation for deduplication

---

### 2. agent.py - Agent Orchestration

#### Configuration
- **LeadExtractionConfig**: Centralized configuration
  - API key management
  - Google Cloud settings
  - Processing options
  - Environment variable loading

#### Sub-Agents

##### DatabaseSearchAgent
- **Purpose**: Search B2B databases (Apollo.io, ZoomInfo)
- **Tools**: apollo_search_tool, zoominfo_search_tool
- **Specialization**: Converting criteria to database queries

##### LinkedInAgent
- **Purpose**: LinkedIn Sales Navigator extraction
- **Tools**: linkedin_search_tool
- **Specialization**: Professional network searches

##### WebScrapingAgent
- **Purpose**: Google Search and web scraping
- **Tools**: google_search_tool, web_scraping_tool
- **Specialization**: Finding and scraping business websites

##### SocialMediaAgent
- **Purpose**: Twitter/X lead extraction
- **Tools**: Twitter search tools
- **Specialization**: Social signal analysis

##### EnrichmentAgent
- **Purpose**: Data enrichment
- **Tools**: email_finder_tool, company_enrichment_tool
- **Specialization**: Finding missing information

##### ScoringAgent
- **Purpose**: Quality control
- **Tools**: deduplication_tool, lead_scoring_tool
- **Specialization**: Deduplication and scoring

#### Main Orchestrator

**LeadExtractionOrchestrator**
- Coordinates all sub-agents
- Manages extraction workflow:
  1. Phase 1: Parallel extraction from multiple sources
  2. Phase 2: Enrichment for incomplete leads
  3. Phase 3: Deduplication
  4. Phase 4: Scoring and filtering
  5. Phase 5: Result aggregation
- Handles errors and statistics
- Supports CSV/Excel import

---

## Extraction Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                  ExtractionRequest                           │
│  (campaign_id, search_criteria, sources, filters)           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              LeadExtractionOrchestrator                      │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┴───────────────┐
          │                              │
          ▼                              ▼
┌──────────────────────┐      ┌──────────────────────┐
│  Phase 1: Extract    │      │   Parallel Tasks:    │
│  from Sources        │      │   - Apollo.io        │
│                      │      │   - ZoomInfo         │
│                      │      │   - LinkedIn         │
│                      │      │   - Google Search    │
│                      │      │   - Twitter/X        │
└──────────┬───────────┘      └──────────┬───────────┘
           │                             │
           └──────────┬──────────────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │  Phase 2: Enrich    │
           │  - Find emails      │
           │  - Enrich companies │
           └──────────┬──────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │ Phase 3: Deduplicate│
           │  - Email matching   │
           │  - Name+Company     │
           └──────────┬──────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │  Phase 4: Score     │
           │  - Calculate score  │
           │  - Filter by min    │
           └──────────┬──────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │ Phase 5: Aggregate  │
           │  - Statistics       │
           │  - Sort by score    │
           │  - Limit results    │
           └──────────┬──────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │  ExtractionResult   │
           │  - Leads list       │
           │  - Statistics       │
           │  - Errors           │
           └─────────────────────┘
```

---

## Lead Scoring Algorithm

Leads are scored 0-100 based on:

### 1. Data Completeness (40 points)
Fields checked:
- first_name
- last_name
- email
- phone
- title
- company_name
- company_domain
- linkedin_url

Score = (filled_fields / 8) * 40

### 2. Job Title Match (20 points)
- Full 20 points if title matches any in search criteria
- Case-insensitive matching

### 3. Company Fit (20 points)
- Industry match: 10 points
- Company size match: 10 points

### 4. Seniority Level (10 points)
- Full 10 points if seniority matches criteria
- Recognizes: C-Level, VP, Director, Manager, etc.

### 5. Email Validity (10 points)
- Full 10 points for valid email format
- Checks for @ symbol and domain

**Example Scores:**
- Complete lead with perfect match: 100
- Lead with email only: 15-25
- Lead with full data but no match: 50-60
- Typical high-quality lead: 70-85

---

## Rate Limiting

### Token Bucket Algorithm

Each API client has a rate limiter:

```python
class RateLimiter:
    def __init__(self, max_requests: int, time_window: int = 60):
        # Track requests in sliding window
        # Block when limit reached
        # Auto-resume when window slides
```

### Default Limits

| Service | Requests | Window | Implementation |
|---------|----------|--------|----------------|
| Apollo.io | 200 | 60s | Token bucket |
| ZoomInfo | 100 | 60s | Token bucket |
| LinkedIn | 30 | 60s | Token bucket |
| SerpAPI | 100 | 60s | Token bucket |
| Hunter.io | 100 | 60s | Token bucket |
| Clearbit | 600 | 60s | Token bucket |
| Twitter | 450 | 900s | Token bucket |

### Retry Logic

```python
for attempt in range(max_retries):
    try:
        response = make_request()
        return response
    except HTTPError as e:
        if e.status_code == 429:  # Rate limit
            wait = int(e.headers.get("Retry-After", 60))
            sleep(wait)
            continue
        elif e.status_code >= 500:  # Server error
            wait = 2 ** attempt  # Exponential backoff
            sleep(wait)
            continue
        else:
            raise
```

---

## Error Handling

### Levels of Error Handling

1. **Client Level**: Retry logic in APIClient base class
2. **Agent Level**: Try/catch in each sub-agent
3. **Orchestrator Level**: Exception aggregation
4. **Result Level**: Errors list in ExtractionResult

### Error Recovery Strategies

- **Rate Limits**: Wait and retry with Retry-After header
- **Server Errors**: Exponential backoff (1s, 2s, 4s, 8s)
- **Network Errors**: Retry up to 3 times
- **Invalid Data**: Log warning and skip
- **Missing APIs**: Graceful degradation (skip source)

### Logging

```python
# Comprehensive logging at all levels
logger.info("Starting extraction...")
logger.warning("API key not configured")
logger.error("Request failed", exc_info=True)
```

---

## Data Validation

### Pydantic Models

All data validated with Pydantic:

```python
class Lead(BaseModel):
    email: Optional[EmailStr]  # Validates email format
    phone: Optional[str]       # Custom validator
    linkedin_url: Optional[HttpUrl]  # Validates URL
    confidence_score: float = Field(ge=0.0, le=100.0)  # Range check

    @validator('phone')
    def validate_phone(cls, v):
        # International phone validation
        return phonenumbers.format_number(parsed, E164)
```

### Benefits
- Type safety
- Automatic validation
- Clear error messages
- Serialization/deserialization
- IDE autocomplete

---

## Performance Optimization

### Parallel Processing

```python
# Extract from multiple sources in parallel
extraction_tasks = [
    self._extract_from_apollo(criteria),
    self._extract_from_zoominfo(criteria),
    self._extract_from_linkedin(criteria),
]

results = await asyncio.gather(*extraction_tasks)
```

### Concurrency Control

```python
# Limit concurrent tasks
semaphore = asyncio.Semaphore(max_concurrent_tasks)

async def task_with_limit():
    async with semaphore:
        return await expensive_operation()
```

### Expected Throughput

| Operation | Throughput | Notes |
|-----------|------------|-------|
| Apollo extraction | 200 leads/min | Rate limited |
| ZoomInfo extraction | 100 leads/min | Rate limited |
| LinkedIn extraction | 30 leads/min | Rate limited |
| Web scraping | 10 sites/min | CPU intensive |
| Email enrichment | 100 leads/min | Rate limited |
| Deduplication | 10,000 leads/s | In-memory |
| Scoring | 5,000 leads/s | Pure Python |

---

## Production Readiness Checklist

### ✅ Error Handling
- [x] Comprehensive try/catch blocks
- [x] Retry logic with exponential backoff
- [x] Rate limit detection and handling
- [x] Graceful degradation
- [x] Error aggregation in results

### ✅ Validation
- [x] Pydantic models for all data
- [x] Email validation
- [x] Phone number validation
- [x] URL validation
- [x] Range checks on scores

### ✅ Rate Limiting
- [x] Token bucket algorithm
- [x] Per-client rate limiters
- [x] Respect Retry-After headers
- [x] Configurable limits

### ✅ Logging
- [x] Structured logging
- [x] Log levels (INFO, WARNING, ERROR)
- [x] Exception stack traces
- [x] Performance metrics

### ✅ Testing
- [x] Example usage file
- [x] Multiple test scenarios
- [x] Error case handling
- [x] Documentation

### ✅ Documentation
- [x] README with quick start
- [x] API reference
- [x] Code comments
- [x] Type hints
- [x] Examples

### ✅ Security
- [x] Environment variable configuration
- [x] No hardcoded credentials
- [x] Input validation
- [x] Safe error messages

### ✅ Scalability
- [x] Async/await support
- [x] Parallel processing
- [x] Configurable concurrency
- [x] Efficient deduplication

---

## Configuration Best Practices

### Environment Variables

```bash
# Required
export GCP_PROJECT_ID="your-project"
export VERTEX_AI_MODEL="gemini-2.0-flash-exp"

# Data Sources (configure at least one)
export APOLLO_API_KEY="your-key"
export ZOOMINFO_API_KEY="your-key"
export LINKEDIN_SESSION_COOKIE="your-cookie"

# Enrichment (recommended)
export HUNTER_API_KEY="your-key"
export CLEARBIT_API_KEY="your-key"
```

### Code Configuration

```python
config = LeadExtractionConfig(
    # Processing
    enable_enrichment=True,      # Find missing emails
    enable_deduplication=True,   # Remove duplicates
    enable_scoring=True,         # Calculate scores
    min_lead_score=70.0,        # Quality threshold
    max_concurrent_tasks=10,     # Parallel tasks

    # Google Cloud
    gcp_project_id="project-id",
    vertex_ai_model="gemini-2.0-flash-exp",
)
```

---

## Integration Examples

### With FastAPI Backend

```python
from fastapi import FastAPI, BackgroundTasks
from lead_extraction import create_lead_extraction_agent

app = FastAPI()
agent = create_lead_extraction_agent()

@app.post("/api/leads/extract")
async def extract_leads(request: ExtractionRequest):
    result = await agent.extract_leads(request)
    return result
```

### With Cloud Tasks

```python
from google.cloud import tasks_v2

def enqueue_extraction(campaign_id: str, criteria: dict):
    client = tasks_v2.CloudTasksClient()
    task = {
        "http_request": {
            "http_method": "POST",
            "url": "https://your-service.run.app/extract",
            "body": json.dumps({
                "campaign_id": campaign_id,
                "criteria": criteria
            }).encode()
        }
    }
    client.create_task(parent=queue_path, task=task)
```

### With Database Storage

```python
from sqlalchemy import create_engine
import pandas as pd

# Extract leads
result = await agent.extract_leads(request)

# Convert to DataFrame
df = pd.DataFrame([lead.dict() for lead in result.leads])

# Store in database
engine = create_engine("postgresql://...")
df.to_sql("leads", engine, if_exists="append")
```

---

## Monitoring & Observability

### Key Metrics to Track

1. **Extraction Metrics**
   - Total leads extracted
   - Unique leads after deduplication
   - Average lead score
   - Extraction time

2. **Source Metrics**
   - Leads per source
   - Source success rate
   - Source response time

3. **Enrichment Metrics**
   - Enrichment success rate
   - Emails found
   - Companies enriched

4. **Error Metrics**
   - Error count by type
   - Retry count
   - Failed sources

### Logging Example

```python
logger.info(f"Extraction started: campaign={campaign_id}")
logger.info(f"Sources: {', '.join(sources)}")
logger.info(f"Criteria: {criteria}")
logger.info(f"Results: {total_leads} leads in {duration}s")
logger.info(f"Stats: {json.dumps(statistics)}")
```

---

## Future Enhancements

### Potential Improvements

1. **Additional Sources**
   - Crunchbase integration
   - AngelList/Wellfound
   - Product Hunt
   - GitHub
   - Clutch/G2

2. **Enhanced Enrichment**
   - Phone number finding
   - Social media profiles
   - Company technology stack
   - Funding information
   - Employee count trends

3. **Advanced Scoring**
   - ML-based scoring
   - Custom scoring models
   - Historical conversion data
   - Industry-specific scoring

4. **Performance**
   - Caching layer (Redis)
   - Database connection pooling
   - Batch API requests
   - CDN for static data

5. **Features**
   - Real-time webhooks
   - Scheduled extractions
   - Incremental updates
   - Lead tracking

---

## License

Apache License 2.0

## Support

- **Documentation**: README.md and example.py
- **Issues**: [GitHub Issues](https://github.com/google/adk-samples/issues)
- **Discussions**: [GitHub Discussions](https://github.com/google/adk-samples/discussions)

---

**Built with Google Agent Development Kit (ADK)**
