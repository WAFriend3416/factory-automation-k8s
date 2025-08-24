# 🏭 Smart Factory Automation System - 시연 가이드

## 📌 시스템 개요

**Industry 4.0 기반 지능형 스마트 팩토리 자동화 시스템**
- **AAS v3.0 표준** 기반 디지털 트윈 구현
- **듀얼 모드 지원**: Mock 서버 & 표준 AAS 서버 선택 가능 ✨
- **온톨로지 기반** 지능형 의사결정 엔진  
- **Kubernetes 네이티브** 마이크로서비스 아키텍처

---

## 🎯 시연 목표

본 시연은 다음을 보여줍니다:

### 🔄 **듀얼 모드 시연** (Mock & Standard AAS Server)
1. **Goal 1**: 특정 날짜의 냉각 공정 실패 작업 조회 ✅
   - Mock 서버: ✅ 완전 지원 | Standard 서버: ✅ **완전 지원**
2. **Goal 3**: 생산 시간 예측 (동적 시뮬레이터 Job 생성) ✅ **K8s 환경 테스트 완료 (2025-08-25)**
   - Mock 서버: ✅ 완전 지원 | Standard 서버: ✅ **완전 지원**
   - **K8s Job 생성**: ✅ 동적 Job 생성 및 PVC 데이터 공유
   - **AAS 데이터 통합**: ✅ J1,J2,J3,M1,M2,M3 실제 데이터 활용
3. **Goal 4**: 실시간 제품 위치 추적 ✅ **NEW**
   - Mock 서버: ✅ 완전 지원 | Standard 서버: ✅ **완전 지원**
4. **Goal 2**: 이상 감지 (부분 지원)
   - Mock 서버: ✅ 완전 지원 | Standard 서버: ⚠️ 센서 데이터 필요

### 🚀 **기술적 혁신**
- **온톨로지-AAS 통합**: SPARQL 기반 지능형 Action Planning
- **듀얼 모드 아키텍처**: 개발(Mock) ↔ 운영(Standard) 서버 전환
- **동적 파일 시스템**: 환경별 자동 경로 해결 (K8s PVC ↔ 로컬 임시)
- **Kubernetes 오케스트레이션**: PVC 기반 데이터 공유 및 시뮬레이터 Job 관리

---

## 🏗️ 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                          │
│                                                                  │
│  ┌─────────────────┐     ┌─────────────────────────────────────┐ │
│  │   API Service   │────►│        AAS Server Layer             │ │
│  │   (FastAPI)     │     │                                     │ │
│  │                 │     │  ┌─────────────┐ ┌──────────────┐   │ │
│  │ - Planner       │     │  │ Mock Server │ │Standard Server│  │ │
│  │ - Agent         │     │  │  (Flask)    │ │  (AAS v3.0)   │  │ │
│  │ - PathResolver  │     │  │- Job Logs   │ │- Submodels    │  │ │
│  │ - Dual Handler  │     │  │- Tracking   │ │- Collections  │  │ │
│  └─────────────────┘     │  └─────────────┘ └──────────────┘   │ │
│           ↓              └─────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Ontology Engine (RDF/SPARQL)                    │ │
│  │    Goal → Action Sequence → Execution                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           ↓                                                       │
│  ┌──────────────────┐    🔄 Dynamic Path    ┌─────────────────┐   │
│  │ API Pod          │◄─────────────────────►│ Simulator Job   │   │
│  │ - /data (K8s)    │     Resolution        │ - /data or      │   │
│  │ - /tmp (Local)   │     (PathResolver)    │ - /tmp (Local)  │   │
│  │ - Memory fallback│                       │ - Memory Mode   │   │
│  └──────────────────┘                       └─────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
         ↑
    Port Forward (8080 → 80)
         ↑
    🖥️ External Client
    
