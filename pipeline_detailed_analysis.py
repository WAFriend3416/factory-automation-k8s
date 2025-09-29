#!/usr/bin/env python3
"""
QueryGoal 파이프라인 6단계 상세 분석
각 단계별 입력/출력 값을 구체적으로 추출하여 보여주는 스크립트
"""
import json
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from querygoal.pipeline.orchestrator import PipelineOrchestrator


def print_stage_detail(stage_name, input_data, output_data, stage_number):
    """각 단계의 상세 입력/출력 정보 출력"""
    print(f"\n{'='*60}")
    print(f"📍 STAGE {stage_number}: {stage_name}")
    print(f"{'='*60}")

    print(f"📥 INPUT:")
    if isinstance(input_data, dict) and len(input_data) > 0:
        for key, value in input_data.items():
            if isinstance(value, (str, int, float, bool)):
                print(f"   • {key}: {value}")
            elif isinstance(value, list):
                print(f"   • {key}: [{len(value)} items]")
                for i, item in enumerate(value[:2]):  # 처음 2개만
                    if isinstance(item, str):
                        print(f"     - [{i}] {item}")
                    elif isinstance(item, dict) and 'key' in item:
                        print(f"     - [{i}] {item['key']}: {item.get('value', 'N/A')}")
                if len(value) > 2:
                    print(f"     - ... and {len(value)-2} more")
            elif isinstance(value, dict):
                print(f"   • {key}: {{dict with {len(value)} keys}}")
                for k, v in list(value.items())[:2]:
                    if isinstance(v, (str, int, float, bool)):
                        print(f"     - {k}: {v}")
                if len(value) > 2:
                    print(f"     - ... and {len(value)-2} more keys")
            else:
                print(f"   • {key}: {type(value).__name__}")
    else:
        print(f"   • (empty or simple value): {input_data}")

    print(f"\n📤 OUTPUT:")
    if isinstance(output_data, dict) and len(output_data) > 0:
        for key, value in output_data.items():
            if isinstance(value, (str, int, float, bool)):
                print(f"   • {key}: {value}")
            elif isinstance(value, list):
                print(f"   • {key}: [{len(value)} items]")
                for i, item in enumerate(value[:2]):
                    if isinstance(item, str):
                        print(f"     - [{i}] {item}")
                    elif isinstance(item, dict) and any(k in item for k in ['actionId', 'key', 'name']):
                        identifier = item.get('actionId') or item.get('key') or item.get('name', f'item_{i}')
                        print(f"     - [{i}] {identifier}")
                if len(value) > 2:
                    print(f"     - ... and {len(value)-2} more")
            elif isinstance(value, dict):
                print(f"   • {key}: {{dict with {len(value)} keys}}")
                if 'goalType' in value:
                    print(f"     - goalType: {value['goalType']}")
                if 'category' in value:
                    print(f"     - category: {value['category']}")
                if 'modelId' in value:
                    print(f"     - modelId: {value['modelId']}")
            else:
                print(f"   • {key}: {type(value).__name__}")
    else:
        print(f"   • (empty or simple value): {output_data}")


