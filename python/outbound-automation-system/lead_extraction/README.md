# Lead Extraction System

A comprehensive, production-ready multi-agent system for extracting, enriching, and scoring B2B leads from multiple sources using Google ADK (Agent Development Kit).

## Features

### Data Sources

- **Apollo.io** - B2B contact database with 275M+ contacts
- **ZoomInfo** - Enterprise contact and company intelligence
- **LinkedIn Sales Navigator** - Professional network search
- **Google Search** - Web search with automated scraping
- **Twitter/X** - Social media lead extraction
- **CSV/Excel Import** - Import existing lead lists

### Data Enrichment

- **Email Finding** - Hunter.io integration for email discovery
- **Email Verification** - Validate email deliverability
- **Company Enrichment** - Clearbit for company data
- **Phone Validation** - International phone number validation

### Processing

- **Deduplication** - Remove duplicate leads across sources
- **Lead Scoring** - 0-100 quality score based on completeness and fit
- **Rate Limiting** - Respect API limits with token bucket algorithm
- **Parallel Processing** - Concurrent extraction from multiple sources
- **Error Handling** - Comprehensive retry logic and error recovery

## Architecture

```
LeadExtractionOrchestrator (Main Agent)
├── DatabaseSearchAgent (Apollo.io, ZoomInfo)
├── LinkedInAgent (LinkedIn Sales Navigator)
├── WebScrapingAgent (Google Search, Web Scraping)
├── SocialMediaAgent (Twitter/X)
├── EnrichmentAgent (Hunter.io, Clearbit)
└── ScoringAgent (Deduplication, Scoring)
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or using uv
uv sync
```

## Configuration

### Environment Variables

Create a `.env` file with your API keys:

```bash
# Required: Google Cloud
GCP_PROJECT_ID=your-gcp-project
GCP_REGION=us-central1
VERTEX_AI_MODEL=gemini-2.0-flash-exp

# Optional: Data Sources
APOLLO_API_KEY=your-apollo-key
ZOOMINFO_API_KEY=your-zoominfo-key
ZOOMINFO_USERNAME=your-username
ZOOMINFO_PASSWORD=your-password
LINKEDIN_SESSION_COOKIE=your-linkedin-cookie
SERPAPI_KEY=your-serpapi-key
TWITTER_BEARER_TOKEN=your-twitter-token

# Optional: Enrichment
HUNTER_API_KEY=your-hunter-key
CLEARBIT_API_KEY=your-clearbit-key
```

### Configuration Object

```python
from lead_extraction import LeadExtractionConfig

# Load from environment
config = LeadExtractionConfig.from_env()

# Or create manually
config = LeadExtractionConfig(
    apollo_api_key="your-key",
    hunter_api_key="your-key",
    enable_enrichment=True,
    min_lead_score=70.0,
    max_concurrent_tasks=10
)
```

## Quick Start

### Basic Usage

```python
import asyncio
from lead_extraction import (
    create_lead_extraction_agent,
    ExtractionRequest,
    SearchCriteria,
    LeadSource
)

async def main():
    # Create agent
    agent = create_lead_extraction_agent()

    # Define search criteria
    criteria = SearchCriteria(
        titles=["CEO", "CTO", "VP Engineering"],
        industries=["Technology", "SaaS"],
        company_sizes=["50-200", "201-500"],
        locations=["United States"],
        max_results=500
    )

    # Create extraction request
    request = ExtractionRequest(
        campaign_id="campaign-001",
        search_criteria=criteria,
        sources=[
            LeadSource.APOLLO,
            LeadSource.LINKEDIN,
            LeadSource.GOOGLE_SEARCH
        ],
        min_score=70.0,
        max_leads=1000,
        enable_enrichment=True
    )

    # Extract leads
    result = await agent.extract_leads(request)

    print(f"Extracted {result.total_leads} leads")
    print(f"Average score: {result.statistics['avg_score']:.2f}")

    # Access leads
    for lead in result.leads:
        print(f"{lead.get_full_name()} - {lead.email} - Score: {lead.lead_score}")

asyncio.run(main())
```

### Import from CSV

```python
from lead_extraction import create_lead_extraction_agent

agent = create_lead_extraction_agent()

# Define column mapping
mapping = {
    "First Name": "first_name",
    "Last Name": "last_name",
    "Email": "email",
    "Phone": "phone",
    "Job Title": "title",
    "Company": "company_name",
}

# Import leads
leads = agent.import_from_csv("leads.csv", mapping)

print(f"Imported {len(leads)} leads")
```

### Export Results

```python
import pandas as pd

# After extraction
result = await agent.extract_leads(request)

# Convert to DataFrame
leads_data = [
    {
        "Name": lead.get_full_name(),
        "Email": lead.email,
        "Title": lead.title,
        "Company": lead.company_name,
        "Score": lead.lead_score,
    }
    for lead in result.leads
]

df = pd.DataFrame(leads_data)

# Export to CSV
df.to_csv("extracted_leads.csv", index=False)

# Export to Excel
df.to_excel("extracted_leads.xlsx", index=False)
```

## API Reference

### SearchCriteria

Search parameters for lead extraction:

```python
SearchCriteria(
    keywords: Optional[List[str]] = None,
    titles: Optional[List[str]] = None,
    industries: Optional[List[str]] = None,
    company_sizes: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    seniority_levels: Optional[List[str]] = None,
    departments: Optional[List[str]] = None,
    technologies: Optional[List[str]] = None,
    max_results: int = 100
)
```

### ExtractionRequest

Request for lead extraction:

