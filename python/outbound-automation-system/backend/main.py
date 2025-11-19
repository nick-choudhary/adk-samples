"""
Main FastAPI application for Outbound Automation System.

This module provides the REST API for:
- Campaign management
- Lead extraction and enrichment
- Multi-channel outreach (email, SMS, calls)
- Analytics and reporting
- Webhook handling
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import logging
import os

from .config import settings
from .auth import verify_token
from . import models, schemas
from .database import engine, get_db, SessionLocal
from sqlalchemy.orm import Session

# Import background job handlers
from .jobs import (
    enqueue_lead_extraction_job,
    enqueue_outreach_job,
    get_job_status
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# APPLICATION LIFECYCLE
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup
    logger.info("Starting Outbound Automation System...")

    # Create database tables
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Initialize Redis connection
    # await init_redis()

    yield

    # Shutdown
    logger.info("Shutting down Outbound Automation System...")

# ============================================
# FASTAPI APPLICATION
# ============================================

app = FastAPI(
    title="Outbound Automation API",
    description="Complete automated outbound system with Email, SMS, and Voice calls",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ============================================
# MIDDLEWARE
# ============================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Security bearer
security = HTTPBearer()

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "outbound-automation-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Outbound Automation System API",
        "docs": "/docs",
        "health": "/health"
    }

# ============================================
# CAMPAIGN ENDPOINTS
# ============================================

@app.post("/api/campaigns", response_model=schemas.CampaignResponse)
async def create_campaign(
    campaign: schemas.CampaignCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_token)
):
    """Create a new outbound campaign"""
    import uuid

    campaign_id = str(uuid.uuid4())

    db_campaign = models.Campaign(
        id=campaign_id,
        name=campaign.name,
        status="draft",
        config={
            "target_industries": campaign.target_industries,
            "target_titles": campaign.target_titles,
            "company_size": campaign.company_size,
            "geography": campaign.geography,
            "sources": campaign.sources,
            "min_score": campaign.min_score,
            "created_by": user_id
        },
        stats={
            "total_leads": 0,
            "contacted": 0,
            "responded": 0,
            "converted": 0
        }
    )

    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)

    logger.info(f"Campaign created: {campaign_id} by user {user_id}")

    return schemas.CampaignResponse(
        id=campaign_id,
        name=campaign.name,
        status="draft",
        config=db_campaign.config,
        stats=db_campaign.stats,
        created_at=db_campaign.created_at,
        updated_at=db_campaign.updated_at
    )

@app.get("/api/campaigns/{campaign_id}", response_model=schemas.CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_token)
):
    """Get campaign details"""
    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == campaign_id
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return schemas.CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        status=campaign.status,
        config=campaign.config,
        stats=campaign.stats,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at
    )

@app.get("/api/campaigns", response_model=List[schemas.CampaignResponse])
async def list_campaigns(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_token)
):
    """List all campaigns"""
    query = db.query(models.Campaign)

    if status:
        query = query.filter(models.Campaign.status == status)

    campaigns = query.offset(skip).limit(limit).all()

    return [
        schemas.CampaignResponse(
            id=c.id,
            name=c.name,
            status=c.status,
            config=c.config,
            stats=c.stats,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in campaigns
    ]

@app.delete("/api/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_token)
):
    """Delete a campaign"""
    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == campaign_id
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Don't allow deleting active campaigns
    if campaign.status == "active":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete active campaign. Pause it first."
        )

    db.delete(campaign)
    db.commit()

    logger.info(f"Campaign deleted: {campaign_id}")

    return {"message": "Campaign deleted successfully"}

# ============================================
# LEAD EXTRACTION ENDPOINTS
# ============================================

@app.post("/api/leads/extract", response_model=schemas.JobResponse)
async def extract_leads(
    request: schemas.LeadExtractionRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_token)
):
    """Start lead extraction job (async)"""

    # Verify campaign exists
    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == request.campaign_id
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Enqueue extraction job
    job_id = await enqueue_lead_extraction_job(
        campaign_id=request.campaign_id,
        target_count=request.target_count,
        sources=request.sources,
        filters=request.filters
    )

    # Update campaign status
    campaign.status = "extracting"
    db.commit()

    logger.info(f"Lead extraction job enqueued: {job_id} for campaign {request.campaign_id}")

    return schemas.JobResponse(
        job_id=job_id,
        status="pending",
        message=f"Lead extraction started. Target: {request.target_count} leads"
    )

@app.get("/api/leads/job/{job_id}", response_model=schemas.JobStatusResponse)
async def get_extraction_job_status(
    job_id: str,
    user_id: str = Depends(verify_token)
):
    """Check status of lead extraction job"""
    job_status = await get_job_status(job_id, "extraction")

    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")

    return schemas.JobStatusResponse(**job_status)

@app.get("/api/campaigns/{campaign_id}/leads", response_model=List[schemas.LeadResponse])
async def get_campaign_leads(
    campaign_id: str,
    skip: int = 0,
    limit: int = 50,
    min_score: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_token)
):
    """Get leads for a campaign (paginated)"""
    query = db.query(models.Lead).filter(
        models.Lead.campaign_id == campaign_id
    )

    if min_score:
        query = query.filter(models.Lead.score >= min_score)

    if status:
        query = query.filter(models.Lead.status == status)

    leads = query.offset(skip).limit(limit).all()

    return [
        schemas.LeadResponse(
            id=lead.id,
            campaign_id=lead.campaign_id,
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            company=lead.company,
            title=lead.title,
            score=lead.score,
            status=lead.status,
            source=lead.source,
            created_at=lead.created_at
        )
        for lead in leads
    ]

# ============================================
# OUTREACH ENDPOINTS
# ============================================

@app.post("/api/outreach/start", response_model=schemas.JobResponse)
async def start_outreach(
    request: schemas.OutreachRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_token)
):
    """Start outbound outreach campaign"""

    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == request.campaign_id
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get qualified leads
    min_score = campaign.config.get("min_score", 70)
    leads = db.query(models.Lead).filter(
        models.Lead.campaign_id == request.campaign_id,
        models.Lead.status == "new",
        models.Lead.score >= min_score
    ).all()

    if not leads:
        raise HTTPException(
            status_code=400,
            detail=f"No qualified leads found (min score: {min_score})"
        )

    # Enqueue outreach job
    job_id = await enqueue_outreach_job(
        campaign_id=request.campaign_id,
        lead_ids=[lead.id for lead in leads],
        channels=request.channels,
        schedule=request.schedule
    )

    # Update campaign status
    campaign.status = "active"
    db.commit()

    logger.info(f"Outreach job enqueued: {job_id} for {len(leads)} leads")

    return schemas.JobResponse(
        job_id=job_id,
        status="pending",
        message=f"Outreach started for {len(leads)} leads via {', '.join(request.channels)}"
    )

@app.post("/api/outreach/pause/{campaign_id}")
async def pause_outreach(
    campaign_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_token)
):
    """Pause outreach campaign"""
    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == campaign_id
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = "paused"
    campaign.updated_at = datetime.utcnow()
    db.commit()

    # TODO: Cancel pending Cloud Tasks

    logger.info(f"Campaign paused: {campaign_id}")

    return {"message": "Campaign paused successfully"}

@app.post("/api/outreach/resume/{campaign_id}")
async def resume_outreach(
    campaign_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_token)
):
    """Resume paused campaign"""
    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == campaign_id
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status != "paused":
        raise HTTPException(
            status_code=400,
            detail="Can only resume paused campaigns"
        )

    campaign.status = "active"
    campaign.updated_at = datetime.utcnow()
    db.commit()

    logger.info(f"Campaign resumed: {campaign_id}")

    return {"message": "Campaign resumed successfully"}

# ============================================
# ANALYTICS ENDPOINTS
# ============================================

@app.get("/api/campaigns/{campaign_id}/stats", response_model=schemas.CampaignStats)
async def get_campaign_stats(
    campaign_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_token)
):
    """Get campaign performance statistics"""
    from sqlalchemy import func

    # Lead counts
    total_leads = db.query(func.count(models.Lead.id)).filter(
        models.Lead.campaign_id == campaign_id
    ).scalar()

    contacted = db.query(func.count(models.Lead.id)).filter(
        models.Lead.campaign_id == campaign_id,
        models.Lead.status.in_(["contacted", "responded", "converted"])
    ).scalar()

    responded = db.query(func.count(models.Lead.id)).filter(
        models.Lead.campaign_id == campaign_id,
        models.Lead.status.in_(["responded", "converted"])
    ).scalar()

    converted = db.query(func.count(models.Lead.id)).filter(
        models.Lead.campaign_id == campaign_id,
        models.Lead.status == "converted"
    ).scalar()

    # Email metrics
    email_sent = db.query(func.count(models.Interaction.id)).filter(
        models.Interaction.campaign_id == campaign_id,
        models.Interaction.channel == "email",
        models.Interaction.type == "sent"
    ).scalar()

    email_opened = db.query(func.count(models.Interaction.id)).filter(
        models.Interaction.campaign_id == campaign_id,
        models.Interaction.channel == "email",
        models.Interaction.type == "opened"
    ).scalar()

    email_clicked = db.query(func.count(models.Interaction.id)).filter(
        models.Interaction.campaign_id == campaign_id,
        models.Interaction.channel == "email",
        models.Interaction.type == "clicked"
    ).scalar()

    # Calculate rates
    email_open_rate = (email_opened / email_sent * 100) if email_sent > 0 else 0
    email_click_rate = (email_clicked / email_sent * 100) if email_sent > 0 else 0
    response_rate = (responded / contacted * 100) if contacted > 0 else 0
    conversion_rate = (converted / contacted * 100) if contacted > 0 else 0

    return schemas.CampaignStats(
        total_leads=total_leads or 0,
        contacted=contacted or 0,
        responded=responded or 0,
        converted=converted or 0,
        email_open_rate=round(email_open_rate, 2),
        email_click_rate=round(email_click_rate, 2),
        response_rate=round(response_rate, 2),
        conversion_rate=round(conversion_rate, 2)
    )

# ============================================
# WEBHOOK ENDPOINTS
# ============================================

@app.post("/webhooks/email/sendgrid")
async def sendgrid_webhook(events: List[Dict[str, Any]], db: Session = Depends(get_db)):
    """Handle SendGrid email events"""
    import uuid

    for event in events:
        interaction = models.Interaction(
            id=str(uuid.uuid4()),
            lead_id=event.get("lead_id"),
            campaign_id=event.get("campaign_id"),
            channel="email",
            type=event.get("event"),
            timestamp=datetime.fromtimestamp(event.get("timestamp", 0)),
            data=event
        )
        db.add(interaction)

    db.commit()

    logger.info(f"Processed {len(events)} SendGrid events")

    return {"status": "received"}

@app.post("/webhooks/sms/twilio")
async def twilio_sms_webhook(event: Dict[str, Any], db: Session = Depends(get_db)):
    """Handle Twilio SMS status callbacks"""
    import uuid

    interaction = models.Interaction(
        id=str(uuid.uuid4()),
        lead_id=event.get("lead_id"),
        campaign_id=event.get("campaign_id"),
        channel="sms",
        type=event.get("SmsStatus"),
        data=event
    )
    db.add(interaction)
    db.commit()

    return {"status": "received"}

@app.post("/webhooks/call/twilio")
async def twilio_call_webhook(event: Dict[str, Any], db: Session = Depends(get_db)):
    """Handle Twilio call status callbacks"""
    import uuid

    interaction = models.Interaction(
        id=str(uuid.uuid4()),
        lead_id=event.get("lead_id"),
        campaign_id=event.get("campaign_id"),
        channel="call",
        type=event.get("CallStatus"),
        data=event
    )
    db.add(interaction)
    db.commit()

    return {"status": "received"}

# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# ============================================
# STARTUP
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
