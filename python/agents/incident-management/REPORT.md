# Incident Management Agent - Technical Documentation Report

## Project Scope

### High-Level Summary
The Incident Management Agent is a production-ready demonstration of dynamic identity propagation with ServiceNow using Google Cloud's Application Integration Connectors and ADK. This agent showcases how to build secure, enterprise-grade integrations that pass end-user credentials at runtime rather than using hardcoded service accounts, enabling proper authentication, authorization, and audit trails for ServiceNow operations.

### Core Capabilities
- Dynamic identity propagation with OAuth2 authentication
- CRUD operations on ServiceNow Incidents table
- Real-time incident creation with user confirmation
- Incident retrieval and listing with formatted output
- Per-request credential validation
- Seamless integration with ADK Web UI authentication flow
- Zero hardcoded credentials in agent code

### Primary Use Cases
- Employee self-service IT incident reporting
- Automated incident management and tracking
- Customer support ticket creation
- IT helpdesk automation
- Enterprise service management workflows
- Multi-user incident handling with proper attribution

### Target Users
- Enterprise IT teams building ServiceNow integrations
- Developers implementing secure agent-based workflows
- IT support organizations automating incident management
- Platform engineers requiring dynamic authentication
- Teams migrating from service account to user identity patterns

### Key Innovations/Differentiators
- Dynamic identity propagation (no hardcoded credentials)
- Runtime user authentication with OAuth2
- Integration Connectors as ADK tools pattern
- Security-first design with per-request validation
- Reusable pattern for 150+ first/third-party service integrations
- Production-ready authentication flow with Web UI
- Demonstrates enterprise security best practices

## Technical Architecture

### Multi-Agent Hierarchy

```
┌────────────────────────────────────────────────────────────┐
│                    snow_agent (Root)                        │
│                    (Single Agent System)                    │
│  - Model: gemini-2.5-pro                                   │
│  - Description: ServiceNow incident management             │
│  - Tools: [snow_connector_tool]                            │
└────────────────┬───────────────────────────────────────────┘
                 │
                 └─── snow_connector_tool
                      (ApplicationIntegrationToolset)
                      │
                      ├─── Connection Details
                      │    - Project: SNOW_CONNECTION_PROJECT_ID
                      │    - Location: SNOW_CONNECTION_REGION
                      │    - Connection: SNOW_CONNECTION_NAME
                      │
                      ├─── Supported Operations
                      │    - Incident.GET (sys_id → incident details)
                      │    - Incident.LIST (query → incident list)
                      │    - Incident.CREATE (payload → new incident)
                      │
                      └─── Authentication
                           - OAuth2 with authorization code flow
                           - Dynamic user credentials
                           - No service account

AUTHENTICATION FLOW:

┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│             │         │              │         │              │
│  End User   │────────▶│  ADK Web UI  │────────▶│  ServiceNow  │
│             │         │              │         │   OAuth      │
│             │◀────────│  OAuth Flow  │◀────────│   Endpoint   │
└─────────────┘         └──────────────┘         └──────────────┘
                               │
                               ├─── 1. User triggers incident operation
                               ├─── 2. ADK detects OAuth2 requirement
                               ├─── 3. Redirect to ServiceNow login
                               ├─── 4. User authenticates with their credentials
                               ├─── 5. ServiceNow returns authorization code
                               ├─── 6. ADK exchanges code for access token
                               └─── 7. Token used for API request

INTEGRATION CONNECTOR ARCHITECTURE:

┌────────────────────────────────────────────────────────────┐
│              Application Integration Connector             │
│  (Deployed in Google Cloud Project)                        │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │  ServiceNow Connection                           │    │
│  │  - Instance: dev12345.service-now.com            │    │
│  │  - Auth: OAuth2 with client credentials          │    │
│  │  - Entities: Incident                            │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Entity Definitions                              │    │
│  │  - Incident.GET(sys_id)                          │    │
│  │  - Incident.LIST(query_params)                   │    │
│  │  - Incident.CREATE(incident_payload)             │    │
│  └──────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ApplicationIntegrationToolset
                    (Exposes as ADK Tool)
```

