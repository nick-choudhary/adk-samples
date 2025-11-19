# FOMC Research Agent - Technical Documentation Report

## Project Scope

The FOMC Research Agent is an advanced multi-agent system that automates the analysis of Federal Open Market Committee (FOMC) meetings. It demonstrates a sophisticated, workflow-based approach to financial analysis using AI agents.

### Core Capabilities
- Automated retrieval of FOMC meeting data from federalreserve.gov
- Analysis of FOMC statements with redline comparisons between current and previous meetings
- Computation of interest rate move probabilities using Fed Futures pricing data from BigQuery
- Transcript summarization with sentiment analysis
- Multi-modal document processing (PDF parsing, HTML extraction)
- Generation of comprehensive analysis reports with minimal human intervention

### Primary Use Cases
- Financial analysts conducting FOMC meeting research
- Investment firms monitoring Federal Reserve policy changes
- Economic researchers analyzing monetary policy trends
- Automated report generation for trading desks
- Educational demonstrations of multi-agent workflows

### Target Users
- Quantitative analysts and traders
- Economic research teams
- Portfolio managers tracking monetary policy
- Financial institutions requiring automated Fed analysis
- Developers learning multi-agent architectures

### Key Innovations/Differentiators
- **Workflow-based architecture**: Non-conversational design where agents coordinate autonomously
- **External data integration**: Seamless integration with BigQuery for historical pricing data
- **Multi-modal processing**: Handles PDFs, HTML, transcripts, and structured data
- **Agent hierarchy**: Sophisticated orchestration of 6 specialized agents
- **Rate limiting**: Built-in callback system to prevent API quota exhaustion
- **Production-ready deployment**: Supports deployment to Google Vertex AI Agent Engine

## Technical Architecture

### Multi-Agent Hierarchy

The FOMC Research Agent employs a hierarchical multi-agent architecture with specialized sub-agents coordinated by a root orchestrator:

```
┌─────────────────────────────────────────────────────────────┐
│                      root_agent                              │
│  (Orchestrates workflow, stores meeting date)                │
│  File: fomc_research/agent.py (lines 35-50)                  │
└─────┬────────────────────────────────────────────┬───────────┘
      │                                            │
      ├────────────────────────┬───────────────────┘
      │                        │
      ▼                        ▼
┌──────────────────┐    ┌──────────────────────────────┐
│ retrieve_meeting │    │     research_agent           │
│   _data_agent    │    │ (Coordinates research tasks) │
│ (Fetches data    │    │ File: sub_agents/            │
│  from Fed site)  │    │   research_agent.py (28-45)  │
│ File: sub_agents/│    └─────┬────────────────────────┘
│  retrieve_*.py   │          │
│  (lines 26-37)   │          ▼
└────┬─────────────┘    ┌──────────────────────────────┐
     │                  │  summarize_meeting_agent     │
     ▼                  │  (Summarizes transcript)     │
┌──────────────────┐    │  File: sub_agents/           │
│ extract_page_data│    │    summarize_*.py (24-35)    │
│     _agent       │    └──────────────────────────────┘
│ (Extracts URLs)  │
│ File: sub_agents/│          ┌──────────────────────────┐
│  extract_*.py    │          │    analysis_agent        │
│  (lines 24-31)   │          │ (Generates final report) │
└──────────────────┘          │ File: sub_agents/        │
                              │   analysis_agent.py      │
                              │   (lines 23-31)          │
                              └──────────────────────────┘
```

### Code Flow Explanation

**1. Initialization and Entry Point** (`fomc_research/agent.py`, lines 35-50)
- Root agent is initialized with model configuration from environment variable `GOOGLE_GENAI_MODEL`
- Default model: `gemini-2.5-flash` (defined in `__init__.py`, line 29)
- Agent registers three sub-agents and one tool (store_state_tool)
- Rate limiting callback is attached to prevent API exhaustion

**2. User Interaction Flow** (`fomc_research/root_agent_prompt.py`, lines 17-31)
- Agent prompts user for meeting date in ISO format (YYYY-MM-DD)
- Validates user input and requests correction if invalid
- Stores validated date in ToolContext using `store_state_tool` with key "user_requested_meeting_date"
- Delegates to `retrieve_meeting_data_agent`

