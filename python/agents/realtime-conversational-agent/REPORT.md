# Real-Time Conversational Agent Template - Technical Documentation Report

## Project Scope

### High-Level Summary
The Real-Time Conversational Agent Template is a production-ready, full-stack foundation for building multimodal conversational AI applications. Built on ADK (backend) and Next.js (frontend), this template handles all complex WebSocket and media streaming infrastructure, allowing developers to focus entirely on agent logic and user experience. It demonstrates the power of Gemini's Live API with native audio support for real-time, bidirectional audio/video conversations.

### Core Capabilities
- Real-time bidirectional audio streaming with natural conversation flow
- Live video feed processing from camera or screen share
- Simultaneous audio transcription (Speech-to-Text and Text-to-Speech)
- Automatic activity detection for turn-taking
- Configurable agent persona and voice characteristics
- Clean separation of streaming infrastructure from business logic
- Production-ready error handling and reconnection logic
- Reusable architecture for any real-time AI application

### Primary Use Cases
- Real-time tutoring and educational assistance (default: math tutor)
- Live customer support with visual guidance
- Accessibility tools (visual description, screen reading)
- Interactive assistants with multimodal context
- Remote collaboration and pair programming
- Real-time translation and interpretation
- Healthcare consultation with visual examination

### Target Users
- Developers building voice-enabled AI applications
- Product teams creating real-time customer experiences
- Educational technology companies
- Accessibility solution providers
- Enterprise teams requiring live AI assistance
- Startups prototyping conversational AI products

### Key Innovations/Differentiators
- Complete abstraction of WebSocket/media streaming complexity
- Zero configuration needed for basic use cases
- Single-file persona customization (no code changes required)
- Native audio support with natural voice characteristics
- Automatic activity detection for smooth conversations
- Production-ready client-server architecture
- Reusable across all industry verticals
- Educational example (math tutor) demonstrating best practices

## Technical Architecture

### Multi-Agent Hierarchy

```
┌────────────────────────────────────────────────────────────┐
│                   example_agent (Root)                      │
│                   (Single Agent System)                     │
│  - Model: gemini-live-2.5-flash-preview-native-audio       │
│  - Persona: Expert Math Tutor (configurable)               │
│  - Voice: Puck (configurable)                              │
│  - Language: en-US (configurable)                          │
└────────────────────────────────────────────────────────────┘

FULL-STACK ARCHITECTURE:

┌─────────────────────────────────────────────────────────────┐
│                     Client (Next.js/React)                  │
│  Location: /client                                          │
│  ┌───────────────────────────────────────────────────┐     │
│  │  UI Components                                    │     │
│  │  - Microphone control                             │     │
│  │  - Video feed (camera/screen share)               │     │
│  │  - Live transcriptions display                    │     │
│  │  - Audio playback                                 │     │
│  └───────────────────────────────────────────────────┘     │
│  ┌───────────────────────────────────────────────────┐     │
│  │  Media Handlers                                   │     │
│  │  - AudioRecorder: Capture microphone              │     │
│  │  - AudioPlayer: Play agent voice                  │     │
│  │  - VideoCapture: Camera/screen share              │     │
│  │  - WebSocket client                               │     │
│  └───────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                           │
                    WebSocket Connection
                    (Concurrent Tasks)
                           │
┌─────────────────────────────────────────────────────────────┐
│                  Server (FastAPI + ADK)                     │
│  Location: /server                                          │
│  ┌───────────────────────────────────────────────────┐     │
│  │  WebSocket Endpoint: /ws/{user_id}                │     │
│  │  ┌─────────────────────────────────────────┐     │     │
│  │  │  Client → Agent (upstream)              │     │     │
│  │  │  - Receives text/audio/video messages   │     │     │
│  │  │  - Converts to LiveRequestQueue format  │     │     │
│  │  │  - Base64 decode for binary data        │     │     │
│  │  └─────────────────────────────────────────┘     │     │
│  │  ┌─────────────────────────────────────────┐     │     │
│  │  │  Agent → Client (downstream)            │     │     │
│  │  │  - Receives Events from run_live()      │     │     │
│  │  │  - Extracts transcriptions & audio      │     │     │
│  │  │  - Formats structured messages          │     │     │
│  │  │  - Base64 encode audio for transport    │     │     │
│  │  └─────────────────────────────────────────┘     │     │
│  └───────────────────────────────────────────────────┘     │
│  ┌───────────────────────────────────────────────────┐     │
│  │  ADK Integration                                  │     │
│  │  - InMemoryRunner                                 │     │
│  │  - Session management                             │     │
│  │  - LiveRequestQueue                               │     │
│  │  - RunConfig with Live API settings               │     │
│  └───────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                           │
                    Gemini Live API
                           │
┌─────────────────────────────────────────────────────────────┐
│                     Gemini Live API                         │
│  - Native audio processing                                  │
│  - Real-time speech understanding                           │
│  - Natural voice synthesis                                  │
│  - Multimodal (audio + video) analysis                      │
│  - Automatic transcription                                  │
└─────────────────────────────────────────────────────────────┘

MESSAGE FLOW:

User speaks → Microphone captures → AudioRecorder →
PCM audio chunks → WebSocket send (base64) →
Server upstream_task → Decode → LiveRequestQueue.send_realtime() →
Gemini Live API processes →
Events stream back → Server downstream_task →
Extract audio + transcription → Base64 encode →
WebSocket send (JSON) → Client receives →
AudioPlayer plays + UI shows transcription
```

