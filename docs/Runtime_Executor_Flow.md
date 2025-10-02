# QueryGoal Runtime Executor - 실행 절차 및 데이터 흐름

## 📋 전체 실행 플로우

```
자연어 입력
    ↓
[기존 Pipeline] QueryGoal 생성
    ↓
[Runtime Executor] 실제 실행
    ↓
최종 결과 반환
```

---

## 🔄 Runtime Executor 상세 실행 절차

### 입력: 완성된 QueryGoal 객체
```json
{
  "QueryGoal": {
    "goalId": "goal3_production_20250930_001",
    "goalType": "goal3_production_time_prediction",
    "metadata": {
      "pipelineStages": ["swrlSelection", "yamlBinding", "simulation"]
    },
    "selectedModel": {
      "modelId": "nsga2_simulator",
      "metaDataFile": "manifests/goal3_nsga2_manifest.yaml",
      "container": {
        "image": "factory-nsga2:latest"
      }
    },
    "parameters": [
      {"key": "productId", "value": "ABC123"},
      {"key": "quantity", "value": 50}
    ]
  }
}
```

---

## Stage 1: swrlSelection (모델 선택 단계)

### 📥 입력
- QueryGoal 전체 객체
- ExecutionContext (goal_id, work_directory 등)

### 🔧 처리 과정
```python
1. QueryGoal에서 selectedModel 확인
   - 이미 SWRL 엔진이 파이프라인에서 모델 선택 완료

2. 모델 메타데이터 파일 로드
   - metaDataFile 경로 확인 (최상위 레벨)
   - 예: "manifests/goal3_nsga2_manifest.yaml"

3. Manifest 파일 존재 확인
   - config/manifests/goal3_nsga2_manifest.yaml 검증
```

### 📤 출력
```json
{
  "status": "success",
  "handler": "SwrlSelectionHandler",
  "timestamp": "2025-09-30T10:15:23Z",
  "selectedModel": {
    "modelId": "nsga2_simulator",
    "metaDataFile": "manifests/goal3_nsga2_manifest.yaml",
    "container": {"image": "factory-nsga2:latest"}
  },
  "manifestPath": "/path/to/config/manifests/goal3_nsga2_manifest.yaml",
  "selectionMethod": "pre_selected",
  "modelStatus": "ready",
  "stage": "swrlSelection",
  "executionTime": 0.15
}
```

### ✅ Stage-Gate 검증
```python
success_criteria = lambda result: result.get("selectedModel") is not None
# → selectedModel 존재 여부 확인 → PASS
```

---

## Stage 2: yamlBinding (데이터 수집 단계)

### 📥 입력
- QueryGoal 전체 객체
- ExecutionContext (work_directory)
- Stage 1 결과: manifestPath

### 🔧 처리 과정
```yaml
# 1. Manifest 파싱 (goal3_nsga2_manifest.yaml)
data_sources:
  - name: "machines"
    type: "aas_shell_collection"
    required: true
    config:
      shell_filter:
        id_pattern: "Machine"
      combination_rules:
        - type: "submodel_property"
          submodel_id: "MachineData"
          property_path: "Identification.MachineId"
          result_key: "machineId"
        - type: "submodel_property"
          submodel_id: "MachineData"
          property_path: "Capabilities.ProductionCapacity"
          result_key: "capacity"

  - name: "materials"
    type: "aas_property"
    required: true
    config:
      submodel_id: "MaterialManagement"
      property_path: "Materials.AvailableMaterials"

  - name: "maintenance_schedule"
    type: "aas_property"
    required: false  # 선택적 소스
    config:
      submodel_id: "MaintenanceManagement"
      property_path: "Schedule.Upcoming"
```

