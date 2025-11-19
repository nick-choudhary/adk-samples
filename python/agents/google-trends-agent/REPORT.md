# Google Trends Agent - Technical Documentation Report

## Project Scope

### High-Level Summary
The Google Trends Agent is an AI-powered system designed to surface and analyze the newest Google Trends in real-time. It leverages Google's public BigQuery dataset of trending search terms to identify emerging topics, analyze their velocity, and provide insights into what is currently capturing global attention across different regions and time periods.

### Core Capabilities
- **Real-Time Trend Discovery**: Access the latest trending search terms from Google's public dataset
- **Geographic Filtering**: Query trends by country, region, or city-specific data
- **Temporal Analysis**: Analyze trends across different time periods (weeks, quarters, specific dates)
- **Rising Term Detection**: Identify breakout terms with significant search volume increases
- **Natural Language Querying**: Convert user questions in plain English to optimized BigQuery SQL
- **Top Term Ranking**: Surface the most popular search terms by region and time period
- **Trend Velocity Metrics**: Access percent gain and score metrics for trending terms

### Primary Use Cases
- **Marketing Campaign Planning**: Design campaigns based on regional trends related to products/services
- **Content Creation**: Identify trending topics for timely content development
- **Market Research**: Analyze emerging interests and consumer behavior patterns
- **Competitive Intelligence**: Monitor industry-specific trending topics
- **Regional Analysis**: Compare trend patterns across different geographic locations
- **Trend Forecasting**: Identify rising topics before they reach mainstream awareness

### Target Users
- Marketing professionals and campaign planners
- Content creators and social media managers
- Business analysts and market researchers
- Data scientists studying consumer behavior
- Product managers identifying market opportunities
- News organizations tracking breaking trends

### Key Innovations/Differentiators
- **Two-Stage Pipeline Architecture**: Separates SQL generation from execution for clarity and debugging
- **Template-Based Prompting**: Uses Jinja2 templates with few-shot examples for consistent query generation
- **Automatic Cost Optimization**: Built-in LIMIT clauses and partition filtering to minimize BigQuery costs
- **Schema-Aware Generation**: Understands differences between US and international table structures
- **Domain-Specific Reasoning**: Specialized prompts for handling Google Trends dataset peculiarities
- **Error Resilience**: SQL cleaning and validation before execution

## Technical Architecture

### Multi-Agent Hierarchy

```
┌──────────────────────────────────────────────────────────────┐
│                  Google Trends Agent                         │
│                  (SequentialAgent)                           │
│          /google_trends_agent/agent.py (lines 56-61)        │
└──────────────────────────────────────────────────────────────┘
                            │
                            ├── Sequential Execution ──┐
                            │                          │
                            ▼                          ▼
          ┌─────────────────────────────┐   ┌────────────────────────────┐
          │ TrendsQueryGeneratorAgent   │   │ TrendsQueryExecutorAgent   │
          │      (LlmAgent)             │   │      (LlmAgent)            │
          │   agent.py (lines 28-34)    │   │  agent.py (lines 38-50)    │
          └─────────────────────────────┘   └────────────────────────────┘
                       │                                 │
                       │ Uses                            │ Uses
                       ▼                                 ▼
          ┌─────────────────────────┐        ┌──────────────────────────┐
          │  Dynamic Instructions   │        │  execute_bigquery_sql    │
          │  - Table Structure      │        │  (Custom Tool)           │
          │  - Few-Shot Examples    │        │  tools.py (lines 27-54)  │
          │  - Query Rules          │        └──────────────────────────┘
          │  prompt.py (lines 63-78)│
          └─────────────────────────┘
                       │
                       ├─── Loaded via Jinja2 ───┐
                       │                          │
                       ▼                          ▼
          ┌──────────────────────┐    ┌────────────────────────────┐
          │ Table Structure      │    │  Few-Shot Examples         │
          │ Template (.j2)       │    │  Template (.j2)            │
          │ Lines 1-60           │    │  Lines 1-159               │
          └──────────────────────┘    └────────────────────────────┘
```

### Code Flow Explanation

**Entry Point**: `/home/user/adk-samples/python/agents/google-trends-agent/google_trends_agent/agent.py`

1. **Environment and Configuration Loading** (lines 1-21):
   - Loads `.env` file from package directory (lines 10-13)
   - Sets model configurations:
     - `MODEL_AGENT`: `gemini-2.5-pro` for SQL generation (line 17)
     - `MODEL_TOOL`: `gemini-2.5-flash` for SQL execution (line 18)
   - Dynamically loads agent instructions from Jinja2 templates (line 21)

2. **TrendsQueryGeneratorAgent Initialization** (lines 28-34):
   - **Purpose**: Converts natural language questions to BigQuery SQL
   - **Model**: Uses `gemini-2.5-pro` for complex reasoning
   - **Instruction**: Loads comprehensive prompt with table schemas and examples
   - **Output**: Stores generated SQL in `state['generated_sql']` (line 33)
   - **No Tools**: Pure language-to-SQL translation without external calls

3. **TrendsQueryExecutorAgent Initialization** (lines 38-50):
   - **Purpose**: Executes SQL and interprets results for users
   - **Model**: Uses `gemini-2.5-flash` for faster execution
   - **Instruction**: Simple execution-focused prompt (lines 42-47)
     - Reads SQL from `{generated_sql}` placeholder
     - Uses `execute_bigquery_sql` tool without modification
     - Interprets query results for user-friendly output
   - **Tools**: Equipped with `execute_bigquery_sql` (line 49)

