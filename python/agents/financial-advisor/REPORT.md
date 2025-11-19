# Financial Advisor Agent - Technical Documentation Report

## Project Scope

The Financial Advisor is a multi-agent system designed to assist human financial advisors and investors by providing structured financial analysis and strategy development. It orchestrates four specialized AI agents that work together to analyze market data, develop trading strategies, create execution plans, and evaluate risks - all tailored to user-specific risk tolerance and investment goals.

**IMPORTANT LEGAL DISCLAIMER**: This agent is for educational and informational purposes ONLY. It does NOT provide financial advice, investment recommendations, or offers to buy/sell securities. Always consult with a qualified independent financial advisor before making investment decisions.

**Core Capabilities:**
- **Market Data Analysis**: Comprehensive analysis of stock tickers using Google Search for SEC filings and market intelligence
- **Trading Strategy Development**: Creates 5+ customized trading strategies aligned with user risk profile and investment horizon
- **Execution Planning**: Develops detailed plans for implementing strategies (order types, timing, position sizing)
- **Risk Assessment**: Provides comprehensive risk analysis with mitigation strategies
- **Structured Workflow**: Guided 4-step process from analysis to risk evaluation
- **Conversational Interface**: Natural language interaction with context preservation across steps

**Use Cases:**
- Financial advisors seeking AI-assisted market analysis
- Investors researching trading strategies for specific stocks
- Educational purposes for learning about investment strategy development
- Risk assessment for proposed investment plans
- Understanding execution considerations for different trading approaches

**Target Users:**
- Financial advisors and investment professionals
- Individual investors with moderate to advanced knowledge
- Financial educators and students
- Risk analysts evaluating investment portfolios

**Agent Type:** Multi-Agent, Medium Complexity, Structured Conversational Workflow

## Technical Architecture

### Multi-Agent Hierarchy

```
Financial Coordinator Agent (Root Orchestrator)
    ├─→ Data Analyst Agent (Market research and analysis)
    ├─→ Trading Analyst Agent (Strategy development)
    ├─→ Execution Analyst Agent (Implementation planning)
    └─→ Risk Analyst Agent (Risk assessment and mitigation)
```

### Code Flow

The Financial Advisor implements a **sequential workflow pattern** where each agent builds upon the previous agent's output:

1. **Initialization** (`financial_advisor/agent.py:30-49`):
   - Creates root `financial_coordinator` agent with Gemini 2.5 Pro
   - Registers 4 sub-agents as AgentTools
   - Defines output key for state management
   - Sets up structured prompt guiding the 4-step process

2. **Step 1: Market Analysis**:
   ```
   User: "Analyze AAPL"

   Financial Coordinator → Validates ticker symbol
                         → Calls: data_analyst_agent

   Data Analyst Agent → Searches: Recent SEC filings (10-K, 10-Q, 8-K)
                      → Searches: Financial news and market sentiment
                      → Searches: Analyst opinions and ratings
                      → Searches: Stock performance data
                      → Compiles: Comprehensive market analysis report
                      → Stores: market_data_analysis_output in state

   Financial Coordinator → Presents analysis summary to user
                         → Prompts for: Risk attitude and investment period
   ```

3. **Step 2: Strategy Development**:
   ```
   User: "Moderate risk, long-term investment"

   Financial Coordinator → Calls: trading_analyst_agent
                         → Passes: market_data_analysis_output + user profile

   Trading Analyst Agent → Reviews: Market analysis
                         → Develops: 5+ trading strategies
                           - Strategy 1: Core Buy & Hold with Compounding
                           - Strategy 2: Dividend Growth Focus (DRIP)
                           - Strategy 3: Value Averaging on Dips
                           - Strategy 4: Covered Call Writing (Income)
                           - Strategy 5: GARP Accumulation
                         → Each strategy includes:
                           - Description and rationale
                           - Alignment with user profile
                           - Key indicators to watch
                           - Entry/exit conditions
                           - Specific risks
                         → Stores: proposed_trading_strategies_output

   Financial Coordinator → Presents strategies to user
                         → Asks: Execution preferences
   ```

