# Image Scoring Agent - Technical Documentation Report

## Project Scope

The Image Scoring Agent is an automated image generation and evaluation system that creates and validates AI-generated images based on text descriptions while ensuring strict compliance with predefined policies. The agent implements an iterative quality assurance loop that generates, evaluates, and regenerates images until they meet specific quality and compliance standards.

**Core Capabilities:**
- **Text-to-Image Generation**: Creates images from text descriptions using Google Imagen 3.0
- **Policy-Based Evaluation**: Scores generated images against predefined quality and compliance criteria
- **Iterative Refinement**: Automatically regenerates images that don't meet policy requirements
- **Threshold-Based Termination**: Continues iteration until quality score meets threshold or max iterations reached
- **Detailed Scoring Feedback**: Provides granular scores (0-5) for each policy criterion

**Primary Use Cases:**
- Automated content generation for news articles and blogs
- Brand compliance verification for marketing materials
- Safety and policy enforcement for user-generated content platforms
- Quality assurance for AI-generated visual assets
- Automated image validation pipelines

**Target Users:**
- Content management systems with image generation
- Marketing teams requiring brand-compliant visuals
- Publishers generating illustrated articles
- Platform safety and moderation teams
- Creative agencies using AI-assisted workflows

## Technical Architecture

### Looping Multi-Agent Workflow

The system implements a **LoopAgent architecture** with embedded sequential workflow:

```
LoopAgent (image_scoring) [Repeats until threshold met or max iterations]
    │
    ├─→ SequentialAgent (image_generation_scoring_agent)
    │       ├─→ Prompt Generation Agent (optimizes Imagen prompt)
    │       ├─→ Image Generation Agent (creates image with Imagen 3.0)
    │       └─→ Scoring Agent (evaluates against policies)
    │
    └─→ Checker Agent (evaluates score, decides continue/stop)
```

**Agent Definitions** (`image_scoring/agent.py`):

1. **Root: image_scoring** (LoopAgent) - lines 63-72:
   - **Type**: `LoopAgent` - Repeats sub-agents until termination condition met
   - **Sub-agents**:
     1. `image_generation_scoring_agent` (sequential workflow)
     2. `checker_agent_instance` (termination evaluator)
   - **Callback**: `set_session` - Creates unique ID and timestamp before execution
   - **Termination**: When `checker_agent` sets `tool_context.actions.escalate = True`

2. **image_generation_scoring_agent** (SequentialAgent) - lines 44-56:
   - **Type**: `SequentialAgent` - Executes sub-agents in order
   - **Sub-agents** (sequential):
     1. `image_generation_prompt_agent` - Creates optimized Imagen prompts
     2. `image_generation_agent` - Generates images
     3. `scoring_images_prompt` - Evaluates images against policies
   - **Description**: Analyzes text → generates prompt → generates image → scores image

### Sub-Agents (from README lines 163-186)

1. **Prompt Generation Agent** (`sub_agents/prompt.py`):
   - **Purpose**: Creates policy-compliant, optimized prompts for Imagen
   - **Model**: Gemini
   - **Input**: Original text description
   - **Output**: Optimized prompt stored in session state
   - **Features**: Ensures prompts align with policy requirements

2. **Image Generation Agent** (`sub_agents/image.py`):
   - **Purpose**: Generates images using Imagen 3.0
   - **Tool**: Imagen 3.0 API
   - **Configuration**:
     - Aspect ratio control
     - Safety filters
     - Quality parameters
   - **Output**:
     - Generated images saved to Google Cloud Storage (GCS)
     - GCS URIs and image artifacts stored in session state

3. **Scoring Agent** (`sub_agents/scoring.py`):
   - **Purpose**: Evaluates images against policy rules
   - **Policy Source**: `policy.json` file
   - **Scoring**:
     - Assigns scores 0-5 for each policy criterion
     - Computes total score
     - Stores score in session state
   - **Output**: Detailed feedback for each policy rule

