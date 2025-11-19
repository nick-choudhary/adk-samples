# Order Processing Agent - Technical Documentation Report

## Project Scope

The Order Processing Agent is an AI-powered conversational agent that automates order management workflows with intelligent human-in-the-loop approval patterns. This sample demonstrates the integration of Google Cloud's Application Integration platform with ADK to create production-grade agentic workflows.

### Core Capabilities
- Conversational order intake and validation
- Automatic order data persistence to BigQuery
- Email confirmation system for order acknowledgments
- Intelligent human-in-the-loop approval workflow for high-quantity orders (>100 items)
- Seamless integration with Google Cloud Application Integration platform
- Real-time order status tracking

### Primary Use Cases
- E-commerce order processing automation
- Enterprise procurement systems with approval workflows
- B2B order management requiring supervisory oversight
- High-volume retail order handling with conditional approval gates

### Target Users
- E-commerce businesses requiring automated order processing
- Enterprise teams building procurement workflows
- Developers learning ADK and Application Integration patterns
- Organizations implementing AI-driven order management systems

### Key Innovations/Differentiators
- **Low-Code Integration**: Leverages Application Integration's no-code platform to create deterministic workflow tools through `ApplicationIntegrationToolset`
- **Conditional Workflow Branching**: Automatically triggers human approval for orders exceeding quantity thresholds
- **Production-Ready Pattern**: Demonstrates enterprise-grade integration between AI agents and Google Cloud services
- **Email Orchestration**: Automatic email notifications at different workflow stages
- **Deployment Flexibility**: Supports both local development and Vertex AI Agent Engine deployment

---

## Technical Architecture

### Single-Agent Architecture

This is a **single-agent** implementation with one conversational agent orchestrating the entire order processing workflow.

