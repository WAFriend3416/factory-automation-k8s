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
- ✅ QueryGoal Runtime Integration Plan 문서 분석 완료
- ✅ QueryGoal Runtime Executor Implementation Plan 작성 완료
- ✅ selectedModel 필드 접근 경로 수정 (metaDataFile, container.image 구조)
- ✅ Goal3 outputSpec 매핑 수정 (estimatedTime, confidence, productionPlan, bottlenecks)
- 📋 **Git에 저장 필요**: `docs/QueryGoal_Runtime_Executor_Implementation_Plan.md` 커밋하기
- 🔄 **구현 우선순위**:
  1. Phase 1: Core Infrastructure (QueryGoalExecutor, ExecutionContext)
  2. Phase 2: Stage Handlers (SwrlSelectionHandler, YamlBindingHandler, SimulationHandler)
  3. Phase 3: Common Runtime Components (AAS Client, Container Client)
  4. Phase 4: Integration & Testing

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