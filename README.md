# Department Goal Agent

직원 목표 데이터를 LLM 기반 멀티 에이전트 파이프라인으로 정규화/군집화하여 부서업무로 변환하는 프로젝트입니다.

## Features

- **GoalNormalizerAgent**: 자유형식 개인 목표 텍스트를 정규화
- **ClusterAgent**: 유사 목표를 부서 workstream 단위로 군집화
- **DepartmentTaskAgent**: 군집별 부서업무/목표/주관 후보 생성
- **Aggregator (pure Python)**: 통계 집계 및 최종 CSV 생성

## Project Structure

```text
agents/
    goal_normalizer.py
    cluster_agent.py
    department_task_agent.py
pipeline/
    aggregator.py
    run_pipeline.py
services/
    llm_client.py
prompts/
    normalize_prompt.txt
    cluster_prompt.txt
    department_prompt.txt
schemas/
    models.py
data/
    input/
    intermediate/
    output/
.env.example
requirements.txt
README.md
```

## Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env`에 사내 LLM API 정보를 입력하세요.

```env
LLM_API_BASE_URL=
LLM_API_KEY=
LLM_MODEL_NAME=
LLM_TIMEOUT=
```

## Input

- `data/input/goals.csv`
- required columns:
  - `employee`
  - `goal_title`
  - `general_goal`
  - `challenge_goal`
  - `category`
  - `weight`

## Run

```bash
python pipeline/run_pipeline.py
```

## Pipeline Output

1. `data/intermediate/normalized_goals.json`
2. `data/intermediate/clusters.json`
3. `data/intermediate/department_tasks.json`
4. `data/output/department_work.csv`

최종 CSV 컬럼은 아래 순서로 생성됩니다.

- `no`
- `카테고리`
- `부서업무명`
- `부서업무일반목표`
- `부서업무도전목표`
- `연결 개인목표 수`
- `가중치합`
- `가중치합 비중`
- `(동적 employee 컬럼들)`
- `주관`

## Notes

- Aggregator는 LLM 호출 없이 Python/pandas만 사용합니다.
- LLM 응답은 JSON 스키마 검증(Pydantic)을 통해 안전하게 파싱합니다.
