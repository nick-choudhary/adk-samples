# Brand Search Optimization - Technical Documentation Report

## Project Scope

### High-Level Summary
The Brand Search Optimization agent is an advanced multi-agent system designed to enhance product data for retail websites by generating keywords based on product information, performing automated web searches, and analyzing top search results to provide actionable recommendations for enriching product titles. This addresses common e-commerce challenges such as "Null & Low Recovery" or "Zero Results" searches by identifying gaps in product data presentation.

### Core Capabilities
- **Automated Keyword Generation**: Extracts and generates relevant search keywords from product catalog data stored in BigQuery
- **Web Browser Automation**: Performs automated web searches and crawls e-commerce websites using Selenium WebDriver
- **Competitive Analysis**: Analyzes top search results to identify patterns and best practices in product titling
- **Data-Driven Recommendations**: Provides specific suggestions for improving product titles based on competitor analysis
- **Multi-Agent Orchestration**: Coordinates three specialized sub-agents for keyword finding, search results retrieval, and comparison analysis

### Primary Use Cases
- **Product Title Optimization**: Enhance product titles to improve search discoverability
- **Zero Results Prevention**: Identify and fix product data gaps that lead to failed searches
- **Competitive Intelligence**: Understand how competitors structure their product information
- **Search Engine Optimization**: Improve product findability on e-commerce platforms
- **Data Quality Enhancement**: Systematically improve product catalog completeness

### Target Users
- **E-commerce Product Managers**: Responsible for catalog quality and search performance
- **Digital Merchandising Teams**: Need to optimize product presentation
- **SEO Specialists**: Focus on improving product discoverability
- **Data Quality Engineers**: Maintain and enhance product catalog data
- **Retail Operations Teams**: Manage large-scale product inventories

### Key Innovations/Differentiators
- **Computer Use Integration**: Leverages ADK's computer use capability for autonomous web browsing
- **BigQuery Integration**: Direct connection to enterprise data warehouses for scalable product data access
- **Router Agent Pattern**: Implements a sophisticated multi-agent design pattern with specialized sub-agents
- **Automated Web Analysis**: Uses AI to analyze webpage structure and determine navigation actions
- **Context-Aware Recommendations**: Provides brand-specific suggestions based on actual search behavior

## Technical Architecture

### Multi-Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                     Root Agent                               │
│              (brand_search_optimization)                     │
│         Orchestrates workflow and routes requests            │
└──────────────────┬──────────────────────────────────────────┘
                   │
         ┌─────────┴─────────┬─────────────────┐
         │                   │                 │
         ▼                   ▼                 ▼
┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Keyword       │  │  Search Results  │  │  Comparison      │
│  Finding Agent │  │  Agent           │  │  Root Agent      │
│                │  │                  │  │                  │
│ - Queries BQ   │  │ - Web browsing   │  │ - Orchestrates   │
│ - Extracts     │  │ - Takes actions  │  │   comparison     │
│   keywords     │  │ - Screenshots    │  │                  │
└────────────────┘  └──────────────────┘  └────────┬─────────┘
                                                    │
                                          ┌─────────┴─────────┐
                                          │                   │
                                          ▼                   ▼
                                  ┌──────────────┐  ┌─────────────────┐
                                  │ Comparison   │  │ Comparison      │
                                  │ Generator    │  │ Critic Agent    │
                                  │ Agent        │  │                 │
                                  └──────────────┘  └─────────────────┘
