# Step 4: NSGA-II Simulation

## 📝 설명  
SWRL 추론과 DataOrchestrator를 거쳐 생성된 JSON 파일들로 Goal3 NSGA-II 시뮬레이션 실행

## 📂 input/
- 6개 시뮬레이션 JSON 파일 (SWRL R002 규칙으로 생성됨)

## 📂 output/
- `goal3_manifest.json`: Goal3 실행 메타데이터
- `simulator_optimization_result.json`: 최적화 결과 (Goal3 답변)
- `job_info.csv`: 30개 작업 상세 실행 정보
- `operation_info.csv`: 95개 오퍼레이션 실행 정보
- `agv_logs_*.xlsx`: AGV 로그 파일들 (M1-M8)
- `simulation_metadata.json`: 전체 시뮬레이션 실행 정보

## 🎯 Goal3 최종 결과
- **예측 완료 시간**: 3600초
- **신뢰도**: 0.5
- **실행 시간**: 33초
- **상태**: simulation_completed_no_analysis

## 🔄 완전한 파이프라인 달성
사용자 요청 → SWRL 추론 → AASX 데이터 → JSON 변환 → NSGA-II 실행 → 결과 도출