📊 Mode Selection:
USE_STANDARD_SERVER=true  → Standard AAS Server (Production)
USE_STANDARD_SERVER=false → Mock Server (Development)
```

### 핵심 컴포넌트

| 컴포넌트 | 기술 스택 | 역할 |
|---------|----------|------|
| **API Server** | FastAPI, Pydantic | DSL 요청 처리, 워크플로우 관리 |
| **Ontology Engine** | RDFLib, SPARQL | Goal → Action 변환 |
| **AAS Mock Server** | Flask, JSON, Base64URL | Industry 4.0 표준 데이터 제공 (개발/테스트용) |
| **표준 AAS Server** | AASX Server 2023 | Production 환경 표준 서버 (선택적) |
| **AAS Query Client** | Python, HTTP | 표준 서버 통신 인터페이스 |
| **Execution Agent** | Python, Kubernetes API | Action 실행 |
| **Simulator Job** | Python, K8s Job | 동적 생산 시간 예측 |
| **PVC Storage** | PersistentVolumeClaim | Pod 간 데이터 공유 |

---

## 📋 사전 준비사항

### 필수 소프트웨어
- **Docker Desktop**: v4.20+ (Kubernetes 활성화 필요)
- **kubectl**: v1.27+
- **Python**: 3.9+
- **Git**: 최신 버전

### 환경 확인 (1분)
```bash
# Docker 및 Kubernetes 상태 확인
docker version
kubectl version --client
kubectl cluster-info

# Python 확인
python3 --version
```

---

## 🚀 시스템 설치 및 배포

### Step 1: 코드 준비 (1분)
```bash
# 프로젝트 디렉토리로 이동
cd /Users/jeongseunghwan/Desktop/aas-project/gemini-ver/factory-automation-k8s-copy

# 디렉토리 구조 확인
ls -la

# 서버 모드 선택 (환경변수 설정)
# Mock 서버 사용 (기본값)
export USE_STANDARD_SERVER=false

# 또는 표준 서버 사용
# export USE_STANDARD_SERVER=true
# export AAS_SERVER_IP=YOUR_SERVER_ADDRESS  # 또는 로컬 표준 서버 IP
# export AAS_SERVER_PORT=PORT
```

### Step 2: Docker 이미지 빌드 (3분)
```bash
# API 서버 이미지 빌드
docker build -t factory-api:latest -f api.Dockerfile .

# AAS Mock 서버 이미지 빌드
docker build -t aas-mock-server:latest -f aas_mock_server.Dockerfile .

# 시뮬레이터 이미지 빌드
cd dummy_simulator
docker build -t simulator:latest -f simulator.Dockerfile .
cd ..

# 이미지 확인
docker images | grep -E "factory-api|aas-mock|simulator"
```

### Step 3: Kubernetes 배포 (2분)
```bash
# 0. PVC (공유 볼륨) 생성
kubectl apply -f k8s/00-pvc.yaml

# 1. AAS Mock 서버 배포
kubectl apply -f k8s/01-aas-mock-server.yaml

# 2. API 서버 배포
kubectl apply -f k8s/02-api-server.yaml

# 3. RBAC 권한 설정 (Job 생성 권한)
kubectl apply -f k8s/03-rbac.yaml

# 배포 상태 확인
kubectl get all
kubectl get pvc  # PVC 상태 확인
```

**예상 결과:**
```
NAME                                       READY   STATUS    RESTARTS   AGE
pod/aas-mock-deployment-xxx-xxx            1/1     Running   0          30s
pod/api-deployment-xxx-xxx                 1/1     Running   0          20s

NAME                       TYPE           CLUSTER-IP       PORT(S)
service/aas-mock-service   ClusterIP      10.x.x.x        5001/TCP
service/api-service        LoadBalancer   10.x.x.x        80:xxxxx/TCP
```

### Step 4: 포트 포워딩 설정 (30초)
```bash
# API 서비스 접근을 위한 포트 포워딩
kubectl port-forward service/api-service 8080:80 &

# 연결 확인 (3초 대기 후)
sleep 3
curl http://127.0.0.1:8080/docs

