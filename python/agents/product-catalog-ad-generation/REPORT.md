# Product Catalog Ad Generation - Technical Documentation Report

## Project Scope

### High-level Summary
The Product Catalog Ad Generation Agent is an AI-powered creative assistant that automates the production of short-form video advertisements (under 15 seconds) grounded in product catalogs. The agent orchestrates a sophisticated multi-step workflow involving BigQuery product selection, storyline generation, image synthesis, video creation, audio production, and final assembly—all with human-in-the-loop feedback mechanisms for iterative refinement.

### Core Capabilities
- **Intelligent Product Selection**: Query BigQuery catalog with semantic search and demographic validation
- **AI-Driven Storytelling**: Generate "before and after" narratives with detailed visual style guides
- **Multi-Modal Asset Generation**: Create images (Gemini/Imagen), videos (Veo), and audio (Lyria)
- **Asset Sheet Synthesis**: Automated character and scene reference sheet creation
- **Brand Consistency**: Enforces corporate branding standards and product imagery
- **Quality Evaluation**: AI-based media evaluation to ensure output quality
- **Human Feedback Loop**: Interactive refinement at key workflow stages
- **GCS Integration**: Automated storage and organization of generated assets

### Primary Use Cases
- Marketing teams generating product ads at scale
- E-commerce platforms creating personalized video content
- Social media campaigns requiring short-form video ads
- A/B testing different creative approaches for products
- Rapid prototyping of advertising concepts
- Seasonal campaign generation with consistent branding

### Target Users
- Marketing and creative teams in e-commerce companies
- Advertising agencies managing multiple product catalogs
- Social media managers creating vertical video content
- Product managers demonstrating features visually
- Developers building automated content generation systems

### Key Innovations/Differentiators
- **End-to-End Automation**: Complete pipeline from product selection to final video
- **Multi-Model Orchestration**: Combines Gemini (storyline/images), Imagen (photorealistic images), Veo (video), and Lyria (audio)
- **Evaluation-Driven Generation**: Best-of-N image selection based on AI quality assessment
- **9:16 Aspect Ratio**: Optimized for TikTok, Instagram Reels, YouTube Shorts
- **Bring Your Own Assets**: Support for custom product photos and asset sheets via GCS URIs
- **Iterative Refinement**: Human feedback integration at storyline and final output stages
- **Production-Ready Infrastructure**: BigQuery catalog, GCS storage, structured workflows

## Technical Architecture

### Single-Agent with Function Tools Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   ROOT AGENT                                    │
│            (Content Generation Agent)                           │
│              Model: gemini-2.5-pro                              │
│         File: content_gen_agent/agent.py:65-76                  │
│                                                                 │
│  INSTRUCTION: Orchestrate ad generation workflow with          │
│               human confirmation at each step                   │
└──────────────────┬─────────────────────────────────────────────┘
                   │
        ┌──────────┴───────────┬──────────────┬──────────────┬─────────────┐
        ▼                      ▼              ▼              ▼             ▼
┌──────────────────┐  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│ GENERATE         │  │ GENERATE        │  │ GENERATE     │  │ GENERATE     │
│ STORYLINE        │  │ IMAGES          │  │ VIDEO        │  │ AUDIO        │
│ FunctionTool     │  │ FunctionTool    │  │ FunctionTool │  │ FunctionTool │
└────────┬─────────┘  └────────┬────────┘  └──────┬───────┘  └──────┬───────┘
         │                     │                   │                  │
         ▼                     ▼                   ▼                  ▼
┌──────────────────┐  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│ • Query BigQuery │  │ • Load Asset    │  │ • Convert    │  │ • Music:     │
│ • Select Product │  │   Sheet         │  │   Images to  │  │   Lyria-002  │
│ • Gen Narrative  │  │ • Gemini Flash  │  │   Video      │  │ • Voiceover: │
│ • Gen Visual     │  │   Image or      │  │ • Veo-3.0-   │  │   Gemini TTS │
│   Style Guide    │  │   Imagen-4      │  │   fast       │  │              │
│ • Gen Asset      │  │ • Best-of-3     │  │ • Parallel   │  │              │
│   Sheet (3x)     │  │   Evaluation    │  │   Async      │  │              │
│ • Eval & Select  │  │ • Save to GCS   │  │   Processing │  │              │
│   Best           │  │                 │  │              │  │              │
└──────────────────┘  └─────────────────┘  └──────────────┘  └──────────────┘
                                                   │                  │
                                                   └────────┬─────────┘
                                                            ▼
                                                   ┌──────────────────┐
                                                   │   COMBINE        │
                                                   │   FunctionTool   │
                                                   │ • Merge Video    │
                                                   │ • Add Audio      │
                                                   │ • Add Voiceover  │
                                                   │ • Upload to GCS  │
                                                   │ • MoviePy        │
                                                   └──────────────────┘
