# Factory Automation with QueryGoal System

**현대화된 스마트 팩토리 자동화 시스템**: AAS (Asset Administration Shell) 통합, QueryGoal 파이프라인, NSGA-II 기반 시뮬레이션

## 시스템 개요

본 프로젝트는 두 가지 주요 실행 모드를 제공합니다:

1. **QueryGoal Pipeline/Runtime** (Goal 3) - 자연어 → 실행 가능한 쿼리 → 시뮬레이션 결과
2. **Legacy Goal Execution** (Goal 1, 4) - 기존 온톨로지 기반 실행 엔진

> 📖 **작동 방식 상세**: QueryGoal의 E2E 흐름에 대한 자세한 설명은 [Goal3 E2E Flow Plan](docs/Goal3_E2E_Flow_Plan_Corrected.md)을 참조하세요.

## 시스템 요구사항

- **Python 3.8+** - 로컬 개발 및 테스트
- **Docker** - NSGA-II 시뮬레이션 컨테이너 실행
- **AAS Server** (선택적) - 표준 AAS 서버 (`localhost:5001`) 또는 로컬 시뮬레이션 모드

## 빠른 시작

### 1. 환경 설정
```bash
# 의존성 설치
pip install -r requirements.txt

# (선택) Docker 이미지 빌드 (Goal 3 시뮬레이션용)
cd scripts
./build_nsga2_docker.sh
```

### 2. API 서버 실행
```bash
# 로컬 시뮬레이션 모드 (AAS 서버 불필요)
export USE_STANDARD_SERVER=true
export AAS_SERVER_IP=127.0.0.1
export AAS_SERVER_PORT=5001
export FORCE_LOCAL_MODE=true
uvicorn api.main:app --reload --port 8000

# 또는 표준 AAS 서버 연동 모드
export USE_STANDARD_SERVER=true
export AAS_SERVER_IP=221.139.184.184
export AAS_SERVER_PORT=5001
uvicorn api.main:app --reload --port 8000
```

### 3. 시스템 테스트
```bash
# Goal 3: QueryGoal E2E 테스트 (Pipeline → Runtime → Simulation)
python test_runtime_executor.py

# Goal 1: 냉각 작업 실패 쿼리 (Legacy)
python test_goal1.py

# Goal 4: 제품 위치 추적 (Legacy)
python test_goal4.py
```

## 주요 기능

| Goal | 설명 | 상태 | 테스트 명령어 | 실행 방식 |
|------|------|------|--------------|-----------|
| **Goal 3** | **생산 시간 예측** | ✅ **완전 구현** | `python test_runtime_executor.py` | **QueryGoal Pipeline/Runtime** |
| Goal 1 | 냉각 작업 실패 쿼리 | ✅ 작동 | `python test_goal1.py` | Legacy Ontology |
| Goal 4 | 제품 위치 추적 | ✅ 작동 | `python test_goal4.py` | Legacy Ontology |
| Goal 2 | 이상 감지 | ⏳ ML 모델 필요 | - | Legacy Ontology |

### Goal 3: QueryGoal 시스템 특징

**자연어 입력 → 실행 결과 완전 자동화**

```
입력: "Predict production time for product TEST_RUNTIME quantity 30"
    ↓
Pipeline (6 stages): Pattern Matching → Template Loading → Parameter Filling
                     → ActionPlan Resolution → Model Selection → Validation
    ↓
QueryGoal JSON (완전한 실행 명세)
    ↓
Runtime (3 stages): swrlSelection → yamlBinding → simulation
    ↓
출력: estimatedTime, confidence, productionPlan, bottlenecks
```

**핵심 특징**:
- ✅ SPARQL 기반 모델 선택 (SelectionEngine)
- ✅ Stage-Gate 패턴 검증
- ✅ Docker 기반 NSGA-II 시뮬레이션
- ✅ AAS 서버 데이터 자동 수집 및 변환
- ✅ 작업 디렉터리 관리 및 결과 추적성

## API Endpoints

### POST `/execute-goal`
Execute goal-based operations using ontology-driven workflow.

**Request:**
```json
{
  "goal": "query_failed_jobs_with_cooling",
  "date": "2025-08-11"
}
```

**Supported Goals:**
- `query_failed_jobs_with_cooling` - Query failed jobs with cooling process
- `track_product_position` - Track product location in factory
- `predict_first_completion_time` - Predict production completion time

## 시스템 아키텍처

### QueryGoal 시스템 (Goal 3)
```
자연어 입력
    ↓
┌─────────────────────────────────────┐
│ Pipeline (PipelineOrchestrator)     │
│ • Pattern Matching                  │
│ • Template Loading                  │
│ • Parameter Filling                 │
│ • ActionPlan Resolution             │
│ • Model Selection (SPARQL)          │
│ • Validation                        │
└─────────────────────────────────────┘
    ↓ QueryGoal JSON
┌─────────────────────────────────────┐
│ Runtime (QueryGoalExecutor)         │
│ • swrlSelection                     │
│ • yamlBinding (AAS 데이터 수집)     │
│ • simulation (Docker NSGA-II)       │
└─────────────────────────────────────┘
    ↓ 결과 (outputs + executionLog)
```

### Legacy 시스템 (Goal 1, 4)
```
External AAS Server (localhost:5001 또는 221.139.184.184:5001)
           ↑
    FastAPI Service (port 8000)
           ↓
    Execution Engine + Ontology (RDF/TTL)
```

## 프로젝트 구조

