"""
SQLAlchemy database models for Outbound Automation System.

This module defines the database schema for:
- Campaign management
- Lead tracking
- Interaction logging
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    JSON,
    Boolean,
    ForeignKey,
    Index,
    Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from typing import Optional


# ============================================
# BASE MODEL
# ============================================

Base = declarative_base()


# ============================================
# ENUMS
# ============================================

class CampaignStatus(str, enum.Enum):
    """Campaign status values."""
    DRAFT = "draft"
    EXTRACTING = "extracting"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class LeadStatus(str, enum.Enum):
    """Lead status values."""
    NEW = "new"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    CONVERTED = "converted"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    DNC = "dnc"  # Do Not Contact


class InteractionChannel(str, enum.Enum):
    """Communication channel types."""
    EMAIL = "email"
    SMS = "sms"
    CALL = "call"
    LINKEDIN = "linkedin"


class InteractionType(str, enum.Enum):
    """Interaction event types."""
    # Email events
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    SPAM_REPORTED = "spam_reported"

    # SMS events
    SMS_DELIVERED = "sms_delivered"
    SMS_FAILED = "sms_failed"
    SMS_REPLIED = "sms_replied"

    # Call events
    CALL_INITIATED = "call_initiated"
    CALL_ANSWERED = "call_answered"
    CALL_COMPLETED = "call_completed"
    CALL_FAILED = "call_failed"
    CALL_NO_ANSWER = "call_no_answer"
    VOICEMAIL = "voicemail"

    # LinkedIn events
    CONNECTION_SENT = "connection_sent"
    CONNECTION_ACCEPTED = "connection_accepted"
    MESSAGE_SENT = "message_sent"
    MESSAGE_REPLIED = "message_replied"


# ============================================
# CAMPAIGN MODEL
# ============================================

class Campaign(Base):
    """
    Campaign model for managing outbound campaigns.

    A campaign represents a complete outbound effort including:
    - Target criteria (industries, titles, etc.)
    - Lead extraction sources
    - Outreach configuration
    - Performance metrics
    """
    __tablename__ = "campaigns"

    # Primary key
    id = Column(
        String(36),
        primary_key=True,
        index=True,
        comment="Campaign UUID"
    )

    # Basic information
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Campaign name"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Campaign description"
    )
    status = Column(
        SQLEnum(CampaignStatus),
        nullable=False,
        default=CampaignStatus.DRAFT,
        index=True,
        comment="Campaign status"
    )

    # Configuration (stored as JSON)
    config = Column(
        JSON,
        nullable=False,
        default=dict,
        comment="Campaign configuration including target criteria and sources"
    )

    # Performance statistics (stored as JSON)
    stats = Column(
        JSON,
        nullable=False,
        default=dict,
        comment="Campaign performance metrics"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Campaign start timestamp"
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Campaign completion timestamp"
    )

    # Relationships
    leads = relationship(
        "Lead",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    interactions = relationship(
        "Interaction",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_campaign_status_created", "status", "created_at"),
        Index("idx_campaign_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name}, status={self.status})>"


# ============================================
# LEAD MODEL
# ============================================

class Lead(Base):
    """
    Lead model for tracking individual contacts.

    Stores all lead information including:
    - Contact details (name, email, phone)
    - Company information
    - Lead quality score
    - Status and source
    """
    __tablename__ = "leads"

    # Primary key
    id = Column(
        String(36),
        primary_key=True,
        index=True,
        comment="Lead UUID"
    )

    # Foreign key
    campaign_id = Column(
        String(36),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated campaign ID"
    )

    # Contact information
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Full name"
    )
    first_name = Column(
        String(128),
        nullable=True,
        comment="First name"
    )
    last_name = Column(
        String(128),
        nullable=True,
        comment="Last name"
    )
    email = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Email address"
    )
    phone = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Phone number"
    )

    # Professional information
    title = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Job title"
    )
    company = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Company name"
    )
    company_domain = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Company website domain"
    )
    industry = Column(
        String(128),
        nullable=True,
        index=True,
        comment="Industry"
    )
    company_size = Column(
        String(50),
        nullable=True,
        comment="Company size range"
    )
    location = Column(
        String(255),
        nullable=True,
        comment="Geographic location"
    )

    # Social profiles
    linkedin_url = Column(
        String(500),
        nullable=True,
        comment="LinkedIn profile URL"
    )
    twitter_url = Column(
        String(500),
        nullable=True,
        comment="Twitter/X profile URL"
    )

    # Lead metadata
    source = Column(
        String(64),
        nullable=True,
        index=True,
        comment="Lead extraction source (apollo, linkedin, etc.)"
    )
    score = Column(
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="Lead quality score (0-100)"
    )
    status = Column(
        SQLEnum(LeadStatus),
        nullable=False,
        default=LeadStatus.NEW,
        index=True,
        comment="Lead status"
    )

    # Additional data (stored as JSON)
    enrichment_data = Column(
        JSON,
        nullable=True,
        comment="Additional enrichment data from various sources"
    )

    # Email verification
    email_verified = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether email has been verified"
    )
    email_verification_date = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Email verification timestamp"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )
    last_contacted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last contact attempt timestamp"
    )

    # Relationships
    campaign = relationship("Campaign", back_populates="leads")
    interactions = relationship(
        "Interaction",
        back_populates="lead",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_lead_campaign_status", "campaign_id", "status"),
        Index("idx_lead_campaign_score", "campaign_id", "score"),
        Index("idx_lead_email_unique", "email", "campaign_id", unique=True),
        Index("idx_lead_source", "source"),
        Index("idx_lead_company", "company"),
        Index("idx_lead_title", "title"),
    )

    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, name={self.name}, email={self.email}, score={self.score})>"


# ============================================
# INTERACTION MODEL
# ============================================

class Interaction(Base):
    """
    Interaction model for logging all outreach activities.

    Tracks every interaction with leads including:
    - Email sends, opens, clicks
    - SMS messages and replies
    - Phone call attempts and outcomes
    - LinkedIn activities
    """
    __tablename__ = "interactions"

    # Primary key
    id = Column(
        String(36),
        primary_key=True,
        index=True,
        comment="Interaction UUID"
    )

    # Foreign keys
    lead_id = Column(
        String(36),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated lead ID"
    )
    campaign_id = Column(
        String(36),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated campaign ID"
    )

    # Interaction details
    channel = Column(
        SQLEnum(InteractionChannel),
        nullable=False,
        index=True,
        comment="Communication channel"
    )
    type = Column(
        SQLEnum(InteractionType),
        nullable=False,
        index=True,
        comment="Interaction event type"
    )

    # Message content
    subject = Column(
        String(500),
        nullable=True,
        comment="Email subject or message title"
    )
    message = Column(
        Text,
        nullable=True,
        comment="Message content"
    )

    # External IDs
    external_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="External service message ID (SendGrid, Twilio, etc.)"
    )

    # Status and metadata
    status = Column(
        String(64),
        nullable=True,
        index=True,
        comment="Status of the interaction"
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if interaction failed"
    )

    # Additional data (stored as JSON)
    data = Column(
        JSON,
        nullable=True,
        comment="Additional interaction data and webhook payloads"
    )

    # Timing
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Interaction timestamp"
    )
    scheduled_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Scheduled send time (for queued messages)"
    )

    # Relationships
    lead = relationship("Lead", back_populates="interactions")
    campaign = relationship("Campaign", back_populates="interactions")

    # Indexes
    __table_args__ = (
        Index("idx_interaction_lead_channel", "lead_id", "channel"),
        Index("idx_interaction_campaign_type", "campaign_id", "type"),
        Index("idx_interaction_timestamp", "timestamp"),
        Index("idx_interaction_external", "external_id"),
        Index("idx_interaction_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Interaction(id={self.id}, channel={self.channel}, type={self.type}, lead_id={self.lead_id})>"


# ============================================
# DO NOT CONTACT LIST MODEL
# ============================================

class DoNotContact(Base):
    """
    Do Not Contact (DNC) list for compliance.

    Maintains a list of contacts who have opted out or should not be contacted.
    """
    __tablename__ = "do_not_contact"

    # Primary key
    id = Column(
        String(36),
        primary_key=True,
        index=True,
        comment="DNC entry UUID"
    )

    # Contact identifiers
    email = Column(
        String(255),
        nullable=True,
        index=True,
        unique=True,
        comment="Email address to block"
    )
    phone = Column(
        String(50),
        nullable=True,
        index=True,
        unique=True,
        comment="Phone number to block"
    )

    # Reason for DNC
    reason = Column(
        String(128),
        nullable=True,
        comment="Reason for adding to DNC list"
    )
    source = Column(
        String(64),
        nullable=True,
        comment="Source of DNC request (unsubscribe, manual, etc.)"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Date added to DNC list"
    )

    # Indexes
    __table_args__ = (
        Index("idx_dnc_email", "email"),
        Index("idx_dnc_phone", "phone"),
    )

    def __repr__(self) -> str:
        return f"<DoNotContact(email={self.email}, phone={self.phone}, reason={self.reason})>"


# ============================================
# UTILITY FUNCTIONS
# ============================================

def create_tables(engine):
    """
    Create all database tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(bind=engine)


def drop_tables(engine):
    """
    Drop all database tables.

    WARNING: This will delete all data!

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.drop_all(bind=engine)


# ============================================
# EXPORTS
# ============================================

__all__ = [
    "Base",
    "Campaign",
    "Lead",
    "Interaction",
    "DoNotContact",
    "CampaignStatus",
    "LeadStatus",
    "InteractionChannel",
    "InteractionType",
    "create_tables",
    "drop_tables",
]
