from __future__ import annotations

import unittest

from schemas.models import (
    ClusterAssignment,
    ClusterAssignments,
    DepartmentTask,
    DepartmentTasks,
    NormalizedGoalItem,
    NormalizedGoals,
)
from validators.contracts import ContractValidationError, validate_pipeline_contracts


class TestContracts(unittest.TestCase):
    def _build_valid_data(self) -> tuple[NormalizedGoals, ClusterAssignments, DepartmentTasks]:
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
                    category="CatB",
                    weight=2.0,
                ),
            ]
        )
        clusters = ClusterAssignments(
            clusters=[
                ClusterAssignment(goal_id="GOAL_0001", cluster_id="CLUSTER_01"),
                ClusterAssignment(goal_id="GOAL_0002", cluster_id="CLUSTER_02"),
            ]
        )
        tasks = DepartmentTasks(
            department_tasks=[
                DepartmentTask(
                    cluster_id="CLUSTER_01",
                    department_task_name="Task1",
                    department_general_objective="Gen1",
                    department_challenge_objective="Cha1",
                    representative_category="CatA",
                    owner_candidate="Alice",
                ),
                DepartmentTask(
                    cluster_id="CLUSTER_02",
                    department_task_name="Task2",
                    department_general_objective="Gen2",
                    department_challenge_objective="Cha2",
                    representative_category="CatB",
                    owner_candidate="Bob",
                ),
            ]
        )
        return normalized, clusters, tasks

    def test_valid_contracts(self) -> None:
        normalized, clusters, tasks = self._build_valid_data()
        validate_pipeline_contracts(normalized, clusters, tasks)

    def test_duplicate_cluster_goal_raises(self) -> None:
        normalized, clusters, tasks = self._build_valid_data()
        clusters.clusters.append(ClusterAssignment(goal_id="GOAL_0001", cluster_id="CLUSTER_99"))
        with self.assertRaises(ContractValidationError):
            validate_pipeline_contracts(normalized, clusters, tasks)

    def test_invalid_owner_candidate_raises(self) -> None:
        normalized, clusters, tasks = self._build_valid_data()
        tasks.department_tasks[0].owner_candidate = "Charlie"
        with self.assertRaises(ContractValidationError):
            validate_pipeline_contracts(normalized, clusters, tasks)


if __name__ == "__main__":
    unittest.main()
