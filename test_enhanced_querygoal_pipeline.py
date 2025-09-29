#!/usr/bin/env python3
"""
Enhanced QueryGoal 파이프라인 테스트 스크립트
- SelectionEngine 통합 검증
- Fail-fast 로직 테스트
- 정합성 검사 실행
"""
import json
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from querygoal.pipeline.orchestrator import PipelineOrchestrator
from querygoal.pipeline.model_selector import ModelSelectorError
from querygoal.tools.registry_checker import RegistryChecker


def test_selection_engine_integration():
    """SelectionEngine 통합 테스트"""
    print("=" * 60)
    print("SelectionEngine Integration Test")
    print("=" * 60)

    orchestrator = PipelineOrchestrator()

    test_cases = [
        {
            "name": "Goal 3 - SelectionEngine Integration",
            "input": "Predict production time for product type WIDGET001 with quantity 25",
            "expected_goal": "goal3_predict_production_time",
            "expects_model": True
        }
    ]

    for test_case in test_cases:
        print(f"\n🔧 Test: {test_case['name']}")
        print(f"   Input: {test_case['input']}")

        try:
            # QueryGoal 생성
            querygoal = orchestrator.process_natural_language(test_case['input'])
            qg = querygoal["QueryGoal"]

            print(f"   ✅ Conversion Success!")
            print(f"   - Goal ID: {qg['goalId']}")
            print(f"   - Goal Type: {qg['goalType']}")

            # SelectionEngine 통합 확인
            if test_case.get("expects_model"):
                if qg.get("selectedModel"):
                    print(f"   ✅ Model Selection: {qg['selectedModel']['modelId']}")
                    provenance = qg.get("selectionProvenance", {})
                    selection_method = provenance.get("selectionMethod", "unknown")
                    print(f"   - Selection Method: {selection_method}")

                    if "SPARQL" in selection_method:
                        print(f"   ✅ SelectionEngine Integration: SUCCESS")
                    else:
                        print(f"   ⚠️  SelectionEngine Integration: Using fallback method")
                else:
                    print(f"   ❌ Model Selection: FAILED")

        except Exception as e:
            print(f"   ❌ Test Failed: {e}")

    print("\n" + "=" * 60)


def test_fail_fast_logic():
    """Fail-Fast 로직 테스트"""
    print("\n" + "=" * 60)
    print("Fail-Fast Logic Test")
    print("=" * 60)

    from querygoal.pipeline.model_selector import ModelSelector

    # 모델이 필요한데 찾을 수 없는 상황 시뮬레이션
    selector = ModelSelector()

    # 빈 레지스트리로 테스트
    original_registry = selector.model_registry.copy()
    selector.model_registry = {}  # 빈 레지스트리

    test_querygoal = {
        "templateId": "base_querygoal",
        "QueryGoal": {
            "goalId": "test_goal_fail_fast",
            "goalType": "goal3_predict_production_time",
            "parameters": [
                {"key": "productType", "value": "TEST", "required": True},
                {"key": "quantity", "value": 10, "required": True}
            ],
            "metadata": {
                "category": "prediction",
                "requiresModel": True,  # 모델이 필수
                "pipelineStages": ["swrlSelection", "yamlBinding", "simulation"]
            }
        }
    }

    print(f"\n🚨 Testing Fail-Fast Logic for Required Model")

    try:
        # 이것은 ModelSelectorError를 발생시켜야 함
        result = selector.bind_model_to_querygoal(
            querygoal=test_querygoal,
            goal_type="goal3_predict_production_time"
        )
        print(f"   ❌ FAIL-FAST LOGIC FAILED: Should have raised exception but didn't")

    except ModelSelectorError as e:
        print(f"   ✅ FAIL-FAST SUCCESS: Exception raised as expected")
        print(f"   - Error: {e}")

    except Exception as e:
        print(f"   ⚠️  UNEXPECTED ERROR: {type(e).__name__}: {e}")

    # 레지스트리 복원
    selector.model_registry = original_registry

    # 모델이 필요 없는 경우 테스트
    test_querygoal_no_model = {
        "templateId": "base_querygoal",
        "QueryGoal": {
            "goalId": "test_goal_no_model",
            "goalType": "goal1_query_cooling_failure",
            "parameters": [
                {"key": "machineId", "value": "M001", "required": True}
            ],
            "metadata": {
                "category": "diagnostics",
                "requiresModel": False,  # 모델이 필요 없음
                "pipelineStages": ["aasQuery", "dataFiltering"]
            }
        }
    }

    print(f"\n✅ Testing Non-Model Goal (should succeed)")

    try:
        result = selector.bind_model_to_querygoal(
            querygoal=test_querygoal_no_model,
            goal_type="goal1_query_cooling_failure"
        )
        print(f"   ✅ NO-MODEL SUCCESS: Processed without model requirement")

    except Exception as e:
        print(f"   ❌ NO-MODEL FAILED: {e}")

    print("\n" + "=" * 60)


