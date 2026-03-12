from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.cluster_agent import ClusterAgent
from agents.department_task_agent import DepartmentTaskAgent
from agents.goal_normalizer import GoalNormalizerAgent
from pipeline.aggregator import Aggregator
from schemas.models import GoalInput
from services.llm_client import LLMClient
from validators.contracts import validate_pipeline_contracts


class PipelineStageError(RuntimeError):
    """Raised when a pipeline stage fails with additional context."""


def load_goals(csv_path: str) -> list[GoalInput]:
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Input CSV not found: {csv_path}") from exc
    except OSError as exc:
        raise OSError(f"Failed to read input CSV: {csv_path}") from exc

    df.columns = [str(col).strip().lstrip("\ufeff") for col in df.columns]

    expected_cols = [
        "employee",
        "goal_title",
        "general_goal",
        "challenge_goal",
        "category",
        "weight",
    ]
    missing = [col for col in expected_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in goals.csv: {missing}")

    goals: list[GoalInput] = []
    for idx, row in df.iterrows():
        try:
            goals.append(
                GoalInput(
                    goal_id=f"GOAL_{idx + 1:04d}",
                    employee=str(row["employee"]).strip(),
                    goal_title=str(row["goal_title"]).strip(),
                    general_goal=str(row["general_goal"]).strip(),
                    challenge_goal=str(row["challenge_goal"]).strip(),
                    category=str(row["category"]).strip(),
                    weight=float(row["weight"]),
                )
            )
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid row at index {idx} in goals CSV: {exc}") from exc

    return goals


def main() -> None:
    input_csv = "data/input/goals.csv"
    normalized_path = "data/intermediate/normalized_goals.json"
    cluster_path = "data/intermediate/clusters.json"
    department_path = "data/intermediate/department_tasks.json"
    output_csv = "data/output/department_work.csv"

    try:
        goals = load_goals(input_csv)
    except Exception as exc:  # noqa: BLE001
        raise PipelineStageError(f"[Load CSV] Failed to load goals from {input_csv}: {exc}") from exc

    try:
        llm_client = LLMClient.from_env()
    except Exception as exc:  # noqa: BLE001
        raise PipelineStageError(f"[LLM Init] Failed to initialize LLM client: {exc}") from exc

    normalizer = GoalNormalizerAgent(llm_client=llm_client)
    cluster_agent = ClusterAgent(llm_client=llm_client)
    department_agent = DepartmentTaskAgent(llm_client=llm_client)

    try:
        normalized = normalizer.run(goals=goals, output_path=normalized_path)
    except Exception as exc:  # noqa: BLE001
        raise PipelineStageError(f"[GoalNormalizerAgent] Failed: {exc}") from exc

    try:
        clusters = cluster_agent.run(normalized_goals=normalized, output_path=cluster_path)
    except Exception as exc:  # noqa: BLE001
        raise PipelineStageError(f"[ClusterAgent] Failed: {exc}") from exc

    try:
        department_tasks = department_agent.run(
            normalized_goals=normalized,
            clusters=clusters,
            output_path=department_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise PipelineStageError(f"[DepartmentTaskAgent] Failed: {exc}") from exc

    try:
        validate_pipeline_contracts(
            normalized_goals=normalized,
            clusters=clusters,
            department_tasks=department_tasks,
        )
    except Exception as exc:  # noqa: BLE001
        raise PipelineStageError(f"[Contract Validation] Failed: {exc}") from exc

    try:
        Aggregator.aggregate(
            normalized_goals=normalized,
            clusters=clusters,
            department_tasks=department_tasks,
            output_path=output_csv,
        )
    except Exception as exc:  # noqa: BLE001
        raise PipelineStageError(f"[Aggregator] Failed: {exc}") from exc

    print("Pipeline completed successfully.")
    print(f"- {normalized_path}")
    print(f"- {cluster_path}")
    print(f"- {department_path}")
    print(f"- {output_csv}")


if __name__ == "__main__":
    main()
