# Marketing Agency - Technical Documentation Report

## Project Scope

The Marketing Agency is an AI-powered multi-agent system designed to streamline and automate the end-to-end process of launching a digital brand presence for creative agencies and businesses.

### Core Capabilities
- **Domain Name Discovery**: Intelligent suggestion of available DNS domains based on brand keywords
- **Professional Website Creation**: Automated generation of complete, responsive website code (HTML, CSS, JavaScript)
- **Marketing Strategy Development**: Comprehensive online marketing campaign planning and strategy formulation
- **Logo Design Generation**: AI-powered logo creation using advanced image generation models
- **Sequential Workflow Orchestration**: Guided step-by-step process from brand concept to complete digital identity

### Primary Use Cases
- New business launches requiring complete digital branding
- Startups needing rapid time-to-market for online presence
- Marketing agencies looking to accelerate client onboarding
- Entrepreneurs exploring brand identity options
- Digital transformation projects requiring comprehensive web assets

### Target Users
- Creative agencies and marketing professionals
- Startup founders and entrepreneurs
- Small business owners
- Digital marketing consultants
- Brand strategists

### Key Innovations/Differentiators
- **Unified Multi-Agent Workflow**: Seamlessly integrates four specialized AI agents into a coherent branding pipeline
- **Real-Time Domain Availability**: Uses Google Search to verify domain availability before suggesting options
- **Production-Ready Website Code**: Generates complete, modern, mobile-responsive website templates
- **AI Image Generation**: Leverages Google's Imagen 3.0 for professional logo creation
- **Conversational Interface**: Natural language interaction guides users through complex branding decisions
- **ADK Framework Integration**: Built on Google's Agent Development Kit for robust agent orchestration

## Technical Architecture

### Multi-Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                  Marketing Coordinator                      │
│                 (Root Agent - LlmAgent)                     │
│                    Model: gemini-2.5-pro                    │
│                                                             │
│  Role: Orchestrates the complete digital branding workflow │
│  File: marketing_agency/agent.py (lines 28-45)            │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┬──────────────┬──────────────┐
        │                     │              │              │
        ▼                     ▼              ▼              ▼
┌───────────────┐   ┌──────────────┐  ┌────────────┐  ┌──────────┐
│ Domain Create │   │Website Create│  │  Marketing │  │   Logo   │
│     Agent     │   │    Agent     │  │   Create   │  │  Create  │
│               │   │              │  │   Agent    │  │  Agent   │
└───────┬───────┘   └──────┬───────┘  └─────┬──────┘  └────┬─────┘
        │                  │                │              │
        ▼                  ▼                ▼              ▼
  Google Search      No Tools        No Tools      Imagen 3.0
   Tool (Built-in)                                generate_image()
                                                  load_artifacts()
