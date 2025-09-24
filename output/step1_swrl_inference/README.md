# Step 1: SWRL Inference

## 📝 설명
SWRL(Semantic Web Rule Language) 추론 엔진을 통해 사용자 요청을 구체적인 데이터 요구사항으로 확장

## 📂 input/
- `user_request_analysis.json`: Step 0의 요청 분석 결과
- `goal3_swrl_rules.json`: Goal3용 SWRL 규칙 정의

## 📂 output/
- `swrl_inference_results.json`: 추론 결과 및 데이터 수집 지시사항

## 🧠 SWRL 규칙 적용
- **Rule R001**: Goal3 → 필요한 서브모델 결정
- **Rule R002**: 서브모델 → JSON 파일 요구사항 확장

## 📊 추론 결과
- **필요 서브모델**: simulation_data + capability(M1-M4) + status(M1-M4)  
- **필요 JSON 파일**: 6개 파일 (jobs, operations, machines, durations, transfer_time, release)
- **AASX 쿼리 지시**: 직접 서브모델 접근 방식 결정
