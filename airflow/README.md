# Airflow DAG for Goal3 Visualization

Goal3 QueryGoal 실행 과정을 Airflow DAG UI로 시각화하는 가이드입니다.

## 📋 개요

**목적**: 터미널 로그 대신 Airflow 웹 UI에서 Goal3의 Pipeline + Runtime 실행 과정을 시각적으로 확인

**DAG 구조**:
```
create_querygoal (Pipeline 전체)
    ↓
execute_runtime (Runtime 전체)
    ↓
summarize_results (결과 요약)
```

---

## 🚀 빠른 시작

### 1. Airflow 설치

```bash
# 프로젝트 루트로 이동
cd /Users/jsh/Desktop/aas-project/gemini-ver/factory-automation-k8s

# Airflow 설치 (requirements.txt에 이미 포함됨)
pip install apache-airflow

# 또는 전체 의존성 재설치
pip install -r requirements.txt
```

### 2. Airflow 환경 설정

```bash
# Airflow 홈 디렉터리 설정
export AIRFLOW_HOME=~/airflow

# DAG 폴더 경로 설정 (현재 프로젝트의 airflow/dags)
export AIRFLOW__CORE__DAGS_FOLDER=/Users/jsh/Desktop/aas-project/gemini-ver/factory-automation-k8s/airflow/dags

# (선택) 로그 레벨 설정
export AIRFLOW__LOGGING__LOGGING_LEVEL=INFO
```

### 3. Airflow 데이터베이스 초기화

```bash
# DB 초기화 (SQLite - 로컬 개발용)
airflow db init
```

### 4. Airflow 사용자 생성

```bash
# Admin 사용자 생성
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```

### 5. Airflow 서버 실행

**터미널 2개 필요**:

**터미널 1 - Webserver**:
```bash
cd /Users/jsh/Desktop/aas-project/gemini-ver/factory-automation-k8s
export AIRFLOW_HOME=~/airflow
export AIRFLOW__CORE__DAGS_FOLDER=/Users/jsh/Desktop/aas-project/gemini-ver/factory-automation-k8s/airflow/dags
airflow webserver --port 8080
```

**터미널 2 - Scheduler**:
```bash
cd /Users/jsh/Desktop/aas-project/gemini-ver/factory-automation-k8s
export AIRFLOW_HOME=~/airflow
export AIRFLOW__CORE__DAGS_FOLDER=/Users/jsh/Desktop/aas-project/gemini-ver/factory-automation-k8s/airflow/dags
airflow scheduler
```

### 6. Airflow UI 접속

1. 브라우저에서 `http://localhost:8080` 접속
2. 로그인: `admin` / `admin`
3. DAG 목록에서 `goal3_execution` 찾기

---

## 🎬 시연 방법

### 방법 1: 웹 UI에서 실행

1. **DAG 페이지 열기**
   - DAG 목록에서 `goal3_execution` 클릭

2. **DAG 실행**
   - 우측 상단 "Trigger DAG" 버튼 클릭 (▶️ 아이콘)

3. **실행 확인**
   - **Graph View**: 각 Task의 실행 상태를 그래프로 확인
     - ⬜ 회색: 대기 중
     - 🟦 파란색: 실행 중
     - 🟩 초록색: 성공
     - 🟥 빨간색: 실패

4. **상세 로그 확인**
   - 각 Task 클릭 → **Log 탭** → 실행 로그 확인
   - **XCom 탭**: Task 간 전달된 데이터 확인

5. **결과 확인**
   - `summarize_results` Task의 로그에서 최종 결과 확인

### 방법 2: CLI에서 실행

```bash
# DAG 수동 트리거
airflow dags trigger goal3_execution

# 실행 상태 확인
airflow dags list-runs -d goal3_execution

# 특정 Task 로그 확인
airflow tasks logs goal3_execution create_querygoal <execution_date>
```

---

## 📊 DAG 구조 상세

