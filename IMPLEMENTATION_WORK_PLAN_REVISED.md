# 지능형 공장 자동화 시스템 2.0 구현 작업 계획 (수정판)

**작성일**: 2025-09-17  
**수정 기준**: 담당자 피드백 및 NSGA-II 시뮬레이터 실제 분석 결과 반영  
**목표**: Goal 3 시나리오 합성 아키텍처 구현 및 논문 실험용 시스템 구축

---

## 📋 프로젝트 개요

### 담당자 피드백 반영사항
1. **외부 AAS 서버**: 주소 변경 예정, 인증 불필요, 시나리오별 Submodel 생성
2. **SQLite 서버**: AAS 서버 옆에서 시계열 데이터 폴링용으로 구축 예정
3. **NSGA-II 시뮬레이터**: Public GitHub, Docker 컨테이너화 (pandas 의존성 포함)
4. **논문 실험 목적**: 프로덕션 배포가 아닌 연구 실험용 시스템
5. **핵심 파이프라인**: QueryGoal 입력 → 시나리오 생성 → 검증 → 실행 → 결과 반환

### NSGA-II 시뮬레이터 실제 분석 결과
- **저장소**: https://github.com/Otober/AASX (Public)
- **실행 방법**: `python3 simulator/main.py --scenario scenarios/my_case`
- **의존성**: pandas, numpy, openpyxl 필요
- **입력 파일**: 6개 JSON (initial_machine_status.json은 레거시 제외)
- **출력**: simulator_optimization_result.json (best_objective, search_time 등)

---

## 🎯 수정된 구현 로드맵

### Phase 0: 환경 구축 및 시뮬레이터 분석 (2일)

#### 🔍 **Task 0.1: NSGA-II 시뮬레이터 Docker 이미지 구축**
- **기반**: https://github.com/Otober/AASX 분석 완료
- **작업 내용**:
  ```dockerfile
  FROM python:3.9-slim
  RUN pip install pandas numpy openpyxl
  COPY /tmp/nsga-analysis /opt/nsga-simulator
  WORKDIR /opt/nsga-simulator
  ENTRYPOINT ["python3", "simulator/main.py"]
  ```
- **성공 기준**:
  - [ ] Docker 이미지 빌드 및 로컬 테스트 성공
  - [ ] 6개 입력 JSON 파일로 시뮬레이터 정상 실행
  - [ ] simulator_optimization_result.json 출력 확인

#### 📊 **Task 0.2: QueryGoal OutputSpec 시뮬레이터 매핑 정의**
- **작업 내용**: 시뮬레이터 출력을 QueryGoal outputSpec에 맞게 매핑
- **매핑 정의**:
  ```json
  {
    "completion_time": "best_objective",  // makespan을 완료시간으로
    "tardiness_s": "calculated_tardiness", // 별도 계산 로직 필요
    "sla_met": "sla_compliance_check"     // 별도 검증 로직 필요
  }
  ```
- **성공 기준**:
  - [ ] 시뮬레이터 출력 → QueryGoal 응답 변환 로직 완성
  - [ ] 모든 outputSpec 필드 매핑 완료

#### 🗄️ **Task 0.3: AAS 데이터 모델 및 SQLite 연동 설계**
- **작업 내용**:
  - 동적 시나리오별 Submodel 구조 설계
  - SQLite 시계열 데이터 스키마 정의
  - 하이브리드 데이터 수집 전략 구체화
- **성공 기준**:
  - [ ] Scenario_{scenario_id}_* Submodel 네이밍 규칙 정의
  - [ ] SQLite machine_states 테이블 스키마 완성
  - [ ] 정적/동적 데이터 분류 및 수집 방법 문서화

---

### Phase 1: 핵심 인프라 구현 (4일)