```

### Code Flow Explanation

#### 1. Root Agent Initialization
**File**: `/home/user/adk-samples/python/agents/marketing-agency/marketing_agency/agent.py`

- **Lines 28-45**: The `marketing_coordinator` agent is instantiated as an `LlmAgent`
- **Line 30**: Uses `gemini-2.5-pro` model for sophisticated orchestration
- **Line 38**: Loads the main instruction prompt from `prompt.MARKETING_COORDINATOR_PROMPT`
- **Lines 39-44**: Registers four sub-agents as `AgentTool` instances for delegation

#### 2. Workflow Orchestration
**File**: `/home/user/adk-samples/python/agents/marketing-agency/marketing_agency/prompt.py`

- **Lines 17-56**: Defines the complete workflow logic in natural language
- **Lines 22-27**: Step 1 - Domain name selection process
- **Lines 29-32**: Step 2 - Website creation workflow
- **Lines 34-37**: Step 3 - Marketing strategy development
- **Lines 39-42**: Step 4 - Logo design generation
- **Lines 46-54**: Output formatting requirements for tool results

#### 3. Sub-Agent: Domain Create
**File**: `/home/user/adk-samples/python/agents/marketing-agency/marketing_agency/sub_agents/domain_create/agent.py`

- **Lines 24-30**: Agent definition with Google Search tool integration
- **Line 25**: Uses `gemini-2.5-pro` for domain creativity
- **Line 29**: Integrates `google_search` built-in tool for availability verification

**Prompt File**: `marketing_agency/sub_agents/domain_create/prompt.py`
- **Lines 17-41**: Detailed instructions for domain generation and verification
- **Lines 24-28**: Google Search verification process for domain availability
- **Lines 30-36**: Requires generation of 50+ candidates, filtering to 10 available domains

#### 4. Sub-Agent: Website Create
**File**: `/home/user/adk-samples/python/agents/marketing-agency/marketing_agency/sub_agents/website_create/agent.py`

- **Lines 23-28**: Minimal agent configuration for HTML/CSS/JS generation
- **Line 24**: Uses `gemini-2.5-pro` for code generation capabilities
- **Line 26**: References website creation prompt with full stack specifications

#### 5. Sub-Agent: Marketing Create
**File**: `/home/user/adk-samples/python/agents/marketing-agency/marketing_agency/sub_agents/marketing_create/agent.py`

- **Lines 23-28**: Agent for strategic marketing campaign development
- **Line 24**: Uses `gemini-2.5-pro` for comprehensive strategy formulation
- **Line 26**: Loads marketing strategy prompt with targeting and campaign details

#### 6. Sub-Agent: Logo Create
**File**: `/home/user/adk-samples/python/agents/marketing-agency/marketing_agency/sub_agents/logo_create/agent.py`

- **Lines 27-46**: Custom tool `generate_image` for logo generation
  - **Line 29**: Initializes Google GenAI Client
  - **Lines 30-34**: Calls Imagen 3.0 (`imagen-3.0-generate-002`) to generate images
  - **Lines 37-41**: Saves generated image as artifact with proper MIME type
- **Lines 49-59**: Agent configuration with image generation and artifact tools
  - **Line 50**: Uses `gemini-2.5-pro` for prompt engineering and image description
  - **Line 58**: Integrates both `generate_image` and `load_artifacts` tools

### Agent Definitions with Roles and Responsibilities

| Agent | Model | Role | Input | Output | Key Capabilities |
|-------|-------|------|-------|--------|------------------|
| **marketing_coordinator** | gemini-2.5-pro | Orchestrates entire workflow, manages user interaction | User keywords and preferences | Complete digital branding package | Sequential agent delegation, state management, conversational guidance |
| **domain_create_agent** | gemini-2.5-pro | Suggests available domain names | Brand keywords | List of 10 available domain names | Google Search integration, creativity in naming, availability verification |
| **website_create_agent** | gemini-2.5-pro | Generates complete website code | Domain name, brand details | HTML, CSS, JS files for full website | Full-stack code generation, responsive design, modern web standards |
| **marketing_create_agent** | gemini-2.5-pro | Develops marketing strategy | Domain name, target audience | Comprehensive marketing campaign plan | Persona development, channel strategy, content planning, KPI definition |
| **logo_create_agent** | gemini-2.5-pro | Creates brand logo | Domain name, brand identity | Logo image file (PNG) | Imagen 3.0 integration, prompt engineering, artifact management |

### Key Libraries and Dependencies

**File**: `/home/user/adk-samples/python/agents/marketing-agency/pyproject.toml`

- **Lines 8-14**: Core dependencies
  - `google-cloud-aiplatform[adk,agent-engines]>=1.93.0` - ADK framework and Vertex AI integration
  - `google-genai>=1.9.0` - Google GenAI client for Imagen and Gemini models
  - `pydantic>=2.10.6` - Data validation and settings management
  - `python-dotenv>=1.0.1` - Environment variable management
  - `google-adk>=1.0.0` - Agent Development Kit core library

- **Lines 18-25**: Development dependencies
  - `pytest>=8.3.2` - Testing framework
  - `google-adk[eval]>=1.0.0` - Agent evaluation tools
  - `agent-starter-pack>=0.14.1` - Production deployment scaffolding

- **Lines 27-29**: Deployment dependencies
  - `absl-py>=2.2.1` - Application-level utilities

### Tools and Integrations

1. **Google Search Tool** (Built-in ADK Tool)
   - **Location**: `domain_create/agent.py` line 29
   - **Purpose**: Verify domain name availability via web search
   - **Usage**: Searches for exact domain strings to identify active websites

2. **Imagen 3.0 Image Generation**
   - **Location**: `logo_create/agent.py` lines 27-46
   - **Model**: `imagen-3.0-generate-002`
   - **Purpose**: Generate professional logo images from text prompts
   - **Configuration**: Single image generation with PNG output format

3. **Artifact Management**
   - **Location**: `logo_create/agent.py` line 58
   - **Tools**: `load_artifacts` (built-in ADK tool)
   - **Purpose**: Save and retrieve generated files (images, documents)
   - **Implementation**: Stores artifacts with proper MIME types for user download

4. **AgentTool Wrapper**
   - **Location**: `agent.py` lines 18, 39-44
   - **Purpose**: Enables sub-agent invocation from parent agent
   - **Mechanism**: Wraps agent instances as callable tools with automatic state passing

### Reasoning Mechanisms

The Marketing Agency employs a **sequential reasoning workflow** with explicit state management:

1. **Prompted Chain-of-Thought**: Each agent receives detailed instructions in their prompt files defining step-by-step reasoning processes (e.g., `prompt.py` lines 17-56)

2. **Tool-Augmented Generation**: Agents leverage external tools (Google Search, Imagen) to ground their outputs in real-world data and capabilities

3. **Output Key State Management**:
   - `domain_create_output` - Stores selected domain
   - `website_create_output` - Stores generated website code
   - `marketing_create_output` - Stores marketing strategy
   - `logo_create_output` - Stores logo image reference

4. **Conversational State Tracking**: The root agent maintains conversation history to track user decisions and preferences across the multi-step workflow

5. **Verification Loops**: Domain agent iterates through candidate generation and verification until finding 10 available options (domain prompt lines 30-36)

## Build & Run Instructions

### Prerequisites

- **Python**: Version 3.10 or higher (up to 3.12)
- **uv**: Fast Python package installer and resolver ([installation guide](https://docs.astral.sh/uv/))
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Google Cloud Platform**: Active GCP project with billing enabled
- **Google Cloud CLI**: For authentication and project configuration ([installation guide](https://cloud.google.com/sdk/docs/install))
- **Required GCP APIs**:
  - Vertex AI API
  - Cloud Storage API
  - Generative AI API

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/google/adk-samples.git
   cd adk-samples/python/agents/marketing-agency
   ```

