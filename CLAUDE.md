# Factory Automation K8s Project - 현재 구현 상황

## 프로젝트 개요
스마트 팩토리 자동화 시스템 - QueryGoal 기반 실행 파이프라인 구축 완료

### ✅ 현재 SWRL 파이프라인

```
1. QueryGoal 입력 ✅
   ↓
2. SWRL 엔진 → AI 모델 선택 결정 ✅
   - SPARQL 파일의 SWRL 규칙을 온톨로지에 동적 추가
   - 조건부 추론으로 최적 모델 선택
   ↓
3. 선택된 모델의 메타데이터 확인 ✅
   - 모델 input/output 스펙 분석
   - 필요한 데이터 타입 및 형식 확인
   ↓
4. 데이터 바인딩 YAML → 실제 원본 데이터 위치 파악 (향후 구현)
   - AAS 서버의 실제 데이터 경로 매핑
   - 데이터 접근 방법 및 필터링 조건
   ↓
5. 필요 데이터 수집 (AAS 서버에서) (향후 구현)
   - 실제 센서 데이터, 머신 상태, 작업 로그 수집
   ↓
6. 입력 데이터로 가공 (모델 요구 형식으로) (향후 구현)
   - 모델별 입력 스키마에 맞춰 데이터 변환
   ↓
7. 모델에 입력 데이터 넣고 결과 받기 (향후 구현)
   - 실제 AI/ML 모델 실행 및 예측 결과 생성
```

**복구 완료된 구성요소**:
- ✅ SWRL 규칙이 포함된 SPARQL 파일 (`config/rules.sparql`)
- ✅ 동적 온톨로지 규칙 추가 엔진 (`execution_engine/swrl/selection_engine.py`)
- ✅ 모델 메타데이터 시스템 (`config/model_registry.json`)
- ✅ QueryGoal 전처리 및 검증 (`execution_engine/swrl/preprocessor.py`, `schema_validator.py`)
- ✅ RDF/OWL 온톨로지 (`config/ontology.owl`)

**향후 구현 필요**:
- 🔄 데이터 바인딩 YAML 시스템[진행중] * 이전 담당자의 작업을 이어야해야할 수 있음.
- 🔄 실제 데이터 수집 및 가공 모듈

## 📝 TODO: QueryGoal Runtime Executor 구현

### ✅ 완료된 작업
- ✅ QueryGoal Runtime Integration Plan 문서 분석 완료
- ✅ QueryGoal Runtime Executor Implementation Plan 작성 완료
- ✅ selectedModel 필드 접근 경로 수정 (metaDataFile, container.image 구조)
- ✅ Goal3 outputSpec 매핑 수정 (estimatedTime, confidence, productionPlan, bottlenecks)
- ✅ Docker 명령어 환경변수 순서 수정 (이미지 이름 앞에 -e 플래그 배치)
- ✅ Kubernetes 실행 경로 제거 (Docker-only, future expansion으로 표시)
- ✅ Stage-Gate yamlBinding Required-flag filtering 적용
- ✅ Manifest 스키마에 required 필드 추가 및 예제 작성
- ✅ Manifest 키 이름 통일 (data_sources)
- ✅ Stage-Gate error 상태 체크 추가 (status == "success")
- ✅ Manifest combination_rules와 _apply_combination_rules 로직 정렬
- ✅ **Runtime Executor 구현 완료 (Phase 1-3 모든 컴포넌트)**
  - ✅ `querygoal/runtime/executor.py` - QueryGoalExecutor 오케스트레이터
  - ✅ `querygoal/runtime/utils/stage_gate.py` - Stage-Gate Validator
  - ✅ `querygoal/runtime/utils/work_directory.py` - Work Directory Manager
  - ✅ `querygoal/runtime/utils/manifest_parser.py` - Manifest Parser
  - ✅ `querygoal/runtime/handlers/base_handler.py` - Base Handler
  - ✅ `querygoal/runtime/handlers/swrl_selection_handler.py` - SWRL Selection
  - ✅ `querygoal/runtime/handlers/yaml_binding_handler.py` - YAML Binding with AAS
  - ✅ `querygoal/runtime/handlers/simulation_handler.py` - Docker Simulation
  - ✅ `querygoal/runtime/clients/aas_client.py` - AAS REST API Client
  - ✅ `querygoal/runtime/clients/container_client.py` - Docker Container Client
  - ✅ `querygoal/runtime/exceptions.py` - Runtime Exception Classes
  - ✅ `test_runtime_executor.py` - 기본 통합 테스트

### 📋 구현 우선순위 (4-Phase 8주 로드맵)

#### Phase 1: 핵심 Runtime Executor (주 1-2) ✅ **완료**
- [x] **Task 1.1**: QueryGoalExecutor 오케스트레이터 구현 (2일)
  - `querygoal/runtime/executor.py` - 메인 실행 엔진
  - ExecutionContext 데이터 클래스
  - Stage-Gate 검증 로직

- [x] **Task 1.2**: Base Handler 추상 클래스 (1일)
  - `querygoal/runtime/handlers/base_handler.py`
  - pre_execute/execute/post_execute 훅
  - 공통 에러 처리

- [x] **Task 1.3**: Stage-Gate Validator (1일)
  - `querygoal/runtime/utils/stage_gate.py`
  - 성공 기준 검증 로직
  - Required-flag filtering 지원

