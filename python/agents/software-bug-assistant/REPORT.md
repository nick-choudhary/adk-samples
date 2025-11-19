# Software Bug Assistant - Technical Documentation Report

## Project Scope

The Software Bug Assistant is a production-ready AI agent designed to help IT Support teams and Software Developers efficiently triage, manage, and resolve software issues through intelligent automation and context-aware assistance.

### Core Capabilities
- **Intelligent Ticket Management**: Create, update, search, and manage bug tickets in a PostgreSQL database with vector-based semantic search
- **RAG-Powered Duplicate Detection**: Leverage Retrieval-Augmented Generation (RAG) with Cloud SQL's Vertex AI ML Integration to identify similar or duplicate issues
- **External Issue Tracking**: Connect to GitHub repositories to search and retrieve external bug reports, pull requests, and issues
- **Knowledge Base Integration**: Query StackOverflow for community-driven solutions and best practices
- **Web Search Grounding**: Use Google Search to find relevant documentation, CVE details, and real-time information
- **Conversational Interface**: Natural language interaction for triaging bugs, analyzing patterns, and providing debugging assistance

### Primary Use Cases
- Triaging incoming bug reports and assigning appropriate priority levels
- Finding duplicate or related tickets to avoid redundant work
- Researching known issues, CVEs, and security vulnerabilities
- Discovering solutions from community resources like StackOverflow
- Managing ticket lifecycle (status updates, priority changes, assignments)
- Analyzing patterns across internal and external bug databases

### Target Users
- IT Support Engineers responding to software incidents
- Software Developers investigating and resolving bugs
- Engineering Managers tracking issue resolution and team workload
- QA Teams managing bug lifecycles and testing workflows

### Key Innovations/Differentiators
- **Multi-Source Intelligence**: Combines internal database, GitHub MCP server, StackOverflow, and Google Search in a single conversational interface
- **Native Vector Search**: Uses Cloud SQL's built-in Vertex AI integration for semantic similarity matching without external vector databases
- **MCP Protocol Integration**: Demonstrates both local MCP toolbox usage (databases) and remote MCP server integration (GitHub)
- **Production-Ready Deployment**: Full Cloud Run deployment guide with Cloud SQL, Secret Manager, and IAM configuration
- **Tool Diversity Showcase**: Exemplifies ADK's support for function tools, built-in tools, third-party LangChain tools, and MCP toolsets

## Technical Architecture

### Agent Type
**Single Agent Architecture** with multiple tool integrations

The Software Bug Assistant uses a single-agent design pattern where one root agent (`software_assistant`) orchestrates all tool calls based on user intent. There are no sub-agents; instead, the architecture demonstrates a specialized "search agent" wrapped as an AgentTool for Google Search capabilities.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Software Bug Assistant                      │
│                    (Single Agent: Gemini 2.5)                   │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├──────────────┬──────────────┬──────────────┬────────────────┬─────────────────┐
             │              │              │              │                │                 │
             ▼              ▼              ▼              ▼                ▼                 ▼
    ┌────────────────┐ ┌─────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────────┐ ┌──────────┐
    │ Function Tool  │ │Built-in │ │  AgentTool   │ │Toolbox   │ │   MCP Toolset    │ │LangChain │
    │get_current_date│ │  Tool   │ │(search_agent)│ │  Tools   │ │  (GitHub MCP)    │ │   Tool   │
    └────────────────┘ └─────────┘ └──────────────┘ └──────────┘ └──────────────────┘ └──────────┘
                           │              │              │                │                 │
                           │              │              │                │                 │
                           ▼              ▼              ▼                ▼                 ▼
                    ┌────────────┐ ┌───────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                    │   Google   │ │  Gemini   │ │ PostgreSQL   │ │GitHub Remote │ │ StackExchange│
                    │   Search   │ │2.5 Flash  │ │  Database    │ │  MCP Server  │ │     API      │
                    └────────────┘ └───────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                                                        │
                                                        ▼
                                                  ┌──────────────┐
                                                  │ Vertex AI ML │
                                                  │ Integration  │
                                                  │(text-embed-  │
                                                  │ ding-005)    │
                                                  └──────────────┘
