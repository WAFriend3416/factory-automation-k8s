# Factory Automation K8s - Pipeline Output Structure

이 폴더는 AASX 서버에서 NSGA-II 시뮬레이션까지의 전체 데이터 파이프라인 결과를 단계별로 정리한 것입니다.

## 📁 폴더 구조

```
output/
├── step1_aasx_raw_data/       # AASX 서버 원본 데이터
├── step2_data_orchestrator/   # DataOrchestrator 처리 결과  
├── step3_nsga2_simulation/    # NSGA-II 시뮬레이션 결과
├── metadata/                  # 전체 실행 메타데이터
└── README.md                  # 이 파일
```

## 🔄 데이터 플로우

1. **AASX 서버** → Property.value 필드에서 JSON 문자열 추출
2. **DataOrchestrator** → 6개 시뮬레이션 JSON 파일 생성
3. **NSGA-II 시뮬레이터** → 스케줄링 최적화 및 결과 생성

각 단계별 상세 정보는 해당 폴더의 README.md를 참조하세요.