```

### Code Flow Explanation

**1. Agent Initialization** (`content_gen_agent/agent.py:65-76`)
```python
root_agent = Agent(
    name="content_generation_agent",
    model='gemini-2.5-pro',  # Line 67 - Most capable model for orchestration
    instruction=SYSTEM_INSTRUCTION,  # Lines 33-63 - Workflow guidance
    tools=[
        FunctionTool(func=generate_storyline),      # Step 1
        FunctionTool(func=generate_images_from_storyline),  # Step 2
        FunctionTool(func=generate_video),          # Step 3
        FunctionTool(func=generate_audio_and_voiceover),    # Step 4
        FunctionTool(func=combine),                 # Step 5
    ],
)
```

**2. Workflow Orchestration** (`agent.py:33-63`)
The system instruction enforces a strict workflow:
```python
SYSTEM_INSTRUCTION = f"""
CORE RULE: NEVER execute a function without explicit verbal confirmation.

Workflow:
1. Storyline Generation
2. Image Generation
3. Video Generation
4. Audio & Voiceover Generation
5. Final Assembly

Guidance:
- Guide user step-by-step
- Present proposed inputs and STOP for confirmation
- Ensure 9:16 aspect ratio
- Parallelize video and audio generation when possible
- Avoid generating children
"""
```

**3. Step 1: Storyline & Asset Sheet Generation** (`func_tools/generate_storyline.py:86-182`)

**Function Signature** (lines 86-114):
```python
async def generate_storyline(
    product: str,                    # Product name for BigQuery search
    target_demographic: str,         # Target audience validation
    tool_context: ToolContext,       # ADK artifact storage
    company_name: str,               # Branding
    num_images: int = 5,             # Scene count
    product_photo_filename: Optional[str] = None,  # Custom product photo
    style_preference: str = "photorealistic",
    user_provided_asset_sheet_gcs_uri: Optional[str] = None,  # Custom asset sheet
) -> Dict[str, Any]:
```

**Execution Flow**:
```
A. If user_provided_asset_sheet_gcs_uri exists:
   └─> Load from GCS (lines 126-137)
   └─> Save to tool_context artifacts

B. Generate Storyline Text (lines 139-148)
   └─> Call _generate_storyline_text() using gemini-2.5-pro
   └─> Input: product, demographic, style_guide, num_images
   └─> Output: JSON with "storyline" and "visual_style_guide"
   └─> File: lines 185-263

C. If no custom asset sheet:
   └─> Fetch product photo from BigQuery (lines 154-156)
       └─> select_product_from_bq() in func_tools/select_product.py
   └─> Generate Asset Sheet Image (lines 163-165)
       └─> _generate_asset_sheet_image() at lines 417-503
       └─> Generate 3 candidates in parallel (line 469)
       └─> Evaluate each with evaluate_media() (lines 365-367)
       └─> Select best based on evaluation score (lines 483-486)
       └─> Model: gemini-2.5-flash-image-preview (line 56)

D. Save Artifacts (lines 167-174)
   └─> visual_style_guide.json
   └─> storyline.json
   └─> asset_sheet.png

Return: {storyline, asset_sheet_filename, visual_style_guide_filename, status}
```

**4. Step 2: Image Generation** (`func_tools/generate_image.py:260-363`)

**Function Signature** (lines 260-282):
```python
async def generate_images_from_storyline(
    prompts: List[str],               # One prompt per scene
    tool_context: ToolContext,
    scene_numbers: Optional[List[int]] = None,  # Selective regeneration
    logo_prompt_present: bool = True,           # Last scene is logo
) -> List[str]:  # Returns JSON status strings
```

**Multi-Model Strategy**:
```
For each scene (lines 318-341):
├─ If scene is logo scene (line 328):
│  └─> Load logo from GCS (LOGO_GCS_URI at line 113)
│  └─> Use Gemini Flash Image with logo overlay (lines 332-335)
│
└─ If regular scene:
   ├─ Load asset_sheet.png from artifacts (lines 303-308)
   │
   ├─ If no input images:
   │  └─> Use Imagen 4.0 (_call_imagen_api at lines 167-205)
   │     └─> Model: imagen-4.0-generate-001
   │     └─> Aspect ratio: 9:16 (line 184)
   │     └─> Person generation: allow_all (line 187)
   │
   └─> If input images exist:
       └─> Use Gemini Flash Image (_call_gemini_image_api at lines 122-164)
       └─> Generate 3 candidates (MAX_RETRIES=3 at line 58)
       └─> Evaluate each (lines 151-152)
       └─> Select best (lines 239-249)