**3. Data Retrieval Phase** (`fomc_research/sub_agents/retrieve_meeting_data_agent.py`, lines 26-37)
- Uses `fetch_page_tool` to retrieve HTML from federalreserve.gov
- Calls `extract_page_data_agent` (via AgentTool wrapper) to parse HTML
- Extracts URLs for current statement, previous statement, and meeting transcript
- Stores extracted URLs in ToolContext state

**4. Research Coordination** (`fomc_research/sub_agents/research_agent.py`, lines 28-45)
- Orchestrates four specialized tools:
  - `compare_statements_tool`: Downloads PDFs, extracts text, generates HTML redline comparison (`tools/compare_statements.py`, lines 27-92)
  - `fetch_transcript_tool`: Retrieves FOMC meeting transcript
  - `compute_rate_move_probability_tool`: Queries BigQuery for Fed Futures data, computes rate change probabilities (`tools/compute_rate_move_probability.py`, lines 26-45)
  - `store_state_tool`: Persists intermediate results
- Delegates to `summarize_meeting_agent` for transcript analysis

**5. Transcript Summarization** (`fomc_research/sub_agents/summarize_meeting_agent.py`, lines 24-35)
- Reads full meeting transcript
- Generates summary with sentiment analysis
- Stores summary in ToolContext for analysis agent

**6. Final Analysis** (`fomc_research/sub_agents/analysis_agent.py`, lines 23-31)
- Receives all research outputs from ToolContext
- Synthesizes comprehensive analysis report
- Provides implications for future FOMC actions

### Agent Definitions with Roles and Responsibilities

| Agent Name | Role | Responsibilities | File Location |
|------------|------|------------------|---------------|
| **root_agent** | Workflow Orchestrator | - Request meeting date from user<br>- Validate and store input<br>- Coordinate sub-agent execution | `fomc_research/agent.py` (lines 35-50) |
| **retrieve_meeting_data_agent** | Data Fetcher | - Fetch Fed website HTML<br>- Extract statement and transcript URLs<br>- Store URLs in context | `sub_agents/retrieve_meeting_data_agent.py` (lines 26-37) |
| **extract_page_data_agent** | HTML Parser | - Parse HTML content<br>- Extract specific data elements<br>- Return structured information | `sub_agents/extract_page_data_agent.py` (lines 24-31) |
| **research_agent** | Research Coordinator | - Execute statement comparison<br>- Compute rate probabilities<br>- Fetch and process transcript<br>- Coordinate summarization | `sub_agents/research_agent.py` (lines 28-45) |
| **summarize_meeting_agent** | Content Summarizer | - Read meeting transcript<br>- Generate executive summary<br>- Analyze sentiment | `sub_agents/summarize_meeting_agent.py` (lines 24-35) |
| **analysis_agent** | Report Generator | - Synthesize all research outputs<br>- Generate final analysis<br>- Provide forward-looking insights | `sub_agents/analysis_agent.py` (lines 23-31) |

### Key Libraries and Dependencies

From `pyproject.toml` (lines 9-24):

| Library | Version | Purpose |
|---------|---------|---------|
| **google-adk** | ^1.0.0 | Core ADK framework for agent development |
| **google-genai** | ^1.5.0 | Gemini API client for model interactions |
| **google-cloud-bigquery** | ^3.30.0 | BigQuery integration for Fed Futures pricing data |
| **google-cloud-aiplatform** | ^1.93.0 | Vertex AI deployment and Agent Engine support |
| **pdfplumber** | ^0.11.5 | PDF parsing for FOMC statements |
| **requests** | ^2.32.3 | HTTP client for web scraping |
| **diff-match-patch** | ^20241021 | Text diffing for statement comparison |
| **pydantic** | ^2.10.6 | Data validation and schema definition |
| **scikit-learn** | ^1.6.1 | Statistical computations for probability analysis |
| **absl-py** | ^2.2.1 | Application utilities and logging |
| **tabulate** | ^0.9.0 | Table formatting for output |

**Python Requirement**: ^3.9 (line 10)

### Tools and Integrations

**Custom Tools** (`fomc_research/tools/`):

1. **store_state_tool** (`store_state.py`)
   - Stores key-value pairs in ToolContext
   - Enables state sharing between agents
   - Used throughout workflow for data persistence

