# Academic Research Agent - Technical Documentation Report

## Project Scope

The Academic Research Agent is an AI-driven multi-agent system designed to facilitate comprehensive exploration of the academic landscape surrounding seminal research papers. The agent addresses a critical challenge researchers face: navigating the vast and expanding body of literature influenced by foundational studies.

**Core Capabilities:**
- **Seminal Paper Analysis**: Accepts PDF uploads of foundational research papers and performs deep analysis to extract key insights, innovations, methodologies, and contributions
- **Citation Mapping**: Leverages Google Search to identify and retrieve recent academic publications that cite the seminal paper, tracking its contemporary influence and impact
- **Future Research Direction Synthesis**: Analyzes both the original seminal paper and recent citing literature to propose novel, promising research directions and identify research gaps

**Primary Use Cases:**
- Literature review acceleration for PhD students and researchers
- Understanding the research lineage and impact of foundational papers
- Identifying emerging trends in specific research areas
- Discovering unexplored research opportunities
- Mapping the evolution of scientific ideas over time

**Target Users:**
- Academic researchers and PhD students
- Research institutions and think tanks
- Grant reviewers assessing research impact
- Technology companies tracking academic developments

## Technical Architecture

### Multi-Agent Architecture

The system implements a **hierarchical multi-agent architecture** with one coordinator and two specialized sub-agents:

```
User Query → Academic Coordinator Agent (Root)
              ├─→ Academic WebSearch Agent (finds recent citing papers)
              └─→ Academic NewResearch Agent (suggests future directions)
```

**Agent Hierarchy:**

1. **Academic Coordinator Agent** (`academic_research/agent.py:27-43`):
   - **Model**: Gemini 2.5 Pro
   - **Role**: Orchestrates the entire research workflow
   - **Responsibilities**:
     - Manages user interaction and conversation flow
     - Analyzes uploaded seminal papers (PDF)
     - Delegates citation search to WebSearch sub-agent
     - Delegates future direction synthesis to NewResearch sub-agent
     - Formats and presents results to users
   - **Output Key**: `seminal_paper`

2. **Academic WebSearch Agent** (`academic_research/sub_agents/academic_websearch/agent.py`):
   - **Purpose**: Finds recent papers citing the seminal work
   - **Tools**: Google Search (built-in)
   - **Inputs**: Seminal paper identifiers, timeframe (e.g., "last year")
   - **Outputs**: List of recent citing papers with metadata (title, authors, year, source, link)

3. **Academic NewResearch Agent** (`academic_research/sub_agents/academic_newresearch/agent.py`):
   - **Purpose**: Synthesizes future research directions
   - **Inputs**: Seminal paper analysis + recent citing papers
   - **Outputs**: Structured list of potential research directions with rationales

### Code Flow

**Step-by-Step Workflow** (`academic_research/prompt.py:18-70`):

1. **Initiation Phase**:
   ```
   User uploads PDF → Coordinator greets and requests seminal paper
   ```

2. **Seminal Paper Analysis** (Coordinator):
   - Extracts and structures paper metadata:
     - Title, authors with affiliations
     - Full abstract
     - Narrative summary (5-10 sentences)
     - Key topics and keywords
     - Key innovations (bulleted, up to 5)
     - Complete bibliography/references
   - Builds comprehensive context for subsequent analysis

3. **Recent Citations Search** (WebSearch Sub-Agent):
   ```
   Coordinator → academic_websearch tool
                  ├─ Input: Seminal paper identifiers
                  ├─ Parameter: Timeframe (default: last year)
                  └─ Output: Recent citing papers list
   ```
   - Uses Google Search to find recent academic publications
   - Filters by specified recency (e.g., since January 2025)
   - Returns structured results with full metadata

4. **Future Research Synthesis** (NewResearch Sub-Agent):
   ```
   Coordinator → academic_newresearch tool
                  ├─ Input: Seminal paper summary, keywords, innovations
                  ├─ Input: Recent citing papers from WebSearch
                  └─ Output: Synthesized research directions
   ```
   - Analyzes gaps between seminal work and recent literature
   - Identifies emerging patterns and unexplored areas
   - Generates numbered list of future research directions

5. **Presentation and Conclusion**:
   - Coordinator formats all results with clear headings
   - Presents findings to user
   - Offers to explore specific areas in more depth

### Key Libraries and Dependencies

**Core Framework:**
- `google-adk>=1.0.0` - Google Agent Development Kit for multi-agent orchestration
- `google-cloud-aiplatform[adk,agent-engines]>=1.93.0` - Vertex AI integration
- `google-genai>=1.9.0` - Generative AI capabilities