```
┌─────────────────────────────────────────────────────────────┐
│                    User (Conversational)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           Order Processing Agent (Gemini 2.5 Flash)         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Agent Instruction:                                   │  │
│  │  "Help the user with creating orders, leverage       │  │
│  │   the tools you have access to"                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         ApplicationIntegrationToolset                 │  │
│  │  - Invokes Application Integration workflows         │  │
│  │  - Handles order processing logic                    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Google Cloud Application Integration                │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │   BigQuery     │  │    Email     │  │  Human-in-Loop  │ │
│  │   Storage      │  │Confirmation  │  │    Approval     │ │
│  └────────────────┘  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Code Flow Explanation

**1. Agent Initialization** (`/home/user/adk-samples/python/agents/order-processing/order_processing/agent.py`, lines 19-24):
- Creates the root agent using Gemini 2.5 Flash model
- Configures the agent with conversational instructions
- Attaches the `order_processing_tool` to handle order workflows

**2. Tool Configuration** (`/home/user/adk-samples/python/agents/order-processing/order_processing/order_processing_tool.py`, lines 56-62):
- Initializes `ApplicationIntegrationToolset` with Google Cloud project details
- Configures integration name, location, and trigger information
- Embeds detailed tool instructions for order processing workflow

**3. Environment Configuration** (`/home/user/adk-samples/python/agents/order-processing/order_processing/order_processing_tool.py`, lines 19-24):
- Loads environment variables for Google Cloud project settings
- Retrieves Application Integration process name and trigger
- Establishes connection parameters for the integration platform

**4. Conversation Flow** (Defined in `order_processing_tool.py`, lines 26-54):
   - **Greeting Phase**: Agent welcomes user and offers order assistance
   - **Information Gathering**: Collects product type, quantity, customer name, and shipping address
   - **Tool Execution**: Once all data is collected, invokes ApplicationIntegrationToolset
   - **Response Handling**:
     - If status is "In Progress" → Awaits management approval (quantity > 100)
     - If status is "Success" → Order confirmed and email sent

**5. Application Integration Workflow**:
   - Receives order data from the agent tool
   - Persists order information to BigQuery
   - Sends confirmation email with order details
   - If quantity > 100: Triggers human approval workflow
   - Returns status to agent for user communication

### Agent Definitions

**Root Agent** (`agent.py`, lines 19-24):
- **Name**: `order_processing_agent`
- **Model**: Gemini 2.5 Flash
- **Role**: Primary conversational interface for order processing
- **Responsibilities**:
  - Engage with users to gather order information
  - Validate completeness of order data
  - Invoke Application Integration tool
  - Communicate order status back to users

**Tool: ApplicationIntegrationToolset** (`order_processing_tool.py`, lines 56-62):
- **Purpose**: Bridge between ADK agent and Google Cloud Application Integration
- **Configuration**:
  - Project: From `GOOGLE_CLOUD_PROJECT` environment variable
  - Location: From `GOOGLE_CLOUD_LOCATION` environment variable
  - Integration: From `APPINT_PROCESS_NAME` environment variable
  - Triggers: From `APPINT_PROCESS_TRIGGER` environment variable

### Key Libraries and Dependencies

**Core ADK Dependencies** (`pyproject.toml`, lines 12-17):
- `google-adk (>=1.5.0,<2.0.0)`: Core ADK framework for building agents
- `google-cloud-aiplatform[adk,agent-engines] (>=1.100.0,<2.0.0)`: Vertex AI integration and deployment
- `python-dotenv (>=1.1.1,<2.0.0)`: Environment variable management
- `google-cloud-secret-manager (>=2.24.0,<3.0.0)`: Secure secrets handling

**Deployment Dependencies** (`pyproject.toml`, lines 28-29):
- `absl-py (^2.2.2)`: Google's Python library for command-line flags
- `google-cloud-aiplatform`: Extended features for Agent Engine deployment

### Tools and Integrations

**1. ApplicationIntegrationToolset** (`order_processing_tool.py`, line 56):
- **Type**: Built-in ADK tool for Google Cloud Application Integration
- **Purpose**: Converts deterministic Application Integration workflows into agent-usable tools
- **Configuration**: Requires project ID, location, integration name, and trigger configuration
- **Invocation**: Automatically called by agent when order information is complete

**2. Google Cloud Application Integration**:
- **BigQuery**: Stores structured order data for analytics and record-keeping
- **Email Service**: Sends automated confirmations to customers
- **Human-in-Loop Workflow**: Routes high-value orders (quantity > 100) for manual approval
- **Process Orchestration**: Manages the end-to-end order fulfillment pipeline

### Reasoning Mechanisms

**1. Information Completeness Check** (`order_processing_tool.py`, lines 36-43):
- Agent must collect all four required fields before tool invocation:
  - Product type
  - Quantity
  - Customer name
  - Shipping address
- Prevents premature API calls and ensures data quality

**2. Status-Based Response Logic** (`order_processing_tool.py`, lines 48-53):
- **Deterministic Branching**:
  - `{"status": "In Progress"}` → Management approval required message
  - `{"status": "Success"}` → Order confirmation message
- Uses exact phrasing to maintain consistent user experience

**3. Workflow Orchestration**:
- Application Integration handles conditional logic for approval workflows
- Agent delegates complex business rules to the integration platform
- Maintains separation between conversational AI and deterministic process logic

---

## Build & Run Instructions

### Prerequisites

**Required Software**:
- **Python**: Version 3.12 or higher
- **Poetry**: Dependency management tool
  - Installation: `pip install poetry`
  - Documentation: https://python-poetry.org/docs/

**Google Cloud Requirements**:
- Active Google Cloud Project
- Required IAM Roles:
  - Application Integration Admin
  - Connector Admin
  - Secret Manager Admin
  - Storage Admin
  - Service Usage Consumer
  - Logs Viewer

**Google Cloud SDK**:
```bash
# Install from https://cloud.google.com/sdk/docs/install
gcloud auth login
```

**Enable Required APIs**:
```bash
export PROJECT_ID=<your_project_id>
gcloud services enable integrations.googleapis.com \
  connectors.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  compute.googleapis.com \
  --project "$PROJECT_ID"
