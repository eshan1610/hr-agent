#!/usr/bin/env python3
"""Employee Self-Service HR Copilot — powered by Groq + Pinecone RAG."""
from __future__ import annotations

import json
import os

from openai import OpenAI
from pinecone import Pinecone

from hr_data import EMPLOYEES, HR_METRICS, LEAVE_BALANCES

# ── Clients ───────────────────────────────────────────────────────────────────

_pc    = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
_index = _pc.Index("hrbot-knowledge")

EMBED_MODEL = "multilingual-e5-large"
TOP_K = 4


def _embed(text: str) -> list[float]:
    result = _pc.inference.embed(
        model=EMBED_MODEL,
        inputs=[text],
        parameters={"input_type": "query", "truncate": "END"},
    )
    return result[0]["values"]


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are Argus.ai, the Employee Self-Service AI Copilot for XYZ Company.
You support employees in India and China with accurate, policy-aligned HR answers in a warm, professional tone.

## Important Notice
This agent operates on a training-grade HR policy for demo and development purposes.
All figures and examples are illustrative only and are not legal advice.
For binding entitlements, employees should consult official HR documentation or contact their country HR team.

## Tools Available
- search_hr_knowledge   — semantic search over leave policies, benefits, holidays, HR contacts (Pinecone RAG)
- get_leave_balance     — exact leave balance lookup by employee ID
- get_hr_metrics        — monthly recruitment / attrition metrics

## Behaviour Rules
1. Always call the appropriate tool — never guess policy details or balances.
2. For leave balance queries, ask for the Employee ID (4-digit, e.g. 1001 for India, 2001 for China) if not provided.
3. When searching HR knowledge, always pass the correct country ('India' or 'China').
4. Present answers with bullet points and bold labels; use INR/₹ for India and CNY for China.
5. After answering, proactively offer related follow-up help.
6. Always remind employees that leave requests must be submitted via the HR system/portal.
7. If a question is outside HR scope, direct to the relevant country HR email.

