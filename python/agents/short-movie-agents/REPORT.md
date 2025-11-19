# Short Movie Agents - Technical Documentation Report

## Project Scope

The Short Movie Agents is an advanced multi-agent AI system that orchestrates the complete production pipeline for creating short animated campfire stories, from initial concept to final video output. This project demonstrates sophisticated agent collaboration, multimodal AI integration, and automated creative workflows.

### Core Capabilities
- **Story Generation**: Create engaging campfire narratives with character development, plot structure, and Scout Leader persona
- **Screenplay Writing**: Transform stories into professional screenplay format with scene headings, action lines, and dialogue
- **Storyboard Visualization**: Generate black-and-white comic-style storyboards using Imagen4 for each scene
- **Video Production**: Produce 8-second video clips for each scene using Veo3, with automatic dialogue extraction and audio integration
- **Interactive Director Workflow**: Guide users step-by-step through the creative process with approval gates at each stage
- **Multi-Scene Orchestration**: Coordinate multiple scenes with consistent character appearances and narrative flow

### Primary Use Cases
- Automated short film production for educational content
- Rapid prototyping of video stories for scouts and youth organizations
- Creative writing workshops with visual feedback
- Content creation for social media or marketing campaigns
- Educational demonstrations of multi-agent AI collaboration
- Storyboarding and pre-visualization for film projects

### Target Users
- Content Creators developing short-form video content
- Educators teaching storytelling or film production
- Marketing Teams creating narrative-driven campaigns
- Scout Leaders and youth organization coordinators
- AI/ML Engineers learning multi-agent orchestration patterns
- Creative Professionals prototyping story concepts

### Key Innovations/Differentiators
- **Full Production Pipeline Automation**: End-to-end video creation from text prompt to final video without manual intervention
- **Multi-Agent Hierarchical Architecture**: Director agent coordinates 4 specialized sub-agents, each with distinct creative responsibilities
- **Multimodal AI Integration**: Seamlessly combines text generation (Gemini), image generation (Imagen4), and video generation (Veo3)
- **Session State Management**: Maintains creative artifacts across agent handoffs using ADK's output_key mechanism
- **Character Consistency**: Propagates character descriptions through the entire pipeline to ensure visual coherence
- **Interactive Approval Workflow**: User-in-the-loop design with revision capabilities at each production stage
- **Tool Context Awareness**: Custom tools access session metadata for GCS path management and asset organization

## Technical Architecture

### Multi-Agent Hierarchy

**Architecture Pattern**: Hierarchical Multi-Agent System with Sequential Delegation

The Short Movie Agents implements a director-worker pattern where a root "director" agent orchestrates four specialized sub-agents in a sequential creative pipeline.

### Agent Hierarchy Diagram

```
                            ┌──────────────────────────────────────┐
                            │      Director Agent (Root)           │
                            │    Model: Gemini 2.5 Flash           │
                            │    Role: Orchestration & User        │
                            │          Interaction                 │
                            └──────────────┬───────────────────────┘
                                           │
                                           │ Delegates tasks sequentially
                                           │
        ┌──────────────────────────────────┼───────────────────────────────────────┐
        │                                  │                                       │
        ▼                                  ▼                                       ▼
┌───────────────────┐            ┌──────────────────┐                   ┌──────────────────┐
│  Story Agent      │            │Screenplay Agent  │                   │Storyboard Agent  │
│  (Sub-Agent 1)    │───────────▶│  (Sub-Agent 2)   │──────────────────▶│  (Sub-Agent 3)   │
├───────────────────┤            ├──────────────────┤                   ├──────────────────┤
│ Model: Gemini     │            │ Model: Gemini    │                   │ Model: Gemini    │
│       2.5 Flash   │            │       2.5 Flash  │                   │       2.5 Flash  │
│ Output: 'story'   │            │ Output:          │                   │ Output:          │
│                   │            │   'screenplay'   │                   │   'storyboard'   │
│ Tools: None       │            │ Tools: None      │                   │ Tools:           │
│                   │            │                  │                   │  - storyboard_   │
│ Persona: Scout    │            │ Role: Transform  │                   │    generate()    │
│  Leader telling   │            │  story to        │                   │                  │
│  campfire stories │            │  screenplay      │                   │ External Model:  │
└───────────────────┘            │  format          │                   │  Imagen4 (Ultra) │
                                 └──────────────────┘                   └──────────────────┘
                                                                                  │
                                                                                  │
                                                                                  ▼
                                                                         ┌──────────────────┐
                                                                         │  Video Agent     │
                                                                         │  (Sub-Agent 4)   │
                                                                         ├──────────────────┤
                                                                         │ Model: Gemini    │
                                                                         │       2.5 Flash  │
                                                                         │ Output: 'video'  │
                                                                         │                  │
                                                                         │ Tools:           │
                                                                         │  - video_        │
                                                                         │    generate()    │
                                                                         │                  │
                                                                         │ External Model:  │
                                                                         │  Veo3 (Preview)  │
                                                                         └──────────────────┘

Data Flow (Session State):
─────────────────────────────
1. Director → Story Agent:        User concept
2. Story Agent → Session:         'story' (with character descriptions)
3. Session → Screenplay Agent:    'story' (retrieved from session)
4. Screenplay Agent → Session:    'screenplay' (structured screenplay)
5. Session → Storyboard Agent:    'screenplay' + 'story'
6. Storyboard Agent → Session:    'storyboard' (list of GCS image URIs)
7. Session → Video Agent:         'screenplay' + 'storyboard' + 'story'
8. Video Agent → Session:         'video' (list of GCS video URIs)
9. Session → Director:            All artifacts for user presentation
```

### Code Flow Explanation

**1. Entry Point - Director Agent**
**File**: `/home/user/adk-samples/python/agents/short-movie-agents/app/agent.py`

- **Lines 28-30**: Configuration constants define model (Gemini 2.5 Flash) and agent description
- **Lines 34-41**: Director agent initialization with 4 sub-agents registered
  - Imports sub-agents from separate modules (Lines 19-23)
  - Loads director prompt from file using utility (Line 39)
  - Sets up sub_agents list: `[story_agent, screenplay_agent, storyboard_agent, video_agent]`
