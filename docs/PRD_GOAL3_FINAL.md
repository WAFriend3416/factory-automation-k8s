# Goal 3 시나리오 합성 시스템 PRD (최종판)

**문서 버전**: 2.0  
**작성일**: 2025-09-17  
**기반**: 담당자 피드백 및 NSGA-II 시뮬레이터 실제 분석 결과  
**목표**: 논문 실험용 Goal 3 시나리오 합성 및 NSGA-II 통합 시스템

---

## 1. 개요 (Executive Summary)

### 1.1 프로젝트 목적
논문 실험을 위한 **동적 시나리오 합성 기반 제조 시스템 최적화** 시스템 구축. 기존 정적 Action Plan 방식에서 벗어나 QueryGoal 명세에 따른 실시간 시나리오 생성 및 NSGA-II 최적화 시뮬레이터를 통한 정확한 작업 완료 시간 예측 시스템 개발.

### 1.2 핵심 가치 제안
- **동적 시나리오 합성**: MetaData.json + bindings.yaml 기반 실시간 데이터 조합
- **고정밀 시뮬레이션**: NSGA-II Branch-and-Bound 알고리즘을 통한 최적 스케줄링
- **완전한 재현성**: manifest.json 기반 실행 이력 추적 및 감사
- **연구 활용**: 논문 실험 데이터 생성 및 알고리즘 검증 플랫폼

### 1.3 프로젝트 범위
- **대상**: Goal 3 (`predict_job_completion_time`) 전용 구현
- **기존 시스템**: Goal 1, 2, 4는 현재 방식 유지 (무영향)
- **환경**: Docker Desktop K8s 클러스터 기반 개발/실험 환경
- **기간**: 11일 (2주 이내) 집중 개발

---

## 2. 시스템 아키텍처

### 2.1 전체 데이터 흐름
```
QueryGoal.json → MetaData.json 로드 → bindings.yaml 파싱 → 
동적 Submodel 생성 → 다중 소스 데이터 수집 → 데이터 결합 정책 적용 → 
6개 JSON 파일 생성 → NSGA-II 시뮬레이터 실행 → 결과 매핑 → 
manifest.json 로깅 → QueryGoal 응답 반환
```

### 2.2 핵심 컴포넌트

#### **API Layer** (`api/`)
- **역할**: QueryGoal 요청 접수 및 Goal 3 분기 처리
- **핵심 기능**:
  - QueryGoal Pydantic 스키마 검증
  - `goalType: "predict_job_completion_time"` 분기 라우팅
  - ScenarioComposer 호출 및 응답 처리

#### **Scenario Composer** (`execution_engine/scenario_composer.py`)
- **역할**: 시나리오 합성의 핵심 엔진
- **핵심 기능**:
  - MetaData.json 기반 requiredInputs 파악
  - bindings.yaml 파싱 및 데이터 소스 매핑
  - 동적 시나리오별 Submodel 생성/관리
  - 복잡한 데이터 결합 정책 (overlay, concat, latest) 적용
  - NSGA-II 시뮬레이터용 6개 JSON 파일 생성

#### **Execution Agent** (`execution_engine/agent.py`)
- **역할**: K8s Job을 통한 NSGA-II 시뮬레이터 실행
- **핵심 기능**:
  - Docker 컨테이너 기반 시뮬레이터 실행
  - PVC 마운트를 통한 시나리오 파일 전달
  - 시뮬레이터 결과 수집 및 매핑

#### **AAS Data Layer**
- **역할**: 다중 데이터 소스 통합 관리
- **구성요소**:
  - **AAS 서버**: 정적 시나리오 데이터 (Scenario_* Submodel)
  - **SQLite 서버**: 시계열 기계 상태 데이터
  - **파일 시스템**: WIP, Backlog 등 파일 기반 데이터

---

## 3. 데이터 모델 및 스키마

