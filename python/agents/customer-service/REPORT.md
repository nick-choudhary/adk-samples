# Customer Service Agent - Technical Documentation Report

## Project Scope

The Cymbal Home & Garden Customer Service Agent is an AI-powered retail assistant designed to provide comprehensive customer service for a big-box home improvement and gardening retailer. The agent leverages multimodal capabilities (text and video) to deliver personalized shopping experiences, product recommendations, order management, and service scheduling.

**Core Capabilities:**
- **Personalized Customer Assistance**: Greets returning customers by name, accesses purchase history and cart contents
- **Multimodal Product Identification**: Uses video input to identify plants from visual descriptions
- **Intelligent Product Recommendations**: Suggests products tailored to customer needs, location (climate-aware), and plant types
- **Order Management**: Views, modifies, and manages shopping carts with real-time updates
- **Service Scheduling**: Books appointments for professional planting and other services
- **Discount Management**: Approves discounts within limits, escalates to managers when necessary
- **Customer Engagement**: Sends care instructions, generates QR codes for future discounts

**Use Cases:**
- Customer assistance for plant identification and product selection
- Shopping cart management and order processing
- Professional service scheduling (planting, installation, etc.)
- Competitor price matching and discount approvals
- Customer retention through personalized recommendations and loyalty rewards
- Climate-specific gardening advice (e.g., Las Vegas desert gardening)

**Target Users:**
- Retail customers shopping for home improvement and gardening supplies
- Customer service representatives using AI assistance
- In-store and online shoppers seeking personalized guidance

**Agent Type:** Single Agent, Intermediate Complexity, Conversational Interaction with Multimodal Support

## Technical Architecture

### Code Flow

The Customer Service Agent follows a tool-rich, stateful architecture:

1. **Initialization** (`customer_service/agent.py:51-74`):
   - Loads configuration from `Config()` object
   - Injects customer profile into `GLOBAL_INSTRUCTION` from session state
   - Creates single root agent with 12 custom tools
   - Configures callbacks for rate limiting, tool monitoring, and logging
   - Uses configurable model (default: Gemini 2.5 Flash)

2. **Session State Management** (`customer_service/entities/customer.py`):
   - Preloads customer data (name, location, purchase history, preferences)
   - In production, should be populated from CRM system based on authentication
   - Customer profile injected into agent context via `GLOBAL_INSTRUCTION`
   - Default customer: Alex Johnson, Las Vegas NV, 2+ year customer

3. **Interaction Flow**:
   ```
   User Query → Agent (Gemini 2.5 Flash)
                → Analyzes customer profile from session state
                → Determines required tools
                → Decision Point:
                   ├─ Product question? → get_product_recommendations
                   ├─ Cart management? → access_cart_information → modify_cart
                   ├─ Visual identification? → send_call_companion_link (video)
                   ├─ Service needed? → get_available_planting_times → schedule_planting_service
                   ├─ Discount request? → approve_discount OR sync_ask_for_approval
                   └─ Follow-up care? → send_care_instructions + generate_qr_code
                → Synthesizes response
                → Updates CRM via update_salesforce_crm
   ```

4. **Multimodal Video Integration**:
   - Agent recognizes need for visual plant identification
   - Calls `send_call_companion_link(phone_number)` to initiate video session
   - Receives video stream for real-time plant identification
   - Provides recommendations based on visual analysis

5. **Discount Approval Workflow**:
   ```
   Customer requests discount
   → Agent checks discount value
   → If ≤10% → approve_discount (auto-approved)
   → If >10% → sync_ask_for_approval (manager approval required)
   → Tool returns status
   → Agent communicates result to customer
   ```

### Key Components

**Agent Definition** (`customer_service/agent.py`):
- Single `root_agent` with 12 tools
- Global instruction includes customer profile context
- Main instruction defines "Project Pro" persona and capabilities
- Callbacks for rate limiting and tool execution monitoring

**Custom Tools** (`customer_service/tools/tools.py`):

