# Personalized Shopping Agent - Technical Documentation Report

## Project Scope

The Personalized Shopping Agent is an advanced AI-powered e-commerce assistant that provides tailored product recommendations through interactive web navigation and multi-modal search capabilities. Built on the ADK framework, this agent demonstrates sophisticated product discovery in a simulated retail environment with 1.18 million real-world products.

### Core Capabilities
- **Multi-Modal Search**: Text-based and image-based product search
- **Web Navigation**: Autonomous navigation through product pages, descriptions, features, and reviews
- **Interactive Shopping Flow**: Step-by-step guidance from search to purchase
- **Product Comparison**: Intelligent analysis of features, reviews, and specifications
- **Conversational Memory**: Maintains context across entire shopping sessions
- **Visual Artifacts**: Displays product pages as HTML artifacts in the UI

### Primary Use Cases
- E-commerce product discovery and recommendations
- Visual search for similar items ("find products like this image")
- Guided shopping experiences with detailed product exploration
- Fashion and apparel shopping with size/color customization
- Conversational product research and comparison

### Target Users
- E-commerce businesses building AI shopping assistants
- Developers learning multi-modal agent development
- Retail companies implementing conversational commerce
- Teams exploring web navigation agents and RAG patterns

### Key Innovations/Differentiators
- **Real-World Dataset**: 1.18M products from WebShop (Princeton NLP)
- **Simulated Web Environment**: Gym-based environment for controlled testing
- **Multi-Modal Input**: Supports both text queries and image uploads
- **Tool-Based Navigation**: Custom `search` and `click` tools for web interaction
- **Evaluation Framework**: Built-in metrics for tool trajectory and response quality
- **Production Deployment**: Wheel-based deployment to Vertex AI Agent Engine

---

## Technical Architecture

### Single-Agent Architecture with Custom Environment

This agent uses a **single conversational agent** with specialized tools for interacting with a simulated e-commerce environment.

```
┌──────────────────────────────────────────────────────────────────┐
│                    User (Text or Image Input)                    │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│       Personalized Shopping Agent (Gemini 2.5 Flash)             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Agent Instruction (prompt.py):                            │  │
│  │  - Interactive shopping flow                               │  │
│  │  - Multi-step product exploration                          │  │
│  │  - Purchase confirmation workflow                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            │                                      │
│              ┌─────────────┴─────────────┐                       │
│              ▼                           ▼                       │
│  ┌──────────────────────┐   ┌──────────────────────┐            │
│  │   Search Tool        │   │    Click Tool        │            │
│  │  (text/image search) │   │  (button navigation) │            │
│  └──────────────────────┘   └──────────────────────┘            │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│              WebShop Environment (Gym-based)                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Web Agent Site Engine                                      │  │
│  │  - Product database (1.18M items)                           │  │
│  │  - HTML generation                                          │  │
│  │  - State management                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            │                                      │
│              ┌─────────────┴─────────────┐                       │
│              ▼                           ▼                       │
│  ┌──────────────────────┐   ┌──────────────────────┐            │
│  │  Search Engine       │   │  Product Database    │            │
│  │  (PySerini/Lucene)   │   │  (JSON files)        │            │
│  │  - Keyword indexing  │   │  - 1.18M products    │            │
│  │  - Retrieval         │   │  - Annotations       │            │
│  └──────────────────────┘   └──────────────────────┘            │
└──────────────────────────────────────────────────────────────────┘
```

### Code Flow Explanation

**1. Agent Initialization** (`/home/user/adk-samples/python/agents/personalized-shopping/personalized_shopping/agent.py`, lines 23-35):
- Creates root agent with Gemini 2.5 Flash
- Loads detailed instruction prompt from `prompt.py`
- Attaches `search` and `click` function tools
- Wraps native Python functions with `FunctionTool`

**2. Prompt Engineering** (`/home/user/adk-samples/python/agents/personalized-shopping/personalized_shopping/prompt.py`, lines 15-60):
Defines a sophisticated interaction flow:
- **Initial Inquiry** (lines 19-21): Handles text queries or image uploads
- **Search Phase** (lines 23-26): Uses search tool and presents results
- **Product Exploration** (lines 28-34): Automatically navigates Description, Features, and Reviews sections
- **Purchase Confirmation** (lines 36-41): Selects size/color options and confirms purchase
- **Finalization** (lines 43-45): Processes purchase or handles errors

**3. Environment Initialization** (`/home/user/adk-samples/python/agents/personalized-shopping/personalized_shopping/shared_libraries/init_env.py`, lines 25-45):
- Registers custom Gym environment `WebAgentTextEnv-v0`
- Implements singleton pattern for environment instance
- Lazy-loads 50,000 products on first access (configurable via `num_product_items` at line 34)
- Resets environment state for fresh sessions

