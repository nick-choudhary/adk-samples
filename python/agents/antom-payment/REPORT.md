# Antom Payment Agent - Technical Documentation Report

## Project Scope

The Antom Payment Agent is an AI-powered payment service integration that enables conversational payment processing through Ant International's Antom payment platform. The agent leverages the Model Context Protocol (MCP) to wrap Ant International's Antom payment APIs into standardized, AI-accessible tools.

**Core Capabilities:**
- **Payment Session Creation**: Generate secure payment links for customers through conversational interfaces
- **Payment Status Queries**: Retrieve real-time transaction status and payment details
- **Payment Cancellation**: Cancel pending payments when results aren't returned within expected timeframes
- **Refund Processing**: Initiate full or partial refunds for completed transactions
- **Refund Status Tracking**: Query and monitor refund request statuses

**Primary Use Cases:**
- E-commerce checkout flows via conversational interfaces
- Customer service chatbots handling payment inquiries
- Voice-enabled payment systems for accessibility
- Automated refund processing for customer support
- Order management systems with natural language interfaces

**Target Users:**
- E-commerce merchants using Ant International payment services
- Customer service teams managing payments and refunds
- Developers building conversational commerce experiences
- Digital wallet integrators

**Key Differentiator:**
This agent provides a seamless dialogue-based payment process, allowing merchants to flexibly organize payment flows according to consumer intent without requiring complex UI implementations.

## Technical Architecture

### Architecture Overview

The Antom Payment Agent implements a **single-agent architecture with MCP toolset integration**:

```
User Request → Antom Payment Agent (Gemini 2.0 Flash)
                    ↓
               MCPToolset (STDIO connection)
                    ↓
          ant-intl-antom-mcp server (uvx)
                    ↓
          Antom Payment APIs (Ant International)
```

### Code Flow

**Agent Initialization** (`antom-payemnt-agent/agent.py:7-43`):

1. **Agent Configuration**:
   - **Name**: `antom_payment_agent`
   - **Model**: Gemini 2.0 Flash (optimized for conversational interfaces)
   - **Description**: Creates payment links and queries payment details

2. **MCP Toolset Setup**:
   ```python
   MCPToolset(
       connection_params=StdioConnectionParams(
           server_params=StdioServerParameters(
               command='uvx',  # uv executable runner
               args=['ant-intl-antom-mcp'],  # MCP server package
               env={...}  # Antom API credentials
           )
       )
   )
   ```

3. **STDIO Connection**:
   - Uses `uvx` to spawn the Antom MCP server process
   - Communicates via standard input/output (STDIO)
   - Passes environment variables for authentication

### MCP (Model Context Protocol) Integration

**What is MCP?**
The Model Context Protocol (MCP) is a standardized protocol for exposing external tools and services to AI models. It provides:
- Uniform tool discovery and invocation
- Standard data schemas for requests/responses
- Secure credential management
- Process isolation between agent and external services

**Antom MCP Server** (`ant-intl-antom-mcp`):
- Installed via `uvx` (uv executable runner) on-demand
- Wraps Ant International Antom payment REST APIs
- Exposes five primary tools:
  1. `create_payment_session` - Generate payment checkout links
  2. `query_payment_detail` - Retrieve payment transaction status
  3. `cancel_payment` - Cancel pending payment requests
  4. `create_refund` - Initiate refund requests
  5. `query_refund_detail` - Check refund processing status

### Request Flow Example

**User**: "Create a payment link for an order called 'Cream Puff' for $100"

**Agent Processing**:
1. Parses user intent: Create payment for "Cream Puff", amount $100
2. Generates random `RequestId` (per instructions)
3. Invokes `create_payment_session` via MCP toolset:
   ```json
   {
     "orderDescription": "Cream Puff",
     "amount": {"currency": "USD", "value": "100.00"},
     "requestId": "<randomly_generated>"
   }
   ```
4. MCP server calls Antom API with merchant credentials
5. Receives payment session response with checkout URL
6. Formats conversational response with payment link
7. Adds creative description of "Cream Puff" (per instructions)

**Response**:
```
🔗 Payment Link:
https://open-sea-global.alipayplus.com/api/open/v1/ac/cashier/self/codevalue/checkout.htm?codeValue=...

"Indulge in our heavenly Cream Puff — a delicate, golden shell filled with
silky vanilla custard and a hint of caramel, perfect for any sweet craving."
```

### Key Libraries and Dependencies

**Core Framework:**
- `google-adk>=1.11.0` - Google Agent Development Kit for agent orchestration
- `mcp>=1.13.0` - Model Context Protocol for tool integration

**MCP Integration Components:**
- `google.adk.tools.MCPToolset` - Wrapper for MCP tool collections
- `google.adk.tools.mcp_tool.StdioConnectionParams` - STDIO communication configuration
- `mcp.StdioServerParameters` - MCP server process parameters