4. **Checker Agent** (`checker_agent.py`):
   - **Purpose**: Determines workflow continuation or termination
   - **Responsibilities**:
     - Tracks iteration count
     - Compares total score against threshold (default: 10)
     - Enforces maximum iteration limit
   - **Termination Conditions**:
     - Score meets or exceeds threshold → escalate (stop loop)
     - Max iterations reached → escalate (stop loop)
     - Score below threshold & iterations remain → continue loop

### Workflow Sequence

**Example: "A peaceful mountain landscape at sunset"**

**Iteration 1**:
1. **set_session callback**: Creates unique_id and timestamp in state
2. **Prompt Agent**:
   - Input: "A peaceful mountain landscape at sunset"
   - Gemini optimizes: "Serene mountain vista at golden hour, soft clouds, warm sunset colors, photorealistic"
   - Stores in `state["prompt"]`
3. **Image Agent**:
   - Calls Imagen 3.0 with optimized prompt
   - Generates image
   - Saves to GCS: `gs://bucket/unique_id/image_1.png`
   - Stores URI in `state["image_uri"]`
4. **Scoring Agent**:
   - Loads `policy.json` rules:
     - "Image contains visible horizon line" (weight: 2)
     - "Sunset colors are warm and natural" (weight: 3)
     - "No distorted elements" (weight: 3)
     - etc.
   - Analyzes image: Scores [4, 3, 2, ...]
   - Total score: 9/15
   - Stores in `state["total_score"]`
5. **Checker Agent**:
   - Checks: `total_score (9) >= threshold (10)` ? **No**
   - Checks: `iteration_count (1) >= max_iterations (5)` ? **No**
   - Decision: **Continue loop** (does not escalate)

**Iteration 2**:
1-4. Repeats with refined generation
5. **Checker Agent**:
   - New `total_score: 12 >= threshold (10)` ? **Yes**
   - Decision: **Escalate (stop loop)**
   - Returns final image

### Key Libraries and Dependencies

**Core Framework:**
- `google-adk>=1.5.0` - Agent Development Kit (LoopAgent, SequentialAgent)
- `google-cloud-aiplatform[adk,agent-engines]>=1.93.0` - Vertex AI, Imagen integration

**Image Processing:**
- `pillow>=10.3.0` - Image manipulation and analysis

**Data & Logging:**
- `pandas>=2.1.1` - Data structures for evaluation metrics
- `google-cloud-logging>=3.12.0` - Cloud logging for debugging

**Evaluation:**
- `pytest>=8.3.4` - Testing framework
- `pytest-asyncio>=0.23.8` - Async test support
- `nest-asyncio>=1.6.0` - Nested event loop support

**Development:**
- `agent-starter-pack>=0.14.1` - Production deployment utilities
- `jupyter~=1.1.1` - Notebook support (optional)
- `ruff>=0.4.6` - Fast linter
- `mypy~=1.18.2` - Type checking

### Session State Management

**Callback Context State** (`agent.py:23-32`):
- **Before Execution**:
  - `unique_id`: UUID for tracking
  - `timestamp`: ISO 8601 timestamp
- **During Workflow**:
  - `prompt`: Optimized Imagen prompt
  - `image_uri`: GCS URI of generated image
  - `image_artifacts`: Image metadata
  - `policy_scores`: Individual rule scores
  - `total_score`: Aggregate score
  - `iteration_count`: Current iteration number

**State Persistence**: Maintained across loop iterations via `CallbackContext`

### Policy Configuration

**policy.json Structure** (referenced in README line 176):
```json
{
  "rules": [
    {
      "criterion": "Image contains required elements",
      "weight": 3,
      "description": "Check if all required elements from prompt are present"
    },
    {
      "criterion": "No distorted or malformed objects",
      "weight": 3,
      "description": "Ensure image quality and realism"
    },
    {
      "criterion": "Appropriate colors and lighting",
      "weight": 2,
      "description": "Colors match described scene"
    }
  ],
  "threshold": 10,
  "max_iterations": 5
}
```

