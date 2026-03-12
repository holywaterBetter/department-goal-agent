from __future__ import annotations

from pathlib import Path

import pandas as pd

from schemas.models import ClusterAssignments, DepartmentTasks, NormalizedGoals


class Aggregator:
    @staticmethod
    def aggregate(
        normalized_goals: NormalizedGoals,
        clusters: ClusterAssignments,
        department_tasks: DepartmentTasks,
        output_path: str,
    ) -> pd.DataFrame:
        goals_df = pd.DataFrame([item.model_dump() for item in normalized_goals.items])
        clusters_df = pd.DataFrame([item.model_dump() for item in clusters.clusters])
        tasks_df = pd.DataFrame([item.model_dump() for item in department_tasks.department_tasks])

        if goals_df.empty:
            raise ValueError("Aggregator received no normalized goals.")

        goal_ids = set(goals_df["goal_id"].tolist())
        cluster_goal_ids = set(clusters_df["goal_id"].tolist())
        missing_goal_ids = sorted(goal_ids - cluster_goal_ids)
        if missing_goal_ids:
            raise ValueError(
                "Aggregator found goals without cluster assignments: " + ", ".join(missing_goal_ids)
            )

        merged = goals_df.merge(clusters_df, on="goal_id", how="left", validate="one_to_one")
        if merged["cluster_id"].isna().any():
            missing_after_merge = merged.loc[merged["cluster_id"].isna(), "goal_id"].tolist()
            raise ValueError(
                "Aggregator merge produced unassigned goals: " + ", ".join(sorted(missing_after_merge))
            )

        merged_rows = len(merged)
        if merged_rows != len(goals_df):
            raise ValueError(
                f"Aggregator row mismatch: expected {len(goals_df)} rows from goals, got {merged_rows}"
            )

        cluster_stats = (
            merged.groupby("cluster_id", as_index=False)
            .agg(
                **{
                    "연결 개인목표 수": ("goal_id", "count"),
                    "가중치합": ("weight", "sum"),
                }
            )
            .sort_values("cluster_id")
        )

        total_weight = float(cluster_stats["가중치합"].sum())
        if total_weight == 0:
            cluster_stats["가중치합 비중"] = 0.0
        else:
            cluster_stats["가중치합 비중"] = cluster_stats["가중치합"] / total_weight

        employee_pivot = (
            merged.pivot_table(
                index="cluster_id",
                columns="employee",
                values="weight",
                aggfunc="sum",
                fill_value=0.0,
            )
            .reset_index()
            .rename_axis(None, axis=1)
        )

        final_df = (
            tasks_df.merge(cluster_stats, on="cluster_id", how="left", validate="one_to_one")
            .merge(employee_pivot, on="cluster_id", how="left", validate="one_to_one")
            .sort_values("cluster_id")
            .reset_index(drop=True)
        )

        required_task_columns = {
            "representative_category",
            "department_task_name",
            "department_general_objective",
            "department_challenge_objective",
            "owner_candidate",
        }
        missing_task_columns = sorted(required_task_columns - set(final_df.columns))
        if missing_task_columns:
            raise ValueError("Aggregator missing required department task columns: " + ", ".join(missing_task_columns))

        final_df.insert(0, "no", final_df.index + 1)
        final_df = final_df.rename(
            columns={
                "representative_category": "카테고리",
                "department_task_name": "부서업무명",
                "department_general_objective": "부서업무일반목표",
                "department_challenge_objective": "부서업무도전목표",
                "owner_candidate": "주관",
            }
        )

        employee_columns = sorted(merged["employee"].unique().tolist())
        ordered_columns = [
            "no",
            "카테고리",
            "부서업무명",
            "부서업무일반목표",
            "부서업무도전목표",
            "연결 개인목표 수",
            "가중치합",
            "가중치합 비중",
            *employee_columns,
            "주관",
        ]

        for col in employee_columns:
            if col not in final_df.columns:
                final_df[col] = 0.0

        missing_final_columns = [col for col in ordered_columns if col not in final_df.columns]
        if missing_final_columns:
            raise ValueError(
                "Aggregator missing required final output columns: " + ", ".join(missing_final_columns)
            )

        final_df = final_df[ordered_columns]
        final_df["가중치합"] = final_df["가중치합"].round(4)
        final_df["가중치합 비중"] = final_df["가중치합 비중"].round(4)
        for col in employee_columns:
            final_df[col] = final_df[col].round(4)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            final_df.to_csv(output_file, index=False, encoding="utf-8-sig")
        except OSError as exc:
            raise OSError(f"Aggregator failed to write output CSV: {output_file}") from exc

        return final_df