### 3.1 QueryGoal 입력 스키마
```json
{
  "QueryGoal": {
    "goalId": "goal-job-eta-0001",
    "goalType": "predict_job_completion_time",
    "parameters": [
      { "key": "jobId", "value": "JOB-7f2e3a8b-1d" },
      { "key": "dueDate", "value": "@현재시간" }
    ],
    "outputSpec": [
      { "name": "completion_time", "datatype": "datetime" },
      { "name": "tardiness_s", "datatype": "number" },
      { "name": "sla_met", "datatype": "boolean" }
    ],
    "selectedModelRef": "aas://ModelCatalog/JobETAModel@1.4.2",
    "selectedModel": {
      "modelId": "JobETAModel",
      "MetaData": "JobEtaMetaData.json",
      "container": {
        "image": "nsga-simulator:latest",
        "digest": "sha256:..."
      }
    }
  }
}
```

### 3.2 MetaData.json 구조
```json
{
  "modelId": "JobETAModel_v1.4.2",
  "description": "NSGA-II 기반 작업 완료 시간 예측 모델",
  "requiredInputs": [
    "JobRoute", "MachineState", "Calendar", 
    "SetupMatrix", "WIP", "Backlog"
  ],
  "bindings": "bindings_goal3.yaml",
  "simulator": {
    "container_image": "nsga-simulator:latest",
    "algorithm": "branch_and_bound",
    "timeout_seconds": 300,
    "resource_limits": {
      "cpu": "1000m",
      "memory": "2Gi"
    }
  },
  "outputMapping": {
    "completion_time": "best_objective",
    "tardiness_s": "calculated.tardiness",
    "sla_met": "validation.sla_compliance"
  },
  "validation": {
    "required_files": [
      "jobs.json", "operations.json", "machines.json",
      "operation_durations.json", "machine_transfer_time.json", 
      "job_release.json"
    ],
    "schema_version": "1.0"
  }
}
```

### 3.3 bindings.yaml 구조
```yaml
# 데이터 소스 바인딩 설정
sources:
  # AAS 서버 기반 정적 데이터
  JobRoute:
    type: "aas"
    uri: "aas://FactoryTwin/Scenario_{scenario_id}_JobRoute_{jobId}"
    extract: "Content"  # JSON 문자열 프로퍼티
    parser: "json"
    
  # SQLite 시계열 데이터
  MachineState:
    type: "timeseries"
    uri: "sqlite://machine_states"
    query: |
      SELECT machine_id, status, timestamp, job_id 
      FROM machine_status 
      WHERE timestamp <= ? 
      ORDER BY timestamp DESC 
      LIMIT 10
    params: ["{bindAt}"]
    format: "machines.json"
    
  # 파일 시스템 기반 동적 데이터
  WIP:
    type: "file"
    path: "/data/wip/*.json"
    glob:
      pattern: "wip_*.json"
      sort: ["mtime:desc", "name:asc"]
      window: { count: 5 }
    combine:
      op: "overlay"
      key: "partId"
      merge_strategy: "last_wins"
      
  Backlog:
    type: "file"
    path: "/data/backlog/*.json"
    glob:
      pattern: "backlog_*.json"
      sort: ["mtime:desc"]
      window: { count: 3 }
    combine:
      op: "concat"
      
  # 정적 설정 데이터
  Calendar:
    type: "static"
    content: |
      {
        "working_hours": {
          "monday": {"start": "09:00", "end": "18:00"},
          "tuesday": {"start": "09:00", "end": "18:00"},
          "wednesday": {"start": "09:00", "end": "18:00"},
          "thursday": {"start": "09:00", "end": "18:00"},
          "friday": {"start": "09:00", "end": "18:00"},
          "saturday": "closed",
          "sunday": "closed"
        },
        "holidays": ["2025-01-01", "2025-03-01", "2025-12-25"],
        "timezone": "Asia/Seoul"
      }
      
  SetupMatrix:
    type: "aas"
    uri: "aas://FactoryTwin/Scenario_{scenario_id}_SetupMatrix"
    extract: "Content"
    parser: "json"

# 데이터 결합 정책
combine_policies:
  overlay:
    description: "나중 데이터가 먼저 데이터를 덮어씀 (last-wins)"
    conflict_resolution: "latest_timestamp"
    
  concat:
    description: "모든 데이터를 순차적으로 연결"
    ordering: "timestamp_asc"
    
  latest:
    description: "가장 최신 타임스탬프 데이터만 유지"
    timestamp_field: "timestamp"
    
# 매크로 치환 규칙
macros:
  "@현재시간": 
    format: "iso8601"
    timezone: "Asia/Seoul"
  "{scenario_id}":
    pattern: "goal3_{timestamp}_{jobId}"
  "{bindAt}":
    source: "parameters.dueDate"
    fallback: "@현재시간"
```