4. **Root Agent - SequentialAgent** (lines 56-61):
   - Orchestrates two-stage pipeline
   - Ensures sequential execution: generation → execution
   - Formats output as user-friendly markdown
   - Separates SQL query from result interpretation

5. **Prompt Loading Pipeline** (`/home/user/adk-samples/python/agents/google-trends-agent/google_trends_agent/prompt.py`):

   **`load_agent_instructions()` Function** (lines 63-78):
   - Calls `load_table_structure_prompt()` (lines 42-60)
   - Calls `load_few_shot_examples()` (lines 20-39)
   - Combines both templates into full instruction
   - Returns complete prompt or fallback on error

   **Template Loading Process**:
   ```
   1. Set up Jinja2 environment (lines 28-30)
   2. Load template from prompt-template/ directory
   3. Render template with dynamic values
   4. Return rendered string
   ```

6. **SQL Execution Tool** (`/home/user/adk-samples/python/agents/google-trends-agent/google_trends_agent/tools.py`):

   **`execute_bigquery_sql()` Function** (lines 27-54):
   - **Input**: SQL query string (potentially with markdown code blocks)
   - **Cleaning** (lines 16-24):
     - Removes newline escapes and actual newlines
     - Strips markdown code block markers (```sql```)
     - Normalizes whitespace
   - **Execution** (lines 32-36):
     - Creates BigQuery client using `GOOGLE_CLOUD_PROJECT` (line 34)
     - Submits query job and waits for completion
     - Converts RowIterator to list of dictionaries (line 39)
   - **Output** (lines 42-51):
     - Returns "Query returned no results." if empty
     - JSON-formatted results with datetime serialization
     - Error messages for failed queries

### Agent Definitions with Roles and Responsibilities

**1. TrendsQueryGeneratorAgent** (`agent.py` lines 28-34)
- **Role**: SQL query architect and BigQuery expert
- **Model**: `gemini-2.5-pro` - chosen for superior reasoning on complex query generation
- **Instruction Source**: Dynamically loaded from Jinja2 templates
- **Responsibilities**:
  - Parse natural language questions about Google Trends
  - Select appropriate table (US vs. international)
  - Apply mandatory `refresh_date` filtering for cost optimization
  - Generate syntactically correct BigQuery SQL
  - Handle complex queries (aggregations, subqueries, date ranges)
  - Apply LIMIT 100 to all queries
  - Store SQL in state for next agent
- **Output Key**: `generated_sql` - accessible to downstream agents via state

**2. TrendsQueryExecutorAgent** (`agent.py` lines 38-50)
- **Role**: SQL executor and results interpreter
- **Model**: `gemini-2.5-flash` - chosen for fast execution and interpretation
- **Instruction**: Simple execution-focused prompt (lines 42-47)
- **Responsibilities**:
  - Read SQL from `{generated_sql}` state variable
  - Execute SQL without modification using tool
  - Interpret raw JSON results
  - Format findings as user-friendly markdown
  - Provide insights and summaries
  - Handle empty results gracefully
- **Tools**: `execute_bigquery_sql`

### Key Libraries and Dependencies

From `/home/user/adk-samples/python/agents/google-trends-agent/pyproject.toml` (lines 11-21):

**Core Dependencies**:
- **google-cloud-aiplatform[adk,agent-engines]** (>=1.104.0,<2.0.0): Vertex AI and ADK framework
- **google-adk** (>=1.7.0,<2.0.0): Agent Development Kit core
- **google-genai** (>=1.26.0,<2.0.0): Gemini API client
- **google-cloud-bigquery** (>=3.35.0,<4.0.0): BigQuery client for data access
- **pydantic** (>=2.11.7,<3.0.0): Data validation and settings
- **jinja2** (>=3.1.6,<4.0.0): Template rendering for prompts
- **python-dotenv** (>=1.1.1,<2.0.0): Environment variable management
- **pandas** (>=2.3.1,<3.0.0): Data manipulation for query results
- **uvicorn** (>=0.35.0,<0.36.0): ASGI server for web deployments

**Deployment Dependencies** (lines 34-39):
- **absl-py** (^2.2.2): Command-line flag parsing for deployment scripts

### Tools and Integrations

**1. BigQuery Integration** (`tools.py`)

**execute_bigquery_sql Tool** (lines 27-54):
- **Purpose**: Query Google Trends public dataset
- **Dataset**: `bigquery-public-data.google_trends.*`
- **Tables Available**:
  - `top_terms` (US only)
  - `international_top_terms` (all countries)
  - `top_rising_terms` (US only)
  - `international_top_rising_terms` (all countries)

**SQL Cleaning Function** (lines 16-24):
- Handles markdown-formatted SQL from LLM output
- Removes escape sequences and code block markers
- Ensures clean SQL for BigQuery execution

**Error Handling** (lines 52-53):
- Catches all exceptions during query execution
- Returns formatted error messages to agent

**2. Google Trends BigQuery Dataset**

**Dataset Details** (from `google_trends_table_structure.j2`):

**Top Terms Tables** (lines 11-25):
- **Purpose**: Most popular overall search terms (top 25)
- **US Table**: `bigquery-public-data.google_trends.top_terms`
- **International Table**: `bigquery-public-data.google_trends.international_top_terms`
- **Schema**:
  - `term`: STRING - The search term
  - `rank`: INTEGER - Popularity rank (1-25)
  - `score`: INTEGER - Relative search interest (0-100)
  - `week`: DATE - First day of week for data
  - `refresh_date`: DATE - Partition key for filtering
  - `country_name`, `country_code`, `region_name`, `region_code`: Only in international table