4. **Step 3: Execution Planning**:
   ```
   User: "No specific preferences"

   Financial Coordinator → Calls: execution_analyst_agent
                         → Passes: All previous outputs + user profile

   Execution Analyst Agent → For each strategy, defines:
                            - Optimal entry conditions and timing
                            - Recommended order types (Limit vs Market)
                            - Position sizing methodology
                            - Stop-loss strategies
                            - In-trade management approach
                            - Accumulation/scaling-in tactics
                            - Partial exit triggers
                            - Full exit conditions
                            - Slippage considerations
                           → Stores: execution_plan_output

   Financial Coordinator → Presents detailed execution plan
                         → Proceeds to final risk evaluation
   ```

5. **Step 4: Risk Assessment**:
   ```
   Financial Coordinator → Calls: risk_analyst_agent
                         → Passes: All previous outputs

   Risk Analyst Agent → Evaluates:
                       - Market risks (concentration, sector, volatility)
                       - Liquidity risks
                       - Counterparty and platform risks
                       - Operational and technological risks
                       - Strategy-specific risks
                       - Psychological risks
                      → Assesses alignment with user profile
                      → Identifies potential misalignments
                      → Provides mitigation strategies
                      → Stores: final_risk_assessment_output

   Financial Coordinator → Presents comprehensive risk report
                         → Workflow complete
   ```

### Agent Details

**1. Financial Coordinator (Root Agent)** (`financial_advisor/agent.py:30-49`):
- **Model**: Gemini 2.5 Pro
- **Role**: Orchestrates the 4-step workflow, maintains conversation state
- **Tools**: 4 AgentTools (sub-agents)
- **State Management**: Uses `output_key` to store results at each step
- **Workflow Logic**:
  1. Prompts user for ticker symbol
  2. Validates input and calls data_analyst
  3. Collects user risk profile
  4. Sequentially calls trading_analyst → execution_analyst → risk_analyst
  5. Ensures each step completes before proceeding

**2. Data Analyst Agent** (`financial_advisor/sub_agents/data_analyst/agent.py`):
- **Model**: Gemini 2.5 Pro (configurable)
- **Purpose**: Gather comprehensive market data and analysis
- **Tools**: Google Search (built-in ADK tool)
- **Research Areas**:
  - SEC filings (10-K, 10-Q, 8-K)
  - Recent financial news (last 7 days)
  - Stock performance metrics
  - Market sentiment analysis
  - Analyst ratings and opinions
  - Key risks and opportunities
- **Output**: Structured market analysis report stored in state

**3. Trading Analyst Agent** (`financial_advisor/sub_agents/trading_analyst/agent.py`):
- **Model**: Gemini 2.5 Pro (configurable)
- **Purpose**: Develop 5+ trading strategies tailored to user profile
- **Inputs**: Market analysis + risk attitude + investment period
- **Strategy Types**:
  - Buy and Hold strategies
  - Dividend-focused strategies
  - Value-based approaches (GARP, dip buying)
  - Income generation (covered calls)
  - Momentum and technical strategies
- **Output**: Detailed strategy outlines with rationale, indicators, and risks

**4. Execution Analyst Agent** (`financial_advisor/sub_agents/execution_analyst/agent.py`):
- **Model**: Gemini 2.5 Pro (configurable)
- **Purpose**: Create actionable execution plans for strategies
- **Considerations**:
  - Order types (Limit, Market, Stop-Loss)
  - Timing and entry conditions
  - Position sizing calculations
  - Risk management (stop-loss placement)
  - Scaling in/out methodologies
  - Cost optimization (slippage, commissions)
- **Output**: Comprehensive execution plan for each strategy

**5. Risk Analyst Agent** (`financial_advisor/sub_agents/risk_analyst/agent.py`):
- **Model**: Gemini 2.5 Pro (configurable)
- **Purpose**: Comprehensive risk evaluation and mitigation recommendations
- **Risk Categories Analyzed**:
  - Market risks (concentration, volatility, sector)
  - Liquidity risks
  - Counterparty risks (broker, platform)
  - Operational risks (human error, technology)
  - Strategy-specific risks
  - Psychological risks (fear, impatience, bias)