- **Lines 42-54**: Error handling and validation logging
  - Checks each sub-agent initialized successfully
  - Logs specific failures for debugging

**2. Story Agent - Creative Writer**
**File**: `/home/user/adk-samples/python/agents/short-movie-agents/app/story_agent.py`

- **Lines 28-36**: Agent creation
  - Model: Gemini 2.5 Flash (Line 28)
  - Description loaded from `story_agent_desc.txt` (Line 33)
  - Instruction loaded from `story_agent.txt` (Line 34)
  - **Critical**: `output_key="story"` (Line 35) - stores output in session state for downstream agents
- **Prompt** (`app/prompts/story_agent.txt`):
  - Persona: Scout Leader at campfire (Lines 1-3)
  - Structure requirements: Beginning, rising action, climax, resolution (Lines 5-9)
  - **Character descriptions mandatory** at end (Lines 11-15) - enables visual consistency
  - Transfers back to root agent after completion (Line 18)

**3. Screenplay Agent - Format Translator**
**File**: `/home/user/adk-samples/python/agents/short-movie-agents/app/screenplay_agent.py`

- **Lines 30-38**: Agent initialization
  - Lighter model acceptable for formatting task (comment Line 32)
  - `output_key="screenplay"` (Line 37) - publishes formatted screenplay
- **Prompt** (`app/prompts/screenplay_agent.txt`):
  - **Retrieves story from session** (Line 7): "Access the session state and retrieve the story"
  - Excludes framing narrative - focuses on core story (Lines 9-10)
  - Screenplay structure: Scene headings, action lines, character names, dialogue, parentheticals (Lines 14-19)
  - **Maintains character consistency** using descriptions (Line 20)
  - Comprehensive coverage of all story parts (Line 22)

**4. Storyboard Agent - Visual Scene Designer**
**File**: `/home/user/adk-samples/python/agents/short-movie-agents/app/storyboard_agent.py`

- **Lines 36-45**: Vertex AI initialization for Imagen4
  - Project/location from environment variables (Lines 38-39)
  - `vertexai.init()` configures client (Lines 41-44)
  - Loads Imagen 4.0 Ultra model (Line 45)

- **Lines 48-96**: `storyboard_generate()` custom tool function
  - **Parameters**: `prompt` (scene description), `scene_number`, `tool_context` (Lines 49-50)
  - **Line 65**: Extracts session ID from ToolContext for GCS path construction
  - **Lines 66-68**: Builds GCS URI: `gs://{bucket}/{session_id}/scene_{scene_number}`
  - **Lines 71-81**: Imagen4 API call
    - `number_of_images=1`, `aspect_ratio="1:1"`, `person_generation="allow_adult"`
    - Saves directly to GCS with `output_gcs_uri`
  - **Lines 83-93**: Returns authorized storage URLs (replaces `gs://` with MTLS endpoint)

- **Lines 100-111**: Agent configuration
  - Tools: `[storyboard_generate]` (Line 109) - single custom function
  - `output_key="storyboard"` (Line 108) - saves list of image URIs

- **Prompt** (`app/prompts/storyboard_agent.txt`):
  - Retrieves screenplay AND character descriptions (Lines 7-8)
  - **Iterates through scenes** maintaining scene numbers (Line 10)
  - Tool call requirements (Lines 18-27):
    - Two parameters: prompt with style keywords ("black and white comic"), scene number
    - Style specification critical: "in the style of a black and white comic book drawing" (Line 25)
    - Uses character descriptions for visual consistency (Line 22)
  - Returns **ordered list** of GCS links (Line 32)

**5. Video Agent - Final Production**
**File**: `/home/user/adk-samples/python/agents/short-movie-agents/app/video_agent.py`

- **Lines 30-44**: Veo3 client initialization
  - Uses Google GenAI client with Vertex AI backend (Lines 40-44)
  - Model: `veo-3.0-generate-preview`, Location: `us-central1` (Lines 33-34)
  - Aspect ratio: 16:9 for video (Line 38)

- **Lines 47-115**: `video_generate()` custom tool function
  - **Parameters**: `prompt`, `scene_number`, `image_link` (storyboard), `screenplay`, `tool_context` (Lines 48-53)
  - **Lines 69-77**: Dialogue extraction from screenplay using regex
    - Pattern 1: Character names with parentheticals (Line 76)
    - Pattern 2: Indented dialogue (Line 77)
    - Appends dialogue to prompt for audio track (Line 80)
  - **Lines 82-95**: Veo3 API call
    - `duration_seconds=8` (Line 92) - 8-second clips per scene
    - `number_of_videos=1`, saves to GCS (Lines 90-91)
  - **Lines 97-100**: Polling loop - waits for video generation (15-second intervals)
  - **Lines 102-112**: Returns authorized GCS URLs for generated videos

- **Lines 119-131**: Agent configuration
  - Tools: `[video_generate]` (Line 128)
  - `output_key="video"` (Line 127)

- **Prompt** (`app/prompts/video_agent.txt`):
  - Retrieves screenplay, storyboard links, character descriptions (Lines 7-8)
  - Processes each scene with corresponding storyboard image (Line 10)
  - Prompt construction guidance (Lines 14-20):
    - Scene heading, action lines, character consistency
    - Reference to storyboard composition (Line 19)
  - Returns ordered list of video links (Line 30)

**6. Utility Functions**
**File**: `/home/user/adk-samples/python/agents/short-movie-agents/app/utils/utils.py`

- **Lines 23-40**: `load_prompt_from_file()` function
  - Constructs path relative to script location (Line 30)
  - Loads prompt text from `../prompts/` directory (Line 20)
  - Graceful error handling with default instruction fallback (Lines 28-40)

### Agent Definitions with Roles and Responsibilities