### Task 1: create_querygoal
- **역할**: Pipeline 전체 (자연어 → QueryGoal 변환)
- **소요 시간**: 약 5-10초
- **출력**: QueryGoal JSON (XCom으로 저장)
- **색상**: 파란색 (#1E88E5)

**6단계 파이프라인**:
1. Pattern Matching - Goal Type 추출
2. Template Loading - QueryGoal 템플릿 생성
3. Parameter Filling - 파라미터 주입
4. ActionPlan Resolution - ActionPlan 설정
5. Model Selection - SWRL 추론으로 모델 선택
6. Validation - QueryGoal 스키마 검증

### Task 2: execute_runtime
- **역할**: Runtime 전체 (QueryGoal 실행)
- **소요 시간**: 약 10-30초 (AAS 서버 통신 + 시뮬레이션)
- **입력**: XCom에서 QueryGoal 가져오기
- **출력**: 실행 결과 (XCom으로 저장)
- **색상**: 초록색 (#43A047)

**3단계 런타임**:
1. swrlSelection - Manifest 파일 로딩
2. yamlBinding - AAS 서버에서 데이터 수집 (JobOrders, Machines 등)
3. simulation - NSGA-II 시뮬레이션 실행

### Task 3: summarize_results
- **역할**: 결과 요약 및 리포트 생성
- **소요 시간**: 1-2초
- **색상**: 오렌지색 (#FB8C00)

**출력 정보**:
- Goal ID
- 실행 상태
- 예상 생산 시간 (estimatedTime)
- 신뢰도 (confidence)
- 작업 디렉터리 정보

---

## 🔧 문제 해결

### 1. DAG이 목록에 나타나지 않는 경우

**원인**: DAG 폴더 경로가 잘못 설정됨

**해결**:
```bash
# DAG 폴더 확인
echo $AIRFLOW__CORE__DAGS_FOLDER

# 올바른 경로로 재설정
export AIRFLOW__CORE__DAGS_FOLDER=/Users/jsh/Desktop/aas-project/gemini-ver/factory-automation-k8s/airflow/dags

# Scheduler 재시작
```

### 2. DAG에 Import Error가 있는 경우

**원인**: Python 모듈 경로 문제

**해결**:
```bash
# 프로젝트 루트에서 실행 확인
cd /Users/jsh/Desktop/aas-project/gemini-ver/factory-automation-k8s

# Python path 확인
python3 -c "import sys; print(sys.path)"

# DAG 파일 구문 오류 확인
python3 -m py_compile airflow/dags/goal3_execution_dag.py
```

### 3. Task 실행 시 AAS 서버 연결 오류

**원인**: AAS 서버가 실행되지 않음

**해결**:
```bash
# AAS 서버 실행 확인
curl http://127.0.0.1:5001/shells

# 서버가 없다면 실행 (별도 터미널)
# (AAS 서버 실행 명령어)
```

### 4. asyncio 관련 오류

**원인**: Airflow Worker가 비동기 함수 처리 실패

**해결**: `goal3_execution_dag.py`의 `task_execute_runtime` 함수에서 이미 asyncio 이벤트 루프 처리가 구현되어 있습니다. 그래도 오류가 발생하면:

```python
# DAG 파일에서 확인
loop = asyncio.get_event_loop()
if loop.is_closed():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
```

---

## 📁 파일 구조

```
factory-automation-k8s/
├── airflow/
│   ├── dags/
│   │   └── goal3_execution_dag.py    # 메인 DAG 파일
│   └── README.md                      # 이 파일
├── querygoal/                         # QueryGoal 모듈
│   ├── pipeline/                      # Pipeline 단계
│   └── runtime/                       # Runtime 단계
└── requirements.txt                   # apache-airflow 포함
```

---

## 🎥 시연 영상 촬영 팁

1. **화면 녹화 도구**: QuickTime Player 또는 OBS Studio
2. **녹화 범위**: 브라우저 전체 화면 (Airflow UI)
3. **추천 순서**:
   - DAG 목록 화면
   - `goal3_execution` DAG 페이지
   - "Trigger DAG" 클릭
   - Graph View에서 실시간 실행 확인
   - `create_querygoal` Task 로그 확인
   - `execute_runtime` Task 로그 확인
   - `summarize_results` 최종 결과 확인
4. **편집 포인트**: 각 Task의 로그를 클로즈업하여 상세 정보 표시

---

## 📚 추가 자료

- [Airflow 공식 문서](https://airflow.apache.org/docs/)
- [Goal3 E2E Flow 문서](../docs/Goal3_E2E_Flow_Plan_Corrected.md)
- [QueryGoal 시스템 개요](../CLAUDE.md)

---

## 🆘 지원

문제가 발생하면:
1. Airflow 로그 확인: `~/airflow/logs/`
2. DAG 파일 구문 검사: `python3 -m py_compile airflow/dags/goal3_execution_dag.py`
3. 프로젝트 루트에서 실행 확인