**External MCP Server:**
- `ant-intl-antom-mcp` - Ant International's MCP server (installed via uvx)
  - Not a direct dependency (installed on-demand)
  - Provides payment and refund operation tools
  - Handles authentication and API communication with Antom

**Runtime:**
- `uvx` - uv executable runner for MCP server process management
- Python 3.11+ - Required for MCP protocol support

### Agent Reasoning and Instructions

The agent operates with specific behavioral instructions (`agent.py:13-20`):

1. **Identity**: Positions itself as an "Antom payment agent"
2. **Core Functions**: Creates payment links and queries payment details
3. **RequestId Generation**: Automatically generates random request IDs
4. **Order Descriptions**: Adds creative one-sentence descriptions for orders
5. **Refund Logic**:
   - Retrieves order details and paymentId from original payment request
   - Defaults to full refund in order currency if amount not specified
6. **Conversational Style**: Natural language responses with emojis and formatting

### Security Considerations

**Credential Management:**
- All sensitive credentials passed via environment variables
- MCP server process inherits environment from parent
- No hardcoded credentials in code
- Credentials required:
  - `GATEWAY_URL` - Antom API gateway endpoint
  - `CLIENT_ID` - Merchant client identifier
  - `MERCHANT_PRIVATE_KEY` - RSA private key for signing requests
  - `ALIPAY_PUBLIC_KEY` - RSA public key for verifying responses
  - `PAYMENT_REDIRECT_URL` - Post-payment redirect destination
  - `PAYMENT_NOTIFY_URL` - Webhook for payment status notifications

**Process Isolation:**
- MCP server runs as separate process
- Communication limited to STDIO channel
- Agent cannot directly access payment APIs

## Build & Run Instructions

### Prerequisites

1. **Python 3.11 or higher** (required for MCP support)
2. **uv** package manager (recommended):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   **OR** Poetry:
   ```bash
   pip install poetry
   ```
3. **Ant International Antom Merchant Account** with:
   - Valid merchant credentials (Client ID, private key)
   - Configured payment redirect and notification URLs
   - Access to Antom API gateway

### Step 1: Clone Repository and Navigate to Project

```bash
git clone https://github.com/google/adk-samples.git
cd adk-samples/python/agents/antom-payment
```

### Step 2: Install Dependencies

**Option A: Using uv (Recommended)**
```bash
uv venv
uv sync
```

**Option B: Using Poetry**
```bash
pip install poetry
poetry install
```

### Step 3: Configure Environment Variables

Create `.env` file in `python/agents/antom-payment/antom-payemnt-agent/`:

```bash
cp .env.example antom-payemnt-agent/.env
```

Edit `antom-payemnt-agent/.env`:

```bash
# Google Cloud / Gemini Configuration
GOOGLE_GENAI_USE_VERTEXAI=true
# OR for direct API access:
# GOOGLE_API_KEY=your-api-key

# Antom Payment Configuration
GATEWAY_URL=https://open-sea.alipay.com  # or your regional gateway
CLIENT_ID=your-merchant-client-id
MERCHANT_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nMIIEvQI...\n-----END PRIVATE KEY-----
ALIPAY_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----\nMIIBIjAN...\n-----END PUBLIC KEY-----
PAYMENT_REDIRECT_URL=https://yourwebsite.com/payment/return
PAYMENT_NOTIFY_URL=https://yourwebsite.com/payment/notify
```

**Important Notes:**
- Replace all placeholder values with actual Antom merchant credentials
- Private/public keys should be properly formatted with `\n` for newlines
- Notification URL must be publicly accessible for webhooks

### Step 4: Run the Agent

**Using uv:**
```bash
uv run adk web
```

**Using Poetry:**
```bash
poetry run adk web
```

The command will:
1. Start a local web server
2. Print the URL (typically `http://localhost:8000`)
3. Open the ADK web interface

### Step 5: Interact with the Agent

Open the printed URL in your browser and try these example prompts:

**Example 1: Create Payment Link**
```
User: Create a payment link for an order called "Cream Puff" for $100

Agent: Sure! Here's a payment link for an order called "Cream Puff" for $100:

🔗 Payment Link:
https://open-sea-global.alipayplus.com/api/open/v1/ac/cashier/...

"Indulge in our heavenly Cream Puff — a delicate, golden shell filled with
silky vanilla custard and a hint of caramel, perfect for any sweet craving."
```

**Example 2: Query Payment Status**
```
User: Check the status of payment request ID 12345

Agent: Let me check that for you...
[Agent queries payment details and returns transaction status]
```

**Example 3: Process Refund**
```
User: Refund the payment with request ID 12345

Agent: I'll process a full refund for that payment...
[Agent retrieves payment details and creates refund request]
```

