# Repository Quick Guide (2025-10-01)
codex resume 01999fc7-4004-7500-8186-bb3ccf0a5390.
## Current Focus – QueryGoal End-to-End Runtime
- Natural language → QueryGoal 변환은 `querygoal/pipeline/` 모듈이 담당합니다.
  - `orchestrator.py`가 엔트리포인트이며, 하위 컴포넌트는 `pattern_matcher.py`, `template_loader.py`, `parameter_filler.py`, `model_selector.py`, `validator.py` 순으로 동작합니다.
  - Goal3 모델 선택 시 `config/model_registry.json`과 `config/NSGA2Model_sources.yaml`을 사용합니다.
- 런타임 실행은 `querygoal/runtime/` 이하 Stage-Gate 구조로 구현되어 있습니다.
  - `executor.py` → `handlers/swrl_selection_handler.py` → `handlers/yaml_binding_handler.py` → `handlers/simulation_handler.py` 순으로 호출됩니다.
  - `config/NSGA2Model_sources.yaml`은 런타임 전용 `data_sources` + 레거시 `sources`를 함께 가진 하이브리드 manifest입니다.
  - AAS 연동은 `clients/aas_client.py`(httpx 기반), 시뮬레이션은 `clients/container_client.py`(docker run)에서 처리합니다.
- 실제 실행 산출물은 `temp/runtime_executions/<goalId_timestamp>/` 아래에 생성됩니다.
  - 예) `goal3_test_024717_20251001_174717` 내부: yamlBinding JSON, `my_case/` 시나리오, `results/simulator_optimization_result.json`, 컨테이너 로그 등.

## Project Structure (유지 중인 주요 경로)
- `api/` – FastAPI 메인 서비스 (`main.py`, `schemas.py`).
- `config/` – manifest, 모델 레지스트리, 온톨로지, SPARQL 규칙.
- `execution_engine/` – SWRL SelectionEngine 및 에이전트 로직.
- `querygoal/` – Pipeline + Runtime (현재 핵심 작업 영역).
- `tests/` – 공용 pytest 자산. 루트에 있는 다수의 테스트 스크립트는 디버그/실험용입니다 (공식 시나리오: `test_goal1.py`, `test_goal3.py`, `test_goal4.py`).
- `temp/runtime_executions/` – 최근 실행 결과(성공/실패 모두) 로그 저장소.

## Build & Run
```bash
pip install -r requirements.txt
export USE_STANDARD_SERVER=true        # AAS 표준 서버 사용 시
export AAS_SERVER_IP=127.0.0.1
export AAS_SERVER_PORT=5001

# FastAPI 서버
uvicorn api.main:app --reload --port 8000

# Goal3 파이프라인+런타임 실행 예시
python - <<'PY'
import asyncio
from querygoal.pipeline.orchestrator import PipelineOrchestrator
from querygoal.runtime.executor import QueryGoalExecutor

async def main():
    orch = PipelineOrchestrator()
    qg = orch.process_natural_language(
        "Predict production time for product TEST quantity 5"
    )
    executor = QueryGoalExecutor()
    result = await executor.execute_querygoal(qg)
    print(result["executionLog"]["status"], result["workDirectory"])

asyncio.run(main())
PY
```

## Runtime 성공 체크 리스트
1. `http://<AAS_SERVER_IP>:<PORT>/shells` 요청이 200을 반환하는지 확인.
2. `config/NSGA2Model_sources.yaml`의 URN/idShort가 AAS 데이터와 일치하는지 검증.
3. Docker 이미지 `factory-nsga2:latest`가 로컬에 존재하는지 확인 (`docker images`).
4. 실행 후 `temp/runtime_executions/<goal>/results/`에 `simulator_optimization_result.json`, `job_info.csv`, `operation_info.csv`가 생성됐는지 확인.
5. 실패 시 `failure.log`와 `container_logs_*.txt`에서 StageGate 이유 및 컨테이너 로그 확인.

## Coding & Contribution Tips
- PEP 8, 타입 힌트 권장. 복잡한 Stage 로직은 간결한 주석으로 문서화.
- Manifest/JSON/YAML 포맷은 자동화 의존도가 높으므로 수동 수정 시 `data_sources`와 `sources`가 동기화되었는지 두 번 확인.
- 새 테스트는 `tests/` 구조를 재사용하거나, 루트 테스트 스크립트를 최소화합니다.
- 커밋 메시지는 `[영역] 동사형` 형식을 유지하고, PR에는 문제/해결/테스트 요약을 포함합니다.

## 참고 문서
- `docs/Goal3_E2E_Complete_Flow.md` – Goal3 엔드투엔드 플로우(실행 결과 기반).
- `docs/Runtime_Executor_Flow.md` – 런타임 Stage-Gate 설계 개요.
- `docs/QueryGoal_Runtime_Executor_Implementation_Plan.md` – 구현 계획 및 세부 내역.

추가 질문이나 환경 이슈는 이 파일을 최신으로 유지하면서 주석/이슈에 공유해 주세요.
