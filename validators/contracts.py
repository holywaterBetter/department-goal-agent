from __future__ import annotations

from collections import Counter, defaultdict

from schemas.models import ClusterAssignments, DepartmentTasks, NormalizedGoals


class ContractValidationError(ValueError):
    """Raised when cross-stage data contracts are broken."""


def validate_pipeline_contracts(
    normalized_goals: NormalizedGoals,
    clusters: ClusterAssignments,
    department_tasks: DepartmentTasks,
) -> None:
    normalized_goal_ids = [item.goal_id for item in normalized_goals.items]
    cluster_goal_ids = [item.goal_id for item in clusters.clusters]

    _validate_cluster_goal_id_uniqueness(cluster_goal_ids)
    _validate_cluster_goal_coverage(normalized_goal_ids, cluster_goal_ids)

    cluster_to_employees: dict[str, set[str]] = defaultdict(set)
    goal_to_employee = {item.goal_id: item.employee for item in normalized_goals.items}
    for assignment in clusters.clusters:
        employee = goal_to_employee.get(assignment.goal_id)
        if employee is not None:
            cluster_to_employees[assignment.cluster_id].add(employee)

    assignment_cluster_ids = {item.cluster_id for item in clusters.clusters}
    task_cluster_ids = [task.cluster_id for task in department_tasks.department_tasks]

    _validate_department_cluster_references(assignment_cluster_ids, task_cluster_ids)
    _validate_one_task_per_cluster(assignment_cluster_ids, task_cluster_ids)
    _validate_owner_candidates(department_tasks, cluster_to_employees)


def _validate_cluster_goal_id_uniqueness(cluster_goal_ids: list[str]) -> None:
    duplicated = sorted(goal_id for goal_id, count in Counter(cluster_goal_ids).items() if count > 1)
    if duplicated:
        raise ContractValidationError(
            "Duplicate goal_id values found in cluster assignments: " + ", ".join(duplicated)
        )


def _validate_cluster_goal_coverage(normalized_goal_ids: list[str], cluster_goal_ids: list[str]) -> None:
    normalized_set = set(normalized_goal_ids)
    cluster_set = set(cluster_goal_ids)

    missing = sorted(normalized_set - cluster_set)
    extra = sorted(cluster_set - normalized_set)

    if missing or extra:
        details: list[str] = []
        if missing:
            details.append("missing goal_ids in clusters: " + ", ".join(missing))
        if extra:
            details.append("unknown goal_ids in clusters: " + ", ".join(extra))
        raise ContractValidationError("Cluster coverage mismatch: " + " | ".join(details))


def _validate_department_cluster_references(assignment_cluster_ids: set[str], task_cluster_ids: list[str]) -> None:
    unknown = sorted(set(task_cluster_ids) - assignment_cluster_ids)
    if unknown:
        raise ContractValidationError(
            "Department tasks reference unknown cluster_id values: " + ", ".join(unknown)
        )


def _validate_one_task_per_cluster(assignment_cluster_ids: set[str], task_cluster_ids: list[str]) -> None:
    counts = Counter(task_cluster_ids)
    missing_tasks = sorted(cluster_id for cluster_id in assignment_cluster_ids if counts.get(cluster_id, 0) == 0)
    duplicated_tasks = sorted(cluster_id for cluster_id, count in counts.items() if count > 1)

    if missing_tasks or duplicated_tasks:
        details: list[str] = []
        if missing_tasks:
            details.append("clusters missing task: " + ", ".join(missing_tasks))
        if duplicated_tasks:
            details.append("clusters with duplicate tasks: " + ", ".join(duplicated_tasks))
        raise ContractValidationError("Department task cardinality mismatch: " + " | ".join(details))


def _validate_owner_candidates(
    department_tasks: DepartmentTasks,
    cluster_to_employees: dict[str, set[str]],
) -> None:
    invalid: list[str] = []
    for task in department_tasks.department_tasks:
        allowed = cluster_to_employees.get(task.cluster_id, set())
        if task.owner_candidate not in allowed:
            allowed_list = ", ".join(sorted(allowed)) if allowed else "<none>"
            invalid.append(
                f"{task.cluster_id} owner_candidate={task.owner_candidate} not in cluster employees ({allowed_list})"
            )

    if invalid:
        raise ContractValidationError("Invalid owner candidates: " + " | ".join(invalid))
