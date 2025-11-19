# Podcast Transcript Agent - Technical Documentation Report

## Project Scope

The Podcast Transcript Agent is an intelligent content repurposing system that transforms written documents (PDFs, Markdown, text files) into engaging podcast transcripts. It demonstrates a sequential multi-agent architecture where each agent performs a specialized task in a pipeline.

### Core Capabilities
- Automated topic extraction from source documents (PDFs, Markdown, plain text)
- Intelligent episode planning with structured segments
- Natural conversational script generation between host and expert personas
- Structured output using Pydantic schemas for type safety
- Multi-modal document processing with ADK file handling
- End-to-end pipeline from document upload to complete podcast transcript

### Primary Use Cases
- Content creators repurposing blog posts, articles, or research papers into podcast episodes
- Educational institutions converting lecture notes or textbooks into audio-friendly formats
- Marketing teams transforming whitepapers into conversational content
- Publishers creating podcast series from written content libraries
- Researchers making academic papers more accessible through audio format

### Target Users
- Podcast producers and content creators
- Marketing and communications teams
- Educational content developers
- Technical writers exploring new content formats
- Developers learning sequential agent architectures

### Key Innovations/Differentiators
- **Sequential agent architecture**: Clean pipeline design with clear input/output contracts
- **Structured output schemas**: Type-safe data flow using Pydantic models
- **Persona-based generation**: Configurable host and expert characters for authentic dialogue
- **Segment-level structuring**: Organized transcript with timestamps and clear sections
- **Zero-configuration simplicity**: Works out-of-box with minimal setup
- **Fast model usage**: Leverages `gemini-2.5-flash` for quick, cost-effective generation

## Technical Architecture

### Multi-Agent Hierarchy

The Podcast Transcript Agent uses a **SequentialAgent** pattern where sub-agents execute in a strict order, each transforming the output of the previous agent:

```
┌────────────────────────────────────────────────────────────┐
│           podcast_transcript_agent (Root)                  │
│           Type: SequentialAgent                            │
│           File: podcast_transcript_agent/agent.py (22-30)  │
└─────┬──────────────────────────────────────────────────────┘
      │
      │  Sequential Pipeline (no branching)
      │
      ▼
┌─────────────────────────────────────────┐
│    Step 1: podcast_topics_agent         │
│    ────────────────────────────────     │
│    Input: Source document (PDF/txt/md)  │
│    Output: PodcastTopics                │
│      - main_topic (str)                 │
│      - sub_topics (List[Topic])         │
│    File: sub_agents/podcast_topics/     │
│          agent.py (lines 19-26)         │
└─────┬───────────────────────────────────┘
      │
      │  output_key: "podcast_topics"
      │
      ▼
┌──────────────────────────────────────────────┐
│    Step 2: podcast_episode_planner_agent     │
│    ───────────────────────────────────────   │
│    Input: PodcastTopics from Step 1          │
│    Output: PodcastEpisodePlan                │
│      - episode_title (str)                   │
│      - speakers (List[PodcastSpeaker])       │
│      - segments (List[Segment])              │
│    File: sub_agents/podcast_episode_planner/ │
│          agent.py (lines 20-27)              │
└─────┬────────────────────────────────────────┘
      │
      │  output_key: "podcast_episode_plan"
      │
      ▼
┌──────────────────────────────────────────────┐
│   Step 3: podcast_transcript_writer_agent    │
│   ────────────────────────────────────────   │
│   Input: PodcastEpisodePlan + PodcastTopics  │
│   Output: PodcastTranscript                  │
│     - metadata (PodcastMetadata)             │
│     - speakers (List[PodcastSpeaker])        │
│     - segments (List[PodcastSegment])        │
│   File: sub_agents/                          │
│         podcast_transcript_writer/           │
│         agent.py (lines 19-26)               │
└─────┬────────────────────────────────────────┘
      │
      ▼
   Final Transcript
   (JSON with full dialogue)
```

### Code Flow Explanation

**1. Entry Point and Sequential Orchestration** (`podcast_transcript_agent/agent.py`, lines 22-30)

```python
podcast_transcript_agent = SequentialAgent(
    name="podcast_transcript_agent",
    description="Executes a sequence of podcast generation steps",
    sub_agents=[
        podcast_topics_agent,
        podcast_episode_planner_agent,
        podcast_transcript_writer_agent,
    ],
)
```

- `SequentialAgent` executes sub-agents in array order
- Each agent's output becomes available to subsequent agents
- No parallel execution - strictly sequential pipeline
- Root agent designated as `root_agent` (line 32)

**2. Step 1: Topic Extraction** (`sub_agents/podcast_topics/agent.py`, lines 19-26)

The first agent analyzes the input document and extracts structured topic information.