### Code Flow Explanation

**Tool Initialization (Lines 97-106 in /home/user/adk-samples/python/agents/incident-management/incident_management/snow_connector_tool.py)**
1. Load environment variables from .env file (line 25)
2. Configure OAuth2 scheme with ServiceNow endpoints (lines 76-86):
   - Authorization URL: `https://{instance}.service-now.com/oauth_auth.do`
   - Token URL: `https://{instance}.service-now.com/oauth_token.do`
   - Scopes: Configured via SNOW_OAUTH_SCOPES
3. Create OAuth2 credential with client ID/secret (lines 88-95)
4. Initialize ApplicationIntegrationToolset (lines 97-106):
   - Connects to Integration Connector in GCP
   - Defines entity operations: Incident [GET, LIST, CREATE]
   - Attaches OAuth2 authentication
   - Includes tool instructions for agent

**Agent Initialization (Lines 19-25 in /home/user/adk-samples/python/agents/incident-management/incident_management/agent.py)**
1. Import snow_connector_tool
2. Create root_agent as simple Agent (not LlmAgent)
3. Configure with:
   - Name: 'snow_agent'
   - Model: 'gemini-2.5-pro'
   - Tools: [snow_connector_tool]
   - Instruction: Help with ServiceNow incidents

**Runtime Flow - Create Incident**
1. User: "I would like to create an incident, my laptop has crashed multiple times today and I need help. This is urgent and should be addressed ASAP"
2. Agent analyzes request and extracts information:
   - Description: "My laptop has crashed multiple times today..."
   - Short description: "Laptop crashing multiple times"
   - Impact: 1 (High - deduced from "urgent")
   - Urgency: 1 (High - deduced from "ASAP")
3. Agent presents summary and requests confirmation (per tool instructions lines 67-68)
4. User: "Yes"
5. OAuth2 authentication flow:
   - ADK Web UI detects OAuth2 requirement from tool
   - User redirected to ServiceNow login (popup)
   - User authenticates with their ServiceNow credentials
   - ServiceNow returns authorization code
   - ADK exchanges code for access token
