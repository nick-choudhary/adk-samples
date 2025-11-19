"""
Lead Extraction System for Outbound Automation

This package provides a comprehensive multi-agent system for extracting, enriching,
and scoring B2B leads from multiple sources including Apollo.io, ZoomInfo, LinkedIn,
Google Search, web scraping, social media, and file imports.

Key Components:
    - LeadExtractionOrchestrator: Main orchestrator agent
    - DatabaseSearchAgent: Searches Apollo.io and ZoomInfo
    - LinkedInAgent: Searches LinkedIn Sales Navigator
    - WebScrapingAgent: Google Search and web scraping
    - SocialMediaAgent: Twitter/X lead extraction
    - EnrichmentAgent: Email finding and company enrichment
    - ScoringAgent: Deduplication and lead scoring

Example Usage:
    ```python
    from lead_extraction import create_lead_extraction_agent, ExtractionRequest, SearchCriteria, LeadSource

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
        campaign_id="campaign-123",
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
    ```

Production Features:
    - Rate limiting and retry logic
    - Comprehensive error handling
    - Async/parallel processing
    - Data validation with Pydantic
    - Deduplication and scoring
    - Multi-source aggregation
    - Email verification
    - Company enrichment
"""

from .agent import (
    DatabaseSearchAgent,
    EnrichmentAgent,
    ExtractionRequest,
    ExtractionResult,
    LeadExtractionConfig,
    LeadExtractionOrchestrator,
    LinkedInAgent,
    ScoringAgent,
    SocialMediaAgent,
    WebScrapingAgent,
    create_lead_extraction_agent,
)
from .tools import (
    ApolloClient,
    ClearbitClient,
    FileImporter,
    GoogleSearchClient,
    HunterIOClient,
    Lead,
    LeadDeduplicator,
    LeadScorer,
    LeadSource,
    LinkedInClient,
    RateLimiter,
    SearchCriteria,
    TwitterClient,
    WebScraper,
    ZoomInfoClient,
)

__version__ = "1.0.0"

__all__ = [
    # Main Components
    "LeadExtractionOrchestrator",
    "create_lead_extraction_agent",

    # Configuration
    "LeadExtractionConfig",
    "ExtractionRequest",
    "ExtractionResult",

    # Sub-Agents
    "DatabaseSearchAgent",
    "LinkedInAgent",
    "WebScrapingAgent",
    "SocialMediaAgent",
    "EnrichmentAgent",
    "ScoringAgent",

    # Data Models
    "Lead",
    "LeadSource",
    "SearchCriteria",

    # Clients
    "ApolloClient",
    "ZoomInfoClient",
    "LinkedInClient",
    "GoogleSearchClient",
    "WebScraper",
    "TwitterClient",
    "HunterIOClient",
    "ClearbitClient",
    "FileImporter",

    # Utilities
    "RateLimiter",
    "LeadDeduplicator",
    "LeadScorer",
]