### Code Flow Explanation

**Server Initialization (Lines 29-78 in /home/user/adk-samples/python/agents/realtime-conversational-agent/server/main.py)**

`start_agent_session(user_id)` function:
1. Create `InMemoryRunner` with app_name and agent (lines 33-36)
2. Create new session for user (lines 39-42)
3. Initialize `LiveRequestQueue` for message passing (line 45)
4. Configure `RunConfig` with Live API settings (lines 48-70):
   - Streaming mode: bidirectional
   - Session resumption: transparent
   - Automatic activity detection for turn-taking:
     - Start sensitivity: LOW (more tolerant of background noise)
     - End sensitivity: HIGH (quick turn completion)
     - Zero padding/silence for immediate responses
   - Response modalities: AUDIO (native voice)
   - Speech config: Voice (Puck), Language (en-US)
   - Audio transcription: Both input and output
5. Start `run_live()` generator (lines 73-77)
6. Return live_events stream and queue

**WebSocket Connection (Lines 188-213 in main.py)**
1. Accept WebSocket connection at `/ws/{user_id}`
2. Call `start_agent_session()` to initialize
3. Create concurrent tasks:
   - `agent_to_client_messaging`: Downstream (lines 81-150)
   - `client_to_agent_messaging`: Upstream (lines 152-183)
4. Run with `asyncio.wait(tasks, return_when=FIRST_EXCEPTION)`
5. On disconnect/error: Close LiveRequestQueue

**Upstream Task: Client → Agent (Lines 152-183)**
1. Receive JSON message from WebSocket (line 156)
2. Parse mime_type and data (lines 158-159)
3. Route by mime type:
   - `text/plain`: Create Content with text Part (lines 160-163)
   - `audio/pcm`: Base64 decode, create Blob (lines 165-168)
   - `image/jpeg`: Base64 decode, create Blob (lines 170-173)
4. Send to LiveRequestQueue:
   - Text: `send_content(content)`
   - Audio/Image: `send_realtime(blob)`

**Downstream Task: Agent → Client (Lines 81-150)**
1. Iterate over Events from `run_live()` (line 83)
2. Construct structured message (lines 85-93):
   ```python
   {
     "author": "agent",
     "is_partial": bool,
     "turn_complete": bool,
     "interrupted": bool,
     "parts": [],  # Audio, text, function calls
     "input_transcription": {},  # User speech → text
     "output_transcription": {}  # Agent speech → text
   }
   ```
3. Process event content:
   - User role (lines 102-107): Extract input transcription
   - Model role (lines 109-139):
     - Extract output transcription (lines 110-115)
     - Extract audio (lines 117-121): Base64 encode PCM data
     - Extract function calls/responses (lines 123-139)