2. **fetch_page_tool** (`fetch_page.py`)
   - HTTP client wrapper for web scraping
   - Retrieves HTML from federalreserve.gov
   - Handles error conditions and retries

3. **compare_statements_tool** (`compare_statements.py`, lines 27-92)
   - Downloads current and previous FOMC statement PDFs
   - Extracts text using pdfplumber
   - Generates HTML redline comparison using diff-match-patch
   - Saves artifacts for later analysis

4. **fetch_transcript_tool** (`fetch_transcript.py`)
   - Retrieves FOMC meeting transcript
   - Processes text for agent consumption
   - Handles various transcript formats

5. **compute_rate_move_probability_tool** (`compute_rate_move_probability.py`, lines 26-45)
   - Queries BigQuery for Fed Futures pricing timeseries
   - Computes implied probabilities of rate changes
   - Uses statistical models from `price_utils.py`
   - Returns structured probability distribution

**External Integrations**:

- **BigQuery**: Fed Futures pricing data storage and retrieval
  - Dataset configuration via `GOOGLE_CLOUD_BQ_DATASET` environment variable
  - Timeseries codes: `SFRH5, SFRZ5` (configurable via `.env`)
  - Setup script: `deployment/bigquery_setup.py`

- **Federal Reserve Website**: Live data source for statements and transcripts
  - Base URL: `https://www.federalreserve.gov`
  - Dynamically fetches latest meeting data

- **Google Cloud Storage**: Artifact storage for intermediate results
  - Configured via `GOOGLE_CLOUD_STORAGE_BUCKET` environment variable

### Reasoning Mechanisms

**1. Rate Limiting Callback** (`shared_libraries/callbacks.py`, lines 32-74)
- Implements request-per-minute (RPM) quota management
- Default: 1000 requests per 60 seconds
- Tracks request count and elapsed time in callback context
- Automatically sleeps when approaching quota limit
- Prevents `429: Resource Exhausted` errors

**2. State Management via ToolContext**
- Agents share data through centralized ToolContext
- Key data stored: meeting dates, URLs, extracted text, probabilities, summaries
- Enables asynchronous agent coordination without tight coupling

**3. Multi-Modal Processing**
- PDF parsing for FOMC statements
- HTML scraping for web pages
- Text processing for transcripts
- Structured data from BigQuery

**4. Error Handling**
- Tools return status dictionaries with error messages
- Agents validate tool outputs before proceeding
- Graceful degradation when optional data unavailable

## Build & Run Instructions

### Prerequisites

**Required Software**:
- Python 3.9 or higher
- Poetry package manager
- Google Cloud SDK (gcloud CLI)

**Required Accounts**:
- Google Cloud Project with billing enabled
- Google API key OR Vertex AI authentication

**Required GCP APIs**:
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com
```

### Step-by-Step Installation

**1. Clone Repository**
```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/fomc-research
```

**2. Install Poetry** (if not already installed)
```bash
pip install poetry
```

**Linux users**: If you encounter keyring errors:
```bash
poetry config keyring.enabled false
```

**3. Install Dependencies**
```bash
poetry install
```

This installs all dependencies from `pyproject.toml`, including google-adk ^1.0.0.

**4. Authenticate with Google Cloud**
```bash
gcloud auth login
gcloud auth application-default login
```

**5. Set up BigQuery**

Create dataset and load sample data:
```bash
cd deployment
python bigquery_setup.py \
  --project_id=$GOOGLE_CLOUD_PROJECT \
  --dataset_id=$GOOGLE_CLOUD_BQ_DATASET \
  --location=$GOOGLE_CLOUD_LOCATION \
  --data_file=sample_timeseries_data.csv
