# SWRL 기반 Goal3 통합 구현 계획서

## 📋 프로젝트 개요

**목표**: Desktop/SWRL 모듈을 활용하여 Factory-automation-k8s의 Goal3(제품 생산 시간 예측)를 완전 통합 구현

**핵심 접근**: SWRL의 범용 AI 모델 선택 및 실행 파이프라인을 Goal3에 특화 적용

**우선 순위**: NSGA-II 시뮬레이터 컨테이너화 및 테스트 → 전체 파이프라인 통합

---

## 🎯 Goal3 요구사항 분석

### 현재 Goal3 입력/출력
```json
// 입력
{
  "goal": "predict_first_completion_time",
  "product_id": "Product-A",
  "quantity": 10,
  "date_range": {
    "start": "2025-08-11",
    "end": "2025-08-15"
  }
}

// 출력
{
  "result": {
    "predicted_completion_time": "2025-08-13T14:30:00Z",
    "confidence": 0.85,
    "simulator_type": "aasx-main"
  }
}
```

### NSGA-II 시뮬레이터 요구사항
- **입력**: 6개 JSON 파일 (scenarios/my_case/)
  - jobs.json
  - operations.json
  - machines.json
  - operation_durations.json
  - machine_transfer_time.json
  - job_release.json
- **실행**: `python3 simulator/main.py --scenario scenarios/my_case`
- **출력**: simulator_optimization_result.json

---

## 🏗️ SWRL ↔ Goal3 매핑 전략

### 컴포넌트 매핑
| Goal3 요구사항 | SWRL 컴포넌트 | 구현 상태 | 작업 필요 |
|----------------|---------------|-----------|-----------|
| QueryGoal JSON 처리 | ✅ SelectionEngine | 완료 | Goal3 형식 변환 |
| NSGA-II 모델 선택 | ✅ SPARQL 추론 | 완료 | 모델 등록 |
| 6개 JSON 파일 생성 | ✅ DataOrchestrator | 완료 | AAS 매핑 |
| Docker 실행 | 🔨 신규 구현 | 미완료 | ModelExecutor |
| 결과 처리 | 🔨 신규 구현 | 미완료 | 후처리 로직 |

### 데이터 플로우
```
Goal3 Request → QueryGoal JSON → SWRL 모델선택 → AAS 데이터수집 → 
시나리오 파일생성 → NSGA-II 실행 → 결과 후처리 → Goal3 Response
```

---

## 📂 SWRL 설정 파일 확장

### 1. model_registry.json 확장
```json
{
  "modelId": "NSGA2SimulatorModel",
  "purpose": "ProductionTimeOptimization",
  "version": "1.0.0",
  "description": "NSGA-II 기반 생산 완료 시간 예측 시뮬레이터",
  "capabilities": ["predict_first_completion_time"],
  "inputParameters": [
    {"name": "product_id", "type": "string", "required": true},
    {"name": "quantity", "type": "number", "required": true},
    {"name": "start_date", "type": "string", "required": true},
    {"name": "end_date", "type": "string", "required": true}
  ],
  "execution": {
    "requiredInputs": ["JobOrders", "OperationDetails", "ProcessDurations", 
                      "TransferTimes", "JobReleaseSchedule", "MachineStatus"],
    "dataSourceConfig": "NSGA2Model_sources.yaml",
    "executionType": "nsga2_simulator",
    "containerImage": "factory-nsga2:latest",
    "scenarioTemplate": "scenarios/{scenario_name}"
  },
  "outputSchema": [
    {"name": "predicted_completion_time", "datatype": "datetime"},
    {"name": "confidence", "datatype": "number"},
    {"name": "makespan", "datatype": "number"}
  ]
}
```

### 2. rules.sparql 확장
```sparql
# Goal 3: Production Time Prediction
INSERT {
    ?goal ex:selectedModel ?model .
}
WHERE {
    ?goal rdf:type ex:QueryGoal .
    ?goal ex:goalType "predict_first_completion_time" .
    ?model rdf:type ex:Model .
    ?model ex:purpose "ProductionTimeOptimization" .
}
```

