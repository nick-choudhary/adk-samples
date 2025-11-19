# Travel Concierge - Technical Documentation Report

## Project Scope

### High-level Summary
The Travel Concierge is an advanced multi-agent system that delivers a comprehensive travel experience from initial inspiration to post-trip feedback collection. It orchestrates six specialized agents working together to provide personalized travel planning, booking, and support services throughout the entire traveler journey.

### Core Capabilities
- **Destination Discovery**: AI-powered recommendations based on user preferences
- **Intelligent Trip Planning**: Automated flight, hotel, and activity planning with seat/room selection
- **Mock Booking System**: Complete booking flow simulation including payment processing
- **Pre-Trip Services**: Visa requirements, medical advisories, weather alerts, and packing suggestions
- **In-Trip Support**: Real-time booking changes, day-of navigation assistance, and informative guides
- **Post-Trip Analysis**: Feedback collection and preference extraction for future trips
- **Memory Management**: Session-based state management for itinerary and user preferences
- **Multi-Modal Integration**: Google Places API, Search Grounding, and MCP support

### Primary Use Cases
- End-to-end vacation planning from ideation to finalized bookings
- Real-time travel assistance during trips
- Automated travel advisory and preparation guidance
- Personalized destination and activity recommendations
- Seamless booking coordination across flights, hotels, and experiences

### Target Users
- Travel agencies building conversational booking platforms
- Enterprise travel management systems
- Consumer travel applications
- Travel concierge services seeking automation
- Developers learning multi-agent orchestration patterns

### Key Innovations/Differentiators
- **Phase-Based Agent Routing**: Intelligent delegation based on trip timeline (pre-booking, pre-trip, in-trip, post-trip)
- **Structured JSON Outputs**: Pydantic schemas enable rich GUI rendering of agent responses
- **Nested Agent Hierarchy**: Root agent coordinates 6 sub-agents, each with specialized tool agents
- **MCP Integration**: Demonstrates Airbnb MCP server integration for accommodation search
- **Dynamic Instructions**: Day-of agent adapts based on current location and time
- **Session State Memory**: All agents share state for seamless information handoff

## Technical Architecture

### Multi-Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                        ROOT AGENT                                │
│              (Travel Concierge Orchestrator)                     │
│                   Model: gemini-2.5-flash                        │
│              File: travel_concierge/agent.py:31-45               │
└──────────────────┬──────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┬───────────┬────────────┬──────────┬─────────┐
        │                     │           │            │          │         │
        ▼                     ▼           ▼            ▼          ▼         ▼
┌───────────────┐    ┌──────────────┐  ┌───────────┐ ┌──────────────┐  ┌──────────┐
│ INSPIRATION   │    │  PLANNING    │  │  BOOKING  │ │  PRE-TRIP    │  │ IN-TRIP  │
│    AGENT      │    │    AGENT     │  │   AGENT   │ │    AGENT     │  │  AGENT   │
│ (Discovery)   │    │ (Itinerary)  │  │ (Payment) │ │  (Prep)      │  │ (Support)│
└───┬───────────┘    └──┬───────────┘  └───────────┘ └──────────────┘  └─┬────────┘
    │                   │                                                  │
    ├─ place_agent      ├─ flight_search_agent                            ├─ day_of_agent
    ├─ poi_agent        ├─ flight_seat_selection_agent                    │
    └─ map_tool         ├─ hotel_search_agent                             │
                        ├─ hotel_room_selection_agent                     │
                        ├─ itinerary_agent                                │
                        └─ memorize tool                                  │
                                                                           │
┌──────────────┐                                                          │
│  POST-TRIP   │◄─────────────────────────────────────────────────────────┘
│    AGENT     │
│ (Feedback)   │
└──────────────┘
```

### Code Flow Explanation

**1. Initialization & State Loading** (`travel_concierge/__init__.py:15-25`)
```python
# Set default environment variables
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
```

**2. Root Agent Setup** (`travel_concierge/agent.py:31-45`)
```python
root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    instruction=prompt.ROOT_AGENT_INSTR,  # Line 19
    sub_agents=[...],  # All 6 specialized agents
    before_agent_callback=_load_precreated_itinerary,  # Line 44
)
```

**3. Pre-Agent Callback** (`travel_concierge/tools/memory.py:112-127`)
- Loads initial user profile and itinerary from JSON file (configurable via `TRAVEL_CONCIERGE_SCENARIO` env var)
- Sets system time and initializes session state at lines 98-109
- Default scenario: `travel_concierge/profiles/itinerary_empty_default.json`

**4. Agent Routing Logic** (`travel_concierge/prompt.py:17-49`)
The root agent uses dynamic instructions with state interpolation:
```python
ROOT_AGENT_INSTR = """
Current user: {user_profile}
Current time: {_time}
Trip phases: {itinerary_start_date}, {itinerary_end_date}
"""
```

**5. Sub-Agent Execution Example** (`travel_concierge/sub_agents/inspiration/agent.py:24-54`)
```python
# Nested agent structure
place_agent = Agent(
    output_schema=DestinationIdeas,  # Line 31 - Pydantic schema
    output_key="place",
    generate_content_config=json_response_config,  # Controlled JSON generation
)

