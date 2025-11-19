"""
Outbound Campaign Orchestrator Agent.

This module contains the main orchestrator agent that coordinates all outbound outreach activities:
- Multi-channel campaign management (email, SMS, voice)
- Intelligent channel selection based on lead profile and campaign goals
- Compliance verification and consent management
- Interaction tracking and analytics
- Adaptive sequencing based on engagement
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Literal
from enum import Enum

from google.adk.agents import Agent, AgentOptions
from google.adk.llms import LLM

from .tools import (
    EmailOutreachTool,
    SMSOutreachTool,
    VoiceCallTool,
    InteractionLogger,
    ComplianceChecker
)
from .sub_agents import (
    EmailOutreachAgent,
    SMSOutreachAgent,
    VoiceCallAgent
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================

class Channel(str, Enum):
    """Communication channels for outreach."""
    EMAIL = "email"
    SMS = "sms"
    VOICE = "voice"


class CampaignObjective(str, Enum):
    """Campaign objectives."""
    GENERATE_LEADS = "generate_leads"
    BOOK_MEETINGS = "book_meetings"
    NURTURE_LEADS = "nurture_leads"
    RE_ENGAGE = "re_engage"
    PRODUCT_LAUNCH = "product_launch"
    EVENT_PROMOTION = "event_promotion"


class LeadScore(str, Enum):
    """Lead quality scores."""
    HOT = "hot"  # 80-100: High fit, strong signals
    WARM = "warm"  # 60-79: Good fit, some signals
    COLD = "cold"  # 40-59: Moderate fit
    ICE_COLD = "ice_cold"  # 0-39: Low fit


# ============================================================================
# Channel Selection Logic
# ============================================================================

class ChannelSelector:
    """
    Intelligent channel selection based on lead profile, campaign goals, and engagement history.
    """

    @staticmethod
    def select_channel(
        lead_profile: Dict[str, Any],
        campaign_context: Dict[str, Any],
        interaction_history: List[Dict[str, Any]]
    ) -> Channel:
        """
        Select optimal communication channel for lead.

        Selection criteria:
        1. Lead score and seniority (C-suite = email first, managers = flexible)
        2. Previous engagement (what worked before?)
        3. Industry norms (tech = email, retail = SMS, enterprise = calls)
        4. Campaign objective (awareness = email, urgent = call)
        5. Time sensitivity
        6. Available contact info

        Args:
            lead_profile: Lead information and preferences
            campaign_context: Campaign goals and constraints
            interaction_history: Previous interactions with lead

        Returns:
            Recommended channel
        """
        score = 0
        channel_scores = {
            Channel.EMAIL: 0,
            Channel.SMS: 0,
            Channel.VOICE: 0
        }

        # Check available contact methods
        has_email = bool(lead_profile.get('email'))
        has_phone = bool(lead_profile.get('phone'))
        has_mobile = lead_profile.get('phone_type') == 'mobile'

        if not has_email:
            channel_scores[Channel.EMAIL] = -999
        if not has_phone:
            channel_scores[Channel.SMS] = -999
            channel_scores[Channel.VOICE] = -999
        if not has_mobile:
            channel_scores[Channel.SMS] = -999

        # Factor 1: Lead Score (hot leads get calls)
        lead_score = lead_profile.get('score', 50)
        if lead_score >= 80:
            channel_scores[Channel.VOICE] += 30
            channel_scores[Channel.EMAIL] += 20
        elif lead_score >= 60:
            channel_scores[Channel.EMAIL] += 30
            channel_scores[Channel.VOICE] += 20
        else:
            channel_scores[Channel.EMAIL] += 40
            channel_scores[Channel.SMS] += 20

        # Factor 2: Seniority Level
        title = lead_profile.get('title', '').lower()
        if any(role in title for role in ['ceo', 'cto', 'cfo', 'president', 'vp', 'director']):
            # C-suite and VPs prefer email
            channel_scores[Channel.EMAIL] += 30
            channel_scores[Channel.VOICE] += 20  # High-value calls worth it
            channel_scores[Channel.SMS] -= 20  # Too casual
        elif any(role in title for role in ['manager', 'lead', 'head']):
            # Managers are flexible
            channel_scores[Channel.EMAIL] += 20
            channel_scores[Channel.SMS] += 15
            channel_scores[Channel.VOICE] += 15
        else:
            # Individual contributors respond well to all channels
            channel_scores[Channel.EMAIL] += 15
            channel_scores[Channel.SMS] += 20
            channel_scores[Channel.VOICE] += 10

        # Factor 3: Industry Preferences
        industry = lead_profile.get('industry', '').lower()
        if any(ind in industry for ind in ['technology', 'software', 'saas', 'tech']):
            channel_scores[Channel.EMAIL] += 25  # Tech people live in email
            channel_scores[Channel.SMS] += 10
        elif any(ind in industry for ind in ['retail', 'restaurant', 'hospitality']):
            channel_scores[Channel.SMS] += 25  # Fast-paced, mobile-first
            channel_scores[Channel.VOICE] += 15
        elif any(ind in industry for ind in ['finance', 'legal', 'healthcare']):
            channel_scores[Channel.EMAIL] += 30  # Formal, documented
            channel_scores[Channel.VOICE] += 15
        elif any(ind in industry for ind in ['construction', 'manufacturing', 'services']):
            channel_scores[Channel.VOICE] += 25  # Hands-on, phone-friendly
            channel_scores[Channel.SMS] += 15

        # Factor 4: Campaign Objective
        objective = campaign_context.get('objective')
        if objective == CampaignObjective.BOOK_MEETINGS:
            channel_scores[Channel.VOICE] += 25  # Calls close meetings faster
            channel_scores[Channel.EMAIL] += 15
        elif objective == CampaignObjective.NURTURE_LEADS:
            channel_scores[Channel.EMAIL] += 30  # Email for educational content
        elif objective == CampaignObjective.RE_ENGAGE:
            channel_scores[Channel.SMS] += 25  # SMS breaks through
            channel_scores[Channel.VOICE] += 20
        elif objective == CampaignObjective.EVENT_PROMOTION:
            channel_scores[Channel.EMAIL] += 25
            channel_scores[Channel.SMS] += 20

        # Factor 5: Urgency/Time Sensitivity
        urgency = campaign_context.get('urgency', 'low')
        if urgency == 'high':
            channel_scores[Channel.VOICE] += 30
            channel_scores[Channel.SMS] += 25
        elif urgency == 'medium':
            channel_scores[Channel.SMS] += 15
            channel_scores[Channel.EMAIL] += 10

        # Factor 6: Previous Engagement
        if interaction_history:
            # What channels worked before?
            email_opens = sum(1 for i in interaction_history if i.get('channel') == 'email' and i.get('opened'))
            email_clicks = sum(1 for i in interaction_history if i.get('channel') == 'email' and i.get('clicked'))
            sms_replies = sum(1 for i in interaction_history if i.get('channel') == 'sms' and i.get('replied'))
            call_answers = sum(1 for i in interaction_history if i.get('channel') == 'voice' and i.get('answered'))

            if email_opens > 0:
                channel_scores[Channel.EMAIL] += 20
            if email_clicks > 0:
                channel_scores[Channel.EMAIL] += 30
            if sms_replies > 0:
                channel_scores[Channel.SMS] += 35
            if call_answers > 0:
                channel_scores[Channel.VOICE] += 35

            # Avoid channels that didn't work
            email_sent = sum(1 for i in interaction_history if i.get('channel') == 'email')
            if email_sent > 2 and email_opens == 0:
                channel_scores[Channel.EMAIL] -= 20  # They're not opening emails

        # Factor 7: Opt-out and Preferences
        if lead_profile.get('email_opt_out'):
            channel_scores[Channel.EMAIL] = -999
        if lead_profile.get('sms_opt_out'):
            channel_scores[Channel.SMS] = -999
        if lead_profile.get('call_opt_out'):
            channel_scores[Channel.VOICE] = -999

        # Select channel with highest score
        selected_channel = max(channel_scores.items(), key=lambda x: x[1])[0]

        logger.info(
            f"Channel selection for {lead_profile.get('email', 'unknown')}: "
            f"{selected_channel.value} (scores: {channel_scores})"
        )

        return selected_channel

    @staticmethod
    def create_sequence(
        lead_profile: Dict[str, Any],
        campaign_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Create multi-touch sequence with optimal timing and channels.

        Returns:
            List of touches with channel, timing, and content type
        """
        sequence = []
        lead_score = lead_profile.get('score', 50)
        objective = campaign_context.get('objective')

        # Hot leads (80+): Aggressive sequence
        if lead_score >= 80:
            sequence = [
                {"day": 0, "channel": Channel.EMAIL, "content": "personalized_intro"},
                {"day": 1, "channel": Channel.VOICE, "content": "qualification_call"},
                {"day": 3, "channel": Channel.EMAIL, "content": "case_study"},
                {"day": 7, "channel": Channel.VOICE, "content": "demo_offer"},
            ]

        # Warm leads (60-79): Balanced sequence
        elif lead_score >= 60:
            sequence = [
                {"day": 0, "channel": Channel.EMAIL, "content": "personalized_intro"},
                {"day": 3, "channel": Channel.EMAIL, "content": "value_proposition"},
                {"day": 7, "channel": Channel.SMS, "content": "quick_question"},
                {"day": 14, "channel": Channel.VOICE, "content": "check_in_call"},
            ]

        # Cold leads (40-59): Patient nurture
        elif lead_score >= 40:
            sequence = [
                {"day": 0, "channel": Channel.EMAIL, "content": "intro_with_value"},
                {"day": 5, "channel": Channel.EMAIL, "content": "educational_content"},
                {"day": 14, "channel": Channel.EMAIL, "content": "social_proof"},
                {"day": 28, "channel": Channel.SMS, "content": "re_engagement"},
            ]

        # Ice cold leads (0-39): Long nurture or skip
        else:
            sequence = [
                {"day": 0, "channel": Channel.EMAIL, "content": "broad_value_prop"},
                {"day": 14, "channel": Channel.EMAIL, "content": "industry_insights"},
                {"day": 45, "channel": Channel.EMAIL, "content": "case_study"},
            ]

        return sequence


