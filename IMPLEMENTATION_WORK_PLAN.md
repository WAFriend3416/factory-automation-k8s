# 지능형 공장 자동화 시스템 2.0 구현 작업 계획

**작성일**: 2025-09-16  
**기반 문서**: aasp-prd/main-prd.md, aas-server-data.md, process-criteria.md  
**목표**: Goal 3 시나리오 합성 아키텍처 구현 및 NSGA-II 시뮬레이터 통합

---

## 📋 프로젝트 개요

### 현재 상태 분석
- **프로젝트**: factory-automation-k8s (goal3-implementation-detail 브랜치)
- **기존 아키텍처**: 정적 실행 계획 방식
- **목표 아키텍처**: 동적 시나리오 합성 + NSGA-II 최적화

### 주요 변경사항
1. **API 계층**: QueryGoal 스키마 도입, 라우팅 로직 변경
2. **실행 엔진**: ExecutionPlanner → ScenarioComposer 전환
3. **데이터 전략**: 하이브리드 AAS 데이터 모델 (정적 파일 + 동적 조합)
4. **시뮬레이터**: NSGA-II 통합 및 Docker 컨테이너화
5. **재현성**: manifest.json 기반 추적 시스템

---

## 🎯 구현 로드맵

### Phase 0: 사전 평가 및 준비 (1-2일)

#### 🔍 **Task 0.1: 현재 코드베이스 상세 분석**
- **담당**: 개발팀
- **산출물**: 
  - `current_codebase_analysis.md` 문서
  - 기존 기능 보존을 위한 백업 전략
- **성공 기준**:
  - [ ] 모든 기존 Goal (1,2,4) 테스트 케이스 실행 성공
  - [ ] API 엔드포인트 현재 동작 확인
  - [ ] AAS 서버 연결 상태 검증

#### 🐋 **Task 0.2: NSGA-II 시뮬레이터 평가 및 로컬 테스트**
- **기반 자료**: https://github.com/Otober/AASX
- **산출물**:
  - NSGA-II 시뮬레이터 로컬 실행 가이드
  - 입력 파일 형식 검증 (`my_case/` 폴더 분석)
  - 출력 결과 형식 문서화
- **성공 기준**:
  - [ ] `my_case/` 예시 데이터로 시뮬레이터 로컬 실행 성공
  - [ ] 입력 6개 JSON 파일 스키마 정의 완료
  - [ ] 출력 결과 파싱 로직 설계 완료

#### 📦 **Task 0.3: 개발 환경 및 종속성 준비**
- **산출물**: 업데이트된 `requirements.txt`
- **성공 기준**:
  - [ ] Python 의존성 패키지 설치 완료
  - [ ] Docker 및 K8s 개발 환경 검증
  - [ ] AAS 서버 개발/테스트 데이터 준비

---

### Phase 1: 기반 구축 (3-4일)

#### 🚀 **Task 1.1: API 스키마 업데이트**
- **파일**: `api/schemas.py`
- **작업 내용**:
  - `QueryGoal` Pydantic 모델 구현 (PRD 명세 준수)
  - 기존 `DslRequest` 모델과의 하위 호환성 고려
  - 복잡한 중첩 구조에 대한 검증 로직
- **산출물**: 새로운 스키마 클래스 및 검증 테스트
- **성공 기준** (process-criteria.md 참조):
  - [ ] QueryGoal JSON 구문 분석 성공
  - [ ] Pydantic 스키마 검증 통과
  - [ ] 모든 필수 필드 존재 및 데이터 타입 일치

#### 🔀 **Task 1.2: API 라우팅 로직 수정**
- **파일**: `api/main.py`
- **작업 내용**:
  - `/execute-goal` 엔드포인트에 `goalType` 분기 로직 추가
  - `predict_job_completion_time`일 경우 `ScenarioComposer` 호출
  - 기존 Goal 1,2,4는 `ExecutionPlanner` 유지
- **성공 기준**:
  - [ ] Goal 3 요청시 새로운 라우팅 경로 활성화
  - [ ] 기존 Goal 1,2,4 기능 정상 동작 유지
  - [ ] 에러 처리 및 상태 코드 적절히 반환

#### 🐳 **Task 1.3: NSGA-II 시뮬레이터 Docker 이미지 생성**
- **산출물**: 
  - `Dockerfile.nsga_simulator`
  - 시뮬레이터 컨테이너 이미지
- **작업 내용**:
  - NSGA-II GitHub 저장소 기반 Dockerfile 작성
  - 6개 JSON 입력 파일 처리 로직 포함
  - PVC 마운트 지점 설정
- **성공 기준**:
  - [ ] Docker 이미지 빌드 성공
  - [ ] 컨테이너 내부에서 시뮬레이터 실행 가능
  - [ ] 입출력 파일 경로 정상 인식

