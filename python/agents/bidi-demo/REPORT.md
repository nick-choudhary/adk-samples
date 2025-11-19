# ADK Bidirectional Streaming Demo - Technical Documentation Report

## Project Scope

### High-Level Summary
The ADK Bidi-Demo is a working demonstration of real-time bidirectional streaming with Google's Agent Development Kit (ADK). This FastAPI application showcases WebSocket-based communication with Gemini models, demonstrating the complete lifecycle of Live API interactions including multimodal input (text, audio, image/video) and flexible output modalities (text or audio).

### Core Capabilities
- Real-time bidirectional streaming via WebSocket connections
- Multimodal input support: text messages, audio streams, images, and video
- Automatic audio transcription for both input and output
- Flexible response modalities based on model architecture
- Session resumption for reconnection support
- Concurrent upstream/downstream task management
- Interactive web UI with event console for monitoring
- Google Search tool integration

### Primary Use Cases
- Voice-enabled conversational AI applications
- Real-time video/image analysis with verbal responses
- Multimodal assistants requiring simultaneous text and audio
- Interactive demos of Gemini Live API capabilities
- Development foundation for production streaming applications
- Testing and prototyping bidirectional streaming patterns

### Target Users
- Developers building real-time conversational AI applications
- Engineers prototyping voice-enabled assistants
- Teams evaluating Gemini Live API capabilities
- Researchers exploring multimodal AI interactions
- Product teams building customer-facing voice interfaces

### Key Innovations/Differentiators
- Complete implementation of ADK's recommended concurrent task pattern
- Automatic modality detection based on model architecture
- Clean separation of WebSocket plumbing from agent logic
- Production-ready error handling and graceful termination
- Visual event console for debugging Live API interactions
- Reusable architecture for building custom streaming agents

## Technical Architecture

### Multi-Agent Hierarchy

```
┌────────────────────────────────────────────────────────────┐
│                   google_search_agent                       │
│                   (Single Agent System)                     │
│  - Model: gemini-2.5-flash-native-audio-preview            │
│  - Tools: [google_search]                                  │
│  - Handles both text and audio input/output                │
└────────────────────────────────────────────────────────────┘

APPLICATION ARCHITECTURE:
┌─────────────┐         ┌──────────────────┐         ┌─────────────┐
│             │         │                  │         │             │
│  WebSocket  │────────▶│ LiveRequestQueue │────────▶│  Live API   │
│   Client    │         │                  │         │   Session   │
│             │◀────────│   run_live()     │◀────────│             │
└─────────────┘         └──────────────────┘         └─────────────┘
  Upstream Task              Queue              Downstream Task
     (Lines 129-176)                               (Lines 178-191)

LIFECYCLE PHASES:
1. Application Initialization (Startup)
   - Create FastAPI app
   - Initialize InMemorySessionService
   - Create Runner with agent

2. Session Initialization (Per Connection)
   - Accept WebSocket connection
   - Configure RunConfig with modality detection
   - Create or retrieve Session
   - Initialize LiveRequestQueue

3. Active Session (Concurrent Communication)
   - Upstream: WebSocket → LiveRequestQueue
   - Downstream: run_live() → WebSocket
   - Both run concurrently via asyncio.gather()

4. Session Termination (Cleanup)
   - Close LiveRequestQueue
   - Handle WebSocket disconnect
   - Clean up resources
```

### Code Flow Explanation

**Application Initialization (Lines 37-54 in /home/user/adk-samples/python/agents/bidi-demo/app/main.py)**
1. FastAPI app created and static files mounted
2. `InMemorySessionService` instantiated for session management
3. `Runner` created with app_name="bidi-demo", agent, and session_service
4. Agent loaded from `/home/user/adk-samples/python/agents/bidi-demo/app/google_search_agent/agent.py` (lines 11-16)

**WebSocket Connection Handler (Lines 69-214 in main.py)**
1. Accept WebSocket connection at `/ws/{user_id}/{session_id}`
2. Detect model architecture (lines 83-84):
   - Native audio models: contain "native-audio" in name
   - Half-cascade models: all others