```

### Code Flow Explanation

**Entry Point**: `/home/user/adk-samples/python/agents/software-bug-assistant/software_bug_assistant/agent.py`

1. **Agent Initialization** (Lines 28-33)
   - Creates the root agent `software_assistant` using Gemini 2.5 Flash model
   - Loads instruction prompt from `prompt.py`
   - Assembles tools list by conditionally adding available tools
   - Filters out empty/None tool values to handle unavailable services gracefully

2. **Tool Loading** (Lines 21-26)
   - Base tools: `get_current_date`, `search_tool`, `langchain_tool` (always available)
   - Conditionally extends with `toolbox_tools` if MCP Toolbox server is reachable
   - Conditionally appends `mcp_tools` (GitHub) if authentication token is provided

**Tool Definitions**: `/home/user/adk-samples/python/agents/software-bug-assistant/software_bug_assistant/tools/tools.py`

3. **Function Tool** (Lines 35-39)
   - `get_current_date()`: Simple Python function returning current date in YYYY-MM-DD format
   - Used for date-based ticket queries ("tickets opened this week")

4. **Built-in Tool + AgentTool** (Lines 43-52)
   - Creates specialized `search_agent` using Gemini 2.5 Flash
   - Equipped with `google_search` built-in tool
   - Wrapped as `AgentTool` to delegate web search queries
   - Demonstrates ADK's ability to compose agents as tools

5. **Third-Party LangChain Tool** (Lines 55-57)
   - Instantiates `StackExchangeTool` from LangChain community
   - Wrapped with `LangchainTool` adapter for ADK compatibility
   - Enables querying StackOverflow for community solutions

6. **MCP Toolbox (Database Tools)** (Lines 60-69)
   - Connects to MCP Toolbox server (default: `http://127.0.0.1:5000`)
   - Loads `tickets_toolset` containing 9 PostgreSQL tools defined in `deployment/mcp-toolbox/tools.yaml`
   - Gracefully handles unavailable server (returns empty list)
   - Tools include: search-tickets, get-ticket-by-id, create-new-ticket, update operations, filtered queries

7. **MCP Remote Server (GitHub)** (Lines 73-94)
   - Connects to GitHub's remote MCP server via streamable HTTP
   - Requires `GITHUB_PERSONAL_ACCESS_TOKEN` for authentication
   - Applies tool filter for read-only operations: search_repositories, search_issues, list_issues, get_issue, list_pull_requests, get_pull_request
   - Returns None if token unavailable (graceful degradation)

**Prompt Engineering**: `/home/user/adk-samples/python/agents/software-bug-assistant/software_bug_assistant/prompt.py`

8. **Agent Instruction** (Lines 15-76)
   - Defines persona: Expert in triaging/debugging for "QuantumRoast" (coffee machine company)
   - 6-step workflow: Understand request → Identify tools → Validate parameters → Call tools → Analyze results → Ask for next steps
   - Detailed tool descriptions with usage guidance (12 tools documented)
   - Specific formatting rules (markdown tables for multiple bugs, backticks for code)
   - Priority assignment logic (P0-Critical to P3-Low)

### Key Libraries and Dependencies

From `/home/user/adk-samples/python/agents/software-bug-assistant/pyproject.toml`:

**Core Framework** (Lines 10-16)
- `google-adk>=1.8.0`: Anthropic ADK for agent framework and orchestration
- `google-cloud-aiplatform[agent-engines,evaluation]>=1.93.0`: Vertex AI integration for embeddings and model serving
- `langchain>=0.3.0,<0.4.0`: LangChain core for tool abstraction
- `langchain-community>=0.3.25`: Community tools including StackExchange
- `toolbox-core>=0.1.0`: MCP Toolbox client library for database tools
- `python-dotenv>=1.1.0`: Environment variable management
- `stackapi>=0.3.1`: StackExchange API wrapper

**Runtime**
- Python 3.10-3.12 (Line 8)

**Development Tools** (Lines 20-33)
- pytest, pytest-asyncio for testing
- ruff for linting and formatting
- mypy for type checking
- codespell for spell checking
- agent-starter-pack for deployment scaffolding

### Tools and Integrations

**1. Database Tools (MCP Toolbox)**
- **Source**: PostgreSQL via Cloud SQL or local instance
- **Vector Search**: `search-tickets` uses pgvector with cosine distance on embeddings (Line 27-30 in tools.yaml)
- **CRUD Operations**: create-new-ticket, get-ticket-by-id, update-ticket-priority, update-ticket-status
- **Filtered Queries**: get-tickets-by-assignee, get-tickets-by-status, get-tickets-by-priority, get-tickets-by-date-range
- **Configuration**: `deployment/mcp-toolbox/tools.yaml` defines 9 tools with SQL statements