- **Output**: Detailed risk assessment with alignment analysis and mitigation strategies

### Key Libraries and Dependencies

**Core Framework:**
- `google-adk>=1.0.0` - Google Agent Development Kit
- `google-cloud-aiplatform[adk,agent-engines]>=1.93.0` - Vertex AI integration
- `google-genai>=1.9.0` - Gemini model access

**Configuration:**
- `pydantic>=2.10.6` - Data validation and settings management
- `python-dotenv>=1.0.1` - Environment variable management

**Development and Testing:**
- `pytest>=8.3.2` - Testing framework
- `pytest-asyncio>=0.23.7` - Async testing support
- `google-adk[eval]>=1.0.0` - Evaluation framework
- `nest-asyncio>=1.6.0` - Nested event loop support

**Deployment:**
- `absl-py>=2.2.1` - Command-line flags and application framework
- `agent-starter-pack>=0.14.1` - Production deployment utilities

### Project Structure

```
financial_advisor/
├── agent.py                           # Root coordinator agent
├── prompt.py                          # Coordinator instructions
├── sub_agents/
│   ├── data_analyst/
│   │   ├── agent.py                   # Market research agent
│   │   └── prompt.py                  # Data analyst instructions
│   ├── trading_analyst/
│   │   ├── agent.py                   # Strategy development agent
│   │   └── prompt.py                  # Trading analyst instructions
│   ├── execution_analyst/
│   │   ├── agent.py                   # Execution planning agent
│   │   └── prompt.py                  # Execution analyst instructions
│   └── risk_analyst/
│       ├── agent.py                   # Risk assessment agent
│       └── prompt.py                  # Risk analyst instructions

tests/
└── test_financial_advisor.py         # Integration tests

eval/
└── test_eval.py                       # Evaluation framework

deployment/
├── deploy.py                          # Vertex AI deployment
└── test_deployment.py                 # Remote agent testing
```

### Reasoning Mechanism

**Sequential Workflow Pattern**:
1. Each agent completes its task before the next agent is invoked
2. Agent outputs stored in shared state for downstream agents
3. User confirmation required between major workflow steps
4. Conversational context maintained throughout entire process

**State Management**:
- `market_data_analysis_output` - Data analyst results
- `proposed_trading_strategies_output` - Trading analyst results
- `execution_plan_output` - Execution analyst results
- `final_risk_assessment_output` - Risk analyst results

**Error Handling**:
- Ticker symbol validation before analysis
- Clarifying questions for ambiguous user inputs
- Graceful handling of incomplete user profiles

## Build & Run Instructions

### Prerequisites

1. **Python 3.10, 3.11, or 3.12** (NOT 3.13+)
2. **uv** package manager:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Google Cloud Account** with billing enabled
4. **Google Cloud SDK**:
   ```bash
   curl https://sdk.cloud.google.com | bash
   ```

### Step 1: Clone Repository and Navigate to Project

```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/financial-advisor
```

### Step 2: Install Dependencies

```bash
uv sync
```

### Step 3: Set Up Environment Variables

**Option A: Using .env file**
```bash
cp .env.example .env
```

Edit `.env`:
```bash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name  # Only for deployment
```

**Option B: Export in shell**
```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
```

### Step 4: Authenticate with Google Cloud

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT
```

### Step 5: Run the Agent

**Option 1: Web UI (Recommended)**
```bash
adk web
```

- Opens web interface in browser
- Select "financial_advisor" from dropdown
- Start conversation with "Who are you?" or "Analyze AAPL"

**Option 2: CLI Interface**
```bash
adk run financial_advisor
```

### Example Interaction

```
User: who are you

Agent: I am the financial coordinator agent. My role is to guide you through a
structured process to receive financial advice. I work with specialized subagents
to help you:

1. Analyze a market ticker
2. Develop trading strategies based on your risk profile and investment goals
3. Define an optimal plan for executing those strategies
4. Evaluate the overall risk of the proposed plan

