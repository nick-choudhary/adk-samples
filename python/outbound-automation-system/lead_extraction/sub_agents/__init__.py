"""
Sub-Agents for Lead Extraction System

This module provides specialized sub-agents for different lead extraction tasks.
Each sub-agent focuses on a specific data source or processing task.

Available Sub-Agents:
    - DatabaseSearchAgent: Searches B2B databases (Apollo.io, ZoomInfo)
    - LinkedInAgent: LinkedIn Sales Navigator extraction
    - WebScrapingAgent: Google Search and web scraping
    - SocialMediaAgent: Twitter/X lead extraction
    - EnrichmentAgent: Email finding and company enrichment (Hunter.io, Clearbit)
    - ScoringAgent: Lead deduplication and quality scoring

Each sub-agent:
    - Inherits from google.adk.Agent
    - Has specialized tools and instructions
    - Handles rate limiting and errors
    - Returns structured Lead data
    - Integrates with the main orchestrator

Example:
    ```python
    from lead_extraction.sub_agents import DatabaseSearchAgent
    from lead_extraction import LeadExtractionConfig, SearchCriteria

    config = LeadExtractionConfig.from_env()
    agent = DatabaseSearchAgent(config)

    criteria = SearchCriteria(
        titles=["CEO", "CTO"],
        industries=["Technology"],
        max_results=100
    )

    # The orchestrator will use this agent automatically
    ```
"""

from ..agent import (
    DatabaseSearchAgent,
    EnrichmentAgent,
    LinkedInAgent,
    ScoringAgent,
    SocialMediaAgent,
    WebScrapingAgent,
)

__all__ = [
    "DatabaseSearchAgent",
    "LinkedInAgent",
    "WebScrapingAgent",
    "SocialMediaAgent",
    "EnrichmentAgent",
    "ScoringAgent",
]