```
factory-automation-k8s/
├── querygoal/                  # QueryGoal 시스템 (Goal 3)
│   ├── pipeline/              # Pipeline 6 stages
│   │   ├── orchestrator.py   # 파이프라인 오케스트레이터
│   │   ├── pattern_matcher.py # 자연어 분석
│   │   ├── template_loader.py # QueryGoal 템플릿
│   │   ├── parameter_filler.py # 파라미터 채우기
│   │   ├── model_selector.py  # SPARQL 기반 모델 선택
│   │   └── validator.py       # 스키마 검증
│   └── runtime/               # Runtime 3 stages
│       ├── executor.py        # Stage-Gate 실행 엔진
│       ├── stage_gate_validator.py # 검증 로직
│       └── handlers/          # Stage 핸들러
│           ├── swrl_selection_handler.py
│           ├── yaml_binding_handler.py
│           └── simulation_handler.py
├── api/                       # FastAPI 애플리케이션
│   ├── main.py               # API 엔드포인트
│   └── schemas.py            # Request/Response 모델
├── execution_engine/          # Legacy 실행 엔진 (Goal 1, 4)
│   ├── planner.py            # 온톨로지 기반 계획
│   └── agent.py              # 액션 실행
├── ontology/                  # RDF 온톨로지 파일
│   └── factory_ontology.ttl
├── config/                    # 설정 파일
│   ├── rules.sparql          # SPARQL 규칙 (모델 선택)
│   ├── model_registry.json   # 모델 레지스트리
│   └── NSGA2Model_sources.yaml # Manifest
├── scripts/                   # 유틸리티 스크립트
│   └── build_nsga2_docker.sh
├── k8s/                       # Kubernetes 매니페스트
├── docs/                      # 문서
│   └── Goal3_E2E_Flow_Plan_Corrected.md
├── temp/                      # 런타임 작업 디렉터리
│   └── runtime_executions/   # QueryGoal 실행 결과
└── test_*.py                  # 테스트 스크립트
```

## 환경 설정

### 환경 변수

**QueryGoal 시스템 (Goal 3)**:
```bash
USE_STANDARD_SERVER=true         # AAS 서버 사용
AAS_SERVER_IP=127.0.0.1          # AAS 서버 IP (또는 221.139.184.184)
AAS_SERVER_PORT=5001             # AAS 서버 포트
FORCE_LOCAL_MODE=true            # 로컬 시뮬레이션 모드 (선택)
DEBUG_MODE=true                  # 디버그 로그 활성화 (선택)
```

**Legacy 시스템 (Goal 1, 4)**:
```bash
USE_STANDARD_SERVER=true         # 표준 AAS 서버 사용 (기본값)
AAS_SERVER_IP=127.0.0.1          # AAS 서버 IP
AAS_SERVER_PORT=5001             # AAS 서버 포트
```

### 실행 모드

1. **로컬 시뮬레이션 모드** (AAS 서버 불필요):
   - `FORCE_LOCAL_MODE=true` 설정
   - 하드코딩된 더미 데이터 사용
   - 개발/테스트에 적합

2. **표준 AAS 서버 모드**:
   - 실제 AAS 서버에서 데이터 수집
   - 프로덕션 환경에 적합

## 테스트

### QueryGoal E2E 테스트 (Goal 3)
```bash
# 로컬 모드
export FORCE_LOCAL_MODE=true
python test_runtime_executor.py

# 표준 AAS 서버 모드
export USE_STANDARD_SERVER=true
export AAS_SERVER_IP=221.139.184.184
export AAS_SERVER_PORT=5001
python test_runtime_executor.py
```

### Legacy Goal 테스트 (Goal 1, 4)
```bash
# Goal 1: 냉각 작업 실패 쿼리
USE_STANDARD_SERVER=true python test_goal1.py

# Goal 4: 제품 위치 추적
USE_STANDARD_SERVER=true python test_goal4.py
```

## Kubernetes 배포

Kubernetes 배포 방법은 [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)를 참조하세요.

## 문제 해결

### Goal 3 관련

**SelectionEngine 경고 발생**:
- `rules.sparql`에 모델 선택 규칙이 정의되어 있는지 확인
- `model_registry.json`의 `purpose` 필드가 SPARQL 규칙과 일치하는지 확인
- 로그에서 "SelectionEngine failed" 메시지 확인

**시뮬레이션 실패**:
- Docker 이미지가 빌드되었는지 확인: `docker images | grep factory-nsga2`
- 작업 디렉터리에 JSON 파일들이 생성되었는지 확인
- 컨테이너 로그 확인: `temp/runtime_executions/{goal_id}/container_logs.txt`

**파라미터 타입 오류**:
- `parameter_filler.py`가 네이티브 타입을 유지하는지 확인
- `model_selector.py`의 `_convert_params_to_strings()` 메서드 확인

### Legacy Goal 관련

**Connection Refused to localhost:5001**:
- 외부 AAS 서버가 실행 중인지 확인
- 방화벽 설정 확인
- 포트 5001이 접근 가능한지 확인

**Module Import Errors**:
- 가상 환경이 활성화되었는지 확인
- `pip install -r requirements.txt` 실행

## 개발 가이드

### QueryGoal 시스템 확장

1. **새로운 Goal Type 추가**:
   - `querygoal/pipeline/pattern_matcher.py`에 패턴 추가
   - `querygoal/templates/`에 템플릿 파일 생성
   - `config/rules.sparql`에 SPARQL 규칙 추가

2. **새로운 Runtime Stage 추가**:
   - `querygoal/runtime/handlers/`에 핸들러 클래스 생성
   - `BaseHandler` 상속 및 `execute()` 메서드 구현
   - `executor.py`의 `stage_handlers`에 등록

3. **새로운 모델 추가**:
   - `config/model_registry.json`에 모델 등록
   - Manifest YAML 파일 생성 (`config/`)
   - SPARQL 규칙에 모델 선택 로직 추가

### 상세 개발 가이드

[COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)를 참조하세요.

## License

MIT