from __future__ import annotations

import json
from json import JSONDecodeError


class LLMResponseParseError(ValueError):
    """Raised when an LLM response cannot be parsed as JSON."""


def parse_json_response(response_text: str, context: str) -> dict:
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
    except JSONDecodeError as exc:
        raise LLMResponseParseError(
            f"[{context}] Could not parse JSON response. Raw response: {response_text}"
        ) from exc

    if not isinstance(parsed, dict):
        raise LLMResponseParseError(f"[{context}] JSON response root must be an object.")
    return parsed