**Agent Definition**:
```python
podcast_topics_agent = Agent(
    name="podcast_topics_agent",
    model="gemini-2.5-flash",
    description="Extracts podcast topics from provided input",
    instruction=prompt.TOPIC_EXTRACTION_PROMPT,
    output_schema=PodcastTopics,
    output_key="podcast_topics"
)
```

**Prompt Strategy** (`sub_agents/podcast_topics/prompt.py`, lines 15-40):
- Acts as "expert research analyst"
- Identifies main topic and central argument
- Extracts 5 most important subtopics (avoiding generic sections like "Introduction")
- For each subtopic: title, 2-paragraph summary, key statistics/data
- Returns structured JSON matching `PodcastTopics` schema

**Output Schema** (`models/podcast_topics.py`, lines 18-27):
```python
class Topic(BaseModel):
    topic_name: str
    description: str
    key_facts: list[str]

class PodcastTopics(BaseModel):
    main_topic: str
    sub_topics: List[Topic]
```

**Data Flow**:
- Input: User-uploaded document (PDF, Markdown, or text)
- Processing: Gemini analyzes content, extracts key information
- Output: Stored in context with key `"podcast_topics"`
- Next agent receives this structured data automatically

**3. Step 2: Episode Planning** (`sub_agents/podcast_episode_planner/agent.py`, lines 20-27)

The planner transforms extracted topics into a structured episode outline.

**Agent Definition**:
```python
podcast_episode_planner_agent = Agent(
    name="podcast_episode_planner_agent",
    model="gemini-2.5-flash",
    description="Plans the podcast episode based on extracted topics",
    instruction=prompt.PODCAST_EPISODE_PLANNER_PROMPT,
    output_schema=PodcastEpisodePlan,
    output_key="podcast_episode_plan"
)
```

**Prompt Strategy** (`sub_agents/podcast_episode_planner/prompt.py`, lines 15-31):
- Acts as "podcast producer"
- Creates 5-segment outline with:
  1. Catchy episode title
  2. Introduction (host introduces topic and expert)
  3. Five main segments (logical progression)
  4. Conclusion (summary and final thought)
- Defines host and expert personas
- Ensures segments flow logically from one to next

**Output Schema** (`models/podcast_plan.py`, lines 19-28):
```python
class Segment(BaseModel):
    title: str
    script_points: List[str]

class PodcastEpisodePlan(BaseModel):
    episode_title: str
    speakers: List[PodcastSpeaker]
    segments: List[Segment]
```

**Data Flow**:
- Input: `PodcastTopics` from Step 1 (accessed from context)
- Processing: Organizes topics into coherent episode structure
- Output: Stored with key `"podcast_episode_plan"`
- Includes speaker definitions for next step

**4. Step 3: Transcript Writing** (`sub_agents/podcast_transcript_writer/agent.py`, lines 19-26)

The writer generates the full conversational script.

**Agent Definition**:
```python
podcast_transcript_writer_agent = Agent(
    name="podcast_transcript_writer_agent",
    model="gemini-2.5-flash",
    description="Writes the podcast transcript based on the podcast plan",
    instruction=prompt.PODCAST_TRANSCRIPT_WRITER_PROMPT,
    output_schema=PodcastTranscript,
    output_key="podcast_episode_transcript"
)
```

**Prompt Strategy** (`sub_agents/podcast_transcript_writer/prompt.py`, lines 15-39):
- Acts as "creative scriptwriter"
- Defines two personas:
  - **Host**: Friendly, curious, engaging, asks clarifying questions
  - **Expert**: Authoritative, knowledgeable, passionate (facts from topics only)
- Strictly follows Episode Plan structure
- Ensures expert claims derived from Podcast Topics (no hallucination)
- Formats with clear speaker labels (e.g., "Host (Ben):", "Expert (Dr. Sponge):")
- Injects both `podcast_episode_plan` and `podcast_topics` into prompt (lines 34-38)

**Output Schema** (`models/podcast_transcript.py`, lines 19-48):
```python
class SpeakerDialogue(BaseModel):
    speaker_id: str
    text: str

class PodcastSegment(BaseModel):
    segment_title: str
    title: str
    start_time: float
    end_time: float
    speaker_dialogues: List[SpeakerDialogue]

class PodcastSpeaker(BaseModel):
    speaker_id: str
    name: str
    role: str

class PodcastMetadata(BaseModel):
    episode_title: str
    duration_seconds: int
    summary: str

class PodcastTranscript(BaseModel):
    metadata: PodcastMetadata
    speakers: List[PodcastSpeaker]
    segments: List[PodcastSegment]
```

**Data Flow**:
- Input: Both `PodcastTopics` and `PodcastEpisodePlan` from previous steps
- Processing: Generates natural dialogue between host and expert
- Output: Complete transcript with metadata, speakers, timestamped segments
- Final result returned to user

### Agent Definitions with Roles and Responsibilities