```

### Step-by-Step Installation

**1. Application Integration Setup**:

Before running the agent, you must provision Application Integration and deploy the order processing workflow. Follow the comprehensive setup guide in the Application Integration Samples repository:

- **Repository**: https://github.com/GoogleCloudPlatform/application-integration-samples
- **Workflow Location**: `src/adk-order-processing`
- **Quick Setup**: Use the Cloud Shell tutorial for guided deployment

[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.png)](https://ssh.cloud.google.com/cloudshell/open?cloudshell_git_repo=https://github.com/GoogleCloudPlatform/application-integration-samples&cloudshell_git_branch=main&cloudshell_workspace=.&cloudshell_tutorial=src/adk-order-processing/docs/cloudshell-tutorial.md)

**2. Clone the ADK Samples Repository**:
```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/order-processing
```

**3. Install Dependencies**:

*Note for Linux users*: If you encounter `keyring` errors during installation:
```bash
poetry config keyring.enabled false
```

Install project dependencies:
```bash
poetry install
```

### Configuration

**Environment Variables**:

Copy the example environment file and configure:
```bash
cp .env.example .env
```

Edit `.env` with your configuration (`.env.example`, lines 2-9):
```bash
GOOGLE_CLOUD_PROJECT=<YOUR_PROJECT_ID>
GOOGLE_CLOUD_LOCATION=<YOUR_PROJECT_LOCATION>  # e.g., us-central1
GOOGLE_GENAI_USE_VERTEXAI="TRUE"
GOOGLE_CLOUD_STORAGE_BUCKET=<YOUR_STORAGE_BUCKET>

# Application Integration Configuration
APPINT_PROCESS_NAME=sample_order_processing
APPINT_PROCESS_TRIGGER=api_trigger/sample_order_processing

# Service Account for Deployment
AGENT_SERVICE_ACCOUNT=adk-order-processing@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com
```

### Running the Agent

#### CLI Interface
```bash
# Run in interactive CLI mode
adk run order_processing
```

#### Web UI
```bash
# Start the ADK web interface
adk web

# Then select 'order-processing' from the dropdown menu
```

The web UI provides a more visual chat interface for interacting with the agent.

### Example Interactions

**Scenario 1: Small Order (No Approval Required)**

```
User: Hello

Agent: Hello! How can I assist you today? I can help with creating orders.

User: I would like to order 5 Google Pixel phones please

Agent: No problem! To finalize your order for 5 Google Pixel phones, I need a little
       more information. Could you please provide:

       Your Name:
       Shipping Address:

User: Sure, my name is Test User and my Shipping Address is 15 Testing Drive

Agent: Great! Your order for 5 Google Pixel phones has been placed successfully.
       Your order will be shipped to 15 Testing Drive.
```

**Result**: Email confirmation sent immediately with order ID and details.

**Scenario 2: Large Order (Approval Required)**

```
User: Please use the same name and shipping address as last time, I would like to
      order 150 Chromebooks please

Agent: Your order for 150 Chromebooks has been placed successfully using the same
       name (Test User) and shipping address (15 Testing Drive). The order status
       is currently "In Progress".
```

**Result**: Human-in-the-loop workflow triggered. Manager receives approval request via email. Once approved, confirmation email is sent to customer.

### Testing and Evaluation

**Manual Testing**:
- Use the example interactions above to verify functionality
- Test both small and large orders (threshold: 100 items)
- Verify email delivery for confirmations and approvals
- Check BigQuery for order data persistence

**Monitor Application Integration**:
```bash
# View integration logs
gcloud logging read "resource.type=integrations.googleapis.com" \
  --project="$PROJECT_ID" \
  --limit=50
```

### Deployment

#### Prerequisites for Agent Engine Deployment

**1. Create Service Account**:
```bash
PROJECT_ID=<your_project_id>

gcloud iam service-accounts create "adk-order-processing" \
  --project "$PROJECT_ID"
