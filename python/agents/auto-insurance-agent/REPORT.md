# Auto Insurance Agent - Technical Documentation Report

## Project Scope

The Auto Insurance Agent is a conversational AI system designed to serve as a virtual customer service assistant for an auto insurance company (Cymbal Auto Insurance). The agent demonstrates enterprise API integration through Apigee API Hub, enabling seamless access to organizational API catalogs as AI agent tools.

**Core Capabilities:**
- **Membership Management**: Register new insurance members and retrieve existing member account information
- **Claims Processing**: File and track auto insurance claims for accidents, hail damage, and other incidents
- **Roadside Assistance**: Dispatch emergency services including towing, jump-starting, fuel delivery, tire changes, and lockout assistance
- **Rewards Program**: Find nearby partner offers and discounts for insurance members

**Primary Use Cases:**
- Customer self-service for insurance operations
- Automated roadside emergency dispatching
- Claims intake and initial processing
- Member onboarding and registration
- Location-based rewards discovery

**Target Users:**
- Auto insurance policyholders
- Customer service representatives (agent-assisted mode)
- Insurance company operations teams
- API developers integrating insurance services

**Key Innovation:**
Demonstrates ADK's **ApiHubToolset** functionality, which allows developers to turn any OpenAPI specification from their organization's API catalog into an AI agent tool with minimal code. This bridges enterprise API management (Apigee) with conversational AI.

## Technical Architecture

### Multi-Agent Hierarchy

The system implements a **hierarchical multi-agent architecture** with one root agent and four specialized sub-agents:

```
Root Agent (Customer Service Coordinator)
    ├─→ Membership Agent (new registrations & lookups)
    ├─→ Roadside Agent (emergency assistance)
    ├─→ Claims Agent (claim filing & tracking)
    └─→ Rewards Agent (partner offers)
```

**Agent Definitions** (`auto_insurance_agent/agent.py`):

1. **Root Agent** (lines 94-111):
   - **Model**: Gemini 2.5 Flash
   - **Role**: Main customer service coordinator
   - **Global Instruction**: "Helpful virtual assistant for Cymbal Auto Insurance"
   - **Workflow**:
     1. Welcome users to Cymbal Auto Insurance
     2. Request member ID (required for most operations)
     3. Offer membership registration if not a member
     4. Look up account info using membership tool
     5. Transfer to specialized sub-agents based on request type
     6. Ask if additional help is needed after task completion
     7. Thank user upon conversation end
   - **Tools**: `membership` (for ID lookups)
   - **Sub-agents**: All four specialized agents

2. **Membership Agent** (lines 38-52):
   - **Purpose**: Register new members
   - **Workflow**:
     - Thank user for choosing to become a member
     - Collect required registration information
     - Repeat information as bullet points for confirmation
     - Create member ID using `membership` tool
     - Provide new member ID and instructions
     - Transfer back to root agent
   - **Tools**: `membership`

3. **Roadside Agent** (lines 21-36):
   - **Purpose**: Dispatch roadside assistance services
   - **Workflow**:
     - Determine type of assistance needed (tow, jump start, fuel, tire, unlock)
     - Request location (address or cross street)
     - Create tow request using `roadsideAssistance` tool
     - Provide ETA and fictional tow company name
     - Inform user they'll receive a callback
     - Transfer back to root agent
   - **Tools**: `roadsideAssistance`

4. **Claims Agent** (lines 55-75):
   - **Purpose**: Open insurance claims
   - **Workflow** (reassuring, stress-free approach):
     - Acknowledge that situations can be stressful
     - Determine if accident occurred
     - Check for injuries and get details
     - Identify which vehicle was involved
     - Assess if vehicle is still drivable
     - Collect incident and damage details
     - Get location (address/intersection for accidents)
     - Create claim using `claims` tool
     - Provide claim ID and next steps
     - Arrange replacement vehicle if needed
     - Transfer back to root agent
   - **Tools**: `claims`