#### 🧪 **Task 1.4: 기본 API 테스트 구현**
- **파일**: `test_goal3_schema.py` (신규)
- **작업 내용**:
  - QueryGoal 스키마 검증 테스트
  - API 엔드포인트 기본 응답 테스트
- **성공 기준**:
  - [ ] 유효한 QueryGoal 요청에 대한 200 응답
  - [ ] 잘못된 스키마에 대한 422 에러 응답
  - [ ] 기존 테스트 케이스 영향 없음

---

### Phase 2: 핵심 아키텍처 구현 (5-7일)

#### 🏗️ **Task 2.1: ScenarioComposer 클래스 구현**
- **파일**: `execution_engine/composer.py` (신규 또는 planner.py 리팩토링)
- **핵심 기능**:
  - `compose(goal: QueryGoal)` 메서드
  - AAS 하이브리드 데이터 전략 구현
  - 시나리오 파일 생성 및 PVC 저장
- **데이터 처리 로직** (aas-server-data.md 기준):
  
  | 파일 | 데이터 소스 | 처리 방법 |
  |------|------------|----------|
  | `jobs.json` | AAS `Scenario_Jobs` Submodel | Content Property에서 JSON 문자열 추출 |
  | `operations.json` | AAS `Scenario_Operations` Submodel | 동일한 방식 |
  | `operation_durations.json` | AAS `Scenario_OperationDurations` | 동일한 방식 |
  | `machine_transfer_time.json` | AAS `Scenario_MachineTransferTime` | 동일한 방식 |
  | `job_release.json` | AAS `Scenario_JobRelease` | 동일한 방식 |
  | `machines.json` | 각 설비 AAS `TechnicalData` + `OperationalData` | 동적 조합 생성 |

- **성공 기준** (process-criteria.md 참조):
  - [ ] `MetaData.json` 로드 및 `requiredInputs` 확보
  - [ ] `bindings.yaml` 규칙에 따른 AAS 데이터 조회 성공
  - [ ] 모든 시나리오 파일 PVC 저장 완료
  - [ ] AAS 데이터 조회 실패시 적절한 에러 처리

#### 🔧 **Task 2.2: ExecutionAgent 리팩토링**
- **파일**: `execution_engine/agent.py`
- **변경 사항**:
  - `run()` 메서드 인자 변경: `plan` → `scenario_path`, `container_image`
  - `EnhancedDockerRunHandler` 데이터 처리 로직 제거
  - K8s Job 볼륨 마운트 설정에 집중
- **성공 기준**:
  - [ ] 시나리오 경로 기반 K8s Job 생성
  - [ ] PVC 마운트 설정 정상 동작
  - [ ] Pod 상태 모니터링 및 결과 파일 확인

#### 🗃️ **Task 2.3: AAS 서버 데이터 모델 업데이트**
- **파일**: `aas_mock_server/data/` 하위 파일들
- **작업 내용**:
  - 새로운 Submodel 구조 생성:
    - `Scenario_Jobs_JobETAModel_v1.1`
    - `Scenario_Operations_JobETAModel_v1.1`
    - 기타 시나리오 관련 Submodel들
  - 각 Submodel에 `Content` Property 추가
  - 기존 설비 AAS에 `NextAvailableTime` 필드 추가
- **성공 기준**:
  - [ ] 모든 새로운 Submodel AAS 서버에서 조회 가능
  - [ ] `Content` Property에서 올바른 JSON 문자열 반환
  - [ ] 동적 설비 데이터 조회 성공

#### 🔗 **Task 2.4: 하이브리드 데이터 전략 검증**
- **파일**: `test_scenario_composition.py` (신규)
- **테스트 내용**:
  - 정적 시나리오 데이터 조회 및 파싱
  - 동적 설비 데이터 조합
  - 완전한 시나리오 파일셋 생성
- **성공 기준**:
  - [ ] 6개 JSON 파일 모두 올바른 형식으로 생성
  - [ ] `machines.json`에 실시간 설비 상태 반영
  - [ ] 시나리오 데이터 무결성 검증 통과

---

### Phase 3: 검증 및 고도화 (3-4일)

#### ✅ **Task 3.1: 시나리오 검증 시스템 구현**
- **파일**: `execution_engine/validator.py` (신규) 또는 ScenarioComposer 내부
- **기능**:
  - `_validate_scenario()`: JSON 스키마 검증
  - SHACL 제약 조건 검증 (기본 수준)
  - 데이터 무결성 검사
- **성공 기준** (process-criteria.md 참조):
  - [ ] 모든 시나리오 파일의 JSON 스키마 검증 통과
  - [ ] `MetaData.json` 요구사항과 실제 데이터 일치
  - [ ] 검증 실패시 구체적인 에러 메시지 제공