inspiration_agent = Agent(
    tools=[
        AgentTool(agent=place_agent),  # Nested agent as tool
        AgentTool(agent=poi_agent),
        map_tool  # Function tool
    ]
)
```

**6. Planning Agent Tool Chain** (`travel_concierge/sub_agents/planning/agent.py:88-104`)
The planning agent orchestrates 5 nested agents:
- `flight_search_agent` → `flight_seat_selection_agent` (lines 75-85)
- `hotel_search_agent` → `hotel_room_selection_agent` (lines 38-60)
- `itinerary_agent` → final JSON itinerary (lines 25-35)

**7. Memory Tool** (`travel_concierge/tools/memory.py:53-67`)
```python
def memorize(key: str, value: str, tool_context: ToolContext):
    mem_dict = tool_context.state  # Access shared session state
    mem_dict[key] = value
    return {"status": f'Stored "{key}": "{value}"'}
```

### Agent Definitions with Roles

| Agent Name | Role | Model | Key Features | File Location |
|------------|------|-------|--------------|---------------|
| **root_agent** | Orchestrator | gemini-2.5-flash | Phase-based routing, state interpolation | `agent.py:31-45` |
| **inspiration_agent** | Discovery | gemini-2.5-flash | Destination ideas, POI recommendations | `sub_agents/inspiration/agent.py:48-54` |
| **planning_agent** | Itinerary Builder | gemini-2.5-flash | Flight/hotel search, seat/room selection | `sub_agents/planning/agent.py:88-104` |
| **booking_agent** | Payment Processor | gemini-2.5-flash | Mock payment processing, reservation confirmation | `sub_agents/booking/` |
| **pre_trip_agent** | Pre-Trip Prep | gemini-2.5-flash | Visa, medical, weather, packing suggestions | `sub_agents/pre_trip/` |
| **in_trip_agent** | Travel Assistant | gemini-2.5-flash | Booking changes, day-of navigation | `sub_agents/in_trip/` |
| **post_trip_agent** | Feedback Collector | gemini-2.5-flash | Experience extraction, preference learning | `sub_agents/post_trip/` |

**Nested Tool Agents** (all use gemini-2.5-flash):
- `place_agent` - Destination recommendations with images/ratings (output: DestinationIdeas)
- `poi_agent` - Activity suggestions (output: POISuggestions)
- `itinerary_agent` - Structured itinerary JSON (output: Itinerary schema)
- `day_of_agent` - Dynamic transit directions
- Flight/hotel selection agents - Mock booking data with JSON schemas

### Key Libraries and Dependencies

From `pyproject.toml:14-20`:
```toml
dependencies = [
    "google-cloud-aiplatform[adk,agent-engines]>=1.93.0",  # Vertex AI deployment
    "pydantic>=2.10.6",                                     # Schema validation
    "python-dotenv>=1.0.1",                                 # Environment management
    "google-genai>=1.16.1",                                 # Gemini API
    "google-adk>=1.0.0",                                    # Agent Development Kit
]
```

**Development Dependencies** (`pyproject.toml:24-30`):
- `pytest>=8.3.5` - Testing framework
- `google-adk[eval]>=1.16.0` - Agent evaluation tools
- `pytest-asyncio>=0.26.0` - Async test support

### Tools and Integrations

**1. Google Places API** (`tools/places.py`)
```python
map_tool = FunctionTool(func=get_lat_long)
# Geocoding via Google Maps Platform
# Requires: GOOGLE_PLACES_API_KEY environment variable
```

**2. Google Search Grounding** (used in pre_trip_agent)
- Visa requirements lookup
- Medical advisories
- Travel alerts
- Weather/storm status

**3. MCP Integration** (`tests/mcp_abnb.py`)
Airbnb MCP server integration example:
- Node.js/npx required
- Attaches to planning_agent dynamically
- Provides search and listing tools

**4. Memory Tools** (`tools/memory.py:33-86`)
- `memorize(key, value)` - Store key-value pairs in session state
- `memorize_list(key, value)` - Append to list in state
- `forget(key, value)` - Remove from state

### Reasoning Mechanisms

**1. Phase-Based Routing** (`prompt.py:36-48`)
```python
"""
Trip phases:
- if {itinerary_datetime} is before {itinerary_start_date} → pre_trip phase
- if between start and end dates → in_trip phase
- if after {itinerary_end_date} → post_trip phase
"""
```

**2. JSON Schema Enforcement**
- All booking-related agents use `output_schema` with Pydantic models
- `json_response_config` ensures structured outputs
- Example: `DestinationIdeas`, `FlightsSelection`, `Itinerary` (in `shared_libraries/types.py`)

**3. Controlled Generation**
Planning agent uses low temperature (0.1) and top_p (0.5) for consistent booking selections (`sub_agents/planning/agent.py:101-103`)

**4. Agent Handoff Pattern**
Root agent instructions explicitly define handoff criteria:
- "general knowledge/inspiration" → `inspiration_agent`
- "flight deals/seat selection/lodging" → `planning_agent`
- "ready to book/payments" → `booking_agent`

## Build & Run Instructions

### Prerequisites

**Required:**
- Python 3.10+ (but < 3.13) - specified in `pyproject.toml:22`
- Google Cloud Project with Vertex AI API enabled
- Google Maps Platform API key - [Get API Key](https://developers.google.com/maps/documentation/places/web-service/get-api-key)
- Google Agent Development Kit 1.0+
- uv package manager - [Install uv](https://docs.astral.sh/uv/)

**Optional (for MCP demo):**
- Node.js and npx for Airbnb MCP server

### Step-by-Step Installation

**1. Clone the Repository**
```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/travel-concierge
```

**2. Install uv Package Manager**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**3. Install Dependencies**
```bash
uv sync
```

For development dependencies (testing/evaluation):
```bash
uv sync --dev
```

**4. Authenticate with Google Cloud**
```bash
gcloud auth application-default login
```

### Configuration (Environment Variables)

**1. Create Environment File**
```bash
cp .env.example .env
```

**2. Configure `.env` File** (see `.env.example:1-22`)

```bash
# Model Backend Selection
GOOGLE_GENAI_USE_VERTEXAI=1  # 1 for Vertex AI, 0 for ML Dev