1. **send_call_companion_link(phone_number: str)** - Initiates video call for visual product identification
2. **approve_discount(discount_type: str, value: float, reason: str)** - Auto-approves discounts ≤10%
3. **sync_ask_for_approval(discount_type: str, value: float, reason: str)** - Requests manager approval for larger discounts
4. **update_salesforce_crm(customer_id: str, details: dict)** - Updates CRM with transaction details
5. **access_cart_information(customer_id: str)** - Retrieves shopping cart contents
6. **modify_cart(customer_id: str, items_to_add: list, items_to_remove: list)** - Updates cart items
7. **get_product_recommendations(plant_type: str, customer_id: str)** - Returns product suggestions (e.g., soil, fertilizer)
8. **check_product_availability(product_id: str, store_id: str)** - Checks inventory status
9. **schedule_planting_service(customer_id: str, date: str, time_range: str, details: str)** - Books service appointments
10. **get_available_planting_times(date: str)** - Retrieves available time slots
11. **send_care_instructions(customer_id: str, plant_type: str, delivery_method: str)** - Sends email/SMS care guides
12. **generate_qr_code(customer_id: str, discount_value: float, discount_type: str, expiration_days: int)** - Creates loyalty discount QR codes

**Important Note**: All tools currently return **mocked responses**. For production deployment, replace mock implementations with actual backend API calls in `customer_service/tools/tools.py`.

**Reasoning Mechanism** (`customer_service/prompts.py:23-85`):
- Agent persona: "Project Pro" - friendly, empathetic retail assistant
- Context-aware: Uses customer profile to personalize interactions
- Tool-first approach: Prefers tools over internal knowledge
- Proactive assistance: Anticipates needs and offers relevant services
- Confirmation-based: Always confirms actions before execution
- Climate-aware: Considers location (Las Vegas) for product recommendations

### Key Libraries and Dependencies

**Core Framework:**
- `google-adk>=1.0.0` - Google Agent Development Kit
- `google-cloud-aiplatform[adk,agent_engine]>=1.93.0` - Vertex AI integration and deployment
- `pydantic-settings>=2.8.1` - Configuration management
- `cloudpickle>=3.1.1` - Serialization for deployment

**Utilities:**
- `tabulate>=0.9.0` - Table formatting for cart displays
- `jsonschema>=4.23.0` - JSON validation
- `pylint>=3.3.6` - Code quality

**Development and Testing:**
- `pytest>=8.3.5` - Testing framework
- `pytest-mock>=3.14.0` - Mocking utilities
- `pytest-cov>=6.0.0` - Code coverage
- `pytest-asyncio>=0.25.3` - Async test support

**Deployment:**
- `agent-starter-pack>=0.14.1` - Production deployment utilities
- `pyink>=24.10.1` - Code formatting

### Project Structure

```
customer_service/
├── agent.py                           # Main agent definition
├── config.py                          # Configuration settings
├── prompts.py                         # System instructions and persona
├── tools/
│   ├── tools.py                       # 12 custom tools (mocked)
│   └── __init__.py
├── entities/
│   ├── customer.py                    # Customer profile management
│   └── __init__.py
└── shared_libraries/
    ├── callbacks.py                   # Rate limiting, logging callbacks
    └── __init__.py

tests/
└── unit/
    ├── test_config.py
    └── test_tools.py                  # Unit tests for tools

eval/
└── test_eval.py                       # Integration evaluation tests

deployment/
└── deploy.py                          # Vertex AI deployment script
```

### Agent Reasoning Mechanism

**Stateful Personalization**:
1. Customer profile loaded at session start (name, location, history)
2. Agent references profile before asking questions
3. Recommendations tailored to climate and preferences

**Tool Orchestration Strategy**:
1. **Information Gathering**: Always check cart before recommendations
2. **Sequential Tool Calls**: `access_cart_information` → `get_product_recommendations` → `modify_cart`
3. **Conditional Logic**: Automatic discount approval vs. manager escalation
4. **Multi-step Workflows**: Service scheduling (check availability → book appointment → send confirmation)

**Multimodal Reasoning**:
- Recognizes when text descriptions are insufficient (e.g., "sun-loving annuals")
- Initiates video call for visual identification
- Processes video input to identify specific plant varieties
- Provides targeted recommendations based on visual analysis

**Error Handling and Guardrails**:
- Discount limits enforced in tool logic (≤10% auto-approve, ≤20% fixed)
- Defense-in-depth against prompt injection for unauthorized discounts
- Validates tool inputs before execution
- Provides clear error messages when operations fail

### Key Files

- `customer_service/agent.py` - Root agent configuration
- `customer_service/prompts.py` - System instructions and "Project Pro" persona
- `customer_service/tools/tools.py` - 12 custom tools with mock implementations
- `customer_service/entities/customer.py` - Customer profile data structure
- `customer_service/config.py` - Configuration parameters (model, name, settings)
- `customer_service/shared_libraries/callbacks.py` - Rate limiting and monitoring
- `eval/test_eval.py` - Evaluation framework
- `tests/unit/test_tools.py` - Tool unit tests
- `deployment/deploy.py` - Vertex AI Agent Engine deployment