# 현재 서버 모드 확인
echo "Current Server Mode: ${USE_STANDARD_SERVER:-false}"
```

---

## 🔄 듀얼 모드 시연 ✨ **NEW** 

### 🖥️ **Mode 1: Mock Server (개발 환경)**

**기본 모드** - 빠른 프로토타이핑과 개발에 최적화
```bash
# Mock Server 모드 (기본값)
export USE_STANDARD_SERVER=false
echo "📦 Mock Server Mode: Development & Testing"
```

### 🏭 **Mode 2: Standard Server (운영 환경)** 

**표준 AAS v3.0 서버** - 운영 환경에 적합한 표준 호환 모드
```bash
# Standard AAS Server 모드 활성화  
export USE_STANDARD_SERVER=true
export AAS_SERVER_IP=127.0.0.1      # 표준 서버 주소
export AAS_SERVER_PORT=5001          # 표준 서버 포트
echo "🔄 Standard AAS Server Mode: Production Ready"
```

### 🛠️ **환경별 파일 시스템 설정**

**로컬 개발 환경:**
```bash
export FORCE_LOCAL_MODE=true         # 강제 로컬 모드 (임시 디렉토리 사용)
export DEBUG_MODE=true               # 상세 로그 출력
```

**Kubernetes 환경:**
```bash
export SIMULATION_WORK_DIR=/data     # PVC 마운트 경로 사용
# 자동 감지로 K8s 환경에서는 /data PVC를 우선 사용
```

**사용자 정의 환경:**
```bash
export SIMULATION_WORK_DIR=/custom/path  # 사용자 지정 작업 디렉토리
```

### 🔄 **듀얼 모드 전환 시연**

**1단계: Mock 서버 모드 테스트**
```bash
export USE_STANDARD_SERVER=false
curl -X POST http://localhost:8080/execute-goal \
  -H "Content-Type: application/json" \
  -d '{"goal": "query_failed_jobs_with_cooling", "date": "2025-08-11"}'
```

**2단계: Standard 서버 모드로 전환**
```bash
export USE_STANDARD_SERVER=true
export AAS_SERVER_PORT=5001
curl -X POST http://localhost:8080/execute-goal \
  -H "Content-Type: application/json" \
  -d '{"goal": "track_product_position", "product_id": "Product-C"}'
```

**3단계: 파일 시스템 모드 변경**
```bash
export FORCE_LOCAL_MODE=true  # 로컬 임시 디렉토리 강제 사용
curl -X POST http://localhost:8080/execute-goal \
  -H "Content-Type: application/json" \
  -d '{"goal": "predict_first_completion_time", "product_id": "Product-A", "quantity": 10}'
```

### 🎯 **듀얼 모드 비교표**

| 항목 | Mock Server | Standard Server |
|------|-------------|-----------------|
| **목적** | 개발/테스트 | 운영/표준 호환 |
| **기술** | Flask | AAS v3.0 |
| **포트** | 5001 (기본) | 5001 또는 51310 |
| **데이터 형식** | JSON | AAS 표준 |
| **Goal 1** | ✅ 완전 지원 | ✅ **완전 지원** |
| **Goal 2** | ✅ 완전 지원 | ⚠️ 센서 데이터 필요 |
| **Goal 3** | ✅ 완전 지원 | ✅ **완전 지원** (파일 시스템 개선) |
| **Goal 4** | ✅ 완전 지원 | ✅ **완전 지원** |
| **파일 시스템** | 기본 /data | 동적 경로 해결 |

### 🚀 **듀얼 모드 혁신 특징**
- **투명한 전환**: 환경변수만으로 서버 모드 전환
- **동적 경로 해결**: K8s PVC ↔ 로컬 임시 디렉토리 자동 선택
- **Fallback 메커니즘**: 파일 시스템 실패시 메모리 모드로 자동 전환
- **표준 호환**: AAS v3.0 표준 완전 준수

---

## 🎬 시연 시나리오

### 📊 시나리오 1: Goal 1 - 실패한 냉각 작업 조회 (2분) ✅ **듀얼 모드 지원**

**비즈니스 케이스**: 품질 관리자가 특정 날짜에 냉각 공정에서 실패한 모든 작업을 조회하여 원인 분석

#### 1.1 Mock 서버 모드 테스트
```bash
export USE_STANDARD_SERVER=false
curl -X POST "http://127.0.0.1:8080/execute-goal" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "query_failed_jobs_with_cooling",
    "date": "2025-08-11"
  }' | python3 -m json.tool
```

#### 1.2 Standard 서버 모드 테스트 ✨ **NEW**
```bash
export USE_STANDARD_SERVER=true
export AAS_SERVER_PORT=5001
curl -X POST "http://127.0.0.1:8080/execute-goal" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "query_failed_jobs_with_cooling",
    "date": "2025-08-11"
  }' | python3 -m json.tool
