# Step 2: DataOrchestrator Processing

## 📝 설명
AASX 서버에서 추출된 데이터를 NSGA-II 시뮬레이션용 JSON 파일로 변환하는 단계

## 📂 input/
- `aasx_extracted_data.json`: Step 1에서 추출된 Property.value 데이터

## 📂 output/
- `jobs.json`: 작업 정보 (30개 작업)
- `operations.json`: 오퍼레이션 정보 (95개 오퍼레이션)  
- `machines.json`: 머신 정보 (4개 머신)
- `operation_durations.json`: 작업 소요 시간
- `machine_transfer_time.json`: 머신 간 이동 시간
- `job_release.json`: 작업 릴리즈 시간
- `orchestrator_execution_log.json`: 실행 로그

## 🔧 처리 방식
- JSON 문자열 파싱
- 시뮬레이터 요구 형식으로 변환
- 머신별 capability/status 데이터 통합
