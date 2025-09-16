네, 알겠습니다. 각 단계별 **진행 여부를 판단할 수 있는 명확한 기준**을 담은 프로세스 기준 PRD를 작성해 드리겠습니다.

이 문서는 개발팀이 각 단계의 **완료 조건(Exit Criteria)**을 명확히 인지하고, 어떤 산출물이 나와야 다음 단계로 넘어갈 수 있는지에 대한 **"게이트(Gate)"** 역할을 하도록 설계되었습니다.

---

### **PRD: 지능형 공장 자동화 시스템 2.0 - 단계별 프로세스 기준 및 진행 조건**

* **문서 버전:** 1.2
* **작성일:** 2025년 9월 16일
* **작성자:** Gemini
* **관련 문서:** 지능형 공장 자동화 시스템 2.0 PRD

### **1. 개요 (Overview)**

#### **1.1. 문서의 목적**

본 문서는 `QueryGoal` 요청이 접수된 후 최종 결과가 반환되기까지의 전체 프로세스를 여러 단계로 나누고, 각 단계의 **▲입력(Inputs), ▲수행 작업(Tasks), ▲산출물(Deliverables), ▲다음 단계 진행 조건(Success Criteria)**을 명확히 정의합니다. 이를 통해 개발자는 각 모듈의 책임과 완료 기준을 명확히 이해하고, 시스템의 안정성과 신뢰성을 확보할 수 있습니다.

#### **1.2. 전체 프로세스 흐름**



**[1. 요청 접수 및 검증] ➡️ [2. 시나리오 합성] ➡️ [3. 시나리오 증명 및 검사] ➡️ [4. 시나리오 실행] ➡️ [5. 결과 처리 및 반환]**

---

### **2. 단계별 상세 명세**

#### **단계 1: 요청 접수 및 검증 (Request Reception & Validation)**

* **주요 컴포넌트**: `api/main.py`, `api/schemas.py`
* **입력**: 외부로부터의 HTTP POST 요청 (JSON Body 포함)
* **수행 작업**:
    1.  `/execute-goal` 엔드포인트에서 HTTP 요청을 수신합니다.
    2.  Pydantic 모델을 사용하여 요청 Body가 `QueryGoal` 스키마를 준수하는지 검증합니다.
* **산출물**:
    * 내부 시스템에서 사용할 수 있는, 유효성이 검증된 `QueryGoal` Pydantic 객체.
* **✅ 다음 단계 진행 조건 (Success Criteria)**:
    * **모든 조건이 `True`여야 통과**
    * `QueryGoal.json`의 문법이 올바른가? (JSON-parsable)
    * Pydantic 스키마 검증을 통과했는가? (모든 필수 필드 존재 및 데이터 타입 일치)
    * **[실패 시]**: 위 조건 미충족 시, 프로세스를 즉시 중단하고 클라이언트에게 HTTP `400 Bad Request` 또는 `422 Unprocessable Entity` 오류를 반환합니다.

---

#### **단계 2: 시나리오 합성 (Scenario Composition)**

* **주요 컴포넌트**: `ScenarioComposer` (`execution_engine/composer.py`)
* **입력**: 1단계를 통과한 `QueryGoal` Pydantic 객체.
* **수행 작업**:
    1.  `@현재시간`과 같은 매크로를 실제 시간 값으로 치환합니다.
    2.  `MetaData.json`을 로드하여 `requiredInputs` 목록을 확보합니다.
    3.  `bindings.yaml` 규칙에 따라 각 `requiredInputs`에 대한 데이터를 AAS 서버 또는 파일 시스템에서 수집합니다.
    4.  `combine` 정책(`overlay`, `concat`)에 따라 수집된 데이터를 병합합니다.
    5.  NSGA-II 시뮬레이터가 요구하는 형식의 시나리오 파일셋(`jobs.json` 등)을 생성하여 PVC 내 고유 폴더에 저장합니다.
* **산출물**:
    * PVC에 저장된 시나리오 파일셋 (예: `/data/scenarios/goal-job-eta-0001/`).
* **✅ 다음 단계 진행 조건 (Success Criteria)**:
    * **모든 조건이 `True`여야 통과**
    * `MetaData.json` 로드에 성공했으며, `requiredInputs` 목록을 정상적으로 확보했는가?
    * `bindings.yaml`에 `requiredInputs`의 모든 항목에 대한 규칙이 존재하는가?
    * 규칙에 명시된 모든 AAS 데이터 조회 및 파일 시스템 접근이 성공했는가? (HTTP 404, File Not Found 등 오류 없음)
    * 모든 시나리오 파일(`jobs.json` 등)이 PVC에 성공적으로 저장되었는가?
    * **[실패 시]**: 위 조건 미충족 시, 프로세스를 중단하고 AAS `ExecutionStatus` Submodel에 `'Failed'` 상태와 함께 실패 원인(예: `BindingError: Input 'WIP' source not found`)을 기록합니다.