2. **Install Dependencies**
   ```bash
   # Install package and core dependencies
   uv sync

   # For development and testing (optional)
   uv sync --dev

   # For deployment capabilities (optional)
   uv sync --group deployment
   ```

3. **Verify Installation**
   ```bash
   uv run python -c "import google.adk; print('ADK installed successfully')"
   ```

### Configuration (Environment Variables)

1. **Create Environment File**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   ```

2. **Set Required Environment Variables**

   Edit `.env` or export in your shell:

   ```bash
   # Core configuration
   export GOOGLE_GENAI_USE_VERTEXAI=true
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export GOOGLE_CLOUD_LOCATION=us-central1

   # For deployment only (optional)
   export GOOGLE_CLOUD_STORAGE_BUCKET=your-storage-bucket-name
   ```

   **Configuration Details**:
   - `GOOGLE_GENAI_USE_VERTEXAI`: Enables Vertex AI backend for Gemini models
   - `GOOGLE_CLOUD_PROJECT`: Your GCP project ID (find in GCP Console)
   - `GOOGLE_CLOUD_LOCATION`: Region for Vertex AI (recommend `us-central1` or `europe-west4`)
   - `GOOGLE_CLOUD_STORAGE_BUCKET`: Cloud Storage bucket for agent deployment artifacts

3. **Authenticate with Google Cloud**
   ```bash
   # Authenticate your account
   gcloud auth application-default login

   # Set quota project
   gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT

   # Verify authentication
   gcloud config list
   ```

### Running the Agent

#### CLI Interface

Start an interactive conversation with the agent via command line:

```bash
adk run marketing_agency
```

**Example Interaction**:
```
You: who are you
Agent: I am a marketing expert, and my goal is to help you establish a powerful
online presence and connect effectively with your audience. I will guide you
through defining your digital identity, from choosing the perfect domain name
and crafting a professional website, to strategizing online marketing campaigns,
designing a memorable logo, and creating engaging short videos.