**Director Agent** (`director_agent`)
- **Role**: Orchestrator and user interaction manager
- **Model**: Gemini 2.5 Flash
- **Responsibilities**:
  - Welcome users and gather initial story concept (Lines 7-9 in director_agent.txt)
  - Execute 4-step production workflow: Story → Screenplay → Storyboard → Video (Lines 11-37)
  - Present intermediate outputs to users for approval (Lines 13-16, 20-22, 26-30, 33-35)
  - Handle revision requests by re-calling sub-agents with feedback (Lines 15, 22, 29, 36)
  - Maintain state of approved assets for downstream agents (Line 45)
  - Conclude project when user satisfied (Lines 38-39)
- **Tools**: None (delegates to sub-agents)
- **Sub-Agents**: 4 (story, screenplay, storyboard, video)

**Story Agent** (`story_agent`)
- **Role**: Creative writer with Scout Leader persona
- **Model**: Gemini 2.5 Flash
- **Responsibilities**:
  - Generate campfire story from user concept
  - Implement narrative structure: beginning, rising action, climax, resolution (Lines 5-9)
  - Create character descriptions for visual consistency (Lines 11-15)
  - Maintain warm, enthusiastic Scout Leader tone (Lines 1-6)
  - Store complete story in session state under key 'story' (output_key)
- **Tools**: None
- **Output**: Story text + character descriptions

**Screenplay Agent** (`screenplay_agent`)
- **Role**: Format translator and screenplay writer
- **Model**: Gemini 2.5 Flash
- **Responsibilities**:
  - Retrieve story from session state (Line 7)
  - Extract core narrative, excluding campfire framing (Lines 9-10)
  - Format in standard screenplay structure (Lines 14-19):
    - Scene headings (INT/EXT, location, time)
    - Action lines in present tense
    - Character names (centered, all caps)
    - Dialogue with optional parentheticals
  - Maintain character consistency using descriptions (Line 20)
  - Cover entire narrative without omissions (Line 22)
  - Store screenplay in session state under key 'screenplay' (output_key)
- **Tools**: None
- **Output**: Formatted screenplay text

**Storyboard Agent** (`storyboard_agent`)
- **Role**: Visual scene designer and image generator
- **Model**: Gemini 2.5 Flash (orchestration) + Imagen4 Ultra (generation)
- **Responsibilities**:
  - Retrieve screenplay and character descriptions from session (Lines 7-8)
  - Iterate through each scene in screenplay (Line 10)
  - Analyze visual elements per scene: location, characters, actions, mood (Lines 12-16)
  - Generate storyboard images in black-and-white comic style (Line 25)
  - Maintain visual consistency using character descriptions (Line 22)
  - Manage scene numbering for asset organization (Lines 18-27)
  - Store ordered list of GCS image URIs in session state under key 'storyboard'
- **Tools**: 1 (`storyboard_generate`)
- **Output**: List of GCS image URIs in scene order

**Video Agent** (`video_agent`)
- **Role**: Final video production and audio integration
- **Model**: Gemini 2.5 Flash (orchestration) + Veo3 Preview (generation)
- **Responsibilities**:
  - Retrieve screenplay, storyboard links, character descriptions (Lines 7-8)
  - Generate 8-second video for each scene (Line 10)
  - Extract dialogue from screenplay for audio track (Lines 14-20)
  - Construct detailed prompts with scene context and character consistency (Lines 14-20)
  - Reference storyboard composition for visual continuity (Line 19)
  - Manage video generation operations with polling (video_agent.py Lines 97-100)
  - Store ordered list of GCS video URIs in session state under key 'video'
- **Tools**: 1 (`video_generate`)
- **Output**: List of GCS video URIs in scene order

### Key Libraries and Dependencies

From `/home/user/adk-samples/python/agents/short-movie-agents/pyproject.toml`:

**Core Framework** (Lines 22-30)
- `google-adk~=1.14.0`: Agent Development Kit for multi-agent orchestration, session management, and tool integration
- `google-cloud-aiplatform[evaluation]~=1.116.0`: Vertex AI client for Imagen4, Veo3, and model evaluation capabilities
- `google-cloud-logging>=3.12.0`: Cloud Logging integration for production monitoring
- `opentelemetry-exporter-gcp-trace~=1.9.0`: Distributed tracing for agent execution flows
- `fastapi~=0.115.8`: Web framework for API server (used in deployment)
- `uvicorn~=0.34.0`: ASGI server for FastAPI application
- `psycopg2-binary>=2.9.10`: PostgreSQL adapter (potential backend storage)

**Runtime Requirements**
- Python 3.13 only (Line 32) - latest Python version for performance

**Development Tools** (Lines 36-53)
- `pytest>=8.3.4`, `pytest-asyncio>=0.23.8`: Testing framework
- `nest-asyncio>=1.6.0`: Async event loop management
- `jupyter~=1.0.0`: Interactive notebook environment (optional)
- `ruff>=0.4.6`: Fast Python linter and formatter
- `mypy~=1.15.0`: Static type checking
- `codespell~=2.2.0`: Spell checking

### Tools and Integrations

**1. Storyboard Generation Tool**
- **Function**: `storyboard_generate(prompt, scene_number, tool_context)`
- **Location**: `/home/user/adk-samples/python/agents/short-movie-agents/app/storyboard_agent.py` Lines 48-96
- **Model**: Imagen4 Ultra (`imagen-4.0-ultra-generate-001`)
- **Capabilities**:
  - Text-to-image generation from detailed scene prompts
  - 1:1 aspect ratio for square storyboards
  - Black-and-white comic book art style
  - Direct GCS upload for asset management
  - Person generation enabled for character rendering
- **Parameters**:
  - `prompt`: Detailed visual description with style keywords
  - `scene_number`: Integer for file naming and ordering
  - `tool_context`: ADK ToolContext for session metadata access
- **Output**: List of authorized GCS URIs (MTLS endpoints)

**2. Video Generation Tool**
- **Function**: `video_generate(prompt, scene_number, image_link, screenplay, tool_context)`
- **Location**: `/home/user/adk-samples/python/agents/short-movie-agents/app/video_agent.py` Lines 47-115
- **Model**: Veo3 Preview (`veo-3.0-generate-preview`)
- **Capabilities**:
  - Text-to-video generation with image conditioning
  - 16:9 aspect ratio for widescreen video
  - 8-second duration per clip
  - Dialogue extraction and audio integration
  - Storyboard-guided composition
