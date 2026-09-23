"""
Two-node graph for the judgment step (scratch/03_architecture.md, option A):
match_policy is deterministic, decide is the single LLM call per row. The
conditional edge skips the LLM entirely when no policy matches the procedure,
so an unmapped procedure returns needs-info instead of a guess.

guardrail_check (the deterministic post-check for the absence-vs-negation
rule) is not wired in yet — that's the next step. Treat outputs as
pre-guardrail for now.
"""
import json
import os
import time
from pathlib import Path
from typing import TypedDict

from anthropic import Anthropic
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from pydantic import ValidationError

from backend.app.models import DeterminationResult, PriorAuthRequest
from backend.app.tools.policy_lookup import PolicyNotFoundError, get_policy_section

load_dotenv()

MODEL = os.getenv("MODEL", "claude-sonnet-5")
API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=API_KEY) if API_KEY else None

KNOWLEDGE_PATH = Path(__file__).resolve().parents[2] / "data" / "knowledge.md"

DETERMINE_TOOL = {
    "name": "submit_determination",
    "description": "Submit the prior authorization determination for this single request.",
    "input_schema": {
        "type": "object",
        "properties": {
            "determination": {"type": "string", "enum": ["approve", "deny", "needs-info"]},
            "policy_id": {"type": "string", "description": "e.g. LMB-114"},
            "criterion": {"type": "string", "description": "the specific numbered criterion(s) that drove the outcome"},
            "reason": {"type": "string", "description": "one or two sentences tying the note's facts to the criterion"},
            "urgent": {"type": "boolean", "description": "true if any cross-cutting urgent/red-flag condition applies"},
        },
        "required": ["determination", "policy_id", "criterion", "reason", "urgent"],
    },
}


def _log_llm_call(label: str, input_text: str, output_text: str, usage: dict, latency_ms: float) -> None:
    """Every model call prints its full input and output -- cost and behavior
    should be visible in the terminal, not just in the final determination."""
    print(f"\n===== LLM CALL: {label} =====")
    print("INPUT:-")
    print(input_text)
    print("OUTPUT:-")
    print(output_text)
    print(f"INPUT TOKENS: {usage['input_tokens']}")
    print(f"OUTPUT TOKENS: {usage['output_tokens']}")
    print(f"LATENCY: {latency_ms:.0f} ms")
    print("=" * (len(label) + 18) + "\n")


class GraphState(TypedDict, total=False):
    request: PriorAuthRequest
    policy_text: str
    result: DeterminationResult
    usage: dict


def match_policy(state: GraphState) -> dict:
    req = state["request"]
    try:
        return {"policy_text": get_policy_section(req.procedure)}
    except PolicyNotFoundError:
        return {
            "result": DeterminationResult(
                request_id=req.request_id, member_id=req.member_id, procedure=req.procedure,
                requesting_provider=req.requesting_provider,
                determination="needs-info",
                reason=f"No on-file policy matches procedure '{req.procedure}'.",
            ),
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }


def _route_after_match(state: GraphState) -> str:
    return "decide" if "policy_text" in state else END