```

**Evaluation Mechanism** (`utils/evaluate_media.py`):
- Calls Gemini to assess image quality
- Checks: composition, lighting, brand alignment, demographic appropriateness
- Returns: Pass/Fail decision + detailed feedback
- Score calculation: `calculate_evaluation_score()` (lines in evaluate_media.py)

**5. Step 3: Video Generation** (`func_tools/generate_video.py`)

**Multi-Video Async Generation**:
```python
async def generate_video(
    input_filenames: List[str],     # Image artifact filenames
    prompts: List[str],             # Motion prompts for each video
    tool_context: ToolContext,
    scene_numbers: Optional[List[int]] = None,
) -> List[str]:  # Returns JSON status strings
```

**Process** (from func_tools/generate_video.py):
```
1. Load images from tool_context artifacts
2. For each image+prompt pair:
   └─> Call Veo 3.0 Fast (veo-3.0-fast-generate-001)
   └─> Model generates video from static image + motion prompt
   └─> Async parallel processing (asyncio.gather)
3. Save videos to artifacts with timestamps
4. Return status list
```

**6. Step 4: Audio Generation** (`func_tools/generate_audio.py`)

**Dual Audio Generation**:
```python
async def generate_audio_and_voiceover(
    music_style: str,               # E.g., "upbeat electronic"
    voiceover_script: str,          # Spoken narration text
    tool_context: ToolContext,
) -> Dict[str, Any]:
```

**Process**:
```
Parallel generation (asyncio.gather):
├─ Music Track
│  └─> Model: lyria-002 (Lyria audio generation)
│  └─> Input: music_style description
│  └─> Output: background_audio.wav
│
└─ Voiceover
   └─> Model: gemini-2.5-flash-preview-tts (Text-to-Speech)
   └─> Input: voiceover_script
   └─> Output: voiceover.wav

Both saved to tool_context artifacts
```

**7. Step 5: Final Assembly** (`func_tools/combine_video.py`)

**Video Composition**:
```python
async def combine(
    video_filenames: List[str],     # From step 3
    audio_filename: str,            # Background music from step 4
    voiceover_filename: str,        # Narration from step 4
    tool_context: ToolContext,
) -> Dict[str, Any]:
```

**MoviePy Pipeline** (from combine_video.py):
```
1. Load all video clips from artifacts
2. Concatenate videos sequentially (VideoFileClip + concatenate_videoclips)
3. Load audio tracks:
   ├─ Background music (CompositeAudioClip)
   └─ Voiceover overlay
4. Combine audio tracks (volumex for mixing)
5. Set audio to video (video.set_audio)
6. Export final video:
   └─> Codec: libx264
   └─> Audio codec: aac
   └─> FPS: 24
7. Upload to GCS:
   └─> Bucket: {GCP_PROJECT}-contentgen-static
   └─> Path: videos/YYYY-MM-DD/HH-MM-SS/combined_video_{timestamp}.mp4
8. Save local copy to static/generated/
9. Return GCS URI and local path
```

### Key Libraries and Dependencies

From `pyproject.toml:11-23`:
```toml
dependencies = [
    "google-adk>=1.10.0",                  # Agent Development Kit
    "google-cloud-aiplatform>=1.108.0",    # Vertex AI (Veo, Imagen)
    "google-cloud-bigquery>=3.35.1",       # Product catalog storage
    "google-genai>=1.29.0",                # Gemini API
    "langchain>=0.3.27",                   # LLM utilities
    "pandas>=2.3.1",                       # Data processing
    "toolbox-core>=0.4.0",                 # Utility functions
    "moviepy>=2.2.1",                      # Video editing/composition
    "google-cloud-texttospeech>=2.29.0",   # TTS capabilities
    "soundfile>=0.13.1",                   # Audio file I/O
    "pytest>=8.4.2",                       # Testing
    "aiohttp>=3.12.15",                    # Async HTTP
]
```

**Model Dependencies**:
- **Gemini 2.5 Pro**: Storyline generation, orchestration (`STORYLINE_MODEL` in generate_storyline.py:55)
- **Gemini 2.5 Flash Image**: Image generation with asset reference (`IMAGE_GEN_MODEL_GEMINI` in generate_image.py:55)
- **Imagen 4.0**: Photorealistic image generation (`IMAGE_GEN_MODEL_IMAGEN` in generate_image.py:56)
- **Veo 3.0 Fast**: Video generation from images (in generate_video.py)
- **Lyria 002**: Music generation (in generate_audio.py)
- **Gemini 2.5 Flash TTS**: Voiceover synthesis (in generate_audio.py)

### Tools and Integrations

**1. BigQuery Product Catalog** (`func_tools/select_product.py`)
```python
def select_product_from_bq(product_name: str) -> Optional[Dict[str, Any]]:
    """
    Queries BigQuery for product metadata.

    Dataset: content_generation
    Table: media_assets
    Columns: product_name, description, search_tags, image_gcs_uri

    Search Logic: Exact text match on search_tags column
    Returns: Product dict or None
    """