# Vertex AI Configuration (if GOOGLE_GENAI_USE_VERTEXAI=1)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# ML Dev Configuration (if GOOGLE_GENAI_USE_VERTEXAI=0)
# GOOGLE_API_KEY=your-api-key

# Google Places API
GOOGLE_PLACES_API_KEY=your-places-api-key

# Agent Engine Deployment (optional)
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name

# Scenario Configuration (optional)
# TRAVEL_CONCIERGE_SCENARIO=travel_concierge/profiles/itinerary_seattle_example.json
TRAVEL_CONCIERGE_SCENARIO=travel_concierge/profiles/itinerary_empty_default.json
```

**Environment Variable Reference:**
- `GOOGLE_GENAI_USE_VERTEXAI`: Backend selection (1=Vertex, 0=ML Dev API)
- `GOOGLE_CLOUD_PROJECT`: GCP project ID for Vertex AI
- `GOOGLE_CLOUD_LOCATION`: Region for Gemini models (us-central1 recommended)
- `GOOGLE_PLACES_API_KEY`: API key from Google Maps Platform
- `TRAVEL_CONCIERGE_SCENARIO`: Path to initial state JSON file

### Running the Agent

**Method 1: CLI Interface**
```bash
# From travel-concierge directory
adk run travel_concierge
```

**Method 2: Web UI** (recommended for rich interaction)
```bash
adk web
```
- Open the URL shown in terminal (typically http://localhost:8000)
- Select "travel_concierge" from the dropdown menu
- Start chatting in the interface

**Method 3: API Server**
```bash
# Start FastAPI server
adk api_server travel_concierge
```
- API documentation available at: http://127.0.0.1:8000/docs
- See programmatic example at `tests/programmatic_example.py`

### Example Interactions

**Scenario 1: Inspiration to Booking**
```
User: "Need some destination ideas for the Americas"
Agent: [transfers to inspiration_agent]
      [calls place_agent → returns DestinationIdeas JSON]
      "Here are some amazing destinations..."

