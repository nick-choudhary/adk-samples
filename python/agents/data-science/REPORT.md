# Data Science Multi-Agent - Technical Documentation Report

## Project Scope

The Data Science Multi-Agent is a sophisticated AI-powered system designed for end-to-end data analysis workflows. It orchestrates specialized sub-agents to handle database querying (NL2SQL), data analysis (NL2Py), and machine learning (BQML), providing conversational access to complex data science operations across BigQuery and AlloyDB.

**Core Capabilities:**
- **Natural Language to SQL (NL2SQL)**: Translates natural language queries into SQL for BigQuery and AlloyDB
- **Data Analysis & Visualization (NL2Py)**: Generates Python code for data analysis, creates plots and charts
- **Machine Learning with BQML**: Trains and evaluates ML models using BigQuery ML
- **Cross-Database Operations**: Performs joins and analysis across BigQuery and AlloyDB
- **Code Interpreter Integration**: Executes Python code via Vertex AI Code Interpreter extension
- **Multi-Modal Output**: Returns text responses, visualizations, and data tables
- **Advanced NL2SQL with CHASE**: Supports CHASE-SQL method for improved SQL generation
- **RAG-Enhanced BQML**: Uses Vertex AI RAG Engine with BigQuery ML documentation

**Use Cases:**
- Exploratory data analysis with natural language queries
- Cross-database analytics (e.g., joining BigQuery data warehouse with AlloyDB transactional data)
- Automated forecasting and ML model training (ARIMA, Prophet, Temporal Fusion Transformer)
- Data visualization and reporting generation
- Statistical analysis and hypothesis testing
- Time series analysis and anomaly detection

**Target Users:**
- Data scientists performing ad-hoc analysis
- Business analysts querying databases conversationally
- ML engineers training and evaluating models
- Data engineers building analytics workflows
- Product managers exploring business metrics

**Agent Type:** Multi-Agent, Advanced Complexity, Conversational with Tool Execution

## Technical Architecture

### Multi-Agent Hierarchy

```
Data Science Root Agent (Orchestrator)
    ├─→ BigQuery Agent (NL2SQL for BigQuery)
    │    └─→ BQML Agent (BigQuery ML operations)
    ├─→ AlloyDB Agent (NL2SQL for AlloyDB via MCP Toolbox)
    └─→ Analytics Agent (NL2Py, data visualization, Python execution)
```

### Code Flow

1. **Initialization** (`data_science/agent.py:176-213`):
   - Loads dataset configuration from JSON file (specifies BigQuery/AlloyDB datasets)
   - Initializes database settings for each configured dataset
   - Dynamically constructs tools and sub-agents based on dataset types
   - Sets up OpenTelemetry tracing (optional Weights & Biases integration)
   - Creates root agent with temperature 0.01 for deterministic SQL generation

2. **Dataset Configuration System** (`load_dataset_config`):
   - Reads `DATASET_CONFIG_FILE` environment variable
   - Validates dataset types (BigQuery, AlloyDB)
   - Loads foreign key relationships for cross-database joins
   - Generates schema context for agent instructions

3. **Request Routing Flow**:
   ```
   User: "Show me total sales by country from the train table"

   Root Agent → Analyzes request
              → Identifies: Requires database query
              → Delegates to: call_bigquery_agent tool

   BigQuery Agent → Examines schema in context
                  → Calls: bigquery_nl2sql tool
                  → Generates: SELECT country, SUM(num_sold) as total_sales
                              FROM train GROUP BY country
                  → Executes: BigQueryToolset.execute_sql
                  → Returns: Query results to root agent

   Root Agent → Formats results as table
              → Returns to user
   ```

4. **Visualization Workflow**:
   ```
   User: "Generate a bar plot of total sales per country"

   Root Agent → Has previous query results in state
              → Delegates to: call_analytics_agent

   Analytics Agent → Calls: Code Interpreter extension
                   → Generates: Python code with matplotlib
                   → Executes: Code in sandboxed environment
                   → Returns: Base64-encoded PNG image

   Root Agent → Displays image to user
   ```

5. **BQML Training Workflow**:
   ```
   User: "Train an ARIMA model to forecast sales"

   Root Agent → Delegates to: BQML Agent (sub-agent of BigQuery Agent)

   BQML Agent → Calls: RAG retrieval (BQML documentation)
              → Confirms: Model type, time column, data column
              → Generates: CREATE MODEL SQL with ARIMA_PLUS
              → Executes: Via BigQueryToolset
              → Monitors: Training job status
              → Returns: Model evaluation metrics
   ```

