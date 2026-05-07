# ── Install & Import ──
%pip install -q anthropic

import anthropic
import json
import time
import os
from IPython.display import display, Markdown

# ── API Key Configuration ──
# Option 1: Colab Secrets (recommended — click the 🔑 icon in the left sidebar)
try:
    from google.colab import userdata
    os.environ["ANTHROPIC_API_KEY"] = userdata.get("ANTHROPIC_API_KEY")
    print("✅ API key loaded from Colab Secrets")
except Exception:
    pass

# Option 2: Paste directly (uncomment and replace)
# os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."

client = anthropic.Anthropic(timeout=900.0)  # Longer timeout: needed for max_tokens>21333 with non-streaming calls
MODEL = "claude-sonnet-4-6"

# ── Pre-flight Check ──
errors = []
if not os.environ.get("ANTHROPIC_API_KEY"):
    errors.append("❌ ANTHROPIC_API_KEY not set. Use Colab Secrets (🔑 sidebar) or paste it above.")

sdk_version = anthropic.__version__
print(f"SDK version: {sdk_version}")

if not errors:
    try:
        test = client.messages.create(
            model=MODEL, max_tokens=1024,
            messages=[{"role": "user", "content": "Reply with only: ready"}],
            thinking={"type": "adaptive"},
        )
        text = "".join(b.text for b in test.content if b.type == "text").strip()
        print(f"✅ Model: {MODEL}")
        print(f"✅ API connected — test response: {text}")
    except anthropic.AuthenticationError:
        errors.append("❌ API key is invalid. Check your key and try again.")
    except anthropic.BadRequestError as e:
        errors.append(f"❌ API error: {e}. Your SDK may need updating: %pip install -q --upgrade anthropic")
    except Exception as e:
        errors.append(f"❌ Connection error: {e}")

if errors:
    print("\n⚠️  Setup issues detected:")
    for err in errors:
        print(f"   {err}")
    print("\nFix the issues above and re-run this cell.")
else:
    print("\n🚀 Ready to build!")

# ── Sample Ticket Data ──

TICKETS = {
    "TKT-1042": {
        "id": "TKT-1042", "customer": "Acme Corp", "priority": "high",
        "product_area": "billing",
        "description": "We were charged twice for our March invoice. Invoice #INV-2024-0342 shows $4,500 but our bank shows two identical charges on March 3rd. Need immediate refund of the duplicate charge.",
        "status": "open"
    },
    "TKT-1043": {
        "id": "TKT-1043", "customer": "DataFlow Inc", "priority": "medium",
        "product_area": "api",
        "description": "Our webhook endpoint stopped receiving events after we rotated API keys yesterday. We've verified the new key works for REST calls but webhooks are still failing. Getting 401 errors in the webhook logs.",
        "status": "open"
    },
    "TKT-1044": {
        "id": "TKT-1044", "customer": "CloudScale Ltd", "priority": "low",
        "product_area": "feature_request",
        "description": "Would love to see bulk export functionality in the dashboard. Currently we have to export reports one at a time which is painful when we need quarterly summaries across 50+ projects.",
        "status": "open"
    },
    "TKT-1045": {
        "id": "TKT-1045", "customer": "SecureNet Systems", "priority": "critical",
        "product_area": "account",
        "description": "Our admin account (admin@securenet.io) is locked out after failed MFA attempts. We have 47 team members who can't access the platform because SSO is tied to this admin account. This is blocking all work.",
        "status": "open"
    },
    "TKT-1046": {
        "id": "TKT-1046", "customer": "MedTech Solutions", "priority": "high",
        "product_area": "api",
        "description": "Our production integration started returning intermittent 500 errors around 2am last night. About 15% of API calls are failing. We haven't changed anything on our end. Errors seem random - sometimes the same request works on retry. Our team in Singapore is blocked and we need this resolved ASAP.",
        "status": "open"
    },
}

