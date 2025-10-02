#!/usr/bin/env python3
"""
현실적인 SWRL 파이프라인 테스트 (기존 시스템 통합)
Realistic SWRL Pipeline Test with Existing System Integration
"""
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append('/Users/jsh/Desktop/aas-project/gemini-ver/factory-automation-k8s')

try:
    from execution_engine.swrl.selection_engine import SelectionEngine, SelectionEngineError
    from execution_engine.agent import ExecutionAgent
    from execution_engine.planner import ExecutionPlanner
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("현재 시스템 상태를 확인하세요.")
    sys.exit(1)

class RealisticSWRLPipelineTest:
    """현실적인 SWRL 파이프라인 테스트 (기존 시스템과 통합)"""

    def __init__(self):
        try:
            self.swrl_engine = SelectionEngine()
            print("✅ SWRL 엔진 초기화 성공")
        except Exception as e:
            print(f"❌ SWRL 엔진 초기화 실패: {e}")
            self.swrl_engine = None

        try:
            self.execution_agent = ExecutionAgent()
            print("✅ ExecutionAgent 초기화 성공")
        except Exception as e:
            print(f"❌ ExecutionAgent 초기화 실패: {e}")
            self.execution_agent = None

        try:
            self.execution_planner = ExecutionPlanner()
            print("✅ ExecutionPlanner 초기화 성공")
        except Exception as e:
            print(f"❌ ExecutionPlanner 초기화 실패: {e}")
            self.execution_planner = None

    def test_realistic_swrl_pipeline(self):
        """현실적인 SWRL 파이프라인 테스트"""
        print("=" * 80)
        print("🔧 현실적인 SWRL 파이프라인 테스트")
        print("=" * 80)

        # Test 1: 기존 시스템의 QueryGoal 형태로 SWRL 테스트
        print("\n📋 Test 1: 기존 QueryGoal 형태로 SWRL 추론 테스트")
        self._test_legacy_querygoal_format()

        # Test 2: SWRL 결과를 기존 ExecutionAgent로 전달
        print("\n🔄 Test 2: SWRL 결과 → ExecutionAgent 통합 테스트")
        self._test_swrl_to_execution_agent()

        # Test 3: 실제 AAS 서버 연동 확인
        print("\n📡 Test 3: 실제 AAS 서버 연동 확인")
        self._test_actual_aas_integration()

        print("\n" + "=" * 80)
        print("✅ 현실적인 SWRL 파이프라인 테스트 완료")
        print("=" * 80)

    def _test_legacy_querygoal_format(self):
        """기존 QueryGoal 형태로 SWRL 테스트"""
        if not self.swrl_engine:
            print("   ⚠️ SWRL 엔진이 없어 스킵")
            return

        # 기존 시스템에서 사용하던 Goal 3 QueryGoal 형태
        legacy_querygoal = {
            "id": "querygoal_goal3_realistic",
            "goal_type": "predict_production_time",
            "natural_language_query": "WidgetA 100개 생산하는데 얼마나 걸릴까요?",
            "parameters": {
                "goal": "predict_first_completion_time",
                "product_type": "WidgetA",
                "quantity": 100,
                "production_line": "Line1",
                "current_conditions": {
                    "machine_availability": "high",
                    "material_stock": "sufficient"
                }
            }
        }

        print(f"   📥 입력 QueryGoal (기존 형태):")
        print(f"   {json.dumps(legacy_querygoal, indent=4, ensure_ascii=False)}")

        try:
            # 기존 형태를 SWRL 엔진이 이해할 수 있는 형태로 변환
            swrl_compatible_goal = self._convert_legacy_to_swrl_format(legacy_querygoal)

            print(f"\n   🔄 SWRL 호환 형태로 변환:")
            print(f"   {json.dumps(swrl_compatible_goal, indent=4, ensure_ascii=False)}")

            # SWRL 엔진으로 모델 선택
            result = self.swrl_engine.select_model(swrl_compatible_goal)

            print(f"\n   ✅ SWRL 추론 성공!")
            print(f"   - 선택된 모델: {result['QueryGoal']['selectedModel']['modelId']}")
            print(f"   - 선택 규칙: {result['QueryGoal']['selectionProvenance']['ruleName']}")

            return result

        except Exception as e:
            print(f"   ❌ SWRL 추론 실패: {e}")
            return None

    def _create_fallback_execution_plan(self, selected_model: Dict[str, Any]) -> list:
        """폴백 실행 계획 생성 (기존 시스템 방식)"""
        return [
            {
                "action_id": "ActionFetchProductSpec",
                "type": "aas_query",
                "target_submodel_id": "urn:factory:submodel:process_plan",
                "params": {
                    "goal": "predict_first_completion_time"
                }
            },
            {
                "action_id": "ActionFetchAllMachineData",
                "type": "aas_query",
                "target_submodel_id": None,
                "params": {
                    "goal": "predict_first_completion_time"
                }
            },
            {
                "action_id": "ActionRunSimulation",
                "type": "docker_run",
                "target_submodel_id": None,
                "params": {
                    "goal": "predict_first_completion_time",
                    "image": selected_model["container"]["image"],
                    "scenario": "job_completion_prediction"
                }
            }
        ]

    def _convert_legacy_to_swrl_format(self, legacy_querygoal: Dict[str, Any]) -> Dict[str, Any]:
        """기존 QueryGoal 형태를 SWRL 엔진 형태로 변환"""
        goal_type = legacy_querygoal.get("goal_type", "unknown")
        parameters = legacy_querygoal.get("parameters", {})

        # goal_type 매핑
        swrl_goal_type_mapping = {
            "predict_production_time": "predict_job_completion_time",
            "query_cooling_failure": "detect_job_anomaly",
            "track_product_location": "track_product_status"
        }

        swrl_goal_type = swrl_goal_type_mapping.get(goal_type, goal_type)

        # 파라미터를 SWRL 형태로 변환
        swrl_parameters = []
        for key, value in parameters.items():
            if isinstance(value, (str, int, float)):
                swrl_parameters.append({"key": key, "value": str(value)})
            elif isinstance(value, dict):
                # 복잡한 객체는 JSON 문자열로 변환
                swrl_parameters.append({"key": key, "value": json.dumps(value)})

        # 현재 시간 파라미터 추가
        swrl_parameters.append({"key": "current_time", "value": "@현재시간"})

        return {
            "QueryGoal": {
                "goalId": legacy_querygoal.get("id", "converted_goal"),
                "goalType": swrl_goal_type,
                "parameters": swrl_parameters,
                "outputSpec": [
                    {"name": "completion_time", "datatype": "datetime"},
                    {"name": "confidence_score", "datatype": "number"}
                ]
            }
        }

    def _test_swrl_to_execution_agent(self):
        """SWRL 결과를 ExecutionAgent로 전달하는 테스트"""
        if not self.swrl_engine or not self.execution_agent:
            print("   ⚠️ 필요한 컴포넌트가 없어 스킵")
            return

        # SWRL로 모델 선택
        test_querygoal = {
            "QueryGoal": {
                "goalId": "swrl_to_agent_test",
                "goalType": "predict_job_completion_time",
                "parameters": [
                    {"key": "goal", "value": "predict_first_completion_time"},
                    {"key": "product_type", "value": "WidgetA"},
                    {"key": "quantity", "value": "100"},
                    {"key": "current_time", "value": "@현재시간"}
                ],
                "outputSpec": [
                    {"name": "completion_time", "datatype": "datetime"}
                ]
            }
        }

        try:
            # SWRL 모델 선택
            swrl_result = self.swrl_engine.select_model(test_querygoal)
            selected_model = swrl_result["QueryGoal"]["selectedModel"]

            print(f"   ✅ SWRL 선택 모델: {selected_model['modelId']}")

            # ExecutionPlanner를 사용해서 실제 온톨로지 기반 실행 계획 생성
            if self.execution_planner:
                try:
                    execution_plan = self.execution_planner.create_plan("predict_first_completion_time")
                    print(f"   📋 온톨로지 기반 실행 계획: {execution_plan}")
                except Exception as e:
                    print(f"   ⚠️ ExecutionPlanner 실패, 기본 계획 사용: {e}")
                    execution_plan = self._create_fallback_execution_plan(selected_model)
            else:
                execution_plan = self._create_fallback_execution_plan(selected_model)

            print(f"   📋 생성된 실행 계획: {len(execution_plan)}개 단계")

            # ExecutionAgent 실행 (기존 방식)
            goal_params = {
                "goal": "predict_first_completion_time",
                "product_type": "WidgetA",
                "quantity": 100
            }

            agent_result = self.execution_agent.run(execution_plan, goal_params)

            print(f"   ✅ ExecutionAgent 실행 완료")
            print(f"   📊 결과: {agent_result}")

            return agent_result

        except Exception as e:
            print(f"   ❌ SWRL → ExecutionAgent 통합 실패: {e}")
            return None

    def _test_actual_aas_integration(self):
        """실제 AAS 서버 연동 확인"""
        if not self.execution_agent:
            print("   ⚠️ ExecutionAgent가 없어 스킵")
            return

        print("   🔍 현재 AAS 서버 설정 확인...")

        try:
            # 환경 변수 확인
            use_standard = os.getenv("USE_STANDARD_SERVER", "false").lower() == "true"
            aas_ip = os.getenv("AAS_SERVER_IP", "127.0.0.1")
            aas_port = os.getenv("AAS_SERVER_PORT", "5001")

            print(f"   - USE_STANDARD_SERVER: {use_standard}")
            print(f"   - AAS_SERVER_IP: {aas_ip}")
            print(f"   - AAS_SERVER_PORT: {aas_port}")

            # 실제 AAS 쿼리 테스트
            aas_test_plan = [
                {
                    "action_id": "ActionFetchProductSpec",
                    "handler_type": "aas_query",
                    "params": {
                        "goal": "predict_first_completion_time",
                        "target_sm_id": "urn:factory:submodel:process_plan:J1"
                    }
                }
            ]

            print(f"   📡 실제 AAS 서버 쿼리 테스트...")
            result = self.execution_agent.run(aas_test_plan, {"goal": "predict_first_completion_time"})

            if result and "process_specifications" in result:
                print(f"   ✅ 실제 AAS 서버 연동 성공!")
                print(f"   📊 수신 데이터: {len(result.get('process_specifications', []))}개 항목")
            else:
                print(f"   ⚠️ AAS 서버 응답: {result}")

            return result

        except Exception as e:
            print(f"   ❌ 실제 AAS 연동 테스트 실패: {e}")
            return None

    def run_complete_realistic_test(self):
        """완전한 현실적 테스트 실행"""
        print("🚀 완전한 현실적 SWRL 파이프라인 테스트 시작")

        # 기존 Goal 3 시나리오와 동일한 QueryGoal
        realistic_goal = {
            "id": "realistic_swrl_goal3",
            "goal_type": "predict_production_time",
            "natural_language_query": "WidgetA 100개를 Line1에서 생산하는데 얼마나 걸릴까요?",
            "parameters": {
                "goal": "predict_first_completion_time",
                "product_type": "WidgetA",
                "quantity": 100,
                "production_line": "Line1",
                "current_conditions": {
                    "machine_availability": "high",
                    "material_stock": "sufficient",
                    "operator_shift": "day"
                }
            }
        }

        results = {
            "input": realistic_goal,
            "swrl_selection": None,
            "execution_result": None,
            "aas_data": None,
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Step 1: SWRL 모델 선택
            print("\n🧠 Step 1: SWRL 기반 모델 선택")
            swrl_compatible = self._convert_legacy_to_swrl_format(realistic_goal)
            swrl_result = self.swrl_engine.select_model(swrl_compatible)
            results["swrl_selection"] = swrl_result

            selected_model = swrl_result["QueryGoal"]["selectedModel"]
            print(f"   선택된 모델: {selected_model['modelId']}")

            # Step 2: 기존 ExecutionAgent로 실행
            print("\n🤖 Step 2: ExecutionAgent를 통한 실행")

            # ExecutionPlanner로 실행 계획 생성
            if self.execution_planner:
                try:
                    execution_plan = self.execution_planner.create_plan("predict_first_completion_time")
                    print(f"   📋 온톨로지 기반 실행 계획 생성됨: {len(execution_plan)}개 단계")
                except Exception as e:
                    print(f"   ⚠️ ExecutionPlanner 실패, 폴백 계획 사용: {e}")
                    execution_plan = self._create_fallback_execution_plan(selected_model)
            else:
                execution_plan = self._create_fallback_execution_plan(selected_model)

            execution_result = self.execution_agent.run(execution_plan, realistic_goal["parameters"])
            results["execution_result"] = execution_result

            print(f"   실행 결과: {execution_result}")

            # 결과 저장
            result_file = "/Users/jsh/Desktop/aas-project/gemini-ver/factory-automation-k8s/temp/output_swrl/realistic_swrl_test_result.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"\n💾 테스트 결과 저장: {result_file}")

            return results

        except Exception as e:
            print(f"\n❌ 완전한 테스트 실패: {e}")
            results["error"] = str(e)
            return results

def main():
    """메인 테스트 실행"""
    print("🔧 현실적인 SWRL 파이프라인 테스트")

    tester = RealisticSWRLPipelineTest()

    # 개별 테스트 실행
    tester.test_realistic_swrl_pipeline()

    # 완전한 통합 테스트
    print("\n" + "="*50)
    complete_result = tester.run_complete_realistic_test()

    # 최종 요약
    print("\n📋 최종 테스트 요약:")
    if "error" not in complete_result:
        print("   ✅ SWRL 파이프라인이 기존 시스템과 성공적으로 통합됨")
        print(f"   - SWRL 모델 선택: 성공")
        print(f"   - ExecutionAgent 실행: 성공")
        print(f"   - 결과 데이터: 생성됨")
    else:
        print(f"   ❌ 통합 테스트 실패: {complete_result['error']}")

if __name__ == "__main__":
    main()