```

### Code Flow Explanation

**1. Entry Point - Root Agent** (`brand_search_optimization/agent.py`, lines 28-38)
   - Creates the main orchestrator using `Agent` class from ADK
   - Registers three sub-agents: `keyword_finding_agent`, `search_results_agent`, `comparison_root_agent`
   - Uses the Router Agent pattern to delegate tasks to specialized agents

**2. Root Agent Prompt Logic** (`brand_search_optimization/prompt.py`, lines 17-51)
   - **Gather Brand Name**: Requests brand name from user (lines 26-30)
   - **Sequential Steps**: Executes a strict workflow (lines 32-45):
     1. Calls `keyword_finding_agent` to get keywords
     2. Transfers back to main agent
     3. Calls `search_results_agent` for top keyword
     4. Transfers back to main agent
     5. Calls `comparison_root_agent` to generate report

**3. Keyword Finding Sub-Agent** (`brand_search_optimization/sub_agents/keyword_finding/agent.py`, lines 23-31)
   - Configured with BigQuery connector tool
   - Queries product database for brand-specific data
   - Extracts relevant keywords from product titles, descriptions, and attributes

**4. BigQuery Tool** (`brand_search_optimization/tools/bq_connector.py`, lines 30-83)
   - Initializes BigQuery client (lines 23-27)
   - Function `get_product_details_for_brand` (lines 30-83):
     - Receives brand name from user input (line 46)
     - Queries BigQuery table with brand filter (lines 50-60)
     - Returns results as markdown table (lines 71-82)
     - Limits to 3 products for efficiency (line 59)

**5. Search Results Sub-Agent** (`brand_search_optimization/sub_agents/search_results/agent.py`, lines 187-203)
   - Equipped with 9 specialized tools for web automation:
     - `go_to_url`: Navigate to websites (lines 41-45)
     - `take_screenshot`: Capture page state (lines 48-62)
     - `find_element_with_text`: Locate page elements (lines 71-84)
     - `click_element_with_text`: Interact with buttons/links (lines 87-100)
     - `enter_text_into_element`: Input search terms (lines 103-118)
     - `scroll_down_screen`: Navigate long pages (lines 121-125)
     - `get_page_source`: Extract HTML content (lines 128-132)
     - `load_artifacts_tool`: Process page artifacts (line 200)
     - `analyze_webpage_and_determine_action`: AI-powered navigation decision (lines 135-184)

**6. Web Automation Flow**:
   - Selenium WebDriver initialization (lines 32-38)
   - Chrome driver with custom options for debugging and data persistence
   - Agent uses tools to navigate, search, and extract results
   - Screenshot artifacts saved for analysis

**7. Comparison Root Agent** (`brand_search_optimization/sub_agents/comparison/agent.py`, lines 35-41)
   - Orchestrates two specialized sub-agents:
     - `comparison_generator_agent`: Creates initial comparison (lines 21-26)
     - `comparsion_critic_agent`: Reviews and improves comparison (lines 28-33)
   - Implements a generate-critique-refine pattern

### Agent Definitions with Roles and Responsibilities

**Root Agent** (`brand_search_optimization/agent.py`)
- **Role**: Workflow orchestrator and request router
- **Responsibilities**:
  - Manage user interaction and gather brand information
  - Route requests to appropriate sub-agents in correct sequence
  - Ensure all workflow steps complete before finishing
  - Maintain conversation context across agent transfers

**Keyword Finding Agent** (`brand_search_optimization/sub_agents/keyword_finding/agent.py`)
- **Role**: Product data analyst and keyword extractor
- **Responsibilities**:
  - Query BigQuery database for brand-specific products
  - Analyze product titles, descriptions, and attributes
  - Generate ranked list of search keywords
  - Return keywords in structured format

**Search Results Agent** (`brand_search_optimization/sub_agents/search_results/agent.py`)
- **Role**: Autonomous web browser and data collector
- **Responsibilities**:
  - Navigate to e-commerce websites
  - Perform searches using generated keywords
  - Analyze search results pages
  - Extract top search result information
  - Handle dynamic web pages and CAPTCHA challenges

**Comparison Root Agent** (`brand_search_optimization/sub_agents/comparison/agent.py`)
- **Role**: Analysis coordinator
- **Responsibilities**:
  - Coordinate comparison generation and critique
  - Ensure quality of recommendations
  - Manage sub-agent delegation

**Comparison Generator Agent**
- **Role**: Competitive analysis generator
- **Responsibilities**:
  - Compare product titles from brand vs. competitors
  - Identify patterns and best practices
  - Generate actionable recommendations
  - Structure findings in clear format

**Comparison Critic Agent**
- **Role**: Quality assurance reviewer
- **Responsibilities**:
  - Review generated comparisons for accuracy
  - Suggest improvements to recommendations
  - Ensure recommendations are actionable
  - Validate analysis quality

### Key Libraries and Dependencies

From `pyproject.toml` (lines 9-17):
- **google-genai (>=1.5.0)**: Google's Generative AI SDK for LLM interactions
- **selenium (>=4.30.0)**: Web browser automation framework
- **webdriver-manager (>=4.0.2)**: Automatic WebDriver binary management
- **google-cloud-bigquery (>=3.31.0)**: BigQuery database connectivity
- **absl-py (>=2.2.2)**: Application utilities and logging
- **google-cloud-aiplatform[agent-engines] (>=1.93.0)**: Vertex AI deployment capabilities
- **pillow (>=11.1.0)**: Image processing for screenshots
- **google-adk (>=1.0.0)**: Agent Development Kit core framework

### Tools and Integrations

**BigQuery Connector** (`brand_search_optimization/tools/bq_connector.py`)
- Direct SQL queries to product catalog
- Parameterized queries for security
- Markdown table output format
- Connection pooling for performance

**Computer Use Tools** (Selenium-based):
- Browser automation for Google Shopping (or configurable websites)
- Element detection and interaction
- Screenshot capture and artifact management
- Dynamic page analysis

**ADK Built-in Tools**:
- `load_artifacts_tool`: Manages artifacts like screenshots and HTML content
- Agent transfer mechanisms for sub-agent delegation

### Reasoning Mechanisms

**1. Sequential Workflow Enforcement** (`prompt.py`, lines 32-45)
- Root agent follows strict sequential steps
- Each step must complete before proceeding
- Prevents skipping critical analysis stages

**2. AI-Powered Web Navigation** (`sub_agents/search_results/agent.py`, lines 135-184)
- Agent analyzes webpage HTML to determine next action
- Considers: scrolling, clicking, text entry, or completion
- Adapts to different website structures dynamically

**3. Generate-Critique-Refine Pattern** (`sub_agents/comparison/agent.py`)
- Initial comparison generated by specialist agent
- Critique agent reviews and suggests improvements
- Ensures high-quality recommendations

**4. Tool-Augmented Reasoning**
- Agents request specific tools when needed
- BigQuery tool provides data context
- Web tools enable information gathering
- Artifacts enable visual analysis

## Build & Run Instructions

### Prerequisites

**Required Software:**
- **Python 3.11+**: Latest Python version for modern async features
- **Poetry**: Dependency management and packaging
  - Installation: Visit [python-poetry.org/docs](https://python-poetry.org/docs/)
  - Or via pip: `pip install poetry`
- **Git**: For repository cloning

**Required Accounts:**
- **Google Cloud Platform Account**: For BigQuery and Vertex AI services
- **GCP Project**: Active project with billing enabled
- **Google Cloud CLI**: For authentication
  - Installation: [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)

**Optional:**
- **Google AI Studio API Key**: Alternative to Vertex AI
  - Get from [aistudio.google.com](https://aistudio.google.com)

### Step-by-Step Installation

**1. Clone Repository**
```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/brand-search-optimization
```

**2. Configure Environment Variables**
```bash
# Copy example environment file
cp env.example .env

