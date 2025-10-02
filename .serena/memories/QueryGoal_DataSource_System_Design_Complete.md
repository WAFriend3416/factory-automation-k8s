# QueryGoal 데이터 소스 조회 시스템 설계 완료

## 완성된 설계 문서 위치
- **파일**: temp/output_2/QueryGoal_DataSource_System_Design.md
- **크기**: 약 15,000자, 11개 섹션으로 구성

## 설계 핵심 내용

### 1. 전체 파이프라인 아키텍처
```
자연어 질의 → QueryGoal 생성 → Action Plan ID → Action Plan Resolver → 실행 계획 → ExecutionAgent → 결과
```

### 2. 신규 핵심 컴포넌트
- **QueryGoalOrchestrator**: 전체 파이프라인의 중앙 조정자
- **ActionPlanResolver**: Action Plan ID를 실행 가능한 계획으로 변환하는 핵심 컴포넌트

### 3. Goal별 실행 흐름
- **Goal 1**: 냉각 작업 실패 조회 (ActionFetchJobLog → ActionFilterData)
- **Goal 3**: 생산 시간 예측 (ActionPredictProductionTime)
- **Goal 4**: 제품 위치 추적 (ActionTrackProduct)

### 4. 기존 시스템과의 통합
- ExecutionAgent 아키텍처 재활용
- 기존 핸들러들(AASQueryHandler, AIModelHandler 등) 확장
- SPARQL 규칙 기반 Action Plan 매핑

### 5. 구현 계획
- **Phase 1**: 핵심 인프라 구축 (2주)
- **Phase 2**: 핸들러 확장 (2주) 
- **Phase 3**: 통합 및 최적화 (1주)

### 6. 확장성 및 견고성
- 새로운 Goal 유형 추가 용이
- 에러 처리 및 복구 메커니즘
- 모니터링 및 로깅 체계
- 보안 고려사항

## 다음 단계
1. ActionPlanResolver 클래스 구현
2. QueryGoalOrchestrator 클래스 구현  
3. 핸들러 확장 및 통합 테스트
4. 단계별 프로토타입 개발

## 설계 완료일
2025-09-29

## 기술적 가치
- 기존 QueryGoal 템플릿 시스템을 실제 실행 가능한 시스템으로 확장
- 모듈화된 아키텍처로 확장성과 유지보수성 확보
- AAS 표준과 AI 모델 통합을 통한 스마트 팩토리 자동화 완성