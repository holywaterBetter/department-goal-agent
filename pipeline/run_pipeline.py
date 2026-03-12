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


def load_goals(csv_path: str) -> list[GoalInput]:
    df = pd.read_csv(csv_path)
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
    return goals


def main() -> None:
    input_csv = "data/input/goals.csv"
    normalized_path = "data/intermediate/normalized_goals.json"
    cluster_path = "data/intermediate/clusters.json"
    department_path = "data/intermediate/department_tasks.json"
    output_csv = "data/output/department_work.csv"

    goals = load_goals(input_csv)

    llm_client = LLMClient.from_env()

    normalizer = GoalNormalizerAgent(llm_client=llm_client)
    cluster_agent = ClusterAgent(llm_client=llm_client)
    department_agent = DepartmentTaskAgent(llm_client=llm_client)

    normalized = normalizer.run(goals=goals, output_path=normalized_path)
    clusters = cluster_agent.run(normalized_goals=normalized, output_path=cluster_path)
    department_tasks = department_agent.run(
        normalized_goals=normalized,
        clusters=clusters,
        output_path=department_path,
    )

    Aggregator.aggregate(
        normalized_goals=normalized,
        clusters=clusters,
        department_tasks=department_tasks,
        output_path=output_csv,
    )

    print("Pipeline completed successfully.")
    print(f"- {normalized_path}")
    print(f"- {cluster_path}")
    print(f"- {department_path}")
    print(f"- {output_csv}")


if __name__ == "__main__":
    main()