What keywords are relevant to your brand? I'll use them to suggest some domain names.

You: i want to sell organic cakes
Agent: Great! I'll use "organic" and "cakes" as keywords to find some domain
name options for you.

[Agent searches and returns 10 available domain names]
```

#### Web UI Interface

Launch a browser-based chat interface:

```bash
adk web
```

**Steps**:
1. Command starts local web server and prints URL (typically `http://localhost:8000`)
2. Open URL in your browser
3. Select "marketing_agency" from the dropdown menu in top-left
4. Interact via the chatbot interface on the right panel

### Example Interactions

#### Complete Branding Workflow

**Step 1: Domain Selection**
```
User: Help me find a domain for my organic cake business

Agent: Okay, I can help with that! To start, please tell me some keywords
relevant to your brand. For example, if you're selling handmade jewelry,
keywords might be "handmade," "jewelry," "artisan," "unique," "gifts."

User: organic cakes artisan

Agent: [Searches and presents 10 available domains]
1. PureOrganicBakes.com
2. EarthlyCakes.com
3. ArtisanOrganicCakes.com
...

Please review this list and let me know which domain name you'd like to choose.

User: I like #3 - ArtisanOrganicCakes.com
```

**Step 2: Website Creation**
```
Agent: Excellent choice! "ArtisanOrganicCakes.com" sounds lovely.
Next, we'll move on to crafting a professional website for your chosen domain.

Before we can create the website, I need a little more information:
1. Brand/Project Name: Should we use "Artisan Organic Cakes" or do you have
   an official brand name?
2. Primary Goal/Purpose of the Website
3. Key services, products, or information to be featured

User: The brand is "Sweet Earth Bakery", target young professionals age 25-40,
need product gallery and online ordering capability

Agent: [Generates complete HTML, CSS, and JavaScript files for a professional website]
```

**Step 3: Marketing Strategy**
```
Agent: Great! Now let's develop a marketing strategy for "ArtisanOrganicCakes.com".
[Generates comprehensive marketing campaign with target personas, channel strategy,
content calendar, and KPIs]
```

**Step 4: Logo Design**
```
Agent: Finally, let's create a memorable logo for "Sweet Earth Bakery".
[Generates and displays logo image using Imagen 3.0]

Would you like me to create a different design?
```

### Testing and Evaluation

#### Run Unit Tests

```bash
# Ensure dev dependencies are installed
uv sync --dev

# Run functional tests
uv run pytest tests

# Expected output:
# tests/test_agents.py::test_marketing_agency PASSED
```

**Test File**: `tests/test_agents.py`
- Validates all agents initialize correctly
- Tests basic conversation flow
- Verifies tool integrations

#### Run Evaluation Suite

```bash
# Run agent evaluation
uv run pytest eval

# Expected output:
# eval/test_eval.py::test_agent_evaluation PASSED
```

**Evaluation File**: `eval/test_eval.py`
- Sends predefined requests to agent
- Compares responses against expected outputs using ADK's `AgentEvaluator`
- Measures response quality and consistency

