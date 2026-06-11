"""Argus.ai Web API — FastAPI backend for the HR Copilot."""
from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from agent import make_client, run_turn  # noqa: E402 (must load .env first)

app = FastAPI(title="Argus.ai API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = make_client()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []
    country: str = "India"


@app.post("/api/chat")
async def chat(req: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in req.history]
    messages.append({"role": "user", "content": req.message})

    try:
        response_text = await asyncio.get_event_loop().run_in_executor(
            None, lambda: run_turn(client, messages, country=req.country)
        )
    except Exception as exc:
        return {"response": f"Sorry, I ran into an error: {exc}. Please try again."}

    return {"response": response_text or "Sorry, I couldn't generate a response."}


# Serve frontend
static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
