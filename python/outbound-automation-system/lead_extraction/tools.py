"""
Lead Extraction Tools for Outbound Automation System

This module provides comprehensive tools for extracting, enriching, and scoring leads
from multiple sources including Apollo.io, ZoomInfo, LinkedIn, Google Search, web scraping,
social media, and file imports.

All tools include:
- Production-ready error handling
- Rate limiting and retry logic
- Response validation
- Comprehensive logging
"""

import asyncio
import hashlib
import logging
import re
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import pandas as pd
import phonenumbers
import requests
from bs4 import BeautifulSoup
from google.adk.toolkits import Tool
from pydantic import BaseModel, Field, HttpUrl, EmailStr, validator
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class LeadSource(str, Enum):
    """Enumeration of lead sources"""
    APOLLO = "apollo"
    ZOOMINFO = "zoominfo"
    LINKEDIN = "linkedin"
    GOOGLE_SEARCH = "google_search"
    WEB_SCRAPING = "web_scraping"
    TWITTER = "twitter"
    FILE_IMPORT = "file_import"
    MANUAL = "manual"


class Lead(BaseModel):
    """Lead data model"""
    # Contact Information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    twitter_handle: Optional[str] = None

    # Professional Information
    title: Optional[str] = None
    seniority_level: Optional[str] = None
    department: Optional[str] = None

    # Company Information
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_website: Optional[HttpUrl] = None
    company_industry: Optional[str] = None
    company_size: Optional[str] = None
    company_revenue: Optional[str] = None
    company_location: Optional[str] = None

    # Metadata
    source: LeadSource
    extraction_date: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(default=0.0, ge=0.0, le=100.0)
    lead_score: float = Field(default=0.0, ge=0.0, le=100.0)
    enrichment_status: str = "pending"

    # Additional Data
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    @validator('phone')
    def validate_phone(cls, v):
        """Validate and format phone number"""
        if v:
            try:
                parsed = phonenumbers.parse(v, "US")
                if phonenumbers.is_valid_number(parsed):
                    return phonenumbers.format_number(
                        parsed, phonenumbers.PhoneNumberFormat.E164
                    )
            except Exception:
                pass
        return v

    def get_full_name(self) -> str:
        """Get full name"""
        parts = [self.first_name, self.last_name]
        return " ".join(filter(None, parts))

    def get_unique_id(self) -> str:
        """Generate unique ID for deduplication"""
        # Create hash from email or combination of name + company
        if self.email:
            return hashlib.md5(self.email.lower().encode()).hexdigest()

        unique_string = f"{self.first_name or ''}{self.last_name or ''}{self.company_domain or self.company_name or ''}"
        return hashlib.md5(unique_string.lower().encode()).hexdigest()


class SearchCriteria(BaseModel):
    """Search criteria for lead extraction"""
    keywords: Optional[List[str]] = None
    titles: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    company_sizes: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    seniority_levels: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    revenue_range: Optional[Tuple[int, int]] = None
    employee_range: Optional[Tuple[int, int]] = None
    max_results: int = 100


# ============================================================================
# Rate Limiter
# ============================================================================

class RateLimiter:
    """Rate limiter with token bucket algorithm"""

    def __init__(self, max_requests: int, time_window: int = 60):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Acquire permission to make request (async)"""
        async with self._lock:
            now = time.time()
            # Remove requests outside time window
            self.requests = [r for r in self.requests if now - r < self.time_window]

            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest = self.requests[0]
                wait_time = self.time_window - (now - oldest)
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    # Retry
                    return await self.acquire()

            self.requests.append(now)

    def acquire_sync(self):
        """Acquire permission to make request (sync)"""
        now = time.time()
        # Remove requests outside time window
        self.requests = [r for r in self.requests if now - r < self.time_window]

        if len(self.requests) >= self.max_requests:
            # Calculate wait time
            oldest = self.requests[0]
            wait_time = self.time_window - (now - oldest)
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                # Retry
                return self.acquire_sync()

        self.requests.append(now)


# ============================================================================
# API Client Base Class
# ============================================================================

class APIClient:
    """Base class for API clients with retry logic"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        rate_limiter: Optional[RateLimiter] = None,
        max_retries: int = 3,
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limiter = rate_limiter or RateLimiter(max_requests=100)
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        url = urljoin(self.base_url, endpoint)

        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                self.rate_limiter.acquire_sync()

                # Make request
                response = self.session.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = int(e.response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                elif e.response.status_code >= 500 and attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Server error, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"HTTP error: {e}")
                    raise
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    raise

        raise Exception(f"Failed to make request after {self.max_retries} attempts")


