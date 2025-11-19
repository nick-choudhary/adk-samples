"""
Lead Extraction Agent System for Outbound Automation

This module provides a comprehensive multi-agent system for extracting, enriching,
and scoring leads from multiple sources. The system uses Google ADK to orchestrate
specialized sub-agents for different extraction tasks.

Architecture:
    LeadExtractionOrchestrator (main agent)
    ├── DatabaseSearchAgent (Apollo.io, ZoomInfo)
    ├── LinkedInAgent (LinkedIn Sales Navigator)
    ├── WebScrapingAgent (Google Search, web scraping)
    ├── SocialMediaAgent (Twitter/X)
    ├── EnrichmentAgent (Hunter.io, Clearbit)
    └── ScoringAgent (deduplication, scoring)
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.adk import Agent
from google.adk.toolkits import ToolKit
from pydantic import BaseModel, Field

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
    SearchCriteria,
    TwitterClient,
    WebScraper,
    ZoomInfoClient,
    apollo_search_tool,
    company_enrichment_tool,
    deduplication_tool,
    email_finder_tool,
    google_search_tool,
    lead_scoring_tool,
    linkedin_search_tool,
    web_scraping_tool,
    zoominfo_search_tool,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class LeadExtractionConfig(BaseModel):
    """Configuration for lead extraction system"""

    # API Keys
    apollo_api_key: Optional[str] = Field(default=None)
    zoominfo_api_key: Optional[str] = Field(default=None)
    zoominfo_username: Optional[str] = Field(default=None)
    zoominfo_password: Optional[str] = Field(default=None)
    linkedin_session_cookie: Optional[str] = Field(default=None)
    serpapi_key: Optional[str] = Field(default=None)
    twitter_bearer_token: Optional[str] = Field(default=None)
    hunter_api_key: Optional[str] = Field(default=None)
    clearbit_api_key: Optional[str] = Field(default=None)

    # Google Cloud
    gcp_project_id: str = Field(default="")
    gcp_region: str = Field(default="us-central1")
    vertex_ai_model: str = Field(default="gemini-2.0-flash-exp")

    # Processing Options
    enable_enrichment: bool = Field(default=True)
    enable_deduplication: bool = Field(default=True)
    enable_scoring: bool = Field(default=True)
    min_lead_score: float = Field(default=50.0)
    max_concurrent_tasks: int = Field(default=10)

    @classmethod
    def from_env(cls) -> "LeadExtractionConfig":
        """Create configuration from environment variables"""
        return cls(
            apollo_api_key=os.getenv("APOLLO_API_KEY"),
            zoominfo_api_key=os.getenv("ZOOMINFO_API_KEY"),
            zoominfo_username=os.getenv("ZOOMINFO_USERNAME"),
            zoominfo_password=os.getenv("ZOOMINFO_PASSWORD"),
            linkedin_session_cookie=os.getenv("LINKEDIN_SESSION_COOKIE"),
            serpapi_key=os.getenv("SERPAPI_KEY"),
            twitter_bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
            hunter_api_key=os.getenv("HUNTER_API_KEY"),
            clearbit_api_key=os.getenv("CLEARBIT_API_KEY"),
            gcp_project_id=os.getenv("GCP_PROJECT_ID", ""),
            gcp_region=os.getenv("GCP_REGION", "us-central1"),
            vertex_ai_model=os.getenv("VERTEX_AI_MODEL", "gemini-2.0-flash-exp"),
        )


# ============================================================================
# Extraction Request/Response Models
# ============================================================================

class ExtractionRequest(BaseModel):
    """Lead extraction request"""
    campaign_id: str
    search_criteria: SearchCriteria
    sources: List[LeadSource] = Field(default_factory=list)
    min_score: float = Field(default=50.0)
    max_leads: int = Field(default=1000)
    enable_enrichment: bool = Field(default=True)


class ExtractionResult(BaseModel):
    """Lead extraction result"""
    campaign_id: str
    total_leads: int
    unique_leads: int
    sources_used: List[str]
    leads: List[Lead]
    extraction_time: datetime = Field(default_factory=datetime.utcnow)
    errors: List[str] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Sub-Agents
# ============================================================================

class DatabaseSearchAgent(Agent):
    """Agent for searching B2B contact databases (Apollo.io, ZoomInfo)"""

    def __init__(self, config: LeadExtractionConfig):
        self.config = config

        # Initialize clients
        self.apollo_client = None
        if config.apollo_api_key:
            self.apollo_client = ApolloClient(config.apollo_api_key)

        self.zoominfo_client = None
        if config.zoominfo_api_key and config.zoominfo_username and config.zoominfo_password:
            self.zoominfo_client = ZoomInfoClient(
                api_key=config.zoominfo_api_key,
                username=config.zoominfo_username,
                password=config.zoominfo_password,
            )

        # Create toolkit
        toolkit = ToolKit(name="database_search")
        if self.apollo_client:
            toolkit.add_tool(apollo_search_tool, self._search_apollo)
        if self.zoominfo_client:
            toolkit.add_tool(zoominfo_search_tool, self._search_zoominfo)

        # Initialize agent
        super().__init__(
            name="DatabaseSearchAgent",
            model=config.vertex_ai_model,
            instruction="""You are a database search specialist for B2B lead generation.
            Your role is to search Apollo.io and ZoomInfo databases to find high-quality leads
            matching the specified criteria.

            Key responsibilities:
            1. Parse search criteria and convert to database-specific queries
            2. Execute searches across available databases
            3. Return structured lead data with complete contact information
            4. Handle rate limits and API errors gracefully

            Always aim for accuracy and completeness in the data you return.""",
            toolkits=[toolkit],
        )

    def _search_apollo(self, **kwargs) -> List[Dict[str, Any]]:
        """Search Apollo.io database"""
        if not self.apollo_client:
            logger.warning("Apollo.io client not configured")
            return []

        try:
            criteria = SearchCriteria(**kwargs)
            leads = self.apollo_client.search_people(criteria)
            return [lead.dict() for lead in leads]
        except Exception as e:
            logger.error(f"Apollo.io search failed: {e}")
            return []

    def _search_zoominfo(self, **kwargs) -> List[Dict[str, Any]]:
        """Search ZoomInfo database"""
        if not self.zoominfo_client:
            logger.warning("ZoomInfo client not configured")
            return []

        try:
            criteria = SearchCriteria(**kwargs)
            leads = self.zoominfo_client.search_contacts(criteria)
            return [lead.dict() for lead in leads]
        except Exception as e:
            logger.error(f"ZoomInfo search failed: {e}")
            return []


class LinkedInAgent(Agent):
    """Agent for LinkedIn Sales Navigator extraction"""

    def __init__(self, config: LeadExtractionConfig):
        self.config = config

        # Initialize LinkedIn client
        self.linkedin_client = None
        if config.linkedin_session_cookie:
            self.linkedin_client = LinkedInClient(config.linkedin_session_cookie)

        # Create toolkit
        toolkit = ToolKit(name="linkedin_search")
        if self.linkedin_client:
            toolkit.add_tool(linkedin_search_tool, self._search_linkedin)

        # Initialize agent
        super().__init__(
            name="LinkedInAgent",
            model=config.vertex_ai_model,
            instruction="""You are a LinkedIn Sales Navigator specialist for B2B lead generation.
            Your role is to search LinkedIn to find professionals and decision-makers
            matching the specified criteria.

            Key responsibilities:
            1. Convert search criteria to LinkedIn-specific filters
            2. Execute Sales Navigator searches
            3. Extract comprehensive profile information
            4. Respect LinkedIn's rate limits and terms of service

            Focus on finding verified, active LinkedIn users with complete profiles.""",
            toolkits=[toolkit],
        )

    def _search_linkedin(self, **kwargs) -> List[Dict[str, Any]]:
        """Search LinkedIn Sales Navigator"""
        if not self.linkedin_client:
            logger.warning("LinkedIn client not configured")
            return []

        try:
            criteria = SearchCriteria(**kwargs)
            leads = self.linkedin_client.search_people(criteria)
            return [lead.dict() for lead in leads]
        except Exception as e:
            logger.error(f"LinkedIn search failed: {e}")
            return []


class WebScrapingAgent(Agent):
    """Agent for web scraping and Google Search"""

    def __init__(self, config: LeadExtractionConfig):
        self.config = config

        # Initialize clients
        self.google_client = None
        if config.serpapi_key:
            self.google_client = GoogleSearchClient(config.serpapi_key)

        self.web_scraper = WebScraper(headless=True)

        # Create toolkit
        toolkit = ToolKit(name="web_scraping")
        if self.google_client:
            toolkit.add_tool(google_search_tool, self._search_google)
        toolkit.add_tool(web_scraping_tool, self._scrape_website)

        # Initialize agent
        super().__init__(
            name="WebScrapingAgent",
            model=config.vertex_ai_model,
            instruction="""You are a web scraping specialist for lead generation.
            Your role is to find businesses through Google Search and extract contact
            information from their websites.

            Key responsibilities:
            1. Execute Google searches for businesses matching criteria
            2. Scrape websites to extract contact information (emails, phones, social links)
            3. Parse and structure the extracted data
            4. Handle various website structures and formats
            5. Respect robots.txt and rate limits

            Be thorough but respectful of website resources.""",
            toolkits=[toolkit],
        )

    def _search_google(self, query: str, location: str = "United States", max_results: int = 50) -> List[Dict[str, Any]]:
        """Search Google for businesses"""
        if not self.google_client:
            logger.warning("Google Search client not configured")
            return []

        try:
            results = self.google_client.search_businesses(query, location, max_results)
            return results
        except Exception as e:
            logger.error(f"Google Search failed: {e}")
            return []

    def _scrape_website(self, url: str) -> Dict[str, Any]:
        """Scrape website for contact information"""
        try:
            data = self.web_scraper.scrape_website(url)
            return data
        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            return {"url": url, "error": str(e)}


class SocialMediaAgent(Agent):
    """Agent for social media lead extraction (Twitter/X)"""

    def __init__(self, config: LeadExtractionConfig):
        self.config = config

        # Initialize Twitter client
        self.twitter_client = None
        if config.twitter_bearer_token:
            self.twitter_client = TwitterClient(config.twitter_bearer_token)

        # Create toolkit
        toolkit = ToolKit(name="social_media")
        # Twitter search tool would be added here

        # Initialize agent
        super().__init__(
            name="SocialMediaAgent",
            model=config.vertex_ai_model,
            instruction="""You are a social media specialist for lead generation.
            Your role is to find potential leads on social media platforms,
            particularly Twitter/X, based on their activity and profiles.

            Key responsibilities:
            1. Search Twitter for users matching criteria
            2. Analyze social signals (followers, engagement, bio)
            3. Extract contact information from profiles
            4. Assess lead quality based on social presence

            Focus on finding active, engaged users who match the target profile.""",
            toolkits=[toolkit],
        )


class EnrichmentAgent(Agent):
    """Agent for data enrichment (email finding, company data)"""

    def __init__(self, config: LeadExtractionConfig):
        self.config = config

        # Initialize enrichment clients
        self.hunter_client = None
        if config.hunter_api_key:
            self.hunter_client = HunterIOClient(config.hunter_api_key)

        self.clearbit_client = None
        if config.clearbit_api_key:
            self.clearbit_client = ClearbitClient(config.clearbit_api_key)

        # Create toolkit
        toolkit = ToolKit(name="enrichment")
        if self.hunter_client:
            toolkit.add_tool(email_finder_tool, self._find_email)
        if self.clearbit_client:
            toolkit.add_tool(company_enrichment_tool, self._enrich_company)

        # Initialize agent
        super().__init__(
            name="EnrichmentAgent",
            model=config.vertex_ai_model,
            instruction="""You are a data enrichment specialist for lead generation.
            Your role is to enhance lead data by finding missing information like
            email addresses, phone numbers, and company details.

            Key responsibilities:
            1. Find and verify email addresses using Hunter.io
            2. Enrich company data using Clearbit
            3. Validate and format contact information
            4. Assess data quality and confidence scores

            Always prioritize accuracy over quantity.""",
            toolkits=[toolkit],
        )

    def _find_email(self, first_name: str, last_name: str, company_domain: str) -> Optional[str]:
        """Find email address"""
        if not self.hunter_client:
            logger.warning("Hunter.io client not configured")
            return None

        try:
            email = self.hunter_client.find_email(first_name, last_name, company_domain)
            return email
        except Exception as e:
            logger.error(f"Email finding failed: {e}")
            return None

    def _enrich_company(self, domain: str) -> Dict[str, Any]:
        """Enrich company data"""
        if not self.clearbit_client:
            logger.warning("Clearbit client not configured")
            return {}

        try:
            data = self.clearbit_client.enrich_company(domain)
            return data
        except Exception as e:
            logger.error(f"Company enrichment failed: {e}")
            return {}


class ScoringAgent(Agent):
    """Agent for lead deduplication and scoring"""

    def __init__(self, config: LeadExtractionConfig):
        self.config = config

        # Create toolkit
        toolkit = ToolKit(name="scoring")
        toolkit.add_tool(deduplication_tool, self._deduplicate_leads)
        toolkit.add_tool(lead_scoring_tool, self._score_leads)

        # Initialize agent
        super().__init__(
            name="ScoringAgent",
            model=config.vertex_ai_model,
            instruction="""You are a lead quality specialist for lead generation.
            Your role is to deduplicate leads and calculate quality scores based on
            data completeness, job fit, and company fit.

            Key responsibilities:
            1. Remove duplicate leads based on email and name+company
            2. Calculate lead quality scores (0-100)
            3. Assess data completeness
            4. Evaluate job title and company fit against criteria

            Be strict about duplicates and accurate with scoring.""",
            toolkits=[toolkit],
        )

    def _deduplicate_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate leads"""
        try:
            lead_objects = [Lead(**lead_data) for lead_data in leads]
            unique_leads = LeadDeduplicator.deduplicate(lead_objects)
            return [lead.dict() for lead in unique_leads]
        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
            return leads

    def _score_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score leads"""
        try:
            scored_leads = []
            for lead_data in leads:
                lead = Lead(**lead_data)
                score = LeadScorer.score_lead(lead)
                lead.lead_score = score
                scored_leads.append(lead.dict())
            return scored_leads
        except Exception as e:
            logger.error(f"Lead scoring failed: {e}")
            return leads


# ============================================================================
# Main Orchestrator Agent
# ============================================================================

class LeadExtractionOrchestrator(Agent):
    """
    Main orchestrator agent for lead extraction system.

    This agent coordinates multiple specialized sub-agents to extract, enrich,
    deduplicate, and score leads from various sources.
    """

    def __init__(self, config: Optional[LeadExtractionConfig] = None):
        """
        Initialize Lead Extraction Orchestrator

        Args:
            config: Configuration for lead extraction system
        """
        self.config = config or LeadExtractionConfig.from_env()

        # Initialize sub-agents
        self.database_agent = DatabaseSearchAgent(self.config)
        self.linkedin_agent = LinkedInAgent(self.config)
        self.web_scraping_agent = WebScrapingAgent(self.config)
        self.social_media_agent = SocialMediaAgent(self.config)
        self.enrichment_agent = EnrichmentAgent(self.config)
        self.scoring_agent = ScoringAgent(self.config)

        # Create main agent
        super().__init__(
            name="LeadExtractionOrchestrator",
            model=self.config.vertex_ai_model,
            instruction="""You are the Lead Extraction Orchestrator, responsible for coordinating
            a team of specialized agents to extract and enrich B2B leads from multiple sources.

            Your team consists of:
            1. DatabaseSearchAgent - Searches Apollo.io and ZoomInfo
            2. LinkedInAgent - Searches LinkedIn Sales Navigator
            3. WebScrapingAgent - Performs Google searches and web scraping
            4. SocialMediaAgent - Searches Twitter/X for leads
            5. EnrichmentAgent - Finds emails and enriches company data
            6. ScoringAgent - Deduplicates and scores leads

            Your responsibilities:
            1. Analyze extraction requests and determine which sources to use
            2. Coordinate parallel searches across multiple sources
            3. Delegate tasks to appropriate sub-agents
            4. Aggregate results from all sources
            5. Trigger enrichment for incomplete leads
            6. Ensure deduplication and scoring
            7. Filter leads by minimum score threshold
            8. Compile comprehensive extraction results

            Always aim for high-quality, complete lead data while respecting rate limits
            and API quotas. Prioritize verified data sources and thorough enrichment.""",
            agents=[
                self.database_agent,
                self.linkedin_agent,
                self.web_scraping_agent,
                self.social_media_agent,
                self.enrichment_agent,
                self.scoring_agent,
            ],
        )

        logger.info("Lead Extraction Orchestrator initialized")

    async def extract_leads(self, request: ExtractionRequest) -> ExtractionResult:
        """
        Extract leads based on request criteria

        Args:
            request: Extraction request with criteria and preferences

        Returns:
            ExtractionResult with leads and statistics
        """
        logger.info(f"Starting lead extraction for campaign {request.campaign_id}")
        start_time = datetime.utcnow()

        all_leads: List[Lead] = []
        errors: List[str] = []
        sources_used: List[str] = []

        try:
            # Phase 1: Extract from specified sources
            extraction_tasks = []

            if LeadSource.APOLLO in request.sources:
                extraction_tasks.append(self._extract_from_apollo(request.search_criteria))
                sources_used.append(LeadSource.APOLLO)

            if LeadSource.ZOOMINFO in request.sources:
                extraction_tasks.append(self._extract_from_zoominfo(request.search_criteria))
                sources_used.append(LeadSource.ZOOMINFO)

            if LeadSource.LINKEDIN in request.sources:
                extraction_tasks.append(self._extract_from_linkedin(request.search_criteria))
                sources_used.append(LeadSource.LINKEDIN)

            if LeadSource.GOOGLE_SEARCH in request.sources:
                extraction_tasks.append(self._extract_from_google(request.search_criteria))
                sources_used.append(LeadSource.GOOGLE_SEARCH)

            if LeadSource.TWITTER in request.sources:
                extraction_tasks.append(self._extract_from_twitter(request.search_criteria))
                sources_used.append(LeadSource.TWITTER)

            # Execute extraction tasks in parallel
            if extraction_tasks:
                results = await asyncio.gather(*extraction_tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        errors.append(str(result))
                        logger.error(f"Extraction task failed: {result}")
                    else:
                        all_leads.extend(result)

            logger.info(f"Extracted {len(all_leads)} leads from {len(sources_used)} sources")

            # Phase 2: Enrichment (if enabled)
            if request.enable_enrichment and self.config.enable_enrichment:
                all_leads = await self._enrich_leads(all_leads)

            # Phase 3: Deduplication
            if self.config.enable_deduplication:
                all_leads = LeadDeduplicator.deduplicate(all_leads)
                logger.info(f"After deduplication: {len(all_leads)} unique leads")

            # Phase 4: Scoring
            if self.config.enable_scoring:
                for lead in all_leads:
                    lead.lead_score = LeadScorer.score_lead(lead, request.search_criteria)

                # Filter by minimum score
                all_leads = [lead for lead in all_leads if lead.lead_score >= request.min_score]
                logger.info(f"After score filtering (>={request.min_score}): {len(all_leads)} leads")

            # Phase 5: Limit results
            if len(all_leads) > request.max_leads:
                # Sort by score and take top N
                all_leads.sort(key=lambda x: x.lead_score, reverse=True)
                all_leads = all_leads[:request.max_leads]

            # Calculate statistics
            statistics = self._calculate_statistics(all_leads)
            extraction_time = (datetime.utcnow() - start_time).total_seconds()
            statistics["extraction_time_seconds"] = extraction_time

            return ExtractionResult(
                campaign_id=request.campaign_id,
                total_leads=len(all_leads),
                unique_leads=len(all_leads),
                sources_used=sources_used,
                leads=all_leads,
                errors=errors,
                statistics=statistics,
            )

        except Exception as e:
            logger.error(f"Lead extraction failed: {e}", exc_info=True)
            errors.append(f"Extraction failed: {str(e)}")

            return ExtractionResult(
                campaign_id=request.campaign_id,
                total_leads=0,
                unique_leads=0,
                sources_used=sources_used,
                leads=[],
                errors=errors,
                statistics={},
            )

    async def _extract_from_apollo(self, criteria: SearchCriteria) -> List[Lead]:
        """Extract leads from Apollo.io"""
        if not self.database_agent.apollo_client:
            return []

        try:
            leads = self.database_agent.apollo_client.search_people(criteria)
            logger.info(f"Apollo.io: {len(leads)} leads")
            return leads
        except Exception as e:
            logger.error(f"Apollo extraction failed: {e}")
            return []

    async def _extract_from_zoominfo(self, criteria: SearchCriteria) -> List[Lead]:
        """Extract leads from ZoomInfo"""
        if not self.database_agent.zoominfo_client:
            return []

        try:
            leads = self.database_agent.zoominfo_client.search_contacts(criteria)
            logger.info(f"ZoomInfo: {len(leads)} leads")
            return leads
        except Exception as e:
            logger.error(f"ZoomInfo extraction failed: {e}")
            return []

    async def _extract_from_linkedin(self, criteria: SearchCriteria) -> List[Lead]:
        """Extract leads from LinkedIn"""
        if not self.linkedin_agent.linkedin_client:
            return []

        try:
            leads = self.linkedin_agent.linkedin_client.search_people(criteria)
            logger.info(f"LinkedIn: {len(leads)} leads")
            return leads
        except Exception as e:
            logger.error(f"LinkedIn extraction failed: {e}")
            return []

    async def _extract_from_google(self, criteria: SearchCriteria) -> List[Lead]:
        """Extract leads from Google Search + web scraping"""
        if not self.web_scraping_agent.google_client:
            return []

        leads = []
        try:
            # Build search query
            query_parts = []
            if criteria.keywords:
                query_parts.extend(criteria.keywords)
            if criteria.industries:
                query_parts.extend(criteria.industries)

            query = " ".join(query_parts)

            # Search Google
            results = self.web_scraping_agent.google_client.search_businesses(
                query=query,
                max_results=criteria.max_results
            )

            # Scrape websites (limit concurrent scraping)
            semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)

            async def scrape_with_limit(url: str):
                async with semaphore:
                    return self.web_scraping_agent.web_scraper.scrape_website(url)

            # Scrape top results
            scrape_tasks = [scrape_with_limit(r["url"]) for r in results[:20]]
            scraped_data = await asyncio.gather(*scrape_tasks, return_exceptions=True)

            # Convert scraped data to leads
            for data in scraped_data:
                if isinstance(data, dict) and not data.get("error"):
                    # Create lead from scraped data
                    for email in data.get("emails", []):
                        lead = Lead(
                            email=email,
                            company_website=data.get("url"),
                            source=LeadSource.WEB_SCRAPING,
                        )
                        leads.append(lead)

            logger.info(f"Google Search + Scraping: {len(leads)} leads")
            return leads

        except Exception as e:
            logger.error(f"Google Search extraction failed: {e}")
            return []

    async def _extract_from_twitter(self, criteria: SearchCriteria) -> List[Lead]:
        """Extract leads from Twitter/X"""
        if not self.social_media_agent.twitter_client:
            return []

        leads = []
        try:
            # Build Twitter search query
            query_parts = []
            if criteria.keywords:
                query_parts.extend(criteria.keywords)
            if criteria.titles:
                query_parts.extend(criteria.titles)

            query = " ".join(query_parts)

            # Search Twitter
            users = self.social_media_agent.twitter_client.search_users(
                query=query,
                max_results=criteria.max_results
            )

            # Convert to leads
            for user in users:
                lead = Lead(
                    twitter_handle=user.get("username"),
                    company_name=user.get("description", "").split("|")[0].strip() if "|" in user.get("description", "") else None,
                    source=LeadSource.TWITTER,
                )
                leads.append(lead)

            logger.info(f"Twitter: {len(leads)} leads")
            return leads

        except Exception as e:
            logger.error(f"Twitter extraction failed: {e}")
            return []

    async def _enrich_leads(self, leads: List[Lead]) -> List[Lead]:
        """Enrich leads with missing data"""
        enriched_leads = []

        semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)

        async def enrich_lead(lead: Lead) -> Lead:
            async with semaphore:
                # Find email if missing
                if not lead.email and lead.first_name and lead.last_name and lead.company_domain:
                    if self.enrichment_agent.hunter_client:
                        try:
                            email = self.enrichment_agent.hunter_client.find_email(
                                lead.first_name,
                                lead.last_name,
                                lead.company_domain
                            )
                            if email:
                                lead.email = email
                                lead.enrichment_status = "enriched"
                        except Exception as e:
                            logger.warning(f"Email enrichment failed: {e}")

                # Enrich company data if domain available
                if lead.company_domain and self.enrichment_agent.clearbit_client:
                    try:
                        company_data = self.enrichment_agent.clearbit_client.enrich_company(
                            lead.company_domain
                        )
                        if company_data:
                            # Update lead with company data
                            if not lead.company_name:
                                lead.company_name = company_data.get("name")
                            if not lead.company_industry:
                                lead.company_industry = company_data.get("industry")
                            if not lead.company_size:
                                lead.company_size = str(company_data.get("employees", ""))
                            if not lead.company_revenue:
                                lead.company_revenue = str(company_data.get("revenue", ""))

                            lead.enrichment_status = "enriched"
                    except Exception as e:
                        logger.warning(f"Company enrichment failed: {e}")

                return lead

        # Enrich leads in parallel
        enrichment_tasks = [enrich_lead(lead) for lead in leads]
        enriched_leads = await asyncio.gather(*enrichment_tasks, return_exceptions=True)

        # Filter out exceptions
        valid_leads = [
            lead for lead in enriched_leads
            if not isinstance(lead, Exception)
        ]

        logger.info(f"Enriched {len(valid_leads)} leads")
        return valid_leads

    def _calculate_statistics(self, leads: List[Lead]) -> Dict[str, Any]:
        """Calculate extraction statistics"""
        if not leads:
            return {}

        return {
            "total_leads": len(leads),
            "avg_score": sum(lead.lead_score for lead in leads) / len(leads),
            "max_score": max(lead.lead_score for lead in leads),
            "min_score": min(lead.lead_score for lead in leads),
            "with_email": sum(1 for lead in leads if lead.email),
            "with_phone": sum(1 for lead in leads if lead.phone),
            "with_linkedin": sum(1 for lead in leads if lead.linkedin_url),
            "enriched": sum(1 for lead in leads if lead.enrichment_status == "enriched"),
            "sources": {
                source.value: sum(1 for lead in leads if lead.source == source)
                for source in LeadSource
            },
        }

    def import_from_csv(self, file_path: str, mapping: Dict[str, str]) -> List[Lead]:
        """Import leads from CSV file"""
        return FileImporter.import_csv(file_path, mapping)

    def import_from_excel(
        self,
        file_path: str,
        mapping: Dict[str, str],
        sheet_name: str = 0
    ) -> List[Lead]:
        """Import leads from Excel file"""
        return FileImporter.import_excel(file_path, mapping, sheet_name)


# ============================================================================
# Factory Function
# ============================================================================

def create_lead_extraction_agent(config: Optional[LeadExtractionConfig] = None) -> LeadExtractionOrchestrator:
    """
    Factory function to create and configure the Lead Extraction Orchestrator

    Args:
        config: Optional configuration. If not provided, loads from environment.

    Returns:
        Configured LeadExtractionOrchestrator instance
    """
    if config is None:
        config = LeadExtractionConfig.from_env()

    agent = LeadExtractionOrchestrator(config)
    logger.info("Lead Extraction Agent created successfully")

    return agent


# Export main components
__all__ = [
    "LeadExtractionOrchestrator",
    "LeadExtractionConfig",
    "ExtractionRequest",
    "ExtractionResult",
    "create_lead_extraction_agent",
]
