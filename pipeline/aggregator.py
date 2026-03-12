from __future__ import annotations

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

        merged = goals_df.merge(clusters_df, on="goal_id", how="inner")

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
            tasks_df.merge(cluster_stats, on="cluster_id", how="left")
            .merge(employee_pivot, on="cluster_id", how="left")
            .sort_values("cluster_id")
            .reset_index(drop=True)
        )

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

        final_df = final_df[ordered_columns]
        final_df["가중치합"] = final_df["가중치합"].round(4)
        final_df["가중치합 비중"] = final_df["가중치합 비중"].round(4)
        for col in employee_columns:
            final_df[col] = final_df[col].round(4)

        final_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return final_df
