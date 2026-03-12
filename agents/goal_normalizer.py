from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from schemas.models import GoalInput, NormalizedGoals
from services.llm_client import LLMClient


class GoalNormalizerAgent:
    def __init__(self, llm_client: LLMClient, prompt_path: str = "prompts/normalize_prompt.txt") -> None:
        self.llm_client = llm_client
        self.prompt_template = Path(prompt_path).read_text(encoding="utf-8")

    def run(self, goals: Iterable[GoalInput], output_path: str) -> NormalizedGoals:
        goal_payload = [goal.model_dump() for goal in goals]
        prompt = self.prompt_template.format(goals_json=json.dumps(goal_payload, ensure_ascii=False, indent=2))
        response_text = self.llm_client.generate(prompt)
        parsed = self._parse_json_response(response_text)
        result = NormalizedGoals.model_validate(parsed)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(result.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
        return result

    @staticmethod
    def _parse_json_response(response_text: str) -> dict:
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Could not parse GoalNormalizerAgent JSON response: {response_text}") from exc