### 3.4 동적 Submodel 구조
각 시나리오마다 전용 Submodel 생성:

```json
{
  "Scenario_{scenario_id}_Jobs": {
    "idShort": "Scenario_goal3_20250917_143052_Jobs",
    "id": "urn:factory:scenario:goal3_20250917_143052:Jobs",
    "elements": [
      {
        "idShort": "Content",
        "modelType": "Property",
        "valueType": "string",
        "value": "{\"jobs\": [{\"job_id\": \"J1\", \"part_id\": \"P1\", \"operations\": [\"O11\", \"O12\"], \"release_time\": 0.0}]}"
      }
    ]
  }
}
```

---

## 4. NSGA-II 시뮬레이터 통합

### 4.1 시뮬레이터 분석 결과
- **GitHub**: https://github.com/Otober/AASX (Public)
- **실행 방법**: `python3 simulator/main.py --scenario /path/to/scenario`
- **의존성**: pandas, numpy, openpyxl
- **알고리즘**: branch_and_bound (기본), mcts, dfs

### 4.2 입력 파일 형식 (6개 JSON)
1. **jobs.json**: 작업 정의
   ```json
   [
     {
       "job_id": "J1",
       "part_id": "P1", 
       "operations": ["O11", "O12", "O13"],
       "release_time": 0.0
     }
   ]
   ```

2. **operations.json**: 작업 단계 정의
3. **machines.json**: 기계 정의 및 상태
4. **operation_durations.json**: 작업 시간 분포
5. **machine_transfer_time.json**: 기계 간 이동 시간
6. **job_release.json**: 작업 출시 시간

### 4.3 출력 결과 매핑
시뮬레이터 출력 → QueryGoal outputSpec 매핑:

```python
def map_simulator_output(simulator_result: dict) -> dict:
    """시뮬레이터 결과를 QueryGoal outputSpec 형식으로 변환"""
    return {
        "completion_time": simulator_result["best_objective"],  # makespan
        "tardiness_s": calculate_tardiness(simulator_result),   # 별도 계산
        "sla_met": check_sla_compliance(simulator_result)       # 별도 검증
    }
    
def calculate_tardiness(result: dict) -> float:
    """작업 완료 시간과 목표 시간 차이 계산"""
    # 구현 로직: due_date와 completion_time 비교
    
def check_sla_compliance(result: dict) -> bool:
    """SLA 준수 여부 검증"""
    # 구현 로직: tardiness가 허용 범위 내인지 확인
```

### 4.4 Docker 컨테이너화
```dockerfile
FROM python:3.9-slim

# 시뮬레이터 의존성 설치
RUN pip install pandas==1.5.3 numpy==1.24.3 openpyxl==3.1.2

# NSGA-II 시뮬레이터 복사
COPY ./nsga-simulator /opt/nsga-simulator

# 작업 디렉토리 설정
WORKDIR /opt/nsga-simulator

# 시나리오 실행 스크립트
COPY run_simulation.py /opt/
RUN chmod +x /opt/run_simulation.py

# 시뮬레이터 실행
ENTRYPOINT ["python3", "/opt/run_simulation.py"]
```

---

## 5. 데이터 수집 및 결합 전략

### 5.1 하이브리드 데이터 전략
- **정적 데이터**: AAS Submodel의 Content Property (JSON 문자열)
- **동적 데이터**: SQLite 시계열 조회, 파일 시스템 glob
- **정적 설정**: bindings.yaml에 하드코딩

### 5.2 데이터 결합 정책