# Edit .env file with your values
nano .env  # or use your preferred editor
```

**Required .env Configuration:**
```bash
# Model Backend Selection
GOOGLE_GENAI_USE_VERTEXAI=1  # 1 for Vertex AI, 0 for ML Dev

# Vertex AI Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1  # or your preferred region
MODEL=gemini-2.5-flash

# BigQuery Configuration
DATASET_ID=products_data_agent
TABLE_ID=shoe_items

# Web Driver Configuration
DISABLE_WEB_DRIVER=0  # 0 to enable, 1 to disable for testing

# Deployment Configuration (optional)
STAGING_BUCKET=your-bucket-name
```

**3. Authenticate with Google Cloud**
```bash
gcloud auth application-default login
```

**4. Install Dependencies and Setup Database**
```bash
# This script will:
# 1. Create and activate virtual environment
# 2. Install Python packages via Poetry
# 3. Populate BigQuery with sample data
sh deployment/run.sh
```

**Manual Installation Alternative:**
```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Populate BigQuery manually
python deployment/bq_populate_data.py
```

**5. Verify Installation**
```bash
# Check ADK installation
adk --version

# List available agents
adk list
```

### Configuration

**Environment Variables** (from `brand_search_optimization/shared_libraries/constants.py`, lines 23-32):
- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID (required)
- `GOOGLE_CLOUD_LOCATION`: Region for Vertex AI (default: "global")
- `MODEL`: LLM model name (default: "gemini-2.5-flash")
- `DATASET_ID`: BigQuery dataset name (default: "products_data_agent")
- `TABLE_ID`: BigQuery table name (default: "shoe_items")
- `DISABLE_WEB_DRIVER`: Disable Selenium for testing (default: 0)
- `STAGING_BUCKET`: GCS bucket for deployment (optional)

**BigQuery Table Schema:**
The auto-populated table includes:
- `Title`: Product title string
- `Description`: Product description text
- `Attributes`: Product attributes (size, color, etc.)
- `Brand`: Brand name for filtering

### Running the Agent

**CLI Interface:**
```bash
adk run brand_search_optimization
```

**Web UI Interface:**
```bash
# Start web server
adk web