5. **Rewards Agent** (lines 78-91):
   - **Purpose**: Find nearby partner rewards
   - **Workflow**:
     - Request member's current location
     - Search for nearby offers using `rewards` tool
     - Display available rewards as bullet points
     - Transfer back to root agent
   - **Tools**: `rewards`

### Apigee API Hub Integration

**Architecture Overview**:
```
ADK Agent → ApiHubToolset → Apigee API Hub → API Spec (OpenAPI)
                                              → Apigee API Proxy
                                              → Backend Service
```

**Tools Configuration** (`auto_insurance_agent/tools.py`):

1. **API Hub Connection** (lines 24-27):
   ```python
   PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
   LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
   API_HUB_LOCATION = f"projects/{PROJECT_ID}/locations/{LOCATION}/apis"
   ```

2. **Authentication Setup** (lines 29-32):
   - Retrieves API key from Google Cloud Secret Manager
   - Secret path: `projects/{PROJECT_ID}/secrets/cymbal-auto-apikey/versions/latest`
   - Uses `SecretManagerClient` for secure credential retrieval
   - Converts to auth scheme: API key in header (`x-apikey`)

3. **Tool Registration** (lines 34-68):
   Each API is wrapped as an `APIHubToolset`:
   - **membership**: `members_api` - Account management
   - **claims**: `claims_api` - Claims processing
   - **roadsideAssistance**: `roadside_api` - Emergency services
   - **rewards**: `rewards_api` - Partner offers

   Example:
   ```python
   membership = APIHubToolset(
       name="cymbal-auto-membership-api",
       description="Member Account Management API",
       apihub_resource_name=f"{API_HUB_LOCATION}/members_api",
       auth_scheme=auth_scheme,
       auth_credential=auth_credential
   )
   ```

**What is Apigee API Hub?**
- Centralized catalog for discovering and managing APIs across an organization
- Stores OpenAPI specifications, versioning, and metadata
- Enables governance and standardization
- ADK's `APIHubToolset` automatically converts specs into LLM-compatible tools

### Code Flow Example

**User Request**: "My car broke down and I need help"

1. **Root Agent**:
   - Recognizes request requires roadside assistance
   - Transfers to `roadside_agent`

2. **Roadside Agent**:
   - Asks: "What type of help? (tow, jump, fuel, tire, unlock)"
   - User: "I ran out of gas. I'm on I-70 near Kipling exit"
   - Extracts: service_type=fuel, location="I-70 eastbound near Kipling"

3. **Tool Invocation**:
   - Calls `roadsideAssistance` API via ApiHubToolset
   - API Hub resolves `roadside_api` specification
   - Executes API call to Apigee proxy
   - Returns: `{eta: "45 minutes", service_id: "12345"}`

4. **Response Generation**:
   - Agent: "I have found a company nearby. Roadside Rescue will be there in about 45 minutes. They'll call you shortly."

5. **Transfer Back**:
   - Returns to root agent
   - Root: "Is there anything else I can help you with?"

### Key Libraries and Dependencies

**Core Framework:**
- `google-adk (>=1.5.0,<2.0.0)` - Google Agent Development Kit
- `google-cloud-aiplatform[adk,agent-engines] (>=1.100.0,<2.0.0)` - Vertex AI integration

**API Hub Integration:**
- `google.adk.tools.apihub_tool.apihub_toolset.APIHubToolset` - API Hub tool wrapper
- `google.adk.tools.apihub_tool.clients.secret_client.SecretManagerClient` - Credential management
- `google.adk.tools.openapi_tool.auth.auth_helpers.token_to_scheme_credential` - Auth configuration

**Configuration:**
- `python-dotenv (>=1.1.1,<2.0.0)` - Environment variable management
- `google-cloud-secret-manager (>=2.24.0,<3.0.0)` - Secure credential storage

**Deployment:**
- `absl-py (^2.2.2)` - Command-line flags for deployment scripts

