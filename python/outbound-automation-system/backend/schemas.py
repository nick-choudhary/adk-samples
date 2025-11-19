"""
Pydantic schemas for API request/response validation.

This module defines data validation schemas for:
- Campaign creation and management
- Lead extraction and tracking
- Outreach requests
- Analytics and reporting
"""

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================

class CampaignStatusEnum(str, Enum):
    """Campaign status values."""
    DRAFT = "draft"
    EXTRACTING = "extracting"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class LeadStatusEnum(str, Enum):
    """Lead status values."""
    NEW = "new"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    CONVERTED = "converted"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    DNC = "dnc"


class ChannelEnum(str, Enum):
    """Communication channel types."""
    EMAIL = "email"
    SMS = "sms"
    CALL = "call"
    LINKEDIN = "linkedin"


# ============================================
# CAMPAIGN SCHEMAS
# ============================================

class CampaignCreate(BaseModel):
    """Schema for creating a new campaign."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Campaign name"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Campaign description"
    )
    target_industries: List[str] = Field(
        default_factory=list,
        description="Target industries"
    )
    target_titles: List[str] = Field(
        default_factory=list,
        description="Target job titles"
    )
    company_size: Optional[str] = Field(
        None,
        description="Target company size range (e.g., '50-200')"
    )
    geography: Optional[str] = Field(
        None,
        description="Target geographic region"
    )
    sources: List[str] = Field(
        default_factory=lambda: ["apollo"],
        description="Lead extraction sources"
    )
    min_score: int = Field(
        default=70,
        ge=0,
        le=100,
        description="Minimum lead score threshold"
    )

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, v: List[str]) -> List[str]:
        """Validate lead sources."""
        valid_sources = {
            "apollo",
            "zoominfo",
            "linkedin",
            "google_search",
            "web_scraping",
            "twitter",
            "manual"
        }
        invalid = set(v) - valid_sources
        if invalid:
            raise ValueError(f"Invalid sources: {invalid}. Valid: {valid_sources}")
        return v


class CampaignUpdate(BaseModel):
    """Schema for updating an existing campaign."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[CampaignStatusEnum] = None
    config: Optional[Dict[str, Any]] = None


class CampaignResponse(BaseModel):
    """Schema for campaign response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    status: str
    config: Dict[str, Any]
    stats: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ============================================
# LEAD SCHEMAS
# ============================================

class LeadCreate(BaseModel):
    """Schema for creating a new lead."""
    model_config = ConfigDict(str_strip_whitespace=True)

    campaign_id: str
    name: str = Field(..., min_length=1, max_length=255)
    first_name: Optional[str] = Field(None, max_length=128)
    last_name: Optional[str] = Field(None, max_length=128)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    company_domain: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=128)
    company_size: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    twitter_url: Optional[str] = Field(None, max_length=500)
    source: str = Field(..., max_length=64)
    score: int = Field(default=0, ge=0, le=100)
    enrichment_data: Optional[Dict[str, Any]] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Basic phone validation."""
        if v:
            # Remove common separators
            cleaned = v.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
            if not cleaned.replace("+", "").isdigit():
                raise ValueError("Phone must contain only digits and optional + prefix")
        return v


class LeadUpdate(BaseModel):
    """Schema for updating a lead."""
    model_config = ConfigDict(str_strip_whitespace=True)

    status: Optional[LeadStatusEnum] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    enrichment_data: Optional[Dict[str, Any]] = None