# ============================================================================
# Apollo.io Client
# ============================================================================

class ApolloClient(APIClient):
    """Apollo.io API client for B2B contact database"""

    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="https://api.apollo.io/v1/",
            rate_limiter=RateLimiter(max_requests=200, time_window=60)
        )

    def search_people(self, criteria: SearchCriteria) -> List[Lead]:
        """Search for people matching criteria"""
        payload = {
            "page": 1,
            "per_page": min(criteria.max_results, 100),
            "person_titles": criteria.titles,
            "person_locations": criteria.locations,
            "person_seniorities": criteria.seniority_levels,
            "organization_industry_tag_ids": criteria.industries,
            "organization_num_employees_ranges": criteria.company_sizes,
            "q_keywords": " ".join(criteria.keywords) if criteria.keywords else None,
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            data = self._make_request("POST", "mixed_people/search", json=payload)

            leads = []
            for person in data.get("people", []):
                lead = self._parse_apollo_person(person)
                leads.append(lead)

            logger.info(f"Apollo.io returned {len(leads)} leads")
            return leads

        except Exception as e:
            logger.error(f"Apollo.io search failed: {e}")
            return []

    def _parse_apollo_person(self, person: Dict[str, Any]) -> Lead:
        """Parse Apollo person data into Lead model"""
        organization = person.get("organization", {}) or {}

        return Lead(
            first_name=person.get("first_name"),
            last_name=person.get("last_name"),
            email=person.get("email"),
            phone=person.get("phone_numbers", [{}])[0].get("raw_number") if person.get("phone_numbers") else None,
            linkedin_url=person.get("linkedin_url"),
            twitter_handle=person.get("twitter_url"),
            title=person.get("title"),
            seniority_level=person.get("seniority"),
            department=person.get("departments", [None])[0],
            company_name=organization.get("name"),
            company_domain=organization.get("primary_domain"),
            company_website=organization.get("website_url"),
            company_industry=organization.get("industry"),
            company_size=organization.get("estimated_num_employees"),
            company_revenue=organization.get("annual_revenue"),
            company_location=organization.get("city"),
            source=LeadSource.APOLLO,
            confidence_score=person.get("email_confidence_score", 0) * 100,
        )


# ============================================================================
# ZoomInfo Client
# ============================================================================

class ZoomInfoClient(APIClient):
    """ZoomInfo API client for enterprise contact data"""

    def __init__(self, api_key: str, username: str, password: str):
        super().__init__(
            api_key=api_key,
            base_url="https://api.zoominfo.com/",
            rate_limiter=RateLimiter(max_requests=100, time_window=60)
        )
        self.username = username
        self.password = password
        self._authenticate()

    def _authenticate(self):
        """Authenticate and get JWT token"""
        try:
            response = self._make_request(
                "POST",
                "authenticate",
                json={"username": self.username, "password": self.password}
            )
            token = response.get("jwt")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            logger.info("ZoomInfo authentication successful")
        except Exception as e:
            logger.error(f"ZoomInfo authentication failed: {e}")
            raise

    def search_contacts(self, criteria: SearchCriteria) -> List[Lead]:
        """Search for contacts matching criteria"""
        payload = {
            "managementLevel": criteria.seniority_levels,
            "jobTitle": criteria.titles,
            "companyIndustry": criteria.industries,
            "companySize": criteria.company_sizes,
            "location": criteria.locations,
            "maxResults": min(criteria.max_results, 100),
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            data = self._make_request("POST", "search/contact", json=payload)

            leads = []
            for contact in data.get("data", []):
                lead = self._parse_zoominfo_contact(contact)
                leads.append(lead)

            logger.info(f"ZoomInfo returned {len(leads)} leads")
            return leads

        except Exception as e:
            logger.error(f"ZoomInfo search failed: {e}")
            return []

    def _parse_zoominfo_contact(self, contact: Dict[str, Any]) -> Lead:
        """Parse ZoomInfo contact data into Lead model"""
        return Lead(
            first_name=contact.get("firstName"),
            last_name=contact.get("lastName"),
            email=contact.get("email"),
            phone=contact.get("directPhoneNumber"),
            linkedin_url=contact.get("linkedInUrl"),
            title=contact.get("jobTitle"),
            seniority_level=contact.get("managementLevel"),
            department=contact.get("jobFunction"),
            company_name=contact.get("companyName"),
            company_domain=contact.get("companyDomain"),
            company_website=contact.get("companyWebsite"),
            company_industry=contact.get("companyIndustry"),
            company_size=str(contact.get("companyEmployeeCount")),
            company_revenue=str(contact.get("companyRevenue")),
            company_location=contact.get("companyCity"),
            source=LeadSource.ZOOMINFO,
            confidence_score=85.0,  # ZoomInfo has high quality data
        )


# ============================================================================
# LinkedIn Sales Navigator
# ============================================================================

class LinkedInClient:
    """LinkedIn Sales Navigator client"""

    def __init__(self, session_cookie: str):
        """
        Initialize LinkedIn client

        Args:
            session_cookie: LinkedIn li_at session cookie
        """
        self.session = requests.Session()
        self.session.cookies.set("li_at", session_cookie)
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        })
        self.rate_limiter = RateLimiter(max_requests=30, time_window=60)

    def search_people(self, criteria: SearchCriteria) -> List[Lead]:
        """Search LinkedIn Sales Navigator for people"""
        # Note: This is a simplified implementation
        # Production would use official LinkedIn Marketing API or Sales Navigator API

        search_url = "https://www.linkedin.com/sales-api/salesApiPeopleSearch"

        params = {
            "q": "search",
            "start": 0,
            "count": min(criteria.max_results, 25),
        }

        # Add filters
        if criteria.titles:
            params["titles"] = ",".join(criteria.titles)
        if criteria.locations:
            params["geoUrn"] = ",".join(criteria.locations)
        if criteria.industries:
            params["industries"] = ",".join(criteria.industries)

        try:
            self.rate_limiter.acquire_sync()
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            leads = []
            for element in data.get("elements", []):
                lead = self._parse_linkedin_profile(element)
                leads.append(lead)

            logger.info(f"LinkedIn returned {len(leads)} leads")
            return leads

        except Exception as e:
            logger.error(f"LinkedIn search failed: {e}")
            return []

    def _parse_linkedin_profile(self, profile: Dict[str, Any]) -> Lead:
        """Parse LinkedIn profile data into Lead model"""
        current_position = profile.get("currentPositions", [{}])[0] if profile.get("currentPositions") else {}
        company = current_position.get("companyName")

        return Lead(
            first_name=profile.get("firstName"),
            last_name=profile.get("lastName"),
            linkedin_url=f"https://www.linkedin.com/in/{profile.get('publicIdentifier', '')}",
            title=current_position.get("title"),
            company_name=company,
            company_location=current_position.get("location"),
            source=LeadSource.LINKEDIN,
            confidence_score=90.0,  # LinkedIn has verified data
        )