| Agent Name | Role | Responsibilities | Input | Output | File Location |
|------------|------|------------------|-------|--------|---------------|
| **podcast_transcript_agent** | Pipeline Orchestrator | - Execute agents sequentially<br>- Pass outputs between steps<br>- Manage overall workflow | User document | Complete transcript | `agent.py` (lines 22-30) |
| **podcast_topics_agent** | Research Analyst | - Extract main topic<br>- Identify 5 key subtopics<br>- Gather supporting facts/data<br>- Avoid generic sections | PDF/Markdown/Text | PodcastTopics schema | `sub_agents/podcast_topics/agent.py` (lines 19-26) |
| **podcast_episode_planner_agent** | Content Strategist | - Create episode title<br>- Structure 5 segments<br>- Define speaker personas<br>- Plan introduction/conclusion | PodcastTopics | PodcastEpisodePlan schema | `sub_agents/podcast_episode_planner/agent.py` (lines 20-27) |
| **podcast_transcript_writer_agent** | Scriptwriter | - Write natural dialogue<br>- Maintain persona consistency<br>- Add timestamps<br>- Create engaging conversation | PodcastTopics + PodcastEpisodePlan | PodcastTranscript schema | `sub_agents/podcast_transcript_writer/agent.py` (lines 19-26) |

### Key Libraries and Dependencies

From `pyproject.toml` (lines 6-17):

| Library | Version | Purpose |
|---------|---------|---------|
| **google-adk** | >=1.14.1 | Core ADK framework for agent development and SequentialAgent |
| **google-generativeai** | >=0.8.5 | Gemini API client for model interactions |
| **pydantic** | >=2.11.9 | Data validation and schema definitions for structured outputs |
| **fastapi** | >=0.117.1 | Web framework for API server mode |
| **uvicorn** | >=0.36.0 | ASGI server for running FastAPI |
| **python-dotenv** | >=1.1.1 | Environment variable management from .env files |
| **dotenv** | >=0.9.9 | Alternative dotenv loader |
| **pytest** | >=8.4.2 | Testing framework |
| **pytest-asyncio** | >=1.2.0 | Async support for pytest |

**Python Requirement**: >=3.13 (line 6)

**Package Manager**: uv (recommended for fast dependency resolution)

### Tools and Integrations

**Built-in ADK Capabilities**:

1. **File Upload Support**
   - Web UI includes paperclip icon for file attachment
   - Supports PDF, Markdown (.md), and plain text (.txt)
   - Automatic file content extraction and parsing
   - No custom file handling tools needed - ADK handles it

2. **Structured Output via Pydantic**
   - All agents use `output_schema` parameter
   - Gemini generates valid JSON matching Pydantic models
   - Type safety and validation built-in
   - Automatic serialization/deserialization

3. **Sequential Agent Framework**
   - `SequentialAgent` class from google.adk.agents
   - Automatic context passing between agents
   - Output keys enable data retrieval by subsequent agents
   - No manual state management required

**External Integrations**:

- **Google Gemini API**: Primary LLM for all three agents
- **Vertex AI** (optional): Alternative backend via environment variables
- **Google Cloud Storage** (optional): For storing generated transcripts at scale

**No Custom Tools**: Unlike FOMC Research Agent, this agent doesn't require custom tools. All functionality achieved through:
- Agent prompts
- Pydantic schemas
- Sequential execution
- ADK's built-in file handling

### Reasoning Mechanisms

**1. Schema-Driven Output**
- Each agent has strict `output_schema` parameter
- Gemini must generate valid JSON matching Pydantic models
- Validation happens automatically before passing to next agent
- Prevents hallucination and ensures structural consistency

**2. Context Propagation**
- Sequential agents share context automatically
- `output_key` parameter makes data accessible by name
- Later agents reference earlier outputs (e.g., prompt.py line 34-38 injects previous outputs)
- Implicit data flow - no explicit passing needed

**3. Prompt Chaining Strategy**
- Each prompt builds on previous agent's output
- Topic agent: Extract information
- Planner agent: Organize information
- Writer agent: Generate content from organized information
- Progressively more creative tasks in pipeline

**4. Persona Consistency**
- Planner defines speaker personas in output
- Writer receives persona definitions and maintains them
- Structured dialogue format enforces consistency
- Speaker IDs link dialogues to personas

## Build & Run Instructions

### Prerequisites

**Required Software**:
- Python 3.13 or higher (specified in `pyproject.toml` line 6)
- `uv` package manager (recommended) OR `pip`
- Git (for cloning repository)

**Required Accounts**:
- **Option A**: Google Gemini API key (free tier available)
  - Get key from: https://ai.google.dev/
- **Option B**: Google Cloud Project with Vertex AI enabled
  - Requires: GCP project, billing enabled, Vertex AI API enabled

**No Additional Services Required**:
- No database setup
- No BigQuery configuration
- No cloud storage buckets
- Simple, self-contained agent

### Step-by-Step Installation

**1. Clone Repository**
```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/podcast_transcript_agent
```

