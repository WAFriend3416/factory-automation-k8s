# Goal3 E2E Flow 설명 계획 (코드 검증 완료)

**기반 테스트 파일**: `test_runtime_executor.py`  
**검증 상태**: ✅ 실제 코드 구조와 100% 일치 확인

---

## 📋 목차

1. [개요: E2E Flow 전체 구조](#1-개요-e2e-flow-전체-구조)
2. [Part 1: Pipeline - 자연어 → QueryGoal](#2-part-1-pipeline---자연어--querygoal)
3. [Part 2: Runtime - QueryGoal 실행](#3-part-2-runtime---querygoal-실행)
4. [Stage 1: swrlSelection](#4-stage-1-swrlselection)
5. [Stage 2: yamlBinding](#5-stage-2-yamlbinding)
6. [Stage 3: simulation](#6-stage-3-simulation)
7. [결과 구조 상세](#7-결과-구조-상세)
8. [콘솔 출력 예시](#8-콘솔-출력-예시)
9. [파일 구조 및 경로](#9-파일-구조-및-경로)
10. [핵심 포인트 요약](#10-핵심-포인트-요약)

---

## 1. 개요: E2E Flow 전체 구조

### 1.1 전체 흐름도

```
사용자 입력 (자연어)
    ↓
┌─────────────────────────────────────────────────────────┐
│ PART 1: Pipeline (6 stages)                            │
│ PipelineOrchestrator.process_natural_language()         │
├─────────────────────────────────────────────────────────┤
│ 1. Pattern Matching    → Goal Type + Parameters 추출    │
│ 2. Template Loading    → 기본 QueryGoal 템플릿 생성      │
│ 3. Parameter Filling   → parameters + outputSpec 채우기 │
│ 4. ActionPlan Resolving → metadata 설정                 │
│ 5. Model Selection     → selectedModel 바인딩           │
│ 6. Validation          → QueryGoal 스키마 검증          │
└─────────────────────────────────────────────────────────┘
    ↓
QueryGoal JSON (outputs 필드 없음!)
    ↓
┌─────────────────────────────────────────────────────────┐
│ PART 2: Runtime (3 stages with Stage-Gate)             │
│ QueryGoalExecutor.execute_querygoal()                   │
├─────────────────────────────────────────────────────────┤
│ Stage 1: swrlSelection  → Manifest 로드 + 모델 검증     │
│ Stage 2: yamlBinding    → AAS에서 데이터 수집 + JSON화  │
│ Stage 3: simulation     → Docker 시뮬레이션 실행        │
│                          → QueryGoal.outputs 생성!      │
└─────────────────────────────────────────────────────────┘
    ↓
최종 결과 (QueryGoal + executionLog + workDirectory)
```

### 1.2 두 파트의 역할 분담

**Pipeline (자연어 → QueryGoal)**
- 입력: `"Predict production time for product TEST_RUNTIME quantity 30"`
- 출력: QueryGoal JSON (완전한 실행 명세, 단 `outputs` 필드는 아직 없음)
- 핵심 클래스: `PipelineOrchestrator`

**Runtime (QueryGoal 실행)**
- 입력: QueryGoal JSON
- 출력: 실행된 QueryGoal (outputs 포함) + executionLog + workDirectory
- 핵심 클래스: `QueryGoalExecutor`

---

## 2. Part 1: Pipeline - 자연어 → QueryGoal

### 2.1 시작점: test_runtime_executor.py

```python
# Line 23-29
from querygoal.pipeline.orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator()
querygoal = orchestrator.process_natural_language(
    "Predict production time for product TEST_RUNTIME quantity 30"
)
```

### 2.2 Stage 1-6 처리 흐름

**실제 코드**: `querygoal/pipeline/orchestrator.py`

```python
def process_natural_language(self, input_text: str) -> Dict[str, Any]:
    """자연어 입력 → QueryGoal JSON 변환 (6단계)"""
    
    # Stage 1: Pattern Matching
    analysis_result = self.pattern_matcher.analyze(input_text)
    goal_type = analysis_result["goalType"]           # ← "goalType" 키 사용!
    metadata = analysis_result["metadata"]
    extracted_params = analysis_result["extractedParameters"]  # ← "extractedParameters" 키 사용!
    
    # ⚠️ 중요: Goal3는 productType을 추출합니다 (productId 아님!)
    # pattern_matcher.py Line 118-122:
    # product_match = re.search(r"product[_\s]*(?:type[_\s]*)?[:\s]*([A-Za-z0-9_-]+)", ...)
    # parameters["productType"] = product_match.group(1)
    
    # Stage 2: Template Loading
    querygoal = self.template_loader.create_querygoal(
        goal_type=goal_type,
        category=metadata.get("category", "unknown"),
        requires_model=metadata.get("requiresModel", False),
        pipeline_stages=metadata.get("pipelineStages", [])
    )
    # ⚠️ template_loader.py Line 76-110 실제 시그니처 사용
    
    # Stage 3: Parameter Filling
    querygoal = self.parameter_filler.process(
        querygoal=querygoal,
        extracted_params=extracted_params,
        goal_type=goal_type
    )
    # parameter_filler.py Line 25-26:
    # "required": ["productType", "quantity"]  ← productType 사용!
    
    # Stage 4: ActionPlan Resolution
    querygoal = self.actionplan_resolver.resolve_action_plan(querygoal)
    
    # Stage 5: Model Selection
    querygoal = self.model_selector.bind_model_to_querygoal(querygoal)
    
    # Stage 6: Validation
    validation_result = self.validator.validate(querygoal)
    
    return querygoal
```

### 2.3 Pipeline 출력 구조

**⚠️ 중요: outputs 필드는 아직 생성되지 않습니다!**

```json
{
  "QueryGoal": {
    "goalId": "goal3_test_173727",
    "goalType": "goal3_predict_production_time",
    "parameters": [
      {"key": "productType", "value": "TEST_RUNTIME"},
      {"key": "quantity", "value": 30}
    ],
    "selectedModel": {
      "modelId": "NSGA2SimulatorModel",
      "metaDataFile": "NSGA2Model_sources.yaml",
      "container": {
        "image": "factory-nsga2:latest",
        "registry": "localhost:5000"
      }
    },
    "metadata": {
      "pipelineStages": ["swrlSelection", "yamlBinding", "simulation"],
      "requiresModel": true,
      "dataSourceTypes": ["aas_property", "aas_shell_collection"]
    },
    "outputSpec": [
      {"name": "estimatedTime", "datatype": "number"},
      {"name": "confidence", "datatype": "number"},
      {"name": "productionPlan", "datatype": "object"},
      {"name": "bottlenecks", "datatype": "array"}
    ]
    // ⚠️ outputs 필드 없음! Runtime의 simulation 단계에서 생성됨
  }
}
```

---

## 3. Part 2: Runtime - QueryGoal 실행

### 3.1 시작점: test_runtime_executor.py

```python
# Line 36-40
from querygoal.runtime.executor import QueryGoalExecutor

executor = QueryGoalExecutor()
result = await executor.execute_querygoal(querygoal)
```

### 3.2 Runtime 실행 루프 구조

**실제 코드**: `querygoal/runtime/executor.py`

```python
async def execute_querygoal(self, querygoal: Dict[str, Any]) -> Dict[str, Any]:
    """QueryGoal을 Stage-Gate 패턴으로 실행"""
    
    start_time = datetime.utcnow()
    qg = querygoal["QueryGoal"]
    
    # ExecutionContext 초기화
    context = ExecutionContext(
        goal_id=qg["goalId"],
        goal_type=qg["goalType"],
        work_directory=self.work_dir_manager.create_work_directory(qg["goalId"]),
        start_time=start_time,
        pipeline_stages=qg["metadata"]["pipelineStages"]
    )
    # ⚠️ WorkDirectoryManager 사용 (NOT _create_work_directory)
    
    execution_log = {
        "goalId": context.goal_id,
        "startTime": start_time.isoformat(),
        "stages": [],
        "status": "in_progress"
    }
    
    # pipeline_stages에서 동적으로 읽음 (하드코딩 안 함!)
    for stage_name in context.pipeline_stages:
        context.current_stage = stage_name
        
        # self.stage_handlers 딕셔너리에서 핸들러 가져옴
        if stage_name not in self.stage_handlers:
            raise StageExecutionError(f"Unknown stage: {stage_name}")
        
        # Stage 실행 (_execute_stage가 메타데이터 추가)
        stage_result = await self._execute_stage(
            stage_name, querygoal, context
        )
        # ⚠️ handler는 _execute_stage 내부에서 self.stage_handlers로 가져옴
        # stage_result에는 handler 결과 + stage/executionTime/timestamp 포함
        
        # Stage-Gate 검증
        gate_result = self.stage_gate_validator.validate_stage(
            stage_name, stage_result, self.stage_criteria
        )
        # ⚠️ 실제 메서드명: validate_stage (NOT _validate_stage_gate!)
        
        if not gate_result.passed:
            raise StageGateFailureError(
                f"Stage-Gate failed for {stage_name}: {gate_result.reason}"
            )
        
        # Context에 결과 저장
        context.stage_results[stage_name] = stage_result
        
        # ExecutionLog에 기록
        execution_log["stages"].append({
            "stage": stage_name,
            "status": "completed",
            "result": stage_result,
            "gate_check": {
                "passed": gate_result.passed,
                "reason": gate_result.reason
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    
    execution_log["status"] = "completed"
    execution_log["endTime"] = datetime.utcnow().isoformat()
    
    # 최종 결과 구성 (executor.py Line 168-173)
    final_result = {
        "QueryGoal": querygoal["QueryGoal"],
        "executionLog": execution_log,
        "results": context.stage_results,  # ⚠️ 각 Stage의 결과 payload!
        "workDirectory": str(context.work_directory)
    }
    
    return final_result
```

### 3.3 _execute_stage 메타데이터 추가

**실제 코드**: `executor.py` Line 205-218

```python
async def _execute_stage(
    self, stage_name: str, querygoal, context
) -> Dict[str, Any]:
    """Stage 실행 + 메타데이터 추가"""
    
    # self.stage_handlers에서 핸들러 가져옴
    if stage_name not in self.stage_handlers:
        raise StageExecutionError(f"Unknown stage: {stage_name}")
    
    handler = self.stage_handlers[stage_name]
    stage_start_time = datetime.utcnow()
    
    # Handler 실행 (create_success_result로 래핑된 결과 반환)
    result = await handler.execute(querygoal, context)
    
    execution_time = (datetime.utcnow() - stage_start_time).total_seconds()
    
    # ⚠️ 핸들러 결과에 실행 메타데이터 추가
    result.update({
        "stage": stage_name,
        "executionTime": execution_time,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return result
```

---

## 4. Stage 1: swrlSelection

### 4.1 역할
- Manifest 파일 로드 및 검증
- QueryGoal에 이미 바인딩된 selectedModel 확인

### 4.2 실제 코드

**파일**: `querygoal/runtime/handlers/swrl_selection_handler.py`

```python
async def execute(self, querygoal, context) -> Dict[str, Any]:
    """swrlSelection 실행"""
    
    qg = querygoal["QueryGoal"]
    selected_model = qg.get("selectedModel", {})
    
    # _load_model_manifest 메서드로 경로 처리
    manifest_path = await self._load_model_manifest(selected_model, context)
    # ⚠️ 실제로는 Path(__file__).parent.parent.parent.parent / "config" / manifest_file
    #    절대 경로도 처리 가능 (manifest_file.startswith("/") 체크)
    #    파일이 없으면 _load_model_manifest 내부에서 StageExecutionError 발생!
    
    # Line 44-52: 결과 생성
    result_data = {
        "selectedModel": selected_model,
        "manifestPath": str(manifest_path),
        "selectionMethod": "pre_selected",
        "modelStatus": "ready"
        # ⚠️ manifestData는 포함되지 않음!
    }
    
    await self.post_execute(result_data, context)
    return self.create_success_result(result_data)
    # create_success_result가 status, handler, timestamp 추가
```

### 4.3 실제 결과 구조

```json
{
  "status": "success",
  "handler": "SwrlSelectionHandler",
  "timestamp": "2025-10-01T17:37:27.220411",
  "selectedModel": {
    "modelId": "NSGA2SimulatorModel",
    "metaDataFile": "NSGA2Model_sources.yaml",
    "container": {
      "image": "factory-nsga2:latest",
      "registry": "localhost:5000"
    }
  },
  "manifestPath": "/Users/.../config/NSGA2Model_sources.yaml",
  "selectionMethod": "pre_selected",
  "modelStatus": "ready",
  "stage": "swrlSelection",
  "executionTime": 3.6e-05
}
```

---

## 5. Stage 2: yamlBinding

### 5.1 역할
- Manifest에 정의된 data_sources를 읽어 AAS 서버에서 데이터 수집
- 각 데이터를 JSON 파일로 저장 (JobOrders.json, Machines.json 등)

### 5.2 실제 코드

**파일**: `querygoal/runtime/handlers/yaml_binding_handler.py`

```python
async def execute(self, querygoal, context) -> Dict[str, Any]:
    """yamlBinding 실행"""
    
    qg = querygoal["QueryGoal"]
    
    # 이전 단계에서 생성된 manifest 경로 확인
    manifest_path = context.stage_results.get("swrlSelection", {}).get("manifestPath")
    if not manifest_path:
        return self.create_error_result("Manifest path not found from previous stage")
    
    # Manifest 파싱 (manifest_parser 사용)
    manifest_data = await self.manifest_parser.parse_manifest(Path(manifest_path))
    
    # data_sources 처리
    data_sources = manifest_data.get("data_sources", [])
    if not data_sources:
        return self.create_error_result("No data sources found in manifest")
    
    json_files = {}
    success_count = 0
    
    # Required/Optional 소스 분류
    required_sources = [s for s in data_sources if s.get("required", True)]  # ⚠️ 기본값 True!
    optional_sources = [s for s in data_sources if not s.get("required", True)]
    
    required_count = len(required_sources)
    required_success = 0
    
    for source in data_sources:
        try:
            source_name = source["name"]
            source_type = source["type"]
            is_required = source.get("required", True)  # ⚠️ 기본값 True!
            
            # 소스 타입별 처리
            if source_type == "aas_property":
                json_data = await self._fetch_aas_property_data(source)
            elif source_type == "aas_shell_collection":
                json_data = await self._fetch_aas_shell_collection(source)
            else:
                raise StageExecutionError(f"Unknown data source type: {source_type}")
            
            # JSON 파일 저장
            json_file_path = context.work_directory / f"{source_name}.json"
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            json_files[source_name] = {
                "path": str(json_file_path),
                "size": json_file_path.stat().st_size,
                "record_count": len(json_data) if isinstance(json_data, list) else 1
            }
            
            success_count += 1
            if is_required:
                required_success += 1
                
        except Exception as e:
            self.logger.error(f"❌ Failed to process {source.get('name', 'unknown')}: {e}")
            json_files[source.get('name', 'unknown')] = {"error": str(e)}
    
    # 전체 성공률 및 필수 소스 성공률 계산
    total_sources = len(data_sources)
    success_rate = success_count / total_sources if total_sources > 0 else 0
    required_success_rate = required_success / required_count if required_count > 0 else 0
    
    # Line 102-117: 결과 생성
    result_data = {
        "manifestPath": manifest_path,
        "totalDataSources": total_sources,
        "successfulSources": success_count,
        "success_rate": success_rate,
        # Required-flag filtering 정보
        "required_sources_count": required_count,
        "optional_sources_count": len(optional_sources),
        "required_success_count": required_success,
        "required_success_rate": required_success_rate,
        "jsonFiles": json_files,
        "workDirectory": str(context.work_directory)
    }
    
    await self.post_execute(result_data, context)
    return self.create_success_result(result_data)
```

### 5.3 실제 결과 구조

```json
{
  "status": "success",
  "handler": "YamlBindingHandler",
  "timestamp": "2025-10-01T17:37:27.324815",
  "manifestPath": "/Users/.../config/NSGA2Model_sources.yaml",
  "totalDataSources": 6,
  "successfulSources": 6,
  "success_rate": 1.0,
  "required_sources_count": 5,
  "optional_sources_count": 1,
  "required_success_count": 5,
  "required_success_rate": 1.0,
  "jsonFiles": {
    "JobOrders": {
      "path": "/Users/.../goal3_test_023727_20251001_173727/JobOrders.json",
      "size": 3624,
      "record_count": 30
    },
    "Machines": {
      "path": "/Users/.../goal3_test_023727_20251001_173727/Machines.json",
      "size": 699,
      "record_count": 4
    }
    // ... 나머지 4개 파일
  },
  "workDirectory": "/Users/.../goal3_test_023727_20251001_173727",
  "stage": "yamlBinding",
  "executionTime": 0.104392
}
```

---

## 6. Stage 3: simulation

### 6.1 역할
- Docker 컨테이너로 NSGA-II 시뮬레이션 실행
- 시뮬레이션 결과를 파싱하여 QueryGoal.outputs 생성

### 6.2 실제 코드

**파일**: `querygoal/runtime/handlers/simulation_handler.py`

```python
async def execute(self, querygoal, context) -> Dict[str, Any]:
    """Simulation 실행"""
    
    qg = querygoal["QueryGoal"]
    selected_model = qg.get("selectedModel", {})
    container_image = selected_model["container"]["image"]
    
    # 이전 단계 JSON 파일 확인
    yaml_binding_result = context.stage_results.get("yamlBinding", {})
    json_files = yaml_binding_result.get("jsonFiles", {})
    
    # 시뮬레이션 입력 준비
    simulation_input = await self._prepare_simulation_input(
        qg, json_files, context.work_directory
    )
    
    # 컨테이너 실행
    execution_result = await self.container_client.run_simulation(
        image=container_image,
        input_data=simulation_input,
        work_directory=context.work_directory,
        goal_id=context.goal_id
    )
    
    # 시뮬레이션 결과 파싱
    simulation_output = await self._parse_simulation_output(
        execution_result, context.work_directory
    )
    
    # ⚠️ QueryGoal.outputs 업데이트 (여기서 처음 생성!)
    await self._update_querygoal_outputs(qg, simulation_output)
    
    result_data = {
        "containerImage": container_image,
        "executionId": execution_result.get("execution_id"),
        "status": "completed",
        "simulationOutput": simulation_output,  # ← 시뮬레이터 원본 출력
        "executionTime": execution_result.get("execution_time"),
        "containerLogs": execution_result.get("logs_path")
    }
    
    await self.post_execute(result_data, context)
    return self.create_success_result(result_data)

async def _update_querygoal_outputs(self, qg, simulation_output):
    """QueryGoal.outputs 필드 생성 (Goal3 outputSpec 매핑)"""
    
    if "outputs" not in qg:
        qg["outputs"] = {}
    
    # outputSpec에 정의된 필드로 매핑
    qg["outputs"].update({
        "estimatedTime": simulation_output.get("estimatedTime"),
        "confidence": simulation_output.get("confidence"),
        "productionPlan": simulation_output.get("productionPlan", {}),
        "bottlenecks": simulation_output.get("bottlenecks", []),
        "simulator_type": simulation_output.get("simulator_type"),
        "execution_metadata": simulation_output.get("execution_metadata", {})
    })
```

### 6.3 실제 결과 구조

**⚠️ 중요: simulationOutput vs outputs 구분!**

```json
{
  "status": "success",
  "handler": "SimulationHandler",
  "timestamp": "2025-10-01T17:37:35.892156",
  "containerImage": "factory-nsga2:latest",
  "executionId": "sim_goal3_test_023727_20251001173727",
  "simulationOutput": {
    // ← 시뮬레이터가 반환한 원본 출력
    "estimatedTime": 245.67,
    "confidence": 0.95,
    "simulator_type": "NSGA-II",
    "productionPlan": {...},
    "bottlenecks": [...]
  },
  "containerLogs": "/Users/.../goal3_test_023727/container_logs.txt",
  "stage": "simulation",
  "executionTime": 8.571788  // _execute_stage()가 덮어쓴 최종 값
}
```

**동시에 QueryGoal.outputs도 업데이트됨:**

```json
{
  "QueryGoal": {
    "goalId": "goal3_test_023727",
    "goalType": "goal3_predict_production_time",
    // ... parameters, selectedModel 등 ...
    "outputs": {
      // ← simulation 단계에서 처음 생성!
      "estimatedTime": 245.67,
      "confidence": 0.95,
      "productionPlan": {...},
      "bottlenecks": [...],
      "simulator_type": "NSGA-II",
      "execution_metadata": {...}
    }
  }
}
```

---

## 7. 결과 구조 상세

### 7.1 최종 반환 구조

```json
{
  "QueryGoal": {
    "goalId": "goal3_test_023727",
    "goalType": "goal3_predict_production_time",
    "parameters": [...],
    "selectedModel": {...},
    "metadata": {...},
    "outputSpec": {...},
    "outputs": {
      // ← simulation 단계에서 추가됨
      "estimatedTime": 245.67,
      "confidence": 0.95,
      "productionPlan": {...},
      "bottlenecks": [...]
    }
  },
  "executionLog": {
    "status": "completed",
    "goalId": "goal3_test_023727",
    "stages": [
      {
        "stage": "swrlSelection",
        "status": "completed",
        "result": {
          "status": "success",
          "handler": "SwrlSelectionHandler",
          "timestamp": "2025-10-01T17:37:27.220411",
          "selectedModel": {...},
          "manifestPath": "...",
          "selectionMethod": "pre_selected",
          "modelStatus": "ready",
          "stage": "swrlSelection",
          "executionTime": 3.6e-05
        },
        "gate_check": {
          "passed": true,
          "reason": "Stage criteria satisfied"
        },
        "timestamp": "2025-10-01T17:37:27.220450"
      },
      {
        "stage": "yamlBinding",
        "status": "completed",
        "result": {
          "status": "success",
          "handler": "YamlBindingHandler",
          "timestamp": "2025-10-01T17:37:27.324815",
          "manifestPath": "...",
          "totalDataSources": 6,
          "successfulSources": 6,
          "success_rate": 1.0,
          "required_sources_count": 5,
          "optional_sources_count": 1,
          "required_success_count": 5,
          "required_success_rate": 1.0,
          "jsonFiles": {...},
          "workDirectory": "...",
          "stage": "yamlBinding",
          "executionTime": 0.104392
        },
        "gate_check": {
          "passed": true,
          "reason": "Stage criteria satisfied"
        },
        "timestamp": "2025-10-01T17:37:27.325200"
      },
      {
        "stage": "simulation",
        "status": "completed",
        "result": {
          "status": "success",
          "handler": "SimulationHandler",
          "timestamp": "2025-10-01T17:37:35.892156",
          "containerImage": "factory-nsga2:latest",
          "executionId": "sim_goal3_test_023727_20251001173727",
          "simulationOutput": {
            "estimatedTime": 245.67,
            "confidence": 0.95,
            "productionPlan": {...},
            "bottlenecks": [...]
          },
          "containerLogs": "...",
          "stage": "simulation",
          "executionTime": 8.571788
        },
        "gate_check": {
          "passed": true,
          "reason": "Stage criteria satisfied"
        },
        "timestamp": "2025-10-01T17:37:35.892500"
      }
    ]
  },
  "workDirectory": "/Users/.../temp/runtime_executions/goal3_test_023727_20251001_173727"
}
```

### 7.2 핸들러 결과 래핑 구조

**모든 핸들러의 create_success_result()가 추가하는 필드:**

```python
# base_handler.py
def create_success_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "success",
        "handler": self.__class__.__name__,
        "timestamp": datetime.utcnow().isoformat(),
        **data  # 핸들러 고유 데이터
    }
```

**_execute_stage()가 추가하는 메타데이터:**

```python
result.update({
    "stage": stage_name,
    "executionTime": execution_time,
    "timestamp": datetime.utcnow().isoformat()
})
```

---

## 8. 콘솔 출력 예시

### 8.1 Pipeline 실행 출력

```
============================================================
🧪 QueryGoal Runtime Executor Test
============================================================

📝 Step 1: Creating QueryGoal via Pipeline...
✅ QueryGoal created: goal3_test_023727
   Goal Type: goal3_predict_production_time
   Pipeline Stages: ['swrlSelection', 'yamlBinding', 'simulation']
```

### 8.2 Runtime 실행 출력

```
🚀 Step 2: Executing QueryGoal with Runtime Executor...

📊 Step 3: Execution Results:
   Status: completed
   Goal ID: goal3_test_023727
   Stages Completed: 3
   - swrlSelection: completed
   - yamlBinding: completed
   - simulation: completed
```

### 8.3 작업 디렉터리 출력

```
📁 Work Directory: /Users/.../temp/runtime_executions/goal3_test_023727_20251001_173727
   Files created:
   - JobOrders.json
   - JobRelease.json
   - MachineTransferTime.json
   - Machines.json
   - OperationDurations.json
   - Operations.json
   - my_case/jobs.json
   - my_case/machine_transfer_time.json
   - my_case/machines.json
   - my_case/operation_durations.json
   - my_case/operations.json
   - results/simulator_optimization_result.json
   - simulation_input.json
   - container_logs.txt
```

### 8.4 최종 출력 확인

```
📤 QueryGoal Outputs:
   - estimatedTime: 245.67
   - confidence: 0.95
   - productionPlan: dict with 15 items
   - bottlenecks: ['M2', 'M3']
   - simulator_type: NSGA-II
   - execution_metadata: dict with 8 items

============================================================
✅ Runtime Executor Test PASSED
============================================================
```

---

## 9. 파일 구조 및 경로

### 9.1 주요 소스 파일

```
factory-automation-k8s/
├── test_runtime_executor.py           # E2E 테스트 파일
├── querygoal/
│   ├── pipeline/
│   │   ├── orchestrator.py            # Pipeline 오케스트레이터
│   │   ├── pattern_matcher.py         # Goal Type + Parameters 추출
│   │   ├── template_loader.py         # QueryGoal 템플릿 로드
│   │   ├── parameter_filler.py        # Parameters + outputSpec 채우기
│   │   ├── actionplan_resolver.py     # Metadata 설정
│   │   ├── model_selector.py          # Model 선택 및 바인딩
│   │   └── validator.py               # QueryGoal 스키마 검증
│   └── runtime/
│       ├── executor.py                # Runtime 실행 엔진
│       ├── stage_gate_validator.py    # Stage-Gate 검증
│       ├── handlers/
│       │   ├── base_handler.py        # 베이스 핸들러 (create_success_result)
│       │   ├── swrl_selection_handler.py    # Stage 1
│       │   ├── yaml_binding_handler.py      # Stage 2
│       │   └── simulation_handler.py        # Stage 3
│       └── clients/
│           └── container_client.py    # Docker 컨테이너 클라이언트
├── config/
│   └── NSGA2Model_sources.yaml        # Manifest 파일
└── temp/
    └── runtime_executions/
        └── goal3_test_023727_20251001_173727/  # 작업 디렉터리
            ├── JobOrders.json
            ├── Machines.json
            ├── my_case/
            │   ├── jobs.json
            │   └── machines.json
            └── results/
                └── simulator_optimization_result.json
```

### 9.2 실행 시 생성되는 디렉터리

```
temp/runtime_executions/
└── {goal_id}_{timestamp}/
    ├── JobOrders.json                 # yamlBinding이 생성
    ├── JobRelease.json
    ├── MachineTransferTime.json
    ├── Machines.json
    ├── OperationDurations.json
    ├── Operations.json
    ├── simulation_input.json          # simulation이 생성
    ├── my_case/                       # Docker 컨테이너가 생성
    │   ├── jobs.json
    │   ├── machines.json
    │   └── ...
    ├── results/                       # Docker 컨테이너가 생성
    │   └── simulator_optimization_result.json
    └── container_logs.txt             # Docker 실행 로그
```

---

## 10. 핵심 포인트 요약

### 10.1 코드 정확성 체크리스트

✅ **Pattern Matcher**: Goal3는 `productType` 추출 (NOT productId)
✅ **Parameter Filler**: `required: ["productType", "quantity"]`
✅ **Pipeline 출력**: `outputs` 필드 없음 (Runtime에서 생성)
✅ **Stage Gate**: `stage_gate_validator.validate_stage()` 사용
✅ **Result 래핑**: `create_success_result()` → status/handler/timestamp 추가
✅ **Stage 메타데이터**: `_execute_stage()` → stage/executionTime/timestamp 추가
✅ **swrlSelection**: manifestData 포함 안 함, 경로만 반환
✅ **yamlBinding**: required/optional 구분 + success_rate 계산
✅ **simulation**: simulationOutput (원본) vs QueryGoal.outputs (매핑) 구분

### 10.2 데이터 흐름 요약

```
사용자 입력 (자연어)
    ↓
Pattern Matcher → productType + quantity 추출
    ↓
Template + Parameter Filler → QueryGoal (outputs 없음!)
    ↓
Runtime Executor → ExecutionContext 초기화
    ↓
swrlSelection → Manifest 로드, 경로 확인
    ↓
yamlBinding → AAS 데이터 수집, JSON 파일 생성
    ↓
simulation → Docker 실행, QueryGoal.outputs 생성!
    ↓
최종 결과 (QueryGoal + executionLog + workDirectory)
```

### 10.3 Stage-Gate 검증 흐름

```
각 Stage마다:
    1. Handler.execute() → 핸들러 고유 로직 실행
    2. create_success_result() → status/handler/timestamp 래핑
    3. _execute_stage() → stage/executionTime 추가
    4. stage_gate_validator.validate_stage() → 검증
    5. 통과 → context.stage_results에 저장
    6. 실패 → StageGateFailureError 발생
```

### 10.4 파일 검증 체크리스트

- ✅ `pattern_matcher.py` Line 118-122: productType 추출 확인
- ✅ `parameter_filler.py` Line 25-26: required 파라미터 확인
- ✅ `orchestrator.py`: outputs 필드 생성 안 함 확인
- ✅ `executor.py` Line 119: validate_stage() 메서드 확인
- ✅ `executor.py` Line 205-218: _execute_stage 메타데이터 확인
- ✅ `base_handler.py`: create_success_result 구조 확인
- ✅ `swrl_selection_handler.py` Line 44-52: 결과 구조 확인
- ✅ `yaml_binding_handler.py` Line 102-117: 결과 구조 확인
- ✅ `simulation_handler.py`: simulationOutput vs outputs 구분 확인

---

**검증 완료 일시**: 2025-10-02  
**기반 코드 버전**: factory-automation-k8s (latest)  
**테스트 파일**: test_runtime_executor.py  
**검증 방법**: 실제 소스 코드 line-by-line 확인
