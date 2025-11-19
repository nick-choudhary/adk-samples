# Gemini Fullstack Agent - Technical Documentation Report

## Project Scope

### High-Level Summary
The Gemini Fullstack Agent is a production-ready blueprint for building sophisticated, fullstack research agents powered by Google's Gemini models and the Agent Development Kit (ADK). This agent demonstrates advanced agentic workflows including strategic planning, autonomous research execution, and comprehensive report generation with human-in-the-loop collaboration.

### Core Capabilities
- Strategic multi-step research plan generation with user approval
- Autonomous iterative web search and information gathering
- Intelligent critique and refinement of research findings
- Automatic report synthesis with inline citations
- Real-time progress tracking through interactive timeline
- Multimodal support for complex research tasks

### Primary Use Cases
- Academic and market research requiring comprehensive information synthesis
- Competitive analysis and trend identification
- Technical documentation and report generation
- Due diligence and investigation workflows
- Strategic planning and analysis tasks

### Target Users
- Researchers and analysts requiring AI-assisted investigation
- Product managers conducting market analysis
- Consultants building comprehensive reports
- Academic professionals gathering literature reviews
- Business intelligence teams performing competitive analysis

### Key Innovations/Differentiators
- Two-phase workflow separating planning from execution
- Human-in-the-loop plan approval preventing unwanted research directions
- Automatic source tracking and citation generation
- Iterative research quality evaluation with built-in critic agent
- Production-ready deployment options (Cloud Run, Agent Engine)
- Full-stack architecture with React frontend and FastAPI backend

## Technical Architecture

### Multi-Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                   interactive_planner_agent                     │
│                    (Root Orchestrator)                          │
│  - Converts requests into research plans                       │
│  - Manages human approval loop                                 │
│  - Delegates to research_pipeline                              │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ├─── plan_generator (Tool)
                │    - Creates 5-point research plans
                │    - Classifies tasks as [RESEARCH] or [DELIVERABLE]
                │
                └─── research_pipeline (SequentialAgent)
                     │
                     ├─── section_planner
                     │    - Converts plan into report outline
                     │
                     ├─── section_researcher
                     │    - Executes initial web searches
                     │    - Gathers information per research goal
                     │
                     ├─── iterative_refinement_loop (LoopAgent)
                     │    │
                     │    ├─── research_evaluator
                     │    │    - Critiques research quality
                     │    │    - Generates follow-up queries
                     │    │
                     │    ├─── escalation_checker
                     │    │    - Terminates loop on "pass" grade
                     │    │
                     │    └─── enhanced_search_executor
                     │         - Performs targeted refinement searches
                     │
                     └─── report_composer
                          - Synthesizes final cited report