**2. Create Virtual Environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**3. Install Dependencies**

**Option A: Using `uv` (Recommended - Fast)**
```bash
# Install uv if not already installed
pip install uv

# Sync dependencies
uv sync
```

**Option B: Using `pip`**
```bash
pip install -e .
```

This installs all dependencies from `pyproject.toml`, including:
- google-adk >=1.14.1
- google-generativeai >=0.8.5
- pydantic >=2.11.9
- All other required packages

### Configuration (Environment Variables)

**1. Create `.env` File**

Create a `.env` file in the project root:

**Option A: Using Vertex AI (Recommended for production)**
```bash
# .env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
GOOGLE_CLOUD_LOCATION="us-central1"
```

Then authenticate with gcloud:
```bash
gcloud auth application-default login
```

**Option B: Using Gemini API (Quickstart)**
```bash
# .env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY="your-api-key-here"
```

Get API key from: https://ai.google.dev/

**2. Verify Configuration**
```bash
# Check environment variables loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Vertex AI:', os.getenv('GOOGLE_GENAI_USE_VERTEXAI')); print('Project:', os.getenv('GOOGLE_CLOUD_PROJECT'))"
```

### Running the Agent

#### Method 1: Web Interface (Recommended for Interactive Use)

**1. Start Web UI**
```bash
adk web
```

**Expected Output**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**2. Open Browser**
- Navigate to: `http://127.0.0.1:8000`
- UI loads with chat interface

**3. Upload Document**
- Click paperclip icon 📎 in chat input area
- Select PDF, Markdown, or text file
- File uploads automatically

**4. Send Prompt**
```
Please create a podcast transcript from this document.
```

**5. Monitor Progress**
- See real-time agent execution
- Each step displays its output
- Final transcript appears as structured JSON

#### Method 2: API Server (Programmatic Access)

**1. Start API Server**
```bash
adk api-server
```

**Expected Output**:
```
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
```

**2. Send Request via Script**

Using provided test script:
```bash
cd tests
./run_with_txt.sh
```

**Script Contents** (`tests/run_with_txt.sh`):
```bash
#!/bin/bash
# Sends test_pyramid.txt to agent via API

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "message": "Create a podcast transcript from this content.",
  "files": [
    {
      "name": "test_pyramid.txt",
      "content": "$(cat tests/test_artifacts/test_pyramid.txt | base64)"
    }
  ]
}
EOF
```

**3. Check Response**
```bash
# Output saved to test_response.json
cat test_response.json | jq .
```

### Example Interactions

**Example 1: Simple Text Document**

**Input** (via Web UI):
```
User: [Uploads test_pyramid.txt]
User: Create a podcast about this testing concept.
```

**Agent Execution Flow**:
```
[podcast_topics_agent] Extracting topics...
Output:
{
  "main_topic": "The Testing Pyramid in Software Development",
  "sub_topics": [
    {
      "topic_name": "Unit Testing Foundation",
      "description": "Unit tests form the base of the pyramid...",
      "key_facts": [
        "Fastest to execute",
        "Test individual components in isolation",
        "Should comprise 70% of test suite"
      ]
    },
    // ... 4 more subtopics
  ]
}

[podcast_episode_planner_agent] Creating episode plan...
Output:
{
  "episode_title": "Building Better Software: The Testing Pyramid Explained",
  "speakers": [
    {"speaker_id": "host", "name": "Ben", "role": "Host"},
    {"speaker_id": "expert", "name": "Dr. Sarah Chen", "role": "Software Testing Expert"}
  ],
  "segments": [
    {
      "title": "Introduction to Testing Pyramid",
      "script_points": [
        "Welcome and introduce topic",
        "Explain why testing matters",
        "Introduce expert"
      ]
    },
    // ... 4 more segments
  ]
}

[podcast_transcript_writer_agent] Writing transcript...
Output:
{
  "metadata": {
    "episode_title": "Building Better Software: The Testing Pyramid Explained",
    "duration_seconds": 1800,
    "summary": "Join host Ben and testing expert Dr. Sarah Chen..."
  },
  "speakers": [...],
  "segments": [
    {
      "segment_title": "Introduction",
      "start_time": 0.0,
      "end_time": 180.0,
      "speaker_dialogues": [
        {
          "speaker_id": "host",
          "text": "Welcome to Tech Talks! I'm your host, Ben, and today we're diving into a crucial concept in software development: the Testing Pyramid. Joining me is Dr. Sarah Chen, a renowned expert in software quality assurance. Welcome, Sarah!"
        },
        {
          "speaker_id": "expert",
          "text": "Thanks for having me, Ben! I'm excited to break down this fundamental testing strategy."
        },
        // ... conversation continues
      ]
    },
    // ... more segments
  ]
}
```

**Example 2: PDF Research Paper**