**4. Search Tool** (`/home/user/adk-samples/python/agents/personalized-shopping/personalized_shopping/tools/search.py`, lines 21-60):
- **Input**: Keywords (string) - can be extracted from text or image description
- **Process**:
  - Retrieves WebShop environment instance (line 31)
  - Constructs search action string (line 33)
  - Sets instruction text for environment context (line 34)
  - Executes environment step (line 36)
  - Extracts observation from "Back to Search" onward (lines 39-41)
  - Saves HTML artifact for UI display (lines 51-58)
- **Output**: Text representation of search results webpage

**5. Click Tool** (`/home/user/adk-samples/python/agents/personalized-shopping/personalized_shopping/tools/click.py`, lines 21-60):
- **Input**: Button name (string) - e.g., "Next >", "< Prev", "Description", product ID, size, color
- **Process**:
  - Retrieves WebShop environment instance (line 31)
  - Constructs click action string (line 33)
  - Executes environment step (line 34)
  - Extracts observation (lines 37-39)
  - Handles special "Back to Search" button (lines 47-48)
  - Saves HTML artifact (lines 51-59)
- **Output**: Text representation of updated webpage

**6. Web Environment Engine** (`personalized_shopping/shared_libraries/web_agent_site/`):
- **Text Environment** (`envs/web_agent_text_env.py`): Converts HTML to text observations
- **Engine** (`engine/engine.py`): Manages product state, search results, and page generation
- **Normalization** (`engine/normalize.py`): Cleans and structures product data
- **Goal Tracking** (`engine/goal.py`): Tracks shopping objectives and rewards

**7. Search Engine** (`personalized_shopping/shared_libraries/search_engine/`):
- Uses PySerini (Lucene-based) for product indexing and retrieval
- Supports multiple index sizes: 100, 1k, 10k, 50k products
- Converts JSON product files to Lucene document format
- Provides fast keyword-based product lookup

### Agent Definitions

**Root Agent** (`agent.py`, lines 23-35):
- **Name**: `personalized_shopping_agent`
- **Model**: Gemini 2.5 Flash
- **Role**: Interactive shopping assistant with web navigation capabilities
- **Responsibilities**:
  - Interpret user shopping requests (text or image)
  - Execute searches using the search tool
  - Navigate product pages using the click tool
  - Gather information from multiple sections (Description, Features, Reviews)
  - Guide users through size/color selection
  - Confirm and process purchases

**Tool: search** (`tools/search.py`, lines 21-60):
- **Type**: `FunctionTool` wrapping async Python function
- **Purpose**: Search the product catalog with keywords
- **Context Management**: Maintains WebShop environment state
- **Artifact Generation**: Saves HTML for visual display

**Tool: click** (`tools/click.py`, lines 21-60):
- **Type**: `FunctionTool` wrapping async Python function
- **Purpose**: Navigate web pages by clicking buttons
- **State Tracking**: Updates environment based on button interactions
- **Artifact Generation**: Displays updated pages in UI

### Key Libraries and Dependencies

**Core ADK and Google Cloud** (`pyproject.toml`, lines 8-11):
- `google-cloud-aiplatform[adk,agent-engines]>=1.93.0`: Vertex AI integration and deployment
- `google-genai>=1.9.0`: Gemini API access
- `google-adk>=1.0.0`: Core ADK framework
- `pydantic>=2.10.6`: Data validation and settings management
- `python-dotenv>=1.0.1`: Environment configuration

**Search and Indexing** (`pyproject.toml`, lines 14-15):
- `pyserini>=0.43.0`: Lucene-based search engine for product retrieval
- `cleantext>=1.1.4`: Text normalization and cleaning

**Web Environment** (`pyproject.toml`, lines 16-17, 21):
- `Flask>=3.1.0`: Web server for HTML rendering
- `gym==0.26.2`: OpenAI Gym environment framework

**NLP and ML** (`pyproject.toml`, lines 18-19, 22-23):
- `spacy>=3.8.2`: Natural language processing
- `en_core_web_sm @ https://...`: English language model for spaCy
- `torch>=2.5.1`: PyTorch for deep learning
- `torchvision>=0.20.1`: Image processing capabilities

**Utilities** (`pyproject.toml`, lines 20, 24-27):
- `thefuzz>=0.22.1`: Fuzzy string matching for product names
- `gdown>=5.2.0`: Google Drive file downloads
- `pytest>=8.3.5`: Testing framework
- `tabulate>=0.9.0`: Data formatting
- `absl-py>=2.2.1`: Google's Python common libraries

