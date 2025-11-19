# Data Engineering Agent - Technical Documentation Report

## Project Scope

The Data Engineering Agent is a comprehensive AI-powered assistant specialized in building, troubleshooting, and optimizing Dataform pipelines on Google Cloud Platform. It automates complex data engineering workflows by generating SQLx code, managing BigQuery transformations, and orchestrating ELT (Extract, Load, Transform) operations.

**Core Capabilities:**
- **Dataform Pipeline Development**: Build and modify Dataform SQLx files programmatically
- **Pipeline Troubleshooting**: Diagnose compilation errors, analyze execution logs, and fix issues automatically
- **BigQuery Integration**: Query metadata, sample data, retrieve UDFs/stored procedures, validate schemas
- **Data Transformation**: Design complex SQL transformations with dependency management
- **GCS File Operations**: Read, validate, and list files from Google Cloud Storage buckets
- **Automated Compilation**: Compile pipelines, generate DAG visualizations, and execute workflows
- **Schema Management**: Create declaration files for source tables, manage data types and dependencies

**Use Cases:**
- Automated creation of data enrichment pipelines (e.g., date/time feature engineering)
- Troubleshooting failed Dataform workflows and compilation errors
- Migrating tables between datasets with transformations
- Creating dbt-style ELT pipelines in Dataform
- Generating UDF integrations and stored procedure calls
- Data quality validation and testing pipelines
- Documentation generation for existing pipelines

**Target Users:**
- Data engineers building ETL/ELT pipelines
- Analytics engineers managing data transformations
- Data platform teams automating infrastructure
- Business analysts needing data pipeline assistance

**Agent Type:** Single Agent, Advanced Complexity, Tool-Heavy Workflow

## Technical Architecture

### Code Flow

The Data Engineering Agent follows an iterative workflow pattern:

1. **Initialization** (`data_engineering_agent/agent.py:57-108`):
   - Loads configuration from environment variables
   - Initializes BigQuery client with application default credentials
   - Configures BigQueryToolset with `WriteMode.BLOCKED` (read-only safety)
   - Creates Dataform client for workspace operations
   - Configures GCS client for bucket/file access
   - Assembles 13 tools (7 Dataform + 3 BigQuery + 4 GCS + BigQueryToolset)

2. **Iterative ELT Workflow**:
   ```
   User Request → Agent (Gemini 2.5 Pro)
                → Plan breakdown (multi-step decomposition)
                → Information Gathering:
                   ├─ compile_dataform() → Get pipeline DAG overview
                   ├─ search_files_in_dataform() → Find existing SQLX files
                   ├─ BigQueryToolset.list_tables() → Discover source tables
                   └─ sample_table_data_tool() → Preview data structure
                → Schema Analysis:
                   ├─ BigQueryToolset.get_table_schema() → Extract column definitions
                   └─ get_udf_sp_tool() → Find existing UDFs/procedures
                → Code Generation:
                   ├─ Generate SQLX transformation logic
                   ├─ Create declaration files for source tables
                   └─ write_file_to_dataform() → Upload SQLX files
                → Validation Loop:
                   ├─ compile_dataform(compile_only=True) → Check for errors
                   ├─ Fix compilation errors if any
                   ├─ Validate resolved queries
                   └─ Repeat until successful
                → Optional Execution:
                   ├─ execute_dataform_workflow() → Run pipeline
                   └─ get_dataform_execution_logs() → Monitor results
                → Return DAG link and results
   ```

