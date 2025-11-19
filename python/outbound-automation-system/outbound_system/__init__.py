"""
Outbound Automation System - Multi-channel outreach with AI agents.

This package provides a complete solution for automated outbound campaigns:
- Multi-channel outreach (Email, SMS, Voice)
- AI-powered personalization
- Intelligent channel selection
- Compliance management (CAN-SPAM, TCPA, GDPR)
- Rate limiting and retry logic
- Comprehensive logging and analytics

Main Components:
---------------
- OutboundCampaignAgent: Main orchestrator for multi-channel campaigns
- EmailOutreachAgent: Specialized email composition and sending
- SMSOutreachAgent: SMS message creation and delivery
- VoiceCallAgent: AI-powered voice conversation handling

Tools:
------
- EmailOutreachTool: SendGrid integration
- SMSOutreachTool: Twilio SMS integration
- VoiceCallTool: Twilio voice call integration
- InteractionLogger: Interaction tracking and logging
- ComplianceChecker: Compliance verification and consent management

Quick Start:
-----------
```python
from google.adk.llms import LLM
from outbound_system import create_outbound_agent

# Configure LLM
llm = LLM(model="gemini-2.0-flash")

# Company information
company_info = {
    "name": "Acme Corp",
    "value_proposition": "AI-powered sales automation for B2B teams",
    "product_description": "Multi-channel outreach platform with AI personalization",
    "target_market": "B2B SaaS companies with 10-500 employees",
    "from_email": "sales@acme.com",
    "from_name": "Alex from Acme"
}

# Create agent
agent = create_outbound_agent(llm, company_info)

# Execute outreach
lead_profile = {
    "id": "lead-123",
    "first_name": "Sarah",
    "last_name": "Johnson",
    "email": "sarah@techcorp.com",
    "phone": "+14155551234",
    "title": "VP of Sales",
    "company": "TechCorp",
    "industry": "Technology",
    "company_size": "100-500",
    "score": 85
}

campaign_context = {
    "campaign_id": "campaign-456",
    "objective": "book_meetings",
    "offer": "Free sales automation audit",
    "urgency": "medium"
}

result = agent.execute_outreach(
    lead_profile=lead_profile,
    campaign_context=campaign_context
)

print(f"Outreach executed via {result['channel']}: {result['result']}")
```

Batch Campaign:
--------------
```python
# Run campaign for multiple leads
leads = [lead1, lead2, lead3, ...]

results = agent.run_campaign_batch(
    leads=leads,
    campaign_context=campaign_context,
    max_concurrent=50
)

print(f"Campaign completed: {results['successful']}/{results['total_leads']} successful")
```

Environment Variables:
---------------------
Set these environment variables or pass to agent constructor:

- SENDGRID_API_KEY: SendGrid API key for email
- TWILIO_ACCOUNT_SID: Twilio account SID
- TWILIO_AUTH_TOKEN: Twilio auth token
- TWILIO_PHONE_NUMBER: Twilio phone number (E.164 format)
- TWILIO_TWIML_APP_SID: TwiML application SID for voice

Compliance:
----------
The system enforces:
- CAN-SPAM compliance for email (unsubscribe links, physical address)
- TCPA compliance for SMS/calls (consent verification, opt-out handling)
- GDPR/CCPA data privacy (consent tracking, data retention)
- Do Not Contact list management
- Rate limiting to prevent abuse

For more information, see the documentation in each module.
"""

from .agent import (
    OutboundCampaignAgent,
    create_outbound_agent,
    Channel,
    CampaignObjective,
    LeadScore,
    ChannelSelector
)

from .tools import (
    EmailOutreachTool,
    SMSOutreachTool,
    VoiceCallTool,
    InteractionLogger,
    ComplianceChecker,
    RateLimiter,
    retry_on_failure
)

from .sub_agents import (
    EmailOutreachAgent,
    SMSOutreachAgent,
    VoiceCallAgent
)

# Version
__version__ = "1.0.0"

# Package metadata
__author__ = "Your Name"
__email__ = "you@company.com"
__license__ = "Apache-2.0"

# Public API
__all__ = [
    # Main agent
    "OutboundCampaignAgent",
    "create_outbound_agent",

    # Enums and helpers
    "Channel",
    "CampaignObjective",
    "LeadScore",
    "ChannelSelector",

    # Tools
    "EmailOutreachTool",
    "SMSOutreachTool",
    "VoiceCallTool",
    "InteractionLogger",
    "ComplianceChecker",
    "RateLimiter",
    "retry_on_failure",

    # Sub-agents
    "EmailOutreachAgent",
    "SMSOutreachAgent",
    "VoiceCallAgent",
]