**Top Rising Terms Tables** (lines 27-42):
- **Purpose**: Terms with biggest increase in search interest
- **US Table**: `bigquery-public-data.google_trends.top_rising_terms`
- **International Table**: `bigquery-public-data.google_trends.international_top_rising_terms`
- **Additional Field**: `percent_gain`: INTEGER - Percentage increase in search volume

**3. Jinja2 Template System** (`prompt.py`)

**Template Loading Functions**:
- `load_table_structure_prompt()` (lines 42-60): Loads schema and rules
- `load_few_shot_examples()` (lines 20-39): Loads example queries
- Both use Jinja2 `Environment` and `FileSystemLoader`
- Templates located in `prompt-template/` directory

### Reasoning Mechanisms

**1. Schema-Aware Query Generation** (`google_trends_table_structure.j2` lines 49-52)

**Table Selection Logic**:
```
IF user asks about USA → use top_terms or top_rising_terms
ELSE → use international_top_terms or international_top_rising_terms
       AND filter by country_name
```

**Query Type Selection**:
- "top terms", "most popular", "highest rank" → Top Terms tables
- "rising terms", "breakout", "trending up", "percent gain" → Top Rising Terms tables

**2. Mandatory Cost Optimization** (`google_trends_table_structure.j2` lines 44-47)

**Partition Filtering Rule**:
```sql
WHERE refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
```
- **Purpose**: Avoid expensive full table scans
- **Mandatory**: All queries must include this filter
- **Benefit**: Reduces query costs by ~99%

**Result Limiting**:
```sql
LIMIT 100
```
- Prevents excessive data processing costs
- Applied to all queries automatically

**3. Few-Shot Learning** (`google_trends_few_shots.j2`)

**Example Categories** (8 examples provided):
1. **Top terms in USA** (lines 5-21): Basic aggregation with ARRAY_AGG
2. **Rising terms from past date** (lines 23-45): Subquery for date calculation
3. **Filter by rank** (lines 47-62): Simple rank filtering
4. **Filter by percent gain** (lines 64-80): Breakout term detection
5. **Region-specific query** (lines 82-98): Regional filtering
6. **Time-based range** (lines 100-115): Date range queries
7. **Advanced subquery** (lines 117-142): Combining multiple tables
8. **US rising terms** (lines 144-159): US-specific rising term queries

**Learning Pattern**:
```
User Question → Correct SQL → Expected Output
```
- Teaches table selection logic
- Demonstrates proper filtering patterns
- Shows complex aggregation techniques
- Illustrates date handling

**4. Complex Aggregation Patterns** (`google_trends_table_structure.j2` lines 54-56)

**ARRAY_AGG Pattern for Top N Per Group**:
```sql
ARRAY_AGG(STRUCT(field1, field2) ORDER BY metric DESC LIMIT 1)
```
- Used for "highest score per term" type queries
- Enables efficient grouping without window functions
- Example: Find region with highest score for each term

## Build & Run Instructions

### Prerequisites

1. **Python Version**: Python 3.11 or higher (specified in `pyproject.toml` line 10)

2. **Poetry**: Dependency management tool
   ```bash
   pip install poetry
   ```

3. **Google Cloud Platform Requirements**:
   - Active GCP project with billing enabled
   - BigQuery API enabled
   - Project must have permissions to query public datasets

4. **Google Cloud CLI**: For authentication
   - Installation: https://cloud.google.com/sdk/docs/install

5. **For Deployment**: Google Cloud Storage bucket for staging artifacts

### Step-by-Step Installation

1. **Clone Repository and Navigate to Project**:
   ```bash
   git clone https://github.com/google/adk-samples.git
   cd adk-samples/python/agents/google-trends-agent
   ```

2. **Install Dependencies**:
   ```bash
   poetry install
   ```

   For deployment capabilities:
   ```bash
   poetry install --with deployment
   ```

3. **Verify Installation**:
   ```bash
   poetry show  # List installed packages
   poetry run python -c "import google_trends_agent; print('Installation successful!')"
   ```

### Configuration

#### Environment Variables Setup

**1. Authenticate with Google Cloud**:
```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Authenticate
gcloud auth application-default login
gcloud auth application-default set-quota-project $PROJECT_ID
```

**2. Create `.env` File**:

Create `/home/user/adk-samples/python/agents/google-trends-agent/google_trends_agent/.env`:

```bash
# Required for local and remote execution
GOOGLE_CLOUD_PROJECT="your-project-id"
GOOGLE_CLOUD_LOCATION="us-central1"

# Required only for deployment to Agent Engine
GOOGLE_CLOUD_STORAGE_BUCKET="your-storage-bucket-name"
```

**3. Grant BigQuery Permissions for Deployment** (Required only for Agent Engine deployment):

```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Get your project number
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Grant Agent Engine service account BigQuery permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
    --role="roles/bigquery.user"
```

**Explanation**: This grants the Agent Engine service account permission to run BigQuery jobs when the agent is deployed remotely.

### Running the Agent

#### CLI Interface

**1. Activate Poetry Environment**:
```bash
poetry shell
```

**2. Run Agent in CLI Mode**:
```bash
adk run .
```

**Example Queries**:
```
user: List the top 10 terms in Canada during the past 3 weeks
user: What are the rising terms in the USA with percent gain over 5000?
user: Show me the top ranked term in Germany for the latest week
user: Find rising terms in Brazil from the first quarter of 2023
```