#### 🏗️ **Task 1.1: MetaData.json 및 bindings.yaml 구조 구현**
- **MetaData.json 구조**:
  ```json
  {
    "modelId": "JobETAModel_v1.4.2",
    "requiredInputs": ["JobRoute", "MachineState", "Calendar", "SetupMatrix", "WIP", "Backlog"],
    "bindings": "bindings_goal3.yaml",
    "simulator": {
      "container_image": "nsga-simulator:latest",
      "timeout_seconds": 300
    },
    "outputMapping": {
      "completion_time": "best_objective",
      "tardiness_s": "calculated.tardiness",
      "sla_met": "validation.sla_compliance"
    }
  }
  ```

- **bindings.yaml 구조**:
  ```yaml
  sources:
    JobRoute:
      type: "aas"
      uri: "aas://FactoryTwin/Scenario_{scenario_id}_JobRoute_{jobId}"
      extract: "Content"
      
    MachineState:
      type: "timeseries"
      uri: "sqlite://machine_states"
      query: "SELECT * FROM machine_status WHERE timestamp <= ? ORDER BY timestamp DESC"
      params: ["{bindAt}"]
      
    WIP:
      type: "file"
      path: "/data/wip/*.json"
      glob:
        sort: ["mtime:desc"]
        window: { count: 5 }
      combine:
        op: "overlay"
        key: "partId"
        
    Calendar:
      type: "static"
      content: |
        {
          "working_hours": {"start": "09:00", "end": "18:00"},
          "holidays": ["2025-01-01", "2025-12-25"]
        }
  ```

- **성공 기준**:
  - [ ] MetaData.json 파싱 및 검증 로직 완성
  - [ ] bindings.yaml 파서 구현 (URI 템플릿, glob 처리)
  - [ ] 데이터 결합 정책 (overlay, concat, latest) 구현

#### 🔄 **Task 1.2: ScenarioComposer 핵심 로직 구현**
- **파일**: `execution_engine/scenario_composer.py`
- **핵심 기능**:
  ```python
  class ScenarioComposer:
      def compose(self, query_goal: QueryGoal) -> ScenarioResult:
          # 1. 매크로 치환 (@현재시간 → ISO timestamp)
          # 2. MetaData.json 로드
          # 3. 동적 Submodel 생성
          # 4. bindings.yaml 기반 데이터 수집
          # 5. 데이터 결합 및 6개 JSON 파일 생성
          # 6. manifest.json 생성
          
      def _resolve_macros(self, query_goal):
          """@현재시간 등 매크로를 실제 값으로 치환"""
          
      def _create_dynamic_submodels(self, scenario_id, job_id):
          """시나리오별 전용 Submodel 생성"""
          
      def _collect_data_sources(self, bindings_config):
          """bindings.yaml 기반 다중 소스 데이터 수집"""
          
      def _combine_data(self, sources, combine_policy):
          """overlay/concat/latest 정책에 따른 데이터 결합"""
          
      def _generate_simulator_files(self, combined_data):
          """NSGA-II 시뮬레이터용 6개 JSON 파일 생성"""
  ```

- **성공 기준**:
  - [ ] 전체 compose() 파이프라인 구현 완료
  - [ ] 동적 Submodel 생성/관리 기능 완성
  - [ ] 6개 시뮬레이터 입력 파일 정확한 생성

#### 🚀 **Task 1.3: API 계층 업데이트**
- **파일**: `api/schemas.py`, `api/main.py`
- **작업 내용**:
  - QueryGoal Pydantic 모델 구현
  - Goal 3 전용 라우팅 로직 추가
  - ScenarioComposer 연동
- **성공 기준**:
  - [ ] `/execute-goal` 엔드포인트에서 Goal 3 분기 처리
  - [ ] QueryGoal 스키마 검증 완료
  - [ ] 기존 Goal 1,2,4 기능 무영향 확인

---

### Phase 2: 시뮬레이터 통합 및 실행 (3일)

#### 🐳 **Task 2.1: ExecutionAgent Docker 실행 로직 구현**
- **파일**: `execution_engine/agent.py`
- **작업 내용**:
  - K8s Job으로 NSGA-II 시뮬레이터 컨테이너 실행
  - PVC 마운트를 통한 시나리오 파일 전달
  - 시뮬레이터 결과 파일 수집
