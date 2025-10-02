# Factory Automation with QueryGoal System

**차세대 스마트 팩토리 자동화 플랫폼**: 자연어 기반 쿼리 시스템, AAS (Asset Administration Shell) 통합, 온톨로지 기반 추론 엔진

## 프로젝트 소개

본 프로젝트는 **스마트 팩토리 운영을 위한 지능형 자동화 시스템**으로, 다음과 같은 핵심 목표를 달성합니다:

### 주요 목표 (Goals)

1. **Goal 1 - 작업 실패 분석**: 특정 공정(예: 냉각)에서 실패한 작업 조회 및 분석
2. **Goal 2 - 이상 감지**: 설비 및 공정 이상 패턴 자동 탐지 (ML 모델 기반)
3. **Goal 3 - 생산 시간 예측**: 제품별 생산 완료 시간 예측 및 최적화 (NSGA-II 시뮬레이션)
4. **Goal 4 - 제품 추적**: 공장 내 제품 위치 실시간 추적

### 시스템 진화 전략

본 프로젝트는 **두 가지 실행 아키텍처**를 병행하며, 점진적으로 현대화된 QueryGoal 방식으로 전환합니다:

| 아키텍처 | 설명 | 현재 상태 |
|---------|------|----------|
| **QueryGoal System** | 자연어 → Pipeline(6단계) → Runtime(3단계) → 실행 결과 | ✅ Goal 3 완전 구현 |
| **Legacy System** | 온톨로지 기반 전통적 실행 엔진 | ✅ Goal 1, 4 작동 중 |

> 🎯 **향후 계획**: Goal 1, 4는 현재 Legacy 방식으로 작동하지만, **QueryGoal 시스템으로 전환을 권장**합니다. QueryGoal은 자연어 입력, SPARQL 기반 모델 선택, 추적 가능한 실행 로그 등 현대적인 기능을 제공합니다.

> 📖 **필독**: QueryGoal의 전체 E2E 흐름과 작동 원리는 **[Goal3 E2E Flow Plan](docs/Goal3_E2E_Flow_Plan_Corrected.md)** 문서를 반드시 참조하세요. 시스템 이해를 위한 핵심 문서입니다.

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

## 주요 기능 현황

| Goal | 설명 | 상태 | 테스트 명령어 | 실행 방식 | 비고 |
|------|------|------|--------------|-----------|------|
| **Goal 3** | **생산 시간 예측** | ✅ **완전 구현** | `python test_runtime_executor.py` | **QueryGoal Pipeline/Runtime** | **현대적 아키텍처** |
| Goal 1 | 냉각 작업 실패 쿼리 | ✅ 작동 | `python test_goal1.py` | Legacy Ontology | ⚠️ QueryGoal 전환 권장 |
| Goal 4 | 제품 위치 추적 | ✅ 작동 | `python test_goal4.py` | Legacy Ontology | ⚠️ QueryGoal 전환 권장 |
| Goal 2 | 이상 감지 | ⏳ ML 모델 필요 | - | (미구현) | QueryGoal 방식 권장 |

> 💡 **전환 권장 이유**:
> - **자연어 입력 지원**: "Predict production time for product X quantity 50" 형태의 직관적 입력
> - **SPARQL 기반 모델 선택**: 온톨로지를 통한 지능적 모델 매칭
> - **추적성**: 모든 실행 단계가 `temp/runtime_executions/`에 기록
> - **검증 체계**: Stage-Gate 패턴으로 각 단계 검증
> - **확장성**: 새로운 Goal 추가가 템플릿 기반으로 간편

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

FastAPI 기반 RESTful API를 통해 두 가지 실행 방식을 지원합니다.

### 1. QueryGoal 시스템 (권장)

#### POST `/querygoal/execute`
자연어 기반 QueryGoal 실행 (Pipeline → Runtime → 결과)

**Request:**
```json
{
  "naturalLanguageInput": "Predict production time for product TEST_RUNTIME quantity 30"
}
```

**Response:**
```json
{
  "goalId": "qg_20250110_153045_abc123",
  "goalType": "goal3_predict_production_time",
  "status": "completed",
  "outputs": {
    "estimatedTime": 145.5,
    "confidence": 0.92,
    "productionPlan": [...],
    "bottlenecks": [...]
  },
  "executionLog": {
    "pipeline": {...},
    "runtime": {...}
  }
}
```

**특징**:
- 자연어 입력 자동 분석 (Pattern Matching)
- SPARQL 기반 모델 자동 선택
- 완전한 실행 추적성 (모든 단계 로그 기록)
- Stage-Gate 검증으로 안정성 보장

> 📖 **상세 흐름**: [Goal3 E2E Flow Plan](docs/Goal3_E2E_Flow_Plan_Corrected.md) 참조

### 2. Legacy 시스템 (Goal 1, 4)

#### POST `/execute-goal`
온톨로지 기반 전통적 Goal 실행

**Request:**
```json
{
  "goal": "query_failed_jobs_with_cooling",
  "date": "2025-08-11"
}
```

**Supported Goals:**
- `query_failed_jobs_with_cooling` - 냉각 공정 실패 작업 조회 (Goal 1)
- `track_product_position` - 제품 위치 추적 (Goal 4)
- `predict_first_completion_time` - 생산 시간 예측 (Goal 3 Legacy, ⚠️ QueryGoal 방식 권장)

**Response:**
```json
{
  "result": [...],
  "execution_time": 0.234
}
```

> ⚠️ **마이그레이션 권장**: 이 엔드포인트는 Legacy 지원 목적이며, 향후 `/querygoal/execute`로 통합될 예정입니다.

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

## Kubernetes 배포

Kubernetes 매니페스트는 `k8s/` 디렉터리에 준비되어 있습니다.

### 배포 방법
```bash
# Namespace 생성
kubectl create namespace factory-automation

# ConfigMap 및 Deployment 배포
kubectl apply -f k8s/ -n factory-automation

# 서비스 상태 확인
kubectl get pods -n factory-automation
kubectl get svc -n factory-automation

# 로그 확인
kubectl logs -f deployment/api-deployment -n factory-automation
```

### 서비스 접근
```bash
# 포트 포워딩으로 로컬 접근
kubectl port-forward svc/api-service 8000:8000 -n factory-automation

# API 테스트
curl http://localhost:8000/docs
```

## 참고 문서

- **[Goal3 E2E Flow Plan](docs/Goal3_E2E_Flow_Plan_Corrected.md)** ⭐ - QueryGoal 시스템의 전체 E2E 흐름 (필독)
- **[CLAUDE.md](CLAUDE.md)** - 프로젝트 개발 가이드 및 주의사항

## License

MIT