### 3. NSGA2Model_sources.yaml
```yaml
schema: 1
model: "NSGA2SimulatorModel"
version: "1.0.0"

# AAS Property → NSGA-II JSON 파일 매핑
sources:
  JobOrders:
    description: "작업 목록 및 공정 순서"
    uri: "aas://FactoryTwin/ScenarioData/JobsData"
    method: "GET"
    output_file: "jobs.json"
    required: true
    
  OperationDetails:
    description: "각 공정의 상세 정보"
    uri: "aas://FactoryTwin/ScenarioData/OperationsData"
    method: "GET"
    output_file: "operations.json"
    required: true
    
  ProcessDurations:
    description: "공정별 작업 시간"
    uri: "aas://FactoryTwin/ScenarioData/OperationDurationsData"
    method: "GET"
    output_file: "operation_durations.json"
    required: true
    
  TransferTimes:
    description: "설비 간 이동 시간"
    uri: "aas://FactoryTwin/ScenarioData/TransferTimesData"
    method: "GET"
    output_file: "machine_transfer_time.json"
    required: true
    
  JobReleaseSchedule:
    description: "작업 투입 스케줄"
    uri: "aas://FactoryTwin/ScenarioData/JobReleaseData"
    method: "GET"
    output_file: "job_release.json"
    required: true
    
  MachineStatus:
    description: "설비 상태 정보"
    uri: "aas://FactoryTwin/ScenarioData/MachinesData"
    method: "GET"
    output_file: "machines.json"
    required: true

# 시나리오 출력 설정
scenario_output:
  base_directory: "scenarios"
  scenario_name_template: "{product_id}_{timestamp}"
  manifest_generation: true
  cleanup_after_execution: false
```

---

## 🐳 NSGA-II Docker 컨테이너 구현

### Dockerfile
```dockerfile
FROM python:3.9-slim

# NSGA-II 시뮬레이터 설치
WORKDIR /app
RUN git clone https://github.com/Otober/AASX.git nsga2-simulator
WORKDIR /app/nsga2-simulator

# 종속성 설치
RUN pip install -r requirements.txt

# 시나리오 디렉터리 생성
RUN mkdir -p scenarios

# 실행 스크립트
COPY run_simulation.sh /app/
RUN chmod +x /app/run_simulation.sh

ENTRYPOINT ["/app/run_simulation.sh"]
```

### run_simulation.sh
```bash
#!/bin/bash
set -e

SCENARIO_NAME=${1:-"my_case"}
SCENARIO_PATH="/app/scenarios/${SCENARIO_NAME}"

echo "🚀 Starting NSGA-II simulation for scenario: ${SCENARIO_NAME}"

# 시나리오 디렉터리 확인
if [ ! -d "$SCENARIO_PATH" ]; then
    echo "❌ Scenario directory not found: $SCENARIO_PATH"
    exit 1
fi

# 필수 파일 확인
REQUIRED_FILES=("jobs.json" "operations.json" "machines.json" 
                "operation_durations.json" "machine_transfer_time.json" "job_release.json")

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$SCENARIO_PATH/$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done

echo "✅ All required files found"

# NSGA-II 시뮬레이터 실행
cd /app/nsga2-simulator
python3 simulator/main.py --scenario "scenarios/${SCENARIO_NAME}"

echo "✅ Simulation completed"

# 결과 파일 확인
if [ -f "$SCENARIO_PATH/simulator_optimization_result.json" ]; then
    echo "📊 Results available at: simulator_optimization_result.json"
    # 결과 요약 출력
    python3 -c "
import json
with open('$SCENARIO_PATH/simulator_optimization_result.json', 'r') as f:
    result = json.load(f)
    print(f'Makespan: {result.get(\"makespan\", \"N/A\")}')
    print(f'Schedule length: {len(result.get(\"schedule\", []))}')
"
else
    echo "❌ No results file generated"
    exit 1
fi
```

