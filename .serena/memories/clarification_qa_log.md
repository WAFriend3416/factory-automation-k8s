# 명확화 질문 및 답변 로그

## 첫 번째 질문 세트 (기본 환경)

### Q1: Goal 1, 4가 정상적으로 동작하고 있나요?
**A1**: AAS 서버 데이터 단순 조회로, 각 Goal에 해당하는 서브모델이 존재한다면 정상작동함. 실행 가이드대로 서버를 실행시켜야 서버를 실행시킬 수 있음. AAS 서버는 현재 실행중.

### Q2: API 엔드포인트는 동일하게 유지하나요?
**A2**: 유도리 있게 변경해서 사용해도 됨.

### Q3: 새로운 Scenario_* Submodel들이 구현되어 있나요?
**A3**: 아직 구현되어 있지 않음. 추가하면 관련 전달 가능.

### Q4: NSGA와 AAS의 기기 명명 규칙은?
**A4**: NSGA 쪽 명명 규칙을 따르도록 하겠음. AAS 서버쪽 기기 명칭을 바꾸고 전달함.

### Q5: NSGA-II 시뮬레이터 접근 권한은?
**A5**: https://github.com/Otober/AASX/tree/NSGA 해당 브랜치로 접근하면 될듯.

### Q6: my_case 폴더와 시뮬레이터 실행 방식은?
**A6**: 이건 제 담당이 아니라 시뮬레이터 깃헙의 코드를 살펴보고 파악해야할듯.

### Q7, Q8: QueryGoal과 설정 파일들은?
**A7, A8**: aasp-prd 폴더내에 new-requirement 폴더에 pdf가 존재함. 해당 QueryGoal에 대한 내용도 여기에 존재함.

### Q9: 마이그레이션 전략은?
**A9**: 일단 Goal3을 대상으로 새 파일에서 진행해보도록.

### Q10: 기존 기능 유지 필요성은?
**A10**: 음.. 오히려 Goal3의 기능구현이 잘된다면 나머지 Goal에 대해서도 Goal3 방식으로 변경할 여지 있음.

## 두 번째 질문 세트 (구체적 구현)

### Q11, Q12: QueryGoal JSON 형식과 설정 파일 구조는?
**A11, A12**: 폴더 내부에 example.md 를 참고.

### Q13: NSGA 시뮬레이터 정확한 실행 명령어는?
**A13**: 담당자에게 물어보고 알려줌.

### Q14: Docker 의존성 및 requirements.txt는?
**A14**: 시뮬레이터 깃헙에 없다면 담당자에게 물어봄. 아니면 이미지 파일을 제공해줘도 되는가?

### Q15: 결과 처리 및 API 응답 형식은?
**A15**: 너가 만들어야 될듯, QueryGoal에 보면 Output spec을 참고

### Q16: 개발 환경 설정 (K8s, PVC 등)은?
**A16**: 예처럼 사용함. 그 외에는 쿠버를 잘 몰라서 답하기 어려움.

### Q17: AAS 서버 업데이트 타이밍은?
**A17**: 오늘 피드백 끝나는대로 작업해서 세팅해놓겠음. 일단 대기

### Q18: 개발 시작 전략은?
**A18**: AAS 데이터 준비가 필요할거 같으니 일단은 대기.

## 핵심 정보 정리

### QueryGoal 구조 (example.md에서 확인됨)
- goalId, goalType, parameters, outputSpec, termination
- selectedModel: container 정보, MetaData 참조
- selectionProvenance: 추적 정보

### MetaData.json 구조  
- modelId, requiredInputs, preconditions, outputs
- requiredInputs: ["JobRoute","MachineState","Calendar","SetupMatrix","WIP","Backlog"]

### bindings.yaml 구조
- schema, sources (각 requiredInput의 데이터 소스 정의)
- AAS URI, 파일 경로, glob 패턴, combine 정책

### 대기 중인 사항
1. NSGA 시뮬레이터 실행 명령어 확인
2. Docker 의존성 정보 또는 이미지 제공
3. AAS 서버 데이터 업데이트 (M1-M4 명명, Scenario_* Submodel 추가)