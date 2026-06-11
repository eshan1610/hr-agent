#!/usr/bin/env python3
"""Employee Self-Service HR Copilot — powered by Claude + Pinecone RAG."""
from __future__ import annotations

import os

import anthropic
from anthropic import beta_tool
from openai import OpenAI
from pinecone import Pinecone

from hr_data import EMPLOYEES, HR_METRICS, LEAVE_BALANCES

# ── Clients ───────────────────────────────────────────────────────────────────

_pc  = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
_oai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
_index = _pc.Index("hrbot-knowledge")

EMBED_MODEL = "text-embedding-3-small"
TOP_K = 4


def _embed(text: str) -> list[float]:
    return _oai.embeddings.create(model=EMBED_MODEL, input=[text]).data[0].embedding


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are HRBot, the Employee Self-Service AI Copilot for XYZ Company.
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

CACHED_SYSTEM = [
    {"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
]


# ── Tools ─────────────────────────────────────────────────────────────────────

@beta_tool
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


@beta_tool
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


@beta_tool
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


TOOLS = [search_hr_knowledge, get_leave_balance, get_hr_metrics]


# ── CLI agent loop ────────────────────────────────────────────────────────────

def run_agent() -> None:
    client = anthropic.Anthropic()
    messages: list[dict] = []

    print("\n" + "═" * 64)
    print("  HRBot — Employee Self-Service Copilot  |  XYZ Company")
    print("  Supports: India & China  |  Type 'exit' to end session.")
    print("═" * 64 + "\n")
    print("HRBot: Hello! I'm HRBot, your HR Self-Service assistant.")
    print("       Ask me about leave, benefits, holidays, or HR contacts.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHRBot: Goodbye! Have a great day.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye", "goodbye"):
            print("\nHRBot: Goodbye! Stay well and feel free to return anytime.")
            break

        messages.append({"role": "user", "content": user_input})

        runner = client.beta.messages.tool_runner(
            model="claude-opus-4-6",
            max_tokens=2048,
            system=CACHED_SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        last_msg = None
        try:
            for msg in runner:
                last_msg = msg
        except anthropic.APIError as exc:
            print(f"\nHRBot: Sorry, I ran into an API error ({exc}). Please try again.\n")
            messages.pop()
            continue

        if last_msg is None:
            print("\nHRBot: I'm sorry, I couldn't generate a response. Please try rephrasing.\n")
            messages.pop()
            continue

        response_text = "".join(
            block.text for block in last_msg.content if block.type == "text"
        )

        if response_text:
            messages.append({"role": "assistant", "content": response_text})
            print(f"\nHRBot: {response_text}\n")
        else:
            print("\nHRBot: I'm sorry, I couldn't generate a response. Please try rephrasing.\n")
            messages.pop()


if __name__ == "__main__":
    run_agent()