- **성공 기준**:
  - [ ] K8s Job 생성 및 PVC 마운트 설정
  - [ ] 시뮬레이터 컨테이너 정상 실행
  - [ ] simulator_optimization_result.json 수집 완료

#### 📤 **Task 2.2: 결과 매핑 및 응답 처리 구현**
- **작업 내용**:
  - 시뮬레이터 출력을 QueryGoal outputSpec 형식으로 변환
  - 에러 처리 및 상태 관리
  - manifest.json 업데이트
- **성공 기준**:
  - [ ] completion_time, tardiness_s, sla_met 계산 완료
  - [ ] API 응답 형식 OutputSpec 준수
  - [ ] 실행 과정 manifest.json에 완전 기록

---

### Phase 3: 검증 및 완성 (2일)

#### ✅ **Task 3.1: 종단간(E2E) 테스트 구현**
- **테스트 시나리오**:
  ```python
  def test_goal3_e2e():
      # 1. QueryGoal 요청 전송
      # 2. 시나리오 합성 확인
      # 3. 동적 Submodel 생성 검증
      # 4. NSGA-II 시뮬레이터 실행
      # 5. 결과 매핑 및 응답 검증
      # 6. manifest.json 생성 확인
  ```
- **성공 기준**:
  - [ ] 전체 파이프라인 무중단 실행
  - [ ] 각 단계별 결과물 검증 통과
  - [ ] 에러 시나리오 적절한 처리

#### 📊 **Task 3.2: 시나리오 검증 및 로깅 시스템**
- **작업 내용**:
  - JSON 스키마 기반 시나리오 파일 검증
  - manifest.json 로깅 시스템 완성
  - 재현성 보장을 위한 해시 계산
- **성공 기준**:
  - [ ] 6개 JSON 파일 스키마 검증 완료
  - [ ] manifest.json 완전한 실행 이력 기록
  - [ ] 동일 입력에 대한 해시값 일관성 확인

---

## 🔧 구현 세부사항

### 동적 Submodel 생성 전략
```python
def create_scenario_submodels(self, scenario_id: str, job_id: str):
    """각 시나리오마다 전용 Submodel 생성"""
    submodel_templates = {
        f"Scenario_{scenario_id}_Jobs": {
            "elements": [{"idShort": "Content", "value": ""}]
        },
        f"Scenario_{scenario_id}_Operations": {
            "elements": [{"idShort": "Content", "value": ""}]
        },
        f"Scenario_{scenario_id}_JobRoute_{job_id}": {
            "elements": [{"idShort": "RouteSequence", "value": ""}]
        },
        # ... 기타 필요한 Submodel들
    }
    
    for submodel_name, config in submodel_templates.items():
        self.aas_client.create_submodel(submodel_name, config)
```

### 복잡한 데이터 결합 정책
```python
class DataCombiner:
    def combine_data(self, sources: List[dict], policy: dict) -> dict:
        if policy["op"] == "overlay":
            return self._overlay_combine(sources, policy.get("key"))
        elif policy["op"] == "concat":
            return self._concat_combine(sources)
        elif policy["op"] == "latest":
            return self._latest_combine(sources)
            
    def _overlay_combine(self, sources, key_field):
        """나중 데이터가 먼저 데이터를 덮어씀 (last-wins)"""
        result = {}
        for source in sources:
            for item in source:
                if key_field:
                    result[item[key_field]] = item
                else:
                    result.update(item)
        return list(result.values()) if key_field else result
```