```python
# 2. AAS 서버에서 데이터 수집
for source in data_sources:
    if source["type"] == "aas_property":
        # HTTP GET: http://127.0.0.1:5001/submodels/{submodel_id}/submodel-elements/{property_path}/value
        data = await aas_client.get_submodel_property(submodel_id, property_path)

    elif source["type"] == "aas_shell_collection":
        # HTTP GET: http://127.0.0.1:5001/shells
        shells = await aas_client.list_shells()

        # 필터링 및 조합
        for shell in shells:
            if matches_filter(shell):
                # HTTP GET: http://127.0.0.1:5001/shells/{shell_id}/submodels/{submodel_id}/...
                shell_data = await apply_combination_rules(shell)

    # 3. JSON 파일로 저장
    work_directory/machines.json 생성
    work_directory/materials.json 생성
    work_directory/maintenance_schedule.json 생성 (실패 가능)
```

### 실제 AAS 서버 HTTP 요청 예시
```http
# Request 1: Shell 목록 조회
GET http://127.0.0.1:5001/shells
Accept: application/json

# Response 1:
{
  "result": [
    {"idShort": "Machine_001", "identification": {...}},
    {"idShort": "Machine_002", "identification": {...}}
  ]
}

# Request 2: 특정 Property 조회
GET http://127.0.0.1:5001/shells/Machine_001/submodels/MachineData/submodel-elements/Identification.MachineId/value
Accept: application/json

# Response 2:
{
  "value": "M001",
  "valueType": "string"
}
```

### 📁 생성된 파일들
```
work_directory/
├── machines.json
│   [
│     {
│       "shell_id": "Machine_001",
│       "machineId": "M001",
│       "capacity": 100,
│       "processingTime": 5.2
│     },
│     {
│       "shell_id": "Machine_002",
│       "machineId": "M002",
│       "capacity": 80,
│       "processingTime": 6.1
│     }
│   ]
│
├── materials.json
│   {
│     "available_materials": [
│       {"material_id": "MAT001", "quantity": 500},
│       {"material_id": "MAT002", "quantity": 300}
│     ]
│   }
│
└── maintenance_schedule.json (선택적 - 실패 시 없을 수 있음)
```

### 📤 출력
```json
{
  "status": "success",
  "handler": "YamlBindingHandler",
  "timestamp": "2025-09-30T10:15:25Z",
  "manifestPath": "/path/to/config/manifests/goal3_nsga2_manifest.yaml",
  "totalDataSources": 3,
  "successfulSources": 2,
  "success_rate": 0.667,

  "required_sources_count": 2,
  "optional_sources_count": 1,
  "required_success_count": 2,
  "required_success_rate": 1.0,

  "jsonFiles": {
    "machines": {
      "path": "/path/to/work_directory/machines.json",
      "size": 512,
      "record_count": 2
    },
    "materials": {
      "path": "/path/to/work_directory/materials.json",
      "size": 256,
      "record_count": 1
    },
    "maintenance_schedule": {
      "error": "Property not found: Schedule.Upcoming in submodel MaintenanceManagement"
    }
  },
  "workDirectory": "/path/to/work_directory",
  "stage": "yamlBinding",
  "executionTime": 2.35
}
```

### ✅ Stage-Gate 검증 (Required-flag filtering)
```python
success_criteria = lambda result: (
    result.get("status") == "success" and  # 에러 상태 차단
    (result.get("required_sources_count", 0) == 0 or  # 필수 소스 없으면 통과
     result.get("required_success_rate", 0) >= 1.0)   # 필수 소스 100% 성공
)

# 검증 결과:
# - status: "success" ✓
# - required_sources_count: 2
# - required_success_rate: 1.0 (2/2 = 100%)
# → PASS (선택적 소스 실패는 무시됨)
```

---

## Stage 3: simulation (시뮬레이션 실행 단계)

### 📥 입력
- QueryGoal 전체 객체
- ExecutionContext (work_directory)
- Stage 2 결과: jsonFiles (machines.json, materials.json 경로)