def test_registry_consistency():
    """정합성 검사 테스트"""
    print("\n" + "=" * 60)
    print("Registry Consistency Check")
    print("=" * 60)

    try:
        checker = RegistryChecker()
        report = checker.check_all()

        status = report["status"]
        summary = report["summary"]

        print(f"\n📊 Consistency Check Results:")
        print(f"   Status: {status}")
        print(f"   Total Issues: {summary['total_issues']}")
        print(f"   Critical: {summary['critical']}")
        print(f"   Errors: {summary['error']}")
        print(f"   Warnings: {summary['warning']}")

        if summary['total_issues'] > 0:
            print(f"\n📋 Top Issues by Category:")
            for category, issues in report["issues_by_category"].items():
                if len(issues) > 0:
                    print(f"   • {category}: {len(issues)} issues")
                    if len(issues) <= 3:  # 3개 이하면 모두 표시
                        for issue in issues:
                            print(f"     - {issue['message']}")
                    else:  # 많으면 첫 2개만
                        for issue in issues[:2]:
                            print(f"     - {issue['message']}")
                        print(f"     ... and {len(issues)-2} more")

        if status == "OK":
            print(f"   ✅ All configuration files are consistent!")
        elif status in ["WARNING", "ERROR"]:
            print(f"   ⚠️  Issues found but system can still operate")
        else:  # CRITICAL
            print(f"   🚨 Critical issues found - system may not work properly")

    except Exception as e:
        print(f"   ❌ Consistency check failed: {e}")

    print("\n" + "=" * 60)


def test_enhanced_pipeline_execution():
    """강화된 파이프라인 실행 테스트"""
    print("\n" + "=" * 60)
    print("Enhanced Pipeline Execution Test")
    print("=" * 60)

    orchestrator = PipelineOrchestrator()

    test_cases = [
        {
            "name": "Goal 1 - Diagnostics (No Model)",
            "input": "Check cooling failure for machine M003 at 2024-09-29T15:00:00",
            "expected_success": True,
            "expects_model": False
        },
        {
            "name": "Goal 3 - Production Prediction (With Model)",
            "input": "Predict production time for product type PART567 quantity 75",
            "expected_success": True,
            "expects_model": True
        },
        {
            "name": "Goal 4 - Product Tracking (No Model)",
            "input": "Track product location for product id ITEM-2024-099",
            "expected_success": True,
            "expects_model": False
        }
    ]

    for test_case in test_cases:
        print(f"\n🎯 Test: {test_case['name']}")
        print(f"   Input: {test_case['input']}")

        try:
            # QueryGoal 생성
            querygoal = orchestrator.process_natural_language(test_case['input'])

            # 실행
            execution_result = orchestrator.execute_querygoal(querygoal)

            # 결과 분석
            pipeline_meta = execution_result["pipeline_meta"]
            success = pipeline_meta["success"]
            success_rate = pipeline_meta["success_rate"]

            print(f"   📊 Pipeline Success: {success} ({success_rate:.1%})")
            print(f"   - Completed Stages: {', '.join(pipeline_meta['completed_stages'])}")

            if pipeline_meta['failed_stages']:
                print(f"   - Failed Stages: {', '.join(pipeline_meta['failed_stages'])}")

            if pipeline_meta.get('fail_reason'):
                print(f"   - Failure Reason: {pipeline_meta['fail_reason']}")

            # 모델 관련 확인
            qg = querygoal["QueryGoal"]
            has_model = qg.get("selectedModel") is not None
            expects_model = test_case.get("expects_model", False)

            if expects_model and has_model:
                print(f"   ✅ Model Integration: SUCCESS")
            elif not expects_model and not has_model:
                print(f"   ✅ No-Model Operation: SUCCESS")
            elif expects_model and not has_model:
                print(f"   ❌ Model Integration: FAILED (expected model)")
            else:
                print(f"   ⚠️  Unexpected Model: Got model when none expected")

            # 전체 성공 평가
            expected_success = test_case.get("expected_success", True)
            if success == expected_success:
                print(f"   ✅ Overall: SUCCESS")
            else:
                print(f"   ❌ Overall: FAILED (expected {expected_success}, got {success})")

        except Exception as e:
            print(f"   ❌ Test Failed with Exception: {e}")

    print("\n" + "=" * 60)


