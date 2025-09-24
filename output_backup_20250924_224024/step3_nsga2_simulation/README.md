# Step 3: NSGA-II Simulation

## 📝 설명  
DataOrchestrator에서 생성된 JSON 파일들을 사용해 NSGA-II 시뮬레이션을 실행하는 단계

## 📂 input/
- `jobs.json`, `operations.json`, `machines.json` 등: 시뮬레이션 입력 파일들

## 📂 output/
- `goal3_manifest.json`: 실행 메타데이터
- `simulator_optimization_result.json`: 최적화 결과
- `job_info.csv`: 작업 정보 상세
- `operation_info.csv`: 오퍼레이션 실행 정보
- `agv_logs_*.xlsx`: AGV 로그 파일들
- `simulation_metadata.json`: 시뮬레이션 실행 정보

## 🔧 처리 방식
- Docker 컨테이너: `factory-nsga2:latest`
- 알고리즘: branch_and_bound  
- 실행 시간: ~33초
- 예측 완료 시간: 3600초
