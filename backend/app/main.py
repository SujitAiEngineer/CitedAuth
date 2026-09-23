"""
FastAPI spine for the live build.
Nothing domain specific lives here. Add routers under backend/app/ as needed.
"""
import os
import json
import asyncio
import time
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from anthropic import Anthropic

from backend.app.agents.graph import decide_row, summarize_reason
from backend.app.models import AnalyzeResponse, DeterminationResult, TokenUsage
from backend.app.tools.pdf_letter import build_letters_pdf
from backend.app.tools.xlsx_io import parse_requests

load_dotenv()

MODEL = os.getenv("MODEL", "claude-sonnet-5")
API_KEY = os.getenv("ANTHROPIC_API_KEY")

app = FastAPI(title="Live Build API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Anthropic(api_key=API_KEY) if API_KEY else None


class ChatRequest(BaseModel):
    message: str
    system: Optional[str] = None


@app.get("/api/health")
def health():
    """Proves the server is up and whether the model key is loaded."""
    return {
        "status": "ok",
        "model": MODEL,
        "api_key_loaded": bool(API_KEY),
    }


@app.post("/api/echo")
def echo(req: ChatRequest):
    """No model call. Use this to prove the frontend to backend wiring works."""
    return {"received": req.message, "length": len(req.message)}


@app.post("/api/chat")
def chat(req: ChatRequest):
    """Single turn model call. Blocking. Good enough for a first slice."""
    if client is None:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set in .env")
    kwargs = {
        "model": MODEL,
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": req.message}],
    }
    if req.system:
        kwargs["system"] = req.system
    resp = client.messages.create(**kwargs)
    text = "".join(b.text for b in resp.content if b.type == "text")
    return {
        "reply": text,
        "usage": {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
        },
    }


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    Server sent events. Use this when you want tokens visible on screen as they
    arrive. Demos far better than a spinner.
    """
    if client is None:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set in .env")

    def generate():
        kwargs = {
            "model": MODEL,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": req.message}],
        }
        if req.system:
            kwargs["system"] = req.system
        with client.messages.stream(**kwargs) as stream:
            for chunk in stream.text_stream:
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            final = stream.get_final_message()
            usage = {
                "input_tokens": final.usage.input_tokens,
                "output_tokens": final.usage.output_tokens,
            }
            yield f"data: {json.dumps({'done': True, 'usage': usage})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(file: UploadFile = File(...)):
    """
    One LLM call per row via the decide graph (backend/app/agents/graph.py).
    guardrail_check (the deterministic absence-vs-negation post-check) isn't
    wired in yet -- treat these as pre-guardrail determinations for now.
    """
    contents = await file.read()
    try:
        requests = parse_requests(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    start = time.perf_counter()
    results = []
    total_input = 0
    total_output = 0
    for r in requests:
        result, usage, latency_ms = decide_row(r)
        total_input += usage["input_tokens"]
        total_output += usage["output_tokens"]
        results.append(result)
    total_latency_ms = (time.perf_counter() - start) * 1000

    return AnalyzeResponse(
        results=results,
        usage=TokenUsage(input_tokens=total_input, output_tokens=total_output),
        latency_ms=total_latency_ms,
    )


@app.post("/api/letters/generate")
async def generate_letters(results: list[DeterminationResult]):
    """
    One summarize_reason LLM call per selected row (prose for the letter
    body), then a deterministic PDF render (backend/app/tools/pdf_letter.py).
    No backend persistence -- the frontend sends back the rows it already
    has from /api/analyze, filtered to the checked ones.
    """
    if not results:
        raise HTTPException(status_code=400, detail="No rows selected.")

    items = []
    for r in results:
        letter_text, _usage = summarize_reason(r)
        items.append((r, letter_text))

    pdf_bytes = build_letters_pdf(items)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=prior_auth_letters.pdf"},
    )


@app.post("/api/run")
def run_agent(req: ChatRequest):
    """
    Placeholder for the agent graph. Replace the body once /architect has
    settled on a shape. Returning a stub keeps the app runnable from minute one.
    """
    return {
        "status": "not_implemented",
        "note": "Agent graph goes here. Wire backend/app/agents/graph.py into this.",
        "input": req.message,
    }