**Development Dependencies** (`pyproject.toml`, lines 34-35):
- `pytest-asyncio>=0.26.0`: Async test support
- `agent-starter-pack>=0.14.1`: Production deployment scaffolding

**Linting Tools** (`pyproject.toml`, lines 39-45):
- `ruff>=0.4.6`: Fast Python linter
- `mypy>=1.15.0`: Static type checking
- `codespell>=2.2.0`: Spell checking

### Tools and Integrations

**1. WebShop Environment** (Princeton NLP):
- **Source**: https://github.com/princeton-nlp/WebShop
- **Dataset**: 1.18M real-world products from various e-commerce sites
- **Annotations**: 12,087 crowd-sourced text instructions
- **Integration**: Modified and adapted for ADK agent interaction
- **Purpose**: Provides realistic product data and browsing simulation

**2. PySerini Search Engine**:
- **Technology**: Apache Lucene-based information retrieval
- **Indexing**: Pre-processes product JSON into searchable documents
- **Performance**: Optimized for fast keyword searches across large catalogs
- **Configuration**: Multiple index sizes (100 to 50k products)

**3. Gym Environment Framework**:
- **Purpose**: Standardized interface for agent-environment interaction
- **Observation Space**: Text representations of HTML pages
- **Action Space**: Search and click actions
- **Reward System**: Tracks successful product discovery and purchases

**4. Artifact System**:
- **Technology**: ADK's `ToolContext.save_artifact` functionality
- **Format**: HTML rendered in UI alongside text responses
- **Use Case**: Visual confirmation of agent actions on web pages

### Reasoning Mechanisms

**1. Multi-Step Product Exploration** (`prompt.py`, lines 28-34):
- Agent must proactively gather information from three sections:
  - Description: Product overview and details
  - Features: Key specifications and highlights
  - Reviews: Customer feedback and ratings
- Uses `< Prev` button navigation to return between sections
- Summarizes all information before making recommendations
- Avoids asking users to review sections individually

**2. Context-Aware Button Clicking** (`prompt.py`, lines 57-60):
- **Constraint**: Only click buttons visible on current page
- **Navigation**: Use "< Prev" to return to previous pages
- **Search**: Use "Back to Search" when search button not available
- **Validation**: Prevents clicking non-existent buttons from previous states

**3. Purchase Confirmation Flow** (`prompt.py`, lines 36-41):
- Navigate back to product page with size/color options
- Click appropriate size and color based on user preference
- Request explicit user confirmation before "Buy Now"
- Handle rejection by asking for next steps

**4. Image-Based Search** (`prompt.py`, line 21):
- When user uploads image, analyze visual content
- Extract product type, style, color, and attributes
- Use extracted description as search keywords
- Reference uploaded image throughout conversation

**5. Conversational Memory**:
- ADK automatically maintains conversation history
- Agent references previous selections (size, color, product preferences)
- Enables follow-up questions like "show me similar items"
- Preserves shopping context across multiple searches

---

## Build & Run Instructions

### Prerequisites

**Required Software**:
- **Python**: Version 3.10, 3.11, or 3.12 (not 3.13+)
- **uv**: Fast Python package installer and resolver
  - Installation: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Alternative: `pip install uv`

**System Requirements**:
- **Memory**: Minimum 8GB RAM (16GB recommended for full 50k product dataset)
- **Disk Space**: ~6GB for product data and indexes
- **Network**: Stable internet for downloading product datasets

**Google Cloud Requirements**:
- Active Google Cloud Project
- Vertex AI API enabled
- Authenticated `gcloud` CLI

### Step-by-Step Installation

**1. Clone Repository**:
```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/personalized-shopping
```

**2. Install Dependencies**:
```bash
# Install all project dependencies
uv sync
```

**3. Download Product Data**:

The agent requires product JSON files to initialize the web environment. These files must be downloaded from Google Drive:

```bash
cd personalized_shopping/shared_libraries
mkdir data
cd data

# Small dataset (4.5MB) - 1,000 products
gdown https://drive.google.com/uc?id=1EgHdxQ_YxqIQlvvq5iKlCrkEKR6-j0Ib

# Small instructions (147KB)
gdown https://drive.google.com/uc?id=1IduG0xl544V_A_jv3tHXC0kyFi7PnyBu

# Full dataset (5.1GB) - All 1.18M products
gdown https://drive.google.com/uc?id=1A2whVgOO0euk5O13n2iYDM0bQRkkRduB

# Full instructions (178MB)
gdown https://drive.google.com/uc?id=1s2j6NgHljiZzQNL3veZaAiyW_qDEgBNi

# Human annotations (4.9MB)
gdown https://drive.google.com/uc?id=14Kb5SPBk_jfdLZ_CDBNitW98QLDlKR5O
```