### Deployment (Optional)

#### Deploy to Vertex AI Agent Engine

1. **Prepare Environment**
   ```bash
   # Install deployment dependencies
   uv sync --group deployment

   # Ensure storage bucket exists
   gcloud storage buckets create gs://$GOOGLE_CLOUD_STORAGE_BUCKET \
     --location=$GOOGLE_CLOUD_LOCATION
   ```

2. **Create Deployment**
   ```bash
   uv run deployment/deploy.py --create
   ```

   **Output**:
   ```
   Deploying agent to Vertex AI...
   Created remote agent: projects/123456/locations/us-central1/reasoningEngines/789012
   ```

3. **List Deployed Agents**
   ```bash
   uv run deployment/deploy.py --list
   ```

   **Output**:
   ```
   All remote agents:

   789012 ("marketing_agency")
   - Create time: 2025-11-19 10:30:45.123456+00:00
   - Update time: 2025-11-19 10:32:10.654321+00:00
   ```

4. **Interact with Deployed Agent**
   ```bash
   export USER_ID=user123
   export AGENT_ENGINE_ID=789012

   uv run deployment/test_deployment.py \
     --resource_id=${AGENT_ENGINE_ID} \
     --user_id=${USER_ID}
   ```

   **Interactive Session**:
   ```
   Found agent with resource ID: 789012
   Created session for user ID: user123
   Type 'quit' to exit.
   Input: Hello. What can you do for me?
   Response: I am a marketing expert...
   ```

5. **Delete Deployment**
   ```bash
   uv run deployment/deploy.py --delete --resource_id=${AGENT_ENGINE_ID}
   ```

#### Alternative: Agent Starter Pack Deployment

For production-ready deployment with CI/CD:

```bash
# Create production project structure
uvx agent-starter-pack create my-marketing-agency -a adk@marketing-agency

# Follow prompts to select:
# - Cloud Run deployment
# - GitHub Actions CI/CD
# - Monitoring and logging
```

### Troubleshooting

#### Issue: "Module 'google.adk' not found"
**Solution**: Ensure virtual environment is activated and dependencies are installed
```bash
uv sync
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### Issue: "Authentication failed"
**Solution**: Re-authenticate with Google Cloud
```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT
```

#### Issue: "Quota exceeded" errors
**Solution**: Check Vertex AI API quotas in GCP Console
- Navigate to: APIs & Services > Enabled APIs > Vertex AI API > Quotas
- Request quota increase if needed

#### Issue: "Domain suggestions not working"
**Solution**: Verify Google Search tool is accessible
- Ensure Custom Search API is enabled in GCP Console
- Check that the agent has proper tool permissions

#### Issue: "Imagen 3.0 not available"
**Solution**: Verify region and API access
```bash
# Imagen is available in limited regions, try us-central1
export GOOGLE_CLOUD_LOCATION=us-central1

# Ensure Generative AI API is enabled
gcloud services enable generativelanguage.googleapis.com
```

#### Issue: "Slow response times"
**Solution**:
- Gemini 2.5 Pro can be slower for complex tasks
- Consider using `gemini-2.5-flash` for faster responses (edit `agent.py` line 26)
- Deploy to Agent Engine for improved latency

## Customization Options

### 1. Add Video Generation with Veo Integration

**Goal**: Extend the agent to create promotional videos after logo generation.

**Implementation**:

Create new sub-agent file: `marketing_agency/sub_agents/video_create/agent.py`

```python
from google.adk import Agent
from google.genai import Client, types

MODEL = "gemini-2.5-pro"
MODEL_VIDEO = "veo-002"  # Google Veo video generation

