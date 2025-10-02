# SWRL 시스템 완전 분석 결과

## 📂 ~/Desktop/swrl 폴더 구조
```
swrl/
├── data/                           # 핵심 데이터 파일들
│   ├── JobETAModel_sources.yaml   # AAS 서버 기반 YAML 설정
│   ├── model_registry.json        # 4개 모델 등록 정보
│   ├── ontology.owl               # RDF 온톨로지
│   └── rules.sparql               # SPARQL 기반 모델 선택 규칙
├── input_data/                    # 사용자 입력 데이터
│   ├── user_input_clean.json      # QueryGoal 스키마 예시
│   └── user_input.json           # 원본 사용자 입력
├── src/                           # 실제 SWRL 추론 엔진
│   ├── selection_engine.py        # SPARQL 기반 모델 선택 엔진
│   ├── data_orchestrator.py       # 데이터 수집 오케스트레이터
│   ├── preprocessor.py            # 전처리기
│   └── schema_validator.py        # 스키마 검증기
└── main.py                        # 메인 실행 파일
```

## 🎯 올바른 파이프라인 구조 (실제 SWRL 시스템)

### 1. QueryGoal 입력 스키마
```json
{
  "QueryGoal": {
    "goalId": "goal-job-eta-0001",
    "goalType": "predict_job_completion_time",
    "parameters": [
      { "key": "jobId", "value": "JOB-7f2e3a8b-1d" }
    ],
    "outputSpec": [
      { "name": "completion_time", "datatype": "datetime" }
    ]
  }
}
```

### 2. SPARQL 기반 모델 선택 규칙
- Rule 1: goalType "predict_job_completion_time" → JobETAModel
- Rule 2: goalType "classify_job_priority" → JobClassifierModel  
- Rule 3: goalType "detect_job_anomaly" → AnomalyDetectorModel
- Rule 4: goalType "optimize_job_schedule" → ScheduleOptimizerModel

### 3. 모델 레지스트리 (4개 AI 모델)
- JobETAModel (1.4.2): 작업 완료 시간 예측
- JobClassifierModel (2.1.0): 작업 우선순위 분류
- AnomalyDetectorModel (3.0.1): 작업 패턴 이상 탐지
- ScheduleOptimizerModel (1.8.5): 작업 스케줄 최적화

### 4. YAML 설정 구조 (AAS 기반)
```yaml
sources:
  JobOrders:
    uri: "aas://FactoryTwin/ProcessData/JobOrders"
    method: "GET"
    required: true
  MachineStatus:
    uri: "aas://FactoryTwin/LiveData/MachineStateSnapshot"
    method: "GET"
    fallback:
      strategy: "default"
```

### 5. 실제 SWRL 추론 엔진
- selection_engine.py: SPARQL 기반 모델 선택
- RDFLib를 사용한 온톨로지 추론
- 4단계 추론: 전처리 → SPARQL 실행 → 메타데이터 통합 → 최종 응답

## 🔍 기존 구현과의 차이점

### ❌ 기존 잘못된 구현
1. 하드코딩된 JSON 파일들로 SWRL 시뮬레이션
2. NSGA-II 시뮬레이터만 고려 (AI 모델 미고려)
3. QueryGoal 입력 과정 누락
4. 실제 SPARQL 추론 엔진 미구현

### ✅ 올바른 구현 (~/desktop/swrl 기반)
1. 실제 SPARQL 규칙 기반 모델 선택
2. 4개 AI 모델 + 1개 시뮬레이터 지원
3. QueryGoal 스키마 정의 및 검증
4. RDFLib 기반 실제 추론 엔진 구현
5. AAS URI 기반 데이터 소스 설정

## 📝 다음 단계
기존 factory-automation-k8s 프로젝트에 올바른 SWRL 시스템 통합 필요