# Navigate to printed URL (typically http://localhost:8080)
# Select "brand-search-optimization" from dropdown menu
```

**Important Notes:**
- Web driver will open a Chrome window - **do not close it manually**
- Set `DISABLE_WEB_DRIVER=0` in `.env` before running
- Complete CAPTCHA on first Google Shopping visit (if using that website)
- After CAPTCHA completion, agent runs automatically in subsequent sessions

### Example Interactions

**Example Session Flow:**

**User Input 1:**
```
Hello, I need help with brand search optimization
```

**Agent Response:**
```
Hello! I'm your Brand Search Optimization assistant. I help enhance product
titles by analyzing search results. To get started, please provide me with
a brand name.
```

**User Input 2:**
```
BSOAgentTestBrand
```

**Agent Response:**
```
[Calls keyword_finding_agent]
I found the following keywords for BSOAgentTestBrand:

| Keyword | Rank |
|---------|------|
| Kids running shoes | 1 |
| Athletic footwear | 2 |
| Sports sneakers | 3 |

Would you like me to search for these keywords?
```

**User Input 3:**
```
Yes, please search for the top keyword
```

**Agent Response:**
```
[Calls search_results_agent - opens browser, navigates, searches]
[Takes screenshots, extracts results]

I've found the top 3 search results for "Kids running shoes". Here's what I found:

1. Brand X Kids Running Shoes - Size 5-12, Multiple Colors
2. SuperSport Youth Athletic Sneakers - Lightweight Design
3. ActiveKids Running Trainers - Breathable Mesh

Would you like me to compare these with your products?
```

**User Input 4:**
```
Yes, create a comparison report
```

**Agent Response:**
```
[Calls comparison_root_agent]
[comparison_generator_agent creates report]
[comparsion_critic_agent reviews]

## Comparison Report

### Your Current Title:
"BSOAgentTestBrand Shoes"