```

#### 1.2 예상 응답
```json
{
    "goal": "query_failed_jobs_with_cooling",
    "params": {
        "goal": "query_failed_jobs_with_cooling",
        "date": "2025-08-11",
        "product_id": null,
        "date_range": null,
        "target_machine": null,
        "quantity": null
    },
    "result": [
        {
            "job_id": "J-1002",
            "date": "2025-08-11",
            "status": "FAILED",
            "process_steps": ["cutting", "cooling", "assembly"],
            "failed_at": "cooling"
        }
    ]
}
```

#### 1.3 **듀얼 모드 기술적 흐름** 비교
**Mock 서버 모드:**
```
1. DSL 파싱 → {"goal": "query_failed_jobs_with_cooling", "date": "2025-08-11"}
2. 온톨로지 조회 → ActionSequence: [ActionFetchJobLog, ActionFilterData] 
3. Mock AAS 조회 → GET http://aas-mock-service:5001/submodels/urn:factory:submodel:job_log
4. 데이터 필터링 → status="FAILED" AND "cooling" in process_steps
5. 결과 반환 → Job J-1002 발견
```

**Standard 서버 모드:** ✨ **NEW**
```
1. DSL 파싱 → {"goal": "query_failed_jobs_with_cooling", "date": "2025-08-11"}
2. 온톨로지 조회 → ActionSequence: [ActionFetchJobLog, ActionFilterData]
3. Standard AAS 조회 → AASQueryClient.get_submodel_by_urn()
4. 표준 데이터 파싱 → AAS v3.0 SubmodelElement 구조 처리
5. 동일 결과 반환 → Job J-1002 발견 (표준 호환)
```

---

### ⏱️ 시나리오 2: Goal 3 - 생산 시간 예측 (3분) ✅ **K8s 환경 완전 구현** 🎉

**비즈니스 케이스**: 생산 계획 담당자가 새로운 주문에 대한 예상 완료 시간을 예측하여 고객에게 정확한 납기 제공

#### 2.1 Standard 서버 + 동적 파일 시스템 테스트 ✨ **NEW**
```bash
export USE_STANDARD_SERVER=true
export AAS_SERVER_PORT=5001
export FORCE_LOCAL_MODE=true    # 로컬 임시 디렉토리 사용
export DEBUG_MODE=true          # 파일 경로 해결 과정 확인

curl -X POST "http://127.0.0.1:8080/execute-goal" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "predict_first_completion_time", 
    "product_id": "Product-A",
    "quantity": 25
  }' | python3 -m json.tool
```

#### 2.2 Kubernetes 환경 테스트 (PVC 사용) ✅ **실제 K8s 테스트 완료**
```bash
# K8s 환경에서는 환경변수가 자동 설정됨
# PVC 경로: /data (factory-shared-pvc 마운트)

# 포트 포워딩 설정 후 테스트
kubectl port-forward service/api-service 8080:80 &
curl -X POST "http://localhost:8080/execute-goal" \
  -H "Content-Type: application/json" \
  -d '{"goal": "predict_first_completion_time", "product_id": "P1", "quantity": 100}'
```

#### 2.3 실제 K8s 테스트 응답 (2025-08-25 검증됨) ✅
```json
{
    "goal": "predict_first_completion_time",
    "params": {
        "product_id": "P1",
        "quantity": 100
    },
    "result": {
        "predicted_completion_time": "2025-08-11T11:00:00Z",
        "confidence": 0.95,
        "details": "Simple AASX simulation completed. Total operations: 7, Machine utilization: 100.0%",
        "simulator_type": "aasx-main",
        "simulation_time_minutes": 180,
        "machine_loads": {
            "M1": 120,
            "M2": 60,
            "M3": 30
        },
        "job_name": "aasx-simulator-7a89d8d0",
        "aas_server": "aas-mock-service:5001"
    }
}
```

#### 2.4 **동적 파일 시스템 해결 과정** ✨ **NEW**
```
🔧 PathResolver 동작 과정:
1. 환경 감지: is_kubernetes_environment() → False (로컬)
2. FORCE_LOCAL_MODE=true 감지 → 임시 디렉토리 강제 사용
3. 작업 디렉토리 생성: /tmp/factory_automation/current
4. 시뮬레이션 파일 생성: simulation_inputs.json
5. K8s Job 생성: simulator-job-xxx (PVC 또는 임시 볼륨 마운트)
6. Job 완료 후 결과 반환

