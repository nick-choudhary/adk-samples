# RAG Agent - Technical Documentation Report

## Project Scope

The RAG (Retrieval-Augmented Generation) Agent is a documentation retrieval and question-answering system that leverages Google Vertex AI RAG Engine to provide accurate, citation-backed responses to user queries about uploaded documents. The agent is designed to:

- Answer questions based on a specialized corpus of documents stored in Vertex AI RAG Engine
- Provide accurate citations for all retrieved information, formatted as URLs and document references
- Distinguish between casual conversation and knowledge-seeking queries to optimize tool usage
- Support conversational interactions with context awareness
- Handle document information retrieval with high precision and relevance

**Use Cases:**
- Corporate knowledge base queries (e.g., answering questions about company 10-K reports)
- Technical documentation assistance
- Research paper and academic document retrieval
- Regulatory compliance documentation queries

**Agent Type:** Single Agent, Intermediate Complexity, Conversational Interaction

## Technical Architecture

### Code Flow

The RAG agent follows a straightforward yet effective architecture:

1. **Initialization** (`rag/agent.py:24-54`):
   - Loads environment variables from `.env` file using `python-dotenv`
   - Conditionally builds tools list based on RAG_CORPUS availability
   - Configures VertexAiRagRetrieval tool with:
     - Corpus resource name from environment
     - Similarity top-k: 10 (retrieves top 10 most relevant chunks)
     - Vector distance threshold: 0.6 (filters results by relevance)
   - Instantiates Agent with Gemini 2.5 Flash model

2. **Query Processing Flow**:
   ```
   User Query → Agent (Gemini 2.5 Flash) → Decision Point:
                                              ├─ Casual conversation? → Direct response
                                              └─ Knowledge query? → VertexAiRagRetrieval tool
                                                                   → Retrieve relevant chunks
                                                                   → Synthesize answer
                                                                   → Add citations
                                                                   → Return to user
   ```

3. **Reasoning Logic** (`rag/prompts.py:22-106`):
   - The agent uses sophisticated instruction prompts (v1 currently active)
   - Determines if user query requires retrieval or is casual conversation
   - Asks clarifying questions when uncertain about user intent
   - Only queries the RAG corpus for knowledge-seeking questions
   - Synthesizes information from multiple chunks when needed
   - Formats citations according to strict guidelines (document title, section, URL)

### Key Libraries and Dependencies

**Core Framework:**
- `google-adk>=1.10.0` - Google Agent Development Kit, the primary framework for building the agent
- `google-cloud-aiplatform[adk,agent-engines]>=1.108.0` - Vertex AI integration and deployment

**RAG and Retrieval:**
- `vertexai.preview.rag` - Vertex AI RAG Engine integration for document retrieval
- `google.adk.tools.retrieval.vertex_ai_rag_retrieval.VertexAiRagRetrieval` - Pre-built tool for RAG operations
- `llama-index>=0.12` - Document indexing and retrieval utilities

**Supporting Libraries:**
- `pydantic-settings>=2.8.1` - Configuration management
- `python-dotenv` - Environment variable management
- `google-auth>=2.36.0` - Google Cloud authentication
- `requests>=2.32.3` - HTTP requests for document downloads
- `tabulate>=0.9.0` - Table formatting for outputs

**Development and Testing:**
- `pytest>=8.3.5` - Testing framework
- `pytest-mock>=3.14.0` - Mocking for tests
- `scikit-learn>=1.6.1` - Evaluation metrics
- `agent-starter-pack>=0.14.1` - Production deployment utilities

### Agent Reasoning Mechanism

The agent implements a **conditional tool usage pattern**:

1. **Intent Classification**: Analyzes user input to determine if it's:
   - Casual conversation (no retrieval needed)
   - Knowledge-seeking query (requires RAG retrieval)
   - Ambiguous (asks clarifying questions)

2. **Retrieval Strategy**:
   - Queries Vertex AI RAG Engine with semantic search
   - Uses vector similarity matching with configurable threshold
   - Retrieves top-k most relevant document chunks
   - Filters results based on distance threshold (0.6)

3. **Response Synthesis**:
   - Combines information from multiple retrieved chunks
   - Generates coherent answers using Gemini 2.5 Flash
   - Deduplicates citations from the same source document
   - Formats citations at the end of responses

4. **Error Handling**:
   - Clearly states when information is unavailable
   - Avoids hallucination by only using retrieved content
   - Provides explanations when unable to answer

### Key Files

- `rag/agent.py` - Main agent definition and tool configuration
- `rag/prompts.py` - Instruction prompts and reasoning guidelines
- `rag/shared_libraries/prepare_corpus_and_data.py` - Corpus setup and document upload utilities
- `deployment/deploy.py` - Vertex AI Agent Engine deployment script
- `deployment/run.py` - Remote agent testing script
- `eval/test_eval.py` - Evaluation framework using AgentEvaluator
- `eval/data/conversation.test.json` - Test cases with expected tool usage and responses
- `eval/data/test_config.json` - Evaluation criteria and thresholds