**Note**: If `gdown` fails, manually download from the individual Google Drive links and place in `personalized_shopping/shared_libraries/data/`.

**4. Index Product Data**:

Convert JSON files to Lucene-compatible format and create search indexes:

```bash
# Navigate to search engine directory
cd ../search_engine

# Create resource directories
mkdir -p resources_100 resources_1k resources_10k resources_50k

# Convert product files to document format
uv run python convert_product_file_format.py

# Create search indexes
mkdir -p indexes
bash run_indexing.sh

# Return to project root
cd ../../
```

This process creates multiple index sizes (100, 1k, 10k, 50k products) for flexible testing.

### Configuration

**Environment Variables**:

Copy and edit the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration (`.env.example`, lines 2-5):
```bash
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=<YOUR_PROJECT_NAME>
GOOGLE_CLOUD_LOCATION=<YOUR_PROJECT_LOCATION>  # e.g., us-central1
GOOGLE_CLOUD_STORAGE_BUCKET=<YOUR_STORAGE_BUCKET>  # For deployment
```

**Authenticate Google Cloud**:
```bash
gcloud auth application-default login
```

### Running the Agent

#### Option 1: CLI Interface
```bash
# From the personalized-shopping directory
adk run personalized_shopping
```

This starts an interactive CLI session where you can chat with the agent.

#### Option 2: Web UI
```bash
# Start ADK web interface
adk web

# Navigate to the URL printed (usually http://localhost:8080)
# Select "personalized_shopping" from the dropdown menu
```

The web UI provides:
- Visual chat interface
- HTML artifact display (product pages)
- Image upload capability for visual search

**Note**: The first run takes several minutes as the system loads 50,000 products into memory.

### Example Interactions

#### Example 1: Text-Based Search

**Session File**: `/home/user/adk-samples/python/agents/personalized-shopping/tests/example_interactions/text_search_floral_dress.session.md`

```
User: Hello, can you help me find a summer dress? I want something flowy and floral.

Agent: I can definitely help you find a summer dress! Let me search for flowy floral
       dresses.
       [Executes: search("flowy floral summer dress")]

       I found several beautiful options:
       1. Floral Print Maxi Dress - $45.99
       2. Bohemian Floral Sundress - $38.50
       3. Vintage Floral Midi Dress - $52.00

       Which one would you like to explore further?

User: Tell me more about option 1

Agent: Let me gather all the information about the Floral Print Maxi Dress.
       [Clicks: Product ID]
       [Clicks: "Description"]
       [Clicks: "< Prev"]
       [Clicks: "Features"]
       [Clicks: "< Prev"]
       [Clicks: "Reviews"]

       Here's a complete overview:

       **Description:** This beautiful maxi dress features a vibrant floral print
       perfect for summer occasions...

       **Features:**
       - Lightweight, breathable fabric
       - Adjustable straps
       - Side pockets
       - Machine washable

       **Reviews:** 4.5/5 stars (127 reviews)
       Customers love the fit and the quality of the fabric...

       Would you like to proceed with purchasing this dress?

User: Yes, I'd like it in medium and blue color

Agent: [Clicks: "< Prev" to return to product page]
       [Clicks: "Medium"]
       [Clicks: "Blue"]

       I've selected Medium size in Blue. Shall I proceed with adding this to your
       cart and completing the purchase?

User: Yes, please!

Agent: [Clicks: "Buy Now"]

       Perfect! Your purchase is being processed. You've ordered the Floral Print
       Maxi Dress in Medium, Blue color for $45.99.
```

#### Example 2: Image-Based Search

**Session File**: `/home/user/adk-samples/python/agents/personalized-shopping/tests/example_interactions/image_search_denim_skirt.session.md`

**Input Image**: `/home/user/adk-samples/python/agents/personalized-shopping/tests/example_interactions/example_product.png`

```
User: [Uploads image of a denim skirt]
      Can you find me something similar to this?

Agent: I can see you've uploaded an image of a denim skirt. It appears to be a
       classic A-line style with button detailing. Let me search for similar items.
       [Executes: search("denim A-line skirt button front")]

       I found these similar denim skirts:
       1. Classic Denim A-Line Skirt - $32.99
       2. Button-Front Denim Skirt - $28.50
       3. Vintage Denim Mini Skirt - $35.00

       The first one looks very similar to your image. Would you like me to show
       you more details?
```