4. Send to WebSocket as JSON (line 147)

**Agent Definition (Lines 15-20 in /home/user/adk-samples/python/agents/realtime-conversational-agent/server/example_agent/agent.py)**
```python
root_agent = Agent(
    name="example_agent",
    model="gemini-live-2.5-flash-preview-native-audio",
    description="A helpful AI assistant.",
    instruction=AGENT_INSTRUCTION  # From prompts.py
)
```

### Agent Definitions with Roles and Responsibilities

| Agent Name | Type | File Location | Model | Responsibilities |
|------------|------|---------------|-------|------------------|
| `example_agent` | Agent | example_agent/agent.py:15-20 | gemini-live-2.5-flash-preview-native-audio | Math tutor using Socratic method; guides students through problem-solving without giving answers; provides encouragement and conceptual hints |

**Persona Configuration (prompts.py:1-29)**
- Core Philosophy: Socratic method teaching
- Never give final answers, always guide
- Ask leading questions to help discover solutions
- Encourage step-by-step thinking
- Patient and positive reinforcement
- Handle requests for direct answers gracefully
- Verify understanding before concluding

### Key Libraries and Dependencies

**Server Dependencies**
- `google-adk` - Agent Development Kit
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-dotenv` - Environment management
- `certifi` - SSL certificates
- Python 3.11+ required

**Client Dependencies (package.json)**
- `next`: ^15.1.4 - React framework
- `react`: ^19.0.0 - UI library
- `tailwindcss`: ^3.4.1 - Styling
- `@radix-ui/*` - Accessible UI components
- `lucide-react` - Icon library
- TypeScript for type safety

**Audio Processing**
- PCM audio format: 16kHz, mono
- MediaRecorder API (browser)
- AudioContext and AudioWorklet
- Web Audio API for playback

### Tools and Integrations

**Gemini Live API Integration**
- Model: `gemini-live-2.5-flash-preview-native-audio`
- Native audio processing (no TTS/STT pipeline)
- Multimodal input (audio + video + text)
- Automatic activity detection
- Session resumption support

**Voice Configuration**
Available voices for Gemini Live models:
- Puck (default) - Friendly and approachable
- Charon - Professional and clear
- Kore - Warm and empathetic
- Fenrir - Authoritative
- Aoede - Melodic

**Activity Detection**
```python
automatic_activity_detection=types.AutomaticActivityDetection(
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
    prefix_padding_ms=0,
    silence_duration_ms=0
)
```

### Reasoning Mechanisms

**Socratic Teaching Method (prompts.py)**
The agent implements a sophisticated pedagogical approach:

1. **Never provide answers** - Forces student engagement
2. **Ask leading questions** - Guides discovery
3. **Break down problems** - Encourages systematic thinking
4. **Identify errors gently** - Maintains confidence
5. **Provide conceptual hints** - Enables transfer learning
6. **Verify understanding** - Solidifies knowledge

**Example Teaching Flow:**
```
Student: "What's the answer to x^2 + 5x + 6 = 0?"

Agent: "Great question! Let's work through this together. What have you learned about solving quadratic equations? What methods do you know?"

Student: "Factoring?"

Agent: "Excellent! Factoring is perfect for this. When we factor, we're looking for two numbers. What relationship do these numbers need to have with the coefficients?"

Student: "They multiply to 6 and add to 5?"

Agent: "Exactly right! So what two numbers multiply to 6 and add to 5?"

Student: "2 and 3?"

Agent: "Perfect! Now how do we write that as factors? What does the factored form look like?"

Student: "(x + 2)(x + 3) = 0"

Agent: "Excellent work! Now, what does that tell us about the values of x?"

Student: "x = -2 or x = -3"

Agent: "Outstanding! Can you explain why those are the solutions? I want to make sure you understand the reasoning."
```

## Build & Run Instructions

### Prerequisites

**Required Software**
- Node.js v22 or later
- Python 3.11 or later
- `uv` (recommended): `pip install uv`

**Required Accounts**
Choose one platform:

**Option 1: Google AI Studio (Simpler)**
- Get API key from: https://aistudio.google.com/

**Option 2: Google Cloud / Vertex AI**
- Google Cloud Project with Vertex AI API enabled
- Google Cloud CLI installed
- Authenticated: `gcloud auth login`

### Step-by-Step Installation

**Server Setup**

1. Navigate to server directory:
```bash
cd realtime-conversational-agent/server
```

2. Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. Install Python dependencies:
```bash
uv pip install .
```

4. Set SSL certificate:
```bash
export SSL_CERT_FILE=$(python -m certifi)
```

**Client Setup**

1. Open new terminal, navigate to client:
```bash
cd realtime-conversational-agent/client
```

2. Install Node.js dependencies:
```bash
npm install
```

### Configuration (Environment Variables)

Create `server/.env` file:

**Option 1: Google AI Studio**
```bash
# Platform
GOOGLE_GENAI_USE_VERTEXAI=FALSE

# Authentication
GOOGLE_API_KEY="YOUR_ACTUAL_API_KEY"

# Voice Configuration
AGENT_VOICE="Puck"
AGENT_LANGUAGE="en-US"
```

**Option 2: Google Cloud / Vertex AI**
```bash
# Platform
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Google Cloud
GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
GOOGLE_CLOUD_LOCATION="us-central1"

# Voice Configuration
AGENT_VOICE="Puck"
AGENT_LANGUAGE="en-US"
```

**Available Configurations**
- Voices: Puck, Charon, Kore, Fenrir, Aoede
- Languages: en-US, en-GB, es-ES, fr-FR, de-DE, ja-JP, etc.
- Model: gemini-live-2.5-flash-preview-native-audio (default)

### Running the Agent (CLI and Web UI)

**Start Server**
```bash
cd server
uvicorn main:app --reload
# Server runs at http://127.0.0.1:8000
```

**Start Client (New Terminal)**
```bash
cd client
npm run dev
# Client runs at http://localhost:3000
```

**Access Application**
```
Open browser: http://localhost:3000
Click microphone icon to start conversation
```

### Example Interactions

**Example 1: Math Tutoring Session**
```
[User clicks microphone, shares screen with math problem]

User: (Speaks) "I'm stuck on this problem: Find the area of a circle with radius 5."

Agent: (Speaks with transcription shown)
"Great! I can see the problem. Let's think about this together. Do you remember the formula for the area of a circle?"

User: "Um, pi r squared?"

Agent: "Exactly! π r². Now, what's our radius in this problem?"

User: "It's 5."

Agent: "Perfect! So what would we substitute into the formula?"

User: "π times 5 squared?"

Agent: "Yes! And what's 5 squared?"

User: "25"

Agent: "Excellent! So what's our full expression?"

User: "π times 25, which is 25π"

Agent: "Outstanding work! Can you tell me in your own words why we square the radius?"

User: "Because that's the formula?"

Agent: "That's true, but why do you think the formula uses r squared instead of just r? What does the area measure?"

User: "Oh! Because area is two-dimensional, so we multiply radius by itself?"

Agent: "Brilliant insight! You've really understood this. Great job working through that!"
```

**Example 2: Screen Share Assistance**
```
[User shares screen showing code with error]

User: "I don't understand why this code isn't working."

Agent: "I can see your screen. Let's investigate together. Can you walk me through what you're trying to accomplish with this code?"

User: "I'm trying to add these two numbers."

Agent: "I see. Let's look at line 3. What operation are you using there?"

User: "Oh! I used a minus instead of plus!"

Agent: "Excellent catch! You found it yourself. That's exactly the kind of careful checking that makes a great programmer."
```

**Example 3: Multilingual Support**
```
# Change server/.env: AGENT_LANGUAGE="es-ES"

User: (Speaks in Spanish) "No entiendo este problema de matemáticas"

Agent: (Responds in Spanish)
"¡Claro! Vamos a trabajar juntos. ¿Qué parte del problema te confunde más?"
```

### Testing and Evaluation

**Functionality Tests**
- [ ] Audio input captured correctly
- [ ] Agent responds with voice
- [ ] Input transcription appears in real-time
- [ ] Output transcription synchronized with audio
- [ ] Video feed visible when shared
- [ ] Turn-taking natural (no overlapping)
- [ ] Session maintains context across turns

**Performance Metrics**
- Audio latency: < 500ms for responses
- Transcription accuracy: > 95% for clear speech
- Turn detection: Minimal false triggers
- Memory usage: Stable over long sessions

**Browser Testing**
- Chrome/Edge: Full support (recommended)
- Firefox: Audio/video supported
- Safari: May have WebSocket limitations

### Deployment (Optional)

**Docker Deployment**

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY server/ .

RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t realtime-agent .
docker run -p 8000:8000 --env-file server/.env realtime-agent
```

**Cloud Run Deployment**
```bash
gcloud run deploy realtime-agent \
  --source ./server \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Production Considerations**
- Use HTTPS for WebSocket security
- Implement rate limiting
- Add authentication
- Set up monitoring and logging
- Configure auto-scaling
- Use production-grade session storage

### Troubleshooting

**Issue: Microphone not working**
- Grant browser microphone permissions
- Check browser console for errors
- Verify HTTPS (required for getUserMedia)
- Test with different browsers

**Issue: No audio playback**
- Check browser audio permissions
- Verify speakers/headphones connected
- Look for audio codec errors in console
- Try refreshing page

**Issue: WebSocket connection fails**
- Verify server is running on port 8000
- Check firewall settings
- Look for CORS errors
- Ensure SSL_CERT_FILE is set

**Issue: Transcriptions not appearing**
- Verify RunConfig includes transcription settings
- Check event processing in downstream_task
- Look for JSON parsing errors
- Test with simpler audio

**Issue: Agent gives direct answers**
- Verify AGENT_INSTRUCTION loaded correctly
- Check prompts.py is not modified
- Restart server after changing prompts
- Test with explicit "don't tell me the answer" phrasing

## Customization Options

### 1. Change Agent Persona (Zero Code Changes)

**File:** `/home/user/adk-samples/python/agents/realtime-conversational-agent/server/example_agent/prompts.py`

Transform the math tutor into any persona:

**Example: Generic Assistant**
```python
AGENT_INSTRUCTION = """
You are a helpful and friendly AI assistant. Keep your responses concise.
"""
```

**Example: Customer Support Agent**
```python
AGENT_INSTRUCTION = """
You are a professional customer support agent for TechCorp.

Your responsibilities:
1. Greet customers warmly
2. Identify their issue clearly
3. Provide step-by-step troubleshooting
4. Escalate to human agent if needed (say "Let me connect you with a specialist")
5. Always end with "Is there anything else I can help you with?"

Company policies:
- Returns accepted within 30 days
- Premium support available 24/7
- Standard warranty: 1 year
"""
```

**Example: Language Learning Tutor**
```python
AGENT_INSTRUCTION = """
You are a patient Spanish language tutor. When the user speaks English, respond in Spanish.
Correct their mistakes gently by repeating the phrase correctly, then continue the conversation.

Example:
User: "Yo es un estudiante"
You: "Casi! Decimos 'Yo SOY un estudiante.' ¡Muy bien! ¿Qué estudias?"
"""
```

**Impact:** Complete persona transformation without any code changes. Just edit one file and restart server.

### 2. Add Tools and Function Calling

**File:** `/home/user/adk-samples/python/agents/realtime-conversational-agent/server/example_agent/agent.py`

Add real-time tool access:

```python
from google.adk.tools import Tool
from pydantic import BaseModel
import requests

class WeatherQuery(BaseModel):
    location: str

def get_weather(location: str) -> str:
    """Get current weather for a location."""
    # Your weather API integration
    api_key = os.getenv("WEATHER_API_KEY")
    response = requests.get(
        f"https://api.weather.com/v1/current",
        params={"location": location, "key": api_key}
    )
    data = response.json()
    return f"Weather in {location}: {data['temperature']}°F, {data['conditions']}"

weather_tool = Tool(
    name="get_weather",
    description="Get current weather conditions",
    input_schema=WeatherQuery,
    function=get_weather
)

root_agent = Agent(
    name="example_agent",
    model="gemini-live-2.5-flash-preview-native-audio",
    tools=[weather_tool],  # Add tools here
    instruction="""You are a helpful assistant with access to weather information.
    When users ask about weather, use the get_weather tool."""
)
```

**Impact:** Enables real-time information retrieval during voice conversations.

### 3. Customize Voice and Speech Parameters

**File:** `/home/user/adk-samples/python/agents/realtime-conversational-agent/server/main.py` (lines 60-67)

Fine-tune voice characteristics:

```python
speech_config=types.SpeechConfig(
    voice_config=types.VoiceConfig(
        prebuilt_voice_config=types.PrebuiltVoiceConfig(
            voice_name="Charon"  # Change voice: Puck, Charon, Kore, Fenrir, Aoede
        )
    ),
    language_code="en-GB",  # British English
    # Add custom parameters
    speaking_rate=1.2,  # Faster speech
    pitch=0.5,  # Lower pitch
    volume_gain_db=2.0  # Louder
)
```

**Impact:** Customizes voice personality to match brand or use case.

### 4. Implement Multi-User Session Management

**File:** Create `/home/user/adk-samples/python/agents/realtime-conversational-agent/server/session_manager.py`

Support multiple concurrent users:

```python
from google.adk.sessions import CloudStorageSessionService

class MultiUserSessionManager:
    def __init__(self):
        self.sessions = {}
        self.session_service = CloudStorageSessionService(
            bucket_name=os.getenv("SESSION_BUCKET")
        )

    async def get_or_create_session(self, user_id: str):
        """Get existing session or create new one."""
        if user_id not in self.sessions:
            session = await self.session_service.create_session(
                app_name=os.getenv("APP_NAME"),
                user_id=user_id
            )
            self.sessions[user_id] = session

        return self.sessions[user_id]

    async def cleanup_inactive_sessions(self):
        """Remove sessions inactive for > 30 minutes."""
        # Implementation for cleanup
        pass

# Use in main.py
session_manager = MultiUserSessionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    session = await session_manager.get_or_create_session(user_id)
    # ... rest of code
```

**Impact:** Enables scalable multi-user deployment with session persistence.

### 5. Add Real-Time Emotion Detection

**File:** Create `/home/user/adk-samples/python/agents/realtime-conversational-agent/server/emotion_analyzer.py`

Analyze user emotion from voice:

```python
from google.cloud import speech_v1p1beta1 as speech

class EmotionAnalyzer:
    def __init__(self):
        self.client = speech.SpeechClient()

    def analyze_emotion(self, audio_data: bytes) -> str:
        """Detect emotion from audio characteristics."""
        # Use Google Cloud Speech-to-Text with emotion detection
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True,
            # Enable emotion detection in beta API
            metadata=speech.RecognitionMetadata(
                interaction_type=speech.RecognitionMetadata.InteractionType.DISCUSSION,
                microphone_distance=speech.RecognitionMetadata.MicrophoneDistance.NEARFIELD
            )
        )

        audio = speech.RecognitionAudio(content=audio_data)
        response = self.client.recognize(config=config, audio=audio)

        # Extract emotion from response
        # (Implementation depends on API features)
        return "neutral"

# Integrate into upstream task
emotion_analyzer = EmotionAnalyzer()

async def client_to_agent_messaging(websocket, live_request_queue):
    while True:
        message = await websocket.receive_text()
        data = json.loads(message)

        if data["mime_type"] == "audio/pcm":
            audio_bytes = base64.b64decode(data["data"])

            # Detect emotion
            emotion = emotion_analyzer.analyze_emotion(audio_bytes)

            # Add to agent context
            context_msg = f"[User emotion detected: {emotion}]"
            live_request_queue.send_content(
                Content(role="user", parts=[Part.from_text(text=context_msg)])
            )

            # Send audio
            live_request_queue.send_realtime(Blob(data=audio_bytes, mime_type="audio/pcm"))
```

Update agent instruction:
```python
AGENT_INSTRUCTION = """
You are an empathetic assistant. Pay attention to emotional cues indicated in brackets.
Adjust your tone accordingly - be more supportive if user seems frustrated or stressed.
"""
```

**Impact:** Creates emotionally intelligent agent that adapts to user's state.

### 6. Implement Screen Annotation

**File:** Create client-side annotation overlay

Add to `client/app/page.tsx`:

```typescript
import { useState } from 'react';

export default function AnnotationOverlay() {
  const [annotations, setAnnotations] = useState([]);

  const handleAgentAnnotation = (event) => {
    // When agent says "circle this part" or "draw attention to X"
    // Parse location from vision analysis
    const annotation = {
      x: event.coordinates.x,
      y: event.coordinates.y,
      text: event.annotation_text,
      type: "circle" // or "arrow", "highlight"
    };

    setAnnotations([...annotations, annotation]);
  };

  return (
    <div className="annotation-layer">
      {annotations.map((ann, idx) => (
        <div
          key={idx}
          className={`annotation annotation-${ann.type}`}
          style={{ left: ann.x, top: ann.y }}
        >
          {ann.text}
        </div>
      ))}
    </div>
  );
}
```

Update agent instruction:
```python
AGENT_INSTRUCTION = """
You are a visual tutor. When looking at the user's screen:
1. Reference specific parts: "Look at the top right corner"
2. Guide attention: "Focus on line 5 of the code"
3. Request annotations: "Let me highlight the important part for you"
"""
```

**Impact:** Creates interactive visual guidance for complex problems.

### 7. Add Conversation Recording and Playback

**File:** Create `/home/user/adk-samples/python/agents/realtime-conversational-agent/server/recorder.py`

Record sessions for review:

```python
import json
from datetime import datetime
from pathlib import Path

class ConversationRecorder:
    def __init__(self, recordings_dir="recordings"):
        self.recordings_dir = Path(recordings_dir)
        self.recordings_dir.mkdir(exist_ok=True)
        self.current_recording = None

    def start_recording(self, user_id: str, session_id: str):
        """Start recording a conversation."""
        timestamp = datetime.now().isoformat()
        filename = f"{user_id}_{session_id}_{timestamp}.jsonl"
        self.current_recording = open(
            self.recordings_dir / filename, "w"
        )

    def record_event(self, event_type: str, data: dict):
        """Record an event in the conversation."""
        if self.current_recording:
            record = {
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "data": data
            }
            self.current_recording.write(json.dumps(record) + "\n")
            self.current_recording.flush()

    def stop_recording(self):
        """Stop and save recording."""
        if self.current_recording:
            self.current_recording.close()
            self.current_recording = None

# Integrate into WebSocket handler
recorder = ConversationRecorder()

async def agent_to_client_messaging(websocket, live_events, user_id, session_id):
    recorder.start_recording(user_id, session_id)

    async for event in live_events:
        # Record event
        recorder.record_event("agent_output", {
            "audio": event.audio_base64 if hasattr(event, 'audio_base64') else None,
            "transcription": event.transcription,
            "timestamp": event.timestamp
        })

        # Send to client as usual
        await websocket.send_text(event_json)

    recorder.stop_recording()

# Add playback endpoint
@app.get("/recordings/{user_id}")
async def list_recordings(user_id: str):
    """List all recordings for a user."""
    recordings = list(recorder.recordings_dir.glob(f"{user_id}_*.jsonl"))
    return [{"filename": r.name, "size": r.stat().st_size} for r in recordings]
```

**Impact:** Enables session review, quality assurance, and training data collection.

---

**Important Notes:**
- This is a template designed for easy customization
- No code changes needed for basic persona modifications
- Production deployment requires security hardening
- Ideal for rapid prototyping and MVP development

**Additional Resources:**
- ADK Documentation: https://google.github.io/adk-docs/
- Gemini Live API: https://ai.google.dev/gemini-api/docs/live
- Next.js Documentation: https://nextjs.org/docs
- Web Audio API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
