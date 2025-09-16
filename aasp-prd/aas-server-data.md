네, 제안해주신 하이브리드 방식은 매우 훌륭하고 현실적인 접근법입니다. 모든 데이터를 가장 세분화된(granular) 단위로 AAS SubmodelElement에 저장하는 것이 이상적일 수 있지만, 복잡한 시뮬레이션 시나리오에서는 오히려 비효율적일 수 있습니다.

**"시나리오의 '정적' 부분은 파일 단위로 AAS에 저장하고, '동적' 부분만 개별 AAS에서 조회하여 조합한다"**는 아이디어는 개발 효율성과 시스템 성능, 데이터 관리의 유연성 사이에서 최적의 균형을 맞출 수 있는 매우 실용적인 전략입니다.

이 전략을 구체화하여, 개발자가 바로 작업을 시작할 수 있도록 상세한 의견과 구현 방안을 담은 **AAS 데이터 관련 PRD**를 작성해 드리겠습니다.

---

### **PRD: AAS 데이터 모델 2.1 - 하이브리드 시나리오 데이터 모델**

* **문서 버전:** 1.2
* **작성일:** 2025년 9월 16일
* **작성자:** Gemini
* **관련 문서:** 지능형 공장 자동화 시스템 2.0 PRD

### **1. 개요 (Overview)**

#### **1.1. 배경 및 목표**

지능형 공장 자동화 시스템 2.0은 NSGA-II 최적화 시뮬레이터를 도입함에 따라, 복잡하고 구조화된 시나리오 입력 파일셋(file set)을 요구합니다. 모든 데이터를 가장 세분화된 단위(granular)로 AAS에 저장하는 것은 비효율적일 수 있으므로, **데이터의 성격에 따라 두 가지 방식으로 데이터를 저장하고 제공하는 하이브리드(Hybrid) 데이터 모델**을 도입합니다.

본 문서의 목표는 이 하이브리드 전략에 따라, AAS 서버에 저장될 데이터의 구체적인 구조와 명세를 정의하여 시나리오 합성 과정의 효율성과 데이터 관리의 유연성을 확보하는 것입니다.

#### **1.2. 핵심 전략: 정적 데이터와 동적 데이터의 분리**

* **정적 시나리오 데이터 (Static Scenario Data):** 특정 시뮬레이션 실행 동안에는 **내용이 변하지 않는 데이터 묶음**입니다. (예: 작업 목록, 공정 순서, 작업 시간 분포). 이 데이터들은 하나의 "시나리오 세트"로 간주하여 파일 단위로 AAS에 저장합니다.
* **동적 실시간 데이터 (Dynamic Real-time Data):** 시뮬레이션이 실행되는 **바로 그 시점**의 공장 상태를 반영해야 하는 데이터입니다. (예: 설비의 현재 상태, 대기열 길이). 이 데이터들은 **개별 자산(Asset)의 AAS에서 직접 조회하여 동적으로 조합**합니다.

---

### **2. 상세 명세: 그룹 A (정적 시나리오 데이터)**

`jobs.json`, `operations.json`, `operation_durations.json`, `machine_transfer_time.json`, `job_release.json` 파일들은 이 방식으로 처리합니다.

#### **2.1. AAS Submodel 구현 방안**

* **지시사항**: "시나리오 세트"라는 개념을 중심으로 새로운 AAS Submodel들을 생성합니다. 각 Submodel은 시뮬레이터 입력 JSON 파일 하나에 대응하며, 내부에 파일의 **전체 내용을 문자열(String)로 저장**하는 `Content` Property를 가집니다.

* **명명 규칙**:
    * **idShort**: `Scenario_{FileType}_{ScenarioName_Version}` (예: `Scenario_Jobs_JobETAModel_v1.1`)
    * **id**: `urn:factory:aas:scenario:{ScenarioName_Version}/{FileType}`

#### **2.2. Submodel 상세 정의 (예시)**

##### **`Scenario_Jobs` Submodel**
* **원본 파일**: `jobs.json`
* **idShort**: `Scenario_Jobs_JobETAModel_v1.1`
* **id**: `urn:factory:aas:scenario:JobETAModel_v1.1/Jobs`
* **SubmodelElements**:
    * `Content` (Property, `xs:string`): `jobs.json` 파일의 전체 내용을 JSON 문자열로 저장합니다.
    * `Version` (Property, `xs:string`): 시나리오 데이터의 버전을 명시합니다 (예: "1.1.0").