- **Parameters**:
  - `prompt`: Video content description
  - `scene_number`: Scene identifier
  - `image_link`: Storyboard image for visual reference (unused in current implementation)
  - `screenplay`: Full scene text for dialogue extraction
  - `tool_context`: Session metadata access
- **Output**: List of authorized GCS video URIs
- **Generation Time**: ~15+ seconds per video (polling mechanism)

**3. Google Cloud Storage (GCS) Integration**
- **Purpose**: Persistent storage for generated assets
- **Path Structure**: `gs://{bucket_name}/{session_id}/scene_{number}/`
- **Asset Types**:
  - Storyboards: `.png` images (Imagen4 output)
  - Videos: `.mp4` files (Veo3 output)
- **Access Pattern**: Authorized MTLS endpoints (`https://storage.mtls.cloud.google.com/`)
- **Session-based Organization**: Each user session gets unique folder using `tool_context._invocation_context.session.id`

**4. Session State Management**
- **Mechanism**: ADK's built-in session state with `output_key`
- **Flow**:
  - Story Agent writes to `session['story']`
  - Screenplay Agent reads from `session['story']`, writes to `session['screenplay']`
  - Storyboard Agent reads `screenplay` + `story`, writes to `session['storyboard']`
  - Video Agent reads all three, writes to `session['video']`
- **Persistence**: Maintains state across agent delegations within a single conversation

### Reasoning Mechanisms

**1. Sequential Workflow Enforcement** (director_agent.txt Lines 42-46)
- Director explicitly progresses through stages: "Do not move to the next step until the user has approved"
- Approval gates prevent pipeline advancement with incomplete work
- State tracking ensures correct artifacts passed to each stage (Line 45)

**2. Character Consistency Propagation**
- Story Agent mandates character descriptions (story_agent.txt Lines 11-15)
- Descriptions stored in 'story' output, accessible to all downstream agents
- Storyboard Agent: "using the provided character descriptions to ensure visual consistency" (storyboard_agent.txt Line 22)
- Video Agent: "Use the character descriptions to ensure all characters are rendered consistently" (video_agent.txt Line 17)

**3. Style Enforcement Through Prompting**
- Explicit style keywords in prompts: "in the style of a black and white comic book drawing" (storyboard_agent.txt Line 25)
- Multiple reinforcement terms: "storyboard", "sketch", "line art" (Line 25)
- Ensures generated images match expected aesthetic

**4. Dialogue Extraction Logic** (video_agent.py Lines 75-77)
- Regex pattern matching on screenplay format
- Pattern 1: `^\w+\s*\(.+\)\s*$` - matches "CHARACTER (emotion)"
- Pattern 2: `^\s{2,}.+$` - matches indented dialogue lines
- Concatenates matches and appends to video prompt for audio generation

**5. Error Handling and Graceful Degradation**
- Try-except blocks in agent initialization (story_agent.py Lines 37-41)
- Conditional root agent creation only if all sub-agents available (agent.py Lines 34-54)
- Detailed logging for debugging initialization failures

**6. Scene-Based Iteration**
- Storyboard and Video agents iterate through screenplay scenes
- Maintain scene numbering for asset correlation
- Use scene number in GCS paths for organization

## Build & Run Instructions

### Prerequisites