KB_ARTICLES = {
    "KB-001": {"title": "Processing Duplicate Payment Refunds", "content": "For duplicate charges: 1) Verify the duplicate in the billing system, 2) Issue refund through the payment processor (takes 3-5 business days), 3) Send confirmation email with refund reference number. Escalate if amount exceeds $10,000."},
    "KB-002": {"title": "Webhook Authentication After Key Rotation", "content": "When API keys are rotated, webhook signing secrets must also be updated. Go to Settings > Webhooks > Edit endpoint, and regenerate the signing secret. The old secret is invalidated immediately on key rotation. Common mistake: rotating the API key but not the webhook signing secret."},
    "KB-003": {"title": "Bulk Export Feature (Roadmap)", "content": "Bulk export is on the Q3 roadmap. Workaround: Use the REST API's /reports/export endpoint with date range parameters to programmatically export multiple reports. See API docs for batch export examples."},
    "KB-004": {"title": "Admin Account Lockout Recovery", "content": "For locked admin accounts: 1) Verify identity through the secondary email on file, 2) Reset MFA through the admin recovery flow at /admin/recover, 3) Temporary access can be granted through support-level override (requires manager approval). Critical: If SSO is blocked, enable the bypass login at /login/direct for affected users."},
    "KB-005": {"title": "API Rate Limiting Best Practices", "content": "Default rate limits: 100 requests/minute for standard plans, 1000/minute for enterprise. Use exponential backoff with jitter for retries. Monitor usage via the X-RateLimit headers in responses."},
    "KB-006": {"title": "Invoice Discrepancy Resolution", "content": "For billing discrepancies: Check the billing audit log for the account, compare with payment processor records, and verify no pending transactions. Contact finance team for adjustments over $5,000."},
    "KB-007": {"title": "Intermittent 500 Errors Troubleshooting", "content": "For intermittent server errors: 1) Check the status page for known outages, 2) Review rate limit headers - 429s can masquerade as 500s behind load balancers, 3) Check if errors correlate with payload size or specific endpoints, 4) Enable request ID logging and contact support with specific request IDs for investigation. If >10% error rate persists for >1 hour, escalate to engineering."},
}

def get_ticket(ticket_id: str) -> str:
    ticket = TICKETS.get(ticket_id)
    if ticket:
        return json.dumps(ticket)
    return json.dumps({"error": f"Ticket {ticket_id} not found"})

def search_kb(query: str) -> str:
    query_lower = query.lower()
    results = []
    for article_id, article in KB_ARTICLES.items():
        if any(word in article["title"].lower() or word in article["content"].lower()
               for word in query_lower.split() if len(word) > 2):
            results.append({"id": article_id, **article})
    if not results:
        results = [{"id": "KB-000", "title": "No matches found", "content": "No relevant articles found. Consider escalating to Tier 2 support."}]
    return json.dumps(results[:3])

def resolve_ticket(ticket_id: str, resolution: str, status: str = "resolved") -> str:
    ticket = TICKETS.get(ticket_id)
    if ticket:
        ticket["status"] = status
        ticket["resolution"] = resolution
        return json.dumps({"success": True, "ticket_id": ticket_id, "new_status": status})
    return json.dumps({"error": f"Ticket {ticket_id} not found"})

TOOL_FUNCTIONS = {"get_ticket": get_ticket, "search_kb": search_kb, "resolve_ticket": resolve_ticket}

def execute_tool(name: str, input_data: dict) -> str:
    func = TOOL_FUNCTIONS.get(name)
    if func:
        return func(**input_data)
    return json.dumps({"error": f"Unknown tool: {name}"})

print("Mock tools and sample data loaded!")
print(f"   Available tickets: {', '.join(TICKETS.keys())}")
print(f"   Knowledge base articles: {len(KB_ARTICLES)}")

# ── Tool Schemas ──

tools = [
    {
        "name": "get_ticket",
        "description": "Retrieve full details for a support ticket by its ID, including customer, priority, product area, and description.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string", "description": "The ticket ID, e.g. TKT-1042"}
            },
            "required": ["ticket_id"]
        }
    },
    {
        "name": "search_kb",
        "description": "Search the knowledge base for articles relevant to a support issue. Returns up to 3 matching articles with titles and resolution content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query describing the issue or topic, e.g. 'duplicate charge refund' or 'webhook authentication after key rotation'"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "resolve_ticket",
        "description": "Close a support ticket by recording the resolution and updating its status to resolved, escalated, or pending customer response.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string", "description": "The ticket ID to resolve, e.g. TKT-1042"},
                "resolution": {"type": "string", "description": "Detailed resolution note describing actions taken, steps provided to the customer, and outcome"},
                "status": {
                    "type": "string",
                    "enum": ["resolved", "escalated", "pending_customer"],
                    "description": "New ticket status: resolved (issue fixed), escalated (needs Tier 2/engineering), pending_customer (waiting on customer action)"
                }
            },
            "required": ["ticket_id", "resolution", "status"]
        }
    }
]

print(f"Defined {len(tools)} tool schemas: {[t['name'] for t in tools]}")