# ============================================================================
# Google Search & Web Scraping
# ============================================================================

class GoogleSearchClient:
    """Google Search client using SerpAPI"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
        self.rate_limiter = RateLimiter(max_requests=100, time_window=60)

    def search_businesses(
        self,
        query: str,
        location: str = "United States",
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Search Google for businesses"""
        results = []

        try:
            self.rate_limiter.acquire_sync()

            params = {
                "q": query,
                "location": location,
                "api_key": self.api_key,
                "num": min(max_results, 100),
                "engine": "google",
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            for result in data.get("organic_results", []):
                results.append({
                    "title": result.get("title"),
                    "url": result.get("link"),
                    "snippet": result.get("snippet"),
                })

            logger.info(f"Google Search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Google Search failed: {e}")
            return []


class WebScraper:
    """Web scraper for extracting contact information from websites"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.rate_limiter = RateLimiter(max_requests=60, time_window=60)

    def _get_driver(self) -> webdriver.Chrome:
        """Initialize Chrome WebDriver"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        return webdriver.Chrome(options=options)

    def scrape_website(self, url: str) -> Dict[str, Any]:
        """Scrape contact information from a website"""
        self.rate_limiter.acquire_sync()

        driver = None
        try:
            driver = self._get_driver()
            driver.get(url)

            # Wait for page load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Get page source
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Extract data
            data = {
                "url": url,
                "title": soup.title.string if soup.title else None,
                "emails": self._extract_emails(soup),
                "phones": self._extract_phones(soup),
                "social_links": self._extract_social_links(soup),
                "text": soup.get_text(separator=" ", strip=True)[:1000],
            }

            return data

        except Exception as e:
            logger.error(f"Web scraping failed for {url}: {e}")
            return {"url": url, "error": str(e)}
        finally:
            if driver:
                driver.quit()

    def _extract_emails(self, soup: BeautifulSoup) -> List[str]:
        """Extract email addresses from page"""
        text = soup.get_text()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)

        # Filter out common non-contact emails
        filtered = [
            e for e in emails
            if not any(x in e.lower() for x in ["example", "test", "noreply", "no-reply"])
        ]

        return list(set(filtered))

    def _extract_phones(self, soup: BeautifulSoup) -> List[str]:
        """Extract phone numbers from page"""
        text = soup.get_text()

        # Multiple phone patterns
        patterns = [
            r'\+?1?\s*\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})',
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        ]

        phones = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if isinstance(matches[0], tuple):
                phones.extend([f"({m[0]}) {m[1]}-{m[2]}" for m in matches])
            else:
                phones.extend(matches)

        return list(set(phones))

    def _extract_social_links(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract social media links"""
        social_links = {}

        for link in soup.find_all("a", href=True):
            href = link["href"]

            if "linkedin.com/in/" in href or "linkedin.com/company/" in href:
                social_links["linkedin"] = href
            elif "twitter.com/" in href or "x.com/" in href:
                social_links["twitter"] = href
            elif "facebook.com/" in href:
                social_links["facebook"] = href

        return social_links


# ============================================================================
# Twitter/X Client
# ============================================================================

class TwitterClient:
    """Twitter/X client for lead extraction"""

    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.base_url = "https://api.twitter.com/2/"
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {bearer_token}"})
        self.rate_limiter = RateLimiter(max_requests=450, time_window=900)  # 15 min window

    def search_users(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search Twitter users"""
        try:
            self.rate_limiter.acquire_sync()

            params = {
                "query": query,
                "max_results": min(max_results, 100),
                "user.fields": "description,location,url,verified,public_metrics"
            }

            response = self.session.get(
                f"{self.base_url}users/search",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            users = data.get("data", [])
            logger.info(f"Twitter returned {len(users)} users")
            return users

        except Exception as e:
            logger.error(f"Twitter search failed: {e}")
            return []


# ============================================================================
# Data Enrichment Tools
# ============================================================================

class HunterIOClient(APIClient):
    """Hunter.io client for email finding and verification"""

    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="https://api.hunter.io/v2/",
            rate_limiter=RateLimiter(max_requests=100, time_window=60)
        )

    def find_email(self, first_name: str, last_name: str, domain: str) -> Optional[str]:
        """Find email address for a person"""
        try:
            params = {
                "first_name": first_name,
                "last_name": last_name,
                "domain": domain,
                "api_key": self.api_key,
            }

            data = self._make_request("GET", "email-finder", params=params)

            email_data = data.get("data", {})
            email = email_data.get("email")
            confidence = email_data.get("score", 0)

            if email and confidence > 50:
                logger.info(f"Found email: {email} (confidence: {confidence}%)")
                return email

            return None

        except Exception as e:
            logger.error(f"Hunter.io email finding failed: {e}")
            return None

    def verify_email(self, email: str) -> Dict[str, Any]:
        """Verify email address"""
        try:
            params = {
                "email": email,
                "api_key": self.api_key,
            }

            data = self._make_request("GET", "email-verifier", params=params)

            result = data.get("data", {})
            return {
                "email": email,
                "valid": result.get("result") == "deliverable",
                "score": result.get("score", 0),
                "status": result.get("result"),
            }

        except Exception as e:
            logger.error(f"Hunter.io email verification failed: {e}")
            return {"email": email, "valid": False, "error": str(e)}


class ClearbitClient(APIClient):
    """Clearbit client for company enrichment"""

    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="https://company.clearbit.com/v2/",
            rate_limiter=RateLimiter(max_requests=600, time_window=60)
        )
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def enrich_company(self, domain: str) -> Dict[str, Any]:
        """Enrich company data"""
        try:
            params = {"domain": domain}
            data = self._make_request("GET", "companies/find", params=params)

            return {
                "name": data.get("name"),
                "domain": data.get("domain"),
                "description": data.get("description"),
                "industry": data.get("category", {}).get("industry"),
                "employees": data.get("metrics", {}).get("employees"),
                "revenue": data.get("metrics", {}).get("estimatedAnnualRevenue"),
                "location": data.get("geo", {}).get("city"),
                "tech_stack": data.get("tech", []),
            }

        except Exception as e:
            logger.error(f"Clearbit enrichment failed for {domain}: {e}")
            return {}


