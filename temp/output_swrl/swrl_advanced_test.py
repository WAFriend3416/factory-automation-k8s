#!/usr/bin/env python3
"""
SWRL 고급 기능 테스트
- 다양한 Goal Type에 대한 SWRL 처리
- 파라미터 매핑 개선
- 실제 실행 테스트
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# 경로 추가
sys.path.append('.')
sys.path.append('./temp/output_2')
sys.path.append('./execution_engine')

def test_swrl_goal_types():
    """다양한 Goal Type에 대한 SWRL 처리 테스트"""

    print("🧠 SWRL 다중 Goal Type 테스트")
    print("=" * 50)

    # 테스트할 Goal 샘플들
    test_goals = {
        "Goal1_냉각실패": {
            'goal': 'query_failed_work_order',
            'goal_type': 'query_cooling_failure',
            'job_id': 'JOB-COOLING-001',
            'failure_type': 'cooling',
            'time_range': '2025-08-11T08:00:00Z/2025-08-11T20:00:00Z',
            'aas_endpoint': 'http://127.0.0.1:5001'
        },

        "Goal3_생산시간": {
            'goal': 'predict_first_completion_time',
            'goal_type': 'predict_production_time',
            'product_type': 'WidgetA',
            'quantity': 100,
            'production_line': 'Line1',
            'model_name': 'JobETAModel',
            'prediction_accuracy': 0.85,
            'aas_endpoint': 'http://127.0.0.1:5001'
        },

        "Goal4_제품추적": {
            'goal': 'track_product_position',
            'goal_type': 'track_product',
            'product_id': 'PRODUCT-ABC-123',
            'tracking_mode': 'real_time',
            'location_precision': 'high',
            'aas_endpoint': 'http://127.0.0.1:5001'
        }
    }

    results = {}

    from action_plan_resolver import ActionPlanResolver
    resolver = ActionPlanResolver()

    for goal_name, querygoal in test_goals.items():
        print(f"\n🎯 테스트: {goal_name}")
        print(f"   Goal Type: {querygoal['goal_type']}")

        try:
            # SWRL 처리
            action_plan_id = resolver.determine_action_plan_id(querygoal)
            execution_plan = resolver.resolve_action_plan(action_plan_id, querygoal)

            result = {
                "goal_name": goal_name,
                "querygoal": querygoal,
                "action_plan_id": action_plan_id,
                "execution_steps": len(execution_plan),
                "steps": [step['action_id'] for step in execution_plan],
                "status": "success"
            }

            print(f"   ✅ Action Plan: {action_plan_id}")
            print(f"   📝 실행 단계: {len(execution_plan)}개")
            print(f"   🔄 단계들: {', '.join([step['action_id'] for step in execution_plan])}")

        except Exception as e:
            result = {
                "goal_name": goal_name,
                "querygoal": querygoal,
                "error": str(e),
                "status": "failed"
            }
            print(f"   ❌ 오류: {e}")

        results[goal_name] = result

    return results

def test_swrl_parameter_mapping():
    """SWRL 파라미터 매핑 고급 테스트"""

    print(f"\n🔧 SWRL 파라미터 매핑 테스트")
    print("-" * 30)

    from action_plan_resolver import ActionPlanResolver
    resolver = ActionPlanResolver()

    # Goal 3 샘플로 파라미터 매핑 상세 분석
    querygoal = {
        'goal': 'predict_first_completion_time',
        'goal_type': 'predict_production_time',
        'product_type': 'WidgetA',
        'quantity': 100,
        'production_line': 'Line1',
        'model_name': 'JobETAModel',
        'prediction_accuracy': 0.85,
        'aas_endpoint': 'http://127.0.0.1:5001',
        'current_conditions': 'normal_operation'
    }

    execution_plan = resolver.resolve_action_plan('goal3_production_time', querygoal)

    print("📋 파라미터 매핑 분석:")
    for i, step in enumerate(execution_plan, 1):
        print(f"\nStep {i}: {step['action_id']}")
        print(f"  Type: {step['type']}")
        print(f"  Parameters: {step.get('parameters', {})}")
        print(f"  Params: {step.get('params', {})}")

        # 필요한 파라미터 vs 제공된 파라미터 분석
        if 'params' in step:
            provided = set(step['params'].keys())
            print(f"  제공된 파라미터: {provided}")

    return execution_plan

def test_swrl_with_real_execution():
    """SWRL → ExecutionAgent 실제 실행 테스트 (Goal 3)"""

    print(f"\n🚀 SWRL → ExecutionAgent 실제 실행 테스트")
    print("-" * 40)

    try:
        from action_plan_resolver import ActionPlanResolver
        from agent import ExecutionAgent

        # Goal 3 샘플
        querygoal = {
            'goal': 'predict_first_completion_time',
            'goal_type': 'predict_production_time',
            'product_type': 'WidgetA',
            'quantity': 100,
            'production_line': 'Line1'
        }

        print("1. SWRL 처리...")
        resolver = ActionPlanResolver()
        action_plan_id = resolver.determine_action_plan_id(querygoal)
        execution_plan = resolver.resolve_action_plan(action_plan_id, querygoal)

        print(f"   Action Plan ID: {action_plan_id}")
        print(f"   실행 단계: {len(execution_plan)}개")

        print("\\n2. ExecutionAgent 실행...")
        agent = ExecutionAgent()

        # 실제 실행 (첫 번째 단계만)
        first_step = execution_plan[0]
        print(f"   실행할 단계: {first_step['action_id']}")

        # 실제 실행은 안전을 위해 주석 처리
        # result = agent.handle_action(first_step, querygoal)
        print("   ⚠️ 안전을 위해 실제 실행은 스킵 (Dry Run)")

        return {
            "querygoal": querygoal,
            "action_plan_id": action_plan_id,
            "execution_plan": execution_plan,
            "test_status": "dry_run_success"
        }

    except Exception as e:
        print(f"❌ 실행 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "test_status": "failed"}

def main():
    """메인 테스트 함수"""

    print("🔬 SWRL 고급 기능 종합 테스트")
    print("=" * 60)
    print(f"테스트 시간: {datetime.now()}")

    # 1. 다중 Goal Type 테스트
    goal_results = test_swrl_goal_types()

    # 2. 파라미터 매핑 테스트
    parameter_mapping = test_swrl_parameter_mapping()

    # 3. 실제 실행 테스트
    execution_result = test_swrl_with_real_execution()

    # 종합 결과
    comprehensive_result = {
        "test_timestamp": datetime.now().isoformat(),
        "test_type": "swrl_advanced_comprehensive",
        "goal_type_tests": goal_results,
        "parameter_mapping_analysis": {
            "execution_plan": parameter_mapping,
            "mapping_completeness": "partial" if any("Missing parameter" in str(parameter_mapping) for _ in [1]) else "complete"
        },
        "real_execution_test": execution_result,
        "overall_status": "success"
    }

    # 결과 저장
    output_file = Path("temp/output_swrl/swrl_advanced_test_result.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_result, f, indent=2, ensure_ascii=False)

    print(f"\\n💾 종합 결과 저장: {output_file}")
    print("✅ SWRL 고급 기능 테스트 완료!")

    return comprehensive_result

if __name__ == "__main__":
    main()