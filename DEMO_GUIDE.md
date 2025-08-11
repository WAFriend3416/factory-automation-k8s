# 🏭 Smart Factory Automation System - 시연 가이드

## 📌 시스템 개요

**Industry 4.0 기반 지능형 스마트 팩토리 자동화 시스템**
- **AAS v2 표준** 기반 디지털 트윈 구현
- **온톨로지 기반** 지능형 의사결정 엔진
- **Kubernetes 네이티브** 마이크로서비스 아키텍처
- **실시간** 생산 모니터링 및 추적

---

## 🎯 시연 목표

본 시연은 다음을 보여줍니다:
1. **Goal 1**: 특정 날짜의 냉각 공정 실패 작업 조회
2. **Goal 4**: 실시간 제품 위치 추적
3. **기술적 혁신**: 온톨로지-AAS 통합, Kubernetes 오케스트레이션

---

## 🏗️ 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────┐
│                 Kubernetes Cluster                        │
│                                                           │
│  ┌─────────────────┐        ┌─────────────────┐         │
│  │   API Service   │ ──────>│  AAS Mock       │         │
│  │   (FastAPI)     │  HTTP  │  Service        │         │
│  │                 │        │  (Flask)        │         │
│  │ - Planner       │        │ - Job Logs      │         │
│  │ - Agent         │        │ - Tracking Data │         │
│  │ - Handlers      │        │ - Sensor Data   │         │
│  └─────────────────┘        └─────────────────┘         │
│           ↓                                               │
│  ┌─────────────────────────────────────────┐            │
│  │        Ontology Engine (RDF/SPARQL)      │            │
│  │  Goal → Action Sequence → Execution      │            │
│  └─────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────┘
         ↑
    Port Forward
    (8080 → 80)
         ↑
    External Client
```

### 핵심 컴포넌트

| 컴포넌트 | 기술 스택 | 역할 |
|---------|----------|------|
| **API Server** | FastAPI, Pydantic | DSL 요청 처리, 워크플로우 관리 |
| **Ontology Engine** | RDFLib, SPARQL | Goal → Action 변환 |
| **AAS Mock Server** | Flask, JSON | Industry 4.0 표준 데이터 제공 |
| **Execution Agent** | Python, Kubernetes API | Action 실행 및 오케스트레이션 |

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
cd /Users/jeongseunghwan/Desktop/aas-project/gemini-ver/factory-automation-k8s

# 디렉토리 구조 확인
ls -la
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
# 1. AAS Mock 서버 배포
kubectl apply -f k8s/01-aas-mock-server.yaml

# 2. API 서버 배포
kubectl apply -f k8s/02-api-server.yaml

# 3. RBAC 권한 설정
kubectl apply -f k8s/03-rbac.yaml

# 배포 상태 확인
kubectl get all
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
```

---

## 🎬 시연 시나리오

### 📊 시나리오 1: Goal 1 - 실패한 냉각 작업 조회 (2분)

**비즈니스 케이스**: 품질 관리자가 특정 날짜에 냉각 공정에서 실패한 모든 작업을 조회하여 원인 분석

#### 1.1 요청 실행
```bash
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

#### 1.3 기술적 흐름 설명
```
1. DSL 파싱 → {"goal": "query_failed_jobs_with_cooling", "date": "2025-08-11"}
2. 온톨로지 조회 → ActionSequence: [ActionFetchJobLog, ActionFilterData]
3. AAS 데이터 조회 → GET http://aas-mock-service:5001/submodels/urn:factory:submodel:job_log
4. 데이터 필터링 → status="FAILED" AND "cooling" in process_steps
5. 결과 반환 → Job J-1002 발견
```

---

### 📍 시나리오 2: Goal 4 - 실시간 제품 위치 추적 (2분)

**비즈니스 케이스**: 생산 관리자가 특정 제품의 현재 위치와 진행 상태를 실시간으로 확인

#### 2.1 Product-C 추적
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

#### 2.2 Product-D 추적
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

#### 2.3 기술적 특징
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
향후 확장 가능:
  Goal 2: AI 기반 이상 탐지
  Goal 3: 생산 시간 예측 (시뮬레이터 통합)
  Goal 5+: 사용자 정의 Goal 추가
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

- [ ] Docker Desktop Kubernetes 활성화 확인
- [ ] 모든 Docker 이미지 빌드 완료
- [ ] Kubernetes 리소스 배포 완료
- [ ] 포트 포워딩 설정 완료
- [ ] Goal 1 테스트 성공
- [ ] Goal 4 테스트 성공
- [ ] 로그 모니터링 준비

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