**2. GitHub MCP Server**
- **Protocol**: MCP over streamable HTTP
- **Endpoint**: `https://api.githubcopilot.com/mcp/`
- **Authentication**: GitHub Personal Access Token (Bearer)
- **Capabilities**: Search repositories/issues, list/get issues and PRs (read-only)

**3. Google Search**
- **Integration**: ADK built-in `google_search` tool
- **Usage Pattern**: Delegated to specialized `search_agent` via AgentTool
- **Purpose**: Grounding with up-to-date web information, CVE lookups

**4. StackOverflow/StackExchange**
- **Integration**: LangChain community tool
- **API**: StackExchange API wrapper
- **Purpose**: Community knowledge base for debugging solutions

### Reasoning Mechanisms

**Prompt-Driven Tool Selection** (prompt.py Lines 18-26)
- Agent analyzes user request against documented tool capabilities
- Multi-tool reasoning: "Identify one **or more** appropriate tools"
- Parameter validation before execution: "do some reasoning to make sure you are populating the tool parameters correctly"
- Common-sense heuristics: P0 for critical issues, default "open" status for new bugs

**RAG for Duplicate Detection** (tools.yaml Lines 18-30)
- Vector similarity search using text-embedding-005 model
- Cosine distance threshold ≤ 0.3 signals similar/duplicate tickets (prompt.py Lines 36-39)
- Returns top 3 most similar tickets with distance scores

**Conversational State Management**
- No explicit state beyond prompt context
- Relies on conversational memory within ADK session
- Multi-turn interactions for bug creation workflow

**Error Handling**
- Graceful degradation: Tools return empty lists/None when unavailable (tools.py Lines 64-69, 73-94)
- Try-except blocks prevent initialization failures from breaking agent

## Build & Run Instructions

### Prerequisites