3. Configure RunConfig based on model type (lines 86-108):
   - Native audio: AUDIO response modality + transcription
   - Half-cascade: TEXT response modality for better performance
4. Get or create session (lines 111-121)
5. Create LiveRequestQueue for message passing (line 123)

**Concurrent Task Pattern (Lines 129-209 in main.py)**

*Upstream Task (lines 129-176):*
- Receives messages from WebSocket (text or binary)
- Binary frames: Audio data as PCM (lines 137-145)
  - Wraps in `types.Blob(mime_type="audio/pcm;rate=16000")`
  - Sends via `live_request_queue.send_realtime()`
- Text frames: JSON messages (lines 148-176)
  - Text type: Wraps in `types.Content` and sends via `send_content()`
  - Image type: Base64 decoded, wrapped as Blob, sent via `send_realtime()`

*Downstream Task (lines 178-191):*
- Calls `runner.run_live()` with queue and config
- Receives async stream of Event objects
- Serializes to JSON with `model_dump_json()`
- Sends to WebSocket client

**Graceful Termination (Lines 195-213 in main.py)**
- Catches `WebSocketDisconnect` exception
- Always closes LiveRequestQueue in finally block
- Logs all phases for debugging

### Agent Definitions with Roles and Responsibilities

| Agent Name | Type | File Location | Model | Tools | Responsibilities |
|------------|------|---------------|-------|-------|------------------|
| `google_search_agent` | Agent | google_search_agent/agent.py:11-16 | gemini-2.5-flash-native-audio-preview-09-2025 | google_search | Main agent handling all user interactions, web searches, and response generation |

**Agent Configuration:**
```python
agent = Agent(
    name="google_search_agent",
    model=os.getenv("DEMO_AGENT_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025"),
    tools=[google_search],
    instruction="You are a helpful assistant that can search the web."
)
```

### Key Libraries and Dependencies

**Core Dependencies**
- `fastapi` - Web framework for WebSocket server
- `uvicorn` - ASGI server implementation
- `google-adk` - Agent Development Kit framework
- `python-dotenv` - Environment variable management
- `certifi` - SSL certificate validation

**Frontend Dependencies**
- Vanilla JavaScript (no framework)
- Web Audio API for audio recording/playback
- WebSocket API for real-time communication
- Custom PCM audio processors (pcm-player-processor.js, pcm-recorder-processor.js)

**Python Version**
- Requires Python 3.10 or higher

### Tools and Integrations

**Built-in Tools**
- `google_search` (from google.adk.tools) - Web search via Gemini grounding
  - Integrated at agent level (line 14 in agent.py)
  - Automatically available to model during conversations

**Live API Integration**
- Gemini Live API (GOOGLE_API_KEY authentication)
- Vertex AI Live API (Google Cloud authentication)
- Automatic model selection via DEMO_AGENT_MODEL environment variable

**Audio Processing**
- PCM audio format: 16kHz, 16-bit
- Input: Microphone capture via MediaRecorder
- Output: Audio playback via AudioContext
- Transcription: Automatic via AudioTranscriptionConfig

### Reasoning Mechanisms

**Automatic Modality Detection (Lines 83-108 in main.py)**
```python
model_name = agent.model
is_native_audio = "native-audio" in model_name.lower()

if is_native_audio:
    # Native audio models ONLY support AUDIO response modality
    response_modalities = ["AUDIO"]
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=response_modalities,
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        session_resumption=types.SessionResumptionConfig(),
    )
else:
    # Half-cascade models use TEXT for better performance
    response_modalities = ["TEXT"]
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=response_modalities,
        # No audio transcription for text-only models
    )
```

**Session Resumption**
- Configured via `types.SessionResumptionConfig()` in RunConfig
- Enables reconnection to existing sessions
- Maintains conversation history across disconnections

## Build & Run Instructions

### Prerequisites

**Required Software**
- Python 3.10 or higher
- pip or uv package manager

**Required Accounts**
- Option A: Google AI Studio API Key
  - Get from: https://aistudio.google.com/apikey
  - Free tier available
- Option B: Google Cloud Project with Vertex AI enabled
  - Requires billing enabled
  - Need gcloud CLI installed

