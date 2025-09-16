
-----

### **PRD: 지능형 공장 자동화 시스템 2.0 - 시나리오 합성 기반 예측 및 최적화**

  * **문서 버전:** 2.0 (Final)
  * **작성일:** 2025년 9월 16일
  * **작성자:** Gemini
  * **상태:** 실행 승인

### **0. 개요 (Overview)**
기본 코드 베이스 : https://github.com/WAFriend3416/factory-automation-k8s/tree/goal3-implementation-detail
NSGA 시뮬레이터 깃헙 : https://github.com/Otober/AASX
전달 받은 요구사항 원본 : new-requirement 폴더
    - new-requirement/my_case : NSGA 시뮬레이터 입력 파일 예시.

### **1. 개요 (Overview)**

#### **1.1. 배경 (Background)**

현재 공장 자동화 시스템의 정적 실행 계획 방식에서 벗어나, \*\*재현성과 추적성이 보장되는 실행 시나리오를 동적으로 합성(Synthesis)\*\*하는 고도화된 아키텍처로 전환합니다. 이 시스템은 `QueryGoal` 명세를 입력받아, AAS(Asset Administration Shell) 서버에 저장된 **현재 데이터를 최대한 활용**하여 **NSGA-II 최적화 시뮬레이터**의 입력 파일셋을 동적으로 생성하고 실행하는 것을 목표로 합니다.

#### **1.2. 목표 (Goals)**

1.  **시나리오 합성 아키텍처 도입**: `QueryGoal`, `MetaData`, `bindings.yaml`을 기반으로 동적으로 실행 시나리오를 생성하는 **시나리오 합성(Scenario Synthesis)** 아키텍처를 구현합니다.
2.  **NSGA-II 시뮬레이터 통합**: Goal 3의 실행 엔진을 고성능 NSGA-II 시뮬레이터로 교체하여 예측 및 최적화 성능을 강화합니다.
3.  **하이브리드 AAS 데이터 전략 채택**: 기존 AAS 데이터를 최대한 활용하고, 정적 시나리오 데이터와 동적 실시간 데이터를 분리하여 관리하는 효율적인 데이터 모델을 적용합니다.
4.  [cite\_start]**재현성 및 추적성 확보**: 모든 시나리오 합성 과정의 입력과 결과물을 `manifest.json`으로 기록하여 감사 및 재현이 가능한 시스템을 구축합니다. [cite: 1862-1898]

#### **1.3. 범위 (Scope)**

  * **In-Scope:**
      * \*\*Goal 3 (`predict_job_completion_time`)\*\*을 새로운 시나리오 합성 아키텍처의 **최초 적용 대상**으로 합니다.
      * API 서버(`api/`), 실행 엔진(`execution_engine/`)의 설계 및 구현 변경.
      * NSGA-II 시뮬레이터를 위한 신규 Docker 이미지 생성 및 쿠버네티스 Job 연동.
      * AAS 표준 서버 연동을 위한 `AASQueryClient`의 활용 강화.
  * **Out-of-Scope:**
      * Goal 1, 2, 4는 기존 실행 방식을 유지합니다. (단, 향후 새로운 아키텍처로 마이그레이션할 수 있도록 구조적으로 고려합니다.)
      * 본격적인 SWRL/SHACL 추론 엔진(Reasoner)의 도입. (요구사항 문서에 명시된 규칙의 '의미'를 Python 코드로 구현하는 데 집중합니다.)
      * 사용자 인터페이스(UI) 개발.

-----

### **2. 통합 아키텍처 (Integrated Architecture)**

개선된 시스템은 \*\*시나리오 합성기(Scenario Composer)\*\*를 중심으로 데이터를 처리하며, 전체 데이터 흐름은 다음과 같습니다.

1.  **API 계층 (API Layer)**: 사용자의 `QueryGoal` 요청을 접수하고 **시나리오 합성기**에 전달합니다.
2.  **시나리오 합성기 (Scenario Composer)**: `QueryGoal`, `MetaData`, `bindings.yaml`을 조합하여 NSGA-II 시뮬레이터가 요구하는 **실행 가능한 시나리오 파일셋과 실행 명세(manifest)를 동적으로 생성**합니다.
3.  **실행 에이전트 (Execution Agent)**: 합성된 시나리오를 입력받아 쿠버네티스 Job으로 NSGA-II 시뮬레이터를 실행하고 결과를 모니터링합니다.
4.  **AAS 데이터 계층 (AAS Data Layer)**: 모든 정보의 진실의 원천(Source of Truth) 역할을 하며, `ScenarioComposer`의 데이터 조회 대상이 됩니다.