### Docker 빌드 및 테스트 스크립트
```bash
#!/bin/bash
# build_and_test_nsga2.sh

echo "🔨 Building NSGA-II Docker image..."
docker build -t factory-nsga2:latest .

echo "📁 Creating test scenario..."
mkdir -p test_scenarios/my_case

# 테스트 데이터 생성 (예시)
cat > test_scenarios/my_case/jobs.json << 'EOF'
{
  "jobs": [
    {"id": "J1", "operations": ["O1", "O2"], "due_date": "2025-08-13"},
    {"id": "J2", "operations": ["O2", "O3"], "due_date": "2025-08-14"}
  ]
}
EOF

cat > test_scenarios/my_case/operations.json << 'EOF'
{
  "operations": [
    {"id": "O1", "type": "machining", "resources": ["M1"]},
    {"id": "O2", "type": "assembly", "resources": ["M2"]},
    {"id": "O3", "type": "testing", "resources": ["M3"]}
  ]
}
EOF

# 나머지 JSON 파일들도 생성...

echo "🚀 Testing NSGA-II container..."
docker run --rm \
  -v $(pwd)/test_scenarios:/app/scenarios \
  factory-nsga2:latest my_case

echo "✅ NSGA-II container test completed"
```

---

## 💻 구현 구조

### Goal3SWRLExecutor 클래스
```python
class Goal3SWRLExecutor:
    """Goal3 전용 SWRL 실행기"""
    
    def __init__(self):
        self.selection_engine = SelectionEngine()
        self.data_orchestrator = DataOrchestrator()
        self.model_executor = ModelExecutor()
    
    def execute_goal3(self, goal3_request: Dict) -> Dict:
        """Goal3 요청을 SWRL 파이프라인으로 실행"""
        
        # 1. Goal3 입력 → QueryGoal 변환
        query_goal = self._convert_to_query_goal(goal3_request)
        
        # 2. SWRL 모델 선택 (NSGA-II 선택됨)
        swrl_result = self.selection_engine.select_model(query_goal)
        
        # 3. 데이터 수집 및 시나리오 파일 생성
        orchestration_result = self.data_orchestrator.orchestrate_data(swrl_result)
        
        # 4. NSGA-II 시뮬레이터 실행
        if orchestration_result["readyForExecution"]:
            simulation_result = self.model_executor.execute_nsga2(
                orchestration_result["scenarioPath"]
            )
            
            # 5. 결과를 Goal3 형식으로 변환
            return self._convert_to_goal3_response(simulation_result)
        else:
            raise RuntimeError("Data orchestration failed")
```

### ModelExecutor 클래스 (신규)
```python
class ModelExecutor:
    """모델 실행 엔진"""
    
    def execute_nsga2(self, scenario_path: str) -> Dict:
        """NSGA-II Docker 컨테이너 실행"""
        
        # Kubernetes Job 생성 및 실행
        job_manifest = self._create_k8s_job_manifest(scenario_path)
        job_result = self._execute_k8s_job(job_manifest)
        
        # 결과 파일 읽기
        result_file = os.path.join(scenario_path, "simulator_optimization_result.json")
        if os.path.exists(result_file):
            with open(result_file, 'r') as f:
                return json.load(f)
        else:
            raise RuntimeError("NSGA-II simulation failed - no results")
    
    def _create_k8s_job_manifest(self, scenario_path: str) -> Dict:
        """Kubernetes Job 매니페스트 생성"""
        scenario_name = os.path.basename(scenario_path)
        
        return {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": f"nsga2-simulation-{scenario_name}",
                "namespace": "factory-automation"
            },
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "name": "nsga2-simulator",
                            "image": "factory-nsga2:latest",
                            "args": [scenario_name],
                            "volumeMounts": [{
                                "name": "scenario-data",
                                "mountPath": "/app/scenarios"
                            }]
                        }],
                        "volumes": [{
                            "name": "scenario-data",
                            "persistentVolumeClaim": {
                                "claimName": "factory-scenarios-pvc"
                            }
                        }],
                        "restartPolicy": "Never"
                    }
                }
            }
        }
```

---

## 📊 NSGA-II 출력 형식 분석

### 예상 simulator_optimization_result.json 구조
```json
{
  "metadata": {
    "scenario_name": "my_case",
    "execution_time": 45.3,
    "algorithm": "NSGA-II",
    "generations": 100,
    "population_size": 50
  },
  "results": {
    "makespan": 1440.5,
    "total_tardiness": 120.0,
    "completion_times": {
      "J1": "2025-08-13T10:30:00Z",
      "J2": "2025-08-13T14:15:00Z",
      "J3": "2025-08-13T16:45:00Z"
    }
  },
  "schedule": [
    {
      "job_id": "J1",
      "operation_id": "O1", 
      "machine_id": "M1",
      "start_time": 0,
      "duration": 60,
      "end_time": 60
    }
  ],
  "pareto_front": [
    {"makespan": 1440.5, "tardiness": 120.0},
    {"makespan": 1450.2, "tardiness": 80.0}
  ]
}
```