# ============================================================================
# Main Outbound Campaign Orchestrator Agent
# ============================================================================

class OutboundCampaignAgent(Agent):
    """
    Main orchestrator agent for multi-channel outbound campaigns.

    Responsibilities:
    - Coordinate email, SMS, and voice sub-agents
    - Select optimal channels for each lead
    - Manage campaign sequences and timing
    - Track interactions and engagement
    - Ensure compliance across all channels
    - Adapt strategy based on results
    """

    def __init__(
        self,
        llm: LLM,
        company_info: Dict[str, str],
        sendgrid_api_key: Optional[str] = None,
        twilio_account_sid: Optional[str] = None,
        twilio_auth_token: Optional[str] = None,
        twilio_phone: Optional[str] = None,
        twilio_twiml_app_sid: Optional[str] = None,
        log_endpoint: str = "https://your-domain.com/api/interactions",
        dnc_list: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize outbound campaign orchestrator.

        Args:
            llm: Language model instance
            company_info: Company details for personalization
            sendgrid_api_key: SendGrid API key (or from env)
            twilio_account_sid: Twilio account SID (or from env)
            twilio_auth_token: Twilio auth token (or from env)
            twilio_phone: Twilio phone number (or from env)
            twilio_twiml_app_sid: TwiML app SID for voice (or from env)
            log_endpoint: Endpoint for logging interactions
            dnc_list: Do Not Contact list
        """
        # Load credentials from environment if not provided
        sendgrid_api_key = sendgrid_api_key or os.getenv('SENDGRID_API_KEY')
        twilio_account_sid = twilio_account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        twilio_auth_token = twilio_auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        twilio_phone = twilio_phone or os.getenv('TWILIO_PHONE_NUMBER')
        twilio_twiml_app_sid = twilio_twiml_app_sid or os.getenv('TWILIO_TWIML_APP_SID')

        # Initialize compliance checker
        self.compliance_checker = ComplianceChecker(dnc_list=dnc_list)

        # Initialize tools
        self.logger_tool = InteractionLogger(log_endpoint=log_endpoint)

        self.email_tool = EmailOutreachTool(
            api_key=sendgrid_api_key,
            from_email=company_info.get('from_email', 'hello@company.com'),
            from_name=company_info.get('from_name', company_info['name']),
            compliance_checker=self.compliance_checker,
            max_emails_per_minute=100
        ) if sendgrid_api_key else None

        self.sms_tool = SMSOutreachTool(
            account_sid=twilio_account_sid,
            auth_token=twilio_auth_token,
            from_phone=twilio_phone,
            compliance_checker=self.compliance_checker,
            max_sms_per_minute=50
        ) if all([twilio_account_sid, twilio_auth_token, twilio_phone]) else None

        self.voice_tool = VoiceCallTool(
            account_sid=twilio_account_sid,
            auth_token=twilio_auth_token,
            from_phone=twilio_phone,
            twiml_app_sid=twilio_twiml_app_sid,
            compliance_checker=self.compliance_checker,
            max_calls_per_minute=10
        ) if all([twilio_account_sid, twilio_auth_token, twilio_phone, twilio_twiml_app_sid]) else None

        # Initialize sub-agents
        self.email_agent = EmailOutreachAgent(
            llm=llm,
            email_tool=self.email_tool,
            logger_tool=self.logger_tool,
            company_info=company_info
        ) if self.email_tool else None

        self.sms_agent = SMSOutreachAgent(
            llm=llm,
            sms_tool=self.sms_tool,
            logger_tool=self.logger_tool,
            company_info=company_info
        ) if self.sms_tool else None

        self.voice_agent = VoiceCallAgent(
            llm=llm,
            voice_tool=self.voice_tool,
            logger_tool=self.logger_tool,
            company_info=company_info
        ) if self.voice_tool else None

        # Channel selector
        self.channel_selector = ChannelSelector()

        # Company info
        self.company_info = company_info

        # System prompt for orchestrator
        system_prompt = f"""You are the Outbound Campaign Orchestrator for {company_info['name']}.

Your mission: Intelligently coordinate multi-channel outreach campaigns to maximize engagement and conversions.

RESPONSIBILITIES:

1. CHANNEL SELECTION
   - Analyze lead profile (score, title, industry, engagement history)
   - Consider campaign objectives and urgency
   - Select optimal channel (email, SMS, or voice)
   - Respect opt-outs and compliance requirements

2. CAMPAIGN SEQUENCING
   - Design multi-touch sequences based on lead score
   - Hot leads: Aggressive (4-5 touches over 7-14 days)
   - Warm leads: Balanced (4 touches over 14-21 days)
   - Cold leads: Patient nurture (3-4 touches over 30-60 days)
   - Adapt based on engagement signals

3. PERSONALIZATION
   - Coordinate with sub-agents (email, SMS, voice) for content creation
   - Ensure consistent messaging across channels
   - Personalize based on lead data and behavior

4. COMPLIANCE MANAGEMENT
   - Verify consent before each outreach
   - Check Do Not Contact lists
   - Honor opt-outs immediately
   - Ensure CAN-SPAM, TCPA, GDPR compliance

5. PERFORMANCE TRACKING
   - Log all interactions
   - Monitor engagement metrics
   - Identify best-performing channels and messages
   - Recommend optimizations

6. ADAPTIVE STRATEGY
   - If email not opened after 2 attempts → try SMS or call
   - If SMS not replied → try email with more context
   - If call not answered → leave voicemail and send email
   - If any engagement → accelerate sequence
   - If no engagement after sequence → pause and revisit later

DECISION FRAMEWORK:

For each lead, you should:
1. Assess lead quality and readiness
2. Select appropriate channel(s)
3. Coordinate with relevant sub-agent(s)
4. Execute outreach with compliance checks
5. Log interaction
6. Determine next action based on response

Always prioritize quality over quantity. One highly personalized, well-timed message is worth 100 generic blasts.

Available sub-agents:
- Email Outreach Agent: {self.email_agent.name if self.email_agent else 'Not configured'}
- SMS Outreach Agent: {self.sms_agent.name if self.sms_agent else 'Not configured'}
- Voice Call Agent: {self.voice_agent.name if self.voice_agent else 'Not configured'}
"""

        # Collect all available tools
        tools = [self.logger_tool]
        if self.email_tool:
            tools.append(self.email_tool)
        if self.sms_tool:
            tools.append(self.sms_tool)
        if self.voice_tool:
            tools.append(self.voice_tool)

        super().__init__(
            name="outbound_campaign_orchestrator",
            llm=llm,
            system_prompt=system_prompt,
            tools=tools,
            **kwargs
        )

    def execute_outreach(
        self,
        lead_profile: Dict[str, Any],
        campaign_context: Dict[str, Any],
        interaction_history: Optional[List[Dict[str, Any]]] = None,
        consent_db: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, Any]:
        """
        Execute outreach to a single lead with intelligent channel selection.

        Args:
            lead_profile: Lead information and contact details
            campaign_context: Campaign goals, messaging, and constraints
            interaction_history: Previous interactions with this lead
            consent_db: Consent records for compliance

        Returns:
            Dictionary with execution results and next actions
        """
        interaction_history = interaction_history or []
        consent_db = consent_db or {}

        try:
            # Step 1: Select optimal channel
            selected_channel = self.channel_selector.select_channel(
                lead_profile=lead_profile,
                campaign_context=campaign_context,
                interaction_history=interaction_history
            )

            logger.info(
                f"Executing {selected_channel.value} outreach to "
                f"{lead_profile.get('email', lead_profile.get('phone', 'unknown'))}"
            )

            # Step 2: Execute via appropriate sub-agent
            result = None

            if selected_channel == Channel.EMAIL and self.email_agent:
                # Compose email
                email_composition = self.email_agent.compose_email(
                    lead_profile=lead_profile,
                    campaign_context=campaign_context
                )

                if email_composition.get('success'):
                    # Send email
                    result = self.email_tool.execute(
                        to_email=lead_profile['email'],
                        subject=email_composition['subject'],
                        body_text=email_composition['body_text'],
                        body_html=email_composition.get('body_html'),
                        contact_id=lead_profile.get('id', 'unknown'),
                        campaign_id=campaign_context.get('campaign_id', 'unknown')
                    )

                    # Log interaction
                    self.logger_tool.execute(
                        contact_id=lead_profile.get('id'),
                        campaign_id=campaign_context.get('campaign_id'),
                        channel='email',
                        status='sent' if result.get('success') else 'failed',
                        metadata={
                            'subject': email_composition['subject'],
                            'message_id': result.get('message_id'),
                            'personalization_notes': email_composition.get('personalization_notes')
                        }
                    )

            elif selected_channel == Channel.SMS and self.sms_agent:
                # Compose SMS
                sms_composition = self.sms_agent.compose_sms(
                    lead_profile=lead_profile,
                    campaign_context=campaign_context
                )

                if sms_composition.get('success'):
                    # Send SMS
                    result = self.sms_tool.execute(
                        to_phone=lead_profile['phone'],
                        message=sms_composition['message'],
                        contact_id=lead_profile.get('id', 'unknown'),
                        campaign_id=campaign_context.get('campaign_id', 'unknown'),
                        consent_db=consent_db
                    )

                    # Log interaction
                    self.logger_tool.execute(
                        contact_id=lead_profile.get('id'),
                        campaign_id=campaign_context.get('campaign_id'),
                        channel='sms',
                        status='sent' if result.get('success') else 'failed',
                        metadata={
                            'message': sms_composition['message'],
                            'char_count': sms_composition.get('char_count'),
                            'message_sid': result.get('message_sid')
                        }
                    )

            elif selected_channel == Channel.VOICE and self.voice_agent:
                # Prepare call script
                call_preparation = self.voice_agent.prepare_call_script(
                    lead_profile=lead_profile,
                    campaign_context=campaign_context
                )

                if call_preparation.get('success'):
                    # Initiate call
                    result = self.voice_tool.execute(
                        to_phone=lead_profile['phone'],
                        call_script=call_preparation['opening_script'],
                        call_objective=call_preparation['call_objective'],
                        contact_id=lead_profile.get('id', 'unknown'),
                        campaign_id=campaign_context.get('campaign_id', 'unknown'),
                        consent_db=consent_db,
                        record_call=campaign_context.get('record_calls', True)
                    )

                    # Log interaction
                    self.logger_tool.execute(
                        contact_id=lead_profile.get('id'),
                        campaign_id=campaign_context.get('campaign_id'),
                        channel='voice',
                        status='initiated' if result.get('success') else 'failed',
                        metadata={
                            'call_sid': result.get('call_sid'),
                            'call_objective': call_preparation['call_objective'],
                            'qualification_score_target': call_preparation.get('qualification_score_target')
                        }
                    )

            # Step 3: Determine next action
            next_action = self._determine_next_action(
                result=result,
                channel=selected_channel,
                lead_profile=lead_profile,
                interaction_history=interaction_history
            )

            return {
                "success": True,
                "channel": selected_channel.value,
                "result": result,
                "next_action": next_action,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to execute outreach: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _determine_next_action(
        self,
        result: Dict[str, Any],
        channel: Channel,
        lead_profile: Dict[str, Any],
        interaction_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Determine next action based on outreach result."""

        if not result or not result.get('success'):
            # Failed - retry with different channel after delay
            return {
                "action": "retry",
                "delay_days": 2,
                "suggested_channel": "email" if channel != Channel.EMAIL else "sms",
                "reason": "Previous attempt failed"
            }

        # Count attempts on this channel
        channel_attempts = sum(
            1 for i in interaction_history
            if i.get('channel') == channel.value
        )

        if channel_attempts >= 2:
            # Try different channel
            return {
                "action": "switch_channel",
                "delay_days": 3,
                "reason": f"No response after {channel_attempts} {channel.value} attempts"
            }

        # Default: follow up on same channel
        return {
            "action": "follow_up",
            "delay_days": 3 if channel == Channel.EMAIL else 7,
            "suggested_channel": channel.value,
            "reason": "Continue sequence"
        }

    def run_campaign_batch(
        self,
        leads: List[Dict[str, Any]],
        campaign_context: Dict[str, Any],
        consent_db: Optional[Dict[str, Dict]] = None,
        max_concurrent: int = 50
    ) -> Dict[str, Any]:
        """
        Execute outreach campaign for batch of leads.

        Args:
            leads: List of lead profiles
            campaign_context: Campaign configuration
            consent_db: Consent records
            max_concurrent: Maximum concurrent operations

        Returns:
            Campaign execution summary
        """
        results = {
            "total_leads": len(leads),
            "successful": 0,
            "failed": 0,
            "by_channel": {
                "email": 0,
                "sms": 0,
                "voice": 0
            },
            "errors": [],
            "started_at": datetime.now().isoformat()
        }

        # Process leads in batches
        for i, lead in enumerate(leads):
            logger.info(f"Processing lead {i+1}/{len(leads)}: {lead.get('email', lead.get('phone'))}")

            try:
                # Get interaction history (would come from database)
                interaction_history = lead.get('interaction_history', [])

                # Execute outreach
                outcome = self.execute_outreach(
                    lead_profile=lead,
                    campaign_context=campaign_context,
                    interaction_history=interaction_history,
                    consent_db=consent_db
                )

                if outcome.get('success'):
                    results['successful'] += 1
                    channel = outcome.get('channel')
                    if channel in results['by_channel']:
                        results['by_channel'][channel] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'lead_id': lead.get('id'),
                        'error': outcome.get('error')
                    })

            except Exception as e:
                logger.error(f"Error processing lead {lead.get('id')}: {e}")
                results['failed'] += 1
                results['errors'].append({
                    'lead_id': lead.get('id'),
                    'error': str(e)
                })

        results['completed_at'] = datetime.now().isoformat()
        results['success_rate'] = (results['successful'] / results['total_leads'] * 100) if results['total_leads'] > 0 else 0

        logger.info(
            f"Campaign batch completed: {results['successful']}/{results['total_leads']} successful "
            f"({results['success_rate']:.1f}%)"
        )

        return results