### Step-by-Step Installation

1. **Navigate to Demo Directory**
```bash
cd /path/to/adk-samples/python/agents/bidi-demo
```

2. **Create Virtual Environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -e .
```

4. **Set SSL Certificate Path**
```bash
export SSL_CERT_FILE=$(python -m certifi)
```

### Configuration (Environment Variables)

Create `app/.env` file with one of these configurations:

**Option 1: Gemini Live API (Google AI Studio)**
```bash
# Platform selection
GOOGLE_GENAI_USE_VERTEXAI=FALSE

# Authentication
GOOGLE_API_KEY=your_api_key_here

# Optional: Model selection
DEMO_AGENT_MODEL=gemini-2.5-flash-native-audio-preview-09-2025
```

**Option 2: Vertex AI Live API (Google Cloud)**
```bash
# Platform selection
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1

# Optional: Model selection
DEMO_AGENT_MODEL=gemini-live-2.5-flash-preview-native-audio-09-2025
```

**Supported Models**
- Native Audio (recommended for voice):
  - Gemini Live API: `gemini-2.5-flash-native-audio-preview-09-2025`
  - Vertex AI: `gemini-live-2.5-flash-preview-native-audio-09-2025`
- Half-Cascade (text-optimized):
  - Any standard Gemini model (e.g., `gemini-2.5-flash`)

### Running the Agent (CLI and Web UI)

**Development Mode (with auto-reload)**
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Production Mode (background)**
```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# Monitor logs
tail -f server.log

# Stop server
kill $(lsof -ti:8000)
```

**Access the Application**
```
Open browser: http://localhost:8000
```

### Example Interactions

**Text Mode Example**
```
User: (Types) "What were the major announcements at Google I/O 2024?"

Agent: (Searches web and responds)
"At Google I/O 2024, Google announced several major updates including:
1. Gemini 1.5 Pro with extended context window...
2. Project Astra for multimodal AI assistants...
[continues with detailed information]"

Event Console Shows:
- serverSetup event
- toolCall: google_search
- toolCallCancellationEvent
- toolResponse
- modelTurn with response text
```

**Audio Mode Example**
```
User: (Clicks "Start Audio", speaks) "Tell me about the latest in quantum computing"