### 🔧 처리 과정
```python
# 1. 시뮬레이션 입력 준비
simulation_input = {
    "goal_id": "goal3_production_20250930_001",
    "goal_type": "goal3_production_time_prediction",
    "parameters": {
        "productId": "ABC123",
        "quantity": 50
    },
    "data_files": {
        "machines": "/path/to/work_directory/machines.json",
        "materials": "/path/to/work_directory/materials.json"
    },
    "work_directory": "/path/to/work_directory"
}

# simulation_input.json 저장
work_directory/simulation_input.json 생성

# 2. Docker 컨테이너 실행 (환경변수 순서 수정 적용)
docker_cmd = [
    "docker", "run", "--rm",
    "-v", "/path/to/work_directory:/workspace",
    "--name", "simulation-goal3_production_20250930_001_a1b2c3d4",
    "-e", "PRODUCTID=ABC123",      # 환경변수가 이미지 이름 앞에 위치
    "-e", "QUANTITY=50",
    "factory-nsga2:latest"          # 이미지 이름은 마지막
]

# 3. 컨테이너 실행 및 결과 대기
process = await asyncio.create_subprocess_exec(*docker_cmd, ...)
stdout, stderr = await process.communicate()

# 4. 시뮬레이션 결과 파싱
# 컨테이너가 생성한 출력 파일 확인
work_directory/simulation_output.json 또는
work_directory/goal3_result.json
```

### 📁 시뮬레이션 출력 파일
```json
// work_directory/simulation_output.json
{
  "goal3_data": {
    "predicted_completion_time": 125.5,
    "confidence": 0.92,
    "simulator_type": "NSGA-II",
    "detailed_results": {
      "total_time": 125.5,
      "machine_utilization": {
        "M001": 0.85,
        "M002": 0.78
      },
      "bottlenecks": [
        {
          "machine_id": "M001",
          "wait_time": 12.3,
          "reason": "material_shortage"
        }
      ]
    }
  },
  "execution_metadata": {
    "timestamp": "2025-09-30T10:15:28Z",
    "algorithm": "NSGA-II",
    "iterations": 1000
  }
}
```

### 🔄 Goal3 outputSpec 매핑
```python
# 시뮬레이션 결과를 Goal3 outputSpec에 맞게 매핑
QueryGoal["outputs"] = {
    # predicted_completion_time → estimatedTime
    "estimatedTime": 125.5,

    # confidence는 동일
    "confidence": 0.92,

    # detailed_results → productionPlan
    "productionPlan": {
        "total_time": 125.5,
        "machine_utilization": {...},
        "bottlenecks": [...]
    },

    # bottlenecks 필드
    "bottlenecks": [
        {
            "machine_id": "M001",
            "wait_time": 12.3,
            "reason": "material_shortage"
        }
    ]
}
```

### 📤 출력
```json
{
  "status": "completed",
  "handler": "SimulationHandler",
  "timestamp": "2025-09-30T10:15:30Z",
  "containerImage": "factory-nsga2:latest",
  "executionId": "goal3_production_20250930_001_a1b2c3d4",
  "simulationOutput": {
    "predicted_completion_time": 125.5,
    "confidence": 0.92,
    "simulator_type": "NSGA-II",
    "detailed_results": {...},
    "execution_metadata": {...}
  },
  "executionTime": 3.45,
  "containerLogs": "/path/to/work_directory/container_logs_a1b2c3d4.txt",
  "stage": "simulation",
  "executionTime": 3.45
}
```

### ✅ Stage-Gate 검증
```python
success_criteria = lambda result: result.get("status") == "completed"
# → status: "completed" → PASS
```

---

## 🎯 최종 결과 (Execution Result)