```

**Setup Script**: `scripts/02-deploy-gcs-and-bq.sh`
- Creates dataset and table
- Calls `scripts/populate_bq_with_gemini.py` to generate metadata using Gemini

**2. Google Cloud Storage Integration**
```python
# Asset Storage Structure (from combine_video.py and README.md:126-138)
gs://{project-id}-contentgen-static/
├── branding_logos/
│   └── logo.png                    # Corporate logo
├── products/
│   └── {product_images}.png        # Product photos (9:16 aspect)
└── videos/
    └── YYYY-MM-DD/
        └── HH-MM-SS/
            └── combined_video_{timestamp}.mp4
```

**3. Artifact Management** (via ADK ToolContext)
```python
# Save artifacts during workflow
await tool_context.save_artifact("asset_sheet.png", image_part)
await tool_context.save_artifact("visual_style_guide.json", json_part)

# Load artifacts in later steps
asset_sheet = await tool_context.load_artifact("asset_sheet.png")
```

**4. Media Evaluation System** (`utils/evaluate_media.py`)
```python
async def evaluate_media(
    media_bytes: bytes,
    mime_type: str,
    original_prompt: str
) -> EvaluationResult:
    """
    Uses Gemini to evaluate generated media quality.

    Checks:
    - Visual quality and composition
    - Prompt adherence
    - Brand consistency
    - Demographic appropriateness

    Returns: EvaluationResult(decision="Pass"/"Fail", feedback={...})
    """
```

**Evaluation Prompts**: `utils/evaluation_prompts.py`

### Reasoning Mechanisms

**1. Human-in-the-Loop Confirmation** (`agent.py:35`)
```python
"CORE RULE: NEVER execute a function without explicit verbal confirmation."
```
The agent presents parameters and waits for user approval before each tool call.

**2. Best-of-N Selection**
- Asset sheet: Generate 3 candidates, evaluate all, select best (`generate_storyline.py:468-486`)
- Images: Generate 3 per scene, evaluate, select best (`generate_image.py:228-249`)
- Uses `calculate_evaluation_score()` to rank candidates

**3. Conditional Model Selection**
```python
# In generate_image.py:260-363
if not input_images:
    # No context → use Imagen 4 for photorealistic generation
    return await _call_imagen_api(prompt, filename_prefix)
else:
    # With asset sheet → use Gemini Flash Image for consistency
    return await _call_gemini_image_api(contents, prompt)
```

**4. Parallel Async Execution** (`agent.py:50`)
```python
"When possible, try to parallelize video and audio generation upon user confirmation."
```
Video clips and audio tracks generated concurrently using `asyncio.gather()`.

**5. Safety Configuration** (`generate_storyline.py:59-76`)
```python
SAFETY_SETTINGS = [
    SafetySetting(category=HARM_CATEGORY_HATE_SPEECH, threshold=OFF),
    # ... all categories set to OFF for creative flexibility
]
```

**6. Storyline Instructions** (`utils/storytelling.py`)
Contains detailed prompting strategies for consistent visual narratives.

## Build & Run Instructions

### Prerequisites

**Required:**
- Python 3.12+ (specified in `pyproject.toml:10`)
- Google Cloud SDK - [Install Guide](https://cloud.google.com/sdk/docs/install)
- Active GCP project with billing enabled
- Enabled APIs:
  - Vertex AI API
  - BigQuery API
  - Cloud Storage API
  - Generative Language API

**Optional:**
- `uv` package manager (recommended) - [Install](https://docs.astral.sh/uv/)

### Step-by-Step Installation

**1. Clone Repository**
```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/product-catalog-ad-generation
```

**2. Install Dependencies**

Using uv (recommended):
```bash
uv sync
```

Using pip:
```bash
pip install -r requirements.txt
```

**3. Set Up Google Cloud Credentials**
```bash
# Authenticate
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

**4. Run Setup Scripts**

**Script 1: Enable APIs** (`scripts/01-setup-gcp.sh`)
```bash
bash scripts/01-setup-gcp.sh
```
Enables required Google Cloud APIs for the project.

**Script 2: Deploy Infrastructure** (`scripts/02-deploy-gcs-and-bq.sh`)
```bash
bash scripts/02-deploy-gcs-and-bq.sh
```

This script:
- Creates GCS bucket: `{PROJECT_ID}-contentgen-static`
- Uploads assets from `static/uploads/`:
  - `products/` → Product images (must be 9:16 aspect ratio)
  - `branding/logo.png` → Company logo
- Creates BigQuery dataset: `content_generation`
- Creates table: `media_assets`
- Runs `scripts/populate_bq_with_gemini.py` to generate product metadata

**Product Metadata Generation** (`scripts/populate_bq_with_gemini.py`):
- Lists all images in `gs://{bucket}/products/`
- For each image, uses Gemini to generate:
  - `product_name`
  - `description`
  - `search_tags` (comma-separated keywords)
- Inserts rows into BigQuery table

### Configuration (Environment Variables)

**Create `.env` File**
```bash
cp .env.example .env
```