-----

### **3. AAS 데이터 활용 및 변환 전략 (Hybrid AAS Data Strategy)**
#### [필수! aas-server-data.md 참조] : PRD 와 다르게 구현되지 않았거나 아직 준비 되지 않은 서브모델(엔드포인트)등이 있을 수 있음.
본 시스템은 **기존 AAS 데이터 모델을 최대한 활용**하여 NSGA-II 시뮬레이터가 요구하는 입력 파일셋을 동적으로 생성합니다. 이 과정의 책임은 \*\*`ScenarioComposer`\*\*에 있으며, 각 시뮬레이터 입력 파일에 대한 데이터 소스와 변환/조합 로직은 다음과 같습니다.

| 시뮬레이터 입력 파일 | 데이터 성격 | AAS 데이터 소스 (Submodel) | `ScenarioComposer`의 구체적인 변환/조합 로직 (지시사항) |
| :--- | :--- | :--- | :--- |
| **`jobs.json`** | 정적 | **(신규)** `Scenario_Jobs` | 1. `bindings.yaml`에 명시된 `urn:factory:aas:scenario:...?/Jobs` Submodel을 조회합니다.\<br\>2. `Content` Property의 `value`(JSON 문자열)를 파싱하여 `jobs.json` 파일로 저장합니다. |
| **`operations.json`** | 정적 | **(신규)** `Scenario_Operations` | 위 `jobs.json`과 동일한 방식으로 `Scenario_Operations` Submodel에서 데이터를 가져와 파일로 저장합니다. |
| **`operation_durations.json`** | 정적 | **(신규)** `Scenario_OperationDurations` | 위와 동일한 방식으로 `Scenario_OperationDurations` Submodel에서 데이터를 가져와 파일로 저장합니다. |
| **`machine_transfer_time.json`**| 정적 | **(신규)** `Scenario_MachineTransferTime` | 위와 동일한 방식으로 `Scenario_MachineTransferTime` Submodel에서 데이터를 가져와 파일로 저장합니다. |
| **`job_release.json`** | 정적 | **(신규)** `Scenario_JobRelease` | 위와 동일한 방식으로 `Scenario_JobRelease` Submodel에서 데이터를 가져와 파일로 저장합니다. |
| **`machines.json`** | **동적** | 각 설비 AAS의 `TechnicalData` & `OperationalData` | 1. 시뮬레이션에 필요한 모든 설비 ID 목록(`M1`, `M2`...)을 식별합니다.\<br\>2. **(Loop)** 각 설비 ID에 대해 `technical_data`와 `operational_data` Submodel을 모두 조회합니다.\<br\>3. 두 Submodel의 정보를 조합하여 `machines.json`이 요구하는 `status`, `next_available_time` 등의 필드를 채워 파일을 생성합니다. |

-----

### **4. 구현 명세 (Implementation Specification)**
#### [필수! process-criteria.md 참조]
#### **4.1. API 계층 (`api/`)**

  * **`schemas.py`**: 기존 `DslRequest`를 `QueryGoal.json` 명세에 맞춘 새로운 Pydantic 모델로 교체해야 합니다. `QueryGoal`의 복잡한 중첩 구조를 정확히 반영해야 합니다.
  * **`main.py`**: `/execute-goal` 엔드포인트에서 `goalType`이 `predict_job_completion_time`일 경우, `ExecutionPlanner` 대신 새로운 `ScenarioComposer`를 호출하도록 분기 로직을 추가해야 합니다.

