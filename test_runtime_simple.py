#!/usr/bin/env python3
"""
Simple Goal3 Runtime Test - Direct test without context creation
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from querygoal.runtime.executor import QueryGoalExecutor

async def test_goal3_runtime():
    """Simple Goal3 Runtime Test"""

    print("\n" + "="*60)
    print("🔬 Simple Goal3 Runtime Test")
    print("="*60)

    # QueryGoal Executor 초기화
    executor = QueryGoalExecutor()
    print("✅ QueryGoal Executor initialized")

    # QueryGoal 생성
    querygoal = {
        "QueryGoal": {
            "goalId": f"goal3_test_{datetime.now().strftime('%H%M%S')}",
            "goalType": "goal3_predict_production_time",
            "parameters": [
                {"key": "productId", "value": "TEST"},
                {"key": "quantity", "value": 5}
            ],
            "selectedModel": {
                "modelId": "NSGA2SimulatorModel",
                "metaDataFile": "NSGA2Model_sources.yaml",
                "container": {
                    "image": "factory-nsga2:latest",
                    "registry": "localhost:5000"
                }
            },
            "metadata": {
                "pipelineStages": ["swrlSelection", "yamlBinding", "simulation"],
                "requiresModel": True,
                "dataSourceTypes": ["aas_property", "aas_shell_collection"]
            },
            "outputSpec": {
                "estimatedTime": "float",
                "confidence": "float",
                "productionPlan": "object",
                "bottlenecks": "array"
            }
        }
    }

    print(f"📋 QueryGoal ID: {querygoal['QueryGoal']['goalId']}")
    print("🚀 Executing pipeline...")

    try:
        result = await executor.execute_querygoal(querygoal)

        print("\n✅ Pipeline execution successful!")

        # Final outputs
        if "QueryGoal" in result and "outputs" in result["QueryGoal"]:
            outputs = result["QueryGoal"]["outputs"]
            print("\n📤 Final Outputs:")
            print(f"   estimatedTime: {outputs.get('estimatedTime')}")
            print(f"   confidence: {outputs.get('confidence')}")
            print(f"   bottlenecks: {outputs.get('bottlenecks', [])}")

    except Exception as e:
        print(f"\n❌ Pipeline execution failed!")
        print(f"   Error: {e}")

        # Try to find work directory
        work_dirs = list(Path("/tmp/querygoal_work").glob("goal3_test_*"))
        if work_dirs:
            latest_dir = max(work_dirs, key=lambda x: x.stat().st_mtime)
            print(f"\n📁 Work directory: {latest_dir}")

            # Check for log files
            log_files = list(latest_dir.glob("*.txt"))
            if log_files:
                print("\n📝 Container logs:")
                for log_file in log_files:
                    print(f"\n--- {log_file.name} ---")
                    with open(log_file, 'r') as f:
                        content = f.read()
                        print(content[:2000])  # Print first 2000 chars

    print("\n" + "="*60)
    print("🏁 Test completed")
    print("="*60)

if __name__ == "__main__":
    import os
    print("\n🔧 Environment Configuration:")
    print(f"   USE_STANDARD_SERVER: {os.getenv('USE_STANDARD_SERVER', 'not set')}")
    print(f"   AAS_SERVER_IP: {os.getenv('AAS_SERVER_IP', 'not set')}")
    print(f"   AAS_SERVER_PORT: {os.getenv('AAS_SERVER_PORT', 'not set')}")

    asyncio.run(test_goal3_runtime())