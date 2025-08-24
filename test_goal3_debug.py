#!/usr/bin/env python3
"""
Goal 3 Debug Script - Step by step execution
"""
import sys
import os
from pathlib import Path

# 환경변수 설정
os.environ['USE_STANDARD_SERVER'] = 'true'
os.environ['AAS_SERVER_IP'] = '127.0.0.1'
os.environ['AAS_SERVER_PORT'] = '5001'
os.environ['FORCE_LOCAL_MODE'] = 'true'

sys.path.append(str(Path(__file__).resolve().parent))

from execution_engine.planner import ExecutionPlanner
from execution_engine.agent import ExecutionAgent

def test_goal3_steps():
    print("=" * 60)
    print("🔍 Goal 3 Debug - Step by Step Execution")
    print("=" * 60)
    
    try:
        # Step 1: Initialize Planner
        print("\n1️⃣ Initializing Planner...")
        planner = ExecutionPlanner()
        print("   ✅ Planner initialized")
        
        # Step 2: Create execution plan
        print("\n2️⃣ Creating execution plan for Goal 3...")
        goal = "predict_first_completion_time"
        action_plan = planner.create_plan(goal)
        print(f"   📋 Action plan created with {len(action_plan)} steps:")
        for i, step in enumerate(action_plan, 1):
            print(f"      {i}. {step['action_id']} (type: {step['type']})")
        
        # Step 3: Initialize Agent
        print("\n3️⃣ Initializing Execution Agent...")
        agent = ExecutionAgent()
        print("   ✅ Agent initialized")
        
        # Step 4: Execute plan step by step
        print("\n4️⃣ Executing plan step by step...")
        params = {
            "goal": goal,
            "product_id": "P1",
            "quantity": 100
        }
        
        execution_context = {}
        
        for i, step in enumerate(action_plan, 1):
            print(f"\n   Step {i}: {step['action_id']}")
            step['params'] = params
            
            try:
                action_type = step.get("type")
                handler = agent.handlers.get(action_type)
                
                if not handler:
                    print(f"      ⚠️ No handler for type '{action_type}'")
                    continue
                
                print(f"      🔄 Executing with {handler.__class__.__name__}...")
                
                # Execute with timeout for debugging
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Step execution timed out after 5 seconds")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(5)  # 5 second timeout per step
                
                try:
                    step_result = handler.execute(step, execution_context)
                    signal.alarm(0)  # Cancel alarm
                    
                    execution_context[f"step_{i}_{step['action_id']}"] = step_result
                    print(f"      ✅ Step completed")
                    
                    # Print result summary
                    if isinstance(step_result, dict):
                        keys = list(step_result.keys())[:3]
                        print(f"      📊 Result keys: {keys}")
                        
                except TimeoutError as te:
                    print(f"      ⏱️ Step timed out: {te}")
                    signal.alarm(0)
                    break
                    
            except Exception as e:
                print(f"      ❌ Step failed: {e}")
                import traceback
                traceback.print_exc()
                break
        
        print("\n" + "=" * 60)
        print("✅ Debug execution completed!")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_goal3_steps()