```

### Code Flow Explanation

**Phase 1: Planning (Lines 389-410 in /home/user/adk-samples/python/agents/gemini-fullstack/app/agent.py)**
1. User submits research topic to `interactive_planner_agent`
2. Agent invokes `plan_generator` tool (lines 182-219) to create structured plan
3. Plan includes 5 action-oriented goals tagged as [RESEARCH] or [DELIVERABLE]
4. User reviews and can request modifications through conversation
5. Upon approval, plan is stored in session state under 'research_plan' key

**Phase 2: Research Execution (Lines 370-387 in /home/user/adk-samples/python/agents/gemini-fullstack/app/agent.py)**
1. `research_pipeline` SequentialAgent begins execution
2. `section_planner` (lines 222-238) converts plan into markdown outline
3. `section_researcher` (lines 241-289) performs initial searches:
   - Processes each [RESEARCH] goal with 4-5 targeted queries
   - Executes google_search for each query
   - Stores findings in 'section_research_findings' state key
   - Callback `collect_research_sources_callback` (lines 59-118) tracks sources
4. `iterative_refinement_loop` (lines 376-384) with max 5 iterations:
   - `research_evaluator` (lines 291-316) grades quality using Feedback schema
   - `escalation_checker` (lines 158-178) terminates on "pass" grade
   - `enhanced_search_executor` (lines 318-337) improves failed research
5. `report_composer` (lines 339-368) generates final report:
   - Uses citation tag system: `<cite source="src-ID"/>`
   - Callback `citation_replacement_callback` (lines 121-154) converts to Markdown links

### Agent Definitions with Roles and Responsibilities

| Agent Name | Type | Model | Role | Key Output |
|------------|------|-------|------|------------|
| `interactive_planner_agent` | LlmAgent | gemini-2.5-flash | Root orchestrator managing planning phase | research_plan |
| `plan_generator` | LlmAgent | gemini-2.5-flash | Creates/refines 5-point research plans | research_plan |
| `section_planner` | LlmAgent | gemini-2.5-flash | Converts plan into markdown outline | report_sections |
| `section_researcher` | LlmAgent | gemini-2.5-flash | Executes initial comprehensive searches | section_research_findings |
| `research_evaluator` | LlmAgent | gemini-2.5-pro | Critiques research quality with structured feedback | research_evaluation |
| `escalation_checker` | BaseAgent | N/A | Controls loop termination on quality pass | escalate event |
| `enhanced_search_executor` | LlmAgent | gemini-2.5-flash | Performs targeted refinement searches | section_research_findings (updated) |
| `report_composer` | LlmAgent | gemini-2.5-pro | Synthesizes final report with citations | final_cited_report |

### Key Libraries and Dependencies

**Backend (from /home/user/adk-samples/python/agents/gemini-fullstack/pyproject.toml)**
- `google-adk>=1.8.0` - Core agent framework
- `fastapi` - Web framework for backend API
- `uvicorn` - ASGI server
- Python 3.10-3.12 required

**Frontend**
- React with Vite - UI framework and build tool
- Tailwind CSS - Utility-first styling
- Shadcn UI - Component library
- TypeScript - Type-safe development

### Tools and Integrations

**Built-in Tools (lines 26, 218, 286, 334 in agent.py)**
- `google_search` - Web search capabilities via Gemini grounding
- `AgentTool(plan_generator)` - Exposes plan_generator as callable tool

**Integration Points**
- Google AI Studio API (via GOOGLE_API_KEY)
- Vertex AI API (via GOOGLE_CLOUD_PROJECT)
- WebSocket for real-time frontend updates
- Session state management via ADK SessionService

### Reasoning Mechanisms

**Structured Output Schemas (lines 35-56 in agent.py)**
```python
class SearchQuery(BaseModel):
    search_query: str  # Targeted web query

class Feedback(BaseModel):
    grade: Literal["pass", "fail"]
    comment: str
    follow_up_queries: list[SearchQuery] | None
```

**Configuration (lines 31-46 in /home/user/adk-samples/python/agents/gemini-fullstack/app/config.py)**
```python
@dataclass
class ResearchConfiguration:
    critic_model: str = "gemini-2.5-pro"      # High-quality evaluation
    worker_model: str = "gemini-2.5-flash"     # Fast execution
    max_search_iterations: int = 5             # Quality refinement limit
```

**Thinking Configuration (lines 245-246, 322-323 in agent.py)**
- Uses `BuiltInPlanner` with `ThinkingConfig(include_thoughts=True)`
- Enables reasoning traces for section_researcher and enhanced_search_executor

## Build & Run Instructions

### Prerequisites

**Required Software**
- Python 3.10 or higher (3.13 not supported)
- Node.js (latest LTS recommended)
- uv package manager: `pip install uv`

**Required Accounts**
- Option A: Google AI Studio API Key (simpler, for development)
  - Get key from: https://aistudio.google.com/app/apikey
- Option B: Google Cloud Project (for production deployment)
  - Vertex AI API enabled
  - Google Cloud SDK installed
  - Billing enabled for production use

### Step-by-Step Installation

**Option A: Google AI Studio (Development)**

1. Clone repository:
```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/gemini-fullstack
```

2. Configure environment:
```bash
echo "GOOGLE_GENAI_USE_VERTEXAI=FALSE" >> app/.env
echo "GOOGLE_API_KEY=YOUR_ACTUAL_API_KEY" >> app/.env
```

3. Install and run:
```bash
make install && make dev
```

**Option B: Google Cloud Vertex AI (Production)**

1. Create project from template:
```bash
python -m venv .venv && source .venv/bin/activate
pip install --upgrade agent-starter-pack
agent-starter-pack create my-fullstack-agent -a adk@gemini-fullstack
cd my-fullstack-agent
```

2. Install and run:
```bash
make install && make dev
```

### Configuration (Environment Variables)

**app/.env for AI Studio**
```bash
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=<your-api-key>
```

**app/.env for Vertex AI**
```bash
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=<project-id>
GOOGLE_CLOUD_LOCATION=us-central1
```

### Running the Agent

**CLI Mode (Development)**
```bash
# From gemini-fullstack directory
cd app
python -m uvicorn main:app --reload --port 8000
```

**Web UI Mode (Recommended)**
```bash
# Starts both backend (port 8000) and frontend (port 5173)
make dev
```

Access at: http://localhost:5173

### Example Interactions

**Example 1: Technology Research**
```
User: Create a report on quantum computing advancements in 2024