**Agent Architecture:**
- `google.adk.agents.LlmAgent` - Base class for LLM-powered agents
- `google.adk.tools.agent_tool.AgentTool` - Wraps sub-agents as tools for coordinator

**Configuration and Utilities:**
- `pydantic>=2.10.6` - Data validation and settings management
- `python-dotenv>=1.0.1` - Environment variable management

**Evaluation and Testing:**
- `pytest>=8.3.2` - Testing framework
- `pytest-asyncio>=0.23.7` - Async testing support
- `google-adk[eval]>=1.0.0` - ADK evaluation framework
- `nest-asyncio>=1.6.0` - Nested async event loops
- `pandas>=2.2.3` - Data manipulation for evaluation
- `tabulate>=0.9.0` - Result formatting

**Deployment:**
- `absl-py>=2.2.1` - Command-line flags and logging

### Reasoning Mechanism

The Academic Coordinator implements a **structured sequential reasoning workflow**:

1. **Context Building First**: Always analyzes the seminal paper before searching for citations or suggesting directions. This ensures all subsequent operations are grounded in deep understanding.

2. **Tool-Based Delegation**: Uses `AgentTool` to delegate specialized tasks:
   - Citation search requires domain-specific Google Scholar-style queries
   - Future direction synthesis requires comparing multiple papers

3. **Progressive Information Synthesis**:
   ```
   Seminal Paper → Extract Core Concepts
                 → Find Recent Citations (using concepts as queries)
                 → Identify Gaps and Trends
                 → Synthesize Future Directions
   ```

4. **Structured Output Formatting**: Each phase produces specifically formatted output sections, ensuring consistency and clarity.

### Key Files

- `academic_research/agent.py` - Coordinator agent definition
- `academic_research/prompt.py` - Coordinator workflow instructions
- `academic_research/sub_agents/academic_websearch/agent.py` - Citation search sub-agent
- `academic_research/sub_agents/academic_websearch/prompt.py` - WebSearch instructions
- `academic_research/sub_agents/academic_newresearch/agent.py` - Future research sub-agent
- `academic_research/sub_agents/academic_newresearch/prompt.py` - NewResearch instructions
- `deployment/deploy.py` - Vertex AI Agent Engine deployment
- `deployment/test_deployment.py` - Remote agent interaction script
- `eval/test_eval.py` - Evaluation framework
- `tests/test_agents.py` - Component functionality tests

## Build & Run Instructions

### Prerequisites

1. **Python 3.10, 3.11, or 3.12** (NOT 3.13+)
2. **uv** package manager:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Google Cloud Account** with billing enabled
4. **Google Cloud SDK** (gcloud CLI):
   - Installation: https://cloud.google.com/sdk/docs/install
5. **Git** for repository cloning

### Step 1: Clone Repository and Navigate to Project

```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/academic-research
```

### Step 2: Install Dependencies

```bash
uv sync
```

This creates a virtual environment and installs all required packages.

### Step 3: Configure Environment Variables

**Option A: Shell Environment Variables**

```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1  # or your preferred region
export GOOGLE_CLOUD_STORAGE_BUCKET=your-storage-bucket  # For deployment only
```

**Option B: .env File (Recommended)**

```bash
cp .env.example .env
```

Edit `.env`:
```
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STORAGE_BUCKET=your-storage-bucket
```

### Step 4: Authenticate with Google Cloud

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT
```

### Step 5: Run the Agent

**Option 1: CLI Interface**

```bash
adk run academic_research
```

**Option 2: Web UI Interface**

```bash
adk web
```

- Open the URL printed in the terminal
- Select "academic_research" from the top-left dropdown
- Start chatting in the interface

### Example Interaction Workflow

```
You: who are you

Agent: Hello! I am an AI Research Assistant.

My purpose is to help you explore the academic landscape related to a seminal paper
you're interested in. I can:
- Analyze a seminal paper you provide (Title/Authors, DOI, or URL)
- Find recent academic papers that cite the seminal work using specialized tools
- Suggest potential future research directions based on the analysis and recent findings

How can I help you today? Would you like to provide a seminal paper for analysis?

You: [Upload 1706.03762v7.pdf - "Attention Is All You Need"]

Agent: [Analyzes paper, extracts title, authors, abstract, summary, key innovations]

Agent: [Invokes academic_websearch to find recent citing papers since 2023]

Agent: [Presents list of recent papers citing "Attention Is All You Need"]

Agent: [Invokes academic_newresearch to synthesize future directions]