Event Console Shows:
- realtimeInput (audio chunks being sent)
- inputAudioTranscript (live transcription of user speech)
- toolCall: google_search (if search needed)
- modelTurn with audio response
- outputAudioTranscript (transcription of agent's speech)

Agent: (Speaks response with simultaneous audio playback and text transcription)
```

**Image Analysis Example**
```
User: (Uploads image of a chart)
"Explain what this chart shows"

Event Console Shows:
- realtimeInput (image data)
- modelTurn with analysis

Agent: "This appears to be a bar chart showing quarterly revenue...
[detailed analysis of the image]"
```

### Testing and Evaluation

**Manual Testing Checklist**
- [ ] Text input and response working
- [ ] Audio recording and playback functional
- [ ] Image upload and analysis working
- [ ] Google search tool being invoked correctly
- [ ] Event console showing all Live API events
- [ ] Session resumption working after disconnect
- [ ] Transcriptions appearing for audio I/O

**Testing Different Modalities**
```bash
# Test with native audio model
DEMO_AGENT_MODEL=gemini-2.5-flash-native-audio-preview-09-2025 uvicorn main:app --reload

# Test with text-optimized model
DEMO_AGENT_MODEL=gemini-2.5-flash uvicorn main:app --reload
```

**Performance Metrics**
- Audio latency: Typically < 500ms for native audio models
- WebSocket connection stability
- Event stream continuity
- Memory usage during long sessions

### Deployment (Optional)

**Cloud Run Deployment**
```bash
# Build container
docker build -t bidi-demo .

# Deploy to Cloud Run
gcloud run deploy bidi-demo \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Security Considerations**
- Use HTTPS in production (WebSocket Secure)
- Implement authentication for `/ws/` endpoint
- Add rate limiting to prevent abuse
- Validate all client inputs
- Set up CORS properly for frontend

### Troubleshooting

**Issue: WebSocket fails to connect**
- Verify server is running: `curl http://localhost:8000`
- Check browser console for errors
- Ensure API credentials are valid in .env
- Try clearing browser cache and cookies

**Issue: Audio not working**
- Grant microphone permissions in browser
- Check browser compatibility (Chrome/Edge recommended)
- Verify model supports audio: must contain "native-audio"
- Check SSL certificate: `echo $SSL_CERT_FILE`

**Issue: Model errors or quota exceeded**
- Verify model name matches your platform (Gemini vs Vertex AI)
- Check API quota limits in console
- Ensure billing enabled (for Vertex AI)
- Try switching to different model

**Issue: Events not showing in console**
- Check WebSocket connection status
- Verify event serialization in downstream_task
- Look for JavaScript errors in browser console

**Issue: Session not resuming**
```python
# Verify session_resumption is configured in RunConfig
session_resumption=types.SessionResumptionConfig()
```

## Customization Options

### 1. Change Agent Model and Instructions

**File:** `/home/user/adk-samples/python/agents/bidi-demo/app/google_search_agent/agent.py`

Modify the agent to use different model or instructions:
```python
agent = Agent(
    name="specialized_research_agent",
    model="gemini-2.5-pro",  # Use more powerful model
    tools=[google_search],
    instruction="""You are a specialized research assistant focused on academic topics.
    When users ask questions:
    1. Always search for peer-reviewed sources first
    2. Cite your sources with publication dates
    3. Provide in-depth technical explanations
    4. Use formal academic language"""
)
```

**Impact:** Changes the agent's behavior, personality, and response quality. Using Pro model increases accuracy but costs more.

### 2. Add Custom Tools

**File:** Create `/home/user/adk-samples/python/agents/bidi-demo/app/custom_tools.py`

Add domain-specific tools:
```python
from google.adk.tools import Tool
from pydantic import BaseModel

class WeatherQuery(BaseModel):
    location: str
    units: str = "celsius"

def get_weather(location: str, units: str = "celsius") -> str:
    """Get current weather for a location."""
    # Your weather API integration here
    return f"Weather in {location}: 22°{units[0].upper()}, sunny"

weather_tool = Tool(
    name="get_weather",
    description="Get current weather conditions for a location",
    input_schema=WeatherQuery,
    function=get_weather
)
```

Then add to agent:
```python
from custom_tools import weather_tool

agent = Agent(
    name="google_search_agent",
    model=os.getenv("DEMO_AGENT_MODEL"),
    tools=[google_search, weather_tool],  # Add custom tool
    instruction="You can search the web and check weather conditions."
)
```

**Impact:** Extends agent capabilities with custom functionality beyond web search.

### 3. Customize Audio Processing Parameters

**File:** `/home/user/adk-samples/python/agents/bidi-demo/app/main.py` (lines 86-108)

Adjust audio configuration for different use cases:
```python
if is_native_audio:
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        session_resumption=types.SessionResumptionConfig(),
        # Add speech configuration
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Puck"  # Change voice
                )
            ),
            language_code="es-ES"  # Change language
        ),
        # Adjust activity detection sensitivity
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
                end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_LOW,
                prefix_padding_ms=100,
                silence_duration_ms=300
            )
        )
    )
```

**Impact:** Customizes voice characteristics, language, and speech detection sensitivity for different user experiences.

### 4. Add Authentication and Authorization

**File:** `/home/user/adk-samples/python/agents/bidi-demo/app/main.py`

Implement user authentication:
```python
from fastapi import WebSocket, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token or API key."""
    token = credentials.credentials
    # Your token verification logic
    if not is_valid_token(token):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return get_user_from_token(token)

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: str,
    user: dict = Depends(verify_token)  # Require auth
):
    # Verify user_id matches authenticated user
    if user["id"] != user_id:
        await websocket.close(code=1008)  # Policy violation
        return

    await websocket.accept()
    # ... rest of the code
```

**Impact:** Secures the WebSocket endpoint and enables user-specific sessions and quotas.

### 5. Implement Message History and Session Persistence

**File:** `/home/user/adk-samples/python/agents/bidi-demo/app/main.py`

Add session persistence beyond in-memory:
```python
from google.adk.sessions import CloudStorageSessionService

# Replace InMemorySessionService
session_service = CloudStorageSessionService(
    bucket_name="your-sessions-bucket",
    project_id=os.getenv("GOOGLE_CLOUD_PROJECT")
)

runner = Runner(
    app_name=APP_NAME,
    agent=agent,
    session_service=session_service  # Use cloud storage
)
```

Add session export endpoint:
```python
@app.get("/sessions/{user_id}/{session_id}/history")
async def get_session_history(user_id: str, session_id: str):
    """Export session conversation history."""
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id
    )

    history = []
    for event in session.events:
        if event.content:
            history.append({
                "author": event.author,
                "timestamp": event.timestamp,
                "text": event.content.parts[0].text if event.content.parts else None
            })

    return {"session_id": session_id, "history": history}
```

**Impact:** Enables long-term session storage, conversation export, and analytics.

### 6. Add Real-Time Streaming Metrics

**File:** Create `/home/user/adk-samples/python/agents/bidi-demo/app/metrics.py`

Track and expose metrics:
```python
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class StreamingMetrics:
    session_id: str
    start_time: datetime
    messages_sent: int = 0
    messages_received: int = 0
    audio_chunks_sent: int = 0
    audio_chunks_received: int = 0
    total_latency_ms: float = 0.0

class MetricsCollector:
    def __init__(self):
        self.sessions = {}

    def track_event(self, session_id: str, event_type: str, latency_ms: float = 0):
        if session_id not in self.sessions:
            self.sessions[session_id] = StreamingMetrics(
                session_id=session_id,
                start_time=datetime.now()
            )

        metrics = self.sessions[session_id]
        if event_type == "message_sent":
            metrics.messages_sent += 1
        elif event_type == "audio_chunk":
            metrics.audio_chunks_sent += 1

        metrics.total_latency_ms += latency_ms

    def get_metrics(self, session_id: str):
        return self.sessions.get(session_id)
```

Integrate into main.py:
```python
metrics_collector = MetricsCollector()

async def downstream_task():
    async for event in runner.run_live(...):
        start = asyncio.get_event_loop().time()
        event_json = event.model_dump_json(exclude_none=True, by_alias=True)
        await websocket.send_text(event_json)

        latency = (asyncio.get_event_loop().time() - start) * 1000
        metrics_collector.track_event(session_id, "message_received", latency)

@app.get("/metrics/{session_id}")
async def get_metrics(session_id: str):
    return metrics_collector.get_metrics(session_id)
```

**Impact:** Provides real-time performance monitoring, latency tracking, and usage analytics.

### 7. Support Video Streaming

**File:** `/home/user/adk-samples/python/agents/bidi-demo/app/main.py` (upstream_task)

Add video frame processing:
```python
async def upstream_task():
    while True:
        message = await websocket.receive()

        # Handle video frames
        if "bytes" in message and len(message["bytes"]) > 10000:  # Likely video
            video_data = message["bytes"]
            logger.debug(f"Received video frame: {len(video_data)} bytes")

            video_blob = types.Blob(
                mime_type="video/mp4",  # or detect from headers
                data=video_data
            )
            live_request_queue.send_realtime(video_blob)

        # ... existing code for audio and text
```

Update frontend to capture video:
```javascript
// In static/js/app.js
const videoStream = await navigator.mediaDevices.getUserMedia({
    video: { width: 1280, height: 720 }
});

const videoRecorder = new MediaRecorder(videoStream, {
    mimeType: 'video/webm;codecs=vp9'
});

videoRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) {
        websocket.send(event.data);  // Send as binary
    }
};
```

**Impact:** Enables real-time video analysis, visual assistance, and multimodal interactions combining video, audio, and text.

---

**Additional Resources:**
- ADK Documentation: https://google.github.io/adk-docs/
- Gemini Live API Docs: https://ai.google.dev/gemini-api/docs/live
- Vertex AI Live API: https://cloud.google.com/vertex-ai/generative-ai/docs/live-api
- WebSocket Protocol: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
