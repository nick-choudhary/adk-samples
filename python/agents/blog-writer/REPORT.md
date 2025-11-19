# Blog Writer Agent - Technical Documentation Report

## Project Scope

The Blog Writer Agent (also called "Blogger Agent") is a sophisticated multi-agent system designed to assist users in creating high-quality technical blog posts from start to finish. The agent orchestrates a complete content creation workflow including research, planning, writing, editing, social media promotion, and export.

**Core Capabilities:**
- **Codebase Analysis**: Analyzes source code repositories to extract context for technical writing
- **Blog Planning**: Generates structured outlines with titles, sections, and key points
- **Iterative Writing**: Produces full blog posts with research from Google Search
- **Collaborative Editing**: Refines content based on user feedback through multiple iterations
- **Social Media Generation**: Creates promotional posts for blog distribution
- **Markdown Export**: Saves final articles as properly formatted markdown files

**Primary Use Cases:**
- Technical writers documenting new features or libraries
- Developer advocates creating educational content
- Engineering teams publishing release notes or tutorials
- Content marketers producing SEO-optimized technical articles
- Open source maintainers writing documentation

**Target Users:**
- Software developers and technical writers
- Developer advocates and community managers
- Content marketing teams in tech companies
- Documentation teams

## Technical Architecture

### Multi-Agent Workflow System

The system implements a **sequential multi-agent workflow** with one orchestrator and four specialized sub-agents:

```
Interactive Blogger Agent (Orchestrator)
    ├─→ Robust Blog Planner (outline generation)
    ├─→ Robust Blog Writer (content creation)
    ├─→ Blog Editor (revision and refinement)
    └─→ Social Media Writer (promotional content)
```

**Agent Hierarchy** (`blogger_agent/agent.py`):

1. **Interactive Blogger Agent** (Root Orchestrator) - lines 31-66:
   - **Model**: Configured via `config.worker_model`
   - **Role**: Manages entire blog creation workflow
   - **8-Step Workflow**:
     1. **Analyze Codebase** (Optional): Uses `analyze_codebase` tool if directory provided
     2. **Plan**: Delegates to `robust_blog_planner` for outline generation
     3. **Refine**: Iterates with user feedback until outline approved
     4. **Visuals**: Asks user to choose visual content strategy (upload placeholders vs. none)
     5. **Write**: Delegates to `robust_blog_writer` once outline approved
     6. **Edit**: Uses `blog_editor` to revise based on user feedback (iterative)
     7. **Social Media**: Delegates to `social_media_writer` if user wants promotion
     8. **Export**: Saves to markdown file via `save_blog_post_to_file` tool
   - **Sub-agents**: All 4 specialist agents
   - **Tools**: `save_blog_post_to_file`, `analyze_codebase`
   - **Output Key**: `blog_outline`

2. **Robust Blog Planner** (`sub_agents/blog_planner.py`):
   - **Purpose**: Generates structured blog post outlines
   - **Features**:
     - Uses loops to ensure valid outline creation
     - Can use Google Search for topic research
     - Creates hierarchical structure (Title → Intro → Body → Conclusion)
   - **Output**: Markdown-formatted outline with sections and bullet points

3. **Robust Blog Writer** (`sub_agents/blog_writer.py`):
   - **Purpose**: Writes full blog posts from approved outlines
   - **Features**:
     - Uses Google Search for relevant examples and information
     - Maintains consistency with outline structure
     - Incorporates technical details and code snippets
   - **Output**: Complete blog post draft in markdown

4. **Blog Editor** (`sub_agents/blog_editor.py`):
   - **Purpose**: Revises blog posts based on user feedback
   - **Features**:
     - Iterative refinement process
     - Preserves approved sections while modifying others
     - Maintains writing style and tone
   - **Output**: Revised blog post

5. **Social Media Writer** (`sub_agents/social_media_writer.py`):
   - **Purpose**: Creates social media promotional content
   - **Features**:
     - Generates platform-specific posts (Twitter, LinkedIn, etc.)
     - Extracts key highlights from blog post
     - Includes hashtags and call-to-action
   - **Output**: Social media post variants

### Custom Tools

**Defined in `blogger_agent/tools.py`:**

1. **save_blog_post_to_file**:
   - **Function**: Exports blog post to markdown file
   - **Parameters**: filename, content
   - **Behavior**: Writes UTF-8 encoded markdown to specified path
   - **Use Case**: Final export when user approves content

2. **analyze_codebase**:
   - **Function**: Analyzes source code repository structure
   - **Parameters**: directory_path
   - **Behavior**:
     - Traverses directory tree
     - Identifies file types and structure
     - Extracts key components (classes, functions, modules)
     - Generates summary of codebase
   - **Use Case**: Provides context for technical blog posts about code

**Built-in Tools:**
- **Google Search**: Used by planner and writer for research

### Code Flow Example

**User Request**: "I want to write a blog post about the new Google Gemini 2.5 Flash Preview model, also known as Nanobanana."

