from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.aggregator import Aggregator
from schemas.models import (
    ClusterAssignment,
    ClusterAssignments,
    DepartmentTask,
    DepartmentTasks,
    NormalizedGoalItem,
    NormalizedGoals,
)


class TestAggregator(unittest.TestCase):
    def test_output_columns_include_dynamic_employee(self) -> None:
        normalized = NormalizedGoals(
            items=[
                NormalizedGoalItem(
                    goal_id="GOAL_0001",
                    employee="Alice",
                    normalized_goal="Goal A",
                    keywords=["a"],
                    category="CatA",
                    weight=1.0,
                ),
                NormalizedGoalItem(
                    goal_id="GOAL_0002",
                    employee="Bob",
                    normalized_goal="Goal B",
                    keywords=["b"],
                    category="CatA",
                    weight=3.0,
                ),
            ]
        )
        clusters = ClusterAssignments(
            clusters=[
                ClusterAssignment(goal_id="GOAL_0001", cluster_id="CLUSTER_01"),
                ClusterAssignment(goal_id="GOAL_0002", cluster_id="CLUSTER_01"),
            ]
        )
        department_tasks = DepartmentTasks(
            department_tasks=[
                DepartmentTask(
                    cluster_id="CLUSTER_01",
                    department_task_name="Task",
                    department_general_objective="Gen",
                    department_challenge_objective="Cha",
                    representative_category="CatA",
                    owner_candidate="Alice",
                )
            ]
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "department_work.csv"
            df = Aggregator.aggregate(normalized, clusters, department_tasks, str(output_path))

            expected_prefix = [
                "no",
                "카테고리",
                "부서업무명",
                "부서업무일반목표",
                "부서업무도전목표",
                "연결 개인목표 수",
                "가중치합",
                "가중치합 비중",
            ]
            self.assertEqual(df.columns[:8].tolist(), expected_prefix)
            self.assertIn("Alice", df.columns)
            self.assertIn("Bob", df.columns)
            self.assertEqual(df.iloc[0]["연결 개인목표 수"], 2)
            self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()