SYSTEM_PROMPT = """You are a Tier 1 support agent for TechFlow, a B2B SaaS platform that provides project management and team collaboration tools to mid-market companies.

## Your Role
You handle incoming support tickets by investigating issues, finding solutions in the knowledge base, and resolving tickets with clear, actionable guidance.

## Process
1. ALWAYS look up the ticket first to understand the full context
2. Search the knowledge base for relevant solutions and procedures
3. Resolve the ticket with a detailed resolution that includes specific next steps

## Guidelines
- Be thorough: always search the KB before resolving, even if the issue seems straightforward
- Be specific: include exact steps, links, and timeframes in resolutions
- Escalate when needed: if confidence is low or the issue requires privileged access, mark for escalation
- Categorize accurately: billing, technical, account, or feature_request

## Escalation Criteria
- Financial issues over $10,000
- Security-related account compromises
- Issues requiring engineering intervention
- Customers with Enterprise SLA (response within 1 hour)

## TechFlow Product Tiers
- Starter ($29/user/month): Basic project management, 5GB storage, email support, 5 projects max, community forums
- Professional ($79/user/month): Advanced analytics, 100GB storage, priority support, API access, unlimited projects, custom fields, Gantt charts, time tracking
- Enterprise (custom pricing): SSO/SAML, unlimited storage, dedicated CSM, custom integrations, SLA guarantees, audit logs, advanced security, custom branding, priority API rate limits

## Common Issue Categories and Routing
- Billing: Invoice discrepancies, payment failures, plan changes, refund requests, subscription cancellations, proration questions
- Technical: API errors, integration issues, webhook failures, performance problems, data export issues, browser compatibility
- Account: Login issues, MFA problems, SSO configuration, permission changes, team management, user provisioning
- Feature Requests: Product feedback, roadmap inquiries, workaround requests, beta access requests

## Response Templates
When resolving billing issues, always include: transaction ID, refund timeline, and confirmation email details.
When resolving technical issues, always include: steps to reproduce, workaround if available, and engineering ticket number if escalated.
When resolving account issues, always include: security verification steps taken and any temporary access granted.

## SLA Requirements
- Starter: 24-hour response time, business hours only
- Professional: 4-hour response time, extended hours (6am-10pm)
- Enterprise: 1-hour response time, 24/7 support, dedicated Slack channel

## Tone
Professional, empathetic, and solution-oriented. Acknowledge the customer frustration before jumping to the solution. Use the customer name when available. Reference the specific product tier for relevant guidance."""


def run_agent(user_message: str):
    """Run the support ticket agent."""
    messages = [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=32000,
        system=SYSTEM_PROMPT,
        tools=tools,
        thinking={"type": "adaptive"},
        messages=messages
    )

    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result)
                })

        # Pass ALL content blocks back (including thinking blocks)
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=MODEL,
            max_tokens=32000,
            system=SYSTEM_PROMPT,
            tools=tools,
            thinking={"type": "adaptive"},
            messages=messages
        )

    return response


# Test it!
# response = run_agent("Resolve ticket TKT-1042")
# for block in response.content:
#     if block.type == "text" and block.text.strip():
#         print(f"\n Final response:\n{block.text}")

RESOLUTION_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "diagnosis": {"type": "string", "description": "Root cause analysis of the issue"},
            "solution_steps": {"type": "array", "items": {"type": "string"}, "description": "Ordered steps to resolve"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "escalation_needed": {"type": "boolean"},
            "category": {"type": "string", "enum": ["billing", "technical", "account", "feature_request"]}
        },
        "required": ["diagnosis", "solution_steps", "confidence", "escalation_needed", "category"],
        "additionalProperties": False
    }
}


def get_structured_result(response) -> dict:
    """Extract the structured JSON from the last text block in the response."""
    # With adaptive thinking, content may be [thinking, text] - JSON is in the last text block
    text_blocks = [b for b in response.content if b.type == "text" and b.text.strip()]
    if text_blocks:
        return json.loads(text_blocks[-1].text)
    return None


def run_agent_structured(user_message: str) -> dict:
    """Run the agent with structured JSON output."""
    # Step 1: Run the tool loop without output_config.format
    # (format constrains ALL text output, so tools won't work with it active)
    messages = [{"role": "user", "content": user_message}]
    response = client.messages.create(
        model=MODEL, max_tokens=32000, system=SYSTEM_PROMPT,
        tools=tools, thinking={"type": "adaptive"}, messages=messages
    )
    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(result)})
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
        response = client.messages.create(
            model=MODEL, max_tokens=32000, system=SYSTEM_PROMPT,
            tools=tools, thinking={"type": "adaptive"}, messages=messages
        )

    # Step 2: Append final assistant turn, then request structured output
    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": "Provide your structured resolution as JSON."})
    final = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        output_config={"format": RESOLUTION_SCHEMA},
        tool_choice={"type": "none"},
        thinking={"type": "adaptive"},
        messages=messages
    )
    return get_structured_result(final)