### Testing and Evaluation

#### Tool Unit Tests

Test individual tools in isolation:
```bash
# From personalized-shopping directory
uv run pytest tests/test_tools.py -v
```

This validates:
- Search tool functionality
- Click tool functionality
- Environment state management

#### Agent Evaluation

Run full agent evaluation with metrics:
```bash
# Install dev dependencies
uv sync --dev

# Run evaluation suite
uv run pytest eval -v
```

**Evaluation Configuration** (`eval/eval_data/test_config.json`, lines 1-6):
- `tool_trajectory_avg_score`: 1.0 (perfect tool usage expected)
- `response_match_score`: 0.6 (60% semantic similarity to reference answers)

**Evaluation Process** (`eval/test_eval.py`, lines 30-36):
- Loads test cases from `eval/eval_data/simple.test.json`
- Runs agent on each query
- Compares tool usage against expected trajectory
- Measures response quality against reference answers
- Generates detailed evaluation report

**Custom Evaluation Datasets**:
Add your own test cases in `eval/eval_data/` directory in JSON format:
```json
{
  "query": "Find me a red dress under $50",
  "expected_tools": ["search", "click"],
  "reference_answer": "I found several red dresses..."
}
```

### Deployment

The personalized shopping agent can be deployed to Vertex AI Agent Engine for production use.

#### Prerequisites for Deployment

1. **Ensure product data is downloaded and indexed** (see Installation steps 3-4 above)
2. **Set environment variables** in `.env` file
3. **Create Google Cloud Storage bucket** for staging

#### Build Agent Wheel File

Package the agent and all dependencies:
```bash
cd /path/to/adk-samples/python/agents/personalized-shopping
uv build --wheel --out-dir deployment
```

This creates `deployment/personalized_shopping-0.1.0-py3-none-any.whl`.

#### Deploy to Vertex AI Agent Engine

Run the deployment script (`deployment/deploy.py`, lines 15-71):
```bash
cd deployment
uv run python deploy.py
```

**Deployment Process**:
1. Initializes Vertex AI with project and location (lines 33-37)
2. Creates `AdkApp` from root agent (lines 41-44)
3. Packages wheel file and dependencies (lines 49-56)
4. Deploys to Agent Engine with tracing enabled (line 42)
5. Runs test query to validate deployment (lines 62-68)

**Expected Output**:
```
cloud_project=your-project-id
cloud_location=us-central1
storage_bucket=your-bucket
--------------------------------------------------
Deploying app begin...
Deploying agent to agent engine...
Deploying agent to agent engine finished.
--------------------------------------------------
Testing deployment:
Created remote agent: projects/PROJECT_NUM/locations/LOCATION/reasoningEngines/ENGINE_ID
```

**Note**: Deployment can take 10+ minutes due to the large wheel file (~100MB+).

#### Interact with Deployed Agent

**Python Client**:
```python
import dotenv
dotenv.load_dotenv()
from vertexai import agent_engines

agent_engine_id = "AGENT_ENGINE_ID"  # From deployment output
user_input = "Hello, can you help me find a summer dress?"

agent_engine = agent_engines.get(agent_engine_id)
session = agent_engine.create_session(user_id="user123")

for event in agent_engine.stream_query(
    user_id=session["user_id"],
    session_id=session["id"],
    message=user_input
):
    for part in event["content"]["parts"]:
        print(part["text"])
```

#### Delete Deployed Agent

```bash
uv run python deployment/deploy.py --delete --resource_id=${AGENT_ENGINE_ID}
```

#### Alternative: Agent Starter Pack

For production deployments with CI/CD and additional features:

```bash
# Using uv
uvx agent-starter-pack create my-personalized-shopping -a adk@personalized-shopping

# Or with pip
python -m venv .venv && source .venv/bin/activate
pip install --upgrade agent-starter-pack
agent-starter-pack create my-personalized-shopping -a adk@personalized-shopping
```

This creates a production-ready scaffold with:
- Automated deployment scripts
- CI/CD integration
- Environment management
- Testing infrastructure

### Troubleshooting

**Issue: gdown fails to download product data**
- **Solution**: Manually download files from Google Drive links
- Place in `personalized_shopping/shared_libraries/data/`
- File URLs are in README.md lines 83-96

**Issue: Out of memory errors**
- **Cause**: Loading 50,000+ products exceeds available RAM
- **Solution**: Reduce `num_product_items` in `init_env.py` line 34
- Change from 50000 to 10000 or 5000