#### **Overlay 결합**
```python
def overlay_combine(sources: List[dict], key_field: str) -> List[dict]:
    """나중 데이터가 먼저 데이터를 덮어씀 (last-wins)"""
    result = {}
    for source in sources:
        for item in source:
            result[item[key_field]] = item
    return list(result.values())
```

#### **Concat 결합**
```python
def concat_combine(sources: List[dict]) -> List[dict]:
    """모든 데이터를 순차적으로 연결"""
    result = []
    for source in sources:
        result.extend(source)
    return result
```

#### **Latest 결합**
```python
def latest_combine(sources: List[dict], timestamp_field: str) -> List[dict]:
    """가장 최신 타임스탬프 데이터만 유지"""
    all_items = []
    for source in sources:
        all_items.extend(source)
    
    # 타임스탬프 기준 정렬 후 최신 데이터만 반환
    all_items.sort(key=lambda x: x[timestamp_field], reverse=True)
    return all_items[:1]  # 최신 1개만
```

---

## 6. 재현성 및 추적성

### 6.1 manifest.json 구조
```json
{
  "scenario_id": "goal3_20250917_143052",
  "timestamp": "2025-09-17T14:30:52+09:00",
  "query_goal": {
    "hash": "sha256:abc123def456...",
    "job_id": "JOB-7f2e3a8b-1d",
    "goal_type": "predict_job_completion_time",
    "parameters": {
      "jobId": "JOB-7f2e3a8b-1d",
      "dueDate": "2025-09-17T18:00:00+09:00"
    }
  },
  "metadata": {
    "model_id": "JobETAModel_v1.4.2",
    "bindings_file": "bindings_goal3.yaml",
    "required_inputs": ["JobRoute", "MachineState", "Calendar", "SetupMatrix", "WIP", "Backlog"]
  },
  "data_sources": {
    "JobRoute": {
      "type": "aas",
      "submodel": "Scenario_goal3_20250917_143052_JobRoute_JOB-7f2e3a8b-1d",
      "uri": "aas://FactoryTwin/Scenario_goal3_20250917_143052_JobRoute_JOB-7f2e3a8b-1d",
      "hash": "sha256:def456abc789...",
      "collected_at": "2025-09-17T14:30:53+09:00",
      "size_bytes": 1024
    },
    "MachineState": {
      "type": "timeseries",
      "source": "sqlite://machine_states",
      "query": "SELECT * FROM machine_status WHERE timestamp <= '2025-09-17T14:30:52+09:00' ORDER BY timestamp DESC LIMIT 10",
      "records_count": 8,
      "hash": "sha256:789abcdef123...",
      "collected_at": "2025-09-17T14:30:54+09:00"
    },
    "WIP": {
      "type": "file",
      "path": "/data/wip/*.json",
      "files_processed": ["wip_20250917_1430.json", "wip_20250917_1425.json"],
      "combine_policy": "overlay",
      "hash": "sha256:fedcba987654...",
      "collected_at": "2025-09-17T14:30:55+09:00"
    }
  },
  "scenario_files": {
    "jobs.json": {
      "hash": "sha256:111222333444...",
      "size_bytes": 2048,
      "generated_at": "2025-09-17T14:30:56+09:00"
    },
    "operations.json": {
      "hash": "sha256:555666777888...",
      "size_bytes": 1536,
      "generated_at": "2025-09-17T14:30:56+09:00"
    },
    "machines.json": {
      "hash": "sha256:999aaabbbccc...",
      "size_bytes": 512,
      "generated_at": "2025-09-17T14:30:57+09:00"
    },
    "operation_durations.json": {
      "hash": "sha256:dddeeefff000...",
      "size_bytes": 768,
      "generated_at": "2025-09-17T14:30:57+09:00"
    },
    "machine_transfer_time.json": {
      "hash": "sha256:111aaa222bbb...",
      "size_bytes": 384,
      "generated_at": "2025-09-17T14:30:58+09:00"
    },
    "job_release.json": {
      "hash": "sha256:ccc333ddd444...",
      "size_bytes": 256,
      "generated_at": "2025-09-17T14:30:58+09:00"
    }
  },
  "simulator_execution": {
    "container_image": "nsga-simulator:latest",
    "algorithm": "branch_and_bound",
    "start_time": "2025-09-17T14:31:00+09:00",
    "end_time": "2025-09-17T14:31:45+09:00",
    "duration_seconds": 45,
    "exit_code": 0,
    "command": ["python3", "simulator/main.py", "--scenario", "/tmp/scenario_goal3_20250917_143052", "--algorithm", "branch_and_bound"],
    "resource_usage": {
      "cpu_seconds": 42.3,
      "memory_peak_mb": 256,
      "disk_io_mb": 12.8
    },
    "result_files": [
      "simulator_optimization_result.json",
      "trace.xlsx",
      "job_info.csv",
      "operation_info.csv"
    ]
  },
  "output_mapping": {
    "raw_result": {
      "algorithm": "BRANCH_AND_BOUND",
      "best_objective": 15.2,
      "search_time": 45.3,
      "nodes_explored": 5000,
      "best_schedule": ["Action(O11 -> M1, pos=None)", "Action(O12 -> M2, pos=None)"]
    },
    "mapped_output": {
      "completion_time": "2025-09-17T14:46:12+09:00",
      "tardiness_s": 0,
      "sla_met": true
    }
  },
  "reproducibility": {
    "system_info": {
      "os": "Darwin 24.6.0",
      "python_version": "3.9.18",
      "kubernetes_version": "v1.29.1",
      "docker_version": "24.0.6"
    },
    "environment": {
      "aas_server_version": "v2.1.0",
      "aas_server_endpoint": "http://aas-server:5001",
      "sqlite_db_version": "3.42.0",
      "timezone": "Asia/Seoul"
    },
    "checksums": {
      "metadata_json": "sha256:aaa111bbb222...",
      "bindings_yaml": "sha256:ccc333ddd444...",
      "all_inputs_combined": "sha256:eee555fff666..."
    }
  },
  "validation": {
    "schema_validation": {
      "passed": true,
      "checked_at": "2025-09-17T14:30:59+09:00",
      "validator_version": "1.0"
    },
    "data_integrity": {
      "all_required_files_present": true,
      "file_size_validation": true,
      "json_syntax_validation": true
    }
  }
}
```