**Step-by-Step Execution**:

1. **Planning Phase**:
   ```
   User → Interactive Blogger Agent
         → robust_blog_planner (with Google Search)
         → Returns outline with sections:
            - Title: "Gemini 2.5 Flash: Speed and Efficiency of Nanobanana"
            - Intro (hook, context, thesis)
            - Body (features, capabilities, comparisons)
            - Conclusion (summary, CTA)
   ```

2. **Refinement Phase**:
   ```
   Agent presents outline → User: "looks good, write it"
   ```

3. **Visual Selection**:
   ```
   Agent: "How do you want to handle visuals?"
   Options: 1) Upload placeholders, 2) None
   User: "2"
   ```

4. **Writing Phase**:
   ```
   Interactive Blogger Agent → robust_blog_writer
                             → Google Search for "Gemini 2.5 Flash features"
                             → Google Search for "Nanobanana AI model"
                             → Synthesizes full blog post
                             → Returns complete markdown draft
   ```

5. **Editing Phase**:
   ```
   Agent presents draft → User feedback: "Add more technical details"
   → blog_editor applies revisions
   → Presents updated version
   (Iterates until user approves)
   ```

6. **Social Media Phase**:
   ```
   Agent: "Generate social media posts?"
   User: "Yes"
   → social_media_writer creates promotional content
   ```

7. **Export Phase**:
   ```
   Agent: "What filename?"
   User: "gemini-flash-review.md"
   → save_blog_post_to_file("gemini-flash-review.md", content)
   ```

### Key Libraries and Dependencies

**Core Framework:**
- `google-adk>=1.0.0` - Google Agent Development Kit
- `google-cloud-aiplatform[adk,agent-engines]>=1.117.0` - Vertex AI integration
- `google-genai>=1.9.0` - Generative AI capabilities

**Configuration and Utilities:**
- `pydantic>=2.10.6` - Data validation and configuration management
- `python-dotenv>=1.0.1` - Environment variable management

**Evaluation and Testing:**
- `pytest~=8.4.2` - Testing framework
- `pytest-asyncio~=1.3.0` - Async testing support
- `google-adk[eval]>=1.0.0` - ADK evaluation framework
- `nest-asyncio>=1.6.0` - Nested event loop support

**Deployment:**
- `absl-py~=2.3.1` - Command-line argument parsing
- `agent-starter-pack>=0.14.1` - Production deployment utilities

**Development Tools:**
- `ruff>=0.4.6` - Fast Python linter
- `mypy~=1.18.2` - Static type checking
- `codespell~=2.4.1` - Spell checker

### Project Structure

```
blogger_agent/
├── agent.py                    # Main orchestrator agent
├── config.py                   # Model and configuration settings
├── tools.py                    # Custom tools (save, analyze)
└── sub_agents/
    ├── blog_planner.py         # Outline generation
    ├── blog_writer.py          # Content creation
    ├── blog_editor.py          # Revision and editing
    └── social_media_writer.py  # Social promotion

eval/
└── test_eval.py                # Evaluation framework

tests/
└── test_agent.py               # Integration tests
```

### Reasoning Mechanism

**Iterative Refinement Pattern**:
1. **Generate → Present → Collect Feedback → Refine → Repeat**
2. Each sub-agent focuses on a single task
3. User approval required between major workflow stages
4. Tools used strategically (Google Search for research, file operations for export)

**Context Management**:
- Current date injected into agent instructions
- Codebase analysis results carried through conversation
- Approved outline persists through writing phase
- User preferences (visuals, social media) tracked

## Build & Run Instructions

### Prerequisites

1. **Python 3.10, 3.11, or 3.12** (NOT 3.13+)
2. **uv** package manager (recommended):
   ```bash
   pip install uv
   ```
3. **Google Cloud Account** (for Vertex AI / Gemini access)
4. **API Keys** or **Vertex AI authentication**

### Step 1: Clone Repository

```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/blog-writer
```

### Step 2: Install Dependencies

```bash
uv pip install -r requirements.txt
```

This creates a virtual environment and installs all required packages.

### Step 3: Configure Environment Variables

Create `.env` file (or set in shell):

```bash
# For Vertex AI (recommended)
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# OR for direct Gemini API access
GOOGLE_API_KEY=your-api-key
```

### Step 4: Run the Agent

**Option 1: Web UI (Recommended)**

```bash
uv run adk web
```

- Opens web interface in browser
- Select `blogger_agent` from dropdown
- Interactive chat interface with markdown rendering

**Option 2: CLI Interface**

```bash
uv run adk run blogger_agent
```

- Terminal-based interaction
- Text-only output

### Step 5: Example Interaction