def decide(state: GraphState) -> dict:
    req = state["request"]
    if client is None:
        return {
            "result": DeterminationResult(
                request_id=req.request_id, member_id=req.member_id, procedure=req.procedure,
                requesting_provider=req.requesting_provider,
                determination="needs-info", reason="ANTHROPIC_API_KEY not set; manual review required.",
            ),
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }

    knowledge = KNOWLEDGE_PATH.read_text(encoding="utf-8")
    system = (
        "You are a prior authorization reviewer. Apply the guardrails and policy "
        "below to this single request, then call submit_determination exactly once.\n\n"
        f"## Guardrails\n{knowledge}\n\n## Policy\n{state['policy_text']}"
    )
    user_msg = (
        f"Procedure requested: {req.procedure}\n"
        f"Member age: {req.age}\n"
        f"Clinical note: {req.clinical_note}"
    )

    call_input = f"SYSTEM:\n{system}\n\nUSER:\n{user_msg}"
    label = f"decide request_id={req.request_id} ({req.procedure})"

    start = time.perf_counter()
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
            tools=[DETERMINE_TOOL],
            tool_choice={"type": "tool", "name": "submit_determination"},
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        _log_llm_call(label, call_input, f"<call failed: {e}>", {"input_tokens": 0, "output_tokens": 0}, latency_ms)
        return {
            "result": DeterminationResult(
                request_id=req.request_id, member_id=req.member_id, procedure=req.procedure,
                requesting_provider=req.requesting_provider,
                determination="needs-info", reason="Automated review timed out or failed; manual review required.",
            ),
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }
    latency_ms = (time.perf_counter() - start) * 1000

    usage = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
    tool_use = next((b for b in resp.content if b.type == "tool_use"), None)
    output_text = json.dumps(tool_use.input, indent=2) if tool_use else "<no tool_use block returned>"
    _log_llm_call(label, call_input, output_text, usage, latency_ms)

    if tool_use is None:
        return {
            "result": DeterminationResult(
                request_id=req.request_id, member_id=req.member_id, procedure=req.procedure,
                requesting_provider=req.requesting_provider,
                determination="needs-info", reason="Automated review declined to answer; manual review required.",
            ),
            "usage": usage,
        }

    try:
        result = DeterminationResult(
            request_id=req.request_id, member_id=req.member_id, procedure=req.procedure,
            requesting_provider=req.requesting_provider,
            **tool_use.input,
        )
    except ValidationError:
        result = DeterminationResult(
            request_id=req.request_id, member_id=req.member_id, procedure=req.procedure,
            requesting_provider=req.requesting_provider,
            determination="needs-info", reason="Automated determination could not be parsed; manual review required.",
        )
    return {"result": result, "usage": usage}


_graph = StateGraph(GraphState)
_graph.add_node("match_policy", match_policy)
_graph.add_node("decide", decide)
_graph.set_entry_point("match_policy")
_graph.add_conditional_edges("match_policy", _route_after_match, {"decide": "decide", END: END})
_graph.add_edge("decide", END)
compiled_graph = _graph.compile()


def decide_row(req: PriorAuthRequest) -> tuple[DeterminationResult, dict, float]:
    """Run the graph for one row. Returns (result, usage, latency_ms)."""
    start = time.perf_counter()
    final_state = compiled_graph.invoke({"request": req})
    latency_ms = (time.perf_counter() - start) * 1000
    return final_state["result"], final_state["usage"], latency_ms


def summarize_reason(result: DeterminationResult) -> tuple[str, dict]:
    """
    Second LLM call, used only at letter-generation time: turns the terse
    structured reason into a provider-facing paragraph. Never blocks a
    letter -- on timeout, malformed output, or refusal, it falls back to the
    raw structured reason verbatim (see scratch/03_architecture.md, failure
    plan for summarize_reason).
    """
    if client is None:
        return result.reason, {"input_tokens": 0, "output_tokens": 0}

    prompt = (
        "Write a short, professional paragraph (3-5 sentences) explaining a prior "
        "authorization determination to the requesting provider, for a letter. "
        "Do not invent facts beyond what is given below.\n\n"
        f"Procedure: {result.procedure}\n"
        f"Determination: {result.determination}\n"
        f"Policy: {result.policy_id or 'n/a'}, criterion {result.criterion or 'n/a'}\n"
        f"Internal reasoning: {result.reason}"
    )
    label = f"summarize_reason request_id={result.request_id}"
    start = time.perf_counter()
    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=400, messages=[{"role": "user", "content": prompt}]
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        _log_llm_call(label, prompt, f"<call failed: {e}>", {"input_tokens": 0, "output_tokens": 0}, latency_ms)
        return result.reason, {"input_tokens": 0, "output_tokens": 0}
    latency_ms = (time.perf_counter() - start) * 1000

    usage = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    _log_llm_call(label, prompt, text or "<empty response>", usage, latency_ms)
    return (text or result.reason), usage