**Input**:
```
User: [Uploads "machine_learning_paper.pdf"]
User: Transform this research paper into a podcast transcript. Focus on making it accessible to non-experts.
```

**Result**:
- Topics agent extracts: research question, methodology, key findings, implications, future work
- Planner creates: catchy title, intro explaining context, 5 segments covering main points, conclusion
- Writer generates: conversational dialogue where expert explains complex concepts in simple terms, host asks clarifying questions

**Example 3: Markdown Blog Post**

**Input**:
```
User: [Uploads "kubernetes_guide.md"]
User: Create a podcast episode from this Kubernetes tutorial.
```

**Agent Output**:
- Episode title: "Kubernetes Simplified: A Beginner's Journey"
- 5 segments: What is K8s, Core concepts, Deployment basics, Troubleshooting, Best practices
- Natural host-expert dialogue with examples from original tutorial

### Testing and Evaluation

**Run Unit Tests**
```bash
# Activate virtual environment
source .venv/bin/activate

# Run pytest
pytest tests/test_agents.py -v
```

**Test Files** (`tests/test_agents.py`):
Contains tests for each agent in isolation and full pipeline tests.

**Test Artifacts** (`tests/test_artifacts/`):
- `test_pyramid.txt`: Sample testing pyramid concept document
- Use for manual testing and validation

**Manual Testing Checklist**:
1. ✅ Upload PDF - verify extraction works
2. ✅ Upload Markdown - verify formatting preserved
3. ✅ Upload plain text - verify processing
4. ✅ Check topic quality - relevant, non-generic
5. ✅ Check episode structure - 5 segments, logical flow
6. ✅ Check dialogue quality - natural, persona-consistent
7. ✅ Verify timestamps - segments have start/end times
8. ✅ Check JSON validity - output parses correctly

**Quality Metrics**:
- **Topic Relevance**: All subtopics should relate to main topic
- **Episode Coherence**: Segments flow logically
- **Dialogue Naturalness**: Conversation sounds realistic
- **Fact Accuracy**: Expert statements match source document
- **Persona Consistency**: Host/expert maintain their roles throughout

### Deployment (Optional)

**Local Production Deployment**

Run as background service:
```bash
# Using systemd (Linux)
sudo tee /etc/systemd/system/podcast-agent.service > /dev/null <<EOF
[Unit]
Description=Podcast Transcript Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/path/to/podcast_transcript_agent
Environment="PATH=/path/to/.venv/bin"
ExecStart=/path/to/.venv/bin/adk api-server
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable podcast-agent
sudo systemctl start podcast-agent
```

**Cloud Deployment**

Deploy to Google Cloud Run:
```bash
# Create Dockerfile
cat > Dockerfile <<EOF
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD ["adk", "api-server", "--host", "0.0.0.0", "--port", "8080"]
EOF

# Build and deploy
gcloud run deploy podcast-transcript-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=TRUE \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID
```

### Troubleshooting

**Issue: "Module not found" errors**

**Cause**: Dependencies not installed or virtual environment not activated

**Solution**:
```bash
# Ensure virtual environment activated
source .venv/bin/activate

# Reinstall dependencies
uv sync
# OR
pip install -e .
```

**Issue: "Authentication failed" with Vertex AI**

**Cause**: Missing or expired Google Cloud credentials

**Solutions**:
```bash
# Re-authenticate
gcloud auth application-default login

# Verify credentials
gcloud auth application-default print-access-token

# Check .env file
cat .env | grep GOOGLE_CLOUD
```

**Issue: "File upload not working" in Web UI**

**Cause**: Browser compatibility or large file size

**Solutions**:
1. Try different browser (Chrome recommended)
2. Check file size (< 10MB recommended)
3. Verify file format (PDF, .md, .txt only)
4. Check browser console for JavaScript errors

**Issue: Poor quality topics extracted**

**Cause**: Source document lacks structure or detail

**Solutions**:
- Provide more detailed source documents
- Ensure document has clear sections and information
- Customize topic extraction prompt (see Customization section)
- Try with different document formats

**Issue: Generated dialogue sounds unnatural**

**Cause**: Prompt may need adjustment for your content type

**Solutions**:
- Customize speaker personas in prompt (see Customization section)
- Adjust the formality level in writer prompt
- Add examples of desired dialogue style
- Provide more context in episode planning prompt

**Issue: "Output schema validation failed"**

**Cause**: Gemini generated invalid JSON structure

**Solutions**:
```bash
# Enable debug logging
export GOOGLE_GENAI_LOG_LEVEL=DEBUG

# Run again and check logs
adk web

# If persistent, simplify output schema or provide examples in prompt
```

**Issue: Slow execution**

**Cause**: Using slower model or network latency

**Solutions**:
- Verify using `gemini-2.5-flash` (fast model)
- Check network connection
- Consider using Vertex AI for better performance
- Monitor token usage and adjust input size

**Issue: Tests failing**

**Cause**: Missing test dependencies or environment variables