### 6.2 해시 계산 전략
```python
import hashlib
import json

def calculate_data_hash(data: dict) -> str:
    """데이터의 SHA256 해시값 계산 (재현성 보장)"""
    # JSON 정규화 (키 정렬, 공백 제거)
    normalized_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(normalized_json.encode('utf-8')).hexdigest()

def calculate_file_hash(file_path: str) -> str:
    """파일의 SHA256 해시값 계산"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()
```

---

## 7. 구현 우선순위 및 타임라인

### 7.1 Phase별 구현 계획

#### **Phase 0: 환경 구축 (2일)**
1. **NSGA-II Docker 이미지 구축**
   - GitHub 클론 및 의존성 설치
   - Dockerfile 작성 및 이미지 빌드
   - 로컬 테스트 실행 검증

2. **OutputSpec 매핑 정의**
   - 시뮬레이터 출력 형식 분석
   - QueryGoal outputSpec 매핑 로직 설계
   - 계산 알고리즘 (tardiness, sla_met) 구현

#### **Phase 1: 핵심 인프라 (4일)**
1. **MetaData.json 및 bindings.yaml 파서**
   - 스키마 정의 및 검증 로직
   - URI 템플릿 치환 엔진
   - 데이터 소스 매핑 로직

2. **ScenarioComposer 구현**
   - 동적 Submodel 생성/관리
   - 다중 소스 데이터 수집
   - 복잡한 데이터 결합 정책 적용

3. **API 계층 업데이트**
   - QueryGoal 스키마 구현
   - Goal 3 분기 라우팅
   - 에러 처리 및 응답 매핑

#### **Phase 2: 시뮬레이터 통합 (3일)**
1. **ExecutionAgent 리팩토링**
   - K8s Job 기반 컨테이너 실행
   - PVC 마운트 및 파일 전달
   - 시뮬레이터 결과 수집