Agent: Here are potential future research directions:
1. Beyond Dot-Product Attention: Exploring Non-Linear Similarity Metrics
2. Intrinsically Graph-Aware Attention Mechanisms
3. Physics-Informed and Constraint-Driven Attention
...
```

### Step 6: Run Tests

Install development dependencies:
```bash
uv sync --dev
```

Run component tests:
```bash
uv run pytest tests
```

Run evaluation suite:
```bash
uv run pytest eval
```

**What the tests verify:**
- `tests/test_agents.py`: Ensures all agent components are functional
- `eval/test_eval.py`: Evaluates agent responses against expected outputs using ADK's `AgentEvaluator`

### Step 7: Deploy to Vertex AI Agent Engine (Optional)

Install deployment dependencies:
```bash
uv sync --group deployment
```

Create remote agent:
```bash
uv run deployment/deploy.py --create
```

Output:
```
Created remote agent: projects/<PROJECT_NUMBER>/locations/<LOCATION>/reasoningEngines/<AGENT_ENGINE_ID>
```

List existing agents:
```bash
uv run deployment/deploy.py --list
```

### Step 8: Test Deployed Agent

```bash
export USER_ID=researcher_123
uv run deployment/test_deployment.py --resource_id=<AGENT_ENGINE_ID> --user_id=$USER_ID
```

Interaction:
```
Found agent with resource ID: ...
Created session for user ID: researcher_123
Type 'quit' to exit.
Input: Hello. What can you do for me?
Response: Hello! I'm an AI Research Assistant. I can help you analyze a seminal
academic paper. To get started, please provide the seminal paper you wish to
analyze as a PDF.
```

Delete deployed agent:
```bash
uv run deployment/deploy.py --delete --resource_id=<AGENT_ENGINE_ID>
```

## Customization Options

### 1. Integrate Specialized Search Tools

Replace or augment Google Search with ArXiv-specific search:

```python
from google.adk.tools.arxiv_search import ArxivSearch

# Add to academic_websearch_agent tools
arxiv_tool = ArxivSearch(...)
```

### 2. Implement Output Visualization

Add visualization modules for:
- Citation network graphs (using NetworkX, Plotly)
- Research topic clustering
- Timeline of paper influence

### 3. Customize Agent Instructions

Modify prompts in:
- `academic_research/prompt.py` - Coordinator behavior
- `sub_agents/academic_websearch/prompt.py` - Citation search depth
- `sub_agents/academic_newresearch/prompt.py` - Future direction emphasis

Example customization:
```python
# Emphasize interdisciplinary connections
ACADEMIC_COORDINATOR_PROMPT = """
...
When suggesting future research directions, prioritize interdisciplinary
opportunities that bridge multiple fields.
...
"""
```

### 4. Enable DOI/URL-Based Paper Download

Extend the coordinator to download papers directly:

```python
from scholarly import scholarly
import requests

def download_paper_from_doi(doi):
    # Use Unpaywall API or Crossref to resolve DOI to PDF
    ...

def download_paper_from_url(url):
    response = requests.get(url)
    # Save PDF locally
    ...
```

### 5. Integration with Reference Managers

Add automatic export to Zotero, Mendeley, or EndNote:

```python
from pyzotero import zotero

def export_to_zotero(papers):
    zot = zotero.Zotero(library_id, library_type, api_key)
    for paper in papers:
        zot.create_items([paper_metadata])
```

## Production Deployment with Agent Starter Pack

For production-ready deployment with CI/CD:

```bash
# Using pip
python -m venv .venv && source .venv/bin/activate
pip install --upgrade agent-starter-pack
agent-starter-pack create my-academic-research -a adk@academic-research

# Or using uv
uvx agent-starter-pack create my-academic-research -a adk@academic-research
```

Features included:
- Automated CI/CD deployment scripts
- Infrastructure as code templates
- Monitoring and logging configurations
- Security best practices
- Load balancing and scaling

## Performance Characteristics

**Agent Type:** Multi-Agent (1 coordinator + 2 sub-agents)
**Complexity:** Easy
**Model:** Gemini 2.5 Pro (coordinator and sub-agents)
**Interaction Type:** Conversational with file upload support

**Typical Execution Time:**
- Seminal paper analysis: 10-15 seconds
- Recent citation search: 5-10 seconds (depends on search results)
- Future research synthesis: 10-20 seconds
- **Total end-to-end**: ~30-45 seconds

**Resource Requirements:**
- Minimal local compute (LLM runs on Vertex AI)
- Network bandwidth for PDF uploads and API calls
- Vertex AI quota for Gemini Pro API calls

---

**Author:** Antonio Gulli (gulli@google.com)
**License:** Apache 2.0
**Python Version:** 3.10 - 3.12
**Vertical:** Education