def analyze_pipeline_stages(user_input):
    """파이프라인 각 단계별 상세 분석"""

    print(f"\n🎯 분석 대상: '{user_input}'")
    print("="*80)

    orchestrator = PipelineOrchestrator()

    # 전체 과정 실행하면서 각 단계 추적
    querygoal = orchestrator.process_natural_language(user_input)

    # pipelineLog에서 각 단계 정보 추출
    pipeline_log = querygoal.get("pipelineLog", {})
    stages = pipeline_log.get("stages", [])

    # 원본 입력
    original_input = user_input
    current_data = {"input": original_input}

    print(f"\n🚀 전체 파이프라인 시작")
    print(f"원본 입력: {original_input}")

    stage_names = {
        "patternMatching": "패턴 매칭 (자연어 분석)",
        "templateLoading": "템플릿 로딩 (기본 구조 생성)",
        "parameterFilling": "파라미터 채움 (데이터 바인딩)",
        "actionPlanResolution": "액션 플랜 해결 (실행 계획)",
        "modelSelection": "모델 선택 (AI/ML 모델)",
        "validation": "검증 (품질 체크)"
    }

    for i, stage_info in enumerate(stages, 1):
        stage_name = stage_info["stage"]
        stage_status = stage_info["status"]
        stage_result = stage_info.get("result", {})

        display_name = stage_names.get(stage_name, stage_name)

        # 각 단계의 입력은 이전 단계까지의 누적 결과
        if stage_name == "patternMatching":
            stage_input = {"original_input": original_input}
        elif stage_name == "templateLoading":
            stage_input = {"goalType": stages[0]["result"].get("goalType", "unknown")}
        elif stage_name == "parameterFilling":
            stage_input = {
                "extractedParameters": stages[0]["result"].get("extractedParameters", {}),
                "goalType": stages[0]["result"].get("goalType", "unknown")
            }
        elif stage_name == "actionPlanResolution":
            stage_input = {
                "goalType": stages[0]["result"].get("goalType", "unknown"),
                "parameters": querygoal["QueryGoal"].get("parameters", [])
            }
        elif stage_name == "modelSelection":
            stage_input = {
                "goalType": stages[0]["result"].get("goalType", "unknown"),
                "requiresModel": querygoal["QueryGoal"]["metadata"].get("requiresModel", False),
                "parameters": querygoal["QueryGoal"].get("parameters", [])
            }
        elif stage_name == "validation":
            stage_input = {
                "querygoal": "완성된 QueryGoal 구조",
                "goalType": querygoal["QueryGoal"].get("goalType", "unknown"),
                "parameters_count": len(querygoal["QueryGoal"].get("parameters", [])),
                "actions_count": len(querygoal["QueryGoal"]["metadata"].get("actionPlan", []))
            }
        else:
            stage_input = current_data

        print_stage_detail(display_name, stage_input, stage_result, i)

        # 다음 단계를 위한 누적 데이터 업데이트
        current_data.update(stage_result)

    # 최종 QueryGoal 결과 요약
    print(f"\n{'='*80}")
    print(f"📋 최종 생성된 QueryGoal 요약")
    print(f"{'='*80}")

    qg = querygoal["QueryGoal"]
    print(f"🆔 Goal ID: {qg['goalId']}")
    print(f"🎯 Goal Type: {qg['goalType']}")
    print(f"📂 Category: {qg['metadata']['category']}")
    print(f"🤖 Model Required: {qg['metadata']['requiresModel']}")
    print(f"📊 Parameters: {len(qg['parameters'])}")
    print(f"📋 Output Specs: {len(qg['outputSpec'])}")
    print(f"🔧 Action Plans: {len(qg['metadata']['actionPlan'])}")
    print(f"⚙️ Pipeline Stages: {qg['metadata']['pipelineStages']}")

    if qg.get('selectedModel'):
        print(f"🎯 Selected Model: {qg['selectedModel']['modelId']}")
        print(f"🔍 Selection Method: {qg.get('selectionProvenance', {}).get('selectionMethod', 'unknown')}")

    return querygoal


def main():
    """다양한 Goal에 대해 6단계 파이프라인 상세 분석"""

    print("🔬 QueryGoal 파이프라인 6단계 상세 분석")
    print("각 Goal별 단계별 입력/출력 값을 구체적으로 확인")
    print("="*80)

    test_cases = [
        {
            "name": "Goal 1: 진단 (모델 불필요)",
            "input": "Check cooling failure for machine M005"
        },
        {
            "name": "Goal 3: 예측 (모델 필요)",
            "input": "Predict production time for product type WIDGET999 with quantity 100"
        },
        {
            "name": "Goal 4: 추적 (모델 불필요)",
            "input": "Track product location for product id ITEM-2024-555"
        }
    ]

    for case in test_cases:
        print(f"\n\n{'🔹'*40}")
        print(f"🧪 테스트 케이스: {case['name']}")
        print(f"{'🔹'*40}")

        analyze_pipeline_stages(case['input'])


if __name__ == "__main__":
    main()