How can I help you start this process today? For example, we could begin by
analyzing a market ticker.

User: AAPL

Agent: It looks like there might be a typo in the ticker symbol. Did you mean
"AAPL" for Apple Inc.?

User: correct

Agent: Okay, great. I will now call the data_analyst subagent to gather
comprehensive market data analysis for AAPL (Apple Inc.). This analysis will
include historical performance, key financial ratios, and relevant news sentiment.

[Calls data_analyst_agent with Google Search for AAPL information]

[Data analyst completes research...]

Agent: The data_analyst has completed the market analysis for AAPL covering:
- Recent SEC filings and financial performance
- Stock performance over the past 7 days
- Market sentiment and analyst opinions
- Key risks and opportunities

Step 2: Develop Trading Strategies

Now I need to call the trading_analyst subagent. To tailor the strategies, please
tell me:
- What is your Risk Attitude? (conservative, moderate, aggressive)
- What is your Investment Period? (short-term, medium-term, long-term)

User: moderate risk, long-term investment

Agent: Thank you. I will now call the trading_analyst subagent with your moderate
risk profile and long-term investment horizon.

[Calls trading_analyst_agent]

Agent: The trading_analyst has proposed five potential trading strategies for AAPL:

1. **Core Long-Term Buy & Hold with Compounding**: Focus on AAPL's fundamentals,
   hold for capital appreciation and reinvest dividends
2. **Dividend Growth Focus (DRIP)**: Emphasize dividend reinvestment for compounding
3. **Long-Term Value Averaging on Dips**: Buy shares during significant corrections
   to lower average cost
4. **Covered Call Writing**: Generate income by selling call options (requires 100+
   shares)
5. **GARP Accumulation**: Buy when valuation metrics become more favorable

Each strategy includes detailed rationale, key indicators, entry/exit conditions,
and specific risks.

[Continues through execution planning and risk assessment steps...]
```

### Step 6: Run Tests

```bash
uv sync --dev
uv run pytest tests
```

### Step 7: Run Evaluations

```bash
uv run pytest eval
```

Evaluates:
- Agent workflow completion
- Response quality vs. reference answers
- Sub-agent orchestration correctness

### Step 8: Deploy to Vertex AI Agent Engine (Optional)

```bash
uv sync --group deployment
uv run deployment/deploy.py --create
```

Output:
```
Created remote agent: projects/123456789/locations/us-central1/reasoningEngines/987654321
```

**List deployed agents:**
```bash
uv run deployment/deploy.py --list
```

**Test deployment:**
```bash
export USER_ID=test-user
export AGENT_ENGINE_ID=987654321
uv run deployment/test_deployment.py --resource_id=${AGENT_ENGINE_ID} --user_id=${USER_ID}
```

**Delete deployment:**
```bash
uv run deployment/deploy.py --delete --resource_id=${AGENT_ENGINE_ID}
```

### Alternative: Using Agent Starter Pack

For production-ready deployment with CI/CD:

```bash
python -m venv .venv && source .venv/bin/activate
pip install --upgrade agent-starter-pack
agent-starter-pack create my-financial-advisor -a adk@financial-advisor
```

**OR using uv:**
```bash
uvx agent-starter-pack create my-financial-advisor -a adk@financial-advisor
```

## Customization Options

### 1. Enhance Data Analyst with Specialized Data Sources

Extend the data_analyst agent to access specialized financial APIs:

```python
from financial_advisor.sub_agents.data_analyst import agent

# Add custom tools for real-time data
from custom_tools import (
    get_yahoo_finance_data,
    get_sec_edgar_filings,
    get_finviz_sentiment
)

data_analyst_agent = LlmAgent(
    # ... existing config ...
    tools=[
        GoogleSearch(),
        get_yahoo_finance_data,
        get_sec_edgar_filings,
        get_finviz_sentiment
    ]
)
```

### 2. Add Specialized Analyst Personas

Create role-based variants of analysts:

```python
# Quantitative analyst focused on technical analysis
quant_analyst = LlmAgent(
    name="quant_analyst",
    model="gemini-2.5-pro",
    instruction="You are a quantitative analyst specializing in technical
                 indicators, chart patterns, and statistical analysis..."
    # ... tools ...
)