#### **4.2. 실행 엔진 (`execution_engine/`)**

  * **`planner.py` ➡️ `composer.py` (신규 생성 또는 전면 리팩토링)**
      * **`ScenarioComposer` 클래스 구현 지시사항**:
          * 이 클래스는 **3번 항목의 표에 정의된 하이브리드 데이터 전략을 수행**하는 책임을 가집니다.
          * `compose(goal: QueryGoal)` 메서드는 AAS 서버에 여러 번 쿼리를 수행하여 데이터를 수집하고, 인메모리(in-memory)에서 조합/변환하여 최종 시뮬레이터 입력 파일셋을 생성 후 PVC에 저장해야 합니다.
          * `_validate_scenario()` 와 `_create_manifest()` 메서드를 구현하여 시나리오 검증 및 재현성 보장 기능을 포함해야 합니다.
      * **유의사항**: AAS 데이터 조회 실패, 필수 데이터 누락 등 예외 상황에 대한 에러 처리 및 로깅 로직을 견고하게 구현해야 합니다.
  * **`agent.py`**:
      * **지시사항**: `ExecutionAgent.run()` 메서드의 인자를 `plan`(Action 목록) 대신, `scenario_path`와 `container_image`를 받도록 수정합니다.
      * **지시사항**: `EnhancedDockerRunHandler`의 데이터 처리 관련 로직은 모두 제거하고, 전달받은 `scenario_path`를 K8s Job의 볼륨 마운트로 설정하는 역할에 집중하도록 리팩토링합니다.

#### **4.3. 온톨로지 (`ontology/`)**

  * **`factory_ontology_v2_final_corrected.ttl`**:
      * **지시사항**: Goal 3의 `:hasActionSequence`를 구체적인 데이터 처리 단계 대신, `:ActionComposeScenario`, `:ActionExecuteScenario`, `:ActionProcessResults` 와 같은 추상적인(High-level) 단계로 수정합니다.

#### **4.4. Docker & Kubernetes**

  * **`Dockerfile.nsga_simulator` (신규 파일)**:
      * **지시사항**: NSGA-II 시뮬레이터 GitHub 저장소를 기반으로 Docker 이미지를 생성합니다.
  * **K8s Job**:
      * **지시사항**: `ScenarioComposer`가 생성한 시나리오 폴더를 컨테이너 내부로 마운트하도록 Job 명세를 동적으로 생성해야 합니다.

#### **4.5. 진행 상황 로깅**

  * **지시사항**: 각 주요 단계(요청 접수, 합성 시작, 검증 완료, 실행 시작, 완료)의 상태와 타임스탬프를 로그로 기록하고, 이를 `goalId`와 연결하여 추적할 수 있는 체계를 구축합니다. 
  **(권장: AAS의 `ExecutionStatus` Submodel 활용)** : 해당 서브모델이 구현되어 있지 않을 가능성이 염두해두기 바람.
  


-----

### **5. 단계별 구현 계획 (Phased Implementation Plan)**

1.  **Phase 1: 기반 구축**
      * **Task 1.1**: API 스키마 변경 (`schemas.py`).
      * **Task 1.2**: NSGA-II 시뮬레이터용 Docker 이미지 빌드 및 로컬 테스트 완료.
2.  **Phase 2: 핵심 로직 구현**
      * **Task 2.1**: `ScenarioComposer` 클래스 구현. **3번 항목의 표에 명시된 모든 변환/조합 로직을 구현**하는 것이 이 단계의 핵심.
      * **Task 2.2**: `ExecutionAgent` 및 `EnhancedDockerRunHandler`를 리팩토링하여 `ScenarioComposer`와 연동.
3.  **Phase 3: 검증 및 고도화**
      * **Task 3.1**: `_validate_scenario` (스키마/규칙 검증) 및 `_create_manifest` (재현성) 로직 구현.
      * **Task 3.2**: 종단 간(End-to-End) 테스트 케이스 작성 및 전체 시스템 검증.
      * **Task 3.3**: 단계별 진행 상황 로깅 기능 구현.


-----

### **6. 검증 및 테스트 계획 (Verification & Testing Plan)**

  * **단위 테스트**: `ScenarioComposer`의 각 데이터 조합/변환 로직에 대한 테스트 케이스를 작성 (예: `ProcessData`를 `operation_durations.json`으로 올바르게 변환하는지).
  * **통합 테스트**: AAS 서버에 테스트 데이터를 입력한 후, API를 통해 `QueryGoal`을 요청했을 때, 올바른 시나리오 파일셋이 PVC에 생성되고 K8s Job이 성공적으로 실행되는지 검증.
  * **재현성 테스트**: 동일한 AAS 데이터 상태에서 `ScenarioComposer`를 여러 번 실행했을 때, 생성되는 `manifest.json`의 해시값이 동일하게 유지되는지 검증.