User: "Tell me about activities in Peru"
Agent: [calls poi_agent → returns POISuggestions]
      "In Peru you can visit Machu Picchu..."

User: "Go ahead to planning"
Agent: [transfers to planning_agent]
      "Great! I'll help you plan your Peru trip. When would you like to travel?"

User: "Find flights to Lima from JFK on April 20th for 4 days"
Agent: [calls flight_search_agent → FlightsSelection JSON]
      [calls flight_seat_selection_agent]
      [calls hotel_search_agent]
      [calls itinerary_agent → Itinerary JSON]
```

**Scenario 2: Autonomous Planning**
```
User: "Find flights to London from JFK on April 20th for 4 days. Pick any flights
      and seats; also any hotels and room type. Act on my behalf without my input,
      until you have selected everything, confirm with me before generating an itinerary."

Agent: [Executes full planning workflow autonomously]
      [Provides final selections for confirmation]
```

**Scenario 3: In-Trip Support** (requires Seattle itinerary loaded)
```
# Set TRAVEL_CONCIERGE_SCENARIO=travel_concierge/profiles/itinerary_seattle_example.json

User: "What's the status of my trip?"
Agent: [transfers to in_trip_agent based on current date]
      "You're currently in Seattle. Your hotel reservation is confirmed..."

User: "How do I get from my hotel to Pike Place Market?"
Agent: [calls day_of_agent with dynamic instructions]
      "Here are the transit options..."
```

### Testing and Evaluation

**Run All Tests**
```bash
uv sync --dev
uv run pytest
```

**Run Specific Test Suites**
```bash
# Unit tests only (check agents respond)
uv run pytest tests

# Agent trajectory evaluation tests
uv run pytest eval
```

**Test Files:**
- `tests/unit/` - Basic agent response tests
- `tests/pre_booking_sample.md` - Full pre-booking flow example
- `tests/post_booking_sample.md` - In-trip experience simulation
- `tests/programmatic_example.py` - API client example (lines 1-210)
- `tests/mcp_abnb.py` - MCP integration demo

**MCP Integration Test**
```bash
# Requires Node.js/npx installed
python -m tests.mcp_abnb
```

### Deployment (Optional)

**Deploy to Vertex AI Agent Engine**
```bash
# Install deployment dependencies
uv sync --group deployment

# Create agent
uv run python deployment/deploy.py --create
# Output: projects/*/locations/us-central1/reasoningEngines/[ID]

# Quick test deployed agent
uv run python deployment/deploy.py --quicktest --resource_id=<RESOURCE_ID>

# Delete deployed agent
uv run python deployment/deploy.py --delete --resource_id=<RESOURCE_ID>
```

**Alternative: Agent Starter Pack**
```bash
# Install and create production-ready project
uvx agent-starter-pack create my-travel-concierge -a adk@travel-concierge
```
Provides CI/CD scripts, production configurations, and deployment automation.

### Troubleshooting

**Common Issues:**

1. **Malformed Function Calls / Pydantic Errors**
   - Solution: Tell the agent to "try again"
   - Root cause: JSON generation variations
   - Prevention: Use lower temperature settings (already set for planning_agent)

2. **Wrong Tool Called**
   - Solution: "That's the wrong tool, try again"
   - Agents typically self-correct

3. **Agent Stopped Mid-Execution**
   - Solution: Ask "what's next?" to nudge forward
   - Can implement retry logic in production applications

4. **Import Errors**
   - Ensure you're in the virtual environment:
     ```bash
     eval $(poetry env activate)
     ```

5. **API Key Issues**
   - Verify `.env` file exists and contains correct keys
   - Check `GOOGLE_PLACES_API_KEY` is valid
   - Ensure GCP authentication: `gcloud auth application-default login`

6. **Vertex AI Access Denied**
   - Enable Vertex AI API: `gcloud services enable aiplatform.googleapis.com`
   - Verify project ID in `.env` matches your GCP project

## Customization Options

### 1. Load Custom Itinerary for In-Trip Demo

**Use Case:** Demo the in-trip agent with a pre-populated itinerary without going through the booking flow.

**Implementation:**
1. Create a custom itinerary JSON following the schema in `shared_libraries/types.py`
2. Use `travel_concierge/profiles/itinerary_seattle_example.json` as a template
3. Set environment variable:
   ```bash
   TRAVEL_CONCIERGE_SCENARIO=travel_concierge/profiles/my_custom_itinerary.json
   ```
4. Restart `adk web` or `adk run`

**Code Reference:** `tools/memory.py:112-127`
```python
def _load_precreated_itinerary(callback_context: CallbackContext):
    data = {}
    with open(SAMPLE_SCENARIO_PATH, "r") as file:  # Line 122
        data = json.load(file)
    _set_initial_states(data["state"], callback_context.state)