- [x] **Task 1.4**: Work Directory Manager (1일)
  - `querygoal/runtime/utils/work_directory.py`
  - Goal별 독립 작업 디렉터리 생성/관리

#### Phase 2: Goal3 특화 Stage 핸들러 (주 3-4) ✅ **완료**
- [x] **Task 2.1**: SwrlSelectionHandler 구현 (2일)
  - `querygoal/runtime/handlers/swrl_selection_handler.py`
  - 모델 메타데이터 로딩 (metaDataFile at top level)
  - Manifest 경로 반환

- [x] **Task 2.2**: YamlBindingHandler 구현 (3일)
  - `querygoal/runtime/handlers/yaml_binding_handler.py`
  - Manifest 파싱 (data_sources)
  - Required/Optional 소스 구분 처리
  - AAS 데이터 수집 (aas_property, aas_shell_collection)
  - JSON 파일 생성 (machines.json, materials.json 등)

- [x] **Task 2.3**: SimulationHandler 구현 (3일)
  - `querygoal/runtime/handlers/simulation_handler.py`
  - 컨테이너 이미지 접근 (container.image 구조)
  - Docker 실행 (환경변수 올바른 순서)
  - 시뮬레이션 결과 파싱
  - Goal3 outputSpec 매핑 (estimatedTime, confidence, productionPlan, bottlenecks)

#### Phase 3: 공통 Runtime 컴포넌트 (주 5-6) ✅ **완료**
- [x] **Task 3.1**: AAS Client 구현 (2일)
  - `querygoal/runtime/clients/aas_client.py`
  - REST API 클라이언트 (httpx 기반)
  - list_shells, get_shell, get_submodel_property

- [x] **Task 3.2**: Container Client 구현 (2일)
  - `querygoal/runtime/clients/container_client.py`
  - Docker 실행 (asyncio 기반)
  - 환경변수, 볼륨 마운트 처리
  - 로그 수집 및 결과 파싱

- [x] **Task 3.3**: Manifest Parser 구현 (1일)
  - `querygoal/runtime/utils/manifest_parser.py`
  - YAML manifest 파싱
  - 스키마 검증

- [x] **Task 3.4**: Exception Classes 정의 (1일)
  - `querygoal/runtime/exceptions.py`
  - RuntimeExecutionError, StageExecutionError 등

#### Phase 4: API 통합 및 테스트 (주 7-8)
- [ ] **Task 4.1**: API 엔드포인트 추가 (1일)
  - `api/main.py` - POST /runtime/execute 엔드포인트
  - QueryGoal 실행 요청 처리

- [ ] **Task 4.2**: 통합 테스트 작성 (2일)
  - Goal3 End-to-End 테스트
  - Stage별 유닛 테스트
  - Mock AAS 서버 테스트

- [ ] **Task 4.3**: 문서화 및 예제 (1일)
  - API 사용 가이드
  - Manifest 작성 가이드
  - 문제 해결 가이드

- [ ] **Task 4.4**: 성능 최적화 및 리팩토링 (2일)
  - 병렬 처리 최적화
  - 에러 복구 메커니즘
  - 로깅 개선

### 🎯 구현 시 주의사항
1. **selectedModel 필드 접근**: `metaDataFile` (최상위), `container.image` (중첩)
2. **Manifest 키**: `data_sources` (snake_case) 사용
3. **Required-flag filtering**: `required: true|false` 지원, 기본값 `true`
4. **Stage-Gate 검증**: `status == "success"` 먼저 확인 후 성공률 검증
5. **Docker 명령어**: 환경변수(-e) → 이미지 이름 순서
6. **Kubernetes**: 현재 미지원, Docker-only 실행


<!-- ### 현재 Goal 시나리오
- 총 Goal1,2,3,4 가 존재 , 현재 Goal 1, 3, 4만 구현
- QueryGoal 형태로 Goal3만 진행
    

## 📊 테스트 결과

### 통합 테스트 성공률
- **Dry Run**: Goal 1, 3, 4 모두 100% 성공
- **실제 실행**: Goal 3 완전한 End-to-End 성공
- **AAS 서버 연동**: 실제 HTTP 통신 성공
- **파이프라인 완성도**: 100%

### 실제 확인된 기능 ( Goal3:시뮬레이터 실행 포함 과정 - 한정)
- ✅ QueryGoal → 실행 계획 변환
- ✅ AAS 서버 실제 데이터 쿼리
- ✅ 시뮬레이션 입력 JSON 생성
- ✅ Docker 컨테이너 시뮬레이션 실행
- ✅ 생산 시간 예측 결과 생성

## 환경 설정

### 기본 환경
```bash
cd factory-automation-k8s
pip install -r requirements.txt
```

### API 서버 실행 (표준 AAS 서버 연동)
```bash
export USE_STANDARD_SERVER=true
export AAS_SERVER_IP=127.0.0.1
export AAS_SERVER_PORT=5001
uvicorn api.main:app --reload --port 8000
```

### 통합 테스트 실행
```bash
# 전체 통합 테스트 (Dry Run)
python temp/output_2/integration_test_runner.py

# Goal 3 실제 실행 테스트  
python temp/output_2/goal3_execution_test.py
```

## Git 브랜치 전략
- `main`: 안정적인 메인 브랜치
- `feature/*`: 기능 개발 브랜치
- 커밋 전 항상 `git status` 확인 -->