### Top Competitor Titles:
1. "Brand X Kids Running Shoes - Size 5-12, Multiple Colors"
2. "SuperSport Youth Athletic Sneakers - Lightweight Design"

### Recommendations:
1. Add size range to title for better discoverability
2. Include product category ("Kids Running Shoes" vs just "Shoes")
3. Mention key features (colors, design characteristics)
4. Consider age group specification (Kids/Youth)

### Suggested Improved Title:
"BSOAgentTestBrand Kids Running Shoes - Size 5-12, Lightweight Design, Multiple Colors"
```

For a complete interaction example, see: `tests/example_interaction.md`

### Testing and Evaluation

**Unit Tests:**
```bash
# 1. Set test mode in .env
echo "DISABLE_WEB_DRIVER=1" >> .env

# 2. Run tests
sh deployment/test.sh

# Or manually with pytest
pytest tests/unit/test_tools.py
```

**Evaluation Suite:**
```bash
# Run ADK evaluation
sh deployment/eval.sh
```

**Evaluation Configuration:**
- Uses ADK's built-in evaluation framework
- Test cases defined in `eval/data/`
- Configuration in `eval/data/test_config.json`
- Measures accuracy, relevance, and completeness of recommendations

**Test Coverage:**
- BigQuery tool functionality with mock client
- Agent routing and workflow
- Data extraction and formatting
- Error handling scenarios

### Deployment

**Deploy to Vertex AI Agent Engine:**

**Prerequisites:**
```bash
# 1. Enable DISABLE_WEB_DRIVER for deployment
echo "DISABLE_WEB_DRIVER=1" >> .env

# 2. Ensure STAGING_BUCKET is set
# (Agent Engine doesn't support web driver in production)
```

**Deployment Command:**
```bash
python deployment/deploy.py --create
```

**Post-Deployment:**
- Agent will be accessible via Vertex AI Agent Engine API
- Web driver functionality will be disabled
- BigQuery connections remain functional
- Can integrate with existing applications via API

**Deployment Script Location:** `deployment/deploy.py`

**Note:** Modify deployment script for custom use cases, such as:
- Custom model configurations
- Different regions
- Specific resource quotas
- Custom authentication

### Troubleshooting

**BigQuery Data Not Present**

**Error:**
```
google.api_core.exceptions.NotFound: 404 Not found: Dataset ...:products_data_agent
was not found in location US
```

**Fix:**
1. Ensure you ran `sh deployment/run.sh` OR
2. Manually run: `python deployment/bq_populate_data.py`
3. Verify dataset/table in GCP Console
4. Check `.env` variables match your BigQuery setup
5. Ensure your account has BigQuery permissions

**Selenium/WebDriver Issues**

**Error:**
```
selenium.common.exceptions.SessionNotCreatedException: Message: session not created:
probably user data directory is already in use
```

**Fix:**
```bash
# Remove temporary Selenium directory
rm -rf /tmp/selenium

# Ensure only one instance is running
ps aux | grep chrome  # Kill any orphaned chrome processes
```

**Agent Flow Issues**

**Known Limitations:**
- Agent may not run reliably when websites enforce strict bot detection
- Search elements hidden by JavaScript may cause failures
- Agent might not suggest next step automatically after keyword finding

**Workarounds:**
- After keyword finding, explicitly ask: "Can you search for these keywords?"
- If agent asks for keyword again, provide it explicitly
- Complete CAPTCHA manually when prompted (first run only)
- Use alternative websites if Google Shopping blocks automation

**Permission Errors**

**Error:**
```
Permission denied accessing BigQuery dataset
```

**Fix:**
1. See `customization.md` for detailed permission setup
2. Grant your account necessary BigQuery roles:
   - BigQuery Data Viewer (minimum)
   - BigQuery User (for queries)
3. Ensure service account has dataset access if using Vertex AI

## Customization Options

### 1. Modify Comparison Target: Analyze Descriptions Instead of Titles

**Objective:** Change the agent to compare product descriptions instead of titles.

**Location:** `brand_search_optimization/sub_agents/search_results/prompt.py`

**Modification:**
Find the `<Gather Information>` section in `SEARCH_RESULT_AGENT_PROMPT` and modify it to:

```python
<Gather Information>
Instead of gathering product titles, extract product descriptions from the search results.
For each of the top 3 results:
1. Locate the product description (usually below the title)
2. Extract the full description text
3. Record it in your analysis