```

**2. Assign Required Roles**:
```bash
# Vertex AI User role
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:adk-order-processing@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Application Integration Invoker role
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:adk-order-processing@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/integrations.integrationEditor"
```

**3. Update .env File**:
Add the service account email to your `.env` file:
```bash
AGENT_SERVICE_ACCOUNT=adk-order-processing@${PROJECT_ID}.iam.gserviceaccount.com
```

#### Deploy to Vertex AI Agent Engine

**1. Install Deployment Dependencies**:
```bash
poetry install --with deployment
```

**2. Run Deployment Script** (`deployment/deploy.py`, lines 15-88):
```bash
python3 deployment/deploy.py
```

The deployment process (`deploy.py`, lines 61-81):
- Creates an `AdkApp` from the root agent
- Packages the agent code and dependencies
- Deploys to Vertex AI Agent Engine with the specified service account
- Updates `.env` with the `AGENT_ENGINE_ID`

**Expected Output**:
```
Created remote agent: projects/<PROJECT_NUMBER>/locations/<LOCATION>/reasoningEngines/<AGENT_ENGINE_ID>
```

**3. Test Remote Deployment**:
```bash
python3 deployment/test_deployment.py
```

This creates an interactive CLI session with the deployed agent.

### Troubleshooting

**Issue: Application Integration not found**
- Verify `APPINT_PROCESS_NAME` and `APPINT_PROCESS_TRIGGER` in `.env`
- Ensure Application Integration workflow is deployed
- Check region matches between agent and integration

**Issue: Permission denied errors**
- Verify IAM roles are assigned to your user account
- For deployment, ensure service account has correct permissions
- Check that APIs are enabled in your project

**Issue: Email not received**
- Verify email address configuration in Application Integration
- Check spam folder
- Review Application Integration execution logs

**Issue: Poetry keyring errors (Linux)**
```bash
poetry config keyring.enabled false
```

**Issue: BigQuery access denied**
- Ensure Application Integration service account has BigQuery permissions
- Verify dataset and table exist
- Check firewall rules for BigQuery API

---

## Customization Options

### 1. Modify Order Quantity Threshold for Approvals

**Location**: Application Integration workflow configuration

**What to Change**: Currently, orders with quantity > 100 trigger human approval. You can modify this threshold in your Application Integration workflow:

1. Open Google Cloud Console → Application Integration
2. Navigate to your `sample_order_processing` integration
3. Locate the conditional branching task that checks order quantity
4. Modify the comparison value (e.g., change 100 to 50 or 200)
5. Republish the integration

**Impact**: Adjusts which orders require management approval, enabling tighter or looser control based on business needs.

### 2. Customize Agent Instructions and Conversation Flow

**Location**: `/home/user/adk-samples/python/agents/order-processing/order_processing/order_processing_tool.py`, lines 26-54

**What to Change**: Modify the `TOOL_INSTR` string to alter agent behavior:

```python
TOOL_INSTR = """
      **Tool Instructions: Order Processing**
        You are an order processing assistant with premium service standards.

        Your operational flow must follow these steps:

        1. Greet the User:
          - Provide a warm, personalized greeting
          - Offer to check order history or create new orders

        2. Information Gathering:
          - Collect: product, quantity, name, shipping address
          - Ask for preferred delivery date (new field)
          - Offer express shipping options

        3. Tool Execution:
          - Submit order with additional delivery preferences

        4. Status Communication:
          - For "In Progress": Provide estimated approval timeline
          - For "Success": Include order tracking number
"""
```

**Impact**: Changes the conversational style, adds new data collection fields, or modifies status messages.

### 3. Add Product Catalog Validation

**Location**: Create a new validation tool in `order_processing/product_validator.py`

**Implementation**:
```python
from google.adk.tools import FunctionTool

def validate_product(product_name: str) -> dict:
    """Validate if product exists in catalog."""
    valid_products = [
        "Google Pixel",
        "Chromebook",
        "Pixel Tablet",
        "Pixel Watch"
    ]

    if product_name in valid_products:
        return {"valid": True, "message": f"{product_name} is available"}
    else:
        return {
            "valid": False,
            "message": f"{product_name} not found. Available: {', '.join(valid_products)}"
        }

product_validator = FunctionTool(func=validate_product)
```

**Update agent.py**:
```python
from .product_validator import product_validator

root_agent = Agent(
    model='gemini-2.5-flash',
    name='order_processing_agent',
    instruction="Help the user with creating orders. Validate products before processing.",
    tools=[order_processing_tool, product_validator],
)
```

**Impact**: Prevents invalid product orders and provides immediate feedback to users.

### 4. Switch to a Different Language Model

**Location**: `/home/user/adk-samples/python/agents/order-processing/order_processing/agent.py`, line 20

**What to Change**: Replace the model specification:

```python
# Original
root_agent = Agent(
    model='gemini-2.5-flash',
    name='order_processing_agent',
    instruction="Help the user with creating orders, leverage the tools you have access to",
    tools=[order_processing_tool],
)