### Goal3 응답 변환 로직
```python
def _convert_to_goal3_response(self, simulation_result: Dict) -> Dict:
    """NSGA-II 결과를 Goal3 응답으로 변환"""
    
    # 첫 번째 완료 시간 추출
    completion_times = simulation_result["results"]["completion_times"]
    first_completion = min(completion_times.values())
    
    # 신뢰도 계산 (makespan 기반)
    makespan = simulation_result["results"]["makespan"]
    confidence = min(0.95, 1.0 - (makespan / 2000))  # 단순 계산 예시
    
    return {
        "result": {
            "predicted_completion_time": first_completion,
            "confidence": confidence,
            "simulator_type": "aasx-main",
            "makespan": makespan,
            "total_jobs": len(completion_times)
        }
    }
```

---

## 🚀 구현 단계

### Phase 1: NSGA-II 컨테이너화 (Week 1)
1. **Day 1**: NSGA-II 저장소 분석 및 Docker 환경 구성
2. **Day 2**: Dockerfile 작성 및 기본 컨테이너 빌드
3. **Day 3**: 테스트 시나리오 데이터 생성 및 컨테이너 테스트
4. **Day 4**: 출력 형식 분석 및 파싱 로직 개발
5. **Day 5**: Kubernetes Job 실행 테스트

### Phase 2: SWRL 통합 (Week 2)
1. **Day 6-7**: SWRL 설정 파일 확장 (모델 등록, 규칙, 데이터 소스)
2. **Day 8-9**: DataOrchestrator 시나리오 파일 생성 기능 추가
3. **Day 10**: Goal3SWRLExecutor 구현

### Phase 3: 전체 통합 (Week 3)
1. **Day 11-12**: Factory-automation-k8s 통합
2. **Day 13-14**: End-to-End 테스트
3. **Day 15**: 문서화 및 최적화

---

## 🧪 테스트 계획

### NSGA-II 컨테이너 테스트
1. **단위 테스트**: 컨테이너 빌드 및 기본 실행
2. **통합 테스트**: 6개 JSON 입력 → 결과 출력
3. **성능 테스트**: 다양한 시나리오 크기별 실행 시간
4. **Kubernetes 테스트**: Job 실행 및 PVC 마운트

### 전체 파이프라인 테스트
1. **Goal3 입력 → SWRL QueryGoal 변환**
2. **SWRL 모델 선택 → NSGA-II 선택 확인**
3. **AAS 데이터 수집 → 시나리오 파일 생성**
4. **NSGA-II 실행 → 결과 파싱**
5. **Goal3 응답 형식 변환**

---

## 📝 성공 기준

### 기능적 요구사항
- ✅ NSGA-II Docker 컨테이너 정상 실행
- ✅ 6개 JSON 파일 → 시뮬레이션 결과 생성
- ✅ Goal3 요청 → SWRL 파이프라인 → 응답 변환
- ✅ Kubernetes 환경에서 Job 실행

### 비기능적 요구사항
- **성능**: 시뮬레이션 실행 시간 < 10분
- **안정성**: 95% 이상 성공률
- **확장성**: 다른 모델 추가 가능한 구조
- **추적성**: 전 과정 manifest.json 기록

---

## 🔧 기술 스택

- **SWRL**: SelectionEngine, DataOrchestrator (Python)
- **NSGA-II**: https://github.com/Otober/AASX (Python)
- **Container**: Docker, Kubernetes Job
- **Storage**: PVC (Persistent Volume Claim)
- **AAS**: Asset Administration Shell Server
- **Config**: YAML, JSON

---

## 📚 참고 자료

- [SWRL 모듈 아키텍처](~/desktop/swrl/docs/)
- [NSGA-II 시뮬레이터](https://github.com/Otober/AASX)
- [Goal3 구현 논의](goal3_implementation_discussion.md)
- [AAS 통합 아키텍처](aas_integration_architecture.md)

---

**작성일**: 2025-09-22  
**작성자**: Claude + 사용자 협업  
**버전**: 1.0  
**상태**: 구현 준비 완료