6. Agent calls tool_snow_Incident_CREATE with:
   - Access token (user's identity)
   - Incident payload
7. Integration Connector forwards to ServiceNow API
8. ServiceNow creates incident under user's identity
9. Agent receives response with sys_id
10. Agent confirms creation and provides incident ID

**Runtime Flow - Get Incident**
1. User: "Can you provide more details about Incident ID xxx?"
2. Agent calls tool_snow_Incident_GET with sys_id
3. OAuth2 token reused (or refreshed if expired)
4. Agent receives full incident data
5. Agent formats output per instructions (lines 46-51):
   - Incident Number
   - Description
   - Ticket Creator (shows actual user who created it)
   - Time of Creation

### Agent Definitions with Roles and Responsibilities

| Agent Name | Type | File Location | Model | Tools | Responsibilities |
|------------|------|---------------|-------|-------|------------------|
| `snow_agent` | Agent | incident_management/agent.py:19-25 | gemini-2.5-pro | snow_connector_tool | Manages ServiceNow incident operations, guides users through incident creation, retrieves and formats incident information |

**Tool Configuration:**
```python
snow_connector_tool = ApplicationIntegrationToolset(
    project=SNOW_CONNECTION_PROJECT_ID,
    location=SNOW_CONNECTION_REGION,
    connection=SNOW_CONNECTION_NAME,
    entity_operations={"Incident": ["GET","LIST","CREATE"]},
    tool_name_prefix="tool_snow",
    tool_instructions=TOOL_INSTR,
    auth_credential=oauth2_credential,
    auth_scheme=oauth2_scheme,
)
```

### Key Libraries and Dependencies

**Core Dependencies**
- `google-adk` - Agent Development Kit framework
- `google-adk.tools.application_integration_tool` - Integration Connector toolset
- `google-adk.auth` - OAuth2 authentication support
- `poetry` - Dependency management
- `python-dotenv` - Environment variable loading
- Python 3.12+ required

**Google Cloud Dependencies**
- Application Integration API
- Integration Connectors API
- Secret Manager API (for credentials)
- Cloud Storage API (for deployment)

**FastAPI Dependencies**
- `fastapi.openapi.models.OAuth2` - OAuth2 flow definitions
- `fastapi.openapi.models.OAuthFlowAuthorizationCode` - Authorization code flow

### Tools and Integrations

**ApplicationIntegrationToolset Features**
- Automatic tool generation from connection schema
- Entity operation mapping (GET, LIST, CREATE, UPDATE, DELETE)
- OAuth2 credential management
- Dynamic schema discovery
- Built-in error handling
- Token refresh management

**ServiceNow Integration**
- OAuth2 authorization code flow
- Incident table operations
- Custom scope configuration
- Instance-specific endpoints
- Field mapping and validation

**Supported Operations (Lines 101 in snow_connector_tool.py)**
```python
entity_operations = {
    "Incident": ["GET", "LIST", "CREATE"]
}
```

Generates tools:
- `tool_snow_Incident_GET(sys_id: str)` - Retrieve specific incident
- `tool_snow_Incident_LIST(query: dict)` - List incidents matching criteria
- `tool_snow_Incident_CREATE(incident: dict)` - Create new incident

**Available Integration Connectors**
The ApplicationIntegrationToolset pattern works with 150+ connectors including:
- Salesforce
- Jira
- GitHub
- Slack
- Box
- And many more

### Reasoning Mechanisms

**Tool Instructions (Lines 36-73 in snow_connector_tool.py)**

The agent follows structured instructions embedded in the tool:

1. **Incident Creation Flow:**
   - Collect minimal information (description, short_description, impact, urgency)
   - Deduce appropriate severity levels from user language
   - Present summary to user before execution
   - Request explicit confirmation
   - Provide incident ID for tracking

2. **Incident Retrieval Flow:**
   - Accept sys_id from user
   - Call GET operation
   - Format output with specific fields:
     - Number (user-friendly ID)
     - Description
     - Creator (shows dynamic identity)
     - Creation timestamp

**Impact and Urgency Mapping:**
```
User Language → Severity Level
"critical", "urgent", "ASAP" → Impact: 1, Urgency: 1 (High)
"important", "soon" → Impact: 2, Urgency: 2 (Medium)
"minor", "when possible" → Impact: 3, Urgency: 3 (Low)
```

## Build & Run Instructions

### Prerequisites

**Required Software**
- Python 3.12 or higher
- Poetry for dependency management
- Google Cloud SDK (gcloud)

**Required Accounts and Permissions**
- Google Cloud Project with these roles:
  - Application Integration Admin
  - Connector Admin
  - Secret Manager Admin
  - Storage Admin
  - Service Usage Consumer
  - Logs Viewer
- ServiceNow Developer Instance or production instance
- ServiceNow OAuth application configured

**Required APIs**
```bash
export PROJECT_ID=your-project-id
gcloud services enable aiplatform.googleapis.com \
  compute.googleapis.com \
  connectors.googleapis.com \
  secretmanager.googleapis.com \
  --project "$PROJECT_ID"
```

### Step-by-Step Installation

**1. Provision Application Integration and Integration Connectors**

This project requires Application Integration infrastructure. Follow the quickstart:

[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.png)](https://ssh.cloud.google.com/cloudshell/open?cloudshell_git_repo=https://github.com/GoogleCloudPlatform/application-integration-samples&cloudshell_git_branch=main&cloudshell_workspace=.&cloudshell_tutorial=src/adk-incident-management/docs/cloudshell-tutorial.md)

This will:
- Provision Application Integration in your project
- Create ServiceNow Integration Connector
- Deploy connection with OAuth2 configuration
- Set up required secrets in Secret Manager

**2. Install Poetry**
```bash
pip install poetry
```

For Linux users encountering keyring errors:
```bash
poetry config keyring.enabled false
```

**3. Clone and Setup Repository**
```bash
git clone https://github.com/google/adk-samples.git
cd python/agents/incident-management
poetry install
```

**4. Configure Environment Variables**

Copy `.env.example` to `.env` and configure:
```bash
# ServiceNow Connection Details (from Integration Connector)
SNOW_CONNECTION_PROJECT_ID=your-gcp-project-id
SNOW_CONNECTION_REGION=us-central1
SNOW_CONNECTION_NAME=servicenow-connection

# ServiceNow Instance
SNOW_INSTANCE_NAME=dev12345  # Your instance subdomain

# OAuth Configuration
SNOW_OAUTH_SCOPES=useraccount
SNOW_CLIENT_ID=your-client-id
SNOW_CLIENT_SECRET=your-client-secret

# ADK Web UI Configuration
AGENT_REDIRECT_URI=http://localhost:8080/dev-ui/

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_LOCATION=us-central1
```

**5. Authenticate**
```bash
gcloud auth application-default login
gcloud config set project $PROJECT_ID
```

### Configuration (Environment Variables)

**ServiceNow OAuth Setup**

In ServiceNow instance:
1. Navigate to System OAuth → Application Registry
2. Create new OAuth API endpoint
3. Set Redirect URL to: `http://localhost:8080/dev-ui/`
4. Note Client ID and Client Secret
5. Configure accessible scopes

**Integration Connector Configuration**

In Google Cloud Console:
1. Navigate to Integration Connectors
2. Find your ServiceNow connection
3. Note the connection name and region
4. Verify OAuth2 is configured
5. Test connection

### Running the Agent (CLI and Web UI)

**Web UI Mode (Recommended for OAuth)**
```bash
poetry run adk web
```

Then:
1. Select `incident-management` from dropdown
2. Ensure Redirect URL in ServiceNow matches: `http://localhost:8080/dev-ui/`
3. Start conversation

**CLI Mode (Limited - requires manual OAuth)**
```bash
poetry run adk run incident-management
```

Note: CLI mode requires manual OAuth token management. Web UI is recommended.

### Example Interactions

**Example 1: Create Incident**
```
User: hi

Agent: Hello! I'm a ServiceNow agent and can help you with getting, listing, and creating incidents. How can I help you today?

User: I would like to create an incident, my laptop has crashed multiple times today and I need help. This is urgent and should be addressed ASAP

Agent: I can help with that. I've summarized the incident details below:

Short Description: Laptop crashing multiple times
Description: My laptop has crashed multiple times today and I need help. This is urgent and should be addressed ASAP.

Impact: 1 - High

Urgency: 1 - High

Do you want me to proceed with creating the incident?

User: Yes

[OAuth Flow Triggered]
[Popup window opens for ServiceNow login]
[User signs in with their ServiceNow credentials]
[NOT system administrator - shows dynamic identity]

Agent: I have created the incident for you. The incident ID is INC0010123. A support agent will be in touch with you shortly. Can I help you with anything else?
```

**Example 2: Get Incident Details**
```
User: Yes thank you! Can you provide more details about Incident ID INC0010123?

Agent: Of course! Here are more details for Incident ID INC0010123:

Incident Number: INC0010123

Description: My laptop has crashed multiple times today and I need help. This is urgent and should be addressed ASAP.

Ticket Creator: john.doe@company.com  # Shows the actual user who created it

Time of Creation: 2024-01-15 14:23:45
```

**Example 3: List Incidents**
```
User: Show me all my open incidents

Agent: [Calls tool_snow_Incident_LIST with user filter]

Here are your open incidents:
1. INC0010123 - Laptop crashing multiple times (High priority)
2. INC0010098 - Network connectivity issues (Medium priority)
3. INC0010087 - Software installation request (Low priority)

Would you like details on any of these?
```

### Testing and Evaluation

**Manual Testing Checklist**
- [ ] OAuth flow completes successfully
- [ ] Incident created with correct user identity
- [ ] GET operation retrieves correct incident
- [ ] LIST operation filters properly
- [ ] sys_created_by field shows actual user (not service account)
- [ ] Confirmation workflow works before creation
- [ ] Error handling for invalid sys_id

**Test Different Users**
1. Create incident as User A
2. Verify User A appears as creator
3. Create incident as User B
4. Verify User B appears as creator
5. Confirms dynamic identity propagation works

**ServiceNow Verification**
```
In ServiceNow:
1. Navigate to Incident table
2. Open created incident
3. Verify "Created by" field shows end user
4. Verify "Updated by" field shows end user
5. Check audit log for user attribution
```

### Deployment (Optional)

**Cloud Run Deployment**
```bash
# Deploy backend with environment variables
gcloud run deploy incident-management-agent \
  --source . \
  --region us-central1 \
  --set-env-vars SNOW_CONNECTION_PROJECT_ID=$PROJECT_ID \
  --set-env-vars SNOW_CONNECTION_REGION=us-central1 \
  --set-env-vars AGENT_REDIRECT_URI=https://your-domain.com/callback
```

**Update ServiceNow Redirect URI**
After deployment, update ServiceNow OAuth application:
- New Redirect URI: `https://your-deployed-domain.com/dev-ui/`

### Troubleshooting

**Issue: OAuth popup doesn't appear**
- Verify AGENT_REDIRECT_URI matches exactly in:
  - .env file
  - ServiceNow OAuth application
- Check browser allows popups from localhost
- Clear browser cache and cookies

**Issue: "Connection not found" error**
```bash
# Verify connection exists
gcloud integration-connectors connections list \
  --location=$SNOW_CONNECTION_REGION \
  --project=$PROJECT_ID

# Check connection name matches .env
```

**Issue: "Invalid client" OAuth error**
- Verify SNOW_CLIENT_ID and SNOW_CLIENT_SECRET in .env
- Check ServiceNow OAuth application is active
- Ensure scopes match between .env and ServiceNow

**Issue: "User not found" in ServiceNow**
- User must exist in ServiceNow instance
- User must have appropriate roles
- Test with ServiceNow system administrator first

**Issue: Integration Connector not working**
```bash
# Test connection directly
gcloud integration-connectors connections describe \
  $SNOW_CONNECTION_NAME \
  --location=$SNOW_CONNECTION_REGION \
  --project=$PROJECT_ID

# Check connection status
# Status should be "ACTIVE"
```

**Issue: Poetry installation fails**
```bash
# Linux users: Disable keyring
poetry config keyring.enabled false

# Install again
poetry install
```

## Customization Options

### 1. Add More ServiceNow Operations

**File:** `/home/user/adk-samples/python/agents/incident-management/incident_management/snow_connector_tool.py`

Extend entity operations to support UPDATE and DELETE:
```python
snow_connector_tool = ApplicationIntegrationToolset(
    project=SNOW_CONNECTION_PROJECT_ID,
    location=SNOW_CONNECTION_REGION,
    connection=SNOW_CONNECTION_NAME,
    entity_operations={
        "Incident": ["GET", "LIST", "CREATE", "UPDATE", "DELETE"]
    },
    tool_name_prefix="tool_snow",
    tool_instructions=EXTENDED_TOOL_INSTR,  # Updated instructions
    auth_credential=oauth2_credential,
    auth_scheme=oauth2_scheme,
)
```

Update tool instructions:
```python
EXTENDED_TOOL_INSTR = TOOL_INSTR + """

**Incident Update:**

If the user asks to update an incident:
    1. Collect the sys_id of incident to update
    2. Collect fields to modify (e.g., state, priority, assignment_group)
    3. Present summary of changes
    4. Request confirmation
    5. Call UPDATE operation
    6. Confirm update with updated field values

**Incident Deletion:**

If the user asks to delete/close an incident:
    1. Collect sys_id
    2. Warn about permanent deletion
    3. Request explicit confirmation with "DELETE" keyword
    4. Call DELETE operation
    5. Confirm deletion
"""
```

**Impact:** Enables full CRUD operations on incidents with proper user confirmation flows.

### 2. Add Multiple ServiceNow Tables

**File:** `/home/user/adk-samples/python/agents/incident-management/incident_management/snow_connector_tool.py`

Support multiple entities beyond Incidents:
```python
snow_connector_tool = ApplicationIntegrationToolset(
    project=SNOW_CONNECTION_PROJECT_ID,
    location=SNOW_CONNECTION_REGION,
    connection=SNOW_CONNECTION_NAME,
    entity_operations={
        "Incident": ["GET", "LIST", "CREATE", "UPDATE"],
        "Problem": ["GET", "LIST", "CREATE"],
        "ChangeRequest": ["GET", "LIST", "CREATE"],
        "User": ["GET", "LIST"],
        "Asset": ["GET", "LIST"]
    },
    tool_name_prefix="tool_snow",
    tool_instructions=MULTI_ENTITY_INSTR,
    auth_credential=oauth2_credential,
    auth_scheme=oauth2_scheme,
)
```

This generates tools like:
- `tool_snow_Incident_GET`
- `tool_snow_Problem_CREATE`
- `tool_snow_ChangeRequest_LIST`
- `tool_snow_User_GET`
- `tool_snow_Asset_LIST`

**Impact:** Creates comprehensive ServiceNow agent supporting multiple workflows.

### 3. Implement Approval Workflows

**File:** Create `/home/user/adk-samples/python/agents/incident-management/incident_management/approval_workflow.py`

Add multi-step approval for high-impact incidents:
```python
from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner

approval_agent = LlmAgent(
    name="approval_checker",
    model="gemini-2.5-flash",
    instruction="""
    You are an approval workflow manager. For high-impact incidents:
    1. Check if requestor is authorized to create high-priority incidents
    2. Verify business justification is provided
    3. Request manager approval if needed
    4. Log approval decision
    """,
    output_key="approval_decision"
)

# Integrate into main agent
from google.adk.agents import SequentialAgent

enhanced_snow_agent = SequentialAgent(
    name="incident_management_with_approval",
    sub_agents=[
        approval_agent,
        original_snow_agent
    ]
)
```

**Impact:** Adds governance and compliance workflows for incident creation.

### 4. Add Slack Notifications

**File:** Create `/home/user/adk-samples/python/agents/incident-management/incident_management/slack_notifier.py`

Notify Slack when incidents are created:
```python
from google.adk.tools import Tool
from pydantic import BaseModel
import requests

class SlackNotification(BaseModel):
    channel: str
    message: str
    incident_id: str

def notify_slack(channel: str, message: str, incident_id: str) -> str:
    """Send Slack notification for new incident."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    payload = {
        "channel": channel,
        "text": f"🚨 New Incident Created: {incident_id}",
        "attachments": [{
            "color": "danger",
            "fields": [{
                "title": "Description",
                "value": message,
                "short": False
            }]
        }]
    }

    response = requests.post(webhook_url, json=payload)
    return f"Slack notification sent to {channel}"

slack_tool = Tool(
    name="notify_slack",
    description="Send Slack notification for incident",
    input_schema=SlackNotification,
    function=notify_slack
)

# Add to agent
root_agent = Agent(
    name='snow_agent',
    tools=[snow_connector_tool, slack_tool],
    instruction="""Help with ServiceNow incidents.
    After creating high-priority incidents, notify #it-support channel on Slack."""
)
```

**Impact:** Enables real-time team notifications for incident management.

### 5. Add Incident Analytics

**File:** Create `/home/user/adk-samples/python/agents/incident-management/incident_management/analytics.py`

Provide analytics on incident trends:
```python
from google.adk.tools import Tool
from datetime import datetime, timedelta

def analyze_incidents(days: int = 7) -> str:
    """Analyze incident trends over specified days."""
    # Use LIST operation to fetch recent incidents
    # This is pseudocode - actual implementation would use the tool

    incidents = tool_snow_Incident_LIST({
        "sysparm_query": f"sys_created_on>={days}daysago",
        "sysparm_fields": "priority,state,category,sys_created_on"
    })

    analysis = {
        "total": len(incidents),
        "by_priority": {},
        "by_category": {},
        "avg_resolution_time": 0
    }

    # Process incidents
    for inc in incidents:
        priority = inc.get("priority", "Unknown")
        analysis["by_priority"][priority] = \
            analysis["by_priority"].get(priority, 0) + 1

    return f"""
    Incident Analytics (Last {days} days):
    - Total Incidents: {analysis['total']}
    - By Priority: {analysis['by_priority']}
    - Most common category: {max(analysis['by_category'])}
    """

analytics_tool = Tool(
    name="analyze_incidents",
    description="Analyze incident trends and patterns",
    function=analyze_incidents
)
```

**Impact:** Provides insights for capacity planning and process improvement.

### 6. Implement Role-Based Access Control

**File:** `/home/user/adk-samples/python/agents/incident-management/incident_management/rbac.py`

Add role-based restrictions:
```python
from google.adk.plugins import BasePlugin
from google.adk.tools import BaseTool
from typing import Any

class RBACPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="rbac_plugin")
        self.role_permissions = {
            "end_user": ["GET", "CREATE"],
            "support_agent": ["GET", "LIST", "CREATE", "UPDATE"],
            "admin": ["GET", "LIST", "CREATE", "UPDATE", "DELETE"]
        }

    def get_user_role(self, user_email: str) -> str:
        """Determine user role from email domain or directory service."""
        # In production, query Google Workspace Admin SDK or similar
        if "admin" in user_email:
            return "admin"
        elif "support" in user_email:
            return "support_agent"
        else:
            return "end_user"

    async def before_tool_callback(
        self,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context
    ):
        """Check if user has permission for this operation."""
        user_email = tool_context.user_id  # From OAuth
        user_role = self.get_user_role(user_email)

        # Extract operation from tool name (e.g., "tool_snow_Incident_DELETE")
        operation = tool.name.split("_")[-1]

        allowed_ops = self.role_permissions.get(user_role, [])

        if operation not in allowed_ops:
            return {
                "error": f"Access denied: Role '{user_role}' cannot perform '{operation}'"
            }

        return None  # Allow

# Attach to Runner
runner = Runner(
    app_name="incident-management",
    agent=root_agent,
    plugins=[RBACPlugin()]
)
```

**Impact:** Implements enterprise security with role-based operation restrictions.

### 7. Support Other Integration Connectors

**File:** Create `/home/user/adk-samples/python/agents/incident-management/incident_management/multi_connector.py`

Combine multiple connectors for cross-system workflows:
```python
# Jira Connector
jira_tool = ApplicationIntegrationToolset(
    project=PROJECT_ID,
    location=REGION,
    connection="jira-connection",
    entity_operations={"Issue": ["GET", "LIST", "CREATE"]},
    tool_name_prefix="tool_jira",
    auth_credential=jira_oauth2_credential,
    auth_scheme=jira_oauth2_scheme
)

# Salesforce Connector
salesforce_tool = ApplicationIntegrationToolset(
    project=PROJECT_ID,
    location=REGION,
    connection="salesforce-connection",
    entity_operations={"Case": ["GET", "LIST", "CREATE"]},
    tool_name_prefix="tool_sfdc",
    auth_credential=sfdc_oauth2_credential,
    auth_scheme=sfdc_oauth2_scheme
)

# Multi-system agent
multi_system_agent = Agent(
    name="enterprise_ticket_manager",
    model="gemini-2.5-pro",
    tools=[snow_connector_tool, jira_tool, salesforce_tool],
    instruction="""
    You manage tickets across multiple systems:
    - ServiceNow for IT incidents
    - Jira for engineering issues
    - Salesforce for customer cases

    Route requests to the appropriate system based on context.
    Create linked tickets when needed across systems.
    """
)
```

**Impact:** Creates unified agent for multi-system enterprise workflows.

---

**Additional Resources:**
- Application Integration Documentation: https://cloud.google.com/application-integration/docs
- Integration Connectors Catalog: https://cloud.google.com/integration-connectors/docs/all-integration-connectors
- ServiceNow Developer: https://developer.servicenow.com/
- ADK Documentation: https://google.github.io/adk-docs/
- Application Integration Samples: https://github.com/GoogleCloudPlatform/application-integration-samples