**External Dependencies:**
- **Apigee**: API gateway and proxy management
- **Apigee API Hub**: API catalog and specification storage
- **Google Cloud Secret Manager**: Secure API key storage

### Agent Reasoning Mechanism

**Root Agent Decision Logic**:
1. **Member Authentication**: Always requires member ID before specialized operations
2. **Intent Routing**: Determines which sub-agent handles the request
3. **Session Management**: Tracks conversation state across agent transfers
4. **Graceful Handoffs**: Sub-agents return to root without duplicate greetings

**Sub-Agent Behavior Pattern**:
- **No duplicate greetings**: Sub-agents skip hellos (root already greeted)
- **Focused workflows**: Each has specific step-by-step instructions
- **Silent transfers**: Return to root without additional messages
- **Information gathering**: Collect all required data before API calls

## Build & Run Instructions

### Prerequisites

1. **Python 3.12+** (required)
2. **Poetry** package manager:
   ```bash
   pip install poetry
   ```
3. **Google Cloud Project** with roles:
   - Apigee Organization Admin
   - Secret Manager Admin
   - Storage Admin
   - Service Usage Consumer
   - Logs Viewer

4. **Google Cloud SDK** (gcloud CLI):
   - Installation: https://cloud.google.com/sdk/docs/install

5. **Apigee and API Hub** provisioned in your GCP project
   - See: https://github.com/GoogleCloudPlatform/apigee-samples/tree/main/adk-auto-insurance-agent

### Step 1: Authenticate with Google Cloud

```bash
gcloud auth login
```

Enable required APIs:
```bash
gcloud services enable aiplatform.googleapis.com
```

### Step 2: Deploy API Assets (Apigee + API Hub)

**Option A: Using Cloud Shell (Recommended)**

Click to open automated tutorial:

[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.png)](https://ssh.cloud.google.com/cloudshell/open?cloudshell_git_repo=https://github.com/GoogleCloudPlatform/apigee-samples&cloudshell_git_branch=main&cloudshell_workspace=.&cloudshell_tutorial=adk-auto-insurance-agent/docs/cloudshell-tutorial.md)

This will:
1. Provision Apigee (if needed)
2. Deploy API proxies
3. Register APIs in API Hub
4. Store API keys in Secret Manager

**Option B: Manual Deployment**

Follow instructions at:
https://github.com/GoogleCloudPlatform/apigee-samples/tree/main/adk-auto-insurance-agent

### Step 3: Clone Repository and Install Dependencies

```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/auto-insurance-agent
```

**Linux users**: Disable keyring if installation fails:
```bash
poetry config keyring.enabled false
```

Install dependencies:
```bash
poetry install
```

### Step 4: Configure Environment Variables

Copy example environment file:
```bash
cp .env.example .env
```

Edit `.env`:
```bash
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1  # or your region
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket  # For Agent Engine deployment
```

**Important**: Ensure Secret Manager contains `cymbal-auto-apikey` secret (created during Apigee deployment).

### Step 5: Run the Agent Locally

**Option 1: CLI Interface**

```bash
adk run auto_insurance_agent
```

**Option 2: Web UI Interface**

```bash
adk web
```

Select `auto-insurance-agent` from the dropdown.

### Example Interaction

```
User: hi

Agent: Welcome to Cymbal Auto Insurance! How can I help you today? Do you have a member ID?

User: 37184324

Agent: Thanks, Tom! What can I help you with today?

User: My car broke down and I need help

Agent: What type of help do you need? Do you need a tow, a jump start, fuel, a tire
change, or help unlocking your vehicle? Also, can you provide me with your location?

User: I ran out of gas. I'm on eastbound I-70 near the Kipling exit

Agent: Okay, I'm creating a request for you now. I have found a company nearby who
can help. They estimate they will be there in about 45 minutes. The company is
called Roadside Rescue. They will give you a call shortly. Is there anything else
I can help you with?

User: No that's all thanks

Agent: Thank you for contacting Cymbal Auto Insurance.
```

### Step 6: Deploy to Vertex AI Agent Engine (Optional)

Install deployment dependencies:
```bash
poetry install --with deployment
```

Deploy:
```bash
python3 deployment/deploy.py
```

Output:
```
Created remote agent: projects/<PROJECT_NUMBER>/locations/<LOCATION>/reasoningEngines/<AGENT_ENGINE_ID>
```

The script automatically adds `AGENT_ENGINE_ID` to your `.env` file.

Test deployed agent:
```bash
python3 deployment/test_deployment.py
```

Interact via shell (type `quit` to exit).

### Troubleshooting

**API Hub API Not Found:**
- Verify APIs are registered in API Hub: `gcloud apihub apis list`
- Check API names match: `members_api`, `claims_api`, `roadside_api`, `rewards_api`
- Confirm API_HUB_LOCATION variable is correct

**Secret Manager Access Denied:**
- Verify service account has Secret Manager Secret Accessor role
- Confirm secret path: `projects/{PROJECT_ID}/secrets/cymbal-auto-apikey/versions/latest`
- Check secret exists: `gcloud secrets describe cymbal-auto-apikey`

**Apigee API Calls Failing:**
- Verify Apigee proxies are deployed and active
- Check API key is valid in Secret Manager
- Confirm `x-apikey` header is configured correctly
- Test Apigee endpoints manually with curl

**Poetry Keyring Errors (Linux):**
```bash
poetry config keyring.enabled false
```

## Customization Options

### 1. Add New API Tools

Register additional APIs in API Hub and add to tools.py:

```python
inventory = APIHubToolset(
    name="cymbal-auto-inventory-api",
    description="Vehicle Inventory API",
    apihub_resource_name=f"{API_HUB_LOCATION}/inventory_api",
    auth_scheme=auth_scheme,
    auth_credential=auth_credential
)
```

Add tool to relevant agent:
```python
inventory_agent = Agent(
    name="inventory_agent",
    tools=[inventory],
    ...
)
```

### 2. Customize Agent Instructions

Modify conversation flows in `agent.py`:

```python
claims_agent = Agent(
    instruction="""Custom claims workflow:
    - Ask for photos of damage
    - Request police report number if applicable
    - Offer adjuster appointment scheduling
    ..."""
)
```

### 3. Change Authentication Method

Update `tools.py` for OAuth or other auth schemes:

```python
from google.adk.tools.openapi_tool.auth.auth_helpers import token_to_scheme_credential

auth_scheme, auth_credential = token_to_scheme_credential(
    "bearer",  # OAuth 2.0
    "header",
    "Authorization",
    access_token
)
```

### 4. Add Multi-Language Support

Extend global_instruction:

```python
root_agent = Agent(
    global_instruction="""You are a helpful virtual assistant for Cymbal Auto Insurance.
    Detect the user's language and respond in their preferred language (English, Spanish, French)."""
)
```

### 5. Integrate CRM System

Add post-processing hooks to sync with customer relationship management:

```python
# After membership creation
def on_member_created(member_id, details):
    # Sync to Salesforce/HubSpot
    crm_client.create_contact(member_id, details)
```

## Architecture Benefits

**Enterprise API Integration**:
- Reuses existing API investments
- Maintains API governance through API Hub
- Centralizes authentication and versioning
- Enables rapid tool development (lines of code vs. custom implementations)

**Multi-Agent Design**:
- Separation of concerns (specialized sub-agents)
- Easier testing and maintenance
- Modular additions (new sub-agents plug in easily)
- Clear conversation flow management

**Security**:
- API keys stored in Secret Manager (not code)
- Apigee provides rate limiting and threat protection
- Centralized credential rotation
- Audit logs for all API calls

---

**Author:** David Rush (davidrush@google.com)
**License:** Apache License 2.0
**Python Version:** 3.12+
**Model:** Gemini 2.5 Flash
**Complexity:** Easy (Multi-Agent with API Hub Integration)
**Vertical:** Financial Services (Auto Insurance)