### manifest.json 시나리오 로깅
```json
{
  "scenario_id": "goal3_20250917_143052",
  "timestamp": "2025-09-17T14:30:52+09:00",
  "query_goal": {
    "hash": "sha256:abc123...",
    "job_id": "JOB-7f2e3a8b-1d",
    "goal_type": "predict_job_completion_time"
  },
  "data_sources": {
    "JobRoute": {
      "type": "aas",
      "submodel": "Scenario_goal3_20250917_143052_JobRoute_JOB-7f2e3a8b-1d",
      "hash": "sha256:def456...",
      "collected_at": "2025-09-17T14:30:53+09:00"
    },
    "MachineState": {
      "type": "timeseries",
      "source": "sqlite://machine_states",
      "records_count": 15,
      "hash": "sha256:789abc..."
    }
  },
  "simulator_execution": {
    "container_image": "nsga-simulator:latest",
    "start_time": "2025-09-17T14:31:00+09:00",
    "end_time": "2025-09-17T14:31:45+09:00",
    "exit_code": 0,
    "result_files": ["simulator_optimization_result.json", "trace.xlsx"]
  },
  "output_mapping": {
    "completion_time": 15.2,
    "tardiness_s": 0,
    "sla_met": true
  },
  "reproducibility": {
    "aas_server_version": "v2.1.0",
    "system_timestamp": "2025-09-17T14:30:52+09:00"
  }
}
```

---

## 📊 품질 관리

### 포함 기능 (담당자 요청)
- ✅ **MetaData.json 활용**: requiredInputs 기반 데이터 수집
- ✅ **bindings.yaml 구조**: URI 템플릿, glob, 결합 정책 지원
- ✅ **동적 Submodel 생성**: 시나리오별 전용 Submodel 관리
- ✅ **복잡한 데이터 결합**: overlay, concat, latest 정책 구현
- ✅ **manifest.json 로깅**: 완전한 실행 이력 및 재현성 보장

### 제외/단순화 기능
- ❌ **SWRL/SHACL 추론 엔진**: 하드코딩된 규칙으로 대체
- ❌ **성능 최적화**: 논문 실험 목적으로 기능 우선
- ❌ **복잡한 에러 복구**: 기본 에러 처리만
- ❌ **API 버전 관리**: 단일 버전만 지원
- ❌ **인증/인가**: 개발 환경에서 제외

---

## 📅 수정된 타임라인

| Phase | 기간 | 핵심 산출물 | 검증 기준 |
|-------|------|------------|----------|
| **Phase 0** | 2일 | NSGA-II Docker 이미지, OutputSpec 매핑 | 시뮬레이터 로컬 실행 성공 |
| **Phase 1** | 4일 | ScenarioComposer, bindings.yaml 파서 | 6개 JSON 파일 정확한 생성 |
| **Phase 2** | 3일 | Docker 실행, 결과 매핑 | K8s Job 시뮬레이터 실행 성공 |
| **Phase 3** | 2일 | E2E 테스트, manifest 로깅 | 전체 파이프라인 동작 검증 |
| **총 기간** | **11일** | **논문 실험용 시스템 완성** | **QueryGoal → 결과 반환** |

---

## 🎯 성공 측정 지표

### 논문 실험 요구사항 충족
- [ ] **QueryGoal 입력 → 시나리오 생성 → 검증 → 실행 → 결과 반환** 파이프라인 완전 동작
- [ ] NSGA-II 시뮬레이터 정상 통합 및 결과 매핑
- [ ] 동적 시나리오별 Submodel 생성 및 관리
- [ ] manifest.json 기반 완전한 실행 이력 추적
- [ ] 기존 Goal 1,2,4 기능 무영향 유지

### 실용성 지표
- [ ] 시나리오 합성 시간 < 1분 (논문 실험용)
- [ ] 시뮬레이터 실행 시간 < 5분 (기본 시나리오 기준)
- [ ] 에러 상황 적절한 처리 및 로깅
- [ ] Docker Desktop K8s 환경에서 안정적 동작

---

## 📝 다음 단계 및 우선순위

1. **즉시 시작 가능**: Phase 0 Task 0.1 (NSGA-II Docker 이미지 구축)
2. **병렬 작업**: MetaData.json 구조 설계와 bindings.yaml 파서 개발
3. **의존성 해결**: SQLite 서버 스키마 정의 (AAS 서버 옆 구축 예정)
4. **검증 우선**: 각 Phase 완료 후 즉시 E2E 테스트 실행

---

*이 수정된 계획은 담당자 피드백과 실제 NSGA-II 시뮬레이터 분석 결과를 반영하여 작성되었으며, 논문 실험 목적에 최적화되었습니다.*