**Solutions**:
```bash
# Install test dependencies
uv sync --all-extras

# Set test environment variables
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT=test-project

# Run with verbose output
pytest tests/test_agents.py -v -s
```

## Customization Options

### 1. Customize Speaker Personas

**Location**: `podcast_transcript_agent/sub_agents/podcast_transcript_writer/prompt.py`

**Current Default** (lines 19-24):
```python
**Personas:**
* **Host:** Friendly, curious, and engaging. Asks clarifying questions and acts
  as the voice of the audience. Keeps the conversation moving.
* **Expert:** The authority on the topic. Articulate, knowledgeable, and
  passionate. Their statements must be based on the "Factual Information"
  provided.
```

**Customization Example - Tech Podcast Style**:

Edit `prompt.py` lines 19-24:
```python
**Personas:**
* **Host (Alex Chen):** Experienced developer with 10 years in industry.
  Skeptical but open-minded. Asks tough technical questions. Occasionally
  interjects with personal anecdotes. Uses developer jargon comfortably.

* **Expert (Dr. Jamie Rodriguez):** Computer Science professor and researcher.
  Academic but approachable. Uses analogies to explain complex concepts.
  Excited about cutting-edge developments. Tends to dive deep into details
  when passionate about a topic.

* **Sound:** Include natural conversational elements:
  - Thoughtful pauses: "[pause]"
  - Laughter: "[laughs]"
  - Emphasis: "*word*" for stressed words
```

**Customization Example - Educational Podcast**:
```python
**Personas:**
* **Host (Teacher Sarah):** Elementary school teacher explaining concepts
  to adult beginners. Patient, encouraging, uses simple language.
  Frequently checks for understanding. Uses everyday analogies.

* **Expert (Professor Mike):** Subject matter expert who loves teaching.
  Breaks down complex ideas into digestible chunks. Uses the Socratic
  method - asks the host questions to guide discovery. Provides
  historical context and real-world applications.
```

**Use Cases**:
- Match podcast style to target audience
- Create branded podcast characters
- Adjust formality level (casual vs. professional)
- Add personality traits for authenticity

### 2. Adjust Episode Structure

**Location**: `podcast_transcript_agent/sub_agents/podcast_episode_planner/prompt.py`

**Current Default** (lines 15-31): 5-segment structure

**Customization Example - Longer Episodes**:

Edit `prompt.py`:
```python
PODCAST_EPISODE_PLANNER_PROMPT = """
You are a podcast producer. Using the provided summary and key points, create a
high-level, 10-segment outline for a LONG-FORM podcast episode (60-90 minutes).
The podcast features a host and an expert.

The outline should include:
1.  **Episode Title and Tagline:** A catchy title and one-sentence hook.
2.  **Cold Open (2 min):** Intriguing question or statistic to grab attention.
3.  **Introduction (5 min):** Host introduces topic, expert, and episode goals.
4.  **Part 1: Foundations (10 min):** Basic concepts and background.
5.  **Part 2: Deep Dive (15 min):** Detailed exploration of main topic.
6.  **Interlude: Listener Question (3 min):** Address a common question.
7.  **Part 3: Advanced Concepts (12 min):** Complex aspects for engaged listeners.
8.  **Part 4: Real-World Applications (10 min):** Practical examples and case studies.
9.  **Part 5: Future Implications (8 min):** Where the field is heading.
10. **Conclusion & Call-to-Action (5 min):** Summary, resources, next episode tease.

Each segment should include:
- Estimated duration
- Key talking points (bullet list)
- Transition to next segment
"""
```

**Customization Example - Interview Format**:
```python
PODCAST_EPISODE_PLANNER_PROMPT = """
You are a podcast producer creating an INTERVIEW-STYLE outline.

Structure:
1. **Pre-Interview Intro (1-2 min):** Host sets context, introduces guest
2. **Guest Background (5 min):** Expert's journey and expertise
3. **Main Interview (30 min):** Divided into 3-4 thematic sections:
   - Current work and projects
   - Biggest challenges in the field
   - Surprising findings or insights
   - Advice for beginners
4. **Rapid-Fire Questions (5 min):** Quick, fun questions
5. **Closing Thoughts (3 min):** Final reflections and where to learn more

For each section, provide:
- Sample opening question
- Expected topics to cover
- Natural segue to next section
"""
```

**Use Cases**:
- Adapt to different podcast lengths
- Create interview vs. educational formats
- Add Q&A segments
- Include sponsor breaks or interludes

### 3. Modify Topic Extraction Strategy

**Location**: `podcast_transcript_agent/sub_agents/podcast_topics/prompt.py`

**Current Default** (lines 15-40): Extracts 5 subtopics

**Customization Example - Research Paper Focus**:

Edit `prompt.py`:
```python
TOPIC_EXTRACTION_PROMPT = """
You are an expert academic researcher analyzing research papers for podcast
adaptation. Extract content suitable for a 45-minute academic podcast.

Analyze the research paper and identify:
- **Research Question:** The primary question being investigated
- **Methodology:** How the research was conducted (simplified)
- **Key Findings:** 3-5 main discoveries or results
- **Implications:** Why this research matters
- **Future Directions:** What comes next in this research area

For each finding/implication, extract:
1. A clear, jargon-free title
2. Detailed explanation (3-4 paragraphs) including:
   - What was discovered
   - Why it's significant
   - How it was validated
   - Real-world applications
3. Key statistics, measurements, or data points
4. Visual/diagram descriptions (if applicable)
5. Counterarguments or limitations discussed

Additional requirements:
- Identify technical terms that need explanation
- Flag concepts that need analogies for general audience
- Note any historical context mentioned
- Extract quotes from researchers (if present)

Provide your response in JSON format matching the schema.
"""
```

**Customization Example - News Summary Focus**:
```python
TOPIC_EXTRACTION_PROMPT = """
You are a news analyst extracting information for a daily news podcast.

From the provided news article, extract:
1. **Headline Story:** The main event or development
2. **Background Context:** What led to this event (keep brief)
3. **Key Players:** Who is involved (people, organizations, countries)
4. **Impact Analysis:** Who/what is affected and how
5. **Expert Opinions:** Different perspectives on the event
6. **What Happens Next:** Expected developments

For each section:
- Write for listeners who may be hearing about this for the first time
- Include specific dates, numbers, and names
- Distinguish between facts and speculation
- Note any conflicting reports or uncertainties

Focus on:
- Clarity over completeness
- Context that helps understanding
- Human interest angles
"""
```

**Use Cases**:
- Optimize for specific document types (research, news, tutorials)
- Extract domain-specific information (legal, medical, technical)
- Adjust detail level for target audience
- Focus on specific aspects (practical vs. theoretical)

### 4. Add Timestamps and Production Notes

**Location**: `podcast_transcript_agent/models/podcast_transcript.py` and writer prompt

**Current Schema** (lines 24-30): Basic timestamps per segment

**Enhanced Schema**:

Edit `models/podcast_transcript.py`:
```python
class SpeakerDialogue(BaseModel):
    speaker_id: str
    text: str
    start_time: float  # Add granular timing
    end_time: float
    production_notes: Optional[str] = None  # Add production guidance

class ProductionNote(BaseModel):
    """Production guidance for audio engineers."""
    timestamp: float
    note_type: str  # "music", "sfx", "editing", "tone"
    description: str

class PodcastSegment(BaseModel):
    segment_title: str
    title: str
    start_time: float
    end_time: float
    speaker_dialogues: List[SpeakerDialogue]
    production_notes: List[ProductionNote] = []  # Add production guidance
    background_music: Optional[str] = None
    intro_sfx: Optional[str] = None
    outro_sfx: Optional[str] = None

class PodcastTranscript(BaseModel):
    metadata: PodcastMetadata
    speakers: List[PodcastSpeaker]
    segments: List[PodcastSegment]
    production_notes: List[ProductionNote] = []  # Overall production notes
```

**Update Writer Prompt** (`podcast_transcript_writer/prompt.py`):
```python
PODCAST_TRANSCRIPT_WRITER_PROMPT = """
[... existing persona definitions ...]

**Production Elements:**
Add production notes throughout the script:
- Suggest background music styles for segments (e.g., "upbeat electronica",
  "contemplative piano")
- Indicate sound effects where appropriate (e.g., "[SFX: notification sound]")
- Mark editing opportunities (e.g., "[EDIT: tighten this exchange]")
- Note tone changes (e.g., "[TONE: shift to more serious]")
- Suggest speaker emphasis or pacing (e.g., "[SLOW DOWN for emphasis]")

Include timestamp for each dialogue exchange, estimated in seconds from
episode start.

Example production note format:
```
{
  "timestamp": 245.0,
  "note_type": "music",
  "description": "Fade in energetic music for transition to practical examples"
}
```
"""
```

**Use Cases**:
- Prepare transcripts for audio production
- Guide voice actors or text-to-speech engines
- Plan music and sound effects
- Create editing guides for producers

### 5. Support Multiple Languages

**Location**: All agent prompts

**Implementation Example**:

**1. Add Language Parameter** to each agent:

Edit `sub_agents/podcast_topics/agent.py`:
```python
podcast_topics_agent = Agent(
    name="podcast_topics_agent",
    model="gemini-2.5-flash",
    description="Extracts podcast topics from provided input",
    instruction=prompt.TOPIC_EXTRACTION_PROMPT,
    output_schema=PodcastTopics,
    output_key="podcast_topics",
    # Add configuration for language
    config={
        "output_language": "en"  # Default to English
    }
)
```

**2. Update Prompts** to include language instruction:

Edit `sub_agents/podcast_topics/prompt.py`:
```python
TOPIC_EXTRACTION_PROMPT = """
You are an expert research analyst. Your task is to analyze the provided
text and extract key components for a podcast scriptwriter.

**IMPORTANT: Respond in {language} language.**

[... rest of prompt ...]

All extracted topics, descriptions, and facts must be written in {language}.
"""

# Usage:
def get_prompt(language="English"):
    return TOPIC_EXTRACTION_PROMPT.format(language=language)
```

**3. Pass Language Through Pipeline**:

Create configuration file `config.py`:
```python
class PodcastConfig:
    output_language: str = "English"  # or "Spanish", "French", "German", etc.
    language_code: str = "en"  # ISO 639-1 code

    # Language-specific speaker names
    speaker_names = {
        "en": {"host": "Ben", "expert": "Dr. Smith"},
        "es": {"host": "Carlos", "expert": "Dra. García"},
        "fr": {"host": "Marie", "expert": "Dr. Dubois"},
    }
```

**Use Cases**:
- Create podcasts for international audiences
- Support multilingual content creation
- Localize existing podcasts
- Generate translated versions automatically

### 6. Add Content Filtering and Safety

**Location**: Create new validation layer

**Implementation Example**:

Create `podcast_transcript_agent/validators/content_filter.py`:
```python
from google.adk.agents import Agent
from pydantic import BaseModel

class ContentSafetyCheck(BaseModel):
    is_safe: bool
    issues_found: List[str]
    severity: str  # "none", "low", "medium", "high"
    recommendations: List[str]

content_safety_agent = Agent(
    name="content_safety_agent",
    model="gemini-2.5-flash",
    description="Checks content for inappropriate material",
    instruction="""
    Review the podcast transcript for:
    - Offensive language or slurs
    - Medical misinformation
    - Financial advice (disclaimer needed)
    - Copyright concerns
    - Age-inappropriate content
    - Factual inaccuracies

    Flag any concerns and suggest corrections.
    Provide severity rating and recommendations.
    """,
    output_schema=ContentSafetyCheck,
    output_key="safety_check"
)
```

**Integrate into Pipeline** (`agent.py`):
```python
from google.adk.agents import SequentialAgent
from .validators.content_filter import content_safety_agent

podcast_transcript_agent = SequentialAgent(
    name="podcast_transcript_agent",
    description="Executes a sequence of podcast generation steps",
    sub_agents=[
        podcast_topics_agent,
        podcast_episode_planner_agent,
        podcast_transcript_writer_agent,
        content_safety_agent,  # Add safety check at end
    ],
)
```

**Use Cases**:
- Ensure brand safety
- Comply with platform policies
- Avoid legal issues
- Maintain quality standards

### 7. Generate Show Notes and Metadata

**Location**: Add new agent to pipeline

**Implementation Example**:

Create `sub_agents/show_notes_generator/agent.py`:
```python
from google.adk.agents import Agent
from pydantic import BaseModel

class ShowNotes(BaseModel):
    episode_description: str  # 2-3 paragraphs
    key_takeaways: List[str]  # 5-7 bullet points
    timestamps: List[dict]  # {"time": "12:34", "description": "Topic starts"}
    resources: List[dict]  # {"title": "...", "url": "..."}
    tags: List[str]  # For SEO and categorization
    social_media_posts: dict  # Twitter, LinkedIn, etc.
    seo_title: str
    seo_description: str

show_notes_agent = Agent(
    name="show_notes_generator",
    model="gemini-2.5-flash",
    description="Generates show notes and promotional content",
    instruction="""
    Based on the podcast transcript, create comprehensive show notes.

    Generate:
    1. Episode description (compelling, 2-3 paragraphs, includes keywords)
    2. Key takeaways (5-7 actionable bullet points)
    3. Chapter markers (timestamp + description for major topics)
    4. Related resources (books, articles, tools mentioned)
    5. SEO-optimized title and description
    6. Tags for categorization
    7. Social media posts:
       - Twitter/X: 280 characters, include hashtags
       - LinkedIn: Professional summary, 150-200 words
       - Instagram: Engaging caption with emojis

    Make content shareable and search-friendly.
    """,
    output_schema=ShowNotes,
    output_key="show_notes"
)
```

**Add to Pipeline**:
```python
podcast_transcript_agent = SequentialAgent(
    name="podcast_transcript_agent",
    sub_agents=[
        podcast_topics_agent,
        podcast_episode_planner_agent,
        podcast_transcript_writer_agent,
        show_notes_agent,  # Add show notes generation
    ],
)
```

**Use Cases**:
- Automate marketing content creation
- Improve podcast discoverability
- Generate promotional materials
- Create chapter markers for players

---

**Note**: This agent demonstrates a clean sequential architecture ideal for content transformation workflows. It's designed to be easily extended with additional processing steps, customized for specific content types, and integrated into larger content creation pipelines.