##### **`Scenario_Operations` Submodel**
* **원본 파일**: `operations.json`
* **idShort**: `Scenario_Operations_JobETAModel_v1.1`
* **id**: `urn:factory:aas:scenario:JobETAModel_v1.1/Operations`
* **SubmodelElements**:
    * `Content` (Property, `xs:string`): `operations.json` 파일의 전체 내용을 JSON 문자열로 저장합니다.
    * `Version` (Property, `xs:string`): "1.1.0"

*(나머지 `operation_durations.json`, `machine_transfer_time.json`, `job_release.json` 파일에 대해서도 위와 동일한 패턴으로 Submodel을 생성합니다.)*

#### **2.3. 개발팀을 위한 지시사항**

* **`ScenarioComposer`**: `bindings.yaml`에는 위에서 정의한 Submodel들의 `id`를 연결해야 합니다. `ScenarioComposer`의 작업은 매우 단순해집니다.
* **작업 순서**:
    1.  `bindings.yaml`을 읽어 `urn:factory:aas:scenario:JobETAModel_v1.1/Jobs` URI를 가져옵니다.
    2.  `AASQueryClient`로 해당 Submodel을 조회합니다.
    3.  조회된 Submodel의 `Content` Property에서 `value`(JSON 문자열)를 꺼냅니다.
    4.  이 문자열을 그대로 파싱하여 PVC에 `jobs.json` 파일로 저장합니다.

---

### **3. 상세 명세: 그룹 B (동적 실시간 데이터)**

`machines.json` 파일은 정적 정보와 동적 정보가 혼합되어 있으므로, 여러 소스에서 데이터를 조합하여 동적으로 생성합니다.

#### **3.1. AAS 데이터 소스**

* **정적 정보 소스**: 각 설비(`M1`, `M2`...) AAS의 `TechnicalData` Submodel.
    * **필요 데이터**: `MachineType`, `PerformableOperations`, `Efficiency` 등
* **동적 정보 소스**: 각 설비(`M1`, `M2`...) AAS의 `OperationalData` Submodel.
    * **필요 데이터**: `Status`, `QueueLength` 등
    * **요구사항**: `machines.json` 파일은 `next_available_time` 필드를 요구합니다. 이는 `OperationalData` Submodel에 `NextAvailableTime` (Property, `xs:double`) SubmodelElement를 추가하여 제공해야 합니다.

#### **3.2. `ScenarioComposer`의 역할**

* **지시사항**: `machines.json`을 생성하기 위해 `ScenarioComposer`는 다음과 같은 조합(Composition) 작업을 수행해야 합니다.
* **작업 순서**:
    1.  시뮬레이션에 필요한 모든 설비 ID 목록(`M1`, `M2`, `M3`, `M4`)을 식별합니다.
    2.  **For 루프 실행**: 각 설비 ID에 대해 아래 작업을 반복합니다.
        * 해당 설비의 `TechnicalData` Submodel을 조회하여 정적 정보를 가져옵니다.
        * 해당 설비의 `OperationalData` Submodel을 조회하여 `status`와 `next_available_time` 등 실시간 상태 정보를 가져옵니다.
    3.  **데이터 조합**: 루프를 통해 수집된 모든 설비의 정보를 조합하여 `machines.json` 파일 형식에 맞는 최종 딕셔너리를 생성하고 PVC에 저장합니다.

---

### **4. 구현 전략 및 유의사항**

* **개발 효율성**: 이 하이브리드 전략은 `ScenarioComposer`가 복잡한 데이터 구조를 처음부터 만들어내는 대신, 미리 정의된 JSON 청크(Chunk)를 AAS에서 가져와 사용하므로 개발이 매우 간단하고 빨라집니다.
* **성능 향상**: 수백 개의 개별 SubmodelElement를 조회하는 대신, 단 몇 번의 AAS API 호출로 시나리오의 대부분을 구성할 수 있어 성능에 유리합니다.
* **유연한 시나리오 관리**: "시나리오 세트 A", "시나리오 세트 B"와 같이 여러 버전의 시나리오 데이터를 AAS에 저장해두고, `QueryGoal`의 파라미터에 따라 원하는 시나리오를 선택적으로 불러와 시뮬레이션하는 "What-if" 분석이 용이해집니다.
* **버전 관리**: 모든 "정적 시나리오" Submodel에는 반드시 `Version` Property를 포함하여, 어떤 버전의 시나리오가 사용되었는지 `manifest.json`에 기록해야 재현성이 보장됩니다.
* **데이터 원자성(Atomicity)**: `jobs.json`의 내용 중 일부만 수정하고 싶어도, 전체 JSON 문자열을 통째로 다시 업로드해야 합니다. 이는 관리의 편의성과 세밀한 제어 사이의 트레이드오프입니다.