## What You Do NOT Do
- Process or approve actual leave applications.
- Share salary slips or compensation data.
- Handle disciplinary actions, terminations, or performance management."""

SYSTEM_PROMPT = _SYSTEM_PROMPT

GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


def make_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1",
    )


# ── Tools ─────────────────────────────────────────────────────────────────────

def search_hr_knowledge(query: str, country: str = "India") -> str:
    """Search the HR knowledge base (policies, benefits, holidays, contacts) using semantic search.

    Args:
        query:   Natural-language question about HR policy, benefits, holidays, or contacts.
        country: Employee's country — 'India' or 'China' (default 'India').
    """
    query_vec = _embed(query)
    results = _index.query(
        vector=query_vec,
        top_k=TOP_K,
        include_metadata=True,
        filter={"country": {"$eq": country.strip().title()}},
    )
    matches = results.get("matches", [])
    if not matches:
        # Fallback: search without country filter
        results = _index.query(vector=query_vec, top_k=TOP_K, include_metadata=True)
        matches = results.get("matches", [])

    if not matches:
        return "No relevant HR policy information found. Please contact your country HR team directly."

    chunks = []
    for m in matches:
        meta = m.get("metadata", {})
        text = meta.get("text", "")
        topic = meta.get("topic", "")
        doc_country = meta.get("country", "")
        chunks.append(f"[{doc_country} — {topic}]\n{text}")

    return "\n\n---\n\n".join(chunks)


def get_leave_balance(employee_id: str) -> str:
    """Retrieve the current leave balance for a specific employee.

    Args:
        employee_id: The employee's unique ID (e.g. 1001 for India, 2001 for China).
    """
    eid = employee_id.strip()
    if eid not in EMPLOYEES:
        return f"Employee ID '{employee_id}' not found. Please verify the ID and try again."
    if eid not in LEAVE_BALANCES:
        return f"No leave balance data found for {eid}. Contact your country HR team."

    emp = EMPLOYEES[eid]
    if emp["status"] == "Resigned":
        return f"Employee {emp['name']} ({eid}) has resigned. Leave data is no longer accessible."

    balances = LEAVE_BALANCES[eid]
    hr_email = "india-hr@xyz.example" if emp["country"] == "India" else "cn-hr@xyz.example"
    lines = [
        f"Leave Balance — {emp['name']} ({eid})  [{emp['country']}]",
        f"Department: {emp['department']} | Role: {emp['designation']} | Manager: {emp['manager']}",
        "",
    ]
    for leave_type, days in balances.items():
        lines.append(f"  • {leave_type}: {days} day{'s' if days != 1 else ''} remaining")
    lines.append("\nTo apply for leave, submit a request via the HR system/portal.")
    lines.append(f"For balance corrections, contact: {hr_email}")
    return "\n".join(lines)


def get_hr_metrics(month: str = "all") -> str:
    """Retrieve monthly HR recruitment and attrition metrics.

    Args:
        month: A specific month like 'Jan-2026' or 'all' to see the full summary.
    """
    if month.lower() == "all":
        lines = [
            "HR Metrics (2026):", "",
            f"  {'Month':<12} {'Hires':>6} {'Exits':>6} {'Attrition%':>11} {'Avg Closure (days)':>20}",
            "  " + "-" * 60,
        ]
        for row in HR_METRICS:
            lines.append(
                f"  {row['month']:<12} {row['hires']:>6} {row['exits']:>6} "
                f"{row['attrition_pct']:>10.1f}% {row['avg_closure_days']:>19}"
            )
        return "\n".join(lines)

    target = month.strip()
    for row in HR_METRICS:
        if row["month"].lower() == target.lower():
            return (
                f"HR Metrics — {row['month']}:\n"
                f"  • Hires:            {row['hires']}\n"
                f"  • Exits:            {row['exits']}\n"
                f"  • Attrition %:      {row['attrition_pct']}%\n"
                f"  • Avg Closure Days: {row['avg_closure_days']} days"
            )

    available = ", ".join(r["month"] for r in HR_METRICS)
    return f"No data found for '{month}'. Available months: {available}"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_hr_knowledge",
            "description": "Search the HR knowledge base (policies, benefits, holidays, contacts) using semantic search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural-language question about HR policy, benefits, holidays, or contacts.",
                    },
                    "country": {
                        "type": "string",
                        "enum": ["India", "China"],
                        "description": "Employee's country (default 'India').",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_leave_balance",
            "description": "Retrieve the current leave balance for a specific employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "The employee's unique ID (e.g. 1001 for India, 2001 for China).",
                    },
                },
                "required": ["employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hr_metrics",
            "description": "Retrieve monthly HR recruitment and attrition metrics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {
                        "type": "string",
                        "description": "A specific month like 'Jan-2026' or 'all' for the full summary.",
                    },
                },
                "required": [],
            },
        },
    },
]

_TOOL_MAP = {
    "search_hr_knowledge": search_hr_knowledge,
    "get_leave_balance": get_leave_balance,
    "get_hr_metrics": get_hr_metrics,
}


def run_turn(
    client: OpenAI,
    messages: list[dict],
    country: str | None = None,
    max_rounds: int = 8,
) -> str:
    """Run one user turn through the tool-calling loop and return the reply text."""
    system = SYSTEM_PROMPT
    if country:
        system += (
            f"\n\n## Session Context\nThe employee you are assisting is based in {country}. "
            f"Default to {country} policies, currency, holidays and HR contacts "
            "unless they explicitly ask about another country."
        )
    convo = [{"role": "system", "content": system}] + messages
    reply = ""
    for _ in range(max_rounds):
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=2048,
            messages=convo,
            tools=TOOLS,
        )
        msg = resp.choices[0].message
        reply = msg.content or ""
        if not msg.tool_calls:
            break
        convo.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
            }
        )
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
                result = _TOOL_MAP[tc.function.name](**args)
            except Exception as exc:  # surface tool failures to the model
                result = f"Tool error: {exc}"
            convo.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    return reply


# ── CLI agent loop ────────────────────────────────────────────────────────────

def run_agent() -> None:
    client = make_client()
    messages: list[dict] = []

    print("\n" + "═" * 64)
    print("  Argus.ai — Employee Self-Service Copilot  |  XYZ Company")
    print("  Supports: India & China  |  Type 'exit' to end session.")
    print("═" * 64 + "\n")
    print("Argus.ai: Hello! I'm Argus.ai, your HR Self-Service assistant.")
    print("       Ask me about leave, benefits, holidays, or HR contacts.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nArgus.ai: Goodbye! Have a great day.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye", "goodbye"):
            print("\nArgus.ai: Goodbye! Stay well and feel free to return anytime.")
            break

        messages.append({"role": "user", "content": user_input})

        try:
            response_text = run_turn(client, messages)
        except Exception as exc:
            print(f"\nArgus.ai: Sorry, I ran into an API error ({exc}). Please try again.\n")
            messages.pop()
            continue

        if response_text:
            messages.append({"role": "assistant", "content": response_text})
            print(f"\nArgus.ai: {response_text}\n")
        else:
            print("\nArgus.ai: I'm sorry, I couldn't generate a response. Please try rephrasing.\n")
            messages.pop()


if __name__ == "__main__":
    run_agent()