async def generate_video(video_prompt: str, tool_context: "ToolContext"):
    """Generates a promotional video based on the prompt."""
    client = Client()
    response = client.models.generate_video(
        model=MODEL_VIDEO,
        prompt=video_prompt,
        config={
            "duration_seconds": 15,
            "resolution": "1080p",
            "aspect_ratio": "16:9"
        },
    )
    if not response.generated_videos:
        return {"status": "failed"}

    video_bytes = response.generated_videos[0].video.video_bytes
    await tool_context.save_artifact(
        "promo_video.mp4",
        types.Part.from_bytes(data=video_bytes, mime_type="video/mp4"),
    )
    return {
        "status": "success",
        "detail": "Video generated successfully",
        "filename": "promo_video.mp4",
    }

video_create_agent = Agent(
    model=MODEL,
    name="video_create_agent",
    instruction="Generate engaging 15-second promotional videos based on brand identity",
    output_key="video_create_output",
    tools=[generate_video, load_artifacts],
)
```

**Update root agent** (`marketing_agency/agent.py` line 40):
```python
from .sub_agents.video_create import video_create_agent

tools=[
    AgentTool(agent=domain_create_agent),
    AgentTool(agent=website_create_agent),
    AgentTool(agent=marketing_create_agent),
    AgentTool(agent=logo_create_agent),
    AgentTool(agent=video_create_agent),  # Add this line
]
```

**Update workflow prompt** (`marketing_agency/prompt.py` after line 42):
```python
5.  **Creating promotional videos (Subagent: video_create)**
    * **Input:** The domain name and brand identity established in previous steps.
    * **Action:** Call the `video_create` subagent with brand details.
    * **Expected Output:** The `video_create` subagent should generate a short
      promotional video file (MP4).
```

### 2. Implement Real-Time Domain Registration API

**Goal**: Replace Google Search verification with actual domain registrar API calls for guaranteed availability.

**Implementation**:

Install domain API client:
```bash
# Add to pyproject.toml dependencies
"python-whois>=0.8.0",
"godaddypy>=2.4.6",  # or namecheap-api, etc.
```

Create domain verification tool: `marketing_agency/sub_agents/domain_create/tools.py`

```python
import whois
from godaddypy import Client, Account

def check_domain_availability(domain: str) -> dict:
    """
    Checks domain availability using WHOIS and registrar API.

    Args:
        domain: Domain name to check (e.g., "example.com")

    Returns:
        dict with 'available' boolean and 'details'
    """
    try:
        # WHOIS lookup
        w = whois.whois(domain)
        if w.domain_name:
            return {
                "available": False,
                "details": f"Domain registered to {w.registrar}"
            }
    except whois.parser.PywhoisError:
        pass  # Domain might be available

    # Verify with registrar API (example: GoDaddy)
    api_key = os.getenv("GODADDY_API_KEY")
    api_secret = os.getenv("GODADDY_API_SECRET")

    account = Account(api_key=api_key, api_secret=api_secret)
    client = Client(account)

    available = client.check_availability(domain)

    return {
        "available": available,
        "details": "Available for registration" if available else "Taken"
    }
```

**Update agent** (`marketing_agency/sub_agents/domain_create/agent.py`):
```python
from .tools import check_domain_availability

domain_create_agent = Agent(
    model=MODEL,
    name="domain_create_agent",
    instruction=prompt.DOMAIN_CREATE_PROMPT,
    output_key="domain_create_output",
    tools=[check_domain_availability],  # Replace google_search
)
```

**Update prompt** to use new tool instead of Google Search (lines 24-28).

### 3. Enable Persistent Website Storage and Version Control

**Goal**: Save generated websites to Cloud Storage with version history.

**Implementation**:

Create storage tool: `marketing_agency/sub_agents/website_create/tools.py`

```python
from google.cloud import storage
from datetime import datetime
import json