#### 📜 **Task 3.2: 재현성 보장 시스템**
- **기능**: `_create_manifest()` 구현
- **작업 내용**:
  - 입력 데이터 해시값 계산
  - 시나리오 생성 과정 기록
  - `manifest.json` 파일 생성
- **성공 기준**:
  - [ ] 동일한 입력에 대해 동일한 해시값 생성
  - [ ] 시나리오 재현을 위한 모든 정보 포함
  - [ ] 감사 추적 가능한 로그 기록

#### 🧪 **Task 3.3: 종단간(E2E) 테스트 구현**
- **파일**: `test_goal3_e2e.py`
- **테스트 시나리오**:
  1. QueryGoal 요청 접수
  2. 시나리오 합성
  3. 검증 및 manifest 생성
  4. NSGA-II 시뮬레이터 실행
  5. 결과 처리 및 반환
- **성공 기준**:
  - [ ] 전체 파이프라인 정상 실행
  - [ ] 각 단계별 성공 조건 검증
  - [ ] 실패 시나리오에 대한 적절한 에러 처리

#### 📖 **Task 3.4: 온톨로지 및 문서 업데이트**
- **파일**: 
  - `ontology/factory_ontology_v2_final_corrected.ttl`
  - `README.md`
  - `COMPLETE_SETUP_GUIDE.md`
- **작업 내용**:
  - Goal 3 `:hasActionSequence` 추상화 수정
  - 새로운 아키텍처 문서화
  - 배포 및 운영 가이드 작성
- **성공 기준**:
  - [ ] 온톨로지 파일 구문 검증 통과
  - [ ] 개발자를 위한 명확한 구현 가이드 제공
  - [ ] 운영팀을 위한 배포 문서 완성

---

## 📊 품질 관리 및 위험 대응

### 품질 게이트
각 Phase 완료시 다음 검증 수행:
- [ ] 모든 기존 테스트 케이스 통과 (regression testing)
- [ ] 새로운 기능에 대한 단위 테스트 작성
- [ ] 코드 리뷰 및 문서 검토
- [ ] 성능 및 메모리 사용량 검증

### 위험 관리
1. **기존 기능 보존**: 
   - 기능 플래그를 통한 점진적 마이그레이션
   - 기존 Goal 1,2,4 테스트 지속 실행
   
2. **NSGA-II 통합 위험**:
   - 시뮬레이터 Docker화 전 충분한 로컬 테스트
   - 입출력 형식 불일치에 대한 대안 준비
   
3. **AAS 데이터 모델 변경**:
   - 백워드 호환성 유지
   - 데이터 마이그레이션 스크립트 준비

### 롤백 계획
- 각 Phase별 백업 브랜치 생성
- 주요 변경사항에 대한 롤백 스크립트 준비
- 긴급상황시 기존 시스템으로 즉시 복구 가능

---

## 📅 타임라인 및 마일스톤

| Phase | 기간 | 주요 마일스톤 | 검증 기준 |
|-------|------|--------------|----------|
| **Phase 0** | 2일 | 환경 준비 완료 | NSGA-II 로컬 실행 성공 |
| **Phase 1** | 4일 | API 및 Docker 기반 구축 | QueryGoal 스키마 검증 통과 |
| **Phase 2** | 7일 | 핵심 아키텍처 구현 | 완전한 시나리오 생성 |
| **Phase 3** | 4일 | 검증 및 문서화 | E2E 테스트 통과 |
| **전체** | **17일** | **시스템 운영 준비 완료** | **모든 품질 게이트 통과** |

---

## 🎯 성공 측정 지표

### 기능적 지표
- [ ] QueryGoal → 시나리오 합성 → NSGA-II 실행 → 결과 반환 (전체 파이프라인)
- [ ] 6개 시나리오 파일 정확한 생성
- [ ] manifest.json 기반 재현성 보장
- [ ] 기존 Goal 1,2,4 기능 100% 유지

### 비기능적 지표
- [ ] 시나리오 합성 시간 < 30초
- [ ] AAS 서버 응답 시간 < 5초
- [ ] K8s Job 실행 성공률 > 95%
- [ ] 메모리 사용량 증가 < 20%

### 품질 지표
- [ ] 코드 커버리지 > 80%
- [ ] 문서 완성도 100%
- [ ] 사용자 피드백 긍정률 > 90%

---

## 📝 다음 단계

1. **사용자 피드백 대기**: 현재 작업 계획에 대한 검토 및 승인
2. **리소스 확보**: 개발 환경, NSGA-II 저장소 접근, K8s 클러스터
3. **팀 배정**: 각 Task별 담당자 및 일정 확정
4. **킥오프 미팅**: 프로젝트 시작 및 첫 번째 Sprint 계획

---

*이 문서는 aasp-prd 폴더의 요구사항을 기반으로 작성되었으며, 구현 과정에서 추가 세부사항이 발견될 수 있습니다. 정기적인 검토 및 업데이트가 필요합니다.*