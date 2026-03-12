# Department Goal Agent

직원 목표 데이터를 LLM 기반 멀티 에이전트 파이프라인으로 정규화/군집화하여 부서업무로 변환하는 프로젝트입니다.

## Features

- **GoalNormalizerAgent**: 자유형식 개인 목표 텍스트를 정규화
- **ClusterAgent**: 유사 목표를 부서 workstream 단위로 군집화
- **DepartmentTaskAgent**: 군집별 부서업무/목표/주관 후보 생성
- **Contract Validation**: 단계 간 데이터 정합성 검증
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
validators/
    contracts.py
utils/
    json_utils.py
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

CSV는 `utf-8-sig`로 로딩하며, 헤더 BOM(`\ufeff`)이 있어도 자동 정규화합니다.

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

## Validation Behavior

파이프라인은 Aggregator 실행 전 단계 간 계약을 검증합니다.

- normalized_goals의 모든 `goal_id`는 clusters에 정확히 1회 등장해야 함
- clusters에 중복 `goal_id`가 있으면 실패
- department_tasks의 `cluster_id`는 clusters에 존재해야 함
- clusters의 모든 `cluster_id`는 department_tasks에 정확히 1개 task를 가져야 함
- `owner_candidate`는 해당 cluster에 소속된 employee 중 하나여야 함

또한 Aggregator는 goal 누락 여부를 다시 확인하여 데이터 손실을 방지합니다.

## LLM Retry Behavior

`LLMClient.generate()`는 다음 상황에서 재시도합니다.

- 네트워크 연결 실패 (`ConnectionError`)
- 요청 타임아웃 (`Timeout`)
- HTTP 429 또는 HTTP 5xx

재시도는 지수 백오프(1s, 2s, 4s ...)를 사용하며, 최대 시도 횟수 초과 시 명확한 오류를 발생시킵니다.

## Expected Failure Modes

다음 경우 파이프라인은 stage context와 함께 즉시 실패합니다.

- 입력 CSV 누락/헤더 불일치/행 데이터 타입 오류
- LLM 환경변수 누락 또는 잘못된 timeout 값
- LLM 응답이 JSON이 아니거나 스키마 불일치
- 단계 간 계약 위반(누락 goal, 잘못된 owner_candidate 등)
- 출력 파일 쓰기 실패

## Notes

- Aggregator는 LLM 호출 없이 Python/pandas만 사용합니다.
- LLM 응답은 공통 JSON 파서 + Pydantic 스키마 검증으로 처리합니다.