### Agent Details

**1. Root Agent** (`data_science/agent.py:186-203`):
- **Model**: Gemini 2.5 Flash (configurable via `ROOT_AGENT_MODEL`)
- **Role**: Orchestrates sub-agents, determines task routing
- **Tools**:
  - `call_bigquery_agent` (if BigQuery dataset configured)
  - `call_alloydb_agent` (if AlloyDB dataset configured)
  - `call_analytics_agent` (always available)
- **Sub-agents**:
  - `bqml_agent` (if BigQuery dataset configured)
- **Context**: Injects dataset schemas and foreign key relationships into instructions

**2. BigQuery Agent** (`data_science/sub_agents/bigquery/agent.py:74-89`):
- **Model**: Configurable via `BIGQUERY_AGENT_MODEL` (defaults to root model)
- **Purpose**: NL2SQL translation for BigQuery
- **Tools**:
  - `bigquery_nl2sql` (baseline) OR `chase_db_tools.initial_bq_nl2sql` (CHASE method)
  - `BigQueryToolset` (ADK built-in, write-blocked for safety)
- **Features**:
  - Stores query results in context for analytics agent
  - Supports two NL2SQL methods: Baseline (direct Gemini) or CHASE-SQL
  - Automatic error recovery and query refinement

**3. AlloyDB Agent** (`data_science/sub_agents/alloydb/`):
- **Model**: Configurable via `ALLOYDB_AGENT_MODEL`
- **Purpose**: NL2SQL translation for AlloyDB (PostgreSQL)
- **Integration**: Uses MCP Toolbox for Databases
- **Deployment**: Requires MCP Toolbox running locally or on Cloud Run
- **Features**: PostgreSQL-specific SQL generation, cross-database join support

**4. BQML Agent** (`data_science/sub_agents/bqml/agent.py`):
- **Model**: Configurable via `BQML_AGENT_MODEL`
- **Purpose**: Train, evaluate, and predict with BigQuery ML models
- **RAG Integration**: Vertex AI RAG Engine with BigQuery ML Reference Guide
- **Supported Models**: ARIMA_PLUS, ARIMA_PLUS_XREG, Prophet, TFT, Linear Regression, etc.
- **Tools**:
  - `create_bqml_model` - Generates CREATE MODEL SQL
  - `evaluate_bqml_model` - Retrieves evaluation metrics
  - `predict_bqml_model` - Generates predictions
  - `VertexAiRagRetrieval` - Queries BQML documentation

**5. Analytics Agent** (`data_science/sub_agents/analytics/agent.py`):
- **Model**: Configurable via `ANALYTICS_AGENT_MODEL`
- **Purpose**: Python-based data analysis and visualization (NL2Py)
- **Code Interpreter**: Uses Vertex AI Extension for code execution
- **Capabilities**:
  - Data cleaning and transformation
  - Statistical analysis (correlations, distributions)
  - Visualization (matplotlib, seaborn, plotly)
  - Advanced analytics (clustering, dimensionality reduction)
- **State Access**: Can access BigQuery/AlloyDB query results from context

### Key Libraries and Dependencies

**Core Framework:**
- `google-adk>=1.14` - Google Agent Development Kit with multi-agent support
- `google-cloud-aiplatform[adk,agent-engines]>=1.93.0` - Vertex AI integration

**Database Connectivity:**
- `google-adk` BigQueryToolset - Built-in BigQuery tools
- `toolbox-core>=0.3.0` - MCP Toolbox for AlloyDB/PostgreSQL
- `pg8000>=1.31.2` - PostgreSQL adapter
- `db-dtypes>=1.4.2` - BigQuery data types

**Data Processing:**
- `pandas>=2.3.0` - Data manipulation
- `numpy>=2.3.1` - Numerical computing
- `sqlglot>=26.10.1` - SQL parsing and transformation

**Configuration and Utilities:**
- `python-dotenv>=1.0.1` - Environment management
- `pydantic>=2.11.3` - Data validation
- `immutabledict>=4.2.1` - Immutable dictionaries
- `tabulate>=0.9.0` - Table formatting
- `regex>=2024.11.6` - Regular expressions

