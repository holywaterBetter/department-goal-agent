from __future__ import annotations

from pathlib import Path

from schemas.models import ClusterAssignments, DepartmentTasks, NormalizedGoals
from services.llm_client import LLMClient
from utils.json_utils import parse_json_response


class DepartmentTaskAgent:
    def __init__(self, llm_client: LLMClient, prompt_path: str = "prompts/department_prompt.txt") -> None:
        self.llm_client = llm_client
        self.prompt_template = self._load_prompt(prompt_path)

    def run(
        self,
        normalized_goals: NormalizedGoals,
        clusters: ClusterAssignments,
        output_path: str,
    ) -> DepartmentTasks:
        prompt = self.prompt_template.format(
            normalized_goals_json=normalized_goals.model_dump_json(indent=2, ensure_ascii=False),
            clusters_json=clusters.model_dump_json(indent=2, ensure_ascii=False),
        )
        response_text = self.llm_client.generate(prompt)
        parsed = parse_json_response(response_text, context="DepartmentTaskAgent")
        result = DepartmentTasks.model_validate(parsed)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            output_file.write_text(result.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            raise OSError(f"DepartmentTaskAgent failed to write output file: {output_file}") from exc
        return result

    @staticmethod
    def _load_prompt(prompt_path: str) -> str:
        path = Path(prompt_path)
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise OSError(f"DepartmentTaskAgent failed to read prompt file: {path}") from exc