**Issue: Indexing fails with Java errors**
- **Cause**: PySerini requires Java 11+
- **Solution**: Install Java 11 or higher
  ```bash
  sudo apt-get install openjdk-11-jdk
  export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
  ```

**Issue: Agent is slow on first run**
- **Expected Behavior**: Loading products takes 2-5 minutes initially
- **Optimization**: Reduce product count in `init_env.py`
- **Note**: Subsequent runs are much faster due to caching

**Issue: Search returns no results**
- **Cause**: Indexes not created or corrupted
- **Solution**: Re-run indexing process
  ```bash
  cd personalized_shopping/shared_libraries/search_engine
  rm -rf indexes/*
  bash run_indexing.sh
  ```

**Issue: ImportError for en_core_web_sm**
- **Cause**: spaCy language model not installed
- **Solution**: Install manually
  ```bash
  uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
  ```

**Issue: Deployment timeout**
- **Cause**: Large wheel file takes time to upload
- **Solution**: Be patient (can take 10-15 minutes)
- **Verification**: Check Vertex AI console for deployment status

---

## Customization Options

### 1. Adjust Product Dataset Size

**Location**: `/home/user/adk-samples/python/agents/personalized-shopping/personalized_shopping/shared_libraries/init_env.py`, line 34

**What to Change**: Modify the `num_product_items` variable:

```python
# Original (50,000 products)
num_product_items = 50000

# Reduced for faster loading (10,000 products)
num_product_items = 10000

# Minimal for testing (1,000 products)
num_product_items = 1000

# Full dataset (requires substantial RAM)
num_product_items = 1180000
```

**Impact**:
- **Lower values**: Faster initialization, less memory usage, smaller search space
- **Higher values**: More product variety, realistic e-commerce experience, higher resource requirements

**Trade-offs**:
- 1,000 products: ~30 seconds load time, 2GB RAM
- 10,000 products: ~1 minute load time, 4GB RAM
- 50,000 products: ~3 minutes load time, 8GB RAM
- 1.18M products: ~15 minutes load time, 32GB+ RAM

### 2. Customize Shopping Workflow Instructions

**Location**: `/home/user/adk-samples/python/agents/personalized-shopping/personalized_shopping/prompt.py`, lines 15-60

**What to Change**: Modify the agent's interaction flow and behavior:

**Example - Add Price Comparison Feature**:
```python
personalized_shopping_agent_instruction = """You are a webshop agent focused on
helping users find the best value products.

**Interaction Flow:**

1.  **Initial Inquiry:**
    * Ask what product they're looking for and their budget range
    * If they upload an image, analyze and estimate price category

2.  **Search Phase:**
    * Search for products within their budget
    * Sort results by price or value rating
    * Highlight any sales or discounts

3.  **Product Exploration:**
    * Compare prices across similar items
    * Analyze value: price vs. features vs. reviews
    * Recommend best value option with justification

4.  **Price Negotiation Simulation:**
    * Inform about any available coupons or promotions
    * Suggest bundle deals for multiple items

5.  **Purchase Confirmation:**
    * Display final price with any discounts
    * Calculate estimated shipping and total cost
    * Confirm before clicking "Buy Now"
"""
```

**Impact**: Changes the agent from a general shopping assistant to a price-conscious bargain hunter.

### 3. Switch Language Model

**Location**: `/home/user/adk-samples/python/agents/personalized-shopping/personalized_shopping/agent.py`, line 24

**What to Change**: Replace the model specification:

```python
# Original (Gemini 2.5 Flash - fast and cost-effective)
root_agent = Agent(
    model="gemini-2.5-flash",
    name="personalized_shopping_agent",
    instruction=personalized_shopping_agent_instruction,
    tools=[FunctionTool(func=search), FunctionTool(func=click)],
)

# Enhanced (Gemini 2.5 Pro - better reasoning for complex comparisons)
root_agent = Agent(
    model="gemini-2.5-pro",
    name="personalized_shopping_agent",
    instruction=personalized_shopping_agent_instruction,
    tools=[FunctionTool(func=search), FunctionTool(func=click)],
)

# Budget (Gemini 1.5 Flash - lower cost)
root_agent = Agent(
    model="gemini-1.5-flash",
    name="personalized_shopping_agent",
    instruction=personalized_shopping_agent_instruction,
    tools=[FunctionTool(func=search), FunctionTool(func=click)],
)
```

**Model Comparison**:
- **gemini-2.5-flash**: Best balance of speed, quality, and cost
- **gemini-2.5-pro**: Superior for complex product comparisons and detailed analysis
- **gemini-1.5-flash**: Fastest and cheapest, suitable for simple shopping tasks

