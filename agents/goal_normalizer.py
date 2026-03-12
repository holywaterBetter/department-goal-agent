from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from schemas.models import GoalInput, NormalizedGoals
from services.llm_client import LLMClient
from utils.json_utils import parse_json_response


class GoalNormalizerAgent:
    def __init__(self, llm_client: LLMClient, prompt_path: str = "prompts/normalize_prompt.txt") -> None:
        self.llm_client = llm_client
        self.prompt_template = self._load_prompt(prompt_path)

    def run(self, goals: Iterable[GoalInput], output_path: str) -> NormalizedGoals:
        goal_payload = [goal.model_dump() for goal in goals]
        prompt = self.prompt_template.format(goals_json=json.dumps(goal_payload, ensure_ascii=False, indent=2))
        response_text = self.llm_client.generate(prompt)
        parsed = parse_json_response(response_text, context="GoalNormalizerAgent")
        result = NormalizedGoals.model_validate(parsed)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            output_file.write_text(result.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            raise OSError(f"GoalNormalizerAgent failed to write output file: {output_file}") from exc
        return result

    @staticmethod
    def _load_prompt(prompt_path: str) -> str:
        path = Path(prompt_path)
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise OSError(f"GoalNormalizerAgent failed to read prompt file: {path}") from exc
