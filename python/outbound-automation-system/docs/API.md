# API Documentation - Outbound Automation System

Complete REST API reference for the Outbound Automation System.

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Campaigns](#campaigns)
  - [Lead Extraction](#lead-extraction)
  - [Outreach](#outreach)
  - [Analytics](#analytics)
  - [Webhooks](#webhooks)

## Overview

The Outbound Automation API is a RESTful API that provides programmatic access to all system features. All API requests and responses use JSON format.

### API Features

- **RESTful Design**: Standard HTTP methods (GET, POST, PUT, DELETE)
- **JSON Format**: All requests and responses in JSON
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Protects against abuse
- **Async Jobs**: Long-running tasks processed in background
- **Webhooks**: Real-time event notifications

### Interactive Documentation

The API includes auto-generated interactive documentation:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI Spec**: http://localhost:8080/openapi.json

## Authentication

### JWT Token Authentication

All API endpoints (except health check and webhooks) require authentication using JWT tokens.

#### Get a Token

```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Use the Token

Include the token in the `Authorization` header:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Token Expiration

Tokens expire after 1 hour (3600 seconds). Refresh tokens before they expire:

```bash
POST /api/auth/refresh
Authorization: Bearer <your-old-token>
```

## Base URL

### Local Development
```
http://localhost:8080
```

### Production
```
https://your-domain.com
```

All endpoint paths are relative to the base URL.

## Response Format

### Success Response

```json
{
  "id": "campaign-uuid",
  "name": "Q1 2025 Campaign",
  "status": "active",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### List Response

```json
[
  {
    "id": "campaign-1",
    "name": "Campaign 1"
  },
  {
    "id": "campaign-2",
    "name": "Campaign 2"
  }
]
```

### Pagination

For large datasets, use pagination parameters:

```bash
GET /api/campaigns?skip=0&limit=50
```

**Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 50, max: 100)

## Error Handling

### Error Response Format

```json
{
  "error": "Campaign not found",
  "detail": "No campaign exists with ID: campaign-123",
  "status_code": 404
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Common Error Examples

#### 400 Bad Request
```json
{
  "error": "Validation error",
  "detail": [
    {
      "field": "target_industries",
      "message": "Field required"
    }
  ]
}
```

#### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "detail": "Invalid or expired token"
}
```

#### 429 Rate Limit Exceeded
```json
{
  "error": "Rate limit exceeded",
  "detail": "Maximum 60 requests per minute allowed",
  "retry_after": 45
}
```

## Rate Limiting

### Limits

- **Per User**: 60 requests/minute, 1000 requests/hour
- **Per IP**: 100 requests/minute

### Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642252800
```

### Handling Rate Limits

When rate limited (429 status), wait before retrying:

```python
import time
import requests

response = requests.get(url, headers=headers)

if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    time.sleep(retry_after)
    response = requests.get(url, headers=headers)
```

## Endpoints

## Campaigns

### Create Campaign

Create a new outbound campaign.

```http
POST /api/campaigns
```

**Request Body**:
```json
{
  "name": "Q1 2025 Enterprise SaaS",
  "target_industries": ["Technology", "SaaS", "Financial Services"],
  "target_titles": ["CEO", "CTO", "VP Engineering"],
  "company_size": "50-500",
  "geography": "United States",
  "sources": ["apollo", "linkedin"],
  "min_score": 70
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Campaign name |
| target_industries | array | Yes | Target industries |
| target_titles | array | Yes | Target job titles |
| company_size | string | Yes | Company size range |
| geography | string | Yes | Geographic location |
| sources | array | Yes | Lead sources (apollo, linkedin, google_search, etc.) |
| min_score | integer | No | Minimum lead score (0-100), default: 70 |

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Q1 2025 Enterprise SaaS",
  "status": "draft",
  "config": {
    "target_industries": ["Technology", "SaaS", "Financial Services"],
    "target_titles": ["CEO", "CTO", "VP Engineering"],
    "company_size": "50-500",
    "geography": "United States",
    "sources": ["apollo", "linkedin"],
    "min_score": 70
  },
  "stats": {
    "total_leads": 0,
    "contacted": 0,
    "responded": 0,
    "converted": 0
  },
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8080/api/campaigns \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 2025 Enterprise SaaS",
    "target_industries": ["Technology", "SaaS"],
    "target_titles": ["CEO", "CTO"],
    "company_size": "50-500",
    "geography": "United States",
    "sources": ["apollo"],
    "min_score": 70
  }'
```

### Get Campaign

Retrieve details of a specific campaign.

```http
GET /api/campaigns/{campaign_id}
```

**Parameters**:
- `campaign_id` (path): Campaign UUID

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Q1 2025 Enterprise SaaS",
  "status": "active",
  "config": {...},
  "stats": {...},
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:35:00Z"
}
```

**Example**:
```bash
curl -X GET http://localhost:8080/api/campaigns/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Campaigns

List all campaigns with optional filtering.

```http
GET /api/campaigns
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| skip | integer | No | Number of records to skip (default: 0) |
| limit | integer | No | Max records to return (default: 50, max: 100) |
| status | string | No | Filter by status (draft, extracting, active, paused, completed) |

**Response** (200 OK):
```json
[
  {
    "id": "campaign-1",
    "name": "Q1 2025 Campaign",
    "status": "active",
    "created_at": "2025-01-15T10:30:00Z"
  },
  {
    "id": "campaign-2",
    "name": "Q4 2024 Campaign",
    "status": "completed",
    "created_at": "2024-10-01T09:00:00Z"
  }
]
```

**Example**:
```bash
# Get first 20 active campaigns
curl -X GET "http://localhost:8080/api/campaigns?status=active&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Delete Campaign

Delete a campaign (must be in draft or paused status).

```http
DELETE /api/campaigns/{campaign_id}
```

**Parameters**:
- `campaign_id` (path): Campaign UUID

**Response** (200 OK):
```json
{
  "message": "Campaign deleted successfully"
}
```

**Error** (400 Bad Request):
```json
{
  "error": "Cannot delete active campaign. Pause it first."
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8080/api/campaigns/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Lead Extraction

### Start Lead Extraction

Initiate an asynchronous lead extraction job.

```http
POST /api/leads/extract
```

**Request Body**:
```json
{
  "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_count": 500,
  "sources": ["apollo", "linkedin", "google_search"],
  "filters": {
    "industries": ["Technology", "SaaS"],
    "titles": ["CEO", "CTO", "VP Engineering"],
    "company_size": "50-200",
    "geography": "United States",
    "exclude_domains": ["gmail.com", "yahoo.com"]
  }
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| campaign_id | string | Yes | Campaign UUID |
| target_count | integer | Yes | Target number of leads |
| sources | array | Yes | Sources to extract from |
| filters | object | Yes | Extraction filters |

**Response** (200 OK):
```json
{
  "job_id": "job-uuid-12345",
  "status": "pending",
  "message": "Lead extraction started. Target: 500 leads"
}
```

**Example**:
```bash
curl -X POST http://localhost:8080/api/leads/extract \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
    "target_count": 500,
    "sources": ["apollo"],
    "filters": {
      "industries": ["Technology"],
      "titles": ["CEO", "CTO"],
      "company_size": "50-200"
    }
  }'
```

### Check Extraction Job Status

Monitor the progress of a lead extraction job.

```http
GET /api/leads/job/{job_id}
```

**Parameters**:
- `job_id` (path): Job UUID

**Response** (200 OK):
```json
{
  "job_id": "job-uuid-12345",
  "status": "running",
  "progress": 45,
  "extracted_count": 225,
  "target_count": 500,
  "started_at": "2025-01-15T10:30:00Z",
  "estimated_completion": "2025-01-15T10:45:00Z"
}
```

**Job Statuses**:
- `pending`: Job queued, not started
- `running`: Job in progress
- `completed`: Job finished successfully
- `failed`: Job failed with error
- `cancelled`: Job cancelled by user

**Example**:
```bash
curl -X GET http://localhost:8080/api/leads/job/job-uuid-12345 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Campaign Leads

Retrieve leads for a specific campaign.

```http
GET /api/campaigns/{campaign_id}/leads
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| skip | integer | No | Records to skip (default: 0) |
| limit | integer | No | Max records (default: 50) |
| min_score | integer | No | Filter by minimum score |
| status | string | No | Filter by status (new, contacted, responded, converted) |

**Response** (200 OK):
```json
[
  {
    "id": "lead-uuid-1",
    "campaign_id": "campaign-uuid",
    "name": "John Smith",
    "email": "john.smith@techcorp.com",
    "phone": "+1-555-0101",
    "company": "TechCorp Inc",
    "title": "CEO",
    "score": 85,
    "status": "new",
    "source": "apollo",
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

**Example**:
```bash
# Get top-scoring leads (score >= 80)
curl -X GET "http://localhost:8080/api/campaigns/550e8400-e29b-41d4-a716-446655440000/leads?min_score=80" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Outreach

### Start Outreach Campaign

Launch a multi-channel outreach campaign.

```http
POST /api/outreach/start
```

**Request Body**:
```json
{
  "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
  "channels": ["email", "linkedin", "call"],
  "schedule": {
    "sequence": [
      {
        "day": 0,
        "channel": "email",
        "template": "intro",
        "subject": "Quick question about {{company}}"
      },
      {
        "day": 3,
        "channel": "linkedin",
        "action": "connect",
        "message": "Hi {{first_name}}, saw your work at {{company}}..."
      },
      {
        "day": 7,
        "channel": "email",
        "template": "follow_up_1",
        "subject": "Re: Quick question about {{company}}"
      },
      {
        "day": 14,
        "channel": "call",
        "min_score": 85,
        "script": "voice_intro"
      }
    ],
    "send_time": "09:00-17:00",
    "timezone": "America/New_York"
  }
}
```

**Response** (200 OK):
```json
{
  "job_id": "outreach-job-uuid",
  "status": "pending",
  "message": "Outreach started for 342 leads via email, linkedin, call"
}
```

**Example**:
```bash
curl -X POST http://localhost:8080/api/outreach/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
    "channels": ["email"],
    "schedule": {
      "sequence": [
        {"day": 0, "channel": "email", "template": "intro"}
      ]
    }
  }'
```

### Pause Outreach

Pause an active outreach campaign.

```http
POST /api/outreach/pause/{campaign_id}
```

**Response** (200 OK):
```json
{
  "message": "Campaign paused successfully"
}
```

**Example**:
```bash
curl -X POST http://localhost:8080/api/outreach/pause/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Resume Outreach

Resume a paused campaign.

```http
POST /api/outreach/resume/{campaign_id}
```

**Response** (200 OK):
```json
{
  "message": "Campaign resumed successfully"
}
```

**Error** (400 Bad Request):
```json
{
  "error": "Can only resume paused campaigns"
}
```

**Example**:
```bash
curl -X POST http://localhost:8080/api/outreach/resume/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Analytics

### Get Campaign Statistics

Retrieve performance metrics for a campaign.

```http
GET /api/campaigns/{campaign_id}/stats
```

**Response** (200 OK):
```json
{
  "total_leads": 500,
  "contacted": 342,
  "responded": 45,
  "converted": 12,
  "email_open_rate": 32.5,
  "email_click_rate": 8.2,
  "response_rate": 13.2,
  "conversion_rate": 3.5
}
```

**Metric Definitions**:

| Metric | Description | Calculation |
|--------|-------------|-------------|
| total_leads | Total leads in campaign | Count of all leads |
| contacted | Leads that received outreach | Leads with status ≥ contacted |
| responded | Leads that responded | Leads with status = responded |
| converted | Leads that converted | Leads with status = converted |
| email_open_rate | Email open rate % | (opened / sent) × 100 |
| email_click_rate | Email click rate % | (clicked / sent) × 100 |
| response_rate | Overall response rate % | (responded / contacted) × 100 |
| conversion_rate | Conversion rate % | (converted / contacted) × 100 |

**Example**:
```bash
curl -X GET http://localhost:8080/api/campaigns/550e8400-e29b-41d4-a716-446655440000/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Webhooks

### SendGrid Webhook

Receives email events from SendGrid.

```http
POST /webhooks/email/sendgrid
```

**This endpoint is called by SendGrid, not by you.**

**Configure in SendGrid**:
1. Go to Settings → Mail Settings → Event Webhook
2. Set HTTP Post URL: `https://your-domain.com/webhooks/email/sendgrid`
3. Select events: Delivered, Opened, Clicked, Bounced, Unsubscribed

**Request Body** (example):
```json
[
  {
    "email": "john@example.com",
    "timestamp": 1642252800,
    "event": "opened",
    "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
    "lead_id": "lead-uuid-1"
  }
]
```

**Events**:
- `delivered`: Email delivered successfully
- `opened`: Email opened by recipient
- `clicked`: Link clicked in email
- `bounced`: Email bounced
- `spam_report`: Marked as spam
- `unsubscribe`: Recipient unsubscribed

### Twilio SMS Webhook

Receives SMS status updates from Twilio.

```http
POST /webhooks/sms/twilio
```

**Configure in Twilio**:
1. Go to Phone Numbers → Active Numbers
2. Set Messaging webhook: `https://your-domain.com/webhooks/sms/twilio`

**Request Body** (example):
```json
{
  "SmsStatus": "delivered",
  "MessageSid": "SM1234567890",
  "To": "+15555551234",
  "From": "+15555550100",
  "lead_id": "lead-uuid-1",
  "campaign_id": "campaign-uuid"
}
```

**SMS Statuses**:
- `queued`: Message queued
- `sending`: Message sending
- `sent`: Message sent
- `delivered`: Message delivered
- `failed`: Message failed
- `undelivered`: Message undelivered

### Twilio Call Webhook

Receives call status updates from Twilio.

```http
POST /webhooks/call/twilio
```

**Configure in Twilio**:
1. Go to Voice → TwiML Apps
2. Set Status Callback URL: `https://your-domain.com/webhooks/call/twilio`

**Request Body** (example):
```json
{
  "CallStatus": "completed",
  "CallSid": "CA1234567890",
  "Duration": "180",
  "lead_id": "lead-uuid-1",
  "campaign_id": "campaign-uuid"
}
```

**Call Statuses**:
- `queued`: Call queued
- `ringing`: Phone ringing
- `in-progress`: Call in progress
- `completed`: Call completed
- `busy`: Busy signal
- `failed`: Call failed
- `no-answer`: No answer

## Code Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8080"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create campaign
campaign_data = {
    "name": "Q1 2025 Campaign",
    "target_industries": ["Technology"],
    "target_titles": ["CEO", "CTO"],
    "company_size": "50-200",
    "geography": "United States",
    "sources": ["apollo"],
    "min_score": 70
}

response = requests.post(
    f"{BASE_URL}/api/campaigns",
    json=campaign_data,
    headers=headers
)

campaign = response.json()
print(f"Campaign created: {campaign['id']}")

# Start lead extraction
extraction_data = {
    "campaign_id": campaign["id"],
    "target_count": 500,
    "sources": ["apollo"],
    "filters": {
        "industries": ["Technology"],
        "titles": ["CEO", "CTO"]
    }
}

response = requests.post(
    f"{BASE_URL}/api/leads/extract",
    json=extraction_data,
    headers=headers
)

job = response.json()
print(f"Extraction job started: {job['job_id']}")
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8080';
const TOKEN = 'your-jwt-token';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// Create campaign
const campaignData = {
  name: 'Q1 2025 Campaign',
  target_industries: ['Technology'],
  target_titles: ['CEO', 'CTO'],
  company_size: '50-200',
  geography: 'United States',
  sources: ['apollo'],
  min_score: 70
};

const response = await fetch(`${BASE_URL}/api/campaigns`, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify(campaignData)
});

const campaign = await response.json();
console.log(`Campaign created: ${campaign.id}`);

// Get campaign stats
const statsResponse = await fetch(
  `${BASE_URL}/api/campaigns/${campaign.id}/stats`,
  { headers: headers }
);

const stats = await statsResponse.json();
console.log('Campaign stats:', stats);
```

### cURL

```bash
# Set variables
TOKEN="your-jwt-token"
BASE_URL="http://localhost:8080"

# Create campaign
curl -X POST "$BASE_URL/api/campaigns" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 2025 Campaign",
    "target_industries": ["Technology"],
    "target_titles": ["CEO"],
    "company_size": "50-200",
    "geography": "United States",
    "sources": ["apollo"],
    "min_score": 70
  }'

# List campaigns
curl -X GET "$BASE_URL/api/campaigns?status=active" \
  -H "Authorization: Bearer $TOKEN"

# Get stats
curl -X GET "$BASE_URL/api/campaigns/CAMPAIGN_ID/stats" \
  -H "Authorization: Bearer $TOKEN"
```

---

**Need Help?**
- Interactive docs: http://localhost:8080/docs
- GitHub Issues: https://github.com/google/adk-samples/issues
- Examples: [EXAMPLES.md](./EXAMPLES.md)