**Impact**: Affects response quality, reasoning depth, latency, and operational cost.

### 4. Add Custom Product Filters

**Location**: Create new file `personalized_shopping/tools/filter.py`

**Implementation**:
```python
from google.adk.tools import ToolContext

async def filter_products(
    min_price: float = 0.0,
    max_price: float = 999999.0,
    category: str = "all",
    min_rating: float = 0.0,
    tool_context: ToolContext = None
) -> str:
    """Filter products by price, category, and rating.

    Args:
      min_price: Minimum price in dollars
      max_price: Maximum price in dollars
      category: Product category (e.g., "clothing", "electronics")
      min_rating: Minimum average rating (0-5)
      tool_context: The function context

    Returns:
      str: Filtered product list
    """
    from ..shared_libraries.init_env import get_webshop_env

    webshop_env = get_webshop_env()

    # Get all products from current search results
    products = webshop_env.get_available_products()

    # Apply filters
    filtered = [
        p for p in products
        if min_price <= p.get("price", 0) <= max_price
        and (category == "all" or p.get("category") == category)
        and p.get("rating", 0) >= min_rating
    ]

    if not filtered:
        return "No products match your filters. Try adjusting your criteria."

    result = f"Found {len(filtered)} products:\n"
    for p in filtered[:10]:  # Show top 10
        result += f"- {p['name']}: ${p['price']} (Rating: {p['rating']})\n"

    return result
```

**Update agent.py**:
```python
from .tools.filter import filter_products

root_agent = Agent(
    model="gemini-2.5-flash",
    name="personalized_shopping_agent",
    instruction=personalized_shopping_agent_instruction,
    tools=[
        FunctionTool(func=search),
        FunctionTool(func=click),
        FunctionTool(func=filter_products),  # Add filter tool
    ],
)
```

**Update prompt.py** to include filter usage instructions.

**Impact**: Enables users to narrow down results by price range, category, and ratings.

### 5. Implement Product Comparison Feature

**Location**: Create new file `personalized_shopping/tools/compare.py`

**Implementation**:
```python
from google.adk.tools import ToolContext

async def compare_products(
    product_ids: list[str],
    tool_context: ToolContext = None
) -> str:
    """Compare multiple products side-by-side.

    Args:
      product_ids: List of product IDs to compare (2-4 products)
      tool_context: The function context

    Returns:
      str: Comparison table with features, prices, ratings
    """
    from ..shared_libraries.init_env import get_webshop_env
    from tabulate import tabulate

    if len(product_ids) < 2:
        return "Please provide at least 2 product IDs to compare."

    if len(product_ids) > 4:
        return "Can compare maximum 4 products at once."

    webshop_env = get_webshop_env()

    # Fetch product details for each ID
    products = []
    for pid in product_ids:
        # Navigate to product page and extract details
        webshop_env.step(f"click[{pid}]")
        product_data = webshop_env.extract_product_details()
        products.append(product_data)
        webshop_env.step("click[< Prev]")  # Return to listing

    # Create comparison table
    headers = ["Feature"] + [p["name"][:30] for p in products]
    rows = [
        ["Price"] + [f"${p['price']}" for p in products],
        ["Rating"] + [f"{p['rating']}/5" for p in products],
        ["Reviews"] + [str(p['review_count']) for p in products],
        ["Availability"] + [p['stock_status'] for p in products],
    ]

    # Add feature comparison
    all_features = set()
    for p in products:
        all_features.update(p.get('features', []))

    for feature in sorted(all_features):
        row = [feature]
        for p in products:
            row.append("✓" if feature in p.get('features', []) else "✗")
        rows.append(row)

    table = tabulate(rows, headers=headers, tablefmt="grid")

    return f"Product Comparison:\n\n{table}"
```

**Add to agent.py** tools list.

**Impact**: Allows users to see side-by-side comparisons of multiple products.

### 6. Add Shopping Cart Functionality

**Location**: Create new file `personalized_shopping/tools/cart.py`