**Observability:**
- `opentelemetry-sdk>=1.36.0` - Tracing framework
- `opentelemetry-exporter-otlp-proto-http>=1.36.0` - OTLP exporter for Weights & Biases

**Development and Testing:**
- `pytest>=8.3.5` - Testing framework
- `pytest-asyncio>=0.26.0` - Async testing
- `google-adk[eval]>=1.14` - Evaluation framework
- `black>=25.9.0` - Code formatting

### Dataset Configuration Format

**Example: `flights_dataset_config.json`**
```json
{
  "datasets": [
    {
      "type": "bigquery",
      "name": "flights_dataset",
      "description": "Flight history, ticket sales, and policies in BigQuery"
    },
    {
      "type": "alloydb",
      "name": "flights_dataset",
      "description": "Customer and booking information in AlloyDB"
    }
  ],
  "cross_dataset_relations": {
    "foreign_keys": [
      {
        "child": {
          "type": "bigquery",
          "dataset": "flights_dataset",
          "table": "ticket_sales_history",
          "column": "customer_id"
        },
        "parent": {
          "type": "alloydb",
          "dataset": "flights_dataset",
          "table": "customers",
          "column": "customer_id"
        }
      }
    ]
  }
}
```

### CHASE-SQL Integration

**What is CHASE-SQL?**: A research method from [arXiv:2410.01943](https://arxiv.org/abs/2410.01943) that improves NL2SQL accuracy through chain-of-thought reasoning.

**Configuration**: Set `NL2SQL_METHOD=CHASE` in `.env`

**Workflow**:
1. Schema decomposition and linking
2. SQL skeleton generation
3. Query refinement through error correction
4. Post-processing and validation

### Project Structure

```
data_science/
├── agent.py                           # Root orchestrator agent
├── prompts.py                         # Root agent instructions
├── tools.py                           # Tool wrappers for sub-agents
├── config.py                          # Configuration management
├── sub_agents/
│   ├── bigquery/
│   │   ├── agent.py                   # BigQuery NL2SQL agent
│   │   ├── tools.py                   # NL2SQL tools
│   │   ├── prompts.py                 # BigQuery-specific prompts
│   │   └── chase_sql/                 # CHASE-SQL implementation
│   ├── alloydb/
│   │   ├── agent.py                   # AlloyDB NL2SQL agent
│   │   └── tools.py                   # MCP Toolbox integration
│   ├── bqml/
│   │   ├── agent.py                   # BigQuery ML agent
│   │   ├── tools.py                   # BQML model tools
│   │   └── prompts.py                 # BQML-specific prompts
│   └── analytics/
│       ├── agent.py                   # Python analytics agent
│       └── prompts.py                 # Analytics prompts
├── utils/
│   ├── reference_guide_RAG.py         # BQML RAG corpus setup
│   └── create_bq_table.py             # Sample dataset loader

flights_dataset/
├── flights_dataset_config.json        # Dataset configuration
├── flight_history_table.csv           # Sample data
├── ticket_sales_history_table.csv
└── flights_dataset_alloydb.sql        # AlloyDB schema

tests/
└── test_*.py                          # Integration tests

eval/
└── test_eval.py                       # Evaluation framework

deployment/
├── deploy.py                          # Vertex AI deployment
└── test_deployment.py                 # Remote agent testing
```

## Build & Run Instructions

### Prerequisites

1. **Python 3.12 or higher**
2. **uv** package manager:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Google Cloud Account** with:
   - BigQuery API enabled
   - Vertex AI API enabled
   - AlloyDB API enabled (if using AlloyDB dataset)
4. **Google Cloud SDK**:
   ```bash
   curl https://sdk.cloud.google.com | bash
   ```
5. **Dataform Repository** (for BigQuery dataset loading)

### Step 1: Clone Repository and Navigate to Project

```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/data-science
```

### Step 2: Install Dependencies

```bash
uv sync
```

Activate the virtual environment:
```bash
source .venv/bin/activate
```

### Step 3: Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:
```bash
# Backend Configuration
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Model Selection (optional, defaults to gemini-2.5-flash)
ROOT_AGENT_MODEL=gemini-2.5-pro
BIGQUERY_AGENT_MODEL=gemini-2.5-flash
ANALYTICS_AGENT_MODEL=gemini-2.5-flash
BQML_AGENT_MODEL=gemini-2.5-pro

# NL2SQL Method: BASELINE or CHASE
NL2SQL_METHOD=BASELINE

# Dataset Configuration
DATASET_CONFIG_FILE=./flights_dataset_config.json

# BigQuery Configuration
BQ_DATA_PROJECT_ID=your-project-id
BQ_COMPUTE_PROJECT_ID=your-project-id
BQ_DATASET_ID=flights_dataset

# AlloyDB Configuration (if using AlloyDB)
ALLOYDB_DATABASE=flights_dataset
ALLOYDB_HOSTNAME=<your-alloydb-ip>
ALLOYDB_PORT=5432
ALLOYDB_USER=postgres

# MCP Toolbox (for AlloyDB)
MCP_TOOLBOX_HOST=<toolbox-url-without-https>

# BQML RAG Corpus (will be populated after setup)
BQML_RAG_CORPUS_NAME=

# Code Interpreter Extension (will be created if not provided)
CODE_INTERPRETER_EXTENSION_NAME=
```

### Step 4: Enable Google Cloud APIs

```bash
gcloud auth login
gcloud services enable aiplatform.googleapis.com \
  bigquery.googleapis.com \
  alloydb.googleapis.com \
  compute.googleapis.com \
  servicenetworking.googleapis.com
```

### Step 5A: Set Up BigQuery Dataset (Option 1: Forecasting Sticker Sales)

This dataset uses BigQuery only (simpler setup).

```bash
# Create dataset and load sample data
python3 data_science/utils/create_bq_table.py
```

Update `.env`:
```bash
BQ_DATASET_ID=forecasting_sticker_sales
DATASET_CONFIG_FILE=./forecasting_sticker_sales_dataset_config.json
```

### Step 5B: Set Up Cymbal Airlines Dataset (Option 2: BigQuery + AlloyDB)

**BigQuery Setup:**
```bash
export BQ_DATASET_ID=flights_dataset
bq mk --location $GOOGLE_CLOUD_LOCATION --dataset $BQ_DATA_PROJECT_ID:$BQ_DATASET_ID

cd flights_dataset/
bq --project_id=$BQ_DATA_PROJECT_ID --location=$GOOGLE_CLOUD_LOCATION \
  load --source_format=CSV --autodetect --skip_leading_rows=1 --replace \
  $BQ_DATASET_ID.flight_history flight_history_table.csv

bq --project_id=$BQ_DATA_PROJECT_ID --location=$GOOGLE_CLOUD_LOCATION \
  load --source_format=CSV --autodetect --skip_leading_rows=1 --replace \
  --allow_quoted_newlines \
  $BQ_DATASET_ID.cymbalair_policies cymbalair_policies_table.csv
```

**AlloyDB Setup:**
```bash
# Create AlloyDB cluster
export CLUSTER=my-alloydb-cluster
export INSTANCE=my-alloydb-instance
export REGION=us-central1
export DB_USER=postgres
export DB_PASS=secure-password

gcloud alloydb clusters create $CLUSTER \
  --password=$DB_PASS \
  --network=default \
  --region=$REGION

gcloud alloydb instances create $INSTANCE \
  --instance-type=PRIMARY \
  --cpu-count=8 \
  --region=$REGION \
  --cluster=$CLUSTER \
  --ssl-mode=ALLOW_UNENCRYPTED_AND_ENCRYPTED

# Load data
psql -h $ALLOYDB_HOSTNAME -p 5432 -U postgres -d flights_dataset \
  -f flights_dataset_alloydb.sql
```

**MCP Toolbox Setup (for AlloyDB):**
```bash
# Download toolbox binary
export OS="linux/amd64"  # or darwin/arm64, darwin/amd64, windows/amd64
curl -O https://storage.googleapis.com/genai-toolbox/v0.12.0/$OS/toolbox
chmod +x toolbox

# Configure environment
cp toolbox_env-example.sh toolbox_env.sh
# Edit toolbox_env.sh with your settings
source ./toolbox_env.sh

# Run toolbox server
./toolbox --tools-file "toolbox-alloydb-local.yaml"
```

### Step 6: Set Up BQML RAG Corpus

```bash
python3 data_science/utils/reference_guide_RAG.py
```

This creates a RAG corpus with BigQuery ML documentation and updates `.env` with the corpus name.

### Step 7: Configure Code Interpreter Extension

The agent will auto-create a Code Interpreter extension if not provided. Check logs for the extension ID and add to `.env`:

```bash
CODE_INTERPRETER_EXTENSION_NAME=projects/PROJECT_ID/locations/LOCATION/extensions/EXTENSION_ID
```

### Step 8: Run the Agent

**Web UI (Recommended):**
```bash
uv run adk web
```

Select "data_science" from the dropdown.

**CLI:**
```bash
uv run adk run data_science
```

### Example Interactions

**Example 1: Data Exploration**
```
User: Hi, what data do you have access to?

Agent: I have access to two tables: train and test. Both contain sticker sales
data with columns: id, date, country, store, product, and num_sold.

User: How many stores are there per country?

Agent: [Executes SQL query]
Result: Each of the 6 countries (Canada, Finland, Italy, Kenya, Norway, Singapore)
has 3 distinct stores.

User: Generate a bar plot of total sales by country

Agent: [Generates visualization via Code Interpreter]
[Displays bar chart image]
```

**Example 2: Machine Learning**
```
User: What forecasting models can I train in BQML?

Agent: You can train ARIMA_PLUS, ARIMA_PLUS_XREG, and Temporal Fusion Transformer
(TFT) models. Would you like to proceed?

User: Yes, train an ARIMA model on num_sold

Agent: I'll create an ARIMA_PLUS model. Confirming:
- Time column: date
- Data column: num_sold
- ID columns: country, store, product

[Generates and executes CREATE MODEL SQL]
[Returns evaluation metrics: MAE, RMSE, R²]
```

### Step 9: Run Tests and Evaluations

```bash
uv sync --dev
uv run pytest tests      # Integration tests
uv run pytest eval       # Evaluation tests
```

### Step 10: Deploy to Vertex AI Agent Engine

**Build wheel package:**
```bash
uv build --wheel --out-dir deployment
```

**Deploy MCP Toolbox (if using AlloyDB):**
```bash
# Follow Cloud Run deployment instructions in README
gcloud run deploy toolbox \
  --image us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest \
  --service-account toolbox-identity \
  --region us-central1 \
  --set-secrets "/app/tools.yaml=tools:latest,ALLOYDB_POSTGRES_PASSWORD=ALLOYDB_POSTGRES_PASSWORD:latest" \
  --env-vars-file="toolbox.env"
```

**Deploy agent:**
```bash
cd deployment/
python3 deploy.py --create
```

**Test deployment:**
```bash
export RESOURCE_ID=<agent-engine-id>
export USER_ID=test-user
python3 test_deployment.py --resource_id=$RESOURCE_ID --user_id=$USER_ID
```

## Customization Options

### 1. Add Custom Dataset

Create a dataset configuration JSON:
```json
{
  "datasets": [
    {
      "type": "bigquery",
      "name": "my_custom_dataset",
      "description": "Description of dataset tables and purpose"
    }
  ],
  "cross_dataset_relations": {
    "foreign_keys": []
  }
}
```

### 2. Change NL2SQL Method

```bash
# Use CHASE-SQL for improved accuracy
NL2SQL_METHOD=CHASE
```

### 3. Add Custom Analytics Tools

Extend `data_science/sub_agents/analytics/agent.py`:
```python
from custom_tools import advanced_statistics

analytics_agent = LlmAgent(
    # ... existing config ...
    tools=[code_interpreter, advanced_statistics]
)
```

### 4. Integrate with Weights & Biases

Configure W&B tracing in `.env`:
```bash
WANDB_PROJECT_ID=your-wandb-project
WANDB_API_KEY=your-api-key
```

## Performance Characteristics

**Agent Type:** Multi-Agent (4 sub-agents)
**Complexity:** Advanced
**Models:** Gemini 2.5 Flash/Pro (configurable per agent)
**Interaction Type:** Conversational with tool execution

**Typical Execution Time**:
- Simple SQL query: 5-10 seconds
- Complex join query: 10-20 seconds
- Data visualization: 15-30 seconds
- BQML model training: 2-10 minutes
- Full analysis workflow: 30-120 seconds

---

**Model:** Gemini 2.5 Flash/Pro (configurable)
**Complexity:** Advanced
**Agent Type:** Multi-Agent (Root + 4 Sub-Agents)
**Python Version:** 3.12+
**License:** Apache 2.0
**Vertical:** Data Science / Analytics
**Video Walkthrough:** [YouTube](https://www.youtube.com/watch?v=efcUXoMX818)
