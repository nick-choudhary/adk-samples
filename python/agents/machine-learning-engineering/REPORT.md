# Machine Learning Engineering (MLE-STAR) - Technical Documentation Report

## Project Scope

### High-Level Summary
MLE-STAR (Machine Learning Engineering via Search and Targeted Refinement) is a state-of-the-art autonomous machine learning engineering agent that automates the complete pipeline of training competition-level ML models. The agent leverages web search to discover cutting-edge models, performs targeted code block refinement through ablation studies, and introduces novel ensemble strategies to achieve medal-winning performance on Kaggle competitions. Based on Google Cloud AI Research paper ([arxiv.org/abs/2506.15692](https://www.arxiv.org/abs/2506.15692)), it represents a significant advancement in automated machine learning engineering.

### Core Capabilities
- **Automated Model Discovery**: Uses web search to retrieve state-of-the-art ML models and implementation examples
- **Intelligent Code Generation**: Synthesizes and merges multiple model candidates into optimal solutions
- **Iterative Refinement**: Performs ablation studies to identify and improve high-impact code blocks
- **Novel Ensemble Methods**: Proposes and refines ensemble strategies that outperform individual models
- **Robustness Mechanisms**: Includes automatic debugging, data leakage detection, and data usage verification
- **Competition-Grade Performance**: Achieves medals in 63.6% of MLE-bench-Lite competitions with Gemini-2.5-Pro

### Primary Use Cases
- **Kaggle Competition Automation**: End-to-end solution development for ML competitions
- **Rapid Prototyping**: Quick generation of baseline models for new datasets
- **ML Pipeline Optimization**: Systematic improvement of existing ML workflows
- **Educational Tool**: Learning best practices from generated solutions
- **Research Acceleration**: Automated experimentation with different modeling approaches
- **Production ML Development**: Initial model development for business problems

### Target Users
- **Data Scientists**: Accelerate model development and experimentation
- **ML Engineers**: Automate repetitive engineering tasks and optimize pipelines
- **Kaggle Competitors**: Achieve competitive performance with automated workflows
- **ML Researchers**: Rapid prototyping and baseline generation
- **Business Analysts**: Access ML capabilities without deep technical expertise
- **Academic Researchers**: Teaching tool and research accelerator

### Key Innovations/Differentiators
- **Search-Augmented Learning**: Retrieves cutting-edge models from web rather than relying on pre-trained knowledge
- **Targeted Refinement**: Ablation-based approach identifies and improves critical code blocks systematically
- **Agent-Proposed Ensembles**: Novel ensembling where the agent designs combination strategies
- **Multi-Solution Parallel Processing**: Generates multiple solutions simultaneously for diversity
- **Data Leakage Prevention**: Built-in checker prevents common ML pitfalls
- **State-of-the-Art Performance**: 63.6% medal rate on MLE-bench-Lite (vs. lower rates for alternatives)

## Technical Architecture

### Multi-Agent Hierarchy

```
┌──────────────────────────────────────────────────────────────────────┐
│                    mle_frontdoor_agent (Root)                         │
│              Handles user interaction and task routing                │
└─────────────────────────────┬────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    mle_pipeline_agent                                 │
│              Sequential execution of ML workflow                      │
└──┬───────────────────┬────────────────┬────────────────┬─────────────┘
   │                   │                │                │
   ▼                   ▼                ▼                ▼
┌─────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────────┐
│Initialization│  │ Refinement   │  │ Ensemble │  │ Submission   │
│   Agent      │  │    Agent     │  │  Agent   │  │   Agent      │
└──────┬───────┘  └──────┬───────┘  └────┬─────┘  └──────┬───────┘
       │                 │                │               │
       │                 │                │               │
  ┌────┴─────┐      ┌────┴────┐      ┌───┴────┐     ┌───┴────┐
  │          │      │         │      │        │     │        │
  ▼          ▼      ▼         ▼      ▼        ▼     ▼        ▼
┌──────┐  ┌──────┐ ┌────┐ ┌─────┐ ┌────┐ ┌─────┐ ┌───┐ ┌─────┐
│Task  │  │Model │ │Abl-│ │Plan │ │Init│ │Refine│ │Run│ │Debug│
│Summ- │  │Retr- │ │ation│ │Gen │ │Plan│ │ Plan│ │&  │ │     │
│arize │  │ieval │ │Agent│ │Agent│ │Impl│ │Impl │ │Debug│    │
└──────┘  └──┬───┘ └────┘ └─────┘ └────┘ └─────┘ └───┘ └─────┘
             │
        ┌────┴─────┐
        │          │
   ┌────┴───┐ ┌───┴────┐
   │Model   │ │Model   │
   │Eval 1  │ │Eval 2  │
   └────────┘ └────────┘

Key Agent Types:
- SequentialAgent: Executes sub-agents in order
- ParallelAgent: Executes sub-agents concurrently
- LoopAgent: Repeats sub-agents for iterative refinement
- Agent: Individual LLM-powered agent with specific task
```

### Code Flow Explanation

**1. Entry Point** (`machine_learning_engineering/agent.py`, lines 43-50)
   - **Root Agent**: `mle_frontdoor_agent` serves as the main interface
   - Model: Configurable via `ROOT_AGENT_MODEL` environment variable (line 44)
   - Global instruction defines system-level behavior (line 47)
   - Single sub-agent: `mle_pipeline_agent` (line 48)
   - Low temperature (0.01) for consistent behavior (line 49)

**2. Pipeline Agent** (`machine_learning_engineering/agent.py`, lines 30-40)
   - **Type**: `SequentialAgent` - executes sub-agents in strict order
   - **Sub-agents sequence** (lines 33-36):
     1. `initialization_agent` - Generate initial solutions
     2. `refinement_agent` - Iteratively improve solutions
     3. `ensemble_agent` - Combine multiple solutions
     4. `submission_agent` - Prepare final submission
   - **State persistence**: `save_state` callback after each agent (lines 18-27, line 39)
     - Saves complete state to `workspace_dir/{task_name}/final_state.json`

**3. Initialization Agent** (`sub_agents/initialization/agent.py`, lines 436-444)
   - **Purpose**: Set up environment and generate initial ML solutions
   - **Pre-processing** (lines 226-243):
     - `prepare_task`: Loads configuration from `config.CONFIG` (line 230)
     - Sets random seed for reproducibility (line 235)
     - Loads task description from file (lines 237-242)

   - **Sub-agents** (lines 439-442):
     - `task_summarization_agent`: Creates concise task summary (lines 340-350)
     - `init_parallel_agent`: Generates multiple solutions in parallel (lines 431-435)

   - **Parallel Solution Generation** (lines 351-430):
     - Creates `num_solutions` agents (default: 2) that run concurrently
     - Each solution agent follows this workflow:
       1. **Model Retrieval Loop** (lines 353-371):
          - Uses Google Search to find state-of-the-art models
          - Retries up to `max_retry` times (default: 10)
          - Extracts model name and example code (lines 23-55)

       2. **Model Evaluation** (lines 375-383):
          - For each of `num_model_candidates` (default: 2):
          - Generates code using retrieved model (lines 278-292)
          - Executes and evaluates with `get_run_and_debug_agent`
          - Checks for data leakage if enabled (lines 92-98)

       3. **Ranking** (lines 384-388, 134-168):
          - Ranks solutions by validation score
          - Selects best performing solution as base
          - Saves to `workspace_dir/{task_name}/{task_id}/train0_0.py`

       4. **Code Merging** (lines 390-408):
          - Iteratively merges other candidates with base solution
          - Uses `merger_agent` to integrate beneficial components
          - Updates base if merge improves performance (lines 193-223)

       5. **Selection** (lines 409-414, 171-190):
          - Selects final best solution from all merged candidates
          - Saves as `train0.py`

       6. **Data Usage Check** (lines 415-423):
          - Optional verification that all provided data is utilized
          - Prevents missed features or data files

**4. Refinement Agent** (`sub_agents/refinement/agent.py`, lines 458-463)
   - **Purpose**: Iteratively improve solutions through targeted refinement
   - **Type**: `ParallelAgent` - refines all solutions concurrently
   - **Creates refinement loop for each solution** (lines 321-456):

   - **Outer Loop** (lines 450-456):
     - Runs for `outer_loop_round` iterations (default: 1)
     - Each iteration targets different code block

   - **Ablation Study** (lines 322-364):
     - **Ablation Agent** (lines 322-336):
       - Generates code with components removed/modified
       - First iteration: No previous ablations (lines 132-135)
       - Later iterations: Considers previous results (lines 128-131)
       - Temperature: 1.0 for creative exploration (line 333)

     - **Data Leakage Check** (lines 338-346):
       - Optional validation of ablation code
       - Ensures no improper data access during preprocessing

     - **Debug Loop** (lines 352-364):
       - Retries up to `max_rollback_round` times (default: 2)
       - Fixes errors in ablation code

     - **Summary** (lines 365-375):
       - Analyzes ablation results (lines 115-136)
       - Identifies high-impact code blocks
       - Temperature: 0.0 for factual summary (line 371)

   - **Initial Plan Generation** (lines 376-396):
     - **Plan Agent** (lines 376-387):
       - Extracts most impactful code block from ablation
       - Proposes initial improvement plan
       - Returns JSON with plan and code block (lines 285-304)

     - **Plan Loop** (lines 388-396):
       - Retries until valid code block extracted
       - Max `max_retry` iterations (default: 10)

   - **Plan Implementation** (lines 397-403):
     - Implements initial plan
     - Executes and evaluates result
     - Uses run-and-debug pattern

   - **Inner Loop Refinement** (lines 404-437):
     - **Refine-Implement Cycle** (lines 422-430):
       - `plan_refine_agent`: Improves plan based on previous results
       - Analyzes top `num_top_plans` (default: 2) plans
       - Uses execution time and score for ranking (lines 176-207)
       - `plan_implement_agent`: Executes refined plan

     - **Loop** (lines 431-437):
       - Runs for `inner_loop_round` iterations (default: 1)
       - Each iteration refines the plan further

   - **State Updates** (lines 30-93):
     - After outer loop: Select best improvement (lines 30-93)
     - If improvement found: Update solution
     - If no improvement: Keep previous solution
     - Save to `workspace_dir/{task_name}/{task_id}/train{step}.py`

**5. Ensemble Agent** (`sub_agents/ensemble/agent.py`, lines 242-252)
   - **Purpose**: Combine multiple refined solutions for superior performance
   - **Workspace Setup** (lines 158-186):
     - Creates ensemble directory structure
     - Copies input data for isolated execution

   - **Sub-agents** (lines 245-249):
     - `init_ensemble_plan_agent`: Proposes ensemble strategy
     - `init_ensemble_plan_implement_agent`: Implements initial plan
     - `ensemble_plan_refine_and_implement_loop_agent`: Iterative improvement

   - **Initial Ensemble Plan** (lines 189-200):
     - Gathers all refined solutions (lines 80-92)
     - Agent proposes combination strategy
     - Examples: averaging, stacking, voting
     - Temperature: 1.0 for creative strategies (line 197)

   - **Plan Implementation** (lines 201-207):
     - Implements proposed ensemble method
     - Executes and evaluates combined model
     - Uses run-and-debug pattern

   - **Refinement Loop** (lines 208-241):
     - **Refine Agent** (lines 208-218):
       - Analyzes top `num_top_plans` ensemble strategies
       - Ranks by score: lower better if `lower=True` (lines 100-134)
       - Proposes improved combination method

     - **Implement Agent** (lines 219-225):
       - Executes refined ensemble strategy
       - Evaluates performance

     - **Loop** (lines 226-241):
       - Runs for `ensemble_loop_round` iterations (default: 1)
       - Updates ensemble plan iteratively

**6. Submission Agent** (`sub_agents/submission/agent.py`, lines 71-77)
   - **Purpose**: Prepare final submission file with best solution
   - **Solution Selection** (lines 32-68):
     - Compares all refined solutions (lines 42-53)
     - Compares all ensemble solutions (lines 54-64)
     - Selects overall best by score

   - **Submission Code Generation**:
     - Adds code to create submission file
     - Ensures proper format for competition
     - Uses run-and-debug pattern (lines 71-77)

**7. Debugging Infrastructure** (`shared_libraries/debug_util.py`)
   - **Run-and-Debug Agent Pattern**:
     - Executes Python code
     - Captures stdout, stderr, return code
     - Evaluates performance on validation set
     - Records execution time
     - On error: Triggers debugging loop

   - **Debugging Loop**:
     - Analyzes error messages
     - Proposes fix
     - Re-executes
     - Repeats up to `max_debug_round` times (default: 5)

### Agent Definitions with Roles and Responsibilities

**mle_frontdoor_agent (Root Agent)**
- **Role**: User interface and task coordinator
- **Responsibilities**:
  - Answer general questions about capabilities
  - Load and describe tasks
  - Trigger pipeline execution when requested
  - Maintain conversation context
- **Key Behavior**: Only executes pipeline when explicitly asked

**mle_pipeline_agent (Sequential Agent)**
- **Role**: Workflow orchestrator
- **Responsibilities**:
  - Execute initialization, refinement, ensemble, submission in sequence
  - Ensure each stage completes before next begins
  - Save state after each major stage
  - Manage overall execution flow

**initialization_agent (Sequential Agent)**
- **Role**: Initial solution generator
- **Responsibilities**:
  - Prepare workspace and load task data
  - Summarize task requirements
  - Search for and retrieve relevant ML models
  - Generate multiple candidate solutions
  - Evaluate and merge solutions
  - Select best initial solution

**task_summarization_agent**
- **Role**: Task analyzer
- **Responsibilities**:
  - Read full task description
  - Extract key information (problem type, metrics, constraints)
  - Create concise summary for other agents
  - Store summary in shared state

**model_retriever_agent (Loop Agent)**
- **Role**: Model discovery specialist
- **Responsibilities**:
  - Use Google Search to find state-of-the-art models
  - Extract model names and example implementations
  - Return structured model information
  - Retry on failure

**model_eval_agent (Loop Agent with Debug)**
- **Role**: Code generator and evaluator
- **Responsibilities**:
  - Generate ML code using retrieved model examples
  - Execute code on task data
  - Evaluate performance on validation set
  - Debug errors until code succeeds

**merger_agent (Loop Agent with Debug)**
- **Role**: Code integration specialist
- **Responsibilities**:
  - Combine two solutions into one
  - Preserve best components from each
  - Ensure integrated code executes correctly
  - Maintain or improve performance

**refinement_agent (Parallel Agent)**
- **Role**: Solution optimizer
- **Responsibilities**:
  - Improve all solutions simultaneously
  - Coordinate ablation studies
  - Manage plan generation and implementation
  - Track improvements over iterations

**ablation_agent**
- **Role**: Component analyzer
- **Responsibilities**:
  - Generate code with components removed/ablated
  - Execute ablation studies systematically
  - Identify high-impact components
  - Provide data for prioritization

**ablation_summary_agent**
- **Role**: Analysis synthesizer
- **Responsibilities**:
  - Analyze ablation results
  - Identify most impactful code blocks
  - Rank components by importance
  - Summarize findings clearly

**init_plan_agent (Loop Agent)**
- **Role**: Improvement strategist
- **Responsibilities**:
  - Extract most impactful code block from ablation
  - Propose specific improvement plan
  - Ensure plan targets right component
  - Retry until valid plan generated

**plan_refine_agent**
- **Role**: Plan optimizer
- **Responsibilities**:
  - Analyze results of previous plans
  - Identify successful strategies
  - Propose improved refinement approach
  - Learn from execution time and scores

**plan_implement_agent (Loop Agent with Debug)**
- **Role**: Plan executor
- **Responsibilities**:
  - Implement proposed refinement plan
  - Execute and evaluate result
  - Debug implementation errors
  - Record performance metrics

**ensemble_agent (Sequential Agent)**
- **Role**: Model combiner
- **Responsibilities**:
  - Create workspace for ensemble experiments
  - Propose ensemble strategies
  - Implement and evaluate ensembles
  - Iteratively improve combination methods

**init_ensemble_plan_agent**
- **Role**: Ensemble strategist
- **Responsibilities**:
  - Analyze all refined solutions
  - Propose initial combination strategy
  - Consider diversity and complementarity
  - Suggest concrete implementation approach

**ensemble_plan_refine_agent**
- **Role**: Ensemble optimizer
- **Responsibilities**:
  - Review previous ensemble strategies
  - Identify successful combination patterns
  - Propose improved ensemble methods
  - Learn from performance metrics

**ensemble_plan_implement_agent (Loop Agent with Debug)**
- **Role**: Ensemble executor
- **Responsibilities**:
  - Implement proposed ensemble strategy
  - Execute combined model
  - Evaluate ensemble performance
  - Debug implementation issues

**submission_agent (Loop Agent with Debug)**
- **Role**: Final deliverable creator
- **Responsibilities**:
  - Select best overall solution (refined or ensemble)
  - Add submission file generation code
  - Ensure proper output format
  - Verify submission file created successfully

### Key Libraries and Dependencies

From `pyproject.toml` (lines 9-25):

**Core ML & ADK:**
- **google-adk (>=1.5.0)**: Agent Development Kit framework
- **google-genai (>=1.9.0)**: Google's Generative AI SDK
- **google-cloud-aiplatform (>=1.93)**: Vertex AI integration with agent-engines extras

**ML Libraries:**
- **numpy (>=2.2.3)**: Numerical computing foundation
- **pandas (>=2.3.1)**: Data manipulation and analysis
- **scikit-learn (>=1.7.1)**: Classical ML algorithms and preprocessing
- **torch (>=2.7.1)**: PyTorch for deep learning (CPU version from pytorch_cpu source)

**Utilities:**
- **pydantic (>=2.10.6)**: Data validation and settings management
- **python-dotenv (>=1.0.1)**: Environment variable management

**Development & Evaluation** (lines 29-45):
- **google-adk[eval] (>=1.5.0)**: Evaluation framework
- **google-cloud-aiplatform[evaluation] (>=1.93)**: Evaluation utilities
- **pytest (>=8.3.5)**: Testing framework
- **pytest-asyncio (>=0.26.0)**: Async test support
- **black (>=25.1.0)**: Code formatting

**Deployment** (lines 50-51):
- **absl-py (>=2.2.1)**: Application utilities for deployment scripts

**Custom Package Source** (lines 56-59):
- PyTorch CPU builds from `https://download.pytorch.org/whl/cpu`

### Tools and Integrations

**Google Search Tool** (`sub_agents/initialization/agent.py`, line 358)
- **Purpose**: Retrieve state-of-the-art ML models and implementations
- **Usage**: Model retrieval agent searches for relevant models
- **Source**: `google.adk.tools.google_search_tool.google_search`
- **Benefit**: Accesses latest ML techniques beyond training data cutoff

**Code Execution Tool** (Implicit in debug_util)
- **Purpose**: Execute Python code and capture results
- **Features**:
  - Runs in isolated workspace directories
  - Captures stdout, stderr, return codes
  - Times execution duration
  - Evaluates on validation data
  - Returns structured results

**Data Leakage Checker** (`shared_libraries/check_leakage_util.py`)
- **Purpose**: Prevent common ML mistakes
- **Checks**:
  - No test data access during training
  - Proper train/validation split
  - No future data leakage in time series
- **Configurable**: `use_data_leakage_checker` in config (line 30)

**Data Usage Checker** (Initialization agent)
- **Purpose**: Ensure all provided data is utilized
- **Checks**:
  - All data files are loaded
  - All features are considered
  - No missed information sources
- **Configurable**: `use_data_usage_checker` in config (line 31)

**File System Operations** (`shared_libraries/common_util.py`)
- **Workspace management**: Create isolated directories for each solution
- **Data copying**: Duplicate task data to workspace
- **State persistence**: Save intermediate results and final state

### Reasoning Mechanisms

**1. Search-Augmented Model Discovery**
- Agent queries Google Search for state-of-the-art models
- Extracts model architectures and example code
- Adapts examples to current task
- Benefits from latest ML research automatically

**2. Ablation-Based Prioritization**
- Systematically removes/modifies code components
- Measures impact on performance
- Identifies high-impact blocks for refinement
- Focuses effort on most promising improvements

**3. Iterative Plan Refinement**
- Initial plan based on ablation results
- Execution feedback informs next plan
- Tracks performance and execution time
- Learns successful strategies over iterations

**4. Multi-Solution Diversity**
- Generates multiple independent solutions in parallel
- Explores different model architectures
- Merges complementary approaches
- Maintains solution diversity for ensembling

**5. Agent-Proposed Ensembles**
- Agent analyzes solution characteristics
- Proposes custom combination strategies
- Iteratively improves ensemble methods
- Goes beyond simple averaging/voting

**6. Automatic Error Recovery**
- Debug loops catch and fix code errors
- Multiple retry mechanisms at different levels
- Rollback to previous working state if needed
- Maintains progress even with failures

**7. State-Based Learning**
- Shared state across all agents
- Previous ablations inform future targeting
- Performance history guides refinement
- Cumulative knowledge throughout pipeline

## Build & Run Instructions

### Prerequisites

**Required Software:**
- **Python 3.12+**: Latest Python version for async and typing features
- **Poetry**: Dependency management
  ```bash
  pip install poetry
  ```
- **Git**: Version control
  - Download from [git-scm.com](https://git-scm.com/)
  - Follow [installation guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

**Required Accounts:**
- **Google Cloud Account**: For Vertex AI and API access
- **Google Cloud Project**: Active GCP project with billing
- **Google Cloud CLI**: For authentication
  - Install: [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)

**Recommended Hardware:**
- **CPU**: 4+ cores for parallel solution generation
- **RAM**: 8GB+ for multiple Python processes
- **Storage**: 10GB+ for workspace and model files

### Step-by-Step Installation

**1. Clone Repository**
```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/machine-learning-engineering
```

**2. Install Poetry and Dependencies**
```bash
# Install Poetry if not already installed
pip install poetry

# For Linux users: If you get keyring errors
poetry config keyring.enabled false

# Install all dependencies
poetry install

# Verify installation
poetry env list
# Should show: machine-learning-engineering-Gb54hHID-py3.12 (Activated)
```

**Alternative if `poetry install` fails:**
```bash
python -m poetry install
```

**3. Activate Poetry Shell**
```bash
poetry shell
```

**Alternative activation method:**
```bash
source $(poetry env info --path)/bin/activate
```

**4. Configure Environment Variables**

Create `.env` file from template:
```bash
cp .env.example .env
```

Edit `.env` with your values:
```bash
# Model Backend: 1 for Vertex AI, 0 for ML Dev
GOOGLE_GENAI_USE_VERTEXAI=1

# Vertex AI Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1  # or your preferred region

# Model Selection
ROOT_AGENT_MODEL=gemini-2.5-flash

# For deployment only
GOOGLE_CLOUD_STORAGE_BUCKET=your-storage-bucket
```

**5. Authenticate with Google Cloud**
```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT
```

### Configuration

**Environment Variables** (`.env.example`, lines 1-17):
- `GOOGLE_GENAI_USE_VERTEXAI`: Choose backend (1=Vertex AI, 0=ML Dev)
- `GOOGLE_API_KEY`: API key for ML Dev backend (if using ML Dev)
- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID (required for Vertex)
- `GOOGLE_CLOUD_LOCATION`: GCP region (e.g., us-central1)
- `ROOT_AGENT_MODEL`: LLM model (default: gemini-2.5-flash)
- `GOOGLE_CLOUD_STORAGE_BUCKET`: GCS bucket for deployment (optional)

**Configuration Parameters** (`shared_libraries/config.py`, lines 8-32):

**Task Configuration:**
- `data_dir` (line 10): Directory containing task data (default: "./machine_learning_engineering/tasks/")
- `task_name` (line 11): Task to execute (default: "california-housing-prices")
- `task_type` (line 12): Problem type (default: "Tabular Regression")
- `lower` (line 13): True if lower metric is better (default: True)
- `workspace_dir` (line 14): Output directory (default: "./machine_learning_engineering/workspace/")

**Model Configuration:**
- `agent_model` (line 15): LLM model from env or default
- `seed` (line 19): Random seed for reproducibility (default: 42)
- `exec_timeout` (line 20): Max execution time in seconds (default: 600)

**Solution Generation:**
- `num_solutions` (line 21): Parallel solutions to generate (default: 2)
- `num_model_candidates` (line 22): Models to retrieve per solution (default: 2)

**Retry & Debug:**
- `max_retry` (line 23): Max retries for failed operations (default: 10)
- `max_debug_round` (line 24): Max debugging iterations (default: 5)
- `max_rollback_round` (line 25): Max rollbacks for ablation (default: 2)

**Refinement Loops:**
- `inner_loop_round` (line 26): Plan refinement iterations (default: 1)
- `outer_loop_round` (line 27): Ablation cycles (default: 1)
- `ensemble_loop_round` (line 28): Ensemble refinement iterations (default: 1)
- `num_top_plans` (line 29): Top plans to consider for refinement (default: 2)

**Safety Features:**
- `use_data_leakage_checker` (line 30): Enable data leakage detection (default: False)
- `use_data_usage_checker` (line 31): Enable data usage verification (default: False)

### Running the Agent

**Prepare Your Task**

1. **Create task directory:**
   ```bash
   mkdir -p machine_learning_engineering/tasks/your-task-name
   ```

2. **Add task description:**
   ```bash
   # Create task_description.txt
   cat > machine_learning_engineering/tasks/your-task-name/task_description.txt << EOF
   Task: Predict housing prices in California

   Problem Type: Regression
   Metric: Root Mean Squared Error (lower is better)

   Data Files:
   - train.csv: Training data with features and target
   - test.csv: Test data for predictions

   Features:
   - longitude, latitude: Location coordinates
   - housing_median_age: Median age of houses
   - total_rooms, total_bedrooms: Room counts
   - population, households: Demographics
   - median_income: Median household income
   - ocean_proximity: Categorical location feature

   Target:
   - median_house_value: Median house value (to predict)

   Submission Format:
   CSV file with columns: Id, Predicted
   EOF
   ```

3. **Add data files:**
   ```bash
   # Copy your train.csv and test.csv
   cp /path/to/train.csv machine_learning_engineering/tasks/your-task-name/
   cp /path/to/test.csv machine_learning_engineering/tasks/your-task-name/
   ```

4. **Update config** (if needed):
   Edit `machine_learning_engineering/shared_libraries/config.py`:
   ```python
   task_name: str = "your-task-name"
   task_type: str = "Tabular Regression"  # or "Tabular Classification"
   lower: bool = True  # True if lower metric is better
   ```

**Run via ADK CLI**
```bash
adk run machine_learning_engineering
```

**Run via Poetry**
```bash
poetry run adk run machine_learning_engineering
```

**Run via Web UI**
```bash
adk web
# Navigate to printed URL (e.g., http://localhost:8080)
# Select "machine_learning_engineering" from dropdown
```

### Example Interactions

**Example Session:**

**User:**
```
who are you?
```

**Agent (mle_frontdoor_agent):**
```
I am a machine learning engineer agent.
```

**User:**
```
what can you do?
```

**Agent:**
```
I am a machine learning engineer. My primary role is to engineer solutions
for machine learning tasks, such as the California Housing Task. I can also
describe the task if you'd like. I work by executing a sequence of sub-agents
to solve the machine learning engineering task.
```

**User:**
```
describe the task that you have
```

**Agent:**
```
The task I have is the California Housing Task. This task involves predicting
the median house value in California districts, given various features about
those districts. It's a regression problem where the goal is to build a model
that can accurately estimate house prices based on factors like population,
median income, and housing age within a district.
```

**User:**
```
execute the task
```

**Agent:**
```
[initialization_agent starts]
Searching for state-of-the-art regression models...

[model_retriever_agent_1 finds: XGBoost, RandomForest, GradientBoosting]
[model_retriever_agent_2 finds: LightGBM, CatBoost, Neural Networks]

Generating code for XGBoost model...
[Executes code, evaluates: RMSE = 0.45]

Generating code for RandomForest model...
[Executes code, evaluates: RMSE = 0.52]

Merging solutions...
[Integrated code: RMSE = 0.43]

Initial solution complete: RMSE = 0.43
Saved to: workspace/california-housing-prices/1/train0.py

[refinement_agent starts]
Performing ablation study on current solution...

Ablation results:
- Removing feature engineering: RMSE increases to 0.51 (+0.08)
- Removing hyperparameter tuning: RMSE increases to 0.48 (+0.05)
- Removing data preprocessing: RMSE increases to 0.65 (+0.22)

Most impactful component: Data preprocessing

Generating improvement plan for data preprocessing...
Plan: Add polynomial features and interaction terms

Implementing plan...
[Executes improved code: RMSE = 0.41]

Refinement complete: RMSE = 0.41 (improved by 0.02)

[ensemble_agent starts]
Proposing ensemble strategy...
Strategy: Weighted average of XGBoost and LightGBM with 0.6/0.4 weights

Implementing ensemble...
[Executes ensemble code: RMSE = 0.39]

Refining ensemble weights...
[Optimizes to 0.7/0.3: RMSE = 0.38]

Ensemble complete: RMSE = 0.38 (improved by 0.03)

[submission_agent starts]
Selecting best solution: Ensemble (RMSE = 0.38)

Adding submission file generation code...
[Executes final code]

Submission file saved successfully to:
workspace/california-housing-prices/ensemble/final/submission.csv

Task execution complete!
Final RMSE: 0.38
Submission ready at: workspace/california-housing-prices/ensemble/final/submission.csv
```

### Testing and Evaluation

**Install Test Dependencies**
```bash
poetry install --with dev
```

**Run Unit Tests**
```bash
# From machine-learning-engineering directory
python3 -m pytest tests
```

**Run Evaluation**
```bash
python3 -m pytest eval
```

**Test Coverage:**
- **tests/**: Functional tests on sample request
  - Verifies all components work together
  - Checks agent responses
  - Validates workflow execution

- **eval/**: ADK evaluation demonstration
  - Sends multiple test requests
  - Compares responses to expected outputs
  - Uses `AgentEvaluator` from ADK
  - Measures response quality

**Expected Test Outputs:**
- All agents execute without errors
- Code generates and runs successfully
- Solutions produce valid predictions
- Submission files created correctly

### Deployment

**Prerequisites:**
```bash
# Install deployment dependencies
poetry install --with deployment

# Set GCS bucket in .env
export GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name
```

**Bucket Permissions:**
If bucket exists, grant permissions to service account as described in [Vertex AI troubleshooting docs](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/troubleshooting/deploy#permission_errors).

If bucket doesn't exist, ADK will create it automatically.

**Deploy to Vertex AI Agent Engine**
```bash
python3 deployment/deploy.py --create
```

**Deployment Output:**
```
Created remote agent: projects/<PROJECT_NUMBER>/locations/<PROJECT_LOCATION>/reasoningEngines/<AGENT_ENGINE_ID>
```

**List Deployed Agents**
```bash
python3 deployment/deploy.py --list
```

**Output:**
```
All remote agents:

123456789 ("machine_learning_engineering")
- Create time: 2025-07-11 09:46:07+00:00
- Update time: 2025-05-10 09:46:09+00:00
```

**Test Deployed Agent**
```bash
export USER_ID=test-user-123
export AGENT_ENGINE_ID=<your-agent-id>

python3 deployment/test_deployment.py --resource_id=${AGENT_ENGINE_ID} --user_id=${USER_ID}
```

**Interactive Session:**
```
Found agent with resource ID: ...
Created session for user ID: ...
Type 'quit' to exit.

Input: Hello. What can you do for me?
Response: Hello! I'm a Machine Learning Engineer Assistant. I can help you
achieve competition-level quality in solving machine learning tasks.

To get started, please provide the task description of the competition.

Input: execute california housing task
Response: [Executes full pipeline...]
```

**Delete Deployed Agent**
```bash
python3 deployment/deploy.py --delete --resource_id=${AGENT_ENGINE_ID}
```

### Troubleshooting

**Poetry Installation Issues**

**Error:** `command not found: poetry`

**Fix:**
```bash
# Install via pip
pip install poetry

# Or use python module syntax
python -m poetry install
```

**Error:** Keyring-related errors on Linux

**Fix:**
```bash
poetry config keyring.enabled false
poetry install
```

**Environment Activation Issues**

**Error:** Environment not activating with `poetry shell`

**Fix:**
```bash
# Use explicit activation
source $(poetry env info --path)/bin/activate

# Verify activation
which python  # Should point to virtual environment
```

**PyTorch Installation Issues**

**Error:** PyTorch fails to install or wrong version

**Fix:**
```bash
# CPU version is specified in pyproject.toml
# For GPU support, modify pyproject.toml lines 22-25:
# Change source from pytorch_cpu to pytorch_cu118 (or appropriate CUDA version)
# Visit https://pytorch.org for correct URLs
```

**GCP Authentication Issues**

**Error:** `Default credentials not found`

**Fix:**
```bash
# Re-authenticate
gcloud auth application-default login

# Set quota project
gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT

# Verify credentials
gcloud auth application-default print-access-token
```

**Task Execution Errors**

**Error:** `Task description file not found`

**Fix:**
- Verify task directory exists: `machine_learning_engineering/tasks/<task_name>/`
- Ensure `task_description.txt` is present
- Check `task_name` in config.py matches directory name

**Error:** `Data files not found during execution`

**Fix:**
- Place train.csv, test.csv in task directory
- Ensure filenames match task description
- Check file permissions (must be readable)

**Code Execution Timeout**

**Error:** `Execution exceeded timeout of 600 seconds`

**Fix:**
```python
# In config.py, increase timeout:
exec_timeout: int = 1200  # Increase to 20 minutes

# Or optimize task data:
# - Reduce dataset size for testing
# - Use smaller model for debugging
# - Enable early stopping in models
```

**Memory Issues**

**Error:** `MemoryError` or process killed

**Fix:**
- Reduce `num_solutions` in config (default: 2)
- Reduce `num_model_candidates` (default: 2)
- Increase system RAM allocation
- Process smaller data batches
- Use models with lower memory footprint

**Deployment Errors**

**Error:** `Bucket permission denied`

**Fix:**
- Ensure bucket exists or allow ADK to create it
- Grant service account Storage Object Admin role
- See [Vertex AI troubleshooting](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/troubleshooting/deploy#permission_errors)

**Error:** `Agent Engine quota exceeded`

**Fix:**
- Request quota increase in GCP Console
- Delete unused deployed agents
- Use different region with available quota

## Customization Options

### 1. Adjust Iteration Counts for Faster/Deeper Exploration

**Objective:** Control trade-off between speed and solution quality.

**Location:** `machine_learning_engineering/shared_libraries/config.py`

**Modification:**
```python
@dataclasses.dataclass
class DefaultConfig:
    # ... other fields ...

    # FASTER EXECUTION (reduced iterations)
    num_solutions: int = 1  # Generate 1 solution instead of 2
    num_model_candidates: int = 1  # Try 1 model instead of 2
    inner_loop_round: int = 1  # Plan refinement iterations
    outer_loop_round: int = 1  # Ablation cycles
    ensemble_loop_round: int = 0  # Skip ensemble (set to 0)
    max_debug_round: int = 3  # Reduce debug attempts

    # DEEPER EXPLORATION (increased iterations)
    num_solutions: int = 5  # Generate 5 diverse solutions
    num_model_candidates: int = 3  # Try 3 models per solution
    inner_loop_round: int = 3  # More plan refinements
    outer_loop_round: int = 3  # Multiple ablation cycles
    ensemble_loop_round: int = 3  # Extensive ensemble tuning
    max_debug_round: int = 10  # More debugging attempts
```

**Impact:**
- **Faster**: Reduces execution time by 50-70%, may sacrifice 5-10% accuracy
- **Deeper**: Increases execution time by 2-3x, may improve accuracy by 10-20%

**Recommended Presets:**

**Quick Prototyping:**
```python
num_solutions: int = 1
num_model_candidates: int = 1
inner_loop_round: int = 0  # Skip refinement
outer_loop_round: int = 0  # Skip ablation
ensemble_loop_round: int = 0  # Skip ensemble
```

**Competition Mode:**
```python
num_solutions: int = 4
num_model_candidates: int = 3
inner_loop_round: int = 2
outer_loop_round: int = 2
ensemble_loop_round: int = 2
num_top_plans: int = 3
```

### 2. Enable Data Leakage and Usage Checkers

**Objective:** Ensure ML best practices and prevent common mistakes.

**Location:** `machine_learning_engineering/shared_libraries/config.py`

**Modification:**
```python
@dataclasses.dataclass
class DefaultConfig:
    # ... other fields ...

    # Enable safety checks
    use_data_leakage_checker: bool = True  # Prevent data leakage
    use_data_usage_checker: bool = True   # Verify all data used
```

**What Data Leakage Checker Does:**
- Verifies test data not used during training
- Checks train/validation split is proper
- Detects future data leakage in time series
- Validates preprocessing doesn't peek at test set
- Reviews feature engineering for leakage

**What Data Usage Checker Does:**
- Confirms all provided data files are loaded
- Verifies all features are considered
- Checks no data source is ignored
- Ensures comprehensive data utilization

**Location of Checker Logic:**
- Data leakage: `machine_learning_engineering/shared_libraries/check_leakage_util.py`
- Data leakage prompts: `machine_learning_engineering/shared_libraries/data_leakage_prompt.py`

**Custom Leakage Rules:**
Edit `data_leakage_prompt.py` to add domain-specific checks:
```python
ADDITIONAL_CHECKS = """
For time series tasks:
- Ensure no future information used in feature engineering
- Verify temporal ordering in train/validation split
- Check no data from future periods leaked

For recommendation systems:
- Ensure user-item interactions don't leak test set
- Verify cold-start scenarios properly handled
"""
```

**Impact:**
- Adds 10-20% execution time
- Prevents critical ML mistakes
- Improves solution reliability
- Essential for production deployment

### 3. Customize Task Configuration for Different ML Problems

**Objective:** Adapt agent for classification, regression, or custom tasks.

**Location:** `machine_learning_engineering/shared_libraries/config.py`

**Example: Binary Classification Task**
```python
@dataclasses.dataclass
class DefaultConfig:
    data_dir: str = "./machine_learning_engineering/tasks/"
    task_name: str = "titanic-survival"
    task_type: str = "Tabular Binary Classification"
    lower: bool = False  # Higher accuracy is better
    workspace_dir: str = "./machine_learning_engineering/workspace/"
```

**Example: Multi-class Classification**
```python
task_name: str = "iris-classification"
task_type: str = "Tabular Multi-class Classification"
lower: bool = False  # Higher accuracy is better
```

**Example: Time Series Forecasting**
```python
task_name: str = "sales-forecasting"
task_type: str = "Time Series Regression"
lower: bool = True  # Lower MAE is better
exec_timeout: int = 1200  # Time series may need more time
```

**Example: Image Classification**
```python
task_name: str = "mnist-digits"
task_type: str = "Image Classification"
lower: bool = False  # Higher accuracy is better
exec_timeout: int = 1800  # Deep learning needs more time
```

**Task Description Template:**
Create `tasks/<task_name>/task_description.txt`:
```
Task: [Clear task description]

Problem Type: [Classification/Regression/Time Series/etc.]
Metric: [Accuracy/RMSE/MAE/F1/AUC/etc.]
Optimization: [Maximize/Minimize]

Data Files:
- train.csv: Training data description
- test.csv: Test data description
- [any other files]

Features:
- feature1: Description
- feature2: Description
...

Target:
- target_column: What to predict

Special Considerations:
- [Any domain-specific notes]
- [Evaluation criteria]
- [Constraints]

Submission Format:
[Required output format]
```

### 4. Change LLM Model for Different Performance/Cost Trade-offs

**Objective:** Balance quality, speed, and cost.

**Location:** `.env` file

**Available Models:**

**High Performance (Recommended for Competitions):**
```bash
ROOT_AGENT_MODEL=gemini-2.5-pro
# Pros: Best performance, 63.6% medal rate on MLE-bench-Lite
# Cons: Higher cost, slower execution
```

**Balanced Performance:**
```bash
ROOT_AGENT_MODEL=gemini-2.5-flash
# Pros: Good performance (43.9% medal rate), fast, cost-effective
# Cons: Slightly lower accuracy than Pro
```

**Fast Prototyping:**
```bash
ROOT_AGENT_MODEL=gemini-2.0-flash-001
# Pros: Very fast, low cost
# Cons: May need more iterations
```

**Model Performance Comparison** (from README, lines 9-13):
| Model | Medal Rate | Gold | Silver | Bronze |
|-------|------------|------|--------|--------|
| Gemini-2.5-Pro | 63.6% | 36.4% | 21.2% | 6.1% |
| Gemini-2.5-Flash | 43.9% | 30.3% | 4.5% | 9.1% |

**Advanced: Per-Agent Model Selection**

Modify `config.py` for fine-grained control:
```python
@dataclasses.dataclass
class DefaultConfig:
    # General agent model
    agent_model: str = "gemini-2.5-flash"

    # Override for specific agents (requires code changes)
    # In initialization/agent.py:
    # model_retriever_agent = Agent(model="gemini-2.5-pro", ...)  # Use Pro for retrieval
    # In refinement/agent.py:
    # ablation_agent = Agent(model="gemini-2.5-flash", ...)  # Use Flash for ablation
```

**Cost Optimization Strategy:**
- Use Pro for initialization (most critical)
- Use Flash for refinement iterations (high volume)
- Use Flash for debugging (many retries)
- Use Pro for final ensemble (high impact)

### 5. Implement Custom Evaluation Metrics

**Objective:** Use domain-specific metrics beyond standard MSE/accuracy.

**Location:** Create `machine_learning_engineering/shared_libraries/custom_metrics.py`

**Implementation:**
```python
"""Custom evaluation metrics for ML tasks."""

import numpy as np
from sklearn.metrics import mean_squared_error, log_loss
from typing import Dict, Any


def weighted_rmse(y_true: np.ndarray, y_pred: np.ndarray, weights: np.ndarray) -> float:
    """
    Compute weighted RMSE for imbalanced datasets.

    Args:
        y_true: True target values
        y_pred: Predicted values
        weights: Sample weights

    Returns:
        Weighted RMSE score
    """
    squared_errors = (y_true - y_pred) ** 2
    weighted_se = squared_errors * weights
    wmse = np.sum(weighted_se) / np.sum(weights)
    return np.sqrt(wmse)


def quantile_loss(y_true: np.ndarray, y_pred: np.ndarray, quantile: float = 0.5) -> float:
    """
    Compute quantile loss (useful for forecasting).

    Args:
        y_true: True values
        y_pred: Predicted quantile values
        quantile: Target quantile (default 0.5 for median)

    Returns:
        Quantile loss
    """
    errors = y_true - y_pred
    return np.mean(np.maximum(quantile * errors, (quantile - 1) * errors))


def custom_business_metric(y_true: np.ndarray, y_pred: np.ndarray,
                          cost_false_positive: float = 1.0,
                          cost_false_negative: float = 10.0) -> float:
    """
    Custom business metric with asymmetric costs.

    Args:
        y_true: True binary labels
        y_pred: Predicted binary labels
        cost_false_positive: Cost of false positive
        cost_false_negative: Cost of false negative

    Returns:
        Total business cost
    """
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))

    total_cost = (fp * cost_false_positive) + (fn * cost_false_negative)
    return total_cost


def get_metric_function(metric_name: str):
    """
    Get metric function by name.

    Args:
        metric_name: Name of metric

    Returns:
        Metric function
    """
    metrics = {
        'weighted_rmse': weighted_rmse,
        'quantile_loss': quantile_loss,
        'custom_business': custom_business_metric,
    }

    if metric_name not in metrics:
        raise ValueError(f"Unknown metric: {metric_name}")

    return metrics[metric_name]
```

**Integration:**
Modify `debug_util.py` to use custom metrics:
```python
from machine_learning_engineering.shared_libraries import custom_metrics

def evaluate_solution(y_true, y_pred, metric_name='rmse'):
    """Evaluate solution with custom metric."""
    if metric_name == 'weighted_rmse':
        # Load sample weights from task data
        weights = load_sample_weights()
        score = custom_metrics.weighted_rmse(y_true, y_pred, weights)
    elif metric_name == 'custom_business':
        score = custom_metrics.custom_business_metric(y_true, y_pred)
    else:
        # Default metrics
        score = mean_squared_error(y_true, y_pred, squared=False)

    return score
```

**Update Task Description:**
```
Metric: Weighted RMSE (lower is better)
Weights: Sample weights provided in train.csv weight column
```

### 6. Add Custom Code Templates for Domain-Specific Tasks

**Objective:** Provide starting templates for specific domains.

**Location:** Create `machine_learning_engineering/templates/`

**Example: Time Series Template**
```python
# templates/time_series_template.py
"""Template for time series forecasting tasks."""

TEMPLATE = '''
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit

# Load data
train = pd.read_csv('input/train.csv')
test = pd.read_csv('input/test.csv')

# Parse dates
train['date'] = pd.to_datetime(train['date'])
test['date'] = pd.to_datetime(test['date'])

# Sort by time
train = train.sort_values('date')

# Create time-based features
def create_time_features(df):
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['dayofweek'] = df['date'].dt.dayofweek
    df['quarter'] = df['date'].dt.quarter
    return df

train = create_time_features(train)
test = create_time_features(test)

# Create lag features (avoid data leakage!)
def create_lag_features(df, target_col, lags=[1, 7, 30]):
    for lag in lags:
        df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
    return df

# Model placeholder - INSERT MODEL HERE
# Example: ARIMA, Prophet, LSTM, XGBoost for time series

# Time series cross-validation
tscv = TimeSeriesSplit(n_splits=5)
scores = []

for train_idx, val_idx in tscv.split(X_train):
    # Train and evaluate with temporal ordering
    pass

# Generate predictions
predictions = model.predict(X_test)

# Save submission
submission = pd.DataFrame({
    'Id': test['id'],
    'Predicted': predictions
})
submission.to_csv('submission.csv', index=False)
'''
```

**Integration:**
Modify prompts to reference templates:
```python
# In initialization/prompt.py
MODEL_EVAL_INSTR = """
For time series tasks, start with this template:
{time_series_template}

Then integrate the model: {model_description}
"""
```

### 7. Customize Ablation Strategy for Specific Components

**Objective:** Focus ablation on specific ML pipeline components.

**Location:** `machine_learning_engineering/sub_agents/refinement/prompt.py`

**Modification:**
```python
ABLATION_INSTR = """
Perform systematic ablation study on the solution code.

Priority components to ablate (in order):
1. Feature Engineering
   - Remove feature interactions
   - Remove polynomial features
   - Remove domain-specific features

2. Hyperparameter Tuning
   - Use default hyperparameters
   - Skip grid search

3. Data Preprocessing
   - Remove normalization
   - Remove outlier handling
   - Remove missing value imputation

4. Model Architecture
   - Use simpler model variant
   - Reduce model complexity

For each component:
- Generate code with that component removed/simplified
- Preserve all other components
- Ensure code still executes

Return Python code for ablation study with clear comments indicating
what was removed.

Code should include:
- Same data loading and preprocessing (except what's being ablated)
- Modified model training
- Evaluation on validation set
- Print statements for ablation results

Important:
- Ablate ONE component at a time
- Code must be executable
- Include score calculation
"""
```

**Custom Ablation for Deep Learning:**
```python
DEEP_LEARNING_ABLATION_INSTR = """
For deep learning models, ablate these components:

1. Architecture Components:
   - Remove attention mechanisms
   - Remove skip connections
   - Reduce layer depth
   - Reduce hidden units

2. Regularization:
   - Remove dropout
   - Remove batch normalization
   - Remove weight decay

3. Data Augmentation:
   - Remove augmentation
   - Use only basic transformations

4. Training Strategy:
   - Remove learning rate scheduling
   - Remove early stopping
   - Use simpler optimizer (SGD vs Adam)

Generate executable code for each ablation.
"""
```

---

**Additional Resources:**
- Research Paper: [arxiv.org/abs/2506.15692](https://www.arxiv.org/abs/2506.15692)
- Architecture Diagram: `machine-learning-engineering-architecture.svg`
- Example Tasks: `machine_learning_engineering/tasks/california-housing-prices/`
- Configuration Reference: `machine_learning_engineering/shared_libraries/config.py`
- MLE-Bench-Lite: [github.com/openai/mle-bench](https://github.com/openai/mle-bench/tree/main)