```

**Required Fields in JSON:**
```json
{
  "state": {
    "user_profile": {
      "passport_nationality": "US",
      "home": {
        "address": "123 Main St, City, State",
        "local_prefer_mode": "driving"
      }
    },
    "itinerary": {
      "start_date": "2025-04-20",
      "end_date": "2025-04-24",
      "destination": "Seattle",
      "flights": [...],
      "hotel": {...},
      "activities": [...]
    }
  }
}
```

### 2. Replace Mock Booking APIs with Real Services

**Use Case:** Connect to actual flight and hotel booking systems.

**Implementation:**

**A. Replace Flight Search** (`sub_agents/planning/agent.py:75-85`)
```python
# Current: flight_search_agent with mock instruction
# Replace with:
from your_flight_api import search_flights

real_flight_search = FunctionTool(
    func=search_flights,
    name="search_flights",
    description="Search real-time flight inventory"
)

planning_agent = Agent(
    tools=[real_flight_search, ...]  # Replace flight_search_agent
)
```

**B. Connect to Hotel APIs**
Modify `sub_agents/planning/prompt.py` and replace `hotel_search_agent` with actual API:
```python
from your_hotel_api import search_hotels

real_hotel_search = FunctionTool(func=search_hotels)
```

**C. Payment Processing**
Replace mock payment agent in `sub_agents/booking/` with Stripe/Square integration:
```python
from stripe import PaymentIntent

def process_payment(amount: float, currency: str, tool_context: ToolContext):
    payment = PaymentIntent.create(amount=amount, currency=currency)
    tool_context.state["payment_id"] = payment.id
    return {"status": "success", "payment_id": payment.id}
```

### 3. Integrate Google Maps Directions API

**Use Case:** Provide actual turn-by-turn directions in the day_of_agent instead of generic transit advice.

**Implementation:**

**File:** Create `tools/directions.py`
```python
from google.adk.tools import FunctionTool
from googlemaps import Client as GoogleMapsClient
import os

def get_directions(origin: str, destination: str, mode: str = "transit"):
    """Get real-time directions using Google Maps Directions API."""
    gmaps = GoogleMapsClient(key=os.getenv("GOOGLE_MAPS_API_KEY"))

    directions_result = gmaps.directions(
        origin=origin,
        destination=destination,
        mode=mode,  # driving, walking, transit, bicycling
        departure_time="now"
    )

    # Extract steps from first route
    if directions_result:
        route = directions_result[0]
        steps = []
        for leg in route["legs"]:
            for step in leg["steps"]:
                steps.append({
                    "instruction": step["html_instructions"],
                    "distance": step["distance"]["text"],
                    "duration": step["duration"]["text"]
                })
        return {"steps": steps, "total_duration": route["legs"][0]["duration"]["text"]}
    return {"error": "No route found"}

directions_tool = FunctionTool(func=get_directions)
```

**Modify:** `sub_agents/in_trip/agent.py`
```python
from travel_concierge.tools.directions import directions_tool

day_of_agent = Agent(
    tools=[directions_tool],  # Add to existing tools
    ...
)
```

**Environment:** Add to `.env`
```bash
GOOGLE_MAPS_API_KEY=your-directions-api-key
```

### 4. Add External Database for User Profiles

**Use Case:** Load user preferences from PostgreSQL/Firestore instead of JSON files.

**Implementation:**

**File:** Create `tools/database.py`
```python
from google.cloud import firestore
from google.adk.agents.callback_context import CallbackContext

db = firestore.Client()

def load_user_profile_from_firestore(callback_context: CallbackContext):
    """Load user profile from Firestore instead of JSON file."""
    # Extract user ID from context or initial request
    user_id = callback_context.state.get("user_id", "default_user")

    # Query Firestore
    user_ref = db.collection("users").document(user_id)
    user_data = user_ref.get()

    if user_data.exists:
        profile = user_data.to_dict()
        callback_context.state["user_profile"] = profile

        # Load itinerary if exists
        itinerary_ref = db.collection("itineraries").where("user_id", "==", user_id)
        itineraries = list(itinerary_ref.stream())
        if itineraries:
            callback_context.state["itinerary"] = itineraries[0].to_dict()
