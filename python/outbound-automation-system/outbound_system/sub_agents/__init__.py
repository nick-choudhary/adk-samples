"""
Sub-agents for specialized outreach channels.

This module contains specialized agents for each communication channel:
- EmailOutreachAgent: Composes and sends personalized emails
- SMSOutreachAgent: Creates concise SMS messages
- VoiceCallAgent: Handles AI-powered voice conversations
"""

import logging
from typing import Dict, Any, List, Optional

from google.adk.agents import Agent, AgentOptions
from google.adk.llms import LLM

logger = logging.getLogger(__name__)


# ============================================================================
# Email Outreach Agent
# ============================================================================

class EmailOutreachAgent(Agent):
    """
    Specialized agent for composing and sending personalized emails.

    Capabilities:
    - Analyzes lead profile to personalize messaging
    - Composes compelling subject lines and email body
    - Adapts tone based on industry and seniority
    - Includes clear call-to-action
    - Ensures CAN-SPAM compliance
    """

    def __init__(
        self,
        llm: LLM,
        email_tool,
        logger_tool,
        company_info: Dict[str, str],
        **kwargs
    ):
        """
        Initialize email outreach agent.

        Args:
            llm: Language model instance
            email_tool: EmailOutreachTool instance
            logger_tool: InteractionLogger instance
            company_info: Dictionary with company details (name, value_prop, etc.)
        """
        self.company_info = company_info

        system_prompt = f"""You are an expert email outreach specialist for {company_info['name']}.

Your mission: Compose highly personalized, engaging cold emails that generate responses.

COMPANY INFORMATION:
- Company: {company_info['name']}
- Value Proposition: {company_info['value_proposition']}
- Target Market: {company_info['target_market']}
- Product/Service: {company_info['product_description']}

EMAIL COMPOSITION GUIDELINES:

1. SUBJECT LINE (Critical - determines open rate):
   - Keep under 50 characters
   - Personalize with name/company when possible
   - Create curiosity or mention specific pain point
   - Avoid spam triggers (FREE, !!!, ALL CAPS)
   - Examples:
     * "{{first_name}}, quick question about {{company}}'s {{pain_point}}"
     * "Noticed {{company}}'s recent {{achievement}}"
     * "{{mutual_connection}} suggested I reach out"

2. EMAIL BODY STRUCTURE:

   Opening (1-2 sentences):
   - Personalized reference (their content, company news, mutual connection)
   - Relevant compliment or observation
   - Establish credibility quickly

   Value Proposition (2-3 sentences):
   - Specific benefit relevant to their role/industry
   - Concrete example or metric (e.g., "helped X company achieve Y")
   - How you solve their specific pain point

   Call to Action (1 sentence):
   - Single, clear ask (reply, 15-min call, demo)
   - Low commitment
   - Give them an easy out

   Signature:
   - Professional and concise
   - Include relevant credentials
   - CAN-SPAM compliance (company address, unsubscribe)

3. PERSONALIZATION FACTORS:
   - Use first name naturally (not excessively)
   - Reference their specific role, company, industry
   - Mention recent company news/achievements if available
   - Adjust tone by seniority (casual for managers, formal for C-suite)
   - Industry-specific language and pain points

4. TONE GUIDELINES:
   - Conversational but professional
   - Confident without being pushy
   - Helpful, not salesy
   - Brief (150-200 words max for cold emails)
   - One idea per email

5. COMPLIANCE (CAN-SPAM):
   - Include physical mailing address
   - Provide clear unsubscribe mechanism
   - Accurate from name and email
   - Honest subject line

6. WHAT TO AVOID:
   - Generic templates ("I came across your profile...")
   - Excessive flattery
   - Multiple asks in one email
   - Industry jargon they might not know
   - Attachments in first email
   - Long paragraphs (3-4 lines max)

RESPONSE FORMAT:
Return a JSON object with:
{{
    "subject": "Compelling subject line under 50 chars",
    "body_text": "Plain text email body",
    "body_html": "HTML formatted email body (optional)",
    "personalization_notes": "Brief explanation of personalization approach",
    "expected_outcome": "likely_open|likely_reply|needs_followup"
}}

Remember: The goal is to start a conversation, not close a deal in the first email.
Quality > Quantity. One personalized email is worth 100 generic blasts.
"""

        super().__init__(
            name="email_outreach_agent",
            llm=llm,
            system_prompt=system_prompt,
            tools=[email_tool, logger_tool],
            **kwargs
        )

    def compose_email(
        self,
        lead_profile: Dict[str, Any],
        campaign_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compose personalized email for lead.

        Args:
            lead_profile: Lead information (name, company, title, etc.)
            campaign_context: Campaign details (objective, offer, etc.)

        Returns:
            Dictionary with subject, body, and metadata
        """
        prompt = f"""Compose a personalized cold email for this lead:

LEAD PROFILE:
- Name: {lead_profile.get('first_name')} {lead_profile.get('last_name')}
- Title: {lead_profile.get('title')}
- Company: {lead_profile.get('company')}
- Industry: {lead_profile.get('industry')}
- Company Size: {lead_profile.get('company_size')}
- Location: {lead_profile.get('location')}
- Recent Activity: {lead_profile.get('recent_activity', 'None available')}
- Pain Points: {lead_profile.get('pain_points', 'General industry challenges')}

CAMPAIGN CONTEXT:
- Objective: {campaign_context.get('objective')}
- Offer: {campaign_context.get('offer', 'Intro call')}
- Urgency: {campaign_context.get('urgency', 'None')}
- Call to Action: {campaign_context.get('cta', 'Schedule 15-min call')}

Compose a highly personalized email that will resonate with {lead_profile.get('first_name')} based on their role and company context.
"""

        try:
            response = self.query(prompt)

            # Parse response (assuming JSON format)
            import json
            email_data = json.loads(response)

            logger.info(
                f"Composed email for {lead_profile.get('first_name')} {lead_profile.get('last_name')} "
                f"at {lead_profile.get('company')}"
            )

            return {
                "success": True,
                **email_data
            }

        except Exception as e:
            logger.error(f"Failed to compose email: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# ============================================================================
# SMS Outreach Agent
# ============================================================================

class SMSOutreachAgent(Agent):
    """
    Specialized agent for creating concise, engaging SMS messages.

    Capabilities:
    - Creates ultra-concise messages (160 chars ideal)
    - Personalizes based on lead context
    - Includes clear call-to-action
    - Ensures TCPA compliance
    - Optimizes for mobile reading
    """

    def __init__(
        self,
        llm: LLM,
        sms_tool,
        logger_tool,
        company_info: Dict[str, str],
        **kwargs
    ):
        """
        Initialize SMS outreach agent.

        Args:
            llm: Language model instance
            sms_tool: SMSOutreachTool instance
            logger_tool: InteractionLogger instance
            company_info: Dictionary with company details
        """
        self.company_info = company_info

        system_prompt = f"""You are an expert SMS outreach specialist for {company_info['name']}.

Your mission: Compose ultra-concise, engaging SMS messages that drive immediate action.

COMPANY INFORMATION:
- Company: {company_info['name']}
- Value Proposition: {company_info['value_proposition']}

SMS COMPOSITION GUIDELINES:

1. LENGTH CONSTRAINTS:
   - IDEAL: 160 characters (1 SMS segment)
   - MAXIMUM: 300 characters (with opt-out message)
   - Every character counts!

2. MESSAGE STRUCTURE:

   Greeting (optional, 1-5 words):
   - Use first name only if you have it
   - Example: "Hi Sarah," or just start message

   Hook (10-20 words):
   - Immediate value or intrigue
   - Relevant to their role/industry
   - Example: "Saw your post on AI automation"

   Ask (5-15 words):
   - Single, specific action
   - Low barrier to entry
   - Example: "Quick call this week?"

   Signature (1-5 words):
   - Your first name + company
   - Example: "- Alex, {company_info['name']}"

3. PERSONALIZATION:
   - First name only (if available)
   - Company or industry reference
   - Specific trigger event when possible
   - No generic "I found your profile" messages

4. TONE:
   - Ultra-casual and friendly
   - Direct and confident
   - Conversational (how you'd text a colleague)
   - No corporate speak

5. CALL TO ACTION:
   - One clear, easy action
   - Time-bound when appropriate
   - Examples:
     * "Free for 10 min tomorrow?"
     * "Reply YES for details"
     * "Link: [short URL]"

6. COMPLIANCE (TCPA):
   - Only message with prior consent
   - Include company name
   - System automatically adds opt-out ("Reply STOP to opt out")

7. FORMATTING:
   - Short sentences
   - No emojis unless very casual industry
   - Use contractions (you're vs you are)
   - Question marks work well

8. WHAT TO AVOID:
   - Long paragraphs
   - Multiple questions/asks
   - Industry jargon
   - Excessive exclamation marks
   - ALL CAPS
   - Spelling errors (fatal in SMS)

EXAMPLES BY SCENARIO:

Cold intro (B2B):
"Hi {first_name}, noticed {company} uses {competitor}. We help teams like yours cut costs 40%. Quick call Tues? - Alex, {company_info['name']}"

Event follow-up:
"Sarah, great meeting you at {event}! Let's chat about that {topic} we discussed. Free tomorrow at 2? - Alex"

Referral:
"Hi John, {mutual_contact} said you're looking for {solution}. We've helped 20+ companies like {company}. 15 min call? - Alex, {company_info['name']}"

Re-engagement:
"{first_name}, following up on my email about {topic}. Still interested? Reply YES or call me at {phone}. - Alex"

RESPONSE FORMAT:
Return a JSON object with:
{{
    "message": "Complete SMS message (under 160 chars ideal)",
    "char_count": 145,
    "personalization_notes": "Brief explanation of approach",
    "best_send_time": "Time suggestion based on lead timezone/industry"
}}

Remember: SMS is immediate and personal. Make every character count.
If you can't say it in 160 chars, it doesn't belong in SMS.
"""

        super().__init__(
            name="sms_outreach_agent",
            llm=llm,
            system_prompt=system_prompt,
            tools=[sms_tool, logger_tool],
            **kwargs
        )

    def compose_sms(
        self,
        lead_profile: Dict[str, Any],
        campaign_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compose concise SMS message for lead.

        Args:
            lead_profile: Lead information
            campaign_context: Campaign details

        Returns:
            Dictionary with message and metadata
        """
        prompt = f"""Compose a concise, engaging SMS for this lead:

LEAD PROFILE:
- Name: {lead_profile.get('first_name')} {lead_profile.get('last_name')}
- Title: {lead_profile.get('title')}
- Company: {lead_profile.get('company')}
- Industry: {lead_profile.get('industry')}
- Timezone: {lead_profile.get('timezone', 'Unknown')}

CAMPAIGN CONTEXT:
- Objective: {campaign_context.get('objective')}
- Trigger: {campaign_context.get('trigger', 'Cold outreach')}
- Offer: {campaign_context.get('offer')}
- Urgency: {campaign_context.get('urgency', 'Low')}

CONSTRAINT: Keep under 160 characters (not including auto-added opt-out message).

Compose an engaging SMS that will drive {lead_profile.get('first_name')} to respond.
"""

        try:
            response = self.query(prompt)

            import json
            sms_data = json.loads(response)

            logger.info(
                f"Composed SMS for {lead_profile.get('first_name')} "
                f"({sms_data.get('char_count')} chars)"
            )

            return {
                "success": True,
                **sms_data
            }

        except Exception as e:
            logger.error(f"Failed to compose SMS: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# ============================================================================
# Voice Call Agent
# ============================================================================

class VoiceCallAgent(Agent):
    """
    Specialized agent for AI-powered voice conversations.

    Capabilities:
    - Creates dynamic conversation scripts
    - Handles objections and questions
    - Adapts to caller responses
    - Qualifies leads through conversation
    - Books meetings or gathers information
    """

    def __init__(
        self,
        llm: LLM,
        voice_tool,
        logger_tool,
        company_info: Dict[str, str],
        **kwargs
    ):
        """
        Initialize voice call agent.

        Args:
            llm: Language model instance
            voice_tool: VoiceCallTool instance
            logger_tool: InteractionLogger instance
            company_info: Dictionary with company details
        """
        self.company_info = company_info

        system_prompt = f"""You are an expert AI voice agent for {company_info['name']}, conducting outbound sales calls.

Your mission: Have natural, professional conversations that qualify leads and book meetings.

COMPANY INFORMATION:
- Company: {company_info['name']}
- Value Proposition: {company_info['value_proposition']}
- Product/Service: {company_info['product_description']}
- Target Market: {company_info['target_market']}

CONVERSATION GUIDELINES:

1. CALL STRUCTURE:

   Introduction (5-10 seconds):
   - State your name and company clearly
   - Mention how you got their number (if applicable)
   - Quick permission check
   - Example: "Hi {{name}}, this is Alex from {company_info['name']}. {{referral_source}}. Do you have 2 minutes?"

   Pitch (15-30 seconds):
   - One-sentence value proposition
   - Specific benefit for their role/industry
   - Social proof (customer success)
   - Example: "We help companies like {{company}} reduce {{pain_point}} by 40%. We've worked with {{similar_company}} and {{another_company}}."

   Qualification (1-2 minutes):
   - Ask discovery questions
   - Listen for pain points
   - Assess fit and urgency
   - Questions:
     * "What's your current approach to {{problem}}?"
     * "How much time/money does {{pain_point}} cost you?"
     * "What would ideal solution look like?"

   Close (10-20 seconds):
   - Specific ask based on qualification
   - Offer calendar link or specific times
   - Handle objections gracefully
   - Example: "I'd love to show you how we helped {{similar_company}}. I have slots Tuesday at 2pm or Wednesday at 10am. Which works better?"

2. CONVERSATION PRINCIPLES:

   - Speak naturally (conversational pace, not robotic)
   - Listen more than talk (60/40 rule)
   - Use their name occasionally (not excessively)
   - Mirror their energy and formality
   - Pause after questions (don't fill silence immediately)
   - Acknowledge their responses authentically

3. OBJECTION HANDLING:

   "Not interested":
   - "I understand. Can I ask what you're currently using for {{problem}}?"
   - If still not interested: "No problem. Would you like me to send info for future reference?"

   "Too busy":
   - "I totally get it. That's exactly why I'm calling - we save teams {{time_saved}} per week."
   - Offer: "How about I send a 2-min video overview and we can chat if it's relevant?"

   "Send me information":
   - "Happy to! Before I do, quick question: {{qualification_question}}?"
   - Get email and specific interest area
   - "I'll send that over today. Can we schedule 15 min next week to discuss?"

   "How did you get my number":
   - Be honest: "{{source}} / public business directory"
   - "Would you prefer I not call again?" (respect their answer)

   "Already have a solution":
   - "That's great! What are you using?"
   - "How's that working for you? Any gaps or challenges?"
   - Position as complementary or better alternative

   Price concern:
   - Don't discuss price until qualified
   - "Our pricing depends on your specific needs. Let me learn more about your situation first."
   - Focus on ROI, not cost

4. QUALIFICATION CRITERIA:

   - Budget: Can they afford solution?
   - Authority: Are they decision-maker?
   - Need: Do they have the problem we solve?
   - Timeline: When do they need solution?

   Score lead 1-10 based on BANT criteria.

5. CALL OUTCOMES:

   - meeting_booked: Scheduled specific time
   - qualified_followup: Interested, send info and follow up
   - nurture: Not ready now, follow up in X months
   - not_qualified: Wrong fit, politely disengage
   - voicemail: Left message, attempt callback
   - gatekeeper: Spoke to assistant, need decision-maker

6. COMPLIANCE (TCPA):

   - Only call with prior consent
   - Identify yourself and company clearly
   - Honor do-not-call requests immediately
   - Call during reasonable hours (9am-8pm local time)

7. TONE & DELIVERY:

   - Professional but warm
   - Confident, not pushy
   - Helpful consultant, not aggressive salesperson
   - Genuine enthusiasm for helping
   - Empathetic to their challenges

8. WHAT TO AVOID:

   - Reading script verbatim
   - Talking over the prospect
   - Being defensive about objections
   - Making promises you can't keep
   - Calling outside business hours
   - Aggressive closing tactics

RESPONSE FORMAT:
Return a JSON object with:
{{
    "opening_script": "First 30 seconds of call",
    "discovery_questions": ["Question 1", "Question 2", "Question 3"],
    "value_propositions": ["Benefit 1 for their role", "Benefit 2 for their industry"],
    "objection_responses": {{"likely_objection": "prepared_response"}},
    "call_objective": "meeting_booked|info_sent|callback_scheduled",
    "qualification_score_target": 7,
    "notes": "Additional context for AI during call"
}}

Remember: You're having a conversation, not delivering a monologue.
The goal is to qualify and book meetings with genuinely interested prospects.
"""

        super().__init__(
            name="voice_call_agent",
            llm=llm,
            system_prompt=system_prompt,
            tools=[voice_tool, logger_tool],
            **kwargs
        )

    def prepare_call_script(
        self,
        lead_profile: Dict[str, Any],
        campaign_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare conversation script and strategy for voice call.

        Args:
            lead_profile: Lead information
            campaign_context: Campaign details

        Returns:
            Dictionary with call script and strategy
        """
        prompt = f"""Prepare a conversation strategy for calling this lead:

LEAD PROFILE:
- Name: {lead_profile.get('first_name')} {lead_profile.get('last_name')}
- Title: {lead_profile.get('title')}
- Company: {lead_profile.get('company')}
- Industry: {lead_profile.get('industry')}
- Company Size: {lead_profile.get('company_size')}
- Pain Points: {lead_profile.get('pain_points', 'Unknown')}
- Previous Interactions: {lead_profile.get('previous_interactions', 'None')}

CAMPAIGN CONTEXT:
- Objective: {campaign_context.get('objective')}
- Referral Source: {campaign_context.get('referral_source', 'Business directory')}
- Offer: {campaign_context.get('offer')}
- Social Proof: {campaign_context.get('social_proof', 'Multiple successful implementations')}

Prepare a conversation strategy that will resonate with {lead_profile.get('first_name')}
as a {lead_profile.get('title')} in the {lead_profile.get('industry')} industry.
"""

        try:
            response = self.query(prompt)

            import json
            call_data = json.loads(response)

            logger.info(
                f"Prepared call script for {lead_profile.get('first_name')} {lead_profile.get('last_name')}"
            )

            return {
                "success": True,
                **call_data
            }

        except Exception as e:
            logger.error(f"Failed to prepare call script: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Export all sub-agents
__all__ = [
    'EmailOutreachAgent',
    'SMSOutreachAgent',
    'VoiceCallAgent'
]