Return descriptions in this format:
| Rank | Description |
|------|-------------|
| 1    | Full description text... |
| 2    | Full description text... |
| 3    | Full description text... |
</Gather Information>
```

**Impact:** Agent will now analyze how competitors write descriptions and provide recommendations for description enhancement instead of title optimization.

### 2. Change Data Source: Point to Different BigQuery Table

**Objective:** Use your own product catalog instead of sample data.

**Location:** `.env` file

**Modification:**
```bash
# Update these values to match your BigQuery setup
DATASET_ID=your_custom_dataset
TABLE_ID=your_products_table
GOOGLE_CLOUD_PROJECT=your-project-id
```

**Requirements:**
- Table must have columns: `Title`, `Description`, `Attributes`, `Brand`
- Grant necessary permissions (see `customization.md`)
- Ensure brand names in table match expected input

**Advanced:** Modify `brand_search_optimization/tools/bq_connector.py` to:
- Change column names (lines 51-56)
- Add additional filters (line 58)
- Increase result limit (line 59)
- Add custom data transformations (lines 71-82)

### 3. Change Target Website: Use Your Own E-commerce Site

**Objective:** Analyze your own website instead of Google Shopping.

**Location:** `brand_search_optimization/sub_agents/search_results/prompt.py`

**Modification in Agent Prompt:**
```python
SEARCH_RESULT_AGENT_PROMPT = """
Navigate to https://your-ecommerce-site.com instead of Google Shopping.

Adjust the search interaction:
1. Use go_to_url with "https://your-ecommerce-site.com"
2. find_element_with_text to locate search box
3. enter_text_into_element with your site's search box ID
4. Adapt to your site's search result structure
...
"""
```

**Additional Code Changes:**
- Update default URL in tool calls
- Modify element selectors for your site's HTML structure
- Adjust result extraction logic for your site's layout
- Update screenshot and artifact handling if needed

**Note:** Review website's Terms of Service before automating interactions.

### 4. Expand Analysis Scope: Compare Multiple Attributes

**Objective:** Analyze titles, descriptions, AND attributes simultaneously.

**Location:** `brand_search_optimization/sub_agents/comparison/prompt.py`

**Modification:**
Add to `COMPARISON_AGENT_PROMPT`:

```python
COMPARISON_AGENT_PROMPT = """
Generate a comprehensive comparison covering:

1. Title Comparison (existing)
2. Description Comparison (new)
   - Compare description lengths
   - Identify key features mentioned
   - Note persuasive language patterns

3. Attributes Comparison (new)
   - Compare attribute completeness
   - Identify missing attributes
   - Suggest attribute additions

Provide recommendations for each category with specific examples.
"""
```

**Additional Changes:**
- Update `search_results_agent` to capture descriptions and attributes
- Modify data extraction logic to preserve all fields
- Enhance output formatting for multi-dimensional comparison

### 5. Add Custom Ranking Logic: Prioritize Keywords by Sales Impact

**Objective:** Rank keywords based on historical sales data instead of simple extraction.

**Location:** Create new file `brand_search_optimization/tools/keyword_ranker.py`

**Implementation:**
```python
def rank_keywords_by_sales(keywords: list[str], brand: str) -> list[dict]:
    """
    Rank keywords based on sales data from BigQuery.

    Args:
        keywords: List of candidate keywords
        brand: Brand name for filtering

    Returns:
        Ranked list with sales impact scores
    """
    client = bigquery.Client()

    ranked_keywords = []
    for keyword in keywords:
        query = f"""
            SELECT
                '{keyword}' as keyword,
                COUNT(*) as product_count,
                SUM(sales) as total_sales
            FROM {PROJECT}.{DATASET_ID}.sales_data
            WHERE brand LIKE '%{brand}%'
              AND (title LIKE '%{keyword}%' OR description LIKE '%{keyword}%')
            GROUP BY keyword
        """
        results = client.query(query).result()
        for row in results:
            ranked_keywords.append({
                'keyword': row.keyword,
                'product_count': row.product_count,
                'sales_impact': row.total_sales,
                'rank': 0  # Computed after all queries
            })

    # Sort by sales impact
    ranked_keywords.sort(key=lambda x: x['sales_impact'], reverse=True)
    for i, kw in enumerate(ranked_keywords):
        kw['rank'] = i + 1

    return ranked_keywords