# Enhanced with Gemini Pro for better reasoning
root_agent = Agent(
    model='gemini-2.5-pro',  # More capable, higher cost
    name='order_processing_agent',
    instruction="Help the user with creating orders, leverage the tools you have access to",
    tools=[order_processing_tool],
)
```

**Available Models**:
- `gemini-2.5-flash`: Fast, cost-effective (current)
- `gemini-2.5-pro`: Advanced reasoning, higher quality
- `gemini-1.5-flash`: Previous generation, budget option

**Impact**: Balance between response quality, latency, and cost based on use case requirements.

### 5. Add Multi-Language Support

**Location**: `/home/user/adk-samples/python/agents/order-processing/order_processing/agent.py`, line 22

**What to Change**: Enhance the agent instruction to support multiple languages:

```python
root_agent = Agent(
    model='gemini-2.5-flash',
    name='order_processing_agent',
    instruction="""You are a multilingual order processing assistant.

    - Detect the user's language from their first message
    - Respond in the same language throughout the conversation
    - Supported languages: English, Spanish, French, German, Japanese
    - Help users create orders by gathering product type, quantity, name, and shipping address
    - Use the order processing tool when all information is collected
    """,
    tools=[order_processing_tool],
)
```

**Impact**: Enables global customer support without separate agent instances per language.

### 6. Integrate Custom Email Templates

**Location**: Application Integration email task configuration

**What to Change**:
1. In Application Integration, navigate to the email notification task
2. Modify the email template to include:
   - Company branding and logos
   - Personalized greetings
   - Order summary tables
   - Estimated delivery dates
   - Customer support contact information
3. Use variables from the integration context (order ID, customer name, etc.)

**Example Template**:
```html
<html>
<body>
    <h2>Order Confirmation - [ORDER_ID]</h2>
    <p>Dear [CUSTOMER_NAME],</p>
    <p>Thank you for your order!</p>
    <table>
        <tr><td>Product:</td><td>[PRODUCT_TYPE]</td></tr>
        <tr><td>Quantity:</td><td>[QUANTITY]</td></tr>
        <tr><td>Shipping Address:</td><td>[SHIPPING_ADDRESS]</td></tr>
    </table>
    <p>Estimated delivery: [DELIVERY_DATE]</p>
</body>
</html>
```

**Impact**: Professional, branded customer communications that enhance user experience.

### 7. Add Order History Lookup

**Location**: Create new tool `order_processing/order_history_tool.py`

**Implementation**:
```python
from google.adk.tools import FunctionTool
from google.cloud import bigquery

def get_order_history(customer_name: str) -> str:
    """Retrieve previous orders for a customer."""
    client = bigquery.Client()

    query = f"""
        SELECT order_id, product_type, quantity, order_date, status
        FROM `{project_id}.{dataset}.orders`
        WHERE customer_name = @customer_name
        ORDER BY order_date DESC
        LIMIT 5
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("customer_name", "STRING", customer_name)
        ]
    )

    results = client.query(query, job_config=job_config).result()

    if results.total_rows == 0:
        return f"No previous orders found for {customer_name}"

    order_list = []
    for row in results:
        order_list.append(
            f"Order #{row.order_id}: {row.quantity}x {row.product_type} - {row.status}"
        )

    return f"Previous orders:\n" + "\n".join(order_list)

order_history_tool = FunctionTool(func=get_order_history)
```

**Update agent.py**:
```python
from .order_history_tool import order_history_tool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='order_processing_agent',
    instruction="""Help users create orders and view order history.
    You can look up previous orders by customer name.""",
    tools=[order_processing_tool, order_history_tool],
)
```

**Impact**: Enables customers to track past orders and facilitates repeat purchases with the same shipping information.

---

## Additional Resources

- **ADK Documentation**: https://google.github.io/adk-docs/
- **Application Integration Docs**: https://cloud.google.com/application-integration/docs/overview
- **Application Integration Toolset**: https://google.github.io/adk-docs/tools/google-cloud-tools/#create-an-api-hub-toolset
- **Vertex AI Agent Engine**: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- **Sample Repository**: https://github.com/google/adk-samples
- **Integration Samples**: https://github.com/GoogleCloudPlatform/application-integration-samples

## License

Copyright 2025 Google LLC - Licensed under Apache License 2.0
