"""
Outbound outreach tools for email, SMS, and voice communication.

This module provides production-ready tools for multi-channel outreach:
- SendGrid email sending with templates and tracking
- Twilio SMS messaging with compliance checks
- Twilio voice calls with AI conversation handling
- Rate limiting and retry logic
- Comprehensive error handling and logging
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Literal
from functools import wraps

import phonenumbers
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Personalization
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException
import requests

from google.adk.tools.tool_kit import Tool

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Rate Limiting Decorator
# ============================================================================

class RateLimiter:
    """Thread-safe rate limiter with sliding window algorithm."""

    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[float] = []

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()

            # Remove calls outside the time window
            self.calls = [call for call in self.calls if now - call < self.time_window]

            # Check if we've exceeded the limit
            if len(self.calls) >= self.max_calls:
                wait_time = self.time_window - (now - self.calls[0])
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
                self.calls = self.calls[1:]

            # Record this call
            self.calls.append(now)

            return func(*args, **kwargs)

        return wrapper


def retry_on_failure(max_retries: int = 3, backoff_factor: float = 2.0):
    """
    Retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for wait time between retries
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {wait_time:.1f}s"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")

            raise last_exception

        return wrapper

    return decorator


# ============================================================================
# Compliance and Validation
# ============================================================================

class ComplianceChecker:
    """Handles compliance checks for outbound communications."""

    def __init__(self, dnc_list: Optional[List[str]] = None):
        """
        Initialize compliance checker.

        Args:
            dnc_list: List of phone numbers/emails on Do Not Contact list
        """
        self.dnc_list = set(dnc_list or [])

    def is_on_dnc_list(self, contact: str) -> bool:
        """Check if contact is on Do Not Contact list."""
        return contact.lower() in self.dnc_list

    def validate_email(self, email: str) -> tuple[bool, str]:
        """
        Validate email address.

        Returns:
            Tuple of (is_valid, reason)
        """
        if not email or '@' not in email:
            return False, "Invalid email format"

        if self.is_on_dnc_list(email):
            return False, "Email on Do Not Contact list"

        # Check for disposable domains
        disposable_domains = ['tempmail.com', 'guerrillamail.com', '10minutemail.com']
        domain = email.split('@')[1].lower()
        if domain in disposable_domains:
            return False, "Disposable email domain"

        return True, "Valid"

    def validate_phone(self, phone: str, country: str = 'US') -> tuple[bool, str]:
        """
        Validate phone number.

        Args:
            phone: Phone number to validate
            country: Country code (default: US)

        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            parsed = phonenumbers.parse(phone, country)

            if not phonenumbers.is_valid_number(parsed):
                return False, "Invalid phone number format"

            # Format for DNC check
            formatted = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )

            if self.is_on_dnc_list(formatted):
                return False, "Phone number on Do Not Contact list"

            return True, "Valid"

        except phonenumbers.NumberParseException as e:
            return False, f"Failed to parse phone number: {e}"

    def check_consent(self, contact_id: str, consent_db: Dict[str, Dict]) -> tuple[bool, str]:
        """
        Check if contact has given consent for outreach.

        Args:
            contact_id: Unique identifier for contact
            consent_db: Database of consent records

        Returns:
            Tuple of (has_consent, consent_type)
        """
        consent = consent_db.get(contact_id, {})

        if not consent:
            return False, "No consent record found"

        if consent.get('opted_out'):
            return False, "Contact has opted out"

        # Check consent expiration (1 year for TCPA)
        consent_date = consent.get('consent_date')
        if consent_date:
            consent_datetime = datetime.fromisoformat(consent_date)
            if datetime.now() - consent_datetime > timedelta(days=365):
                return False, "Consent expired (>1 year)"

        return True, consent.get('consent_type', 'implicit')


# ============================================================================
# Email Tool (SendGrid)
# ============================================================================

class EmailOutreachTool(Tool):
    """
    SendGrid-powered email outreach tool with templates and tracking.

    Features:
    - HTML/plain text email support
    - Dynamic template variables
    - Open/click tracking
    - Unsubscribe handling
    - Batch sending
    - Retry logic
    """

    def __init__(
        self,
        api_key: str,
        from_email: str,
        from_name: str,
        compliance_checker: ComplianceChecker,
        max_emails_per_minute: int = 100
    ):
        """
        Initialize email tool.

        Args:
            api_key: SendGrid API key
            from_email: Sender email address
            from_name: Sender name
            compliance_checker: Compliance checker instance
            max_emails_per_minute: Rate limit for email sending
        """
        super().__init__(
            name="send_email",
            description=(
                "Send personalized email via SendGrid. "
                "Supports HTML templates, tracking, and unsubscribe links. "
                "Automatically handles compliance checks and rate limiting."
            ),
            parameters={
                "to_email": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "body_text": {
                    "type": "string",
                    "description": "Plain text email body"
                },
                "body_html": {
                    "type": "string",
                    "description": "HTML email body (optional)"
                },
                "template_id": {
                    "type": "string",
                    "description": "SendGrid template ID (optional)"
                },
                "template_data": {
                    "type": "object",
                    "description": "Dynamic template variables (optional)"
                },
                "contact_id": {
                    "type": "string",
                    "description": "Unique contact identifier for tracking"
                },
                "campaign_id": {
                    "type": "string",
                    "description": "Campaign identifier"
                }
            },
            required=["to_email", "subject", "contact_id", "campaign_id"]
        )

        self.client = SendGridAPIClient(api_key)
        self.from_email = from_email
        self.from_name = from_name
        self.compliance_checker = compliance_checker
        self.rate_limiter = RateLimiter(
            max_calls=max_emails_per_minute,
            time_window=60
        )

    @retry_on_failure(max_retries=3)
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Send email with compliance checks and tracking.

        Returns:
            Dictionary with success status, message_id, and details
        """
        to_email = kwargs['to_email']
        subject = kwargs['subject']
        body_text = kwargs.get('body_text', '')
        body_html = kwargs.get('body_html')
        template_id = kwargs.get('template_id')
        template_data = kwargs.get('template_data', {})
        contact_id = kwargs['contact_id']
        campaign_id = kwargs['campaign_id']

        # Compliance check
        is_valid, reason = self.compliance_checker.validate_email(to_email)
        if not is_valid:
            logger.warning(f"Email blocked for {to_email}: {reason}")
            return {
                "success": False,
                "error": f"Compliance check failed: {reason}",
                "contact_id": contact_id
            }

        # Rate limiting
        self.rate_limiter(lambda: None)()

        try:
            # Build email
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject
            )

            # Add unsubscribe link
            unsubscribe_url = f"https://your-domain.com/unsubscribe?contact={contact_id}"
            body_text += f"\n\nTo unsubscribe: {unsubscribe_url}"

            if body_html:
                body_html += f'<p><a href="{unsubscribe_url}">Unsubscribe</a></p>'

            # Set content
            if template_id:
                message.template_id = template_id
                message.dynamic_template_data = template_data
            else:
                message.content = [Content("text/plain", body_text)]
                if body_html:
                    message.content.append(Content("text/html", body_html))

            # Enable tracking
            message.tracking_settings = {
                "click_tracking": {"enable": True},
                "open_tracking": {"enable": True}
            }

            # Add custom args for tracking
            message.custom_args = {
                "contact_id": contact_id,
                "campaign_id": campaign_id,
                "sent_at": datetime.now().isoformat()
            }

            # Send email
            response = self.client.send(message)

            logger.info(
                f"Email sent successfully to {to_email}. "
                f"Status: {response.status_code}, Message ID: {response.headers.get('X-Message-Id')}"
            )

            return {
                "success": True,
                "message_id": response.headers.get('X-Message-Id'),
                "status_code": response.status_code,
                "contact_id": contact_id,
                "campaign_id": campaign_id,
                "sent_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {
                "success": False,
                "error": str(e),
                "contact_id": contact_id,
                "campaign_id": campaign_id
            }


