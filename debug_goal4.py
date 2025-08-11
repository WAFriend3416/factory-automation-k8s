#!/usr/bin/env python3
"""Goal 4 디버깅 스크립트"""

from execution_engine.planner import ExecutionPlanner
from execution_engine.agent import ExecutionAgent

# Planner와 Agent 초기화
planner = ExecutionPlanner()
agent = ExecutionAgent()

# Goal 4 파라미터
params = {
    "goal": "track_product_position",
    "product_id": "Product-C"
}

# Plan 생성
print("1. Creating plan...")
plan = planner.create_plan("track_product_position")
print(f"   Plan: {plan}")

# Agent 실행
print("\n2. Running agent...")
result = agent.run(plan, params)
print(f"   Result type: {type(result)}")
print(f"   Result: {result}")

# 최종 결과 확인
print("\n3. Final result:")
if "final_result" in result:
    final = result["final_result"]
    print(f"   Type: {type(final)}")
    print(f"   Value: {final}")
else:
    print("   No final_result found in:", result.keys())