## Build & Run Instructions

### Prerequisites

1. **Python 3.10, 3.11, or 3.12** (NOT 3.13+)
2. **uv** package manager:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Google Cloud Account** with billing enabled
4. **Google Cloud SDK** (gcloud CLI):
   ```bash
   curl https://sdk.cloud.google.com | bash
   ```
5. **Git** for repository cloning

### Step 1: Clone Repository and Navigate to Project

```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/customer-service
```

### Step 2: Install Dependencies

```bash
uv sync
```

This creates a virtual environment and installs all dependencies from `pyproject.toml`.

### Step 3: Enable Google Cloud APIs

```bash
gcloud auth login
gcloud services enable aiplatform.googleapis.com
```

### Step 4: Set Up Environment Variables

**Option A: Using .env file**

```bash
cp .env_sample .env
```

Edit `.env`:
```
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_LOCATION=us-central1
```

**Option B: Using shell environment**

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_GENAI_USE_VERTEXAI=1
export GOOGLE_CLOUD_LOCATION=us-central1
```

**Option C: Edit configuration file**

Modify `customer_service/config.py` directly with your project settings.

### Step 5: Authenticate with Google Cloud

```bash
gcloud auth application-default login
```

### Step 6: Run the Agent

**Option 1: CLI Interface**

```bash
adk run customer_service
```

**Option 2: Web UI Interface**

```bash
adk web
```

Then select "customer_service" from the dropdown menu.

### Example Interaction

```
User: Hi there

Agent: Hey Alex, I see you've been a Cymbal Home & Garden customer for a couple
of years now - we appreciate your business! I also see you have a few things in
your cart already. How can I help you get your garden growing today?

User: Yeah, so I'm a bit confused. I just bought some...uh...plants or flowers
that I wanted to put in the backyard. They just say "sun loving annuals" on them.
I totally spaced on picking up potting soil so I'm placing an order for pickup now.
The problem is, I'm not sure if the potting soil and fertilizer I picked out are
the right ones.

Agent: I understand – it can be tricky when you're not quite sure what you've got!
Let's figure this out together. Don't worry, we'll get your plants the right care.
To best help you, would you be willing to share a quick video of the plants you've
purchased? That will help me identify them and make sure you have the right supplies.

User: Sure, how do I do that?

Agent: I just texted you a link to the number in your profile. Just click on that,
and it'll open a secure video connection.
[Tool: send_call_companion_link(phone_number='+12065550123')]
[Response: {'status': 'success', 'message': 'Link sent to +12065550123'}]

User: Okay, I clicked the link...can you see this?

Agent: Yes I can see you Alex! Can you go ahead and point the camera at your
plants so I can inspect them?

User: [Shows plants on video]

Agent: Perfect! Those are beautiful Petunias - a great choice for Las Vegas!
Let me check your cart and recommend the best products for them.
[Tool: access_cart_information(customer_id='123')]
[Tool: get_product_recommendations(plant_type='Petunias', customer_id='123')]

I see you have Standard Potting Soil and General Purpose Fertilizer. For Petunias
in Las Vegas heat, I'd recommend upgrading to:
- Bloom Booster Potting Mix (provides extra nutrients Petunias love)
- Flower Power Fertilizer (specifically formulated for flowering annuals)

Would you like me to update your cart with these better options?
```

### Step 7: Run Evaluations

```bash
uv sync --dev
uv run pytest eval
```

This runs holistic performance tests for:
- Tool usage accuracy
- Response quality
- Workflow completion
- Customer satisfaction simulation

### Step 8: Run Unit Tests

```bash
uv run pytest tests/unit
```

Tests individual tool functions and configuration.

### Step 9: Deploy to Vertex AI Agent Engine (Optional)

**Build the wheel package:**

```bash
uv build --wheel --out-dir deployment
```

**Deploy the agent:**

```bash
cd deployment
uv run python deploy.py
```

The script outputs:
```
Deployed agent to Vertex AI Agent Engine successfully
Resource name: projects/<PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<ENGINE_ID>
```

**Test the deployed agent:**

```python
import vertexai
from customer_service.config import Config
from vertexai.preview.reasoning_engines import AdkApp

configs = Config()

vertexai.init(
    project="your-project-id",
    location="us-central1"
)

