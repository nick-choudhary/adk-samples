# Usage Examples - Outbound Automation System

Real-world examples and use cases for the Outbound Automation System.

## Table of Contents
- [Getting Started](#getting-started)
- [Use Case 1: B2B SaaS Outreach](#use-case-1-b2b-saas-outreach)
- [Use Case 2: Local Business Lead Generation](#use-case-2-local-business-lead-generation)
- [Use Case 3: Enterprise Sales Campaign](#use-case-3-enterprise-sales-campaign)
- [Use Case 4: Event Promotion](#use-case-4-event-promotion)
- [Use Case 5: Multi-Channel Drip Campaign](#use-case-5-multi-channel-drip-campaign)
- [Advanced Examples](#advanced-examples)
- [Best Practices](#best-practices)

## Getting Started

### Prerequisites

1. **API Access**: Obtain JWT token (see [API.md](./API.md#authentication))
2. **Environment**: Local or production setup (see [SETUP.md](./SETUP.md))
3. **API Keys**: Configure external services in `.env`

### Basic Workflow

```
1. Create Campaign → 2. Extract Leads → 3. Review Leads → 4. Launch Outreach → 5. Monitor Results
```

## Use Case 1: B2B SaaS Outreach

**Goal**: Find and contact CTOs at mid-size tech companies to promote a cloud security SaaS product.

### Step 1: Create Campaign

```python
import requests

BASE_URL = "http://localhost:8080"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create campaign
campaign = {
    "name": "Cloud Security SaaS - Q1 2025",
    "target_industries": [
        "Technology",
        "SaaS",
        "Cloud Computing",
        "Cybersecurity"
    ],
    "target_titles": [
        "CTO",
        "VP Engineering",
        "Head of Security",
        "CISO"
    ],
    "company_size": "100-1000",
    "geography": "United States",
    "sources": ["apollo", "linkedin"],
    "min_score": 75
}

response = requests.post(
    f"{BASE_URL}/api/campaigns",
    json=campaign,
    headers=headers
)

campaign_data = response.json()
campaign_id = campaign_data["id"]
print(f"Campaign created: {campaign_id}")
```

### Step 2: Extract Leads

```python
# Start lead extraction
extraction = {
    "campaign_id": campaign_id,
    "target_count": 500,
    "sources": ["apollo", "linkedin"],
    "filters": {
        "industries": ["Technology", "SaaS", "Cloud Computing"],
        "titles": ["CTO", "VP Engineering", "Head of Security", "CISO"],
        "company_size": "100-1000",
        "geography": "United States",
        "exclude_domains": ["gmail.com", "yahoo.com", "hotmail.com"],
        "technologies": ["AWS", "Azure", "GCP"],  # Companies using cloud
        "funding_stage": ["Series A", "Series B", "Series C"]
    }
}

response = requests.post(
    f"{BASE_URL}/api/leads/extract",
    json=extraction,
    headers=headers
)

job = response.json()
job_id = job["job_id"]
print(f"Extraction started: {job_id}")
```

### Step 3: Monitor Extraction

```python
import time

# Poll job status
while True:
    response = requests.get(
        f"{BASE_URL}/api/leads/job/{job_id}",
        headers=headers
    )

    job_status = response.json()
    print(f"Progress: {job_status['progress']}% - {job_status['extracted_count']} leads")

    if job_status['status'] == 'completed':
        print("Extraction complete!")
        break
    elif job_status['status'] == 'failed':
        print(f"Extraction failed: {job_status.get('error')}")
        break

    time.sleep(10)  # Wait 10 seconds before checking again
```

### Step 4: Review Top Leads

```python
# Get high-scoring leads
response = requests.get(
    f"{BASE_URL}/api/campaigns/{campaign_id}/leads?min_score=85&limit=20",
    headers=headers
)

top_leads = response.json()

print(f"\nTop {len(top_leads)} leads:")
for lead in top_leads:
    print(f"- {lead['name']} ({lead['title']}) at {lead['company']} - Score: {lead['score']}")
```

### Step 5: Launch Outreach

```python
# Multi-step email sequence
outreach = {
    "campaign_id": campaign_id,
    "channels": ["email", "linkedin"],
    "schedule": {
        "sequence": [
            {
                "day": 0,
                "channel": "email",
                "template": "intro",
                "subject": "Quick question about {{company}}'s cloud security",
                "personalization": {
                    "value_proposition": "reducing cloud security incidents by 40%",
                    "pain_point": "cloud misconfigurations"
                }
            },
            {
                "day": 3,
                "channel": "linkedin",
                "action": "connect",
                "message": "Hi {{first_name}}, I noticed {{company}} is using {{technology}}. We help similar companies improve cloud security..."
            },
            {
                "day": 7,
                "channel": "email",
                "template": "follow_up_1",
                "subject": "Re: Cloud security at {{company}}",
                "personalization": {
                    "case_study": "How TechCorp reduced incidents by 40%"
                }
            },
            {
                "day": 14,
                "channel": "email",
                "template": "follow_up_2",
                "subject": "Final follow-up: {{company}}'s cloud security",
                "personalization": {
                    "offer": "Free security audit (limited time)"
                }
            }
        ],
        "send_time": "09:00-17:00",
        "timezone": "America/New_York",
        "send_days": ["Monday", "Tuesday", "Wednesday", "Thursday"]
    }
}

response = requests.post(
    f"{BASE_URL}/api/outreach/start",
    json=outreach,
    headers=headers
)

print(f"Outreach started: {response.json()}")
```

### Step 6: Monitor Performance

```python
import time

# Monitor campaign stats every hour
while True:
    response = requests.get(
        f"{BASE_URL}/api/campaigns/{campaign_id}/stats",
        headers=headers
    )

    stats = response.json()

    print(f"\n--- Campaign Stats ---")
    print(f"Total Leads: {stats['total_leads']}")
    print(f"Contacted: {stats['contacted']}")
    print(f"Email Open Rate: {stats['email_open_rate']}%")
    print(f"Response Rate: {stats['response_rate']}%")
    print(f"Conversions: {stats['converted']}")
    print(f"Conversion Rate: {stats['conversion_rate']}%")

    time.sleep(3600)  # Check every hour
```

### Expected Results

- **Lead Extraction**: 500 leads in ~30 minutes
- **Email Open Rate**: 25-35%
- **Response Rate**: 5-10%
- **Conversion Rate**: 2-5%
- **Total Conversions**: 10-25 qualified meetings

## Use Case 2: Local Business Lead Generation

**Goal**: Find local restaurants in New York City to promote a food delivery partnership.

### Complete Example

```python
# 1. Create campaign
campaign = {
    "name": "NYC Restaurant Partnership - Jan 2025",
    "target_industries": ["Restaurants", "Food & Beverage"],
    "target_titles": ["Owner", "Manager", "General Manager"],
    "company_size": "1-50",
    "geography": "New York, NY",
    "sources": ["google_search", "yelp"],
    "min_score": 60
}

campaign_response = requests.post(
    f"{BASE_URL}/api/campaigns",
    json=campaign,
    headers=headers
)
campaign_id = campaign_response.json()["id"]

# 2. Extract leads from Google Maps & Yelp
extraction = {
    "campaign_id": campaign_id,
    "target_count": 200,
    "sources": ["google_search", "yelp"],
    "filters": {
        "location": "New York, NY",
        "radius": "10 miles",
        "business_type": "restaurant",
        "rating": "4.0+",
        "review_count": "50+",
        "exclude_chains": True  # Focus on independent restaurants
    }
}

extract_response = requests.post(
    f"{BASE_URL}/api/leads/extract",
    json=extraction,
    headers=headers
)

# 3. Launch SMS + Phone outreach (more personal for local businesses)
outreach = {
    "campaign_id": campaign_id,
    "channels": ["sms", "call"],
    "schedule": {
        "sequence": [
            {
                "day": 0,
                "channel": "sms",
                "template": "local_intro",
                "message": "Hi {{first_name}}, I'm reaching out to {{company}} about a partnership that's helping NYC restaurants increase delivery orders by 30%. Open to a quick chat?"
            },
            {
                "day": 2,
                "channel": "call",
                "min_score": 70,
                "script": "restaurant_partnership",
                "max_duration": 300  # 5 minute calls
            },
            {
                "day": 5,
                "channel": "sms",
                "template": "follow_up",
                "message": "{{first_name}}, following up on my message about helping {{company}} with delivery. Can we chat this week?"
            }
        ],
        "send_time": "10:00-20:00",  # Restaurant business hours
        "timezone": "America/New_York",
        "send_days": ["Tuesday", "Wednesday", "Thursday"]  # Avoid Mon/Fri/weekends
    }
}

outreach_response = requests.post(
    f"{BASE_URL}/api/outreach/start",
    json=outreach,
    headers=headers
)
```

## Use Case 3: Enterprise Sales Campaign

**Goal**: Target Fortune 500 companies for a high-touch enterprise software sale.

### Strategy: Research-Heavy, Low-Volume, High-Touch

```python
# 1. Create highly targeted campaign
campaign = {
    "name": "Fortune 500 Enterprise Sales - 2025",
    "target_industries": ["Financial Services", "Healthcare", "Manufacturing"],
    "target_titles": ["Chief Digital Officer", "SVP Technology", "Head of Innovation"],
    "company_size": "5000+",
    "geography": "United States",
    "sources": ["zoominfo", "linkedin"],
    "min_score": 90  # Very high bar
}

campaign_response = requests.post(
    f"{BASE_URL}/api/campaigns",
    json=campaign,
    headers=headers
)
campaign_id = campaign_response.json()["id"]

# 2. Extract small number of highly qualified leads
extraction = {
    "campaign_id": campaign_id,
    "target_count": 50,  # Quality over quantity
    "sources": ["zoominfo", "linkedin"],
    "filters": {
        "company_revenue": "$1B+",
        "job_level": "C-Level",
        "industries": ["Financial Services", "Healthcare"],
        "company_list": [  # Target specific companies
            "JPMorgan Chase",
            "UnitedHealth Group",
            "Johnson & Johnson",
            # ... more Fortune 500 companies
        ]
    }
}

# 3. Personalized, multi-touch outreach
outreach = {
    "campaign_id": campaign_id,
    "channels": ["email", "linkedin", "call"],
    "schedule": {
        "sequence": [
            {
                "day": 0,
                "channel": "linkedin",
                "action": "connect",
                "message": "Hi {{first_name}}, I've been following {{company}}'s digital transformation initiatives..."
            },
            {
                "day": 3,
                "channel": "email",
                "template": "enterprise_intro",
                "subject": "{{company}}'s digital transformation",
                "personalization": {
                    "research_insight": "I noticed {{company}} recently {{recent_news}}",
                    "value_proposition": "We helped {{similar_company}} achieve {{specific_result}}"
                }
            },
            {
                "day": 7,
                "channel": "call",
                "min_score": 95,  # Only call the best leads
                "script": "enterprise_discovery",
                "max_duration": 900  # 15-minute calls
            },
            {
                "day": 14,
                "channel": "email",
                "template": "executive_briefing",
                "subject": "Executive briefing for {{company}}",
                "attachment": "custom_executive_brief.pdf"  # Personalized deck
            }
        ],
        "send_time": "08:00-18:00",
        "timezone": "America/New_York"
    }
}
```

### Expected Results for Enterprise

- **Lead Count**: 50 highly qualified leads
- **Response Rate**: 15-25% (higher due to personalization)
- **Meeting Rate**: 10-20%
- **Deal Size**: $100K - $1M+ ARR
- **Sales Cycle**: 3-12 months

## Use Case 4: Event Promotion

**Goal**: Promote a tech conference to software developers and CTOs.

```python
# 1. Create event campaign
campaign = {
    "name": "TechConf 2025 - Registration Drive",
    "target_industries": ["Technology", "Software"],
    "target_titles": ["Software Engineer", "CTO", "VP Engineering", "Developer"],
    "company_size": "10-1000",
    "geography": "United States, Canada",
    "sources": ["linkedin", "twitter"],
    "min_score": 65
}

# 2. Extract leads from tech community
extraction = {
    "campaign_id": campaign_id,
    "target_count": 5000,  # Large volume for event
    "sources": ["linkedin", "twitter"],
    "filters": {
        "interests": ["software development", "cloud computing", "AI"],
        "social_activity": "active",  # Active on social media
        "past_events": ["AWS re:Invent", "Google I/O", "Microsoft Build"]
    }
}

# 3. Multi-channel event promotion
outreach = {
    "campaign_id": campaign_id,
    "channels": ["email", "linkedin", "sms"],
    "schedule": {
        "sequence": [
            {
                "day": 0,
                "channel": "email",
                "subject": "You're invited: TechConf 2025 (Early bird ends soon)",
                "template": "event_invite",
                "personalization": {
                    "discount_code": "EARLY2025",
                    "discount_amount": "30%"
                }
            },
            {
                "day": 7,
                "channel": "linkedin",
                "message": "Hi {{first_name}}! Have you seen the speaker lineup for TechConf 2025? {{keynote_speakers}}. Early bird ends Friday!"
            },
            {
                "day": 14,
                "channel": "email",
                "subject": "Last chance: TechConf 2025 early bird pricing",
                "template": "event_reminder",
                "urgency": "high"
            },
            {
                "day": 15,
                "channel": "sms",
                "message": "{{first_name}}, early bird for TechConf ends TONIGHT! Save 30%: https://techconf.com/register?code=EARLY2025"
            }
        ],
        "send_time": "09:00-21:00",
        "timezone": "America/Los_Angeles"
    }
}
```

## Use Case 5: Multi-Channel Drip Campaign

**Goal**: Nurture leads over 30 days with education-focused content.

```python
# Long-term nurture sequence
outreach = {
    "campaign_id": campaign_id,
    "channels": ["email", "linkedin", "sms"],
    "schedule": {
        "sequence": [
            # Week 1: Education
            {
                "day": 0,
                "channel": "email",
                "subject": "The Ultimate Guide to {{topic}}",
                "template": "content_delivery",
                "content_type": "ebook"
            },
            {
                "day": 3,
                "channel": "linkedin",
                "message": "Hi {{first_name}}, did you get a chance to check out our guide on {{topic}}?"
            },

            # Week 2: Case Study
            {
                "day": 7,
                "channel": "email",
                "subject": "How {{similar_company}} achieved {{result}}",
                "template": "case_study",
                "social_proof": True
            },

            # Week 3: Demo Offer
            {
                "day": 14,
                "channel": "email",
                "subject": "See it in action: Live demo for {{company}}",
                "template": "demo_invite",
                "cta": "Book 15-min demo"
            },
            {
                "day": 16,
                "channel": "sms",
                "message": "{{first_name}}, we'd love to show you how {{product}} can help {{company}}. Free demo? Reply YES"
            },

            # Week 4: Final Push
            {
                "day": 21,
                "channel": "email",
                "subject": "Last call: Special offer for {{company}}",
                "template": "limited_offer",
                "urgency": "high"
            },
            {
                "day": 28,
                "channel": "call",
                "min_score": 80,
                "script": "final_outreach"
            }
        ],
        "send_time": "09:00-17:00",
        "timezone": "America/New_York",
        "a_b_test": {
            "enabled": True,
            "variants": ["subject_line_a", "subject_line_b"],
            "split": 0.5  # 50/50 split
        }
    }
}
```

## Advanced Examples

### Example 1: A/B Testing Email Subject Lines

```python
# Create two campaigns with different subject lines
campaigns = [
    {
        "name": "Test A - Question Format",
        "variant": "A",
        "subject": "Quick question about {{company}}'s {{pain_point}}?"
    },
    {
        "name": "Test B - Value Format",
        "variant": "B",
        "subject": "How {{company}} can save {{savings_amount}}"
    }
]

results = {}

for campaign_config in campaigns:
    # Create campaign
    campaign = requests.post(
        f"{BASE_URL}/api/campaigns",
        json={...},  # Campaign details
        headers=headers
    ).json()

    # Launch with 50% of leads
    # ... extraction and outreach ...

    # Track results
    stats = requests.get(
        f"{BASE_URL}/api/campaigns/{campaign['id']}/stats",
        headers=headers
    ).json()

    results[campaign_config['variant']] = stats

# Compare results
print(f"Variant A open rate: {results['A']['email_open_rate']}%")
print(f"Variant B open rate: {results['B']['email_open_rate']}%")

# Use winner for remaining leads
winner = 'A' if results['A']['email_open_rate'] > results['B']['email_open_rate'] else 'B'
print(f"Winner: Variant {winner}")
```

### Example 2: Lead Scoring Custom Logic

```python
# Get leads and apply custom scoring
response = requests.get(
    f"{BASE_URL}/api/campaigns/{campaign_id}/leads",
    headers=headers
)

leads = response.json()

# Custom scoring logic
for lead in leads:
    score = 0

    # Title score
    if lead['title'] in ['CEO', 'CTO', 'Founder']:
        score += 30
    elif lead['title'] in ['VP', 'Director']:
        score += 20
    else:
        score += 10

    # Company size score
    size = int(lead['company_size'].split('-')[0])
    if 100 <= size <= 500:
        score += 25  # Sweet spot
    elif 50 <= size < 100:
        score += 20
    else:
        score += 15

    # Email quality score
    if lead['email'] and not any(domain in lead['email'] for domain in ['gmail', 'yahoo', 'hotmail']):
        score += 20  # Work email

    # Phone score
    if lead['phone']:
        score += 15

    # Social presence score
    if lead.get('linkedin_url'):
        score += 10

    lead['custom_score'] = min(score, 100)  # Cap at 100

    print(f"{lead['name']}: {lead['custom_score']}")

# Only contact leads with custom score >= 80
high_value_leads = [l for l in leads if l['custom_score'] >= 80]
```

### Example 3: Webhook Integration for Real-Time Actions

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhooks/custom/response-handler', methods=['POST'])
def handle_response():
    """Custom webhook to handle lead responses"""
    event = request.json

    if event['event'] == 'replied':
        lead_id = event['lead_id']

        # Automatically schedule a call for hot leads
        if 'interested' in event['content'].lower() or 'yes' in event['content'].lower():
            # Schedule call
            call_data = {
                "lead_id": lead_id,
                "channel": "call",
                "priority": "high",
                "schedule_time": "next_available"
            }

            requests.post(
                f"{BASE_URL}/api/outreach/schedule-call",
                json=call_data,
                headers=headers
            )

            print(f"Hot lead! Call scheduled for {lead_id}")

        # Move to CRM for "not interested"
        elif 'not interested' in event['content'].lower():
            # Mark as uninterested, remove from campaign
            requests.post(
                f"{BASE_URL}/api/leads/{lead_id}/status",
                json={"status": "not_interested"},
                headers=headers
            )

    return {"status": "processed"}

if __name__ == '__main__':
    app.run(port=5000)
```

### Example 4: Batch Lead Import from CSV

```python
import pandas as pd

# Read CSV file
df = pd.read_csv('leads.csv')

# Create campaign first
campaign = requests.post(
    f"{BASE_URL}/api/campaigns",
    json={
        "name": "CSV Import - Jan 2025",
        "target_industries": ["Various"],
        "target_titles": ["Various"],
        "company_size": "1-10000",
        "geography": "Global",
        "sources": ["csv_upload"],
        "min_score": 0
    },
    headers=headers
).json()

campaign_id = campaign['id']

# Import leads in batches
batch_size = 100

for i in range(0, len(df), batch_size):
    batch = df[i:i+batch_size]

    leads = []
    for _, row in batch.iterrows():
        lead = {
            "campaign_id": campaign_id,
            "name": row['name'],
            "email": row['email'],
            "phone": row.get('phone'),
            "company": row['company'],
            "title": row['title'],
            "source": "csv_upload"
        }
        leads.append(lead)

    # Bulk insert
    response = requests.post(
        f"{BASE_URL}/api/leads/bulk-import",
        json={"leads": leads},
        headers=headers
    )

    print(f"Imported batch {i//batch_size + 1}: {len(leads)} leads")

print(f"Total leads imported: {len(df)}")
```

## Best Practices

### 1. Personalization

```python
# Good: Personalized message
"Hi {{first_name}}, I noticed {{company}} recently raised {{funding_amount}}. Congrats! I wanted to reach out because..."

# Bad: Generic message
"Hello, I wanted to reach out to discuss our product..."
```

### 2. Timing

```python
# Best times to send (based on data)
best_send_times = {
    "email": "09:00-11:00, 14:00-16:00",  # Mid-morning, mid-afternoon
    "linkedin": "07:00-09:00, 17:00-19:00",  # Commute times
    "sms": "10:00-20:00",  # Waking hours, not too early/late
    "call": "10:00-11:00, 14:00-15:00"  # Mid-morning, mid-afternoon
}

# Best days
best_days = ["Tuesday", "Wednesday", "Thursday"]  # Avoid Monday/Friday
```

### 3. Follow-Up Cadence

```python
# Recommended sequence timing
follow_up_schedule = {
    "Initial outreach": "Day 0",
    "First follow-up": "Day 3-4",  # Give them time to see first message
    "Second follow-up": "Day 7-10",  # One week later
    "Third follow-up": "Day 14-21",  # Two weeks later
    "Final follow-up": "Day 28-30"  # One month, then stop
}

# Don't: Email every day (too aggressive)
# Do: Space out with value between each touch
```

### 4. Compliance

```python
# Always include unsubscribe
email_footer = """
---
{{company_name}}
{{physical_address}}

Unsubscribe: {{unsubscribe_link}}
"""

# Check DNC list before outreach
response = requests.post(
    f"{BASE_URL}/api/compliance/check-dnc",
    json={"emails": [lead['email'] for lead in leads]},
    headers=headers
)

clean_leads = response.json()['allowed_contacts']
```

### 5. Lead Quality Over Quantity

```python
# Good: 100 highly qualified leads
extraction = {
    "target_count": 100,
    "min_score": 85,  # Only best leads
    "filters": {
        "job_level": "C-Level",
        "company_revenue": "$50M+"
    }
}

# Bad: 10,000 random leads
extraction = {
    "target_count": 10000,
    "min_score": 0,  # Any lead
    "filters": {}  # No filtering
}
```

### 6. Test Before Scaling

```python
# Phase 1: Small test (100 leads)
# Phase 2: Analyze results, optimize
# Phase 3: Scale to full campaign (1000+ leads)

test_campaign = {
    "name": "Test Campaign - Small Batch",
    "target_count": 100,
    # ... config ...
}

# After test, analyze:
# - Open rate
# - Response rate
# - Unsubscribe rate
# - Quality of responses

# Then scale with improvements
```

---

**More Examples?** Check out:
- [API Documentation](./API.md) - Complete API reference
- [Setup Guide](./SETUP.md) - Local development setup
- [GitHub Discussions](https://github.com/google/adk-samples/discussions) - Community examples