class LeadResponse(BaseModel):
    """Schema for lead response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    company_domain: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    source: str
    score: int
    status: str
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_contacted_at: Optional[datetime] = None


# ============================================
# LEAD EXTRACTION SCHEMAS
# ============================================

class LeadExtractionFilters(BaseModel):
    """Filters for lead extraction."""
    model_config = ConfigDict(str_strip_whitespace=True)

    industries: Optional[List[str]] = None
    titles: Optional[List[str]] = None
    company_size: Optional[str] = None
    locations: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


class LeadExtractionRequest(BaseModel):
    """Schema for lead extraction request."""
    model_config = ConfigDict(str_strip_whitespace=True)

    campaign_id: str = Field(..., description="Campaign ID")
    target_count: int = Field(
        default=500,
        ge=1,
        le=10000,
        description="Target number of leads to extract"
    )
    sources: List[str] = Field(
        default_factory=lambda: ["apollo"],
        description="Lead extraction sources"
    )
    filters: Optional[LeadExtractionFilters] = Field(
        None,
        description="Extraction filters"
    )

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, v: List[str]) -> List[str]:
        """Validate lead sources."""
        valid_sources = {
            "apollo",
            "zoominfo",
            "linkedin",
            "google_search",
            "web_scraping",
            "twitter"
        }
        invalid = set(v) - valid_sources
        if invalid:
            raise ValueError(f"Invalid sources: {invalid}")
        return v


# ============================================
# OUTREACH SCHEMAS
# ============================================

class OutreachScheduleStep(BaseModel):
    """Single step in outreach sequence."""
    model_config = ConfigDict(str_strip_whitespace=True)

    day: int = Field(..., ge=0, description="Day in sequence (0-based)")
    channel: ChannelEnum = Field(..., description="Communication channel")
    template: Optional[str] = Field(None, description="Template name")
    action: Optional[str] = Field(None, description="Action to perform")
    min_score: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Minimum lead score for this step"
    )


class OutreachSchedule(BaseModel):
    """Outreach sequence schedule."""
    sequence: List[OutreachScheduleStep] = Field(
        ...,
        min_length=1,
        description="Sequence of outreach steps"
    )


class OutreachRequest(BaseModel):
    """Schema for starting outreach campaign."""
    model_config = ConfigDict(str_strip_whitespace=True)

    campaign_id: str = Field(..., description="Campaign ID")
    channels: List[ChannelEnum] = Field(
        default_factory=lambda: [ChannelEnum.EMAIL],
        description="Communication channels to use"
    )
    schedule: Optional[OutreachSchedule] = Field(
        None,
        description="Outreach sequence schedule"
    )
    send_immediately: bool = Field(
        default=False,
        description="Send immediately vs. queue for optimal timing"
    )


# ============================================
# INTERACTION SCHEMAS
# ============================================

class InteractionCreate(BaseModel):
    """Schema for creating an interaction."""
    model_config = ConfigDict(str_strip_whitespace=True)

    lead_id: str
    campaign_id: str
    channel: ChannelEnum
    type: str
    subject: Optional[str] = Field(None, max_length=500)
    message: Optional[str] = None
    external_id: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=64)
    data: Optional[Dict[str, Any]] = None


class InteractionResponse(BaseModel):
    """Schema for interaction response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    lead_id: str
    campaign_id: str
    channel: str
    type: str
    subject: Optional[str] = None
    status: Optional[str] = None
    timestamp: datetime


# ============================================
# JOB SCHEMAS
# ============================================

class JobResponse(BaseModel):
    """Schema for job submission response."""
    job_id: str = Field(..., description="Job ID for tracking")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Status message")


class JobStatusResponse(BaseModel):
    """Schema for job status response."""
    job_id: str
    status: str = Field(
        ...,
        description="Job status: pending, running, completed, failed"
    )
    progress: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Progress percentage"
    )
    message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


# ============================================
# ANALYTICS SCHEMAS
# ============================================

class CampaignStats(BaseModel):
    """Schema for campaign statistics."""
    total_leads: int = Field(default=0, description="Total leads extracted")
    contacted: int = Field(default=0, description="Leads contacted")
    responded: int = Field(default=0, description="Leads who responded")
    converted: int = Field(default=0, description="Leads converted")
    email_open_rate: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Email open rate percentage"
    )
    email_click_rate: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Email click rate percentage"
    )
    response_rate: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Response rate percentage"
    )
    conversion_rate: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Conversion rate percentage"
    )


class ChannelStats(BaseModel):
    """Statistics for a specific channel."""
    channel: str
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    responded: int = 0
    bounced: int = 0
    unsubscribed: int = 0


class DateRangeStats(BaseModel):
    """Statistics over a date range."""
    start_date: datetime
    end_date: datetime
    total_interactions: int
    channels: List[ChannelStats]


# ============================================
# AUTHENTICATION SCHEMAS
# ============================================

class UserLogin(BaseModel):
    """Schema for user login."""
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ============================================
# ERROR SCHEMAS
# ============================================

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")


class ValidationErrorDetail(BaseModel):
    """Schema for validation error details."""
    loc: List[str] = Field(..., description="Error location")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(BaseModel):
    """Schema for validation error response."""
    detail: List[ValidationErrorDetail] = Field(
        ...,
        description="Validation errors"
    )


# ============================================
# UTILITY SCHEMAS
# ============================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of records to return"
    )


class BulkOperationResult(BaseModel):
    """Result of a bulk operation."""
    total: int = Field(..., description="Total records processed")
    successful: int = Field(..., description="Successfully processed")
    failed: int = Field(..., description="Failed to process")
    errors: List[str] = Field(default_factory=list, description="Error messages")


# ============================================
# EXPORTS
# ============================================

__all__ = [
    # Enums
    "CampaignStatusEnum",
    "LeadStatusEnum",
    "ChannelEnum",
    # Campaign schemas
    "CampaignCreate",
    "CampaignUpdate",
    "CampaignResponse",
    # Lead schemas
    "LeadCreate",
    "LeadUpdate",
    "LeadResponse",
    # Lead extraction schemas
    "LeadExtractionFilters",
    "LeadExtractionRequest",
    # Outreach schemas
    "OutreachScheduleStep",
    "OutreachSchedule",
    "OutreachRequest",
    # Interaction schemas
    "InteractionCreate",
    "InteractionResponse",
    # Job schemas
    "JobResponse",
    "JobStatusResponse",
    # Analytics schemas
    "CampaignStats",
    "ChannelStats",
    "DateRangeStats",
    # Auth schemas
    "UserLogin",
    "TokenResponse",
    "UserCreate",
    # Error schemas
    "ErrorResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    # Utility schemas
    "PaginationParams",
    "BulkOperationResult",
]