## Build & Run Instructions

### Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Python 3.10, 3.11, or 3.12** (NOT 3.13+)
3. **uv** package manager:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
4. **Git** for repository cloning
5. **Google Cloud SDK** (gcloud CLI) for authentication

### Step 1: Clone Repository and Navigate to Project

```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/RAG
```

### Step 2: Install Dependencies

```bash
uv sync
```

This creates a virtual environment and installs all dependencies from `pyproject.toml`.

### Step 3: Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` file and configure:
```
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1  # or your preferred region
RAG_CORPUS=projects/<project-number>/locations/us-central1/ragCorpora/<corpus-id>
```

### Step 4: Authenticate with Google Cloud

```bash
gcloud auth application-default login
```

### Step 5: Set Up RAG Corpus and Upload Documents

**Option A: Use Default (Alphabet 10-K PDF)**
```bash
uv run python rag/shared_libraries/prepare_corpus_and_data.py
```

This automatically:
- Creates corpus named `Alphabet_10K_2024_corpus`
- Downloads and uploads Alphabet's 2024 10-K PDF
- Updates `.env` with corpus resource name

**Option B: Upload Custom PDF from URL**

Edit `rag/shared_libraries/prepare_corpus_and_data.py`:
```python
CORPUS_DISPLAY_NAME = "My_Custom_Corpus"
CORPUS_DESCRIPTION = "My custom document corpus"
PDF_URL = "https://example.com/document.pdf"
PDF_FILENAME = "my_document.pdf"
```

Then run:
```bash
uv run python rag/shared_libraries/prepare_corpus_and_data.py
```

**Option C: Upload Local PDF**

Modify the `main()` function in `prepare_corpus_and_data.py` and run the script.

### Step 6: Run the Agent

**Option 1: CLI Interface**
```bash
adk run rag
```

**Option 2: Web UI Interface**
```bash
adk web
```
Then select "RAG" from the dropdown menu.

### Example Queries

```
What are the key business segments mentioned in Alphabet's 2024 10-K report?

What was Alphabet's revenue in 2024?

Explain Alphabet's cloud computing strategy.
```

### Step 7: Run Evaluations

```bash
uv sync --dev
uv run pytest eval
```

This runs the evaluation suite that:
- Tests tool trajectory accuracy
- Compares responses against reference answers
- Validates citation quality and correctness

### Step 8: Deploy to Vertex AI Agent Engine (Optional)

```bash
uv run python deployment/deploy.py
```

The script outputs the deployed agent resource name:
```
Deployed agent to Vertex AI Agent Engine successfully, resource name: projects/<PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<AGENT_ENGINE_ID>
```

Grant permissions:
```bash
chmod +x deployment/grant_permissions.sh
./deployment/grant_permissions.sh
```

Test remote deployment:
```bash
uv run python deployment/run.py
```

### Troubleshooting

**Quota Exceeded Errors:**
- New Google Cloud projects have lower default quotas
- Request quota increase at: https://console.cloud.google.com/iam-admin/quotas
- Follow guide: https://cloud.google.com/vertex-ai/docs/quotas#request_a_quota_increase

**Authentication Errors:**
- Ensure `gcloud auth application-default login` was run
- Verify project ID in `.env` matches your active GCP project

**RAG Corpus Not Found:**
- Verify `RAG_CORPUS` in `.env` is correctly formatted
- Check corpus exists: `gcloud ai rag-corpora list --location=us-central1`

## Customization Options

### Add Additional Tools

Edit `rag/agent.py` to include more tools (e.g., Google Search):
```python
from google.adk.tools.search.google_search import GoogleSearch

tools.append(GoogleSearch(...))
```

### Modify System Instructions

Edit `rag/prompts.py` to customize agent behavior, citation format, or reasoning logic.

### Adjust Retrieval Parameters

In `rag/agent.py`, modify:
- `similarity_top_k` - Number of chunks to retrieve (default: 10)
- `vector_distance_threshold` - Relevance threshold (default: 0.6)

### Switch Retrieval Backend

Replace `VertexAiRagRetrieval` with alternative tools:
- Vertex AI Search
- Custom vector database (Pinecone, Weaviate, etc.)
- Traditional search engines

## Performance and Evaluation

The agent includes a comprehensive evaluation framework:

- **Tool Trajectory Score**: Measures correct tool usage
- **Response Match Score**: Compares outputs to reference answers
- Test data in `eval/data/conversation.test.json`
- Configurable thresholds in `eval/data/test_config.json`

## Production Deployment

For production-ready deployment with CI/CD:

```bash
uvx agent-starter-pack create my-rag-agent -a adk@rag
```

This generates:
- Automated deployment scripts
- Infrastructure as code templates
- Monitoring and logging configurations
- Security best practices

---

**Model:** Gemini 2.5 Flash
**Complexity:** Intermediate
**Agent Type:** Single Agent
**Python Version:** 3.10 - 3.12
**License:** Apache 2.0