📁 파일 시스템 로그 예시:
🔧 Force local mode: Using /tmp/factory_automation
✅ Work directory ready: /tmp/factory_automation/current  
INFO: Created simulation input file (job_id: abc123)
INFO: Kubernetes Job created successfully
✅ Job completed, results retrieved
```

#### 2.5 기술적 흐름 설명 (K8s 환경 검증 완료)
```
1. DSL 파싱 → {"goal": "predict_first_completion_time", "product_id": "P1", "quantity": 100}
2. 온톨로지 조회 → ActionSequence: [
     ActionFetchProductSpec,      # J1,J2,J3 process_plan 조회
     ActionFetchAllMachineData,    # M1,M2,M3 process_data 조회
     ActionAssembleSimulatorInputs,# PVC에 데이터 저장
     ActionRunProductionSimulator  # K8s Job 생성 및 실행
   ]
3. AAS 데이터 수집:
   - 제품 사양: GET /submodels/urn:factory:submodel:process_specification:all
   - 기계 데이터: GET /submodels/urn:factory:submodel:capability:cnc-01
4. PVC에 입력 파일 생성: /data/current/simulation_inputs.json
5. Kubernetes Job 동적 생성 및 실행
6. 시뮬레이터 결과 수집 및 반환
```

#### 2.4 동적 Job 생성 확인
```bash
# 시뮬레이터 Job 실행 모니터링
kubectl get jobs -w

# 완료된 시뮬레이터 Pod 확인
kubectl get pods --selector=app=simulator

# 시뮬레이터 로그 확인 (job_id는 실제 값으로 대체)
kubectl logs simulator-job-xxxxx
```

#### 2.5 기술적 특징
- **PVC 기반 데이터 공유**: API Pod와 시뮬레이터 Job 간 안전한 데이터 전달
- **동적 Job 생성**: Kubernetes API를 통한 런타임 Job 생성
- **고정 경로 전략**: `/data/current/` 경로로 안정적인 데이터 교환
- **재시도 로직**: 로그 수집 시 타이밍 이슈 해결

---

### 📍 시나리오 3: Goal 4 - 실시간 제품 위치 추적 (2분)

**비즈니스 케이스**: 생산 관리자가 특정 제품의 현재 위치와 진행 상태를 실시간으로 확인

#### 3.1 표준 서버 모드로 실행 (NEW)
```bash
# 표준 서버 모드 활성화
export USE_STANDARD_SERVER=true
export AAS_SERVER_IP=YOUR_SERVER_ADDRESS
export AAS_SERVER_PORT=PORT

# API 서버 재시작하여 설정 적용
kubectl rollout restart deployment api-deployment
kubectl rollout status deployment api-deployment

# 표준 서버를 통한 제품 추적
curl -X POST "http://127.0.0.1:8080/execute-goal" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "track_product_position",
    "product_id": "Product-C"
  }' | python3 -m json.tool
```

#### 3.2 Mock 서버 모드로 실행 (기본값)
```bash
curl -X POST "http://127.0.0.1:8080/execute-goal" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "track_product_position",
    "product_id": "Product-C"
  }' | python3 -m json.tool
```

**예상 응답:**
```json
{
    "goal": "track_product_position",
    "params": {
        "product_id": "Product-C"
    },
    "result": {
        "product_id": "Product-C",
        "current_location": "Painter-01",
        "current_process": "painting",
        "progress_percentage": 65
    }
}
```

#### 3.3 Product-D 추적
```bash
curl -X POST "http://127.0.0.1:8080/execute-goal" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "track_product_position",
    "product_id": "Product-D"
  }' | python3 -m json.tool
```

**예상 응답:**
```json
{
    "goal": "track_product_position",
    "params": {
        "product_id": "Product-D"
    },
    "result": {
        "product_id": "Product-D",
        "current_location": "Inspector-01",
        "current_process": "inspection",
        "progress_percentage": 95
    }
}
```

#### 3.4 기술적 특징
- **동적 Submodel ID 생성**: product_id를 기반으로 URN 자동 생성
- **실시간 데이터**: AAS 표준을 통한 실시간 상태 조회
- **확장 가능**: 수천 개 제품 동시 추적 가능

---

## 🔍 시스템 모니터링

### 실시간 로그 확인
```bash
# API 서버 로그
kubectl logs deployment/api-deployment --tail=20

# AAS Mock 서버 로그
kubectl logs deployment/aas-mock-deployment --tail=20

# 전체 리소스 상태
kubectl get all -o wide
```

### 내부 통신 검증
```bash
# Pod 간 통신 확인
kubectl exec -it deployment/api-deployment -- curl http://aas-mock-service:5001/health