# ============================================================================
# File Import Tools
# ============================================================================

class FileImporter:
    """Import leads from CSV/Excel files"""

    @staticmethod
    def import_csv(file_path: str, mapping: Dict[str, str]) -> List[Lead]:
        """
        Import leads from CSV file

        Args:
            file_path: Path to CSV file
            mapping: Column name mapping (csv_column -> lead_field)
        """
        try:
            df = pd.read_csv(file_path)
            leads = FileImporter._parse_dataframe(df, mapping)
            logger.info(f"Imported {len(leads)} leads from CSV")
            return leads
        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            return []

    @staticmethod
    def import_excel(file_path: str, mapping: Dict[str, str], sheet_name: str = 0) -> List[Lead]:
        """
        Import leads from Excel file

        Args:
            file_path: Path to Excel file
            mapping: Column name mapping
            sheet_name: Sheet name or index
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            leads = FileImporter._parse_dataframe(df, mapping)
            logger.info(f"Imported {len(leads)} leads from Excel")
            return leads
        except Exception as e:
            logger.error(f"Excel import failed: {e}")
            return []

    @staticmethod
    def _parse_dataframe(df: pd.DataFrame, mapping: Dict[str, str]) -> List[Lead]:
        """Parse DataFrame into Lead objects"""
        leads = []

        for _, row in df.iterrows():
            try:
                # Map columns to Lead fields
                lead_data = {}
                for csv_col, lead_field in mapping.items():
                    if csv_col in row and pd.notna(row[csv_col]):
                        lead_data[lead_field] = row[csv_col]

                # Set source
                lead_data["source"] = LeadSource.FILE_IMPORT

                lead = Lead(**lead_data)
                leads.append(lead)
            except Exception as e:
                logger.warning(f"Failed to parse row: {e}")
                continue

        return leads


# ============================================================================
# Deduplication & Scoring
# ============================================================================

class LeadDeduplicator:
    """Deduplicate leads based on multiple criteria"""

    @staticmethod
    def deduplicate(leads: List[Lead]) -> List[Lead]:
        """Remove duplicate leads"""
        seen: Set[str] = set()
        unique_leads: List[Lead] = []

        for lead in leads:
            lead_id = lead.get_unique_id()

            if lead_id not in seen:
                seen.add(lead_id)
                unique_leads.append(lead)
            else:
                logger.debug(f"Duplicate lead found: {lead.email or lead.get_full_name()}")

        logger.info(f"Deduplication: {len(leads)} -> {len(unique_leads)} leads")
        return unique_leads

    @staticmethod
    def merge_leads(lead1: Lead, lead2: Lead) -> Lead:
        """Merge two leads, keeping the most complete data"""
        merged_data = {}

        for field in Lead.__fields__:
            val1 = getattr(lead1, field)
            val2 = getattr(lead2, field)

            # Keep non-null value, prefer lead with higher confidence score
            if val1 is not None and val2 is not None:
                if lead1.confidence_score >= lead2.confidence_score:
                    merged_data[field] = val1
                else:
                    merged_data[field] = val2
            else:
                merged_data[field] = val1 or val2

        return Lead(**merged_data)


class LeadScorer:
    """Score leads based on quality and fit"""

    @staticmethod
    def score_lead(lead: Lead, criteria: Optional[SearchCriteria] = None) -> float:
        """
        Calculate lead score (0-100)

        Scoring factors:
        - Data completeness (40 points)
        - Job title match (20 points)
        - Company fit (20 points)
        - Seniority level (10 points)
        - Email validity (10 points)
        """
        score = 0.0

        # Data completeness (40 points)
        completeness_fields = [
            "first_name", "last_name", "email", "phone",
            "title", "company_name", "company_domain", "linkedin_url"
        ]
        filled_fields = sum(1 for f in completeness_fields if getattr(lead, f))
        score += (filled_fields / len(completeness_fields)) * 40

        if criteria:
            # Job title match (20 points)
            if criteria.titles and lead.title:
                if any(t.lower() in lead.title.lower() for t in criteria.titles):
                    score += 20

            # Company fit (20 points)
            company_score = 0
            if criteria.industries and lead.company_industry:
                if any(i.lower() in lead.company_industry.lower() for i in criteria.industries):
                    company_score += 10

            if criteria.company_sizes and lead.company_size:
                if lead.company_size in criteria.company_sizes:
                    company_score += 10

            score += company_score

            # Seniority level (10 points)
            if criteria.seniority_levels and lead.seniority_level:
                if lead.seniority_level in criteria.seniority_levels:
                    score += 10

        # Email validity (10 points)
        if lead.email:
            # Basic email validation
            if "@" in lead.email and "." in lead.email.split("@")[1]:
                score += 10

        # Cap at 100
        return min(score, 100.0)


# ============================================================================
# ADK Tools
# ============================================================================

# Apollo.io Search Tool
apollo_search_tool = Tool(
    name="search_apollo",
    description="Search Apollo.io B2B database for leads matching criteria. Returns detailed contact and company information.",
    parameters={
        "type": "object",
        "properties": {
            "titles": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Job titles to search for (e.g., ['CEO', 'CTO', 'VP Engineering'])"
            },
            "industries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Industries to target (e.g., ['Technology', 'SaaS'])"
            },
            "company_sizes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Company size ranges (e.g., ['1-10', '11-50', '51-200'])"
            },
            "locations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Geographic locations (e.g., ['United States', 'San Francisco'])"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 100
            }
        },
        "required": []
    }
)

# ZoomInfo Search Tool
zoominfo_search_tool = Tool(
    name="search_zoominfo",
    description="Search ZoomInfo enterprise database for high-quality B2B contacts.",
    parameters={
        "type": "object",
        "properties": {
            "titles": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Job titles to search for"
            },
            "industries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Industries to target"
            },
            "seniority_levels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Seniority levels (e.g., ['C-Level', 'VP', 'Director'])"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 100
            }
        },
        "required": []
    }
)

# LinkedIn Search Tool
linkedin_search_tool = Tool(
    name="search_linkedin",
    description="Search LinkedIn Sales Navigator for professional contacts.",
    parameters={
        "type": "object",
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Search keywords"
            },
            "titles": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Job titles"
            },
            "locations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Geographic locations"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum results",
                "default": 100
            }
        },
        "required": []
    }
)

# Google Search Tool
google_search_tool = Tool(
    name="search_google",
    description="Search Google for businesses and extract contact information from websites.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (e.g., 'marketing agencies in San Francisco')"
            },
            "location": {
                "type": "string",
                "description": "Geographic location for search",
                "default": "United States"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum results to process",
                "default": 50
            }
        },
        "required": ["query"]
    }
)

# Web Scraping Tool
web_scraping_tool = Tool(
    name="scrape_website",
    description="Scrape contact information from a specific website URL.",
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Website URL to scrape"
            }
        },
        "required": ["url"]
    }
)

# Email Finding Tool
email_finder_tool = Tool(
    name="find_email",
    description="Find and verify email address for a person using Hunter.io.",
    parameters={
        "type": "object",
        "properties": {
            "first_name": {
                "type": "string",
                "description": "First name"
            },
            "last_name": {
                "type": "string",
                "description": "Last name"
            },
            "company_domain": {
                "type": "string",
                "description": "Company domain (e.g., 'google.com')"
            }
        },
        "required": ["first_name", "last_name", "company_domain"]
    }
)

# Company Enrichment Tool
company_enrichment_tool = Tool(
    name="enrich_company",
    description="Enrich company data using Clearbit.",
    parameters={
        "type": "object",
        "properties": {
            "domain": {
                "type": "string",
                "description": "Company domain"
            }
        },
        "required": ["domain"]
    }
)

# Lead Scoring Tool
lead_scoring_tool = Tool(
    name="score_leads",
    description="Calculate quality scores for leads based on completeness and fit.",
    parameters={
        "type": "object",
        "properties": {
            "leads": {
                "type": "array",
                "description": "List of leads to score"
            }
        },
        "required": ["leads"]
    }
)

# Deduplication Tool
deduplication_tool = Tool(
    name="deduplicate_leads",
    description="Remove duplicate leads from a list.",
    parameters={
        "type": "object",
        "properties": {
            "leads": {
                "type": "array",
                "description": "List of leads to deduplicate"
            }
        },
        "required": ["leads"]
    }
)

# Export all tools
__all__ = [
    # Models
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

    # Tools
    "apollo_search_tool",
    "zoominfo_search_tool",
    "linkedin_search_tool",
    "google_search_tool",
    "web_scraping_tool",
    "email_finder_tool",
    "company_enrichment_tool",
    "lead_scoring_tool",
    "deduplication_tool",
]