3. **Example: Table Enrichment Workflow**:
   ```
   Request: "Enrich new_york_taxi_trips.tlc_green_trips_2022 with date/time features"

   Step 1: Get source table schema
   → BigQueryToolset.get_table_schema("new_york_taxi_trips", "tlc_green_trips_2022")

   Step 2: Create declaration file
   → write_file_to_dataform(
       file_content="""config {
         type: "declaration",
         database: "project-id",
         schema: "new_york_taxi_trips",
         name: "tlc_green_trips_2022"
       }""",
       file_path="definitions/sources/tlc_green_trips_2022.sqlx"
     )

   Step 3: Generate enrichment transformation
   → write_file_to_dataform(
       file_content="""config {
         type: "table",
         schema: "new_york_taxi_trips",
         name: "enriched_trips"
       }

       SELECT
         *,
         DATE(pickup_datetime) as pickup_date,
         FORMAT_DATE('%A', DATE(pickup_datetime)) as pickup_day_of_week,
         EXTRACT(HOUR FROM pickup_datetime) as pickup_hour_of_day
       FROM ${ref("tlc_green_trips_2022")}""",
       file_path="definitions/enriched_trips.sqlx"
     )

   Step 4: Compile and validate
   → compile_dataform(compile_only=True)
   → Returns DAG showing: tlc_green_trips_2022 → enriched_trips

   Step 5: Present results with repository link
   → get_dataform_repo_link() → Returns GCP console URL
   ```

### Key Components

**Agent Configuration** (`data_engineering_agent/agent.py:57-108`):
- **Model**: Gemini 2.5 Pro (configurable via `ROOT_AGENT_MODEL`)
- **Name**: `data_engineering_agent`
- **BigQuery Safety**: Write operations blocked via `WriteMode.BLOCKED`
- **System Instruction**: Expert persona in BigQuery and Dataform ELT
- **Planning Directive**: Break tasks into smaller steps iteratively
- **Validation Loop**: Compile → Fix → Repeat until success

**Dataform Tools** (`data_engineering_agent/tools/dataform_tools.py`):

1. **write_file_to_dataform(file_content: str, file_path: str)** - Uploads SQLX files to workspace
2. **delete_file_from_dataform(file_path: str)** - Removes files from workspace
3. **compile_dataform(compile_only: bool = False)** - Compiles pipeline and returns DAG overview
4. **read_file_from_dataform(file_path: str)** - Reads existing SQLX file content
5. **search_files_in_dataform(pattern: Optional[str])** - Lists files matching pattern
6. **get_dataform_execution_logs(workflow_invocation_id: str)** - Retrieves execution logs and error details
7. **get_dataform_repo_link()** - Generates GCP console URL for repository

**BigQuery Tools** (`data_engineering_agent/tools/bigquery_tools.py`):

1. **get_udf_sp_tool(dataset_id: str, routine_type: Optional[str])** - Retrieves UDFs and stored procedures with DDL
2. **sample_table_data_tool(dataset_id: str, table_id: str, sample_size: int, random_seed: Optional[int])** - Samples random rows from tables
3. **BigQueryToolset** (from ADK) - Comprehensive BigQuery operations:
   - `list_datasets()` - List available datasets
   - `list_tables(dataset_id)` - List tables in dataset
   - `get_table_schema(dataset_id, table_id)` - Get column definitions
   - `query_table(query)` - Execute SELECT queries (read-only)
   - Additional metadata operations

**GCS Tools** (`data_engineering_agent/tools/gcs_tools.py`):

1. **validate_bucket_exists_tool(bucket_name: str)** - Checks if bucket exists with metadata
2. **validate_file_exists_tool(bucket_name: str, file_path: str)** - Validates file existence
3. **list_bucket_files_tool(bucket_name: str, prefix, delimiter, max_results)** - Lists files with filtering
4. **read_gcs_file_tool(bucket_name: str, file_path: str, mode: str, num_lines: int)** - Reads file content (head/tail/full)

### Reasoning Mechanism

**Iterative Planning**:
- Agent breaks down complex data engineering tasks into sequential steps
- Each step validated before proceeding to next
- Compilation errors trigger automatic fixing attempts
- Agent makes reasonable assumptions to avoid excessive questions

**Tool Orchestration Strategy**:
1. **Discovery Phase**: Search existing files, list datasets/tables
2. **Analysis Phase**: Sample data, retrieve schemas, examine UDFs
3. **Generation Phase**: Create SQLX files with proper config blocks
4. **Validation Phase**: Compile, check for errors, fix issues
5. **Execution Phase** (optional): Run workflows, monitor logs

