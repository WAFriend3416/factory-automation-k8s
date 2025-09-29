#!/usr/bin/env python3
"""
6단계 파이프라인 입력/출력 요약
각 Goal별로 단계별 입력과 출력을 구체적으로 정리
"""
import json
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from querygoal.pipeline.orchestrator import PipelineOrchestrator


def summarize_goal_pipeline(goal_name, user_input):
    """특정 Goal의 6단계 파이프라인 입출력 요약"""

    print(f"\n{'='*80}")
    print(f"🎯 {goal_name}")
    print(f"📥 입력: {user_input}")
    print(f"{'='*80}")

    orchestrator = PipelineOrchestrator()
    querygoal = orchestrator.process_natural_language(user_input)

    # pipelineLog에서 단계별 정보 추출
    stages = querygoal.get("pipelineLog", {}).get("stages", [])
    qg = querygoal["QueryGoal"]

    stage_details = [
        ("STAGE 1: 패턴 매칭", "자연어", "Goal타입 + 파라미터"),
        ("STAGE 2: 템플릿 로딩", "Goal타입", "기본 QueryGoal 구조"),
        ("STAGE 3: 파라미터 채움", "추출된 파라미터", "완전한 parameters/outputSpec"),
        ("STAGE 4: 액션 플랜 해결", "Goal타입", "실행 계획 리스트"),
        ("STAGE 5: 모델 선택", "Goal타입 + requiresModel", "선택된 모델 정보"),
        ("STAGE 6: 검증", "완성된 QueryGoal", "검증 결과")
    ]

    for i, (stage_name, input_desc, output_desc) in enumerate(stage_details, 1):
        stage_info = stages[i-1] if i-1 < len(stages) else {}
        status = stage_info.get("status", "unknown")
        result = stage_info.get("result", {})

        print(f"\n📍 {stage_name}")
        print(f"   📥 입력: {input_desc}")
        print(f"   📤 출력: {output_desc}")
        print(f"   ✅ 상태: {status}")

        # 구체적인 결과 값들
        if i == 1:  # 패턴 매칭
            print(f"   🔍 결과: goalType={result.get('goalType', 'N/A')}")
            extracted = result.get('extractedParameters', {})
            if extracted:
                print(f"         parameters={list(extracted.keys())}")

        elif i == 2:  # 템플릿 로딩
            print(f"   🆔 결과: goalId={result.get('goalId', 'N/A')}")

        elif i == 3:  # 파라미터 채움
            param_count = result.get('paramCount', 0)
            print(f"   📊 결과: {param_count}개 파라미터 생성")
            print(f"         parameters={[p['key'] for p in qg.get('parameters', [])]}")

        elif i == 4:  # 액션 플랜
            action_count = result.get('actionCount', 0)
            print(f"   🔧 결과: {action_count}개 액션 플랜")
            actions = [a.get('actionType', 'N/A') for a in qg['metadata'].get('actionPlan', [])]
            if actions:
                print(f"         actions={actions}")

        elif i == 5:  # 모델 선택
            model_status = result.get('modelStatus', 'unknown')
            print(f"   🤖 결과: {model_status}")
            if qg.get('selectedModel'):
                print(f"         model={qg['selectedModel']['modelId']}")

        elif i == 6:  # 검증
            errors = result.get('errorCount', 0)
            warnings = result.get('warningCount', 0)
            print(f"   📋 결과: {errors}개 에러, {warnings}개 경고")

    # 최종 QueryGoal 요약
    print(f"\n{'🎉'*60}")
    print(f"📋 최종 QueryGoal 요약")
    print(f"{'🎉'*60}")

    print(f"🆔 Goal ID: {qg['goalId']}")
    print(f"🎯 Goal Type: {qg['goalType']}")
    print(f"📂 Category: {qg['metadata']['category']}")
    print(f"🤖 Model Required: {qg['metadata']['requiresModel']}")

    if qg.get('selectedModel'):
        print(f"🎯 Selected Model: {qg['selectedModel']['modelId']}")
        provenance = qg.get('selectionProvenance', {})
        method = provenance.get('selectionMethod', 'unknown')
        print(f"🔍 Selection Method: {method}")

    print(f"📊 Parameters ({len(qg['parameters'])}):")
    for p in qg['parameters']:
        print(f"    • {p['key']}: {p['value']} ({p.get('type', 'unknown')})")

    print(f"📋 Output Specs ({len(qg['outputSpec'])}):")
    for o in qg['outputSpec'][:3]:  # 처음 3개만
        print(f"    • {o['name']}: {o.get('type', o.get('datatype', 'unknown'))}")
    if len(qg['outputSpec']) > 3:
        print(f"    • ... and {len(qg['outputSpec'])-3} more")

    print(f"🔧 Action Plans ({len(qg['metadata']['actionPlan'])}):")
    for a in qg['metadata']['actionPlan'][:3]:  # 처음 3개만
        print(f"    • {a.get('actionType', 'N/A')}: {a.get('description', 'N/A')}")
    if len(qg['metadata']['actionPlan']) > 3:
        print(f"    • ... and {len(qg['metadata']['actionPlan'])-3} more")

    print(f"⚙️ Pipeline Stages: {qg['metadata']['pipelineStages']}")

    return querygoal


def main():
    """각 Goal별 6단계 파이프라인 입출력 요약 실행"""

    print("🔬 QueryGoal 파이프라인 6단계 입력/출력 완전 분석")
    print("각 Goal별로 단계별 구체적인 입력과 출력 값을 확인합니다")
    print("="*80)

    test_cases = [
        ("Goal 1: 진단 시스템 (모델 불필요)", "Check cooling failure for machine M999"),
        ("Goal 3: 생산 예측 (모델 필요)", "Predict production time for product SAMPLE123 with quantity 200"),
        ("Goal 4: 제품 추적 (모델 불필요)", "Track product location for product id TEST-2024-999")
    ]

    results = []
    for goal_name, user_input in test_cases:
        result = summarize_goal_pipeline(goal_name, user_input)
        results.append((goal_name, result))

    # 전체 비교 요약
    print(f"\n{'🔍'*80}")
    print("📊 Goal별 비교 요약")
    print(f"{'🔍'*80}")

    for goal_name, result in results:
        qg = result["QueryGoal"]
        print(f"\n• {goal_name}")
        print(f"  - Goal Type: {qg['goalType']}")
        print(f"  - Category: {qg['metadata']['category']}")
        print(f"  - Model Required: {qg['metadata']['requiresModel']}")
        print(f"  - Parameters: {len(qg['parameters'])}")
        print(f"  - Actions: {len(qg['metadata']['actionPlan'])}")
        print(f"  - Pipeline: {' → '.join(qg['metadata']['pipelineStages'])}")
        if qg.get('selectedModel'):
            print(f"  - Selected Model: {qg['selectedModel']['modelId']}")


if __name__ == "__main__":
    main()