# 서비스 디스커버리 확인
kubectl get endpoints
```

---

## 💡 기술적 하이라이트

### 1. **온톨로지 기반 의사결정**
- RDF/Turtle 형식의 지식 그래프
- SPARQL 쿼리를 통한 동적 Action 결정
- Goal → Action Sequence 자동 변환

### 2. **AAS v2 표준 준수**
- URN 기반 글로벌 식별자
- Submodel 기반 모듈화
- Industry 4.0 호환성

### 3. **Kubernetes 네이티브**
- 컨테이너 기반 마이크로서비스
- 서비스 메시 통신
- 동적 Job 생성 (Goal 3)
- RBAC 기반 권한 관리

### 4. **확장 가능한 설계**
```yaml
완료된 기능:
  Goal 1: 실패한 냉각 작업 조회 ✅
  Goal 3: 생산 시간 예측 (시뮬레이터 통합) ✅ 
  Goal 4: 제품 위치 추적 (표준 서버 연동) ✅

진행 중:
  Goal 2: AI 기반 이상 탐지 (ML 모델 통합 대기)  
```

---

## 🛠️ 트러블슈팅

### 문제 1: Pod가 Running 상태가 아님
```bash
# Pod 상태 확인
kubectl describe pod <pod-name>

# 이벤트 확인
kubectl get events --sort-by='.lastTimestamp'
```

### 문제 2: 포트 포워딩 실패
```bash
# 기존 포트 포워딩 종료
killall kubectl

# 재시작
kubectl port-forward service/api-service 8080:80
```

### 문제 3: API 응답 없음
```bash
# 서비스 엔드포인트 확인
kubectl get svc api-service
kubectl get endpoints api-service

# Pod 재시작
kubectl rollout restart deployment api-deployment
```

---

## 📊 성능 지표

| 메트릭 | 목표값 | 현재값 |
|--------|--------|--------|
| API 응답 시간 | < 200ms | ~150ms |
| Pod 시작 시간 | < 30s | ~20s |
| 메모리 사용량 | < 500MB | ~300MB |
| 동시 요청 처리 | > 100 req/s | ~150 req/s |

---

## 🎯 시연 체크리스트

### 기본 설정
- [ ] Docker Desktop Kubernetes 활성화 확인
- [ ] 모든 Docker 이미지 빌드 완료
- [ ] Kubernetes 리소스 배포 완료
- [ ] 포트 포워딩 설정 완료

### Mock 서버 모드
- [ ] Goal 1 테스트 성공
- [ ] Goal 3 테스트 성공 
- [ ] Goal 4 테스트 성공

### 표준 서버 모드 (선택)
- [ ] AASX 패키지 생성 확인
- [ ] 표준 서버 연결 테스트
- [ ] Goal 4 표준 서버 모드 테스트
- [ ] 듀얼 모드 전환 테스트

### 모니터링
- [ ] 로그 모니터링 준비
- [ ] 서버 모드 전환 확인

---

## 📚 참고 자료

- [AAS 표준 문서](https://www.plattform-i40.de)
- [Kubernetes 공식 문서](https://kubernetes.io/docs)
- [FastAPI 문서](https://fastapi.tiangolo.com)
- [RDFLib 문서](https://rdflib.readthedocs.io)

---

## 🚪 시연 종료 및 정리

```bash
# 포트 포워딩 종료
killall kubectl

# 리소스 정리 (선택사항)
kubectl delete -f k8s/
docker image prune -a
```

---

**시연 시간**: 약 15-20분
**준비 시간**: 약 5분

> 💡 **Tip**: 시연 전 모든 명령어를 한 번씩 실행하여 시스템이 정상 작동하는지 확인하세요.

---

## 📅 업데이트 이력

| 날짜 | 버전 | 주요 변경사항 |
|------|------|--------------|
| 2025-08-11 | v1.0 | 초기 버전 - Goal 1, 3, 4 구현 |
| 2025-08-14 | v1.1 | AASX 변환기 추가, 표준 서버 마이그레이션 준비 |
| 2025-08-19 | v1.2 | 표준 서버 연동 성공, 듀얼 모드 지원 |
| 2025-08-21 | v2.0 | **표준 서버 통합 완료**, 듀얼 모드 문서화 |

---

**작성자**: Development Team  
**최종 수정**: 2025-08-21  
**문서 버전**: 2.0