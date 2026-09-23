"""
Shared request/response shapes. Kept separate from main.py so tools and graph
nodes can import them without importing the FastAPI app.
"""
from typing import Literal, Optional

from pydantic import BaseModel


class PriorAuthRequest(BaseModel):
    request_id: int
    member_id: str
    age: int
    procedure: str
    clinical_note: str
    requesting_provider: str


class DeterminationResult(BaseModel):
    request_id: int
    member_id: str
    procedure: str
    requesting_provider: str
    determination: Literal["approve", "deny", "needs-info"]
    policy_id: Optional[str] = None
    criterion: Optional[str] = None
    reason: str
    urgent: bool = False


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int


class AnalyzeResponse(BaseModel):
    results: list[DeterminationResult]
    usage: TokenUsage
    latency_ms: float