# result = run_agent_structured("Resolve ticket TKT-1042")
# print(json.dumps(result, indent=2))

def run_agent_thinking(user_message: str, effort: str = "high") -> dict:
    """Run agent with effort-controlled adaptive thinking."""
    messages = [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model=MODEL, max_tokens=32000, system=SYSTEM_PROMPT,
        tools=tools, thinking={"type": "adaptive"},
        output_config={"effort": effort},
        messages=messages
    )

    while response.stop_reason == "tool_use":
        # Display thinking blocks so callers can observe the agent's reasoning
        for block in response.content:
            if block.type == "thinking" and block.thinking:
                preview = block.thinking[:300]
                print(f"\n[Thinking ({effort} effort)]: {preview}{'...' if len(block.thinking) > 300 else ''}")

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\n[Tool call]: {block.name}({json.dumps(block.input)})")
                result = execute_tool(block.name, block.input)
                print(f"[Tool result]: {result[:200]}")
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(result)})

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=MODEL, max_tokens=32000, system=SYSTEM_PROMPT,
            tools=tools, thinking={"type": "adaptive"},
            output_config={"effort": effort},
            messages=messages
        )

    # Final call: structured output with same effort level, no further tool calls
    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": "Provide your structured resolution as JSON."})
    final = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        output_config={"effort": effort, "format": RESOLUTION_SCHEMA},
        tool_choice={"type": "none"},
        thinking={"type": "adaptive"},
        messages=messages
    )
    return get_structured_result(final)


# Run the ambiguous ticket at high effort — observe the thinking traces
print("=== TKT-1046: Intermittent API Errors (ambiguous) ===\n")
result = run_agent_thinking("Resolve ticket TKT-1046", effort="high")
print(f"\nResolution:")
print(json.dumps(result, indent=2))

# Now compare: same ticket, low effort
print(f"\n\n{'='*50}")
print("=== Same ticket, LOW effort ===")
print(f"{'='*50}\n")

for effort in ["high", "low"]:
    start = time.time()
    result = run_agent_thinking("Resolve ticket TKT-1046", effort=effort)
    elapsed = time.time() - start
    print(f"\n[effort={effort}] Confidence: {result['confidence']} | Steps: {len(result['solution_steps'])} | Escalate: {result['escalation_needed']} | Time: {elapsed:.1f}s")


def run_agent_streaming(user_message: str, effort: str = "high") -> dict:
    """Run agent with streaming output."""
    messages = [{"role": "user", "content": user_message}]

    while True:
        with client.messages.stream(
            model=MODEL,
            max_tokens=32000,
            system=SYSTEM_PROMPT,
            tools=tools,
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
            messages=messages
        ) as stream:
            current_block_type = None

            for event in stream:
                if event.type == "content_block_start":
                    current_block_type = event.content_block.type
                    if current_block_type == "thinking":
                        print("\n[Thinking] ", end="", flush=True)
                    elif current_block_type == "tool_use":
                        print(f"\n[Tool: {event.content_block.name}] ", end="", flush=True)
                    elif current_block_type == "text":
                        print("\n[Response] ", end="", flush=True)

                elif event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "thinking_delta":
                        # Print a short preview so output stays readable
                        chunk = delta.thinking
                        print(chunk[:80] if len(chunk) > 80 else chunk, end="", flush=True)
                    elif delta.type == "text_delta":
                        print(delta.text, end="", flush=True)
                    elif delta.type == "input_json_delta":
                        print(delta.partial_json, end="", flush=True)

            response = stream.get_final_message()

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                print(f"\n[Tool result: {block.name}] {result[:200]}")
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(result)})

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    # Final call: structured output, no further tool calls
    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": "Provide your structured resolution as JSON."})

    with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        output_config={"effort": effort, "format": RESOLUTION_SCHEMA},
        tool_choice={"type": "none"},
        thinking={"type": "adaptive"},
        messages=messages
    ) as stream:
        print("\n[Structured output streaming...] ", end="", flush=True)
        for event in stream:
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
        final = stream.get_final_message()

    return get_structured_result(final)


print("Full Agent Demo: Resolving TKT-1045 (account lockout)")
print("   Streaming + Adaptive Thinking + Tools + Structured Output")
print("=" * 60)

start = time.time()
result = run_agent_streaming("Resolve ticket TKT-1045")
elapsed = time.time() - start

print(f"\n\n{'=' * 60}")
print(f"Total time: {elapsed:.1f}s")
print(f"\nStructured Resolution:")
print(json.dumps(result, indent=2))