```

Sample data covers meetings: January 29, 2025 and March 19, 2025.

### Configuration (Environment Variables)

**1. Copy Environment Template**
```bash
cp .env-example .env
```

**2. Edit `.env` File**

Choose backend (ML Dev or Vertex AI):

**Option A: ML Dev Backend** (`.env` lines 3-7)
```bash
GOOGLE_GENAI_USE_VERTEXAI=0
GOOGLE_API_KEY=your_api_key_here
```

**Option B: Vertex AI Backend** (`.env` lines 9-26)
```bash
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_PROJECT_NUMBER=123456789
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_BQ_DATASET=fomc_data
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name
GOOGLE_GENAI_MODEL=gemini-2.5-flash
GOOGLE_GENAI_FOMC_AGENT_TIMESERIES_CODES="SFRH5,SFRZ5"
GOOGLE_GENAI_FOMC_AGENT_LOG_LEVEL="INFO"
```

**3. Export Variables (bash shell)**
```bash
set -o allexport
. .env
set +o allexport
```

### Running the Agent

#### CLI Method

From the `fomc-research` directory:
```bash
adk run fomc_research
```

**Expected Output**:
```
Log setup complete: /tmp/agents_log/agent.20250405_140937.log
To access latest log: tail -F /tmp/agents_log/agent.latest.log
Running agent root_agent, type exit to exit.
```

**Monitor logs in separate terminal**:
```bash
tail -F /tmp/agents_log/agent.latest.log
```

#### Web UI Method

**Start Web Interface**:
```bash
adk web .
```

Navigate to displayed URL (typically `http://localhost:8000`).

Select `fomc_research` from dropdown menu at top left.

**Optional: Save logs to file**:
```bash
adk web . > fomc_research_log.txt 2>&1 &
tail -f fomc_research_log.txt
```

### Example Interactions

**Session 1: Basic Analysis**
```
user: Hello. What can you do for me?

[root_agent]: I can help you analyze past Fed Open Market Committee (FOMC)
meetings and provide you with a thorough analysis report. To start, please
provide the date of the meeting you would like to analyze. If you have already
provided it, please confirm the date. I need the date in ISO format (YYYY-MM-DD).

user: 2025-01-29

[retrieve_meeting_data_agent]: Retrieving meeting data for 2025-01-29...

[research_agent]: Comparing statements, computing rate probabilities,
fetching transcript...

[summarize_meeting_agent]: Summarizing meeting transcript...

[analysis_agent]: Here is a summary and analysis of the January 29, 2025
FOMC meeting, based on the available information:

**Key Decisions:**
- Federal Reserve maintained the target range for the federal funds rate at
  4.25% to 4.50%
- Unanimous decision by all FOMC participants
- Committee continues reducing holdings of Treasury securities and agency MBS

**Economic Outlook:**
- Inflation remains elevated above the 2% target
- Labor market conditions remain solid
- Unemployment rate stabilized but remains elevated
- Economic activity continued to expand at a solid pace

**Market Expectations:**
Based on Fed Futures pricing data:
- Probability of 25bp cut by March meeting: 15%
- Probability of no change: 70%
- Probability of 25bp increase: 15%

**Statement Changes from Previous Meeting:**
[HTML redline showing specific language modifications]

**Sentiment Analysis:**
Overall tone remains cautiously optimistic with continued vigilance on
inflation. Committee emphasized data-dependent approach to future decisions.
```

**Session 2: Troubleshooting Incomplete Run**
```
user: 2025-03-19

[analysis_agent]: [Agent stops mid-workflow]

user: Please continue the analysis.

[analysis_agent]: Continuing... [Completes analysis]
```

### Testing and Evaluation

**Manual Testing**:
```bash
# Test with different meeting dates
adk run fomc_research
# Input: 2025-01-29
# Input: 2025-03-19
```

**Verify BigQuery Connection**:
```bash
cd deployment
python -c "from google.cloud import bigquery; \
  client = bigquery.Client(); \
  print('BigQuery connected successfully')"
```

**Check Artifacts**:
Artifacts are saved to Google Cloud Storage bucket during execution. Verify:
- `requested_statement_fulltext`
- `previous_statement_fulltext`
- `statement_redline` (HTML)

### Deployment (Vertex AI Agent Engine)

**1. Setup Permissions**

Grant BigQuery access to Reasoning Engine Service Agent:
```bash
export RE_SA="service-${GOOGLE_CLOUD_PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
  --member="serviceAccount:${RE_SA}" \
  --condition=None \
  --role="roles/bigquery.user"

gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
  --member="serviceAccount:${RE_SA}" \
  --condition=None \
  --role="roles/bigquery.dataViewer"
```

**2. Build Deployment Package**
```bash
poetry build --format=wheel --output=deployment
```

Output: `deployment/fomc_research-0.1-py3-none-any.whl`

**3. Deploy to Agent Engine**
```bash
cd deployment
python3 deploy.py --create
```