**Edit `.env`** (from `.env.example:1-19`):
```bash
# Runtime Configuration
export GCP_PROJECT="your-gcp-project-id"
export GCP_LOCATION="global"
export GOOGLE_CLOUD_LOCATION="global"
export GOOGLE_GENAI_USE_VERTEXAI=1
export COMPANY_NAME="ACME Corp"  # Used in branding

# Deployment Configuration
export REGION="us-central1"
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"

# BigQuery Configuration (optional overrides)
# BQ_DATASET="content_generation"
# BQ_TABLE="media_assets"
```

**Environment Variable Reference:**
- `GCP_PROJECT`: Your Google Cloud project ID (required)
- `COMPANY_NAME`: Company name for branding (default: "ACME Corp")
- `GOOGLE_GENAI_USE_VERTEXAI`: Use Vertex AI backend (1=yes)
- `GCS_BUCKET`: GCS bucket name (auto-generated if not set: `{PROJECT}-contentgen-static`)
- `REGION`: GCP region for resources (us-central1 recommended)

### Running the Agent

**Method 1: ADK Web UI** (Recommended)
```bash
# Load environment variables
source .env  # or: export $(cat .env | xargs)

# Start ADK web interface
adk web
```

1. Open browser to displayed URL (typically http://localhost:8000)
2. Select "content_generation_agent" from dropdown
3. Start conversation:
   ```
   User: "Generate an ad for a smart light bulb targeting tech-savvy millennials"
   ```

**Method 2: ADK CLI**
```bash
adk run content_gen_agent
```

**Method 3: Python Script**
```python
from google.adk.sessions import Session
from content_gen_agent.agent import root_agent

session = Session(agent=root_agent)
runner = session.create_runner()

# Run asynchronously
import asyncio

async def generate_ad():
    result = await runner.run_async(
        "Create an ad for wireless headphones targeting young professionals"
    )
    async for event in result:
        print(event)

asyncio.run(generate_ad())
```

### Example Interactions

**Scenario 1: Full Workflow with Default Products**
```
User: "I want to create a video ad for a smart bulb for eco-conscious millennials"

Agent: "I'll help you create a video ad! Let me start by generating a storyline.
        I'll use the following parameters:
        - Product: smart bulb
        - Target demographic: eco-conscious millennials
        - Company: ACME Corp
        - Number of scenes: 5
        - Style: photorealistic

        Should I proceed?"

User: "Yes, proceed"

Agent: [Calls generate_storyline]
       [Returns storyline and asset sheet]

       "Here's the storyline I generated:
        Scene 1: Aerial view of a modern apartment building at dusk
        Scene 2: Person struggling with old light switch in dimly lit room
        Scene 3: Person installing smart bulb easily
        Scene 4: Room beautifully lit, person controlling via phone
        Scene 5: ACME Corp logo with glowing background

        The asset sheet shows the character and environments.
        Would you like me to proceed with generating images?"

User: "Yes, generate the images"

Agent: [Calls generate_images_from_storyline]
       [Returns 5 images saved as artifacts]

       "Images generated successfully! All 5 scene images are ready.
        Next, I'll generate videos from these images. Should I proceed?"

User: "Yes"

Agent: "I'll now generate the video clips and audio in parallel to save time.
        For videos, I'll use the prompts:
        - Scene 1: Slow aerial pan over building
        - Scene 2: Camera zooms on frustrated person
        ...

        For audio:
        - Music: Upbeat, modern electronic
        - Voiceover: 'Transform your home with smart lighting...'

        Proceed?"

User: "Yes"

Agent: [Calls generate_video and generate_audio_and_voiceover in parallel]
       [Returns video clips and audio files]

       "Videos and audio generated! Now combining into final ad.
        Should I create the final video?"

User: "Yes, combine them"

Agent: [Calls combine]
       [Returns final video]

       "Your ad is complete!
        GCS URI: gs://your-project-contentgen-static/videos/2025-11-19/14-30-22/combined_video_1234567890.mp4
        Local path: static/generated/combined_video_1234567890.mp4

        The final video is 12 seconds long with background music and voiceover."
```

**Scenario 2: Using Custom Product Photo**
```
User: "Create an ad for my product using this photo: gs://my-bucket/my-product.png"

Agent: "I'll generate a storyline using your custom product photo.
        What demographic are you targeting?"

User: "Parents with young children"

Agent: [Proceeds with generate_storyline using product_photo_filename parameter]
       [Downloads image from GCS, uses in asset sheet generation]
```

**Scenario 3: Bringing Your Own Asset Sheet**
```
User: "I already have an asset sheet at gs://my-bucket/my-asset-sheet.png.
       Use this to create an ad for a coffee maker for busy professionals."

Agent: [Calls generate_storyline with user_provided_asset_sheet_gcs_uri]
       [Skips asset sheet generation, uses provided sheet]
       [Generates storyline based on characters in the sheet]
```

**Scenario 4: Selective Image Regeneration**
```
User: "I don't like scene 2. Can you regenerate just that image?"

Agent: "I'll regenerate only scene 2.
        Would you like a different prompt or keep the same one?"

User: "Keep the same prompt"

Agent: [Calls generate_images_from_storyline with scene_numbers=[2]]
       [Only regenerates scene 2 image]
```

### Testing and Evaluation

**Run Tests**
```bash
# Install dev dependencies
uv sync --dev  # or: pip install -e ".[dev]"

# Run test suite
pytest

# Run specific test file
pytest tests/test_agent.py

# Run with verbose output
pytest -v
```

**Test Coverage:**
The project includes pytest configuration in `pyproject.toml` but test files should be added to a `tests/` directory for comprehensive coverage.

**Manual Testing Checklist:**
1. ✓ Product selection from BigQuery
2. ✓ Storyline generation with valid JSON
3. ✓ Asset sheet quality evaluation
4. ✓ Image generation for all scenes
5. ✓ Logo scene with corporate branding
6. ✓ Video generation from static images
7. ✓ Audio and voiceover synthesis
8. ✓ Final video combination and upload to GCS

### Deployment

**Deploy to Vertex AI Agent Engine**
```bash
# Ensure environment variables are set
source .env

# Run deployment script
python agent_engine_deploy.py
```

**Deployment Script** (`agent_engine_deploy.py:1-200`):
The script packages the agent and deploys to Vertex AI for production use.

**Post-Deployment Testing:**
After deployment, test via Vertex AI Agent Builder UI or API calls.

### Troubleshooting

**1. Product Not Found in BigQuery**
```
Error: Product 'light bulb' not found in BigQuery.
```
**Solution:**
- Check `search_tags` column in BigQuery: `SELECT * FROM content_generation.media_assets`
- BigQuery uses exact text match on `search_tags`
- Add synonyms to search_tags: "light bulb, smart bulb, LED bulb"
- Re-run `scripts/populate_bq_with_gemini.py` to regenerate metadata

**2. Image Aspect Ratio Issues**
```
Warning: Generated images have inconsistent aspect ratios
```
**Solution:**
- Ensure product images in `static/uploads/products/` are 9:16 aspect ratio
- Use padding script to fix:
  ```bash
  python scripts/add_padding.py
  ```
- The script adds white padding to achieve 9:16 ratio

**3. Children Generation Error**
```
Error: Content policy violation - children detected
```
**Solution:**
- Avoid storylines involving children (noted in `agent.py:51`)
- Modify storyline to use adult characters only
- Request to be added to allowlist for necessary permission override

**4. GCS Upload Failures**
```
Error: Failed to upload to GCS
```
**Solution:**
- Verify bucket exists: `gsutil ls gs://{PROJECT_ID}-contentgen-static`
- Check permissions: `gcloud storage buckets describe gs://{bucket-name}`
- Ensure authenticated: `gcloud auth application-default login`

**5. Veo Video Generation Timeout**
```
Error: Video generation timed out
```
**Solution:**
- Veo can take 60-90 seconds per video
- Increase timeout in generate_video.py if needed
- Consider using fewer scenes for faster iteration

**6. Gemini Client Not Initialized**
```
Error: Gemini client not initialized. Check credentials.
```
**Solution:**
- Verify environment variables are set: `echo $GCP_PROJECT`
- Check authentication: `gcloud auth application-default print-access-token`
- Ensure `GOOGLE_GENAI_USE_VERTEXAI=1` in `.env`

**7. MoviePy Codec Errors**
```
Error: MoviePy could not find codec
```
**Solution:**
- Install ffmpeg: `sudo apt-get install ffmpeg` (Linux)
- macOS: `brew install ffmpeg`
- Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Customization Options

### 1. Add Custom Products to Catalog

**Use Case:** Expand the product catalog with your own products.

**Implementation:**

**Step 1:** Add product images to `static/uploads/products/`
```bash
# Copy your product images
cp /path/to/your-product.png static/uploads/products/

# Ensure 9:16 aspect ratio
python scripts/add_padding.py
```

**Step 2:** Re-run deployment script
```bash
bash scripts/02-deploy-gcs-and-bq.sh
```

**Step 3:** Verify product in BigQuery
```bash
bq query --use_legacy_sql=false \
  'SELECT product_name, search_tags FROM content_generation.media_assets'
```

**Manual Insertion** (alternative):
```python
from google.cloud import bigquery

client = bigquery.Client()
table_id = "your-project.content_generation.media_assets"

rows_to_insert = [
    {
        "product_name": "Premium Coffee Maker",
        "description": "High-end espresso machine with smart features",
        "search_tags": "coffee maker, espresso, coffee machine, smart coffee",
        "image_gcs_uri": "gs://your-bucket/products/coffee-maker.png"
    }
]

errors = client.insert_rows_json(table_id, rows_to_insert)
if errors:
    print(f"Errors: {errors}")
```

### 2. Customize Visual Style and Branding

**Use Case:** Enforce specific brand guidelines across all generated ads.

**Implementation:**

**A. Custom Logo** (`static/uploads/branding/logo.png`)
```bash
# Replace default logo
cp your-company-logo.png static/uploads/branding/logo.png

# Re-upload to GCS
gsutil cp static/uploads/branding/logo.png \
  gs://{PROJECT_ID}-contentgen-static/branding_logos/logo.png
```

**B. Company Name** (`.env`)
```bash
export COMPANY_NAME="Your Company Name"
```

**C. Visual Style Preferences** (`func_tools/generate_storyline.py:119-122`)
Modify default style:
```python
style_guide = (
    f"The style must be cinematic, warm lighting, "
    f"brand colors: blue and gold, "
    f"minimal whitespace with a '{style_preference}' effect."
)
```

**D. Storyline Template** (`utils/storytelling.py`)
Add custom storytelling instructions:
```python
STORYTELLING_INSTRUCTIONS = """
BRAND GUIDELINES:
- Always feature products in everyday contexts
- Use warm, inviting color palettes
- Emphasize family-friendly messaging
- Include diverse representation
...
"""
```

### 3. Integrate Custom Media Evaluation Criteria

**Use Case:** Enforce specific quality standards beyond default evaluation.

**Implementation:**

**File:** `utils/evaluation_prompts.py`

Add custom evaluation criteria:
```python
CUSTOM_EVALUATION_PROMPT = """
Evaluate the generated image for:

1. Brand Compliance:
   - Logo visible and correctly positioned
   - Brand colors (blue #0066CC, gold #FFD700) present
   - Fonts match brand guidelines (Helvetica Neue)

2. Legal Compliance:
   - No copyrighted material visible
   - No trademarked logos (except our own)
   - Disclaimers needed: Yes/No

3. Accessibility:
   - Text contrast ratio > 4.5:1
   - Readable at small sizes

4. Performance Marketing Standards:
   - Product visible in first 3 seconds
   - Clear call-to-action visible

Return JSON:
{
  "decision": "Pass" or "Fail",
  "brand_compliance": "Pass/Fail",
  "legal_compliance": "Pass/Fail",
  "accessibility": "Pass/Fail",
  "performance": "Pass/Fail",
  "feedback": "..."
}
"""
```

**File:** `utils/evaluate_media.py`

Update evaluation function:
```python
async def evaluate_media(media_bytes, mime_type, original_prompt):
    # Use custom prompt
    evaluation_prompt = CUSTOM_EVALUATION_PROMPT

    # Add custom scoring logic
    score = 0
    if result.get("brand_compliance") == "Pass":
        score += 25
    if result.get("legal_compliance") == "Pass":
        score += 25
    # ... more criteria

    return EvaluationResult(decision=decision, score=score, ...)
```

### 4. Change Video Duration and Scene Count

**Use Case:** Generate longer ads (30 seconds) or shorter (6 seconds) for different platforms.

**Implementation:**

**A. Modify Default Scene Count** (`agent.py:33-63`)
```python
SYSTEM_INSTRUCTION = f"""
...
Workflow:
1. Storyline Generation: Use generate_storyline tool to create a "before and after"
   narrative with 8 scenes (changed from 5).  # Line 40
...
"""
```

**B. Adjust in Storyline Generation** (`func_tools/generate_storyline.py:86`)
```python
async def generate_storyline(
    ...
    num_images: int = 8,  # Changed from 5
    ...
):
```

**C. Scene Duration Control** (`func_tools/combine_video.py`)

Modify video clip duration:
```python
from moviepy.editor import VideoFileClip

# Load and set duration per clip
clips = []
for filename in video_filenames:
    clip = VideoFileClip(filename)
    # Set each clip to 3 seconds (instead of variable)
    clip = clip.set_duration(3.0)
    clips.append(clip)

# Total duration: 8 scenes × 3 seconds = 24 seconds
```

**D. Platform-Specific Presets**

Create duration profiles:
```python
PLATFORM_PRESETS = {
    "tiktok": {"scenes": 4, "duration_per_scene": 2.0},      # 8 seconds
    "instagram": {"scenes": 5, "duration_per_scene": 3.0},   # 15 seconds
    "youtube": {"scenes": 10, "duration_per_scene": 3.0},    # 30 seconds
}

def generate_for_platform(platform: str):
    preset = PLATFORM_PRESETS[platform]
    return generate_storyline(num_images=preset["scenes"], ...)
```

### 5. Add Multi-Language Support

**Use Case:** Generate ads with voiceovers in different languages.

**Implementation:**

**A. Language Parameter** (`func_tools/generate_audio.py`)
```python
async def generate_audio_and_voiceover(
    music_style: str,
    voiceover_script: str,
    tool_context: ToolContext,
    language_code: str = "en-US",  # Add parameter
    voice_name: str = "en-US-Neural2-A",  # Add parameter
) -> Dict[str, Any]:
```

**B. TTS Configuration**
```python
from google.cloud import texttospeech

# Configure voice
voice = texttospeech.VoiceSelectionParams(
    language_code=language_code,
    name=voice_name,
    ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
)

# Generate voiceover
synthesis_input = texttospeech.SynthesisInput(text=voiceover_script)
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16
)

response = client.synthesize_speech(
    input=synthesis_input,
    voice=voice,
    audio_config=audio_config
)
```

**C. Translation Pipeline**
```python
from google.cloud import translate_v2 as translate

def translate_script(script: str, target_language: str) -> str:
    translate_client = translate.Client()
    result = translate_client.translate(script, target_language=target_language)
    return result['translatedText']

# Usage
voiceover_script_es = translate_script(voiceover_script, "es")
```

**D. Language-Specific Voices**
```python
VOICE_MAPPING = {
    "en-US": "en-US-Neural2-A",
    "es-ES": "es-ES-Neural2-A",
    "fr-FR": "fr-FR-Neural2-A",
    "ja-JP": "ja-JP-Neural2-B",
}
```

### 6. Implement A/B Testing Framework

**Use Case:** Generate multiple creative variations for performance testing.

**Implementation:**

**File:** Create `func_tools/ab_testing.py`
```python
async def generate_variations(
    product: str,
    target_demographic: str,
    num_variations: int = 3,
    tool_context: ToolContext,
) -> List[Dict[str, Any]]:
    """Generate multiple ad variations for A/B testing."""

    # Define variation strategies
    strategies = [
        {"style": "photorealistic", "music": "upbeat electronic"},
        {"style": "minimalist", "music": "calm ambient"},
        {"style": "vibrant", "music": "energetic pop"},
    ]

    results = []
    for i, strategy in enumerate(strategies[:num_variations]):
        # Generate storyline with different style
        storyline_result = await generate_storyline(
            product=product,
            target_demographic=target_demographic,
            style_preference=strategy["style"],
            tool_context=tool_context,
        )

        # Continue with full pipeline
        # ... (generate images, video, audio)

        # Tag with variation ID
        results.append({
            "variation_id": f"variant_{i+1}",
            "strategy": strategy,
            "video_uri": final_video_uri,
        })

    return results
```

**Tracking Metadata:**
```python
# Add to combine() function
metadata = {
    "variation_id": variation_id,
    "strategy": strategy,
    "created_at": datetime.now().isoformat(),
    "product": product,
    "demographic": target_demographic,
}

# Store in BigQuery tracking table
client = bigquery.Client()
table_id = "your-project.content_generation.ad_variations"
client.insert_rows_json(table_id, [metadata])
```

### 7. Custom Product Selection with Semantic Search

**Use Case:** Improve product matching beyond exact text search.

**Implementation:**

**File:** `func_tools/select_product.py`

Replace exact match with vector search:
```python
from google.cloud import aiplatform
from google.cloud.aiplatform.matching_engine import MatchingEngineIndex

def select_product_semantic(query: str) -> Optional[Dict[str, Any]]:
    """Use embedding-based semantic search for products."""

    # Generate query embedding
    from vertexai.language_models import TextEmbeddingModel
    model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
    query_embedding = model.get_embeddings([query])[0].values

    # Search in Matching Engine index
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name="projects/{project}/locations/{location}/indexEndpoints/{id}"
    )

    neighbors = index_endpoint.find_neighbors(
        deployed_index_id="product_index",
        queries=[query_embedding],
        num_neighbors=1,
    )

    # Retrieve full product data from BigQuery
    product_id = neighbors[0][0].id
    client = bigquery.Client()
    query = f"""
        SELECT * FROM content_generation.media_assets
        WHERE product_id = '{product_id}'
    """
    result = client.query(query).result()
    return next(iter(result)).to_dict()
```

**Index Creation:**
```python
# Pre-compute embeddings for all products
# Store in Matching Engine for fast retrieval
```

---

**File References:**
- Main agent: `/home/user/adk-samples/python/agents/product-catalog-ad-generation/content_gen_agent/agent.py`
- Function tools: `/home/user/adk-samples/python/agents/product-catalog-ad-generation/content_gen_agent/func_tools/`
- Utilities: `/home/user/adk-samples/python/agents/product-catalog-ad-generation/content_gen_agent/utils/`
- Setup scripts: `/home/user/adk-samples/python/agents/product-catalog-ad-generation/scripts/`
- Deployment: `/home/user/adk-samples/python/agents/product-catalog-ad-generation/agent_engine_deploy.py`
- Configuration: `/home/user/adk-samples/python/agents/product-catalog-ad-generation/pyproject.toml`