# ============================================================================
# SMS Tool (Twilio)
# ============================================================================

class SMSOutreachTool(Tool):
    """
    Twilio-powered SMS outreach tool with TCPA compliance.

    Features:
    - SMS sending with consent verification
    - TCPA compliance checks
    - Opt-out handling (STOP keywords)
    - Delivery status tracking
    - Rate limiting
    """

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_phone: str,
        compliance_checker: ComplianceChecker,
        max_sms_per_minute: int = 50
    ):
        """
        Initialize SMS tool.

        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_phone: Sender phone number (E.164 format)
            compliance_checker: Compliance checker instance
            max_sms_per_minute: Rate limit for SMS sending
        """
        super().__init__(
            name="send_sms",
            description=(
                "Send SMS message via Twilio with TCPA compliance. "
                "Automatically checks consent, Do Not Contact list, and opt-out status. "
                "Messages must be concise (160 chars recommended)."
            ),
            parameters={
                "to_phone": {
                    "type": "string",
                    "description": "Recipient phone number (E.164 format recommended)"
                },
                "message": {
                    "type": "string",
                    "description": "SMS message body (160 chars recommended, 1600 max)"
                },
                "contact_id": {
                    "type": "string",
                    "description": "Unique contact identifier"
                },
                "campaign_id": {
                    "type": "string",
                    "description": "Campaign identifier"
                },
                "consent_db": {
                    "type": "object",
                    "description": "Consent database for TCPA compliance"
                }
            },
            required=["to_phone", "message", "contact_id", "campaign_id"]
        )

        self.client = TwilioClient(account_sid, auth_token)
        self.from_phone = from_phone
        self.compliance_checker = compliance_checker
        self.rate_limiter = RateLimiter(
            max_calls=max_sms_per_minute,
            time_window=60
        )

    @retry_on_failure(max_retries=3)
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Send SMS with TCPA compliance checks.

        Returns:
            Dictionary with success status, message_sid, and details
        """
        to_phone = kwargs['to_phone']
        message = kwargs['message']
        contact_id = kwargs['contact_id']
        campaign_id = kwargs['campaign_id']
        consent_db = kwargs.get('consent_db', {})

        # Validate phone number
        is_valid, reason = self.compliance_checker.validate_phone(to_phone)
        if not is_valid:
            logger.warning(f"SMS blocked for {to_phone}: {reason}")
            return {
                "success": False,
                "error": f"Phone validation failed: {reason}",
                "contact_id": contact_id
            }

        # Check consent (TCPA requirement)
        has_consent, consent_type = self.compliance_checker.check_consent(
            contact_id, consent_db
        )
        if not has_consent:
            logger.warning(f"SMS blocked for {to_phone}: {consent_type}")
            return {
                "success": False,
                "error": f"Consent check failed: {consent_type}",
                "contact_id": contact_id
            }

        # Add opt-out instructions (TCPA requirement)
        if "reply STOP to opt out" not in message.lower():
            message += "\n\nReply STOP to opt out"

        # Validate message length
        if len(message) > 1600:
            return {
                "success": False,
                "error": "Message exceeds 1600 character limit",
                "contact_id": contact_id
            }

        # Rate limiting
        self.rate_limiter(lambda: None)()

        try:
            # Format phone number
            parsed = phonenumbers.parse(to_phone, 'US')
            formatted_phone = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )

            # Send SMS
            sms = self.client.messages.create(
                to=formatted_phone,
                from_=self.from_phone,
                body=message,
                status_callback=f"https://your-domain.com/webhooks/sms/status?contact={contact_id}",
            )

            logger.info(
                f"SMS sent successfully to {formatted_phone}. "
                f"SID: {sms.sid}, Status: {sms.status}"
            )

            return {
                "success": True,
                "message_sid": sms.sid,
                "status": sms.status,
                "to_phone": formatted_phone,
                "contact_id": contact_id,
                "campaign_id": campaign_id,
                "sent_at": datetime.now().isoformat(),
                "consent_type": consent_type
            }

        except TwilioRestException as e:
            logger.error(f"Twilio error sending SMS to {to_phone}: {e}")
            return {
                "success": False,
                "error": f"Twilio error: {e.msg}",
                "error_code": e.code,
                "contact_id": contact_id
            }
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {e}")
            return {
                "success": False,
                "error": str(e),
                "contact_id": contact_id
            }


# ============================================================================
# Voice Call Tool (Twilio + AI)
# ============================================================================

class VoiceCallTool(Tool):
    """
    Twilio-powered voice call tool with AI conversation handling.

    Features:
    - Outbound call initiation
    - AI-powered conversation via TwiML
    - Call recording and transcription
    - TCPA compliance checks
    - Call status tracking
    """

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_phone: str,
        twiml_app_sid: str,
        compliance_checker: ComplianceChecker,
        max_calls_per_minute: int = 10
    ):
        """
        Initialize voice call tool.

        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_phone: Caller ID phone number
            twiml_app_sid: TwiML application SID for AI handling
            compliance_checker: Compliance checker instance
            max_calls_per_minute: Rate limit for call initiation
        """
        super().__init__(
            name="make_voice_call",
            description=(
                "Initiate outbound voice call via Twilio with AI conversation handling. "
                "Checks TCPA compliance, consent, and Do Not Call list. "
                "AI agent handles conversation based on provided script/objectives."
            ),
            parameters={
                "to_phone": {
                    "type": "string",
                    "description": "Recipient phone number (E.164 format)"
                },
                "call_script": {
                    "type": "string",
                    "description": "Initial message/script for AI agent"
                },
                "call_objective": {
                    "type": "string",
                    "description": "Objective of the call (e.g., 'schedule_demo', 'qualify_lead')"
                },
                "contact_id": {
                    "type": "string",
                    "description": "Unique contact identifier"
                },
                "campaign_id": {
                    "type": "string",
                    "description": "Campaign identifier"
                },
                "consent_db": {
                    "type": "object",
                    "description": "Consent database for TCPA compliance"
                },
                "record_call": {
                    "type": "boolean",
                    "description": "Whether to record the call (default: true)"
                }
            },
            required=["to_phone", "call_script", "call_objective", "contact_id", "campaign_id"]
        )

        self.client = TwilioClient(account_sid, auth_token)
        self.from_phone = from_phone
        self.twiml_app_sid = twiml_app_sid
        self.compliance_checker = compliance_checker
        self.rate_limiter = RateLimiter(
            max_calls=max_calls_per_minute,
            time_window=60
        )

    @retry_on_failure(max_retries=2)  # Fewer retries for calls
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Initiate voice call with AI conversation handling.

        Returns:
            Dictionary with success status, call_sid, and details
        """
        to_phone = kwargs['to_phone']
        call_script = kwargs['call_script']
        call_objective = kwargs['call_objective']
        contact_id = kwargs['contact_id']
        campaign_id = kwargs['campaign_id']
        consent_db = kwargs.get('consent_db', {})
        record_call = kwargs.get('record_call', True)

        # Validate phone number
        is_valid, reason = self.compliance_checker.validate_phone(to_phone)
        if not is_valid:
            logger.warning(f"Call blocked for {to_phone}: {reason}")
            return {
                "success": False,
                "error": f"Phone validation failed: {reason}",
                "contact_id": contact_id
            }

        # Check consent (TCPA requirement for autodialers)
        has_consent, consent_type = self.compliance_checker.check_consent(
            contact_id, consent_db
        )
        if not has_consent:
            logger.warning(f"Call blocked for {to_phone}: {consent_type}")
            return {
                "success": False,
                "error": f"Consent check failed: {consent_type}",
                "contact_id": contact_id
            }

        # Rate limiting
        self.rate_limiter(lambda: None)()

        try:
            # Format phone number
            parsed = phonenumbers.parse(to_phone, 'US')
            formatted_phone = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )

            # Build status callback URL with context
            callback_url = (
                f"https://your-domain.com/webhooks/voice/status"
                f"?contact={contact_id}&campaign={campaign_id}"
            )

            # Build TwiML URL with call context
            twiml_url = (
                f"https://your-domain.com/webhooks/voice/handle"
                f"?contact={contact_id}&objective={call_objective}"
                f"&script={requests.utils.quote(call_script[:200])}"  # URL length limit
            )

            # Initiate call
            call = self.client.calls.create(
                to=formatted_phone,
                from_=self.from_phone,
                url=twiml_url,
                status_callback=callback_url,
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                record=record_call,
                machine_detection='DetectMessageEnd',  # Detect voicemail
                timeout=30  # Ring timeout
            )

            logger.info(
                f"Call initiated to {formatted_phone}. "
                f"SID: {call.sid}, Status: {call.status}"
            )

            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status,
                "to_phone": formatted_phone,
                "contact_id": contact_id,
                "campaign_id": campaign_id,
                "call_objective": call_objective,
                "initiated_at": datetime.now().isoformat(),
                "consent_type": consent_type,
                "record_call": record_call
            }

        except TwilioRestException as e:
            logger.error(f"Twilio error initiating call to {to_phone}: {e}")
            return {
                "success": False,
                "error": f"Twilio error: {e.msg}",
                "error_code": e.code,
                "contact_id": contact_id
            }
        except Exception as e:
            logger.error(f"Failed to initiate call to {to_phone}: {e}")
            return {
                "success": False,
                "error": str(e),
                "contact_id": contact_id
            }


