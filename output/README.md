# Factory Automation K8s - Complete Pipeline Output Structure

이 폴더는 사용자 요청부터 SWRL 추론, AASX 서버 연동, NSGA-II 시뮬레이션까지의 전체 데이터 파이프라인 결과를 단계별로 정리한 것입니다.

## 📁 완전한 폴더 구조

```
output/
├── step0_user_request/        # 사용자 요청 및 요구사항 분석
├── step1_swrl_inference/      # SWRL 추론 엔진 규칙 적용 및 확장
├── step2_aasx_raw_data/       # AASX 서버 원본 데이터 수집
├── step3_data_orchestrator/   # DataOrchestrator JSON 변환
├── step4_nsga2_simulation/    # NSGA-II 시뮬레이션 실행
├── metadata/                  # 전체 실행 메타데이터
└── README.md                  # 이 파일
```

## 🔄 완전한 데이터 플로우

0. **사용자 요청** → Goal3 요구사항 정의 및 분석
1. **SWRL 추론** → 필요한 데이터 모델 및 JSON 파일 결정
2. **AASX 서버** → 추론 결과 기반 데이터 수집
3. **DataOrchestrator** → SWRL 호환 JSON 파일 생성
4. **NSGA-II 시뮬레이터** → 최적화 실행 및 결과 도출

각 단계별 상세 정보는 해당 폴더의 README.md를 참조하세요.

## 🎯 Goal3 완전한 구현

사용자의 "30개 작업 첫 완료 시간 예측" 요청이 SWRL 추론을 통해 시스템적으로 확장되어 완전한 시뮬레이션 파이프라인으로 구현되었습니다.