def save_website_to_storage(
    domain_name: str,
    html_files: dict,
    css_files: dict,
    js_files: dict
) -> str:
    """
    Saves website files to Cloud Storage with versioning.

    Args:
        domain_name: Domain name for folder organization
        html_files: Dict of {filename: content}
        css_files: Dict of {filename: content}
        js_files: Dict of {filename: content}

    Returns:
        GCS URL of saved website
    """
    bucket_name = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"websites/{domain_name}/{timestamp}/"

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Save metadata
    metadata = {
        "domain": domain_name,
        "created_at": timestamp,
        "version": timestamp,
        "file_count": len(html_files) + len(css_files) + len(js_files)
    }

    metadata_blob = bucket.blob(f"{base_path}metadata.json")
    metadata_blob.upload_from_string(
        json.dumps(metadata, indent=2),
        content_type="application/json"
    )

    # Save HTML files
    for filename, content in html_files.items():
        blob = bucket.blob(f"{base_path}html/{filename}")
        blob.upload_from_string(content, content_type="text/html")

    # Save CSS files
    for filename, content in css_files.items():
        blob = bucket.blob(f"{base_path}css/{filename}")
        blob.upload_from_string(content, content_type="text/css")

    # Save JS files
    for filename, content in js_files.items():
        blob = bucket.blob(f"{base_path}js/{filename}")
        blob.upload_from_string(content, content_type="application/javascript")

    gcs_url = f"gs://{bucket_name}/{base_path}"
    return f"Website saved to {gcs_url}"
```

**Update agent** (`marketing_agency/sub_agents/website_create/agent.py`):
```python
from .tools import save_website_to_storage

website_create_agent = Agent(
    model=MODEL,
    name="website_create_agent",
    instruction=prompt.WEBSITE_CREATE_PROMPT + "\nAfter generating website code, call save_website_to_storage to persist files.",
    output_key="website_create_output",
    tools=[save_website_to_storage],
)
```

### 4. Add Multi-Language Support

**Goal**: Generate websites and marketing materials in multiple languages.

**Implementation**:

Update root agent prompt (`marketing_agency/prompt.py` after line 20):

```python
* **Input:** Ask the user for their preferred language(s) for the website and
  marketing materials (e.g., English, Spanish, French, Japanese).
* **Action:** Pass the language preference to all subsequent subagents.
```

Modify website agent instruction to include translation:

```python
WEBSITE_CREATE_PROMPT = """
Generate a complete website in the user's specified language(s).
For multi-language sites, create language selector navigation and separate
content files for each language.

Supported languages: English, Spanish, French, German, Japanese, Chinese,
Portuguese, Italian, Dutch, Korean.

Structure:
- index_en.html, index_es.html, etc. for each language
- Shared CSS and JS files
- Language detection and redirect logic
"""
```

Add translation tool using Google Translation API:

```python
from google.cloud import translate_v2 as translate

def translate_content(text: str, target_language: str) -> str:
    """Translates text to target language using Google Cloud Translation."""
    client = translate.Client()
    result = client.translate(text, target_language=target_language)
    return result['translatedText']
```

### 5. Customize Agent Models and Temperature

**Goal**: Fine-tune performance by using different models or temperature settings.

**Implementation**:

**Option A: Use faster Gemini Flash model for quicker responses**

Edit each agent file (e.g., `domain_create/agent.py`):

```python
# Change line 22 from:
MODEL = "gemini-2.5-pro"
# To:
MODEL = "gemini-2.5-flash"
```

Trade-offs:
- Flash: Faster (2-3x), lower cost, slightly lower quality for complex tasks
- Pro: Slower, higher cost, better reasoning and creativity

**Option B: Adjust temperature for creativity vs. consistency**

Edit agent instantiation to add temperature config:

```python
from google.genai import types

