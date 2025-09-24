# Step 2: AASX Raw Data

## 📝 설명
SWRL 추론 결과를 바탕으로 AASX 서버에서 원본 데이터를 수집하고 Property.value 필드를 추출하는 단계

## 📂 input/
- `swrl_data_requirements.json`: Step 1 SWRL 추론에서 결정된 데이터 요구사항
- `aasx_raw_responses.json`: AASX 서버 서브모델 원본 응답 데이터

## 📂 output/  
- `extracted_property_values.json`: Property.value 필드에서 추출된 JSON 문자열들

## 🔧 처리 방식
- **SWRL 기반 쿼리**: 추론으로 결정된 서브모델만 선택적 조회
- 서브모델 직접 접근: `GET /submodels/{encoded_id}` (Shell 우회)
- Property 타입 필터링 및 JSON 문자열 추출

## 📊 수집 결과
- FactorySimulation: 5개 시뮬레이션 데이터 요소
- Machine Capability: 각 머신별 능력 정보  
- Machine Status: 각 머신별 상태 정보
