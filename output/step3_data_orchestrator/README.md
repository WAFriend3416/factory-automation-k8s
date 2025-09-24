# Step 3: DataOrchestrator Processing

## 📝 설명
AASX 서버에서 추출된 데이터를 SWRL 추론 결과에 따라 NSGA-II 시뮬레이션용 JSON 파일로 변환

## 📂 input/
- `aasx_extracted_data.json`: Step 2에서 추출된 Property.value 데이터

## 📂 output/
- `jobs.json`: 작업 정보 (30개 작업) - SWRL R002 규칙 준수
- `operations.json`: 오퍼레이션 정보 (95개 오퍼레이션)
- `machines.json`: 머신 정보 (4개 머신) - capability + status 통합
- `operation_durations.json`: 작업 소요 시간
- `machine_transfer_time.json`: 머신 간 이동 시간  
- `job_release.json`: 작업 릴리즈 시간
- `orchestrator_execution_log.json`: SWRL 준수 검증 로그

## 🔧 SWRL 규칙 준수
- **R001 준수**: 모든 추론된 서브모델에서 데이터 수집 완료
- **R002 준수**: 6개 필수 JSON 파일 모두 생성 완료
- **검증 완료**: NSGA-II 호환성 및 스키마 유효성 확인