```
User: I want to write a blog post about the new Google Gemini 2.5 Flash Preview
model, also known as Nanobanana.

Agent: I can do that. Here is a blog post outline for an article about the Google
Gemini 2.5 Flash Preview model.

---

## Blog Post Outline: Introducing Gemini 2.5 Flash

### I. Title
Gemini 2.5 Flash: The Speed and Efficiency of Nanobanana

### II. Introduction
- **Hook:** Announcing Google's latest AI model
- **Context:** Designed for speed and efficiency
- **Thesis:** Explore key features and capabilities

### III. Main Body

#### A. What is Gemini 2.5 Flash?
- Lightweight and cost-effective
- Multimodal capabilities
- 1-million token context window
- 'Thinking' capability

#### B. Key Features
- Speed and efficiency
- Controlled generation, function calling
- Specialized versions

#### C. How to Get Access
- Available through Gemini API, AI Studio, Vertex AI

### IV. Conclusion
- Summary of benefits
- Call to action

---

User: looks good, write it

Agent: You have two options for including visual content:
1. Upload: Placeholders for your own images/videos
2. None: No visual content

Please respond with "1" or "2".

User: 2

Agent: [Proceeds to write full blog post using Google Search for research]
[Presents complete draft]
What do you think? Any changes needed?

User: Add more technical details about the token context window

Agent: [Uses blog_editor to revise]
[Presents updated version]

User: Perfect!

Agent: Would you like me to generate social media posts to promote this article?

User: Yes

Agent: [Generates Twitter, LinkedIn posts with hashtags]
Ready to export! What filename would you like?

User: gemini-flash-nanobanana.md

Agent: Blog post saved to gemini-flash-nanobanana.md!
```

### Step 6: Run Tests

**Integration Tests:**
```bash
uv run python -m tests.test_agent
```

**Evaluation (Smoke Test):**
```bash
uv run pytest eval/test_eval.py
```

Evaluates:
- Outline quality
- Writing coherence
- Editing accuracy
- Workflow completion

### Step 7: Production Deployment (Optional)

Using Agent Starter Pack for production-ready deployment:

```bash
# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install and create production project
pip install --upgrade agent-starter-pack
agent-starter-pack create my-blogger-agent -a adk@blogger-agent
```

**OR using uv:**
```bash
uvx agent-starter-pack create my-blogger-agent -a adk@blogger-agent
```

Features included:
- Automated CI/CD pipelines
- Infrastructure as code
- Monitoring and logging
- Security configurations
- Scalability optimizations

## Customization Options

### 1. Change AI Models

Edit `blogger_agent/config.py`:

```python
config.worker_model = "gemini-2.0-flash"  # Faster responses
# OR
config.worker_model = "gemini-2.5-pro"    # Higher quality
```

### 2. Add SEO Optimization

Extend `blog_writer` instructions:

```python
instruction="""
When writing blog posts:
- Include target keywords naturally
- Add meta descriptions
- Use H2/H3 headings appropriately
- Include internal/external links
- Optimize for featured snippets
"""
```

### 3. Support Additional Formats

Add export formats in `tools.py`:

```python
def save_blog_post_as_html(content: str, filename: str):
    import markdown
    html = markdown.markdown(content)
    with open(f"{filename}.html", "w") as f:
        f.write(html)

def save_blog_post_as_pdf(content: str, filename: str):
    from markdown2pdf import convert
    convert(content, f"{filename}.pdf")
```

### 4. Integrate CMS Platforms

Add WordPress/Medium publishing:

```python
def publish_to_wordpress(content: str, title: str, api_key: str):
    import requests
    # WordPress API integration
    ...

def publish_to_medium(content: str, title: str, token: str):
    # Medium API integration
    ...
```

### 5. Add Image Generation

Integrate image generation tools:

```python
from google.adk.tools.imagen import ImagenTool

imagen = ImagenTool(...)

# In blog_writer agent:
tools=[GoogleSearch(), imagen]
```

### 6. Custom Writing Styles

Extend `blog_writer` with style guides:

```python
instruction="""
Writing style guidelines:
- Tone: Conversational yet professional
- Audience: Intermediate developers
- Length: 1500-2000 words
- Code examples: Include for all concepts
- Analogies: Use when explaining complex topics
"""
```

## Performance Characteristics

**Agent Type:** Multi-Agent (1 orchestrator + 4 specialists)
**Complexity:** Intermediate
**Model:** Configurable (default: Gemini 2.5 Flash or Gemini 2.5 Pro)
**Interaction Type:** Conversational with iterative feedback loops

**Typical Execution Time**:
- Outline generation: 10-20 seconds
- Full blog post (1500 words): 30-60 seconds
- Editing iterations: 15-30 seconds each
- Social media posts: 5-10 seconds
- **Total end-to-end**: 2-5 minutes (depending on iterations)

**Resource Requirements**:
- Minimal local compute
- Network bandwidth for API calls
- Vertex AI / Gemini API quota

---

**Author:** Pier Paolo Ippolito (pierippolito@google.com)
**License:** Apache 2.0
**Python Version:** 3.10 - 3.12
**Vertical:** Content Creation / Technical Writing