**Error Handling**:
- Compilation errors parsed and addressed automatically
- Failed workflows analyzed via execution logs
- BigQuery job errors retrieved and diagnosed
- Iterative fixing until successful compilation

**Safety Constraints**:
- BigQuery write operations blocked (`WriteMode.BLOCKED`)
- No destructive SQL operations (DROP commands forbidden)
- Declaration files required for all source tables
- Always validates changes before execution

### Key Libraries and Dependencies

**Core Framework:**
- `google-adk>=0.1.0` - Google Agent Development Kit
- `google-cloud-dataform>=0.4.0` - Dataform API client
- `google-cloud-bigquery>=3.11.4` - BigQuery API client
- `google-cloud-core>=2.3.3` - Core Google Cloud utilities

**Authentication and Configuration:**
- `google-auth>=2.23.0` - Google Cloud authentication
- `google-api-core>=2.15.0` - API core utilities
- `python-dotenv>=1.0.0` - Environment variable management
- `env>=0.1.0` - Environment configuration

**Data and Serialization:**
- `protobuf>=4.24.4` - Protocol buffer serialization
- `typing-extensions>=4.8.0` - Type hints and annotations

**Development and Testing:**
- `pytest>=8.3.5` - Testing framework
- `pytest-asyncio>=0.26.0` - Async testing support
- `black>=25.1.0` - Code formatting
- `google-adk[eval]>=1.0.0` - Evaluation framework

**Deployment:**
- `absl-py>=2.2.1` - Command-line flags and logging
- `poetry-core>=2.0.0` - Package building

### Project Structure

```
data_engineering_agent/
├── agent.py                           # Main agent definition
├── config.py                          # Environment configuration
├── tools/
│   ├── dataform_tools.py              # 7 Dataform workspace operations
│   ├── bigquery_tools.py              # 3 BigQuery helper tools
│   └── gcs_tools.py                   # 4 GCS file operations

tests/
└── test_agents.py                     # Integration tests

eval/
└── test_eval.py                       # Evaluation framework

deployment/
├── deploy.py                          # Vertex AI deployment script
└── test_deployment.py                 # Remote agent testing
```

### Dataform Workflow Integration

**SQLX File Structure**:
```sql
-- Declaration file (definitions/sources/table_name.sqlx)
config {
  type: "declaration",
  database: "project-id",
  schema: "dataset-id",
  name: "table-name"
}

-- Transformation file (definitions/output_table.sqlx)
config {
  type: "table",
  schema: "output-dataset",
  name: "output-table",
  tags: ["daily"],
  assertions: {
    uniqueKey: ["id"]
  }
}

SELECT
  col1,
  col2,
  UPPER(col3) as col3_upper
FROM ${ref("source_table")}
WHERE date_partition = CURRENT_DATE()
```

**Compilation and Execution Flow**:
1. Write SQLX files to workspace
2. Compile to generate DAG and validate SQL
3. Review compilation results (errors or success)
4. Execute workflow to materialize tables
5. Monitor execution via logs and job IDs

## Build & Run Instructions

### Prerequisites

1. **Python 3.9 or higher** (3.11+ recommended)
2. **Poetry** for dependency management:
   ```bash
   pip install poetry
   ```
3. **Google Cloud Account** with:
   - Vertex AI API enabled
   - Dataform API enabled
   - BigQuery API enabled
   - Cloud Storage API enabled
4. **Google Cloud SDK** (gcloud CLI):
   ```bash
   curl https://sdk.cloud.google.com | bash
   ```