2. **결과 매핑 및 검증**
   - 시뮬레이터 출력 파싱
   - OutputSpec 형식 변환
   - 에러 상황 처리

#### **Phase 3: 검증 및 완성 (2일)**
1. **E2E 테스트**
   - 전체 파이프라인 테스트
   - 다양한 시나리오 검증
   - 성능 및 안정성 확인

2. **manifest.json 로깅**
   - 완전한 실행 이력 기록
   - 재현성 보장 검증
   - 감사 추적 기능

### 7.2 성공 측정 지표

#### **기능적 요구사항**
- [ ] QueryGoal → 시나리오 생성 → NSGA-II 실행 → 결과 반환 (전체 파이프라인)
- [ ] 6개 JSON 파일 정확한 생성 및 시뮬레이터 입력
- [ ] 시뮬레이터 결과의 정확한 outputSpec 매핑
- [ ] manifest.json 기반 완전한 실행 이력 추적
- [ ] 기존 Goal 1,2,4 기능 무영향 유지

#### **비기능적 요구사항**
- [ ] 시나리오 합성 시간 < 1분 (논문 실험 수준)
- [ ] 시뮬레이터 실행 시간 < 5분 (기본 시나리오 기준)
- [ ] K8s Job 실행 성공률 > 95%
- [ ] Docker Desktop 환경에서 안정적 동작

#### **품질 요구사항**
- [ ] 모든 입력 데이터 스키마 검증 통과
- [ ] 동일 입력에 대한 재현 가능한 결과
- [ ] 적절한 에러 처리 및 로깅
- [ ] 논문 실험 데이터 생성 가능

---

## 8. 위험 관리 및 대응책

### 8.1 기술적 위험

#### **NSGA-II 시뮬레이터 통합**
- **위험**: 시뮬레이터 실행 실패, 결과 형식 불일치
- **대응**: 사전 충분한 로컬 테스트, 대체 알고리즘 준비

#### **동적 Submodel 생성**
- **위험**: AAS 서버 부하, Submodel 생성 실패
- **대응**: 비동기 처리, 실패 시 재시도 로직

#### **데이터 결합 복잡성**
- **위험**: 데이터 타입 불일치, 결합 정책 오류
- **대응**: 단계별 검증, 상세한 에러 로깅

### 8.2 운영적 위험

#### **AAS 서버 주소 변경**
- **위험**: 개발 중 서버 주소 변경으로 인한 연동 중단
- **대응**: 설정 파일 기반 주소 관리, 환경변수 활용

#### **SQLite 서버 미구축**
- **위험**: 시계열 데이터 소스 부재
- **대응**: 모의 데이터 생성, 파일 기반 대체 방안

### 8.3 일정 위험

#### **11일 개발 기간**
- **위험**: 요구사항 추가, 기술적 복잡성 증가
- **대응**: MVP 우선 구현, 단계별 검증

---

## 9. 결론 및 다음 단계

### 9.1 기대 효과
- **연구 목적**: 논문 실험 데이터 생성 및 알고리즘 검증 플랫폼 구축
- **기술적 성과**: 동적 시나리오 합성 아키텍처 실증
- **확장성**: 다른 Goal들로의 점진적 확장 기반 마련

### 9.2 즉시 시작 가능한 작업
1. **NSGA-II 시뮬레이터 Docker 이미지 구축** (Phase 0.1)
2. **MetaData.json 스키마 정의** (Phase 1.1)
3. **QueryGoal Pydantic 모델 구현** (Phase 1.3)

### 9.3 의존성 해결 필요사항
1. **AAS 서버 새 주소 확정** (담당자 확인)
2. **SQLite 서버 구축 일정** (담당자 확인)
3. **K8s 클러스터 PVC 설정** (개발 환경 준비)

---

*이 PRD는 담당자 피드백과 실제 NSGA-II 시뮬레이터 분석을 기반으로 작성되었으며, 논문 실험 목적에 최적화된 구현 계획을 제시합니다.*