```

**Integration:**
- Import in `keyword_finding/agent.py`
- Add as tool to keyword_finding_agent
- Update prompt to request ranked keywords

### 6. Implement Multi-Website Analysis

**Objective:** Compare search results across multiple e-commerce platforms.

**Location:** `brand_search_optimization/sub_agents/search_results/agent.py`

**Modification:**
Add a loop in the prompt to visit multiple sites:

```python
SEARCH_RESULT_AGENT_PROMPT = """
For comprehensive analysis, search across these platforms:
1. Google Shopping (https://shopping.google.com)
2. Amazon (https://amazon.com)
3. Your custom site (https://your-site.com)

For each platform:
- Navigate to the site
- Perform search
- Extract top 3 results
- Record platform name with results

Aggregate results showing:
| Platform | Rank | Title |
|----------|------|-------|
| Google   | 1    | ...   |
| Amazon   | 1    | ...   |
...
"""
```

**Create Platform Configuration:**
```python
# In constants.py
PLATFORMS = [
    {
        'name': 'Google Shopping',
        'url': 'https://shopping.google.com',
        'search_box_id': 'search-box',
    },
    {
        'name': 'Amazon',
        'url': 'https://amazon.com',
        'search_box_id': 'twotabsearchtextbox',
    },
]
```

### 7. Add Performance Metrics Tracking

**Objective:** Track and log agent performance metrics.

**Location:** Create `brand_search_optimization/tools/metrics_tracker.py`

**Implementation:**
```python
import time
import json
from datetime import datetime

class MetricsTracker:
    def __init__(self):
        self.metrics = {
            'start_time': None,
            'end_time': None,
            'keywords_generated': 0,
            'searches_performed': 0,
            'comparisons_made': 0,
            'errors_encountered': [],
        }

    def start_tracking(self):
        self.metrics['start_time'] = datetime.now().isoformat()

    def log_keywords(self, count):
        self.metrics['keywords_generated'] = count

    def log_search(self):
        self.metrics['searches_performed'] += 1

    def log_error(self, error_type, error_msg):
        self.metrics['errors_encountered'].append({
            'type': error_type,
            'message': error_msg,
            'timestamp': datetime.now().isoformat()
        })

    def finalize(self):
        self.metrics['end_time'] = datetime.now().isoformat()
        start = datetime.fromisoformat(self.metrics['start_time'])
        end = datetime.fromisoformat(self.metrics['end_time'])
        self.metrics['total_duration_seconds'] = (end - start).total_seconds()

        # Save to file
        with open('metrics.json', 'w') as f:
            json.dump(self.metrics, f, indent=2)

        return self.metrics
```

**Integration:** Add callbacks in agent.py to track lifecycle events.

---

**Additional Resources:**
- Full example interaction: `tests/example_interaction.md`
- Permission management: `customization.md`
- Architecture diagram: `brand_search_optimization.png`
- Sample data setup: `deployment/bq_data_setup.sql`