```

**Modify:** `agent.py:31-45`
```python
from travel_concierge.tools.database import load_user_profile_from_firestore

root_agent = Agent(
    before_agent_callback=load_user_profile_from_firestore,  # Replace file loader
    ...
)
```

**Write-Through Caching:**
Modify `tools/memory.py:53-67` to persist to database:
```python
def memorize(key: str, value: str, tool_context: ToolContext):
    mem_dict = tool_context.state
    mem_dict[key] = value

    # Write-through to Firestore
    user_id = mem_dict.get("user_id", "default_user")
    db.collection("users").document(user_id).set({key: value}, merge=True)

    return {"status": f'Stored "{key}": "{value}"'}
```

### 5. Customize Agent Prompts and Behavior

**Use Case:** Adjust agent personality, verbosity, or domain focus.

**Implementation:**

**A. Modify Root Agent Behavior** (`prompt.py:17-49`)
```python
ROOT_AGENT_INSTR = """
- You are an exclusive luxury travel concierge  # Change personality
- Focus on high-end destinations and 5-star accommodations  # Add constraints
- Always provide 3 options for each recommendation  # Set expectations
- Keep responses to 2 sentences maximum  # Control verbosity
...
"""
```

**B. Adjust Planning Agent Temperature** (`sub_agents/planning/agent.py:101-103`)
```python
# Current: Low temperature for consistency
generate_content_config=GenerateContentConfig(temperature=0.1, top_p=0.5)

# Alternative: Higher creativity for varied suggestions
generate_content_config=GenerateContentConfig(temperature=0.8, top_p=0.95)
```

**C. Add Custom Tool to Inspiration Agent** (`sub_agents/inspiration/agent.py:48-54`)
```python
from your_tools import weather_forecast_tool

inspiration_agent = Agent(
    tools=[
        AgentTool(agent=place_agent),
        AgentTool(agent=poi_agent),
        map_tool,
        weather_forecast_tool,  # Add custom tool
    ]
)
```

### 6. Implement Multi-Language Support

**Use Case:** Support travelers in their native language.

**Implementation:**

**File:** Create `tools/translation.py`
```python
from google.cloud import translate_v2 as translate

translate_client = translate.Client()

def detect_and_set_language(callback_context: CallbackContext):
    """Detect user language from first message."""
    first_message = callback_context.state.get("first_message", "")
    detection = translate_client.detect_language(first_message)
    language = detection["language"]
    callback_context.state["user_language"] = language
```

**Modify Agent Prompts:**
```python
ROOT_AGENT_INSTR = """
User's preferred language: {user_language}
Always respond in the user's language.
...
"""
```

**Add to Root Agent:**
```python
root_agent = Agent(
    before_agent_callback=detect_and_set_language,
    ...
)
```

### 7. Add Event Streaming for GUI Rendering

**Use Case:** Build a rich UI that renders flight selections as cards, seat maps, etc.

**Reference:** See `tests/programmatic_example.py:1-210` for event handling patterns.

**Implementation:**
```python
from google.adk.sessions import Session

session = Session(agent=root_agent)
runner = session.create_runner()

async for event in runner.run_async("Find flights to NYC"):
    if event.type == "function_call":
        # Detect which agent/tool called
        if event.name == "flight_search_agent":
            # Parse JSON response when available
            pass
    elif event.type == "function_response":
        if event.name == "flight_search_agent":
            flights_data = event.response
            # Send to GUI: render_flight_cards(flights_data)
```

**Schema Detection:**
All booking agents use Pydantic schemas (`shared_libraries/types.py`):
- `FlightsSelection` - Flight options with prices
- `SeatsSelection` - Seat map data
- `HotelsSelection` - Hotel listings
- `Itinerary` - Complete trip JSON

Parse these in your frontend to render rich components.

---

**File References:**
- Main agent: `/home/user/adk-samples/python/agents/travel-concierge/travel_concierge/agent.py`
- Prompts: `/home/user/adk-samples/python/agents/travel-concierge/travel_concierge/prompt.py`
- Sub-agents: `/home/user/adk-samples/python/agents/travel-concierge/travel_concierge/sub_agents/`
- Tools: `/home/user/adk-samples/python/agents/travel-concierge/travel_concierge/tools/`
- Types: `/home/user/adk-samples/python/agents/travel-concierge/travel_concierge/shared_libraries/types.py`
- Tests: `/home/user/adk-samples/python/agents/travel-concierge/tests/`
- Configuration: `/home/user/adk-samples/python/agents/travel-concierge/pyproject.toml`