## Build & Run Instructions

### Prerequisites

1. **Python 3.10, 3.11, or 3.12** (NOT 3.13+)
2. **uv** package manager:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Google Cloud Project** with:
   - Imagen 3.0 API enabled
   - Cloud Storage bucket for images
   - Vertex AI API enabled

### Step 1: Clone Repository

```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/image-scoring
```

### Step 2: Install Dependencies

```bash
uv sync --dev
```

### Step 3: Configure Environment

Copy example environment file:
```bash
cp .env-example .env
```

Edit `.env`:
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True

# OR for AI Studio:
# GOOGLE_GENAI_USE_VERTEXAI=FALSE
# GOOGLE_API_KEY=your-api-key
```

Authenticate:
```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT
```

### Step 4: Run the Agent

**CLI Interface:**
```bash
adk run image_scoring
```

**Web UI:**
```bash
adk web
```
Select `image_scoring` from dropdown.

### Example Prompts

Try these text descriptions:
- "a peaceful mountain landscape at sunset"
- "a cat riding a bicycle"
- "a polar bear in the Sahara desert"

### Step 5: Run Evaluation

```bash
uv run pytest eval
```

Validates:
- Tool usage correctness
- Score calculation accuracy
- Iteration behavior

## Customization Options

### 1. Adjust Policy Rules

Edit `policy.json`:
```json
{
  "rules": [
    {"criterion": "Brand logo visible", "weight": 5},
    {"criterion": "No competing brands", "weight": 4},
    {"criterion": "Consistent color palette", "weight": 2}
  ],
  "threshold": 8,
  "max_iterations": 3
}
```

### 2. Modify Imagen Parameters

In `sub_agents/image.py`:
```python
imagen_config = {
    "aspect_ratio": "16:9",  # Change aspect ratio
    "number_of_images": 4,   # Generate multiple variants
    "safety_filter_level": "block_most",
    "person_generation": "allow_adult"
}
```

### 3. Add Custom Evaluation Metrics

Extend `sub_agents/scoring.py`:
```python
def evaluate_custom_metrics(image, policies):
    scores = {}
    # Add ML-based quality assessment
    scores["aesthetic_score"] = compute_aesthetic_score(image)
    scores["technical_quality"] = compute_sharpness(image)
    return scores
```

### 4. Change Termination Logic

Modify `checker_agent.py`:
```python
# Early termination if score perfect
if total_score == max_possible_score:
    tool_context.actions.escalate = True

# Or adaptive threshold based on iteration count
threshold = base_threshold - (iteration_count * 0.5)
```

### 5. Integration with CMS

Add publishing workflow:
```python
def publish_approved_image(image_uri, metadata):
    # Upload to WordPress/Contentful
    cms_client.create_media(image_uri, metadata)
```

## Production Deployment

Using Agent Starter Pack:

```bash
# With pip
python -m venv .venv && source .venv/bin/activate
pip install --upgrade agent-starter-pack
agent-starter-pack create my-image-scorer -a adk@image-scoring

# With uv
uvx agent-starter-pack create my-image-scorer -a adk@image-scoring
```

## Performance Characteristics

**Agent Type:** Multi-Agent (LoopAgent + SequentialAgent)
**Complexity:** Medium
**Interaction Type:** Workflow (automated)

**Typical Execution**:
- Prompt generation: 2-5 seconds
- Image generation (Imagen 3.0): 10-20 seconds
- Scoring: 3-5 seconds
- **Per iteration**: ~15-30 seconds
- **Average workflow**: 2-3 iterations = 30-90 seconds total

**Resource Requirements**:
- Cloud Storage for generated images
- Imagen 3.0 API quota
- Vertex AI Gemini quota

---

**Author:** Kishore Jagannath (kishorerj@google.com)
**License:** Apache 2.0
**Python Version:** 3.10 - 3.12
**Vertical:** Horizontal (Content Generation, Quality Assurance)