### 📤 전체 실행 결과
```json
{
  "QueryGoal": {
    "goalId": "goal3_production_20250930_001",
    "goalType": "goal3_production_time_prediction",
    "metadata": {...},
    "selectedModel": {...},
    "parameters": [...],

    "outputs": {
      "estimatedTime": 125.5,
      "confidence": 0.92,
      "productionPlan": {
        "total_time": 125.5,
        "machine_utilization": {
          "M001": 0.85,
          "M002": 0.78
        },
        "bottlenecks": [...]
      },
      "bottlenecks": [
        {
          "machine_id": "M001",
          "wait_time": 12.3,
          "reason": "material_shortage"
        }
      ]
    }
  },

  "executionLog": {
    "goalId": "goal3_production_20250930_001",
    "startTime": "2025-09-30T10:15:23Z",
    "endTime": "2025-09-30T10:15:30Z",
    "status": "completed",
    "stages": [
      {
        "stage": "swrlSelection",
        "status": "completed",
        "result": {...},
        "gate_check": {"passed": true, "reason": "Stage criteria satisfied"},
        "timestamp": "2025-09-30T10:15:23Z"
      },
      {
        "stage": "yamlBinding",
        "status": "completed",
        "result": {...},
        "gate_check": {"passed": true, "reason": "Stage criteria satisfied"},
        "timestamp": "2025-09-30T10:15:25Z"
      },
      {
        "stage": "simulation",
        "status": "completed",
        "result": {...},
        "gate_check": {"passed": true, "reason": "Stage criteria satisfied"},
        "timestamp": "2025-09-30T10:15:30Z"
      }
    ]
  },

  "results": {
    "swrlSelection": {...},
    "yamlBinding": {...},
    "simulation": {...}
  },

  "workDirectory": "/Users/jsh/Desktop/aas-project/gemini-ver/factory-automation-k8s/temp/runtime_executions/goal3_production_20250930_001_20250930_101523"
}
```

---

## 📊 실행 절차 요약

| Stage | 주요 작업 | AAS 서버 접근 | 생성 파일 | 실행 시간 |
|-------|----------|--------------|-----------|----------|
| **swrlSelection** | 모델 메타데이터 로드 | ❌ | - | ~0.15s |
| **yamlBinding** | 데이터 수집 및 JSON 생성 | ✅ **HTTP GET** | machines.json<br>materials.json | ~2.35s |
| **simulation** | Docker 시뮬레이션 실행 | ❌ | simulation_output.json<br>container_logs.txt | ~3.45s |
| **Total** | - | - | - | **~6.0s** |

---

## 🔗 AAS 서버 접근 상세

### HTTP 요청 흐름
```
YamlBindingHandler
    ↓
AASClient.list_shells()
    ↓ HTTP GET http://127.0.0.1:5001/shells
    ↓
AAS Server 응답: [{"idShort": "Machine_001", ...}, ...]
    ↓
AASClient.get_submodel_property(shell_id, submodel_id, property_path)
    ↓ HTTP GET http://127.0.0.1:5001/shells/Machine_001/submodels/MachineData/submodel-elements/Identification.MachineId/value
    ↓
AAS Server 응답: {"value": "M001"}
    ↓
JSON 파일 생성: machines.json
```

### 사용되는 AAS API 엔드포인트
1. `GET /shells` - Shell 목록 조회
2. `GET /shells/{shell_id}` - 특정 Shell 조회
3. `GET /submodels` - Submodel 목록 조회
4. `GET /shells/{shell_id}/submodels/{submodel_id}/submodel-elements/{property_path}/value` - Property 값 조회
5. `GET /submodels/{submodel_id}/submodel-elements/{property_path}/value` - Property 값 조회 (shell 없이)

### httpx를 통한 비동기 HTTP 통신
```python
# querygoal/runtime/clients/aas_client.py
self.client = httpx.AsyncClient(
    timeout=httpx.Timeout(30),
    limits=httpx.Limits(max_keepalive_connections=10, max_connections=50)
)

response = await self.client.get(url)
response.raise_for_status()
return response.json()
```

---

## 💡 핵심 특징

1. **실제 AAS 서버 HTTP 통신**: yamlBinding 단계에서 `httpx`를 통해 실제 REST API 호출
2. **Required-flag Filtering**: 필수 데이터 소스만 검증, 선택적 소스 실패는 무시
3. **Docker 환경변수 순서**: `-e` 플래그가 이미지 이름 앞에 위치하도록 수정
4. **Goal3 outputSpec 매핑**: 시뮬레이션 결과를 표준 필드명으로 변환
5. **작업 디렉터리 격리**: Goal별 독립적인 실행 환경 유지
6. **Stage-Gate 검증**: 각 단계 성공 여부 확인 후 다음 단계 진행

---

## 🧪 테스트 실행 방법

```bash
# 환경 변수 설정
export USE_STANDARD_SERVER=true
export AAS_SERVER_IP=127.0.0.1
export AAS_SERVER_PORT=5001

# Runtime Executor 테스트 실행
python test_runtime_executor.py
```