Agent: Here's a research plan:
• Analyze key quantum computing breakthroughs announced in 2024
• Identify leading companies and research institutions in the field
• Investigate practical applications and commercial deployments
• Examine challenges and limitations facing the technology
• Assess the implications for industries and future development

Does this plan look good, or would you like to refine it further?

User: Add a section on quantum error correction

Agent: I've updated the plan:
[Previous 5 points remain]
• [RESEARCH][NEW] Investigate advances in quantum error correction techniques

Would you like to proceed with this plan?

User: Yes, execute it

Agent: [Autonomously executes research, showing timeline progress]
[Generates comprehensive report with inline citations]
```

### Testing and Evaluation

**Run Tests**
```bash
# From gemini-fullstack directory
pytest tests/
```

**Evaluation Criteria**
- Plan quality: Does plan comprehensively cover topic?
- Research depth: Are findings thorough with credible sources?
- Citation accuracy: Are sources properly linked and formatted?
- Report coherence: Is final output well-structured and readable?

### Deployment (Production)

**Deploy to Cloud Run**
```bash
gcloud config set project YOUR_PROJECT_ID
make backend
```

**Deploy to Agent Engine**
```bash
# Follow Agent Starter Pack guide
# https://googlecloudplatform.github.io/agent-starter-pack/guide/development-guide.html
```

**Production Checklist**
- Set up CI/CD pipelines
- Configure monitoring and logging
- Implement rate limiting
- Add authentication/authorization
- Set up error tracking (e.g., Sentry)
- Configure auto-scaling policies

### Troubleshooting

**Issue: "Module not found" errors**
```bash
# Reinstall dependencies
make clean
make install
```

**Issue: Frontend can't connect to backend**
- Verify backend running on port 8000
- Check CORS configuration in FastAPI
- Ensure .env file exists in app/ directory

**Issue: Authentication failures**
```bash
# For Vertex AI
gcloud auth application-default login
gcloud auth application-default set-quota-project PROJECT_ID
```

**Issue: Search quota exceeded**
- Check API quotas in Google Cloud Console
- Reduce max_search_iterations in config.py
- Implement exponential backoff

## Customization Options

### 1. Modify Research Models and Parameters

**File:** `/home/user/adk-samples/python/agents/gemini-fullstack/app/config.py` (lines 31-46)

Change the models used and iteration limits:
```python
@dataclass
class ResearchConfiguration:
    critic_model: str = "gemini-2.0-flash-exp"  # Use faster model for evaluation
    worker_model: str = "gemini-2.5-pro"        # Use better model for research
    max_search_iterations: int = 3              # Reduce iterations for speed
```

**Impact:** Faster execution with potentially lower quality, or vice versa. Adjusting iterations affects research depth and API costs.

### 2. Customize Planning Instructions

**File:** `/home/user/adk-samples/python/agents/gemini-fullstack/app/agent.py` (lines 186-217)

Modify the plan_generator instruction to change planning behavior:
```python
plan_generator = LlmAgent(
    model=config.worker_model,
    name="plan_generator",
    instruction=f"""
    You are a research strategist specializing in technical documentation.
    Create plans with 7 goals instead of 5, focusing heavily on:
    1. Technical specifications and architecture
    2. Code examples and implementation details
    3. Performance benchmarks and comparisons

    Each goal must include specific metrics to investigate.
    Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
    """,
    tools=[google_search],
)
```

**Impact:** Changes plan structure and focus area to match specific domain requirements.

### 3. Add Custom Tools for Domain-Specific Research

**File:** `/home/user/adk-samples/python/agents/gemini-fullstack/app/agent.py` (lines 241-289)

Add custom tools to section_researcher:
```python
from google.adk.tools import Tool
from pydantic import BaseModel

class DatabaseQueryInput(BaseModel):
    query: str

def query_internal_database(query: str) -> str:
    """Query company's internal knowledge base."""
    # Your database query logic here
    return f"Results for: {query}"

database_tool = Tool(
    name="query_internal_database",
    description="Search internal company knowledge base",
    input_schema=DatabaseQueryInput,
    function=query_internal_database
)

