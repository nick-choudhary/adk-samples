"""
Configuration management for Outbound Automation System.

This module uses Pydantic Settings to manage application configuration
from environment variables and .env files.
"""

from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ============================================
    # GOOGLE CLOUD CONFIGURATION
    # ============================================

    GOOGLE_CLOUD_PROJECT: str = Field(
        default="",
        description="Google Cloud project ID"
    )
    GOOGLE_CLOUD_LOCATION: str = Field(
        default="us-central1",
        description="Google Cloud region"
    )
    GOOGLE_GENAI_USE_VERTEXAI: bool = Field(
        default=True,
        description="Use Vertex AI for Gemini models"
    )

    # ============================================
    # DATABASE CONFIGURATION
    # ============================================

    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/outbound_db",
        description="PostgreSQL connection string"
    )

    # BigQuery configuration
    BQ_DATASET: str = Field(
        default="outbound_analytics",
        description="BigQuery dataset name"
    )
    BQ_LEADS_TABLE: str = Field(
        default="extracted_leads",
        description="BigQuery leads table"
    )
    BQ_INTERACTIONS_TABLE: str = Field(
        default="interactions",
        description="BigQuery interactions table"
    )

    # Firestore configuration
    FIRESTORE_COLLECTION: str = Field(
        default="outbound_sessions",
        description="Firestore collection for sessions"
    )

    # Redis configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )

    # ============================================
    # AUTHENTICATION
    # ============================================

    JWT_SECRET: str = Field(
        default="change-this-secret-in-production",
        description="JWT secret key for token signing"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    JWT_EXPIRATION_MINUTES: int = Field(
        default=60,
        description="JWT token expiration in minutes"
    )

    # Firebase (optional)
    FIREBASE_PROJECT_ID: Optional[str] = Field(
        default=None,
        description="Firebase project ID"
    )
    FIREBASE_WEB_API_KEY: Optional[str] = Field(
        default=None,
        description="Firebase web API key"
    )

    # ============================================
    # EMAIL SERVICE (SendGrid)
    # ============================================

    SENDGRID_API_KEY: Optional[str] = Field(
        default=None,
        description="SendGrid API key"
    )
    FROM_EMAIL: str = Field(
        default="noreply@example.com",
        description="Default sender email address"
    )
    FROM_NAME: str = Field(
        default="Outbound System",
        description="Default sender name"
    )
    SENDGRID_WEBHOOK_SECRET: Optional[str] = Field(
        default=None,
        description="SendGrid webhook verification secret"
    )

    # ============================================
    # SMS & VOICE (Twilio)
    # ============================================

    TWILIO_ACCOUNT_SID: Optional[str] = Field(
        default=None,
        description="Twilio account SID"
    )
    TWILIO_AUTH_TOKEN: Optional[str] = Field(
        default=None,
        description="Twilio auth token"
    )
    TWILIO_PHONE_NUMBER: Optional[str] = Field(
        default=None,
        description="Twilio phone number for outbound calls/SMS"
    )
    TWILIO_WEBHOOK_BASE_URL: Optional[str] = Field(
        default=None,
        description="Base URL for Twilio webhooks"
    )

    # ============================================
    # LEAD DATABASE APIS
    # ============================================

    APOLLO_API_KEY: Optional[str] = Field(
        default=None,
        description="Apollo.io API key"
    )
    ZOOMINFO_USERNAME: Optional[str] = Field(
        default=None,
        description="ZoomInfo username"
    )
    ZOOMINFO_PASSWORD: Optional[str] = Field(
        default=None,
        description="ZoomInfo password"
    )
    LINKEDIN_ACCESS_TOKEN: Optional[str] = Field(
        default=None,
        description="LinkedIn API access token"
    )

    # ============================================
    # DATA ENRICHMENT APIS
    # ============================================

    HUNTER_API_KEY: Optional[str] = Field(
        default=None,
        description="Hunter.io API key for email finding"
    )
    CLEARBIT_API_KEY: Optional[str] = Field(
        default=None,
        description="Clearbit API key for company enrichment"
    )
    NEVERBOUNCE_API_KEY: Optional[str] = Field(
        default=None,
        description="NeverBounce API key for email verification"
    )

    # ============================================
    # WEB SCRAPING
    # ============================================

    SERPAPI_KEY: Optional[str] = Field(
        default=None,
        description="SerpAPI key for Google Search scraping"
    )
    PROXY_URL: Optional[str] = Field(
        default=None,
        description="Proxy service URL for web scraping"
    )

    # ============================================
    # SOCIAL MEDIA APIS
    # ============================================

    TWITTER_BEARER_TOKEN: Optional[str] = Field(
        default=None,
        description="Twitter/X API bearer token"
    )

    # ============================================
    # CLOUD TASKS (Job Queue)
    # ============================================

    CLOUD_TASKS_PROJECT: Optional[str] = Field(
        default=None,
        description="Google Cloud project for Cloud Tasks"
    )
    CLOUD_TASKS_LOCATION: str = Field(
        default="us-central1",
        description="Cloud Tasks queue location"
    )
    LEAD_EXTRACTION_QUEUE: str = Field(
        default="lead-extraction-queue",
        description="Queue name for lead extraction jobs"
    )
    OUTREACH_QUEUE: str = Field(
        default="outreach-queue",
        description="Queue name for outreach jobs"
    )
    WORKER_SERVICE_URL: Optional[str] = Field(
        default=None,
        description="Worker service URL for Cloud Tasks"
    )

    # ============================================
    # APPLICATION SETTINGS
    # ============================================

    ENVIRONMENT: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    API_BASE_URL: str = Field(
        default="http://localhost:8080",
        description="API base URL"
    )
    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        description="Frontend application URL"
    )
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # ============================================
    # SECURITY & COMPLIANCE
    # ============================================

    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="API rate limit per minute"
    )
    RATE_LIMIT_PER_HOUR: int = Field(
        default=1000,
        description="API rate limit per hour"
    )
    SESSION_TIMEOUT: int = Field(
        default=60,
        description="Session timeout in minutes"
    )
    MAX_UPLOAD_SIZE: int = Field(
        default=10,
        description="Max file upload size in MB"
    )
    DNC_LIST_TABLE: str = Field(
        default="do_not_contact",
        description="Do Not Contact list table name"
    )

    # ============================================
    # MONITORING & LOGGING
    # ============================================

    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    SENTRY_DSN: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    ENABLE_CLOUD_LOGGING: bool = Field(
        default=False,
        description="Enable Google Cloud Logging"
    )

    # ============================================
    # FEATURE FLAGS
    # ============================================

    ENABLE_LINKEDIN_EXTRACTION: bool = Field(default=True)
    ENABLE_VOICE_CALLS: bool = Field(default=True)
    ENABLE_SMS: bool = Field(default=True)
    ENABLE_EMAIL: bool = Field(default=True)
    ENABLE_WEB_SCRAPING: bool = Field(default=False)

    # ============================================
    # AGENT CONFIGURATION
    # ============================================

    DEFAULT_MODEL: str = Field(
        default="gemini-2.0-flash",
        description="Default AI model for agents"
    )
    PREMIUM_MODEL: str = Field(
        default="gemini-2.5-pro",
        description="Premium AI model for complex tasks"
    )
    CREATIVE_TEMPERATURE: float = Field(
        default=1.0,
        description="Model temperature for creative tasks"
    )
    ANALYTICAL_TEMPERATURE: float = Field(
        default=0.2,
        description="Model temperature for analytical tasks"
    )

    # Lead scoring weights (should sum to ~100)
    TITLE_WEIGHT: int = Field(default=30)
    COMPANY_SIZE_WEIGHT: int = Field(default=25)
    INDUSTRY_WEIGHT: int = Field(default=20)
    CONTACT_COMPLETENESS_WEIGHT: int = Field(default=15)

    MIN_LEAD_SCORE: int = Field(
        default=70,
        description="Minimum lead score to contact"
    )

    # ============================================
    # CAMPAIGN DEFAULTS
    # ============================================

    DEFAULT_TARGET_COUNT: int = Field(default=500)
    DEFAULT_MIN_SCORE: int = Field(default=70)
    MAX_OUTREACH_PER_DAY: int = Field(default=1000)

    # Email sequence timing (days)
    INITIAL_EMAIL_DELAY: int = Field(default=0)
    FOLLOW_UP_1_DELAY: int = Field(default=3)
    FOLLOW_UP_2_DELAY: int = Field(default=7)
    CALL_DELAY: int = Field(default=14)

    # ============================================
    # DEVELOPMENT TOOLS
    # ============================================

    DEBUG: bool = Field(default=False)
    RELOAD: bool = Field(default=False)
    DB_ECHO: bool = Field(default=False)

    # ============================================
    # VALIDATORS
    # ============================================

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is valid."""
        valid_envs = ["development", "staging", "production"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {valid_envs}")
        return v_lower

    # ============================================
    # HELPER METHODS
    # ============================================

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    @property
    def cloud_tasks_project(self) -> str:
        """Get Cloud Tasks project (defaults to main project)."""
        return self.CLOUD_TASKS_PROJECT or self.GOOGLE_CLOUD_PROJECT

    def get_queue_name(self, queue_type: str) -> str:
        """
        Get full queue name for Cloud Tasks.

        Args:
            queue_type: Type of queue ('extraction' or 'outreach')

        Returns:
            Full queue path
        """
        queue_map = {
            "extraction": self.LEAD_EXTRACTION_QUEUE,
            "outreach": self.OUTREACH_QUEUE
        }
        queue_name = queue_map.get(queue_type)
        if not queue_name:
            raise ValueError(f"Unknown queue type: {queue_type}")

        return (
            f"projects/{self.cloud_tasks_project}/"
            f"locations/{self.CLOUD_TASKS_LOCATION}/"
            f"queues/{queue_name}"
        )

    def validate_required_services(self) -> dict[str, bool]:
        """
        Validate that required external services are configured.

        Returns:
            Dictionary of service availability
        """
        return {
            "google_cloud": bool(self.GOOGLE_CLOUD_PROJECT),
            "database": bool(self.DATABASE_URL),
            "sendgrid": bool(self.SENDGRID_API_KEY),
            "twilio": bool(self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN),
            "cloud_tasks": bool(self.cloud_tasks_project),
        }


# ============================================
# GLOBAL SETTINGS INSTANCE
# ============================================

# Create global settings instance
settings = Settings()


# ============================================
# CONFIGURATION VALIDATION
# ============================================

def validate_configuration() -> None:
    """
    Validate critical configuration on startup.

    Raises:
        ValueError: If critical configuration is missing
    """
    errors = []

    # Check critical settings
    if not settings.GOOGLE_CLOUD_PROJECT and settings.is_production:
        errors.append("GOOGLE_CLOUD_PROJECT is required in production")

    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is required")

    if settings.JWT_SECRET == "change-this-secret-in-production" and settings.is_production:
        errors.append("JWT_SECRET must be changed in production")

    if settings.ENABLE_EMAIL and not settings.SENDGRID_API_KEY:
        errors.append("SENDGRID_API_KEY is required when email is enabled")

    if settings.ENABLE_SMS and not settings.TWILIO_ACCOUNT_SID:
        errors.append("TWILIO_ACCOUNT_SID is required when SMS is enabled")

    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)


# ============================================
# EXPORTS
# ============================================

__all__ = ["settings", "Settings", "validate_configuration"]