# Fundamental analyst focused on financial statements
fundamental_analyst = LlmAgent(
    name="fundamental_analyst",
    instruction="You are a fundamental analyst specializing in financial
                 statement analysis, DCF models, and valuation..."
    # ... tools ...
)
```

### 3. Refine Prompt Engineering

Iterate on prompts for better results:

```python
# financial_advisor/sub_agents/trading_analyst/prompt.py
TRADING_ANALYST_PROMPT = """
You are an expert trading strategist with 20 years of experience.

IMPORTANT CONSTRAINTS:
- Generate EXACTLY 5 distinct strategies
- Each strategy must have:
  * Clear entry/exit criteria with specific thresholds
  * Risk/reward ratio calculations
  * Position sizing formulas
  * Concrete examples using current market data
- Avoid generic advice; provide actionable specifics
- Reference actual technical indicators and their values
"""
```

### 4. Add Backtesting Capabilities

Integrate historical backtesting:

```python
def backtest_strategy(
    strategy_description: str,
    ticker: str,
    start_date: str,
    end_date: str
) -> dict:
    """Backtest a proposed strategy using historical data"""
    # Use libraries like backtrader, zipline, or vectorbt
    import backtrader as bt
    # Implementation...
    return {
        "total_return": 0.23,
        "sharpe_ratio": 1.45,
        "max_drawdown": -0.18,
        "win_rate": 0.62
    }
```

### 5. Implement Portfolio-Level Analysis

Add portfolio context:

```python
def portfolio_impact_analysis(
    new_position: dict,
    existing_portfolio: dict
) -> dict:
    """Analyze how a new position affects overall portfolio risk"""
    # Calculate correlation with existing holdings
    # Assess diversification impact
    # Compute updated portfolio metrics
    return {
        "new_portfolio_sharpe": 1.32,
        "correlation_with_existing": 0.45,
        "diversification_score": 0.78
    }
```

## Important Legal and Ethical Considerations

**Legal Disclaimer**:
- This tool is for **educational and informational purposes ONLY**
- Does NOT constitute financial advice, investment recommendations, or offers to buy/sell securities
- Google and affiliates make NO warranties about accuracy or completeness
- Users bear ALL risk for investment decisions
- Past performance does NOT guarantee future results
- Always consult a qualified financial advisor before investing

**Ethical Guidelines**:
- Clearly display disclaimers at all stages of interaction
- Never guarantee returns or minimize risks
- Encourage users to conduct independent research
- Emphasize the importance of professional financial advice
- Avoid creating a false sense of authority or certainty

**Regulatory Compliance**:
- Not intended for use as a registered investment advisor
- Should not replace human financial professionals
- Users must comply with all applicable securities regulations
- Tool should not be used for automated trading without proper oversight

## Performance Characteristics

**Agent Type:** Multi-Agent (1 coordinator + 4 specialists)
**Complexity:** Medium
**Models:** Gemini 2.5 Pro (configurable per agent)
**Interaction Type:** Structured conversational workflow

**Typical Execution Time**:
- Market analysis (Step 1): 30-60 seconds
- Strategy development (Step 2): 20-40 seconds
- Execution planning (Step 3): 30-50 seconds
- Risk assessment (Step 4): 20-40 seconds
- **Total workflow**: 2-4 minutes

**Tool Usage**:
- Google Search calls: 5-15 per market analysis
- State reads/writes: 4 major outputs stored
- Sub-agent calls: 4 (sequential)

---

**Model:** Gemini 2.5 Pro
**Complexity:** Medium
**Agent Type:** Multi-Agent (Coordinator + 4 Specialists)
**Python Version:** 3.10 - 3.12
**License:** Apache 2.0
**Author:** Antonio Gulli (gulli@google.com)
**Vertical:** Financial Services