section_researcher = LlmAgent(
    model=config.worker_model,
    name="section_researcher",
    tools=[google_search, database_tool],  # Add custom tool
    # ... rest of configuration
)
```

**Impact:** Enables research from proprietary data sources alongside public web search.

### 4. Modify Citation Format

**File:** `/home/user/adk-samples/python/agents/gemini-fullstack/app/agent.py` (lines 121-154)

Customize citation_replacement_callback for different citation styles:
```python
def citation_replacement_callback(callback_context: CallbackContext) -> genai_types.Content:
    final_report = callback_context.state.get("final_cited_report", "")
    sources = callback_context.state.get("sources", {})

    def tag_replacer(match: re.Match) -> str:
        short_id = match.group(1)
        if not (source_info := sources.get(short_id)):
            return ""
        # APA-style citation format
        return f" ({source_info.get('domain', 'Source')}, {short_id})"

    processed_report = re.sub(
        r'<cite\s+source\s*=\s*["\']?\s*(src-\d+)\s*["\']?\s*/>',
        tag_replacer,
        final_report,
    )

    # Append references section
    references = "\n\n## References\n\n"
    for short_id, source in sources.items():
        references += f"{short_id}: {source['title']} - {source['url']}\n"

    processed_report += references
    callback_context.state["final_report_with_citations"] = processed_report
    return genai_types.Content(parts=[genai_types.Part(text=processed_report)])
```

**Impact:** Changes citation style from inline links to numbered references with bibliography section.

### 5. Add Progress Notifications

**File:** `/home/user/adk-samples/python/agents/gemini-fullstack/app/agent.py` (lines 241-289)

Add callbacks for progress tracking:
```python
from google.adk.agents.callback_context import CallbackContext

def notify_progress(callback_context: CallbackContext) -> None:
    """Send progress notifications during research."""
    session = callback_context._invocation_context.session

    # Count completed searches
    completed_searches = session.state.get("completed_searches", 0) + 1
    session.state["completed_searches"] = completed_searches

    # Send email/webhook notification
    if completed_searches % 5 == 0:
        # Your notification logic here
        print(f"Progress update: {completed_searches} searches completed")

section_researcher = LlmAgent(
    model=config.worker_model,
    name="section_researcher",
    after_agent_callback=lambda ctx: (
        collect_research_sources_callback(ctx),
        notify_progress(ctx)
    ),
    # ... rest of configuration
)
```

**Impact:** Enables real-time progress tracking and external notifications for long-running research tasks.

### 6. Implement Custom Security Policies

**File:** Create new `/home/user/adk-samples/python/agents/gemini-fullstack/app/security_policy.py`

Add content filtering and access control:
```python
from google.adk.plugins import BasePlugin
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types

class SecurityPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="security_filter")
        self.blocked_domains = ["blocked-site.com"]

    async def after_model_callback(self, callback_context, llm_response):
        """Filter sources from blocked domains."""
        if not llm_response.grounding_metadata:
            return None

        filtered_chunks = [
            chunk for chunk in llm_response.grounding_metadata.grounding_chunks
            if chunk.web and chunk.web.domain not in self.blocked_domains
        ]

        if len(filtered_chunks) < len(llm_response.grounding_metadata.grounding_chunks):
            # Recreate response with filtered chunks
            llm_response.grounding_metadata.grounding_chunks = filtered_chunks

        return llm_response
```

Then attach to Runner in main.py:
```python
runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service,
    plugins=[SecurityPlugin()]
)
```

**Impact:** Implements domain filtering, content moderation, and access control for enterprise security requirements.

### 7. Add Multi-Language Support

**File:** `/home/user/adk-samples/python/agents/gemini-fullstack/app/agent.py` (lines 339-368)

Modify report_composer to support multiple languages:
```python
report_composer = LlmAgent(
    model=config.critic_model,
    name="report_composer_with_citations",
    instruction="""
    Transform the provided data into a polished, professional report.

    LANGUAGE REQUIREMENT: Generate the report in {language}.
    Use native terminology and idiomatic expressions appropriate for {language}.
    Maintain all citations in their original language with translations in parentheses.

    ### INPUT DATA
    *   Research Plan: `{research_plan}`
    *   Research Findings: `{section_research_findings}`
    *   Citation Sources: `{sources}`
    *   Report Structure: `{report_sections}`
    *   Target Language: `{language}`

    [Rest of instructions...]
    """,
    output_key="final_cited_report",
    after_agent_callback=citation_replacement_callback,
)
```

Add language selection to session state:
```python
# In interactive_planner_agent
session.state["language"] = "Spanish"  # or detect from user preferences
```

**Impact:** Enables report generation in multiple languages while preserving source citations and research integrity.

---

**Additional Resources:**
- ADK Documentation: https://google.github.io/adk-docs/
- Agent Starter Pack: https://googlecloudplatform.github.io/agent-starter-pack/
- Gemini API Docs: https://ai.google.dev/docs
