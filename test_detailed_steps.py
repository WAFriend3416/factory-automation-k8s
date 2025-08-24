#!/usr/bin/env python3
"""
각 단계별 상세 입출력 테스트 스크립트
Goal 3 프로세스의 각 Step별 결과를 개별적으로 확인
"""

import json
import sys
import os
from pathlib import Path

# 환경 설정
sys.path.append(str(Path(__file__).resolve().parent))
os.environ['USE_STANDARD_SERVER'] = 'true'
os.environ['AAS_SERVER_IP'] = '127.0.0.1'
os.environ['AAS_SERVER_PORT'] = '5001'

from execution_engine.planner import ExecutionPlanner
from execution_engine.agent import ExecutionAgent

def test_detailed_steps():
    """Goal 3의 각 단계별 상세 테스트"""
    
    print("🔍 Goal 3 단계별 상세 분석")
    print("=" * 60)
    
    # 초기화
    planner = ExecutionPlanner()
    agent = ExecutionAgent()
    
    # Goal 3 계획 생성
    goal = "predict_first_completion_time"
    action_plan = planner.create_plan(goal)
    
    print("📋 Action Plan:")
    for i, step in enumerate(action_plan, 1):
        print(f"  Step {i}: {step.get('action_id')} ({step.get('type')})")
    print()
    
    # 요청 파라미터
    params = {
        "goal": goal,
        "product_id": "Product-A",
        "quantity": 10,
        "date_range": {
            "start": "2025-08-11", 
            "end": "2025-08-15"
        }
    }
    
    print("🎯 Input Parameters:")
    print(json.dumps(params, indent=2, ensure_ascii=False))
    print()
    
    # 단계별 실행 및 결과 출력
    execution_context = {}
    
    for i, step in enumerate(action_plan):
        step['params'] = params
        action_type = step.get("type")
        action_id = step.get("action_id")
        
        print(f"🔄 Step {i+1}: {action_id}")
        print(f"   Type: {action_type}")
        
        # 입력 출력
        print(f"   📥 Input:")
        print(f"      - step_details: {json.dumps(step, indent=8, ensure_ascii=False)}")
        print(f"      - context: {list(execution_context.keys())}")
        
        handler = agent.handlers.get(action_type)
        if not handler:
            print(f"   ❌ Handler not found for {action_type}")
            continue
            
        try:
            step_result = handler.execute(step, execution_context)
            execution_context[f"step_{i+1}_{action_id}"] = step_result
            
            print(f"   📤 Output:")
            if isinstance(step_result, dict):
                if len(json.dumps(step_result, indent=2)) > 1000:
                    # 큰 결과는 요약해서 표시
                    print(f"      - Type: {type(step_result).__name__}")
                    print(f"      - Keys: {list(step_result.keys())}")
                    if 'final_result' in step_result:
                        print(f"      - Final Result: {step_result.get('final_result')}")
                    else:
                        # 주요 필드만 표시
                        for key, value in list(step_result.items())[:3]:
                            if isinstance(value, (str, int, float, bool)):
                                print(f"      - {key}: {value}")
                            else:
                                print(f"      - {key}: {type(value).__name__} (size: {len(str(value))})")
                else:
                    print(json.dumps(step_result, indent=8, ensure_ascii=False))
            else:
                print(f"      - Result: {step_result}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            execution_context[f"step_{i+1}_{action_id}"] = {"error": str(e)}
        
        print()
    
    print("🎯 Final Execution Context:")
    for key, value in execution_context.items():
        print(f"  - {key}:")
        if isinstance(value, dict) and 'final_result' in value:
            print(f"    └── final_result: {value['final_result']}")
        elif isinstance(value, dict):
            print(f"    └── keys: {list(value.keys())}")
        else:
            print(f"    └── {type(value).__name__}: {str(value)[:100]}...")
    
    print()
    print("=" * 60)

def test_data_converter_details():
    """데이터 변환기 상세 테스트"""
    print("🔄 Data Converter 상세 분석")
    print("=" * 60)
    
    from simulation_data_converter import SimulationDataConverter
    
    converter = SimulationDataConverter("127.0.0.1", 5001)
    
    print("1️⃣ AAS 데이터 수집 시도:")
    aas_data = converter.fetch_all_aas_data()
    
    print(f"   📊 수집된 데이터:")
    print(f"      - Jobs: {len(aas_data.get('jobs', []))}")
    print(f"      - Machines: {len(aas_data.get('machines', []))}")
    print()
    
    print("2️⃣ AASX 형식 변환:")
    aasx_jobs = converter.convert_to_aasx_jobs(aas_data)
    aasx_machines = converter.convert_to_aasx_machines(aas_data)
    aasx_operations = converter.convert_to_aasx_operations(aas_data)
    
    print(f"   📋 변환 결과:")
    print(f"      - AASX Jobs: {len(aasx_jobs)}")
    print(f"      - AASX Machines: {len(aasx_machines)}")
    print(f"      - AASX Operations: {len(aasx_operations)}")
    print()
    
    print("3️⃣ 기본 데이터 생성:")
    default_data = converter.generate_default_data()
    
    print(f"   🏭 기본 데이터:")
    for key, value in default_data.items():
        if isinstance(value, list):
            print(f"      - {key}: {len(value)} items")
        else:
            print(f"      - {key}: {type(value).__name__}")
    
    print("=" * 60)

def main():
    """메인 테스트 함수"""
    print("🧪 Goal 3 상세 단계별 분석")
    print("=" * 80)
    
    try:
        # 데이터 변환기 상세 테스트
        test_data_converter_details()
        print()
        
        # 단계별 실행 테스트  
        test_detailed_steps()
        
    except Exception as e:
        print(f"❌ 테스트 실행 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()