# Retrieve deployed agent
agent_engine = vertexai.agent_engines.get('projects/XXX/locations/us-central1/reasoningEngines/YYY')

# Stream query
for event in agent_engine.stream_query(
    user_id="user123",
    session_id="session456",
    message="Hello!",
):
    print(event)
```

### Alternative: Using Agent Starter Pack

For production-ready deployment with CI/CD:

```bash
# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install and create project
pip install --upgrade agent-starter-pack
agent-starter-pack create my-customer-service -a adk@customer-service
```

**OR using uv:**

```bash
uvx agent-starter-pack create my-customer-service -a adk@customer-service
```

The starter pack includes:
- Automated deployment scripts
- Infrastructure as code templates
- CI/CD pipelines
- Monitoring and logging configurations
- Security best practices

## Customization Options

### 1. Replace Mock Tools with Real Backend

Edit `customer_service/tools/tools.py` to integrate with actual systems:

```python
def access_cart_information(customer_id: str) -> dict:
    # Replace mock with actual API call
    import requests
    response = requests.get(f"https://api.cymbal.com/cart/{customer_id}")
    return response.json()

def schedule_planting_service(customer_id: str, date: str, time_range: str, details: str) -> dict:
    # Integrate with scheduling system
    import requests
    payload = {
        "customer_id": customer_id,
        "service_type": "planting",
        "date": date,
        "time": time_range,
        "details": details
    }
    response = requests.post("https://api.cymbal.com/appointments", json=payload)
    return response.json()
```

### 2. Customize Customer Profile Loading

Edit `customer_service/entities/customer.py` to load from CRM:

```python
@staticmethod
def get_customer(customer_id: str) -> "Customer":
    # Replace mock with CRM integration
    import requests
    response = requests.get(f"https://crm.cymbal.com/customers/{customer_id}")
    customer_data = response.json()
    return Customer(**customer_data)
```

### 3. Add Additional Tools

Extend agent capabilities in `customer_service/agent.py`:

```python
from google.adk.tools.search.google_search import GoogleSearch

# Add to tools list
tools=[
    send_call_companion_link,
    # ... existing tools ...
    GoogleSearch(),  # Add web search capability
]
```

### 4. Modify Agent Persona

Edit `customer_service/prompts.py` to change tone, style, or capabilities:

```python
INSTRUCTION = """
You are "Garden Guru," an expert horticulturist and customer service specialist...
[Customize personality, constraints, and capabilities]
"""
```

### 5. Configure Different Models

Edit `customer_service/config.py`:

```python
class AgentSettings(BaseModel):
    model: str = "gemini-2.0-flash"  # Faster responses
    # OR
    model: str = "gemini-2.5-pro"    # Higher quality reasoning
```

### 6. Add Analytics and Monitoring

Extend callbacks in `customer_service/shared_libraries/callbacks.py`:

```python
def after_tool(tool_name: str, tool_result: Any, context: ToolContext):
    # Log to analytics platform
    import logging
    logging.info(f"Tool {tool_name} executed with result: {tool_result}")

    # Send metrics to monitoring service
    send_metric("tool_execution", {
        "tool": tool_name,
        "success": tool_result.get("status") == "success",
        "customer_id": context.session_state.get("customer_id")
    })
```

## Production Considerations

**Important Disclaimer**: This is a sample implementation with **mocked tools**. Before production deployment:

1. **Backend Integration**: Replace all mock tools with real API integrations
2. **Authentication**: Implement secure user authentication and authorization
3. **Session Management**: Integrate with actual CRM for customer profile loading
4. **Error Handling**: Add comprehensive error handling and retry logic
5. **Security**: Implement input validation, rate limiting, and security controls
6. **Monitoring**: Add logging, metrics, and alerting
7. **Testing**: Conduct thorough integration and load testing
8. **Compliance**: Ensure adherence to data privacy regulations (GDPR, CCPA, etc.)

**Known Limitations in Current Implementation**:
- Tools return static mock data
- Cart modifications don't persist between sessions
- Video streaming is simulated (sends link but doesn't process actual video)
- Discount approvals use hardcoded limits
- No actual CRM or inventory system integration

---

**Model:** Gemini 2.5 Flash (configurable)
**Complexity:** Intermediate
**Agent Type:** Single Agent with Multimodal Support
**Python Version:** 3.10 - 3.12
**License:** Apache 2.0
**Author:** Christos Aniftos (aniftos@google.com)
**Vertical:** Retail / E-commerce