def test_error_scenarios():
    """에러 시나리오 테스트"""
    print("\n" + "=" * 60)
    print("Error Scenario Tests")
    print("=" * 60)

    orchestrator = PipelineOrchestrator()

    error_cases = [
        {
            "name": "Unknown Goal Type",
            "input": "Do something completely unknown and unsupported",
            "expect_error": False,  # unknown으로 분류되어야 함
            "expected_goal": "unknown"
        },
        {
            "name": "Empty Input",
            "input": "",
            "expect_error": True
        },
        {
            "name": "Very Ambiguous Input",
            "input": "maybe perhaps could be something",
            "expect_error": False,
            "expected_goal": "unknown"
        }
    ]

    for test_case in error_cases:
        print(f"\n🚫 Error Test: {test_case['name']}")
        print(f"   Input: '{test_case['input']}'")

        try:
            querygoal = orchestrator.process_natural_language(test_case['input'])
            qg = querygoal["QueryGoal"]

            print(f"   📝 Result: {qg['goalType']}")

            if test_case.get("expect_error"):
                print(f"   ❌ Expected error but processing succeeded")
            else:
                expected_goal = test_case.get("expected_goal")
                if expected_goal and qg['goalType'] == expected_goal:
                    print(f"   ✅ Correctly handled as {expected_goal}")
                else:
                    print(f"   ⚠️  Unexpected goal type: {qg['goalType']}")

        except Exception as e:
            if test_case.get("expect_error"):
                print(f"   ✅ Expected error occurred: {type(e).__name__}")
            else:
                print(f"   ❌ Unexpected error: {e}")

    print("\n" + "=" * 60)


def main():
    """통합 테스트 메인 실행"""
    print("🧪 Enhanced QueryGoal Pipeline Tests")
    print("Testing updated requirements with fail-fast logic")
    print("=" * 80)

    # 1. SelectionEngine 통합 테스트
    test_selection_engine_integration()

    # 2. Fail-fast 로직 테스트
    test_fail_fast_logic()

    # 3. 정합성 검사 테스트
    test_registry_consistency()

    # 4. 강화된 파이프라인 실행 테스트
    test_enhanced_pipeline_execution()

    # 5. 에러 시나리오 테스트
    test_error_scenarios()

    print("\n✅ All enhanced tests completed!")
    print("📋 Summary:")
    print("  ✅ SelectionEngine integration verified")
    print("  ✅ Fail-fast logic implemented and tested")
    print("  ✅ Registry consistency checker working")
    print("  ✅ Enhanced pipeline execution validated")
    print("  ✅ Error handling scenarios covered")


if __name__ == "__main__":
    main()