**Required Software**
- **Python 3.13**: Exact version required (specified in pyproject.toml Line 32)
  - Download from [python.org](https://www.python.org/downloads/)
  - Verify: `python3 --version` (must show 3.13.x)
- **uv**: Universal Python package manager - [Installation](https://docs.astral.sh/uv/getting-started/installation)
  - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Verify: `uv --version`
- **Google Cloud SDK** (gcloud): For Vertex AI and deployment - [Installation](https://cloud.google.com/sdk/docs/install)
  - Install: Follow platform-specific guide
  - Verify: `gcloud --version`
- **make**: Build automation tool - Pre-installed on most Unix systems
  - MacOS/Linux: Typically pre-installed
  - Windows: Install via [GNU Make for Windows](https://gnuwin32.sourceforge.net/packages/make.htm)

**Google Cloud Account**
- **Google Cloud Project**: Required for Vertex AI, GCS, and deployment
  - Create at [Google Cloud Console](https://console.cloud.google.com/)
  - Enable billing on the project
- **Enabled APIs**:
  - Vertex AI API (`aiplatform.googleapis.com`)
  - Cloud Storage API (`storage.googleapis.com`)
  - Cloud Run API (`run.googleapis.com`) - for deployment

**Google Cloud Resources**
- **GCS Bucket**: For storing generated images and videos
  - Create: `gcloud storage buckets create gs://your-bucket-name --location=us-central1`
  - Note bucket name for environment configuration

### Step-by-Step Installation

**1. Clone Repository**
```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/short-movie-agents
```

**2. Authenticate with Google Cloud**
```bash
# Login to Google Cloud
gcloud auth login

# Set default project
gcloud config set project YOUR_PROJECT_ID

# Authenticate for application default credentials (required for Vertex AI)
gcloud auth application-default login

# Set application default quota project
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

**3. Enable Required Google Cloud APIs**
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable run.googleapis.com
```

**4. Create GCS Bucket for Assets**
```bash
# Replace YOUR_BUCKET_NAME with a globally unique name
export BUCKET_NAME="short-movie-assets-$(date +%s)"

gcloud storage buckets create gs://$BUCKET_NAME \
  --location=us-central1 \
  --uniform-bucket-level-access

# Grant yourself access
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
  --member="user:YOUR_EMAIL@gmail.com" \
  --role="roles/storage.objectAdmin"
```

**5. Install Dependencies**
```bash
# Uses Makefile target (Line 2-4)
make install

# Alternatively, use uv directly:
uv sync --dev
```

This installs all dependencies from `pyproject.toml` including ADK, Vertex AI SDK, and development tools.

### Configuration (Environment Variables)

**Create .env File**

From the project directory:
```bash
# Copy template
cp .env-template .env

# Edit with your values
vim .env  # or use your preferred editor
```

**Required Environment Variables** (based on .env-template):
```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT="your-project-id"
GOOGLE_CLOUD_LOCATION="us-central1"  # Must match Veo3 location
GOOGLE_CLOUD_BUCKET_NAME="your-bucket-name"  # From step 4

# Optional: Enable Vertex AI (default is Google AI Studio)
GOOGLE_GENAI_USE_VERTEXAI="TRUE"

# Optional: For Google AI Studio instead of Vertex AI
# GOOGLE_API_KEY="your-api-key-from-aistudio"
# GOOGLE_GENAI_USE_VERTEXAI="FALSE"
```

**Location Requirements**:
- Veo3 is only available in `us-central1` (video_agent.py Line 34)
- Imagen4 supports multiple regions, but use `us-central1` for consistency

### Running the Agent

**Option 1: CLI Mode with ADK Web (Recommended for Development)**

From project directory:
```bash
make playground
```

Or equivalently:
```bash
uv run adk web . --port 8501 --reload_agents
```

**What happens**:
1. ADK web server starts on http://localhost:8501
2. Browser opens automatically (or open URL manually)
3. Select 'app' folder from dropdown (important: see Makefile Line 10)
4. Interactive chat interface appears
5. Code changes auto-reload agents (hot-reload enabled)

**Option 2: CLI Interactive Mode**

```bash
uv run adk run app
```

This starts a command-line chat interface without web UI.

**Option 3: Local Backend Server (API Mode)**

For custom frontend or API integration:
```bash
make local-backend
```

Or:
```bash
uv run uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
```

Access API at http://localhost:8000 (FastAPI endpoints).

### Example Interactions

**Example 1: Complete Story Creation Workflow**

```
User: I want to create a campfire story about a brave squirrel who finds a magical acorn.

Director Agent: Welcome! I'll help you create a short animated campfire story about a brave squirrel and a magical acorn.

Let me start by generating the story. This will take a moment...

[Calls story_agent]

Story Agent: *As a Scout Leader persona*

"Gather 'round, scouts! Tonight I'll tell you about Sammy the Squirrel...

[Story with beginning, rising action, climax, resolution]

Character Descriptions:
- Sammy the Squirrel: A small, fluffy red squirrel with bright, curious eyes and a bushy tail.
- The Wise Owl: A large barn owl with speckled feathers and knowing amber eyes.
- The Shadow Fox: A sleek black fox with glowing green eyes."

Director Agent: Here's the generated story [presents story]. Are you happy with it, or would you like me to make changes?

User: This looks great! Continue.

Director Agent: Excellent! Now I'll create the screenplay...

[Calls screenplay_agent]

Screenplay Agent:
EXT. FOREST CLEARING - DAY
Sammy, a small red squirrel, discovers a glowing golden acorn beneath an ancient oak tree.

SAMMY
(in awe)
I've never seen anything like this!

[Full screenplay in standard format]

Director Agent: Here's the screenplay [presents]. Does this capture the story well?

User: Perfect!

Director Agent: Great! Now I'll generate storyboards for each scene...

[Calls storyboard_agent with scene-by-scene processing]

Storyboard Agent:
[For Scene 1]
Calling storyboard_generate(
  prompt="in the style of a black and white comic book drawing, exterior forest clearing during day. A small, fluffy red squirrel with bright, curious eyes discovers a glowing golden acorn beneath ancient oak tree. The squirrel looks amazed.",
  scene_number=1
)

[Imagen4 generates image, saves to GCS]

Storyboard Agent: Generated storyboards:
1. https://storage.mtls.cloud.google.com/bucket/session_abc123/scene_1/image.png
2. https://storage.mtls.cloud.google.com/bucket/session_abc123/scene_2/image.png
[... more scenes]

Director Agent: Here are the storyboards [displays images]. Are these visually what you imagined?

User: Scene 2 doesn't match. The owl should look wiser.

Director Agent: I'll regenerate Scene 2...

[Calls storyboard_agent again with updated prompt]

User: Much better!

Director Agent: Fantastic! Now for the final step - video generation. This will take several minutes...

[Calls video_agent]

Video Agent:
[For each scene]
- Extracting dialogue from screenplay
- Adding dialogue to video prompt
- Calling Veo3 with storyboard reference
- Polling for completion (15s intervals)
- Returning GCS video URI

Video Agent: Generated videos:
1. https://storage.mtls.cloud.google.com/bucket/session_abc123/scene_1/video.mp4
2. https://storage.mtls.cloud.google.com/bucket/session_abc123/scene_2/video.mp4
[... all scenes]

Director Agent: Your movie is complete! [presents video links]

User: Amazing!

Director Agent: Congratulations on creating your campfire story movie! Would you like to create another?
```

**Example 2: Revision Request Mid-Pipeline**

```
User: Create a spooky story about a haunted tent.

[Story generation completes]

User: The story isn't scary enough. Add more suspense.

Director Agent: I'll work with the story team to add more suspense...

[Calls story_agent with feedback: "Make the story scarier with more suspenseful moments"]

[New story generated with enhanced tension]

Director Agent: Here's the revised story with increased suspense. Better?

User: Perfect! Continue.
```

**Example 3: Character-Focused Request**

```
User: I want three characters: a detective hedgehog, a sneaky raccoon, and a wise turtle. They solve a mystery.

Director Agent: Great character lineup! Let me create the story...

[Story Agent generates with all three characters, including detailed descriptions]

Story Agent Output:
Character Descriptions:
- Detective Herbert: A stout hedgehog with brown spines, wearing a tiny magnifying glass on a chain, with keen investigative eyes.
- Rascal the Raccoon: A mischievous raccoon with a black mask, nimble paws, and a sly grin.
- Wise Terrence: An ancient turtle with a weathered shell, calm demeanor, and spectacles perched on his nose.

[Pipeline continues, all visual agents use these descriptions for consistency]
```

### Testing and Evaluation

**Run All Tests**
```bash
make test
```

This executes (Makefile Line 34-35):
- Unit tests: `uv run pytest tests/unit`
- Integration tests: `uv run pytest tests/integration`

**Run Linting and Code Quality Checks**
```bash
make lint
```

This runs (Makefile Lines 38-43):
- **codespell**: Spell checking across codebase
- **ruff check**: Python linting (syntax, style violations)
- **ruff format**: Code formatting verification
- **mypy**: Static type checking

**Fix Formatting Issues**
```bash
uv run ruff format .
```

**Manual Testing Checklist**:
1. **Story Generation**:
   - Test various story concepts (adventure, mystery, comedy)
   - Verify character descriptions always included
   - Check narrative structure completeness

2. **Screenplay Formatting**:
   - Validate scene headings (INT/EXT format)
   - Verify dialogue formatting (character names, parentheticals)
   - Check action line present tense usage

3. **Storyboard Quality**:
   - Confirm black-and-white comic style
   - Verify character appearance matches descriptions
   - Check scene composition clarity

4. **Video Generation**:
   - Validate 8-second duration per clip
   - Verify dialogue audio matches screenplay
   - Check video quality and composition
   - Confirm 16:9 aspect ratio

5. **End-to-End Flow**:
   - Complete full pipeline without errors
   - Test revision requests at each stage
   - Verify GCS asset organization

### Deployment to Google Cloud

**Deploy to Cloud Run**

The Makefile includes a deployment target for Cloud Run:

```bash
# Ensure .env file is configured
make backend
```

**Deployment Details** (Makefile Lines 16-27):
- **Service Name**: `short-movie-agents`
- **Region**: `europe-west4` (configurable)
- **Memory**: 4GiB (high memory for video processing)
- **CPU**: No throttling (always-on for consistent performance)
- **Source Deploy**: Builds from source directory
- **Environment**: Loads all variables from `.env` file
- **Authentication**: Unauthenticated (public access) - change to `--no-allow-unauthenticated` for IAP
- **Labels**: `created-by=adk`, `dev-tutorial=sample-short-movie-agents`

**Deployment Steps**:

1. **Set Google Cloud Project**:
```bash
gcloud config set project YOUR_PROJECT_ID
```

2. **Verify .env Configuration**:
Ensure all required environment variables are set in `.env`.

3. **Deploy**:
```bash
make backend
```

4. **Custom Port** (optional):
```bash
make backend PORT=8080
```

5. **Monitor Deployment**:
```bash
# View logs
gcloud run services logs read short-movie-agents --region europe-west4

# Get service URL
gcloud run services describe short-movie-agents --region europe-west4 --format="value(status.url)"
```

**Post-Deployment**:
- Service URL will be printed at end of deployment
- Access ADK Web UI at the service URL
- Cloud Logging and Tracing automatically configured

**Optional: Enable Identity-Aware Proxy (IAP)**

For production deployments requiring authentication:
```bash
# Remove unauthenticated access
gcloud run services update short-movie-agents \
  --region europe-west4 \
  --no-allow-unauthenticated

# Configure IAP (follow Cloud Run IAP documentation)
```

### Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'google.adk'`
- **Cause**: Dependencies not installed or wrong Python version
- **Solution**: Run `make install` or `uv sync --dev`
- **Verify**: `uv run python -c "import google.adk; print(google.adk.__version__)"`

**Issue**: `ValueError: Model veo-3.0-generate-preview not found`
- **Cause**: Veo3 only available in `us-central1` region
- **Solution**: Set `GOOGLE_CLOUD_LOCATION=us-central1` in `.env`
- **Verify**: Check video_agent.py Line 34 for correct model location

**Issue**: `PermissionDenied: User does not have permission to access aiplatform`
- **Cause**: Vertex AI API not enabled or authentication issues
- **Solution 1**: Enable API: `gcloud services enable aiplatform.googleapis.com`
- **Solution 2**: Re-authenticate: `gcloud auth application-default login`
- **Solution 3**: Set quota project: `gcloud auth application-default set-quota-project YOUR_PROJECT_ID`

**Issue**: Storyboard/video generation fails with 403 Forbidden
- **Cause**: GCS bucket permissions or bucket doesn't exist
- **Solution**: Verify bucket exists: `gcloud storage buckets describe gs://YOUR_BUCKET_NAME`
- **Solution**: Grant access: `gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET_NAME --member="user:YOUR_EMAIL" --role="roles/storage.objectAdmin"`

**Issue**: "Server ready" message but can't select agent in UI
- **Cause**: Must select 'app' folder, not individual agent files
- **Solution**: In ADK Web dropdown, select the 'app' directory (see Makefile Line 10 note)

**Issue**: Video generation takes too long or times out
- **Cause**: Veo3 generation can take 1-2 minutes per 8-second clip
- **Expected**: For 5-scene story, expect 5-10 minutes total
- **Workaround**: Reduce number of scenes in screenplay or adjust polling interval (video_agent.py Line 98)

**Issue**: Character appearances inconsistent across scenes
- **Cause**: Character descriptions not detailed enough or not propagated
- **Solution**: Ensure Story Agent includes detailed visual descriptions
- **Verify**: Check session state contains 'story' with character list at end

**Issue**: Dialogue not in video audio
- **Cause**: Screenplay formatting doesn't match regex patterns
- **Solution**: Follow standard screenplay format in screenplay_agent.txt
- **Debug**: Check video_agent.py Lines 76-77 regex patterns match your screenplay

**Issue**: Python 3.13 not available on system
- **Cause**: Project requires exactly Python 3.13 (pyproject.toml Line 32)
- **Solution**: Install Python 3.13 from [python.org](https://www.python.org/downloads/)
- **Alternative**: Use `pyenv` to manage multiple Python versions:
  ```bash
  pyenv install 3.13.0
  pyenv local 3.13.0
  ```

**Issue**: Rate limits or quota errors
- **Cause**: Vertex AI models have quota limits
- **Solution**: Check quotas in Google Cloud Console > IAM & Admin > Quotas
- **Request Increase**: For production, request quota increase for Imagen4 and Veo3 models

## Customization Options

### 1. Change Story Theme and Persona

**Customization**: Modify the storytelling persona and narrative style

**Location**: `/home/user/adk-samples/python/agents/short-movie-agents/app/prompts/story_agent.txt`

**Example**: Change from Scout Leader campfire stories to nature documentary narrator

```text
# Original (Lines 1-3)
**Name:** Scout Leader

You are now speaking to young scouts gathered around a crackling fire.

# Modified
**Name:** Nature Documentary Narrator

You are David Attenborough narrating a nature documentary about wildlife.
Your tone should be authoritative yet warm, educational yet entertaining.

When responding to any query, you must present it as a nature documentary segment.
Each story should observe animals in their natural habitat, describing their behaviors,
adaptations, and ecological relationships. Use vivid sensory details: sights, sounds,
and movements of the natural world.

The narrative must include:
- **Opening**: Establish the setting (habitat, season, time of day)
- **Observation**: Introduce the animal subjects and their current activity
- **Challenge**: Present a survival challenge or behavioral pattern
- **Resolution**: Show how the animals adapt or overcome

**Character Descriptions:**
At the end, provide a scientific description of each animal species featured, including
distinguishing physical characteristics and ecological role.
```

Then update other prompts to maintain consistency (e.g., screenplay should reference documentary style).

### 2. Adjust Storyboard Visual Style

**Customization**: Generate storyboards in different artistic styles

**Location**: `/home/user/adk-samples/python/agents/short-movie-agents/app/prompts/storyboard_agent.txt` (Line 25)

**Example**: Change from black-and-white comics to watercolor concept art

```text
# Original (Line 25)
"**in the style of a black and white comic book drawing**, **a storyboard**, **sketch**, or **line art**"

# Modified for watercolor
"**in the style of a watercolor painting**, **soft colors**, **artistic concept art**, **gentle brush strokes**"

# Or for cinematic realism
"**in the style of a cinematic film frame**, **photorealistic**, **professional cinematography**, **movie still**"

# Or for children's book illustration
"**in the style of a children's book illustration**, **colorful and whimsical**, **hand-drawn art**, **friendly and approachable**"
```

Also update the aspect ratio in `storyboard_agent.py` Line 76 if needed:
```python
# Original: 1:1 square
aspect_ratio="1:1",

# Modified for widescreen
aspect_ratio="16:9",
```

### 3. Modify Video Duration and Count

**Customization**: Generate longer or shorter video clips, or change number of clips

**Location**: `/home/user/adk-samples/python/agents/short-movie-agents/app/video_agent.py` (Line 92)

**Example**: Increase video duration to 15 seconds per scene

```python
# Original (Line 92)
duration_seconds=8,

# Modified
duration_seconds=15,  # Veo3 supports up to 15 seconds
```

**Change number of video variations** (Line 91):
```python
# Original: 1 video per scene
number_of_videos=1,

# Modified: Generate 3 alternatives per scene for selection
number_of_videos=3,
```

**Note**: Longer duration and multiple videos significantly increase generation time and costs.

### 4. Add Scene Transitions and Editing Instructions

**Customization**: Include editing notes in screenplay for post-production

**Location**: `/home/user/adk-samples/python/agents/short-movie-agents/app/prompts/screenplay_agent.txt`

**Example**: Add transition instructions between scenes

```text
# Add to screenplay structure section (after Line 19)

* **Transitions:** Use standard screenplay transitions between scenes:
  - FADE IN: / FADE OUT: - for beginning and ending
  - CUT TO: - for immediate scene changes
  - DISSOLVE TO: - for time passage or mood shift
  - MATCH CUT TO: - for visual continuity between scenes

# Example output with transitions:

FADE IN:

EXT. FOREST - DAY

[Scene content]

DISSOLVE TO:

INT. CAVE - NIGHT

[Scene content]

CUT TO:

EXT. MOUNTAIN PEAK - SUNRISE

[Scene content]

FADE OUT.
```

### 5. Implement Multi-Language Story Generation

**Customization**: Support story creation in different languages

**Location**: Multiple files - director_agent.txt, story_agent.txt, and agent.py

**Example**: Add Spanish language support

**Step 1**: Modify director agent prompt (`app/prompts/director_agent.txt`):
```text
# Add to Primary Objective (Line 3):
**Language Support:** Ask the user for their preferred language (English or Spanish).
All story content will be generated in the selected language.

# Add to Step 1 (after Line 9):
    * Ask which language they prefer: English (EN) or Spanish (ES).
    * Remember this choice for all subsequent agent calls.
```

**Step 2**: Create language-specific story prompts:

Create `app/prompts/story_agent_es.txt`:
```text
**Nombre:** Líder Scout

Estás hablando con jóvenes scouts reunidos alrededor de una fogata crepitante.

Por lo tanto, al responder cualquier consulta, debes encarnar completamente la persona de un Líder Scout amigable y atractivo. Tu tono debe ser cálido, entusiasta y un poco misterioso.

Cada historia debe tener un **comienzo** claro, **acción ascendente**, **clímax** y **resolución**.

**Descripciones de Personajes:**
Al final de la historia, DEBES proporcionar una lista de todos los personajes con una breve descripción de una oración de su apariencia.
```

**Step 3**: Update Story Agent to load appropriate prompt (`app/story_agent.py`):
```python
# Add language parameter (requires modifying agent architecture)
def create_story_agent(language="en"):
    prompt_file = "story_agent.txt" if language == "en" else "story_agent_es.txt"
    story_agent = Agent(
        model=MODEL,
        name="story_agent",
        description=load_prompt_from_file("story_agent_desc.txt"),
        instruction=load_prompt_from_file(prompt_file),
        output_key="story",
    )
    return story_agent
```

**Step 4**: Director agent passes language context in delegation (requires ADK features for parameter passing).

### 6. Add Background Music and Sound Effects

**Customization**: Enhance videos with audio layers beyond dialogue

**Location**: `/home/user/adk-samples/python/agents/short-movie-agents/app/video_agent.py` (video_generate function)

**Example**: Add background music and ambient sounds to video prompts

```python
# Modify Lines 75-80 in video_generate function

# Original
if dialogue:
    prompt += f"\n\nAudio:\n{dialogue}"

# Modified
if dialogue:
    prompt += f"\n\nAudio:\n{dialogue}"

# Add ambient sounds based on scene
if "FOREST" in screenplay.upper():
    prompt += "\n\nBackground: Birds chirping, rustling leaves, gentle wind"
elif "CAVE" in screenplay.upper():
    prompt += "\n\nBackground: Dripping water, echoing sounds, mysterious ambiance"
elif "BEACH" in screenplay.upper():
    prompt += "\n\nBackground: Ocean waves, seagulls, gentle breeze"

# Add music mood
if scene_number == 1:  # Opening scene
    prompt += "\n\nMusic: Gentle, mysterious orchestral music with soft strings"
else:
    prompt += "\n\nMusic: Adventurous orchestral score matching the scene mood"
```

### 7. Create Custom Agent for Script Editing

**Customization**: Add a fifth agent for editing and refining screenplays

**Location**: Create new file `/home/user/adk-samples/python/agents/short-movie-agents/app/editor_agent.py`

**Example**: Script editor agent that reviews and enhances screenplays

```python
# Copyright 2025 Google LLC
# [License header]

import logging
from google.adk.agents import Agent
from .utils.utils import load_prompt_from_file

logger = logging.getLogger(__name__)

# Configuration
MODEL = "gemini-2.5-flash"
DESCRIPTION = "Agent responsible for editing and refining screenplays for clarity and impact"

# --- Editor Agent ---
editor_agent = None
try:
    editor_agent = Agent(
        model=MODEL,
        name="editor_agent",
        description=DESCRIPTION,
        instruction=load_prompt_from_file("editor_agent.txt"),
        output_key="edited_screenplay",
    )
    logger.info(f"✅ Agent '{editor_agent.name}' created using model '{MODEL}'.")
except Exception as e:
    logger.error(f"❌ Could not create Editor agent. Error: {e}")
```

Create `app/prompts/editor_agent.txt`:
```text
**Role:** Screenplay Editor

**Primary Objective:** Review and enhance screenplays for cinematic quality, pacing, and visual storytelling.

**Core Tasks:**

1. **Retrieve Screenplay:** Access the session state and retrieve the screenplay under the key 'screenplay'.

2. **Analyze and Improve:**
   * **Pacing**: Ensure scene lengths are balanced and narrative flows smoothly
   * **Visual Descriptions**: Enhance action lines with more vivid, cinematic details
   * **Dialogue**: Tighten dialogue for impact, remove redundancy
   * **Character Voice**: Ensure each character has distinct speaking style
   * **Scene Transitions**: Add or improve transition instructions
   * **Clarity**: Remove ambiguous directions, specify camera angles when helpful

3. **Preserve Intent:** Maintain the original story's tone, plot, and character arcs.

4. **Output:** Return the edited screenplay in standard format.
```

Then update `app/agent.py` to include in sub-agents list:
```python
from .editor_agent import editor_agent

# Add to sub_agents (Line 40)
sub_agents=[story_agent, screenplay_agent, editor_agent, storyboard_agent, video_agent]
```

Update director prompt to include editing step between screenplay and storyboard.

### 8. Batch Processing Multiple Stories

**Customization**: Create a batch mode to generate multiple stories from a list

**Location**: Create new file `/home/user/adk-samples/python/agents/short-movie-agents/app/batch_processor.py`

**Example**: Process multiple story concepts in sequence

```python
# Copyright 2025 Google LLC
# [License header]

import asyncio
from typing import List, Dict
from google.adk.agents import Agent
from .agent import root_agent

async def batch_process_stories(
    story_concepts: List[Dict[str, str]]
) -> List[Dict[str, any]]:
    """
    Process multiple story concepts through the full pipeline.

    Args:
        story_concepts: List of dicts with 'title' and 'concept' keys

    Returns:
        List of dicts with generated assets for each story
    """
    results = []

    for i, concept in enumerate(story_concepts):
        print(f"\n{'='*60}")
        print(f"Processing story {i+1}/{len(story_concepts)}: {concept['title']}")
        print(f"{'='*60}\n")

        try:
            # Create new session for each story
            session_result = await root_agent.run_async(
                user_message=f"Create a campfire story about: {concept['concept']}"
            )

            results.append({
                "title": concept["title"],
                "status": "success",
                "story": session_result.get("story"),
                "screenplay": session_result.get("screenplay"),
                "storyboards": session_result.get("storyboard"),
                "videos": session_result.get("video"),
            })

            print(f"✅ Successfully generated: {concept['title']}")

        except Exception as e:
            print(f"❌ Failed to generate: {concept['title']} - Error: {e}")
            results.append({
                "title": concept["title"],
                "status": "error",
                "error": str(e)
            })

    return results


# Example usage
if __name__ == "__main__":
    story_ideas = [
        {
            "title": "The Brave Squirrel",
            "concept": "A squirrel who overcomes fear to save the forest"
        },
        {
            "title": "The Mysterious Cave",
            "concept": "Scouts discover ancient cave paintings with a hidden message"
        },
        {
            "title": "The Helpful Hedgehog",
            "concept": "A hedgehog teaches scouts about kindness and cooperation"
        },
    ]

    results = asyncio.run(batch_process_stories(story_ideas))

    # Print summary
    print(f"\n{'='*60}")
    print("BATCH PROCESSING COMPLETE")
    print(f"{'='*60}")
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {result['title']}: {result['status']}")
```

Run with: `uv run python app/batch_processor.py`

---

**Report Generated**: 2025-11-19
**ADK Version**: 1.14.0
**Primary Model**: Gemini 2.5 Flash
**Specialized Models**: Imagen4 Ultra, Veo3 Preview
**Architecture Pattern**: Hierarchical Multi-Agent with Sequential Delegation
**Production Status**: Demo/Sample (requires customization for production use)