5. **Dataform Repository** and **Workspace** created:
   - Create via [Dataform Console](https://console.cloud.google.com/bigquery/dataform)
   - Note repository name and workspace name

### Step 1: Clone Repository and Navigate to Project

```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/data-engineering
```

### Step 2: Install Dependencies

```bash
poetry install
```

This creates a virtual environment and installs all required packages.

### Step 3: Enable Google Cloud APIs

```bash
gcloud auth login
gcloud services enable aiplatform.googleapis.com
gcloud services enable dataform.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable storage.googleapis.com
```

### Step 4: Create Dataform Repository and Workspace

**Option A: Using GCP Console**
1. Navigate to [Dataform Console](https://console.cloud.google.com/bigquery/dataform)
2. Click "Create Repository"
3. Enter repository name (e.g., `my-data-pipelines`)
4. Select region (e.g., `us-central1`)
5. Create a workspace (e.g., `dev-workspace`)

**Option B: Using gcloud CLI**
```bash
gcloud dataform repositories create my-data-pipelines \
  --location=us-central1

gcloud dataform workspaces create dev-workspace \
  --repository=my-data-pipelines \
  --location=us-central1
```

### Step 5: Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` file:
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=1

# Model Configuration
ROOT_AGENT_MODEL=gemini-2.5-pro

# Dataform Configuration
DATAFORM_REPOSITORY_NAME=my-data-pipelines
DATAFORM_WORKSPACE_NAME=dev-workspace
```

### Step 6: Authenticate with Google Cloud

```bash
gcloud auth application-default login
```

### Step 7: Run the Agent

**From parent directory** (important for ADK to find the agent):

```bash
cd ..
adk web
```

**OR using CLI:**

```bash
cd ..
adk run data-engineering-agent
```

### Example Interaction

```
User: Enrich the new_york_taxi_trips.tlc_green_trips_2022 table by generating
date and time features from the pickup_datetime column. Use new_york_taxi_trips
dataset for the enriched table.

Agent: Of course. I will enrich the tlc_green_trips_2022 table by creating a
new table with additional date and time features from the pickup_datetime column.

First, I need to get information about the existing table to ensure I have the
correct column names and data types.

[Tool: BigQueryToolset.get_table_schema("new_york_taxi_trips", "tlc_green_trips_2022")]

Now I'll create the declaration file for the source table and the transformation file.

[Tool: write_file_to_dataform(
  file_path="definitions/sources/tlc_green_trips_2022.sqlx",
  content="config { type: 'declaration', database: 'project-id',
           schema: 'new_york_taxi_trips', name: 'tlc_green_trips_2022' }"
)]

[Tool: write_file_to_dataform(
  file_path="definitions/enriched_trips.sqlx",
  content="config { type: 'table', schema: 'new_york_taxi_trips',
           name: 'enriched_trips' }

           SELECT *,
             DATE(pickup_datetime) as pickup_date,
             FORMAT_DATE('%A', DATE(pickup_datetime)) as pickup_day_of_week,
             EXTRACT(HOUR FROM pickup_datetime) as pickup_hour_of_day
           FROM ${ref('tlc_green_trips_2022')}"
)]

I have created a new table named enriched_trips in the new_york_taxi_trips dataset.
This table includes the original data from tlc_green_trips_2022 plus:
- pickup_date: The date of the pickup
- pickup_day_of_week: The day of the week (e.g., Sunday, Monday)
- pickup_hour_of_day: The hour of the day

I will now compile the project to view the DAG.

[Tool: compile_dataform(compile_only=True)]

I have successfully compiled the Dataform project. The compilation was successful,
and here's the pipeline DAG:
[Shows DAG visualization]

You can view the repository here:
https://console.cloud.google.com/bigquery/dataform/locations/us-central1/repositories/my-data-pipelines/workspaces/dev-workspace
```

### Step 8: Run Tests

```bash
poetry install --with dev
python3 -m pytest tests
```

### Step 9: Run Evaluations

```bash
python3 -m pytest eval
```

Tests agent's ability to:
- Generate valid SQLX files
- Fix compilation errors
- Create declaration files correctly
- Handle BigQuery schema queries

### Step 10: Deploy to Vertex AI Agent Engine (Optional)

```bash
poetry install --with deployment
python3 deployment/deploy.py --create
```

Output:
```
Created remote agent: projects/123456789/locations/us-central1/reasoningEngines/987654321
```

**List deployed agents:**
```bash
python3 deployment/deploy.py --list
```

Output:
```
All remote agents:

987654321 ("data_engineering_agent")
- Create time: 2025-01-15 12:35:34.245431+00:00
- Update time: 2025-01-15 12:36:01.421432+00:00
```

**Test deployed agent:**
```bash
export USER_ID=test-user
export AGENT_ENGINE_ID=987654321
python3 deployment/test_deployment.py --resource_id=${AGENT_ENGINE_ID} --user_id=${USER_ID}
```

**Delete deployed agent:**
```bash
python3 deployment/deploy.py --delete --resource_id=${AGENT_ENGINE_ID}
```

## Customization Options

### 1. Change AI Model

Edit `.env`:
```bash
ROOT_AGENT_MODEL=gemini-2.0-flash  # Faster, lower cost
# OR
ROOT_AGENT_MODEL=gemini-2.5-pro    # Higher quality (default)
```

### 2. Add Custom Dataform Templates

Extend agent instructions in `data_engineering_agent/agent.py`:

```python
instruction=f"""
You are a BigQuery and Dataform ELT expert.

Template Library:
- Incremental models: Use config {{ type: "incremental" }} with merge strategy
- Snapshots: Use config {{ type: "snapshot" }} for SCD Type 2
- Assertions: Add uniqueness and null checks
- Pre/Post operations: Use pre_operations and post_operations for DDL

[existing instructions...]
"""
```

### 3. Enable BigQuery Write Operations

**WARNING**: Use with caution. Only enable if you trust the agent with write access.

Edit `data_engineering_agent/agent.py:46`:
```python
# Change from BLOCKED to SANDBOX or UNRESTRICTED
tool_config = BigQueryToolConfig(write_mode=WriteMode.SANDBOX)
```

### 4. Add dbt-Style Macros

Create custom tools for dbt macro equivalents:

```python
def generate_source_yaml(dataset_id: str) -> str:
    """Generate dbt-style sources.yml for Dataform"""
    # Implementation...
    pass

def generate_schema_test(table_id: str, tests: List[str]) -> str:
    """Generate assertion files for data quality tests"""
    # Implementation...
    pass
```

### 5. Integrate with CI/CD

Add to `deployment/deploy.py` for automated deployments:

```bash
# .github/workflows/deploy.yml
name: Deploy Data Engineering Agent
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: poetry install --with deployment
      - run: python3 deployment/deploy.py --create
```

### 6. Add Data Quality Validation

Extend tools with Great Expectations integration:

```python
def run_great_expectations_suite(dataset_id: str, table_id: str, suite_name: str) -> dict:
    """Run Great Expectations validation suite"""
    import great_expectations as gx
    # Implementation...
    pass
```

## Advanced Use Cases

### Incremental Pipeline Development

```
User: Create an incremental pipeline that updates daily_sales from transactions,
merging on transaction_date.

Agent: [Creates incremental SQLX with merge strategy]
```

### Schema Evolution Handling

```
User: The source table added a new column 'discount_amount'. Update the
aggregation pipeline.

Agent: [Modifies existing SQLX to include new column in transformations]
```

### Error Recovery

```
User: The pipeline failed with "Column not found: user_id"

Agent: [Analyzes execution logs, identifies missing column, fixes reference, recompiles]
```

## Performance Characteristics

**Agent Type:** Single Agent
**Complexity:** Advanced
**Model:** Gemini 2.5 Pro (configurable)
**Interaction Type:** Conversational with multi-step workflows

**Typical Execution Time**:
- Simple transformation: 20-40 seconds
- Complex multi-table pipeline: 1-3 minutes
- Error fixing iteration: 15-30 seconds
- Full compilation + execution: 2-5 minutes

**Tool Usage Pattern**:
- Average tools per request: 4-8
- Compilation attempts: 1-3 (with error fixing)
- BigQuery queries: 2-5

---

**Model:** Gemini 2.5 Pro (configurable)
**Complexity:** Advanced
**Agent Type:** Single Agent
**Python Version:** 3.9+
**License:** Apache 2.0
**Authors:** Samet Karadag (sametkaradag@google.com), Saurabh Maurya (saurabhmaurya@google.com)
**Vertical:** Data Engineering / Analytics