# ============================================================================
# Factory Function
# ============================================================================

def create_outbound_agent(
    llm: LLM,
    company_info: Dict[str, str],
    **kwargs
) -> OutboundCampaignAgent:
    """
    Factory function to create configured outbound campaign agent.

    Args:
        llm: Language model instance
        company_info: Company information for personalization
            Required keys:
            - name: Company name
            - value_proposition: One-sentence value prop
            - product_description: What you sell
            - target_market: Who you sell to
            - from_email: Sender email
            - from_name: Sender name
        **kwargs: Additional configuration

    Returns:
        Configured OutboundCampaignAgent instance

    Example:
        >>> from google.adk.llms import LLM
        >>> llm = LLM(model="gemini-2.0-flash")
        >>> company_info = {
        ...     "name": "Acme Corp",
        ...     "value_proposition": "AI-powered sales automation",
        ...     "product_description": "Multi-channel outreach platform",
        ...     "target_market": "B2B SaaS companies",
        ...     "from_email": "sales@acme.com",
        ...     "from_name": "Alex from Acme"
        ... }
        >>> agent = create_outbound_agent(llm, company_info)
        >>> result = agent.execute_outreach(lead_profile, campaign_context)
    """
    return OutboundCampaignAgent(
        llm=llm,
        company_info=company_info,
        **kwargs
    )