```python
ExtractionRequest(
    campaign_id: str,
    search_criteria: SearchCriteria,
    sources: List[LeadSource] = [],
    min_score: float = 50.0,
    max_leads: int = 1000,
    enable_enrichment: bool = True
)
```

### ExtractionResult

Result from lead extraction:

```python
ExtractionResult(
    campaign_id: str,
    total_leads: int,
    unique_leads: int,
    sources_used: List[str],
    leads: List[Lead],
    extraction_time: datetime,
    errors: List[str],
    statistics: Dict[str, Any]
)
```

### Lead

Lead data model:

```python
Lead(
    # Contact Information
    first_name: Optional[str],
    last_name: Optional[str],
    email: Optional[EmailStr],
    phone: Optional[str],
    linkedin_url: Optional[HttpUrl],
    twitter_handle: Optional[str],

    # Professional Information
    title: Optional[str],
    seniority_level: Optional[str],
    department: Optional[str],

    # Company Information
    company_name: Optional[str],
    company_domain: Optional[str],
    company_website: Optional[HttpUrl],
    company_industry: Optional[str],
    company_size: Optional[str],
    company_revenue: Optional[str],
    company_location: Optional[str],

    # Metadata
    source: LeadSource,
    confidence_score: float,
    lead_score: float,
    enrichment_status: str,
    tags: List[str],
    custom_fields: Dict[str, Any]
)
```

## Lead Scoring

Leads are automatically scored 0-100 based on:

- **Data Completeness (40 points)** - Email, phone, LinkedIn, etc.
- **Job Title Match (20 points)** - Matches search criteria
- **Company Fit (20 points)** - Industry and size match
- **Seniority Level (10 points)** - C-Level, VP, Director, etc.
- **Email Validity (10 points)** - Valid email format

## Rate Limits

Default rate limits per source:

- **Apollo.io**: 200 requests/minute
- **ZoomInfo**: 100 requests/minute
- **LinkedIn**: 30 requests/minute
- **Google Search (SerpAPI)**: 100 requests/minute
- **Hunter.io**: 100 requests/minute
- **Clearbit**: 600 requests/minute
- **Twitter**: 450 requests/15 minutes

All rate limits are automatically managed with token bucket algorithm and retry logic.

## Error Handling

The system includes comprehensive error handling:

- **Retry Logic**: Automatic retries with exponential backoff
- **Rate Limit Handling**: Respects Retry-After headers
- **Timeout Protection**: Configurable timeouts for all requests
- **Validation**: Pydantic models validate all data
- **Logging**: Detailed logging for debugging

## Best Practices

### 1. Start Small

Begin with a small `max_results` to test your configuration:

```python
criteria = SearchCriteria(
    titles=["CEO"],
    max_results=10  # Start small
)
```

### 2. Use Multiple Sources

Combine sources for better coverage:

```python
sources=[
    LeadSource.APOLLO,
    LeadSource.LINKEDIN,
    LeadSource.ZOOMINFO
]
```

### 3. Enable Enrichment

Always enable enrichment for complete data:

```python
request = ExtractionRequest(
    ...,
    enable_enrichment=True  # Find missing emails
)
```

### 4. Set Appropriate Score Thresholds

Filter for quality with minimum scores:

```python
request = ExtractionRequest(
    ...,
    min_score=70.0  # High quality only
)
```

### 5. Monitor API Quotas

Track your API usage to avoid overages:

```python
# Check statistics
print(result.statistics)
```

## Examples

See `example.py` for comprehensive examples including:

1. Basic extraction from Apollo.io
2. Multi-source extraction with enrichment
3. Web scraping for local businesses
4. Twitter/X lead extraction
5. CSV import and scoring
6. Custom configuration
7. Export to multiple formats

Run examples:

```bash
python lead_extraction/example.py
```

## Troubleshooting

### Authentication Errors

Verify your API keys are correct:

```python
config = LeadExtractionConfig.from_env()
print(f"Apollo key configured: {bool(config.apollo_api_key)}")
```

### Rate Limit Errors

Reduce `max_concurrent_tasks`:

```python
config = LeadExtractionConfig(
    max_concurrent_tasks=3  # Reduce concurrency
)
```

### Low Lead Scores

Adjust scoring threshold or check search criteria:

```python
request = ExtractionRequest(
    min_score=50.0,  # Lower threshold
    ...
)
```

### Missing Emails

Enable enrichment and check Hunter.io quota:

```python
request = ExtractionRequest(
    enable_enrichment=True,
    ...
)
```

## Performance

### Throughput

- **Apollo.io**: ~200 leads/minute
- **ZoomInfo**: ~100 leads/minute
- **LinkedIn**: ~30 leads/minute
- **Web Scraping**: ~10 websites/minute
- **Enrichment**: ~100 leads/minute

### Optimization

1. **Parallel Processing**: Extracts from multiple sources simultaneously
2. **Rate Limiting**: Maximizes throughput within API limits
3. **Caching**: Reduces redundant API calls
4. **Async/Await**: Non-blocking I/O operations

## Security

- **API Keys**: Store in environment variables, never commit
- **Rate Limiting**: Protects against abuse
- **Input Validation**: Pydantic validates all inputs
- **Error Handling**: Prevents sensitive data leakage in errors

## License

Apache License 2.0

## Support

For issues and questions:

- **Documentation**: This README and `example.py`
- **Issues**: [GitHub Issues](https://github.com/google/adk-samples/issues)
- **Discussions**: [GitHub Discussions](https://github.com/google/adk-samples/discussions)

## Contributing

Contributions welcome! Please read the main repository's CONTRIBUTING.md.

---

**Built with Google Agent Development Kit (ADK)**
