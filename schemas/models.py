from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, PositiveInt


class GoalInput(BaseModel):
    goal_id: str
    employee: str
    goal_title: str
    general_goal: str
    challenge_goal: str
    category: str
    weight: float


class NormalizedGoalItem(BaseModel):
    goal_id: str
    employee: str
    normalized_goal: str
    keywords: List[str] = Field(default_factory=list)
    category: str
    weight: float


class NormalizedGoals(BaseModel):
    items: List[NormalizedGoalItem]


class ClusterAssignment(BaseModel):
    goal_id: str
    cluster_id: str


class ClusterAssignments(BaseModel):
    clusters: List[ClusterAssignment]


class DepartmentTask(BaseModel):
    cluster_id: str
    department_task_name: str
    department_general_objective: str
    department_challenge_objective: str
    representative_category: str
    owner_candidate: str


class DepartmentTasks(BaseModel):
    department_tasks: List[DepartmentTask]


class DepartmentWorkRow(BaseModel):
    no: PositiveInt
    카테고리: str
    부서업무명: str
    부서업무일반목표: str
    부서업무도전목표: str
    연결_개인목표_수: int
    가중치합: float
    가중치합_비중: float
    주관: str
