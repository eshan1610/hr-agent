"""HRBot Web API — FastAPI backend for the HR Copilot."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from agent import CACHED_SYSTEM, TOOLS  # noqa: E402 (must load .env first)

app = FastAPI(title="HRBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []


@app.post("/api/chat")
async def chat(req: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in req.history]
    messages.append({"role": "user", "content": req.message})

    def run_agent():
        runner = client.beta.messages.tool_runner(
            model="claude-opus-4-6",
            max_tokens=2048,
            system=CACHED_SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        last_msg = None
        for msg in runner:
            last_msg = msg
        return last_msg

    try:
        last_msg = await asyncio.get_event_loop().run_in_executor(None, run_agent)
    except anthropic.APIError as exc:
        return {"response": f"Sorry, I ran into an error: {exc}. Please try again."}

    if last_msg is None:
        return {"response": "Sorry, I couldn't generate a response. Please try rephrasing."}

    response_text = "".join(
        block.text for block in last_msg.content if block.type == "text"
    )
    return {"response": response_text or "Sorry, I couldn't generate a response."}


# Serve frontend
static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
