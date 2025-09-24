# Step 1: AASX Raw Data

## 📝 설명
AASX 서버에서 원본 데이터를 수집하고 Property.value 필드를 추출하는 단계

## 📂 input/
- `aasx_raw_responses.json`: AASX 서버 서브모델 원본 응답 데이터

## 📂 output/  
- `extracted_property_values.json`: Property.value 필드에서 추출된 JSON 문자열들

## 🔧 처리 방식
- 서브모델 직접 접근: `GET /submodels/{encoded_id}`
- Property 타입 필터링
- JSON 문자열 추출 (파싱 전)
