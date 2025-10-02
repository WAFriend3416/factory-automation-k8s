#!/usr/bin/env python3
"""
QueryGoal 파이프라인 전체 과정 시연
사용자 요청 → 최종 결과물까지의 모든 단계를 보여주는 데모
"""
import json
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from querygoal.pipeline.orchestrator import PipelineOrchestrator


def print_separator(title, char="="):
    """구분선 출력"""
    print(f"\n{char * 80}")
    print(f"🎯 {title}")
    print(f"{char * 80}")


def print_json_pretty(data, title=""):
    """JSON 데이터를 보기 좋게 출력"""
    if title:
        print(f"\n📄 {title}:")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def demonstrate_pipeline(user_input):
    """파이프라인 전체 과정 시연"""

    print_separator(f"사용자 요청: '{user_input}'", "🔹")

    orchestrator = PipelineOrchestrator()

    # Step 1: 자연어 → QueryGoal 변환
    print_separator("STEP 1: 자연어 → QueryGoal 변환")
    print(f"📥 입력: {user_input}")

    querygoal = orchestrator.process_natural_language(user_input)

    print(f"✅ QueryGoal 생성 완료!")
    print(f"   - Goal ID: {querygoal['QueryGoal']['goalId']}")
    print(f"   - Goal Type: {querygoal['QueryGoal']['goalType']}")
    print(f"   - Category: {querygoal['QueryGoal']['metadata']['category']}")
    print(f"   - Requires Model: {querygoal['QueryGoal']['metadata']['requiresModel']}")
    print(f"   - Pipeline Stages: {querygoal['QueryGoal']['metadata']['pipelineStages']}")

    # 상세 QueryGoal 구조 출력
    print_json_pretty(querygoal, "생성된 QueryGoal 전체 구조")

    # Step 2: QueryGoal 실행
    print_separator("STEP 2: QueryGoal 실행")
    print("🔄 파이프라인 실행 중...")

    execution_result = orchestrator.execute_querygoal(querygoal)

    # Step 3: 실행 결과 분석
    print_separator("STEP 3: 실행 결과 분석")

    pipeline_meta = execution_result["pipeline_meta"]
    print(f"📊 파이프라인 성공률: {pipeline_meta['success_rate']:.1%}")
    print(f"🎯 전체 성공: {pipeline_meta['success']}")
    print(f"✅ 완료된 단계: {', '.join(pipeline_meta['completed_stages'])}")

    if pipeline_meta['failed_stages']:
        print(f"❌ 실패한 단계: {', '.join(pipeline_meta['failed_stages'])}")

    if pipeline_meta.get('fail_reason'):
        print(f"⚠️ 실패 원인: {pipeline_meta['fail_reason']}")

    # Step 4: 최종 결과물 출력
    print_separator("STEP 4: 최종 결과물")

    if execution_result.get("result"):
        print("🎉 실행 결과:")
        print_json_pretty(execution_result["result"], "비즈니스 결과")

    if execution_result.get("simulation_output"):
        print("\n🔬 시뮬레이션 결과:")
        print_json_pretty(execution_result["simulation_output"], "시뮬레이션 출력")

    # Step 5: 메타데이터 및 추적 정보
    print_separator("STEP 5: 메타데이터 및 추적 정보")
    print_json_pretty(pipeline_meta, "파이프라인 메타데이터")

    # 모델 관련 정보 (있는 경우)
    selected_model = querygoal['QueryGoal'].get('selectedModel')
    if selected_model:
        print_separator("모델 선택 정보")
        print(f"📝 선택된 모델: {selected_model['modelId']}")
        if querygoal['QueryGoal'].get('selectionProvenance'):
            provenance = querygoal['QueryGoal']['selectionProvenance']
            print(f"🔍 선택 방법: {provenance.get('selectionMethod', 'unknown')}")
            print(f"⏰ 선택 시각: {provenance.get('selectedAt', 'unknown')}")
            print(f"💭 선택 근거: {provenance.get('reason', 'no reason provided')}")

    return querygoal, execution_result


def main():
    """메인 실행 - 다양한 시나리오 데모"""

    print("🚀 QueryGoal 파이프라인 전체 과정 시연")
    print("=" * 80)
    print("현재 구현된 파이프라인을 통해 사용자 요청이 어떻게 처리되는지 확인")
    print("=" * 80)

    # 시나리오 1: Goal 1 - 진단 (모델 불필요)
    demonstrate_pipeline("Check cooling failure for machine M003")

    # 시나리오 2: Goal 3 - 예측 (모델 필요)
    demonstrate_pipeline("Predict production time for product type ABC123 with quantity 50")

    # 시나리오 3: Goal 4 - 추적 (모델 불필요)
    demonstrate_pipeline("Track product location for product id PROD-2024-001")

    # 시나리오 4: 알 수 없는 요청
    demonstrate_pipeline("Do something completely unknown")

    print_separator("✅ 전체 시연 완료", "🎉")
    print("위 과정을 통해 다음을 확인할 수 있습니다:")
    print("1. 자연어 → 구조화된 QueryGoal 변환")
    print("2. Goal 타입별 적절한 파이프라인 단계 실행")
    print("3. 모델 필요 여부에 따른 자동 선택")
    print("4. 실행 결과 및 메타데이터 생성")
    print("5. 에러 처리 및 fallback 동작")


if __name__ == "__main__":
    main()