**Implementation**:
```python
from google.adk.tools import ToolContext

# Global shopping cart (in production, use session-based storage)
shopping_cart = []

async def add_to_cart(
    product_id: str,
    quantity: int = 1,
    size: str = None,
    color: str = None,
    tool_context: ToolContext = None
) -> str:
    """Add a product to the shopping cart.

    Args:
      product_id: Product identifier
      quantity: Number of items
      size: Selected size
      color: Selected color
      tool_context: The function context

    Returns:
      str: Confirmation message with cart summary
    """
    from ..shared_libraries.init_env import get_webshop_env

    webshop_env = get_webshop_env()

    # Get product details
    webshop_env.step(f"click[{product_id}]")
    product = webshop_env.extract_product_details()
    webshop_env.step("click[< Prev]")

    cart_item = {
        "id": product_id,
        "name": product["name"],
        "price": product["price"],
        "quantity": quantity,
        "size": size,
        "color": color,
        "subtotal": product["price"] * quantity
    }

    shopping_cart.append(cart_item)

    total = sum(item["subtotal"] for item in shopping_cart)

    return f"""Added to cart: {quantity}x {product['name']}
Size: {size or 'N/A'}, Color: {color or 'N/A'}
Subtotal: ${cart_item['subtotal']:.2f}

Cart Total: ${total:.2f} ({len(shopping_cart)} items)"""

async def view_cart(tool_context: ToolContext = None) -> str:
    """View current shopping cart contents."""
    if not shopping_cart:
        return "Your cart is empty."

    from tabulate import tabulate

    rows = []
    for item in shopping_cart:
        rows.append([
            item["name"][:40],
            item["quantity"],
            item.get("size", "N/A"),
            item.get("color", "N/A"),
            f"${item['subtotal']:.2f}"
        ])

    total = sum(item["subtotal"] for item in shopping_cart)

    table = tabulate(
        rows,
        headers=["Product", "Qty", "Size", "Color", "Subtotal"],
        tablefmt="grid"
    )

    return f"Shopping Cart:\n\n{table}\n\nTotal: ${total:.2f}"

async def checkout(tool_context: ToolContext = None) -> str:
    """Process checkout for items in cart."""
    if not shopping_cart:
        return "Your cart is empty. Add items before checkout."

    total = sum(item["subtotal"] for item in shopping_cart)
    item_count = len(shopping_cart)

    # Clear cart after checkout
    shopping_cart.clear()

    return f"""✓ Checkout complete!
{item_count} items purchased
Total charged: ${total:.2f}
Confirmation email will be sent shortly."""
```

**Update agent.py**:
```python
from .tools.cart import add_to_cart, view_cart, checkout

root_agent = Agent(
    model="gemini-2.5-flash",
    name="personalized_shopping_agent",
    instruction=personalized_shopping_agent_instruction,
    tools=[
        FunctionTool(func=search),
        FunctionTool(func=click),
        FunctionTool(func=add_to_cart),
        FunctionTool(func=view_cart),
        FunctionTool(func=checkout),
    ],
)
```

**Update prompt.py** to include cart management instructions.

**Impact**: Enables multi-item shopping sessions with cart management and batch checkout.

### 7. Customize Evaluation Criteria

**Location**: `/home/user/adk-samples/python/agents/personalized-shopping/eval/eval_data/test_config.json`, lines 2-5

**What to Change**: Adjust evaluation thresholds:

```json
{
    "criteria": {
      "tool_trajectory_avg_score": 0.8,
      "response_match_score": 0.7,
      "custom_metric_name": 0.6
    }
}
```

**Available Criteria**:
- `tool_trajectory_avg_score`: How well agent uses tools (0.0-1.0)
- `response_match_score`: Semantic similarity to reference answer (0.0-1.0)
- Custom ADK evaluation criteria

**Add Custom Eval Dataset** (`eval/eval_data/my_test.json`):
```json
{
  "examples": [
    {
      "query": "Find me running shoes under $100",
      "expected_tools": ["search", "filter_products"],
      "reference_answer": "I found several running shoes under $100..."
    },
    {
      "query": "Compare these two products: ABC123 and XYZ789",
      "expected_tools": ["compare_products"],
      "reference_answer": "Here's a comparison of the two products..."
    }
  ]
}
```

**Impact**: Customizes testing to match your specific use cases and quality standards.

---

## Additional Resources

- **ADK Documentation**: https://google.github.io/adk-docs/
- **WebShop Dataset**: https://github.com/princeton-nlp/WebShop
- **PySerini Documentation**: https://github.com/castorini/pyserini
- **Agent Starter Pack**: https://goo.gle/agent-starter-pack
- **Vertex AI Agent Engine**: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- **Sample Repository**: https://github.com/google/adk-samples

## Acknowledgments

This agent incorporates modified code from [princeton-nlp/WebShop](https://github.com/princeton-nlp/WebShop). We are grateful to the developers for their simulated e-commerce environment and real-world product dataset.

## Disclaimer

This agent sample is provided for illustrative purposes only and is not intended for production use without proper testing, security hardening, and implementation of production-grade features (error handling, logging, scalability, etc.). Users are solely responsible for any further development and deployment.

## License

Copyright 2025 Google LLC - Licensed under Apache License 2.0