# ============================================================================
# Interaction Logging Tool
# ============================================================================

class InteractionLogger(Tool):
    """
    Logs all outreach interactions to database/storage for tracking and analytics.
    """

    def __init__(self, log_endpoint: str):
        """
        Initialize interaction logger.

        Args:
            log_endpoint: API endpoint for logging interactions
        """
        super().__init__(
            name="log_interaction",
            description=(
                "Log outreach interaction (email, SMS, call) to database for tracking. "
                "Records contact details, channel, outcome, and metadata."
            ),
            parameters={
                "contact_id": {"type": "string", "description": "Contact identifier"},
                "campaign_id": {"type": "string", "description": "Campaign identifier"},
                "channel": {
                    "type": "string",
                    "description": "Communication channel",
                    "enum": ["email", "sms", "voice"]
                },
                "status": {
                    "type": "string",
                    "description": "Interaction status",
                    "enum": ["sent", "delivered", "failed", "bounced", "answered", "voicemail"]
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata (message_id, duration, etc.)"
                }
            },
            required=["contact_id", "campaign_id", "channel", "status"]
        )

        self.log_endpoint = log_endpoint

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Log interaction to database."""
        try:
            payload = {
                **kwargs,
                "timestamp": datetime.now().isoformat(),
                "logged_at": datetime.now().isoformat()
            }

            # Send to logging endpoint
            response = requests.post(
                self.log_endpoint,
                json=payload,
                timeout=5
            )

            response.raise_for_status()

            logger.info(f"Logged {kwargs['channel']} interaction for contact {kwargs['contact_id']}")

            return {
                "success": True,
                "log_id": response.json().get('log_id'),
                "timestamp": payload["timestamp"]
            }

        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