**Required Software**
- **Python**: Version 3.10, 3.11, or 3.12 (specified in pyproject.toml Line 8)
- **uv**: Universal Python package manager - [Installation Guide](https://docs.astral.sh/uv/getting-started/installation)
- **Git**: For cloning repository - [Installation Guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- **Google Cloud CLI** (gcloud): For cloud deployment - [Installation Guide](https://cloud.google.com/sdk/docs/install)

**For Local Development**
- **PostgreSQL**: Local instance with psql CLI - [Download](https://www.postgresql.org/download/)

**Accounts and Credentials**
- **GitHub Personal Access Token**: Required for GitHub MCP server integration
  - Generate at [GitHub Developer Settings](https://github.com/settings/tokens)
  - Required scopes: `repo:status`, `public_repo`, `read:user` (minimum for read-only)
- **Gemini API Access**: Choose one of:
  - **Google AI Studio API Key**: Quick start, get at [Google AI Studio](https://aistudio.google.com/apikey)
  - **Google Cloud Project with Vertex AI**: For production deployment

### Step-by-Step Installation

**1. Clone Repository**
```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/software-bug-assistant
```

**2. Download MCP Toolbox Binary**
```bash
# Set your OS (choose one: linux/amd64, darwin/arm64, darwin/amd64, windows/amd64)
export OS="linux/amd64"

# Download toolbox binary
curl -O --output-dir deployment/mcp-toolbox \
  https://storage.googleapis.com/genai-toolbox/v0.6.0/$OS/toolbox

# Make executable
chmod +x deployment/mcp-toolbox/toolbox
```

**3. Set Up Local PostgreSQL Database**

Start PostgreSQL service (MacOS example):
```bash
brew services start postgresql
```

Initialize database:
```bash
psql -U postgres
```

Run SQL setup (from PostgreSQL prompt):
```sql
CREATE DATABASE ticketsdb;
\c ticketsdb;

CREATE TABLE tickets (
    ticket_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assignee VARCHAR(100),
    priority VARCHAR(50),
    status VARCHAR(50) DEFAULT 'Open',
    creation_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample tickets (see README.md Lines 191-220 for full sample data)
INSERT INTO tickets (title, description, assignee, priority, status) VALUES
('Login Page Freezes After Multiple Failed Attempts', 'Users are reporting that after 3 failed login attempts, the login page becomes unresponsive and requires a refresh. No specific error message is displayed.', 'samuel.green@example.com', 'P0 - Critical', 'Open');
-- (Add remaining sample tickets from README)
```

**4. Configure MCP Toolbox for Local Database**

Edit `deployment/mcp-toolbox/tools.yaml` (Lines 10-16):
```yaml
sources:
  postgresql: # LOCAL
    kind: postgres
    host: 127.0.0.1
    port: 5432
    database: ticketsdb
    user: postgres
    password: admin
```

### Configuration (Environment Variables)

**Option A: Google AI Studio (Quickest)**
```bash
# Create .env file
echo "GOOGLE_API_KEY=<your_api_key_here>" >> .env
echo "GOOGLE_GENAI_USE_VERTEXAI=FALSE" >> .env
echo "GITHUB_PERSONAL_ACCESS_TOKEN=<your_github_pat_here>" >> .env

# Source environment variables
set -o allexport && source .env && set +o allexport
```

**Option B: Vertex AI (Production)**
```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project <your_project_id>
gcloud services enable aiplatform.googleapis.com

# Create .env file
echo "GOOGLE_GENAI_USE_VERTEXAI=TRUE" >> .env
echo "GOOGLE_CLOUD_PROJECT=<your_project_id>" >> .env
echo "GOOGLE_CLOUD_LOCATION=us-central1" >> .env
echo "GITHUB_PERSONAL_ACCESS_TOKEN=<your_github_pat_here>" >> .env

# Source environment variables
set -o allexport && source .env && set +o allexport
```

### Running the Agent

**Start MCP Toolbox Server** (in one terminal):
```bash
cd deployment/mcp-toolbox/
./toolbox --tools-file="tools.yaml"
```

Expected output:
```
INFO "Initialized 1 sources."
INFO "Initialized 0 authServices."
INFO "Initialized 9 tools."
INFO "Initialized 2 toolsets."
INFO "Server ready to serve!"
```

Verify: Open http://localhost:5000/api/toolset in browser (should show JSON with tool definitions)

**Run Agent - CLI Mode** (in new terminal):
```bash
uv run adk run software_bug_assistant
```

**Run Agent - Web UI Mode** (in new terminal):
```bash
uv run adk web
```
Then:
1. Open the URL printed by the command (usually http://localhost:8000)
2. Select "software_bug_assistant" from the top-left dropdown
3. Start chatting in the interface

### Example Interactions

**Example 1: List Open Tickets**
```
User: Can you list all open internal ticket issues?

Agent: [Calls get-tickets-by-status tool]
       Here are the open tickets:

       | Ticket ID | Title | Assignee | Priority |
       |-----------|-------|----------|----------|
       | 1 | Login Page Freezes... | samuel.green@example.com | P0 - Critical |
       | 5 | Critical XZ Utils Backdoor... | frank.white@example.com | P0 - Critical |
       ...
```

**Example 2: Update Priority**
```
User: Can you bump the priority of ticket ID 7 to P0?

Agent: [Calls update-ticket-priority tool with priority="P0 - Critical", ticket_id="7"]
       I've updated ticket #7 ("Export to PDF Truncates Long Text Fields") to P0 - Critical priority.
```

**Example 3: StackOverflow Research**
```
User: Are there any discussions on StackOverflow about CVE-2024-3094?

Agent: [Calls stack_exchange tool]
       I found several relevant discussions on StackOverflow regarding CVE-2024-3094 (XZ Utils backdoor)...
```

**Example 4: GitHub Repository Issues**
```
User: Can you list the latest 5 open issues on the psf/requests GitHub repository?

Agent: [Calls list_issues from GitHub MCP toolset]
       Here are the 5 most recent open issues for psf/requests:
       1. Issue #6234: Connection timeout with proxy...
       2. Issue #6233: SSL verification fails...
       ...
```

**Example 5: Semantic Search**
```
User: Any issues around database timeouts?

Agent: [Calls search-tickets tool with query="database timeouts"]
       I found these similar tickets:

       | Ticket ID | Title | Distance |
       |-----------|-------|----------|
       | 6 | Database Connection Timeouts During Peak Usage | 0.15 |
       | 2 | Dashboard Sales Widget Intermittent Data Loading | 0.42 |
```

### Testing and Evaluation

**Run Unit Tests**
```bash
uv run pytest
```

**Linting and Code Quality**
```bash
# Run all linters
uv run ruff check .
uv run mypy .
uv run codespell .

# Auto-fix formatting issues
uv run ruff format .
```

**Test Configuration**: See `pyproject.toml` Lines 77-79
- Uses pytest with pytest-asyncio
- Excludes .venv directories

### Deployment to Google Cloud

**Full deployment includes**:
- Cloud SQL (PostgreSQL) with Vertex AI ML Integration for vector embeddings
- MCP Toolbox deployed to Cloud Run
- ADK agent deployed to Cloud Run
- Secret Manager for credentials
- IAM service accounts with least-privilege permissions

**Key Deployment Steps** (see README.md Lines 320-616 for detailed instructions):

1. **Create Cloud SQL Instance** (Lines 350-359)
   - Enable `google_ml_integration` extension for vector embeddings
   - Create `tickets-db` database
   - Grant Vertex AI permissions to Cloud SQL service account

2. **Set Up Vector Embeddings** (Lines 457-461)
   ```sql
   ALTER TABLE tickets ADD COLUMN embedding vector(768)
   GENERATED ALWAYS AS (embedding('text-embedding-005',description)) STORED;
   ```

3. **Deploy MCP Toolbox to Cloud Run** (Lines 476-544)
   - Store tools.yaml in Secret Manager
   - Configure service account with Cloud SQL and Secret Manager access
   - Deploy using official toolbox container image

4. **Build and Deploy Agent to Cloud Run** (Lines 554-598)
   - Build container with Cloud Build
   - Push to Artifact Registry
   - Deploy with environment variables (API keys, MCP Toolbox URL)

**Deployment URLs**:
- After deployment, agent accessible at Cloud Run service URL
- ADK Web UI served at the service URL

### Troubleshooting

**Issue**: MCP Toolbox tools not loading
- **Solution**: Verify toolbox server is running at http://localhost:5000/api/toolset
- **Solution**: Check tools.yaml database credentials match your PostgreSQL setup
- **Solution**: Ensure `MCP_TOOLBOX_URL` environment variable is set correctly

**Issue**: GitHub MCP tools not available
- **Solution**: Verify `GITHUB_PERSONAL_ACCESS_TOKEN` is set in environment
- **Solution**: Check token has required scopes (`repo:status`, `public_repo`, `read:user`)
- **Solution**: Test token with: `curl -H "Authorization: Bearer $GITHUB_PERSONAL_ACCESS_TOKEN" https://api.github.com/user`

**Issue**: "API Key not valid" error
- **Solution**: For AI Studio, verify `GOOGLE_API_KEY` is set and valid
- **Solution**: For Vertex AI, ensure `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` are set
- **Solution**: For Vertex AI, run `gcloud auth application-default login`

**Issue**: Vector search not working locally
- **Solution**: Vector search requires Cloud SQL with Vertex AI ML Integration
- **Solution**: Use cloud deployment for full RAG capabilities
- **Solution**: Locally, other search tools (by-status, by-assignee) still work

**Issue**: StackOverflow queries timing out
- **Solution**: StackExchange API has rate limits; wait and retry
- **Solution**: Check internet connectivity

## Customization Options

### 1. Add Custom Database Tools

**Customization**: Add new SQL-based tools to the MCP Toolbox configuration

**Location**: `/home/user/adk-samples/python/agents/software-bug-assistant/deployment/mcp-toolbox/tools.yaml`

**Example**: Add a tool to assign tickets to specific engineers based on expertise area

```yaml
tools:
  assign-ticket-by-expertise:
    kind: postgres-sql
    source: postgresql
    description: Assign a ticket to an engineer based on their area of expertise.
    parameters:
      - name: ticket_id
        type: string
        description: The ID of the ticket to assign.
      - name: expertise_area
        type: string
        description: The area of expertise (e.g., 'frontend', 'backend', 'database', 'security').
    statement: |
      UPDATE tickets
      SET assignee = CASE
        WHEN $2 = 'frontend' THEN 'maria.rodriguez@example.com'
        WHEN $2 = 'backend' THEN 'frank.white@example.com'
        WHEN $2 = 'database' THEN 'samuel.green@example.com'
        WHEN $2 = 'security' THEN 'security-team@example.com'
        ELSE assignee
      END
      WHERE ticket_id = $1
      RETURNING ticket_id, assignee;

toolsets:
  tickets_toolset:
    # ... existing tools ...
    - assign-ticket-by-expertise
```

Then update the agent prompt (prompt.py) to document the new tool.

### 2. Switch to Different LLM Models

**Customization**: Use different Gemini models or adjust parameters for cost/performance trade-offs

**Location**: `/home/user/adk-samples/python/agents/software-bug-assistant/software_bug_assistant/agent.py` (Line 29)

**Example**: Use Gemini 1.5 Pro for more complex reasoning or Gemini 1.5 Flash for faster responses

```python
# Original
root_agent = Agent(
    model="gemini-2.5-flash",
    name="software_assistant",
    instruction=agent_instruction,
    tools=tools,
)

# Modified for different models
root_agent = Agent(
    model="gemini-1.5-pro",  # More capable, higher cost
    # OR
    # model="gemini-1.5-flash",  # Faster, lower cost
    name="software_assistant",
    instruction=agent_instruction,
    tools=tools,
)
```

### 3. Customize Company/Domain Context

**Customization**: Adapt the agent for different companies or technical domains

**Location**: `/home/user/adk-samples/python/agents/software-bug-assistant/software_bug_assistant/prompt.py` (Line 16)

**Example**: Change from coffee machine company to e-commerce platform

```python
# Original
agent_instruction = """
You are a skilled expert in triaging and debugging software issues for a coffee machine company, QuantumRoast.
...
"""

# Modified
agent_instruction = """
You are a skilled expert in triaging and debugging software issues for an e-commerce platform, ShopSwift.

Your expertise includes:
- Payment processing systems (Stripe, PayPal integrations)
- Inventory management and stock synchronization
- User authentication and account security
- Shopping cart and checkout flows
- Order fulfillment and shipping integrations
- Performance optimization for high-traffic events

[Rest of instruction remains similar...]
"""
```

### 4. Add Additional External Knowledge Sources

**Customization**: Integrate additional LangChain tools or custom APIs

**Location**: `/home/user/adk-samples/python/agents/software-bug-assistant/software_bug_assistant/tools/tools.py`

**Example**: Add Jira integration for cross-platform ticket management

```python
from langchain_community.utilities import JiraAPIWrapper
from langchain_community.tools import JiraAction

# Initialize Jira connection
jira = JiraAPIWrapper(
    jira_url=os.getenv("JIRA_URL"),
    jira_username=os.getenv("JIRA_USERNAME"),
    jira_api_token=os.getenv("JIRA_API_TOKEN"),
)

# Create Jira tools
jira_get_tool = JiraAction(
    api_wrapper=jira,
    mode="get_issue",
    name="jira_get_issue",
    description="Get details of a Jira issue by key"
)

jira_search_tool = JiraAction(
    api_wrapper=jira,
    mode="jql",
    name="jira_search",
    description="Search Jira issues using JQL query"
)

# Convert to ADK tools
jira_get_adk_tool = LangchainTool(jira_get_tool)
jira_search_adk_tool = LangchainTool(jira_search_tool)

# Add to tools list (Line 22)
tools = [get_current_date, search_tool, langchain_tool, jira_get_adk_tool, jira_search_adk_tool]
```

Don't forget to update `.env` with Jira credentials and document the new tools in `prompt.py`.

### 5. Implement Priority-Based Auto-Assignment

**Customization**: Add intelligent ticket routing based on priority and team capacity

**Location**: Create new file `/home/user/adk-samples/python/agents/software-bug-assistant/software_bug_assistant/tools/assignment.py`

**Example**: Auto-assign critical tickets to on-call engineer

```python
import os
from datetime import datetime
from typing import Dict

def auto_assign_ticket(priority: str, expertise_area: str = "general") -> Dict[str, str]:
    """
    Automatically assign a ticket to the appropriate engineer based on priority and expertise.

    Args:
        priority: Ticket priority (P0 - Critical, P1 - High, P2 - Medium, P3 - Low)
        expertise_area: Area of expertise needed (frontend, backend, database, security, general)

    Returns:
        Dictionary with assignee email and assignment reason
    """
    # Priority-based routing
    if priority == "P0 - Critical":
        # Assign to on-call engineer (rotates by day of week)
        on_call_rotation = {
            0: "frank.white@example.com",  # Monday
            1: "samuel.green@example.com",  # Tuesday
            2: "maria.rodriguez@example.com",  # Wednesday
            3: "frank.white@example.com",  # Thursday
            4: "samuel.green@example.com",  # Friday
            5: "security-team@example.com",  # Weekend
            6: "security-team@example.com",
        }
        day_of_week = datetime.now().weekday()
        assignee = on_call_rotation[day_of_week]
        reason = f"Auto-assigned to on-call engineer for {datetime.now().strftime('%A')}"

    elif priority == "P1 - High":
        # Assign based on expertise with load balancing
        expertise_leads = {
            "frontend": "maria.rodriguez@example.com",
            "backend": "frank.white@example.com",
            "database": "samuel.green@example.com",
            "security": "security-team@example.com",
            "general": "frank.white@example.com",
        }
        assignee = expertise_leads.get(expertise_area, "frank.white@example.com")
        reason = f"Assigned to {expertise_area} team lead"

    else:
        # P2/P3: Assign to general triage queue
        assignee = "triage-team@example.com"
        reason = "Assigned to triage queue for standard processing"

    return {
        "assignee": assignee,
        "assignment_reason": reason,
    }
```

Then integrate in `tools.py`:
```python
from .assignment import auto_assign_ticket

tools = [get_current_date, search_tool, langchain_tool, auto_assign_ticket]
```

### 6. Enable Multi-Language Support

**Customization**: Support bug reports and responses in multiple languages

**Location**: `/home/user/adk-samples/python/agents/software-bug-assistant/software_bug_assistant/prompt.py`

**Example**: Add multilingual capabilities with language detection

```python
agent_instruction = """
You are a skilled expert in triaging and debugging software issues for a coffee machine company, QuantumRoast.

**LANGUAGE SUPPORT:**
You can communicate in multiple languages. Always respond in the same language the user writes in.
Supported languages: English, Spanish, French, German, Japanese, Chinese (Simplified).

When creating tickets from non-English descriptions:
1. Store the original description in the user's language
2. Automatically add an English translation in a new field or as an addendum
3. Tag the ticket with the source language for future reference

**INSTRUCTION:**
[Rest of existing instruction...]
"""
```

Then modify the database schema to support language tags:
```sql
ALTER TABLE tickets ADD COLUMN language VARCHAR(10) DEFAULT 'en';
ALTER TABLE tickets ADD COLUMN description_en TEXT;
```

### 7. Add Ticket Analytics and Reporting

**Customization**: Generate insights from ticket patterns and trends

**Location**: Add new tools in `deployment/mcp-toolbox/tools.yaml`

**Example**: Create analytics tools for management reports

```yaml
tools:
  get-ticket-statistics:
    kind: postgres-sql
    source: postgresql
    description: Get statistical summary of tickets by status and priority.
    parameters: []
    statement: |
      SELECT
        status,
        priority,
        COUNT(*) as ticket_count,
        COUNT(DISTINCT assignee) as unique_assignees,
        AVG(EXTRACT(EPOCH FROM (updated_time - creation_time))/86400) as avg_resolution_days
      FROM tickets
      GROUP BY status, priority
      ORDER BY priority, status;

  get-assignee-workload:
    kind: postgres-sql
    source: postgresql
    description: Get current workload distribution across team members.
    parameters:
      - name: status_filter
        type: string
        description: Filter by status (e.g., 'Open' or 'In Progress'). Use '%' for all statuses.
    statement: |
      SELECT
        assignee,
        COUNT(*) as total_tickets,
        SUM(CASE WHEN priority LIKE 'P0%' THEN 1 ELSE 0 END) as critical_tickets,
        SUM(CASE WHEN priority LIKE 'P1%' THEN 1 ELSE 0 END) as high_priority_tickets,
        STRING_AGG(ticket_id::TEXT || ':' || title, '; ') as ticket_summary
      FROM tickets
      WHERE status ILIKE '%' || $1 || '%'
      GROUP BY assignee
      ORDER BY critical_tickets DESC, high_priority_tickets DESC;
```

Add to toolset and update prompt to document analytics capabilities.

---

**Report Generated**: 2025-11-19
**ADK Version**: 1.8.0+
**Agent Model**: Gemini 2.5 Flash
**Architecture Pattern**: Single Agent with Multi-Tool Integration