---

#### **단계 3: 시나리오 증명 및 검사 (Scenario Verification & Inspection)**

* **주요 컴포넌트**: `ScenarioComposer` 또는 별도의 `Validator` 모듈
* **입력**: 2단계에서 생성된 시나리오 파일셋의 PVC 경로.
* **수행 작업**:
    1.  생성된 시나리오 파일들에 대해 **1차 스키마(Schema) 검증**을 수행합니다.
    2.  스키마 검증 통과 시, **2차 제약 조건(SHACL 등) 검증**을 수행합니다.
    3.  모든 검증 통과 시, 입력 데이터와 산출물의 해시값을 포함하는 **`manifest.json`을 생성**합니다.
* **산출물**:
    * 유효성이 증명된 시나리오 파일셋.
    * 시나리오의 재현성을 보장하는 `manifest.json` 파일.
* **✅ 다음 단계 진행 조건 (Success Criteria)**:
    * **모든 조건이 `True`여야 통과**
    * 모든 시나리오 파일이 미리 정의된 JSON 스키마 검증을 통과했는가?
    * `MetaData.json`의 `requiredInputs`와 실제 생성된 시나리오의 입력 데이터가 일치하는가? (SHACL 제약 조건 검증)
    * `manifest.json`이 성공적으로 생성되었는가?
    * **[실패 시]**: 위 조건 미충족 시, 프로세스를 중단하고 `ExecutionStatus`에 `'Failed'` 상태와 함께 구체적인 검증 실패 사유(예: `ValidationError: Scenario does not conform to schema. Missing key 'jobs'`)를 기록합니다.

---

#### **단계 4: 시나리오 실행 (Scenario Execution)**

* **주요 컴포넌트**: `ExecutionAgent`, `EnhancedDockerRunHandler`, Kubernetes API
* **입력**: 3단계를 통과한 시나리오의 PVC 경로 및 `QueryGoal`의 컨테이너 정보.
* **수행 작업**:
    1.  `QueryGoal.selectedModel.container` 정보를 바탕으로 NSGA-II 시뮬레이터 실행을 위한 쿠버네티스 Job 명세를 생성합니다.
    2.  Job 명세에는 시나리오 파일셋이 저장된 PVC 폴더를 컨테이너로 마운트하는 설정이 포함됩니다.
    3.  생성된 Job을 쿠버네티스 API 서버에 제출하고, Pod의 상태를 모니터링합니다.
* **산출물**:
    * 쿠버네티스 클러스터에서 실행 중이거나 완료된 Job/Pod.
    * 시뮬레이션 결과 파일 (PVC 내 동일 폴더에 저장됨).
* **✅ 다음 단계 진행 조건 (Success Criteria)**:
    * **모든 조건이 `True`여야 통과**
    * 쿠버네티스 Job이 성공적으로 생성되었는가?
    * Job에 의해 생성된 Pod가 `Failed` 상태에 빠지지 않고, 최종적으로 `Succeeded` 상태로 종료되었는가?
    * PVC 경로에 예상된 결과 파일(예: `results.json`)이 생성되었는가?
    * **[실패 시]**: Pod가 `Failed`되거나 Job이 타임아웃될 경우, 프로세스를 중단하고 `ExecutionStatus`에 `'Failed'` 상태와 함께 Pod 로그에서 추출한 오류 내용을 기록합니다.

---

#### **단계 5: 결과 처리 및 반환 (Result Processing & Response)**

* **주요 컴포넌트**: `ExecutionAgent`
* **입력**: PVC에 저장된 시뮬레이션 결과 파일, 원본 `QueryGoal` 객체.
* **수행 작업**:
    1.  PVC에서 시뮬레이션 결과 파일을 읽어옵니다.
    2.  결과 데이터를 `QueryGoal.outputSpec`에 정의된 형식에 맞게 가공/매핑합니다.
    3.  (선택) 최종 결과를 AAS 서버의 관련 Submodel(예: `JobRoute`의 예측 결과 필드)에 업데이트합니다.
    4.  사용자에게 반환할 최종 API 응답을 생성합니다.
* **산출물**:
    * 사용자에게 반환되는 최종 JSON 응답.
    * (선택) 결과가 업데이트된 AAS Submodel.
* **✅ 프로세스 종료 조건**:
    * **모든 조건이 `True`여야 성공**
    * 결과 파일을 성공적으로 파싱했는가?
    * `outputSpec`에 명시된 모든 필드를 성공적으로 생성했는가?
    * 사용자에게 HTTP `200 OK`와 함께 최종 응답을 성공적으로 전송했는가?
    * **[성공 시]**: `ExecutionStatus`를 `'Completed'`로 업데이트하고 모든 프로세스를 정상 종료합니다.