**Expected Output**:
```
projects/your-project/locations/us-central1/reasoningEngines/7737333693403889664
```

Store the resource ID:
```bash
export RESOURCE_ID=7737333693403889664
```

**4. Test Deployed Agent**
```bash
export USER_ID=test_user_001
python test_deployment.py --resource_id=$RESOURCE_ID --user_id=$USER_ID
```

**Example Interaction**:
```
Found agent with resource ID: 7737333693403889664
Created session for user ID: test_user_001
Type 'quit' to exit.

Input: Hello. What can you do for me?
Response: I can create an analysis report on FOMC meetings. To start,
please provide the date of the meeting you want to analyze. I need the
date in YYYY-MM-DD format.

Input: 2025-01-29
Response: I have stored the date you provided. Now I will retrieve the
meeting data...
[Analysis continues...]
```

**5. Delete Deployed Agent**
```bash
python3 deployment/deploy.py --delete --resource_id=$RESOURCE_ID
```

### Troubleshooting

**Issue: "Malformed function call" Error**

**Cause**: Gemini model error (occasional)

**Solution**: Restart the UI or CLI session. The error typically resolves on retry.

**Issue: Agent Stops Mid-Workflow**

**Cause**: Model may require explicit continuation prompt

**Solution**:
```
user: Please continue with the analysis.
```
or
```
user: Continue
```

**Issue: BigQuery Connection Errors**

**Symptoms**: `compute_rate_move_probability_tool` fails

**Solutions**:
1. Verify dataset exists:
   ```bash
   bq ls --project_id=$GOOGLE_CLOUD_PROJECT $GOOGLE_CLOUD_BQ_DATASET
   ```

2. Check authentication:
   ```bash
   gcloud auth application-default login
   ```

3. Verify permissions:
   ```bash
   gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT \
     --flatten="bindings[].members" \
     --filter="bindings.role:roles/bigquery.dataViewer"
   ```

**Issue: Rate Limit (429) Errors**

**Cause**: Exceeding API quota

**Solution**: Adjust rate limit parameters in `shared_libraries/callbacks.py` (lines 28-29):
```python
RATE_LIMIT_SECS = 60  # Increase to 120
RPM_QUOTA = 1000      # Decrease to 500
```

**Issue: PDF Download Failures**

**Symptoms**: `compare_statements_tool` returns errors

**Solutions**:
1. Check network connectivity to federalreserve.gov
2. Verify URLs in ToolContext state are valid
3. Check Cloud Storage bucket write permissions

**Issue: Missing Meeting Data**

**Symptoms**: Agent reports meeting not found

**Solution**: Verify meeting date is correct and meeting has occurred. Sample data only covers:
- 2025-01-29
- 2025-03-19

For other dates, you'll need to add timeseries data to BigQuery.

**Issue: Environment Variables Not Loaded**

**Symptoms**: Agent uses wrong model or fails to connect to GCP

**Solution**:
```bash
# Verify variables are set
echo $GOOGLE_CLOUD_PROJECT
echo $GOOGLE_GENAI_MODEL

# Re-export if needed
set -o allexport && . .env && set +o allexport
```

## Customization Options

### 1. Change AI Model

**Location**: `.env` file or `fomc_research/__init__.py`

**Current Default**: `gemini-2.5-flash` (line 29 in `__init__.py`)

**How to Customize**:

Set environment variable in `.env`:
```bash
GOOGLE_GENAI_MODEL=gemini-2.5-pro
```

Or modify `__init__.py` (lines 27-29):
```python
MODEL = os.getenv("GOOGLE_GENAI_MODEL")
if not MODEL:
    MODEL = "gemini-2.5-pro"  # Changed from gemini-2.5-flash
```

**Use Cases**:
- Use `gemini-2.5-pro` for more complex analysis requiring deeper reasoning
- Use `gemini-2.5-flash` for faster, cost-effective execution
- Use different models for different agents by modifying individual agent definitions

### 2. Customize Analysis Prompts

**Location**: `fomc_research/sub_agents/*_prompt.py` files

**Example - Modify Analysis Focus**:

Edit `analysis_agent_prompt.py` to focus on specific aspects:
```python
PROMPT = """
You are a financial analyst specializing in monetary policy.

FOCUS AREAS (customize these):
1. Market reaction predictions
2. International currency implications
3. Sector-specific impacts (technology, real estate, banking)
4. Historical comparisons with similar rate environments

Analyze the FOMC meeting data and provide insights on:
- Immediate market impact (next 24-48 hours)
- Medium-term implications (1-3 months)
- Long-term policy trajectory (6-12 months)

Use the following data sources:
- Statement comparison (redline)
- Rate move probabilities
- Meeting transcript summary

Generate a report with:
- Executive Summary (2-3 paragraphs)
- Detailed Analysis by focus area
- Risk assessment
- Recommendations for portfolio positioning
"""
```

**Use Cases**:
- Customize for specific investment strategies
- Add sector-specific analysis
- Include ESG considerations
- Focus on international implications

### 3. Add Custom Tools for Additional Data Sources

**Location**: `fomc_research/tools/` (create new tool file)

**Example - Add Economic Indicator Tool**:

Create `fomc_research/tools/fetch_economic_indicators.py`:
```python
from google.adk.tools import ToolContext
import requests

async def fetch_economic_indicators_tool(
    tool_context: ToolContext,
    indicators: list[str] = ["CPI", "Unemployment", "GDP"]
) -> dict[str, str]:
    """Fetches economic indicators from FRED API.

    Args:
        tool_context: ToolContext object
        indicators: List of indicator codes to fetch

    Returns:
        Dict with status and indicator data
    """
    meeting_date = tool_context.state["requested_meeting_date"]

    # Fetch data from FRED API
    fred_api_key = os.getenv("FRED_API_KEY")
    results = {}

    for indicator in indicators:
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": indicator,
            "api_key": fred_api_key,
            "observation_start": meeting_date,
            "file_type": "json"
        }
        response = requests.get(url, params=params)
        results[indicator] = response.json()

    tool_context.state["economic_indicators"] = results
    return {"status": "OK", "indicators_fetched": len(results)}
```

**Register Tool** in `research_agent.py` (lines 38-43):
```python
from ..tools.fetch_economic_indicators import fetch_economic_indicators_tool

ResearchAgent = Agent(
    # ... existing config
    tools=[
        store_state_tool,
        compare_statements_tool,
        fetch_transcript_tool,
        compute_rate_move_probability_tool,
        fetch_economic_indicators_tool,  # Add new tool
    ],
    # ... rest of config
)
```

**Use Cases**:
- Add CPI/inflation data from FRED
- Integrate stock market data
- Pull Treasury yield curves
- Fetch commodity prices

### 4. Modify Rate Probability Computation

**Location**: `fomc_research/shared_libraries/price_utils.py`

**Example - Change Probability Calculation Method**:

Customize the statistical model used for computing rate move probabilities:
```python
def compute_probabilities(meeting_date: str) -> dict:
    """Compute rate move probabilities with custom weighting."""

    # Fetch Fed Futures prices from BigQuery
    prices = fetch_futures_prices(meeting_date)

    # CUSTOMIZE: Apply custom weighting algorithm
    # Example: Weight recent data more heavily
    weights = np.exp(-0.1 * np.arange(len(prices)))
    weights = weights / weights.sum()

    weighted_prices = prices * weights

    # CUSTOMIZE: Change probability bins
    # Original: [-25bp, 0, +25bp]
    # New: [-50bp, -25bp, 0, +25bp, +50bp]
    bins = [-50, -25, 0, 25, 50]

    probabilities = calculate_implied_probabilities(
        weighted_prices,
        bins
    )

    return {
        "status": "OK",
        "output": probabilities,
        "methodology": "exponentially_weighted_5_bin"
    }
```

**Use Cases**:
- Implement alternative probability models (Black-Scholes, Monte Carlo)
- Add confidence intervals
- Include historical volatility adjustments
- Incorporate options pricing data

### 5. Extend with Video Analysis

**Location**: `fomc_research/tools/` (video analysis tool)

**Example - Add Press Conference Analysis**:

The README mentions video analysis is "in development" (line 25). Implement it:

Create `fomc_research/tools/analyze_press_conference.py`:
```python
from google.adk.tools import ToolContext
from google.genai.types import Part

async def analyze_press_conference_tool(
    tool_context: ToolContext
) -> dict[str, str]:
    """Analyzes FOMC press conference video.

    Extracts:
    - Chair's tone and body language
    - Q&A sentiment
    - Key quotes
    - Market-moving statements
    """
    video_url = tool_context.state.get("press_conference_video_url")

    # Download video frames at key moments
    frames = extract_key_frames(video_url)

    # Use Gemini multimodal capabilities
    analysis_prompt = """
    Analyze this FOMC press conference video frame.

    Assess:
    1. Chair's demeanor (confident, cautious, dovish, hawkish)
    2. Body language cues
    3. Emphasis on key topics
    4. Deviation from prepared remarks

    Rate confidence level on policy stance: 1-10
    """

    # Process with Gemini Vision
    for frame in frames:
        part = Part(inline_data={"mime_type": "image/jpeg", "data": frame})
        # Send to model for analysis

    tool_context.state["press_conference_analysis"] = analysis_results
    return {"status": "OK"}
```

**Use Cases**:
- Sentiment analysis of press conference
- Detect tone shifts from prepared statement
- Identify market-moving quotes
- Compare body language across meetings

### 6. Configure Logging and Monitoring

**Location**: `.env` and `fomc_research/__init__.py`

**Example - Enhanced Logging**:

Set log level in `.env` (line 26):
```bash
# Options: DEBUG, INFO, WARNING, ERROR
GOOGLE_GENAI_FOMC_AGENT_LOG_LEVEL="DEBUG"
```

**Add Custom Logging** in `__init__.py` (lines 20-25):
```python
import logging
import sys

loglevel = os.getenv("GOOGLE_GENAI_FOMC_AGENT_LOG_LEVEL", "INFO")
numeric_level = getattr(logging, loglevel.upper(), None)

# CUSTOMIZE: Add file handler with rotation
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__package__)
logger.setLevel(numeric_level)

# Add rotating file handler (10MB max, 5 backups)
file_handler = RotatingFileHandler(
    "fomc_agent.log",
    maxBytes=10*1024*1024,
    backupCount=5
)
file_handler.setFormatter(
    logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
)
logger.addHandler(file_handler)

# Add structured logging for production
import json
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "agent": record.name,
            "message": record.getMessage(),
            "file": record.filename,
            "line": record.lineno
        }
        return json.dumps(log_data)

json_handler = logging.StreamHandler(sys.stdout)
json_handler.setFormatter(JsonFormatter())
logger.addHandler(json_handler)
```

**Use Cases**:
- Production monitoring integration
- Export logs to Cloud Logging
- Track agent performance metrics
- Debug workflow issues

### 7. Customize BigQuery Timeseries Data

**Location**: `.env` and `deployment/bigquery_setup.py`

**Example - Add Custom Fed Futures Contracts**:

Edit `.env` (line 25):
```bash
# Original: Only 2 contracts
GOOGLE_GENAI_FOMC_AGENT_TIMESERIES_CODES="SFRH5,SFRZ5"

# CUSTOMIZE: Add more contracts for deeper analysis
GOOGLE_GENAI_FOMC_AGENT_TIMESERIES_CODES="SFRH5,SFRZ5,SFRM5,SFRU5,SFRQ5"
```

**Expand Data Schema** in BigQuery:
```sql
-- Add custom fields to timeseries table
ALTER TABLE `your-project.fomc_data.fed_futures`
ADD COLUMN open_interest INT64,
ADD COLUMN trading_volume INT64,
ADD COLUMN implied_volatility FLOAT64;
```

**Update Import Script** (`deployment/bigquery_setup.py`):
```python
def load_custom_timeseries_data(csv_file: str):
    """Load timeseries data with additional fields."""
    schema = [
        bigquery.SchemaField("date", "DATE"),
        bigquery.SchemaField("code", "STRING"),
        bigquery.SchemaField("price", "FLOAT64"),
        bigquery.SchemaField("open_interest", "INT64"),      # New
        bigquery.SchemaField("trading_volume", "INT64"),     # New
        bigquery.SchemaField("implied_volatility", "FLOAT64") # New
    ]
    # ... rest of import logic
```

**Use Cases**:
- Analyze multiple contract expirations
- Include options data alongside futures
- Track historical open interest trends
- Incorporate volatility metrics

---

**Note**: This agent is provided for illustrative purposes only. It demonstrates multi-agent workflows, external data integration, and production deployment patterns. Thoroughly test and validate before using in critical financial applications.
