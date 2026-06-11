"""
Simple FastAPI test application for AI Guard Safety observability pipeline.

Flow: User → POST /chat → aiguard.chat() → LiteLLM → LLM → response

The `aiguard` package (installed as aiguard-safety) intercepts every call to
aiguard.chat() to:
  • build a TraceEvent (prompt, response, latency, token usage)
  • enqueue it for non-blocking background processing
  • forward the trace to the AI Guard monitoring pipeline
"""

import os
import aiguard
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


# ── AI Guard SDK – one-time configuration ────────────────────────────────────
# sampling_rate=1.0 → trace every request (good for testing)
# Reads aiguard.yaml from CWD if present; CLI overrides take priority.
aiguard.configure(sampling_rate=1.0)

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Guard Safety – Test LLM App",
    description=(
        "Minimal test app that routes LLM calls through the AI Guard Safety SDK "
        "to generate traces for the monitoring pipeline."
    ),
    version="0.1.0",
)


# ── Request / Response schemas ────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


# ── Endpoint ──────────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Accept a user message, call the LLM through the AI Guard Safety SDK,
    and return the model's response.

    aiguard.chat() is a transparent wrapper around LiteLLM that:
      • instruments the call with latency + token-usage metrics
      • enqueues a TraceEvent for the monitoring pipeline
      • returns the unmodified LiteLLM response
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message must not be empty.")

    model = os.getenv("LLM_MODEL", "gpt-5.2")

    try:
        response = aiguard.chat(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",   "content": request.message},
            ],
            endpoint_name="/chat",
        )

        answer = response.choices[0].message.content
        return ChatResponse(response=answer)

    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}") from exc


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Simple liveness check."""
    return {"status": "ok"}