#### Web UI Interface

**1. Start ADK Web Server**:
```bash
poetry shell
adk web
```

**2. Access Web Interface**:
- Open browser to displayed URL (typically http://localhost:8000)
- Select `google-trends-agent` from dropdown menu
- Interact through chatbot interface

#### Programmatic Access

**Python Script Example**:

```python
import os
import dotenv
from google.adk.runners import InMemoryRunner
from google.genai.types import Part, UserContent

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), "google_trends_agent", ".env")
dotenv.load_dotenv(dotenv_path)

# Import agent
from google_trends_agent.agent import root_agent

# Create runner
runner = InMemoryRunner(agent=root_agent)

# Create session
session = runner.session_service.create_session(
    app_name=runner.app_name,
    user_id="test_user"
)

# Send query
user_input = "List the top 10 terms in Canada during the past 3 weeks"
content = UserContent(parts=[Part(text=user_input)])

# Get response
for event in runner.run(
    user_id=session.user_id,
    session_id=session.id,
    new_message=content
):
    for part in event.content.parts:
        print(part.text)
```

### Example Interactions

**Example 1: Top Terms by Country and Time** (from README lines 136-165)

**User Query**:
```
List the top 10 terms in Canada during the past 3 weeks
```

**TrendsQueryGeneratorAgent Output**:
```sql
SELECT
  term,
  rank,
  week
FROM
  `bigquery-public-data.google_trends.international_top_terms`
WHERE
  refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  AND country_name = 'Canada'
  AND week IN (
    SELECT DISTINCT week
    FROM `bigquery-public-data.google_trends.international_top_terms`
    WHERE refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
      AND country_name = 'Canada'
    ORDER BY week DESC
    LIMIT 3
  )
ORDER BY week DESC, rank
LIMIT 100
```

**TrendsQueryExecutorAgent Output**:
```
The top terms in Canada for the week of 2025-07-13 are:

1. usyk vs dubois
2. man united vs leeds united
3. rashford
4. election loser nyt crossword answers
5. reading vs tottenham
6. blake wheeler
7. france vs germany
8. усик дюбуа
```

**Example 2: Rising Terms with High Percent Gain**

**User Query**:
```
Show me rising terms in the USA with percent gain over 5000
```

**Generated SQL**:
```sql
SELECT
  term,
  percent_gain,
  week
FROM
  `bigquery-public-data.google_trends.top_rising_terms`
WHERE
  refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  AND percent_gain > 5000
ORDER BY percent_gain DESC
LIMIT 100
```

**Agent Output**:
```
Here are the breakout terms in the USA with over 5000% gain:

1. **tornado warning** - 15,450% gain (Week of Jan 15, 2025)
2. **powerball winner** - 12,300% gain (Week of Jan 15, 2025)
3. **inauguration day** - 8,750% gain (Week of Jan 15, 2025)
4. **mlk day** - 6,200% gain (Week of Jan 15, 2025)

These represent explosive growth in search interest during specific events.
```

**Example 3: Region-Specific Query**

**User Query**:
```
What were the top 5 rising terms in the Ile-de-France region of France?
```

**Generated SQL**:
```sql
SELECT
  term,
  rank,
  percent_gain
FROM
  `bigquery-public-data.google_trends.international_top_rising_terms`
WHERE
  refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  AND country_name = 'France'
  AND region_name = 'Ile-de-France'
ORDER BY rank
LIMIT 5
```

### Testing and Evaluation

**Unit Testing**:

While the project doesn't include a `tests/` directory in the current structure, you can create basic tests:

```python
# Create tests/test_agent.py
import pytest
import dotenv
from google.adk.runners import InMemoryRunner
from google.genai.types import Part, UserContent
from google_trends_agent.agent import root_agent

@pytest.fixture(scope="session", autouse=True)
def load_env():
    dotenv.load_dotenv()

@pytest.mark.asyncio
async def test_top_terms_query():
    """Test basic top terms query."""
    user_input = "Show me the top 5 terms in Germany"

    runner = InMemoryRunner(agent=root_agent)
    session = await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id="test_user"
    )

    content = UserContent(parts=[Part(text=user_input)])
    response = ""

    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content
    ):
        if event.content.parts and event.content.parts[0].text:
            response = event.content.parts[0].text

    # Verify response contains expected elements
    assert "germany" in response.lower()
    assert len(response) > 0

@pytest.mark.asyncio
async def test_rising_terms_query():
    """Test rising terms with percent gain."""
    user_input = "Find rising terms in USA with percent gain over 1000"

    runner = InMemoryRunner(agent=root_agent)
    session = await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id="test_user"
    )

    content = UserContent(parts=[Part(text=user_input)])
    response = ""

    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content
    ):
        if event.content.parts and event.content.parts[0].text:
            response = event.content.parts[0].text

    # Verify response mentions percent gain or rising terms
    assert "percent" in response.lower() or "gain" in response.lower()
```

**Run Tests**:
```bash
poetry shell
pytest tests/ -v
```

### Deployment

#### Deploy to Vertex AI Agent Engine

**From**: `/home/user/adk-samples/python/agents/google-trends-agent/deployment/deploy.py`

**1. Install Deployment Dependencies**:
```bash
poetry install --with deployment
```

**2. Ensure Environment Variables are Set**:
```bash
# Verify .env file contains:
# GOOGLE_CLOUD_PROJECT
# GOOGLE_CLOUD_LOCATION
# GOOGLE_CLOUD_STORAGE_BUCKET
cat google_trends_agent/.env
```

**3. Run Deployment Script**:
```bash
poetry shell
python deployment/deploy.py
```

**Deployment Process** (lines 72-88):
- Loads requirements from `pyproject.toml`
- Wraps agent in `AdkApp` with tracing enabled
- Packages `google_trends_agent` directory
- Deploys to Vertex AI Agent Engine
- Updates `.env` with `AGENT_ENGINE_ID`

**Expected Output**:
```
deploying app...
Deployed agent to Vertex AI Agent Engine successfully,
resource name: projects/<PROJECT_NUMBER>/locations/<LOCATION>/reasoningEngines/<AGENT_ENGINE_ID>
Updated AGENT_ENGINE_ID in .env to projects/.../reasoningEngines/...
```

**4. Test Deployed Agent**:
```bash
python deployment/test_deployment.py
```

**Interactive Testing**:
```
Enter your query (or 'quit' to exit): List top 10 terms in Japan
[Agent response displayed]

Enter your query (or 'quit' to exit): quit
```

**5. Programmatic Access to Deployed Agent**:

```python
import dotenv
dotenv.load_dotenv()
from vertexai import agent_engines
import os

agent_engine_id = os.getenv("AGENT_ENGINE_ID")
agent_engine = agent_engines.get(agent_engine_id)

# Create session
session = agent_engine.create_session(user_id="production_user")

# Query agent
for event in agent_engine.stream_query(
    user_id=session["user_id"],
    session_id=session["id"],
    message="Show me rising terms in Australia with percent gain over 2000"
):
    for part in event["content"]["parts"]:
        print(part["text"])
```

### Troubleshooting

**Issue 1: BigQuery Permission Denied**
```
Error: Access Denied: Project your-project-id: User does not have
bigquery.jobs.create permission
```
**Solution**:
```bash
# Grant yourself BigQuery User role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="user:your-email@example.com" \
    --role="roles/bigquery.user"
```

**Issue 2: Missing Environment Variables**
```
KeyError: 'GOOGLE_CLOUD_PROJECT'
```
**Solution**:
- Verify `.env` file exists in `google_trends_agent/` directory
- Check variable names match exactly
- Ensure `dotenv.load_dotenv()` is called before importing agent

**Issue 3: Query Returns No Results**
```
Query returned no results.
```
**Solution**:
- Check if date range is too specific or in the future
- Verify country/region names match dataset exactly (case-sensitive)
- Try broader queries first (e.g., "top terms in USA")

**Issue 4: SQL Syntax Errors**
```
Error executing BigQuery query: Syntax error: Expected end of input
but got keyword SELECT
```
**Solution**:
- Review generated SQL in agent output
- Check for malformed subqueries
- Verify table names are correct
- Ensure `refresh_date` filter is present

**Issue 5: Deployment Fails**
```
Error: Missing required dependency: tomllib
```
**Solution** (Python < 3.11):
```bash
pip install tomli  # Backport for older Python versions
```

**Issue 6: Agent Engine Permission Denied**
```
Error: Service account does not have bigquery.jobs.create permission
```
**Solution**: Run the service account permission grant command from Configuration section:
```bash
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
    --role="roles/bigquery.user"
```

**Issue 7: Import Errors**
```
ModuleNotFoundError: No module named 'google_trends_agent'
```
**Solution**:
```bash
poetry shell  # Activate virtual environment
poetry install  # Reinstall dependencies
```

## Customization Options

### 1. Change Data Source to Alternative Trend Platforms

**Use Case**: Query trends from Twitter, TikTok, Reddit, or proprietary analytics platforms instead of Google Trends

**Implementation** (modify `/home/user/adk-samples/python/agents/google-trends-agent/google_trends_agent/tools.py`):

```python
# Original BigQuery implementation (lines 27-54)
def execute_bigquery_sql(sql: str) -> str:
    """Executes a BigQuery SQL query..."""
    # ... existing implementation ...

# Twitter Trends Integration
import tweepy
import json

def execute_twitter_trends_query(location: str = "worldwide") -> str:
    """Fetch trending topics from Twitter API."""
    try:
        # Set up Twitter API client
        client = tweepy.Client(bearer_token=os.getenv("TWITTER_BEARER_TOKEN"))

        # Map locations to WOEID (Where On Earth ID)
        location_map = {
            "worldwide": 1,
            "united states": 23424977,
            "canada": 23424775,
            "uk": 23424975,
        }

        woeid = location_map.get(location.lower(), 1)

        # Get trends for location
        trends = client.get_place_trends(id=woeid)

        # Format results
        trend_list = []
        for trend in trends[0]["trends"][:25]:
            trend_list.append({
                "name": trend["name"],
                "tweet_volume": trend.get("tweet_volume", "N/A"),
                "url": trend["url"]
            })

        return json.dumps(trend_list, indent=2)

    except Exception as e:
        return f"Error fetching Twitter trends: {str(e)}"

# Reddit Trends Integration
import praw

def execute_reddit_trends_query(subreddit: str = "all", time_filter: str = "day") -> str:
    """Fetch trending posts from Reddit."""
    try:
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
        )

        # Get hot posts from subreddit
        subreddit_obj = reddit.subreddit(subreddit)
        hot_posts = subreddit_obj.hot(limit=25)

        # Format results
        posts = []
        for post in hot_posts:
            posts.append({
                "title": post.title,
                "score": post.score,
                "num_comments": post.num_comments,
                "url": post.url,
                "created_utc": post.created_utc,
            })

        return json.dumps(posts, default=str, indent=2)

    except Exception as e:
        return f"Error fetching Reddit trends: {str(e)}"
```

**Update Agent to Use New Tools** (modify `agent.py` lines 38-50):

```python
from google_trends_agent.tools import (
    execute_bigquery_sql,
    execute_twitter_trends_query,
    execute_reddit_trends_query,
)

trends_query_executor_agent = LlmAgent(
    name="TrendsQueryExecutorAgent",
    model=MODEL_TOOL,
    instruction="""You have access to multiple trend sources:
    - Google Trends (via SQL)
    - Twitter Trends (via Twitter API)
    - Reddit Trends (via Reddit API)

    Choose the appropriate tool based on the user's request.
    Format results in a user-friendly markdown table.
    """,
    description="Executes trend queries across multiple platforms.",
    tools=[
        execute_bigquery_sql,
        execute_twitter_trends_query,
        execute_reddit_trends_query,
    ],
)
```

### 2. Add Sentiment Analysis to Trend Data

**Use Case**: Analyze sentiment of discussions around trending topics

**Implementation** (create `/home/user/adk-samples/python/agents/google-trends-agent/google_trends_agent/sentiment_tools.py`):

```python
from google.cloud import language_v1
import json

def analyze_trend_sentiment(term: str, sample_size: int = 100) -> str:
    """
    Analyze sentiment of conversations around a trending term.

    Uses Google Search to find recent content, then analyzes sentiment.
    """
    try:
        # Initialize Natural Language API client
        client = language_v1.LanguageServiceClient()

        # Fetch sample content about the term (simplified example)
        # In production, use Google Search API or web scraping
        sample_texts = fetch_sample_content(term, sample_size)

        # Analyze sentiment
        sentiments = []
        for text in sample_texts:
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT
            )
            sentiment = client.analyze_sentiment(
                request={'document': document}
            ).document_sentiment

            sentiments.append({
                "score": sentiment.score,  # -1.0 (negative) to 1.0 (positive)
                "magnitude": sentiment.magnitude,  # 0.0 to infinity
            })

        # Aggregate results
        avg_score = sum(s["score"] for s in sentiments) / len(sentiments)
        avg_magnitude = sum(s["magnitude"] for s in sentiments) / len(sentiments)

        # Classify overall sentiment
        if avg_score > 0.25:
            sentiment_label = "Positive"
        elif avg_score < -0.25:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"

        return json.dumps({
            "term": term,
            "sentiment": sentiment_label,
            "average_score": round(avg_score, 2),
            "average_magnitude": round(avg_magnitude, 2),
            "sample_size": len(sentiments),
        }, indent=2)

    except Exception as e:
        return f"Error analyzing sentiment: {str(e)}"

def fetch_sample_content(term: str, sample_size: int) -> list[str]:
    """Fetch sample content mentioning the term (placeholder)."""
    # Implement using Google Search API, News API, or web scraping
    # This is a simplified placeholder
    return [f"Sample text about {term}" for _ in range(sample_size)]
```

**Add to Agent** (modify `agent.py`):

```python
from google_trends_agent.sentiment_tools import analyze_trend_sentiment

# Add tool to executor agent
trends_query_executor_agent = LlmAgent(
    name="TrendsQueryExecutorAgent",
    model=MODEL_TOOL,
    instruction="""Execute BigQuery SQL queries and optionally analyze sentiment.

    After showing trends, you can analyze sentiment by calling
    analyze_trend_sentiment with interesting terms.
    """,
    tools=[execute_bigquery_sql, analyze_trend_sentiment],
)
```

### 3. Implement Automated Notifications for Specific Trends

**Use Case**: Send alerts via email or Slack when trends match specific criteria

**Implementation** (create `/home/user/adk-samples/python/agents/google-trends-agent/google_trends_agent/notification_tools.py`):

```python
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

def send_email_alert(term: str, details: dict) -> str:
    """Send email alert for trending term."""
    try:
        sender_email = os.getenv("ALERT_EMAIL_SENDER")
        sender_password = os.getenv("ALERT_EMAIL_PASSWORD")
        recipient_email = os.getenv("ALERT_EMAIL_RECIPIENT")

        # Create message
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = f"Trend Alert: {term}"

        # Email body
        body = f"""
        New trend detected: {term}

        Details:
        - Rank: {details.get('rank', 'N/A')}
        - Score: {details.get('score', 'N/A')}
        - Percent Gain: {details.get('percent_gain', 'N/A')}%
        - Region: {details.get('region', 'N/A')}
        - Week: {details.get('week', 'N/A')}

        This is an automated alert from Google Trends Agent.
        """

        msg.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return f"Email alert sent for term: {term}"

    except Exception as e:
        return f"Error sending email alert: {str(e)}"

def send_slack_alert(term: str, details: dict) -> str:
    """Send Slack alert for trending term."""
    try:
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")

        # Create Slack message
        message = {
            "text": f"*Trend Alert: {term}*",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔥 Trending: {term}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Rank:*\n{details.get('rank', 'N/A')}"},
                        {"type": "mrkdwn", "text": f"*Score:*\n{details.get('score', 'N/A')}"},
                        {"type": "mrkdwn", "text": f"*Percent Gain:*\n{details.get('percent_gain', 'N/A')}%"},
                        {"type": "mrkdwn", "text": f"*Region:*\n{details.get('region', 'N/A')}"},
                    ]
                }
            ]
        }

        # Send to Slack
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()

        return f"Slack alert sent for term: {term}"

    except Exception as e:
        return f"Error sending Slack alert: {str(e)}"

def create_trend_monitor(keywords: list[str], percent_gain_threshold: int = 1000) -> str:
    """
    Monitor trends and send alerts when keywords appear with high gain.

    This can be run as a scheduled job (e.g., Cloud Scheduler).
    """
    try:
        from google_trends_agent.tools import execute_bigquery_sql

        # Build monitoring query
        keyword_filter = "', '".join(keywords)
        sql = f"""
        SELECT
          term,
          percent_gain,
          rank,
          score,
          week,
          country_name,
          region_name
        FROM
          `bigquery-public-data.google_trends.international_top_rising_terms`
        WHERE
          refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
          AND LOWER(term) IN ('{keyword_filter.lower()}')
          AND percent_gain > {percent_gain_threshold}
        ORDER BY
          percent_gain DESC
        LIMIT 100
        """

        # Execute query
        results = execute_bigquery_sql(sql)

        if results == "Query returned no results.":
            return "No matching trends found."

        # Parse results and send alerts
        trends = json.loads(results)
        alerts_sent = []

        for trend in trends:
            # Send both email and Slack alerts
            email_result = send_email_alert(trend["term"], trend)
            slack_result = send_slack_alert(trend["term"], trend)
            alerts_sent.append(f"{trend['term']}: {email_result}, {slack_result}")

        return f"Alerts sent for {len(alerts_sent)} trends:\n" + "\n".join(alerts_sent)

    except Exception as e:
        return f"Error in trend monitoring: {str(e)}"
```

**Schedule Monitoring** (using Cloud Scheduler):

```python
# Create /home/user/adk-samples/python/agents/google-trends-agent/scheduled_monitor.py

import dotenv
dotenv.load_dotenv()
from google_trends_agent.notification_tools import create_trend_monitor

# Monitor specific keywords
keywords_to_watch = [
    "ai agents",
    "gemini",
    "vertex ai",
    "machine learning",
    "artificial intelligence",
]

result = create_trend_monitor(
    keywords=keywords_to_watch,
    percent_gain_threshold=500
)

print(result)
```

**Deploy as Cloud Function**:
```bash
gcloud functions deploy trend-monitor \
    --runtime python311 \
    --trigger-http \
    --entry-point create_trend_monitor \
    --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id
```

### 4. Add Data Visualization Capabilities

**Use Case**: Generate charts and graphs for trend data analysis

**Implementation** (create `/home/user/adk-samples/python/agents/google-trends-agent/google_trends_agent/visualization_tools.py`):

```python
import matplotlib.pyplot as plt
import pandas as pd
import json
from io import BytesIO
import base64

def create_trend_chart(query_results: str, chart_type: str = "bar") -> str:
    """
    Create visualization from query results.

    Args:
        query_results: JSON string from execute_bigquery_sql
        chart_type: "bar", "line", or "pie"

    Returns:
        Base64-encoded image or file path
    """
    try:
        # Parse results
        data = json.loads(query_results)
        df = pd.DataFrame(data)

        # Create figure
        plt.figure(figsize=(12, 6))

        if chart_type == "bar":
            # Bar chart for rankings
            if "term" in df.columns and "score" in df.columns:
                df_sorted = df.sort_values("score", ascending=False).head(10)
                plt.barh(df_sorted["term"], df_sorted["score"])
                plt.xlabel("Score")
                plt.ylabel("Term")
                plt.title("Top Trending Terms by Score")

        elif chart_type == "line":
            # Line chart for time series
            if "week" in df.columns and "score" in df.columns:
                df["week"] = pd.to_datetime(df["week"])
                df_sorted = df.sort_values("week")

                # Group by term if multiple terms
                if "term" in df.columns:
                    for term in df["term"].unique()[:5]:  # Limit to 5 terms
                        term_data = df_sorted[df_sorted["term"] == term]
                        plt.plot(term_data["week"], term_data["score"], label=term, marker="o")
                    plt.legend()
                else:
                    plt.plot(df_sorted["week"], df_sorted["score"], marker="o")

                plt.xlabel("Week")
                plt.ylabel("Score")
                plt.title("Trend Score Over Time")
                plt.xticks(rotation=45)

        elif chart_type == "pie":
            # Pie chart for distribution
            if "term" in df.columns and "score" in df.columns:
                df_sorted = df.sort_values("score", ascending=False).head(10)
                plt.pie(df_sorted["score"], labels=df_sorted["term"], autopct="%1.1f%%")
                plt.title("Distribution of Top Terms by Score")

        plt.tight_layout()

        # Save to bytes buffer
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
        buffer.seek(0)

        # Encode as base64
        image_base64 = base64.b64encode(buffer.read()).decode()

        plt.close()

        return f"Chart generated successfully (base64): {image_base64[:50]}..."

    except Exception as e:
        return f"Error creating chart: {str(e)}"

def create_heatmap(country: str = "United States") -> str:
    """Create heatmap of regional trend intensity."""
    try:
        from google_trends_agent.tools import execute_bigquery_sql

        # Query regional data
        sql = f"""
        SELECT
          region_name,
          AVG(score) as avg_score,
          COUNT(*) as term_count
        FROM
          `bigquery-public-data.google_trends.international_top_terms`
        WHERE
          refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
          AND country_name = '{country}'
          AND region_name IS NOT NULL
        GROUP BY
          region_name
        ORDER BY
          avg_score DESC
        LIMIT 100
        """

        results = execute_bigquery_sql(sql)
        data = json.loads(results)
        df = pd.DataFrame(data)

        # Create heatmap (simplified - would need geographic library for real map)
        plt.figure(figsize=(10, 8))
        regions = df["region_name"]
        scores = df["avg_score"]

        plt.barh(regions, scores)
        plt.xlabel("Average Score")
        plt.ylabel("Region")
        plt.title(f"Regional Trend Intensity - {country}")
        plt.tight_layout()

        # Save
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=300)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        return f"Heatmap generated for {country}"

    except Exception as e:
        return f"Error creating heatmap: {str(e)}"
```

**Add to Agent**:
```python
from google_trends_agent.visualization_tools import create_trend_chart, create_heatmap

trends_query_executor_agent = LlmAgent(
    name="TrendsQueryExecutorAgent",
    model=MODEL_TOOL,
    instruction="""Execute SQL queries and optionally create visualizations.

    After showing tabular results, offer to create charts using:
    - create_trend_chart(results, chart_type="bar|line|pie")
    - create_heatmap(country="Country Name")
    """,
    tools=[execute_bigquery_sql, create_trend_chart, create_heatmap],
)
```

### 5. Add Comparative Analysis Across Regions/Time Periods

**Use Case**: Compare trends between different countries or time periods

**Implementation** (create `/home/user/adk-samples/python/agents/google-trends-agent/google_trends_agent/comparison_tools.py`):

```python
import json
import pandas as pd
from google_trends_agent.tools import execute_bigquery_sql

def compare_countries(term: str, countries: list[str], weeks_back: int = 4) -> str:
    """Compare how a term trends across multiple countries."""
    try:
        country_filter = "', '".join(countries)

        sql = f"""
        SELECT
          country_name,
          week,
          AVG(score) as avg_score,
          MIN(rank) as best_rank
        FROM
          `bigquery-public-data.google_trends.international_top_terms`
        WHERE
          refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
          AND LOWER(term) = LOWER('{term}')
          AND country_name IN ('{country_filter}')
          AND week >= DATE_SUB(CURRENT_DATE(), INTERVAL {weeks_back} WEEK)
        GROUP BY
          country_name, week
        ORDER BY
          week DESC, avg_score DESC
        LIMIT 100
        """

        results = execute_bigquery_sql(sql)

        if results == "Query returned no results.":
            return f"No data found for '{term}' in specified countries."

        data = json.loads(results)
        df = pd.DataFrame(data)

        # Create comparison summary
        summary = []
        for country in countries:
            country_data = df[df["country_name"] == country]
            if not country_data.empty:
                avg_score = country_data["avg_score"].mean()
                best_rank = country_data["best_rank"].min()
                summary.append({
                    "country": country,
                    "average_score": round(avg_score, 2),
                    "best_rank": int(best_rank),
                    "appearances": len(country_data),
                })

        return json.dumps({
            "term": term,
            "comparison_summary": summary,
            "detailed_data": data,
        }, indent=2)

    except Exception as e:
        return f"Error comparing countries: {str(e)}"

def compare_time_periods(
    country: str,
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str
) -> str:
    """Compare trending terms between two time periods."""
    try:
        sql = f"""
        WITH period1 AS (
          SELECT
            term,
            AVG(score) as avg_score,
            MIN(rank) as best_rank
          FROM
            `bigquery-public-data.google_trends.international_top_terms`
          WHERE
            refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
            AND country_name = '{country}'
            AND week BETWEEN '{period1_start}' AND '{period1_end}'
          GROUP BY term
        ),
        period2 AS (
          SELECT
            term,
            AVG(score) as avg_score,
            MIN(rank) as best_rank
          FROM
            `bigquery-public-data.google_trends.international_top_terms`
          WHERE
            refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
            AND country_name = '{country}'
            AND week BETWEEN '{period2_start}' AND '{period2_end}'
          GROUP BY term
        )
        SELECT
          COALESCE(p1.term, p2.term) as term,
          p1.avg_score as period1_score,
          p1.best_rank as period1_rank,
          p2.avg_score as period2_score,
          p2.best_rank as period2_rank,
          (p2.avg_score - p1.avg_score) as score_change
        FROM period1 p1
        FULL OUTER JOIN period2 p2 ON p1.term = p2.term
        ORDER BY ABS(score_change) DESC
        LIMIT 100
        """

        results = execute_bigquery_sql(sql)
        data = json.loads(results)

        # Categorize changes
        new_terms = [d for d in data if d.get("period1_score") is None]
        disappeared_terms = [d for d in data if d.get("period2_score") is None]
        rising_terms = [d for d in data if d.get("score_change", 0) > 10]
        declining_terms = [d for d in data if d.get("score_change", 0) < -10]

        return json.dumps({
            "country": country,
            "period1": f"{period1_start} to {period1_end}",
            "period2": f"{period2_start} to {period2_end}",
            "new_terms": new_terms[:10],
            "disappeared_terms": disappeared_terms[:10],
            "rising_terms": rising_terms[:10],
            "declining_terms": declining_terms[:10],
        }, indent=2)

    except Exception as e:
        return f"Error comparing time periods: {str(e)}"
```

These customization options transform the Google Trends Agent from a basic query tool into a comprehensive trend analysis platform with multi-source data, sentiment analysis, automated monitoring, visualization capabilities, and comparative analytics.
