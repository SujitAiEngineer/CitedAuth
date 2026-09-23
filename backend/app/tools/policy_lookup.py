"""
Parses policy_criteria.md into per-procedure sections once, so the prompt
builder never re-parses markdown and the decide node can fail loudly on an
unmapped procedure instead of guessing.
"""
import re
from functools import lru_cache
from pathlib import Path

POLICY_PATH = Path(__file__).resolve().parents[2] / "data" / "policy_criteria.md"


class PolicyNotFoundError(Exception):
    """Raised when a request's procedure doesn't match any on-file policy."""


@lru_cache(maxsize=1)
def _load_sections() -> dict[str, str]:
    text = POLICY_PATH.read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    for block in re.split(r"\n## ", text)[1:]:
        header, _, body = block.partition("\n")
        if ":" not in header:
            continue  # skips non-policy sections like "Cross-cutting rules"
        policy_id, _, title = header.partition(":")
        policy_id, title = policy_id.strip(), title.strip()
        body = body.split("\n---", 1)[0].strip()
        sections[title.lower()] = f"## {policy_id}: {title}\n\n{body}"
    return sections


def get_policy_section(procedure: str) -> str:
    """Return the full policy section text matching a request's procedure field."""
    sections = _load_sections()
    key = procedure.strip().lower()
    if key in sections:
        return sections[key]
    for title, text in sections.items():
        if key in title or title in key:
            return text
    raise PolicyNotFoundError(procedure)