**Example 4: Cancel Payment**
```
User: Cancel the pending payment 67890

Agent: I'll cancel that payment request for you...
[Agent cancels the payment session]
```

### Available MCP Tools

Once the agent is running, it has access to these tools via the Antom MCP server:

1. **create_payment_session**
   - Generates payment checkout links
   - Parameters: order description, amount, currency, merchant details
   - Returns: Payment URL for customer checkout

2. **query_payment_detail**
   - Retrieves transaction status
   - Parameters: payment request ID
   - Returns: Payment status, amount, timestamp, etc.

3. **cancel_payment**
   - Cancels pending payments
   - Parameters: payment request ID
   - Returns: Cancellation confirmation

4. **create_refund**
   - Initiates refund requests
   - Parameters: payment ID, refund amount (optional)
   - Returns: Refund request ID and status

5. **query_refund_detail**
   - Checks refund status
   - Parameters: refund request ID
   - Returns: Refund processing status and details

### Troubleshooting

**MCP Server Connection Errors:**
- Ensure `uvx` is available in your PATH (installed with uv)
- Verify `ant-intl-antom-mcp` can be accessed via uvx
- Check environment variables are properly set

**Authentication Failures:**
- Verify CLIENT_ID matches your Antom merchant account
- Ensure RSA keys are properly formatted (include headers and newlines)
- Confirm GATEWAY_URL points to correct regional endpoint

**Payment Creation Fails:**
- Check PAYMENT_REDIRECT_URL and PAYMENT_NOTIFY_URL are accessible
- Verify merchant account has active status
- Ensure currency and amount formats are valid

**Environment Variables Not Loading:**
- Confirm `.env` file is in `antom-payemnt-agent/` directory
- Check file permissions allow reading
- Restart the agent after modifying `.env`

## Customization Options

### 1. Customize Order Descriptions

Modify the agent instruction to change how order descriptions are generated:

```python
instruction=(
    "When creating payment links, include detailed product descriptions "
    "with pricing breakdown, shipping information, and estimated delivery dates."
)
```

### 2. Add Payment Validation Logic

Extend the agent to validate payment amounts before processing:

```python
instruction=(
    "Before creating payment links, verify that amounts are within "
    "acceptable ranges ($1-$10,000) and currency codes are valid (USD, EUR, GBP)."
)
```

### 3. Integrate Additional MCP Tools

Add complementary MCP services (if available):

```python
tools=[
    MCPToolset(...),  # Antom payment
    MCPToolset(...),  # Inventory check MCP
    MCPToolset(...),  # Shipping calculation MCP
]
```

### 4. Multi-Currency Support

Enhance instructions for currency conversion:

```python
instruction=(
    "Support multiple currencies. When amount is specified without currency, "
    "ask the user for their preferred currency (USD, EUR, CNY, etc.)."
)
```

### 5. Payment Link Customization

Add branded payment link generation:

```python
instruction=(
    "Include merchant branding in payment descriptions. "
    "Add order number, customer name, and itemized list when creating payment sessions."
)
```

## Production Deployment Considerations

**Security Best Practices:**
- Never commit `.env` files with real credentials to version control
- Use secret management services (Google Secret Manager, AWS Secrets Manager)
- Implement webhook signature verification for PAYMENT_NOTIFY_URL
- Use HTTPS for all redirect and notification URLs
- Rotate RSA keys periodically

**Scalability:**
- MCP server processes are spawned per-agent instance
- Consider connection pooling for high-traffic scenarios
- Implement rate limiting to comply with Antom API quotas
- Cache payment status queries to reduce API calls

**Monitoring:**
- Log all payment operations with request IDs
- Track MCP connection failures and retries
- Monitor payment success/failure rates
- Set up alerts for refund anomalies

**Compliance:**
- Ensure PCI DSS compliance for payment data handling
- Implement audit logs for all financial transactions
- Configure data retention policies per regional regulations
- Add user consent flows for payment processing

## Integration Architecture

**Typical E-Commerce Integration:**
```
Customer Chat → Antom Payment Agent → MCP Server → Antom APIs
                        ↓
                 Order Management System (webhook)
                        ↓
                 Fulfillment Pipeline
```

**Customer Service Integration:**
```
Support Agent → Antom Payment Agent → Refund Processing
                        ↓
                 CRM System (status update)
                        ↓
                 Customer Notification
```

---

**Authors:**
- Steven (duanmuci@ant-intl.com)
- Zunjiao Wang (wangzunjiao.wzj@digital-engine.com)

**License:** Apache License 2.0
**Python Version:** 3.11+
**Model:** Gemini 2.0 Flash
**Complexity:** Simple (Single Agent with MCP Integration)
