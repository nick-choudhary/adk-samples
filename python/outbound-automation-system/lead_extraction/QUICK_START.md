# Lead Extraction System - Quick Start Guide

## 1. Setup (2 minutes)

### Install Dependencies

```bash
cd /home/user/adk-samples/python/outbound-automation-system
pip install -r requirements.txt
```

### Configure API Keys

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

Minimum required:
```bash
GCP_PROJECT_ID=your-project
APOLLO_API_KEY=your-apollo-key  # Or another data source
```

## 2. Basic Usage (5 minutes)

### Simple Extraction

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

    # Define what you're looking for
    criteria = SearchCriteria(
        titles=["CEO", "CTO"],
        industries=["Technology"],
        max_results=50
    )

    # Create request
    request = ExtractionRequest(
        campaign_id="my-campaign",
        search_criteria=criteria,
        sources=[LeadSource.APOLLO],
        min_score=60.0
    )

    # Extract!
    result = await agent.extract_leads(request)

    # View results
    print(f"Found {result.total_leads} leads")
    for lead in result.leads[:5]:
        print(f"  {lead.get_full_name()} - {lead.email}")

asyncio.run(main())
```

## 3. Common Use Cases

### Find CTOs at Tech Companies

```python
criteria = SearchCriteria(
    titles=["CTO", "VP Engineering", "Head of Engineering"],
    industries=["Technology", "SaaS"],
    company_sizes=["51-200", "201-500"],
    locations=["United States"]
)

request = ExtractionRequest(
    campaign_id="cto-outreach",
    search_criteria=criteria,
    sources=[LeadSource.APOLLO, LeadSource.LINKEDIN],
    min_score=70.0,
    enable_enrichment=True
)
```

### Find Marketing Leaders

```python
criteria = SearchCriteria(
    titles=["CMO", "VP Marketing", "Marketing Director"],
    industries=["E-commerce", "Retail"],
    seniority_levels=["C-Level", "VP"],
    max_results=200
)
```

### Find Local Businesses

```python
criteria = SearchCriteria(
    keywords=["restaurant", "cafe", "coffee shop"],
    locations=["San Francisco, CA"]
)

request = ExtractionRequest(
    campaign_id="local-business",
    search_criteria=criteria,
    sources=[LeadSource.GOOGLE_SEARCH],
    min_score=40.0
)
```

### Import and Score CSV

```python
agent = create_lead_extraction_agent()

mapping = {
    "First Name": "first_name",
    "Last Name": "last_name",
    "Email": "email",
    "Title": "title",
    "Company": "company_name"
}

leads = agent.import_from_csv("leads.csv", mapping)

# Score leads
from lead_extraction.tools import LeadScorer
for lead in leads:
    lead.lead_score = LeadScorer.score_lead(lead)

# Filter high quality
good_leads = [l for l in leads if l.lead_score >= 70]
print(f"High quality: {len(good_leads)}/{len(leads)}")
```

## 4. Export Results

### To CSV

```python
import pandas as pd

result = await agent.extract_leads(request)

df = pd.DataFrame([
    {
        "Name": lead.get_full_name(),
        "Email": lead.email,
        "Title": lead.title,
        "Company": lead.company_name,
        "Score": lead.lead_score
    }
    for lead in result.leads
])

df.to_csv("leads.csv", index=False)
```

### To Excel

```python
df.to_excel("leads.xlsx", index=False, sheet_name="Leads")
```

### To JSON

```python
import json

with open("leads.json", "w") as f:
    json.dump(result.dict(), f, indent=2, default=str)
```

## 5. Configuration Options

### Custom Config

```python
from lead_extraction import LeadExtractionConfig

config = LeadExtractionConfig(
    apollo_api_key="your-key",
    hunter_api_key="your-key",
    enable_enrichment=True,
    min_lead_score=70.0,
    max_concurrent_tasks=5
)

agent = create_lead_extraction_agent(config)
```

### All Sources

```python
sources=[
    LeadSource.APOLLO,        # Apollo.io database
    LeadSource.ZOOMINFO,      # ZoomInfo database
    LeadSource.LINKEDIN,      # LinkedIn Sales Navigator
    LeadSource.GOOGLE_SEARCH, # Google + web scraping
    LeadSource.TWITTER,       # Twitter/X
]
```

## 6. Tips & Tricks

### Start Small

```python
# Test with small numbers first
criteria = SearchCriteria(
    titles=["CEO"],
    max_results=10  # Start small!
)
```

### Use Multiple Sources

```python
# Combine sources for better coverage
sources=[
    LeadSource.APOLLO,
    LeadSource.LINKEDIN,
    LeadSource.ZOOMINFO
]
```

### Enable Enrichment

```python
# Always enable for complete data
request = ExtractionRequest(
    ...,
    enable_enrichment=True  # Finds missing emails!
)
```

### Filter by Quality

```python
# Set minimum score threshold
request = ExtractionRequest(
    ...,
    min_score=70.0  # Only high quality
)
```

### Check Statistics

```python
result = await agent.extract_leads(request)

print(result.statistics)
# {
#   'total_leads': 150,
#   'avg_score': 72.5,
#   'with_email': 145,
#   'enriched': 50,
#   ...
# }
```

## 7. Troubleshooting

### No Leads Found

1. Check API keys are configured
2. Broaden search criteria
3. Lower min_score threshold
4. Try different sources

### Rate Limit Errors

1. Reduce max_results
2. Lower max_concurrent_tasks
3. Wait and retry
4. Check API quota

### Missing Emails

1. Enable enrichment
2. Check Hunter.io quota
3. Use multiple sources
4. Verify company domains

### Low Scores

1. Enable enrichment first
2. Check if data is complete
3. Lower min_score
4. Review scoring algorithm

## 8. Examples

Run comprehensive examples:

```bash
python lead_extraction/example.py
```

Includes:
- Basic Apollo extraction
- Multi-source with enrichment
- Web scraping
- Twitter extraction
- CSV import
- Custom configuration
- Export to multiple formats

## 9. Next Steps

1. Read full [README.md](README.md)
2. Check [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) for architecture
3. Review [example.py](example.py) for code samples
4. Integrate with your application

## 10. Support

- **Documentation**: This guide, README.md, example.py
- **Issues**: [GitHub Issues](https://github.com/google/adk-samples/issues)
- **Discussions**: [GitHub Discussions](https://github.com/google/adk-samples/discussions)

---

**Ready to extract leads? Start with the simple example above!**