logo_create_agent = Agent(
    model=MODEL,
    name="logo_create_agent",
    instruction=prompt.LOGO_CREATE_PROMPT,
    output_key="logo_create_output",
    tools=[generate_image, load_artifacts],
    generate_content_config=types.GenerateContentConfig(
        temperature=1.2,  # Higher = more creative (0.0 - 2.0)
        top_p=0.95,       # Nucleus sampling
        top_k=40,         # Top-k sampling
    ),
)
```

Temperature recommendations:
- Domain names: 1.0-1.2 (creative but relevant)
- Website code: 0.3-0.5 (consistent, correct syntax)
- Marketing strategy: 0.7-0.9 (balanced creativity)
- Logo prompts: 1.0-1.4 (highly creative)

### 6. Integrate Analytics and SEO Optimization

**Goal**: Add analytics tracking and SEO metadata to generated websites.

**Implementation**:

Update website creation prompt to include:

```python
WEBSITE_CREATE_PROMPT = """
...existing prompt...

SEO Requirements:
1. Add comprehensive <meta> tags to all HTML files:
   - meta description (150-160 characters)
   - meta keywords
   - Open Graph tags for social media
   - Twitter Card tags

2. Implement proper heading hierarchy (H1, H2, H3)

3. Add schema.org structured data (JSON-LD) for:
   - Organization
   - LocalBusiness (if applicable)
   - Product listings

4. Generate sitemap.xml file

5. Create robots.txt file

6. Include Google Analytics 4 tracking code:
   <!-- Google tag (gtag.js) -->
   <script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
   <script>
     window.dataLayer = window.dataLayer || [];
     function gtag(){dataLayer.push(arguments);}
     gtag('js', new Date());
     gtag('config', 'GA_MEASUREMENT_ID');
   </script>

7. Add alt text to all images for accessibility and SEO
"""
```

Create SEO analysis tool:

```python
def analyze_seo(html_content: str) -> dict:
    """Analyzes HTML for SEO best practices."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, 'html.parser')

    analysis = {
        "has_title": bool(soup.find('title')),
        "has_meta_description": bool(soup.find('meta', attrs={'name': 'description'})),
        "has_h1": bool(soup.find('h1')),
        "h1_count": len(soup.find_all('h1')),
        "images_without_alt": len([img for img in soup.find_all('img') if not img.get('alt')]),
        "has_analytics": "gtag" in html_content or "analytics" in html_content,
        "recommendations": []
    }

    if analysis["h1_count"] != 1:
        analysis["recommendations"].append("Should have exactly one H1 tag")
    if analysis["images_without_alt"] > 0:
        analysis["recommendations"].append(f"Add alt text to {analysis['images_without_alt']} images")

    return analysis
```

### 7. Add Social Media Content Generation

**Goal**: Generate social media posts and ad copy alongside marketing strategy.

**Implementation**:

Create social media agent: `marketing_agency/sub_agents/social_media_create/agent.py`

```python
SOCIAL_MEDIA_PROMPT = """
Generate comprehensive social media content for the brand.

For each major platform, create:

**Instagram:**
- 10 post captions (varied: promotional, educational, behind-the-scenes)
- 5 Instagram Story scripts
- 10 relevant hashtag sets (#hashtag1 #hashtag2 ...)
- Reel ideas (15-30 second concepts)

**Facebook:**
- 10 post variations (longer form than Instagram)
- 3 Facebook Ad copy variations
- Event descriptions (if applicable)

**Twitter/X:**
- 20 tweet variations (280 characters or less)
- Thread concepts (5-7 connected tweets)

**LinkedIn:**
- 5 professional posts
- Company page description
- Article topics for thought leadership

**TikTok:**
- 10 video script concepts (15-60 seconds)
- Trending audio suggestions
- Hashtag challenges

**Pinterest:**
- 15 pin descriptions
- Board organization strategy

Content should:
- Match brand voice and identity
- Include clear CTAs (Call-to-Action)
- Be optimized for each platform's algorithm
- Incorporate relevant keywords and hashtags
- Suggest posting schedule and frequency
"""

social_media_create_agent = Agent(
    model="gemini-2.5-pro",
    name="social_media_create_agent",
    instruction=SOCIAL_MEDIA_PROMPT,
    output_key="social_media_output",
)
```

Register in root agent's tools list and add to workflow sequence.

---

**End of Marketing Agency Technical Documentation**
