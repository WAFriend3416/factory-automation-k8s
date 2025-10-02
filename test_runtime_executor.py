"""
QueryGoal Runtime Executor 기본 테스트
"""
import asyncio
import os
from pathlib import Path

# 환경 변수 설정
os.environ['USE_STANDARD_SERVER'] = 'true'
os.environ['AAS_SERVER_IP'] = '127.0.0.1'
os.environ['AAS_SERVER_PORT'] = '5001'


async def test_runtime_executor():
    """Runtime Executor 기본 동작 테스트"""

    print("\n" + "=" * 60)
    print("🧪 QueryGoal Runtime Executor Test")
    print("=" * 60)

    try:
        # 1. QueryGoal 생성 (파이프라인 사용)
        from querygoal.pipeline.orchestrator import PipelineOrchestrator

        print("\n📝 Step 1: Creating QueryGoal via Pipeline...")
        orchestrator = PipelineOrchestrator()
        querygoal = orchestrator.process_natural_language(
            "Predict production time for product TEST_RUNTIME quantity 30"
        )

        print(f"✅ QueryGoal created: {querygoal['QueryGoal']['goalId']}")
        print(f"   Goal Type: {querygoal['QueryGoal']['goalType']}")
        print(f"   Pipeline Stages: {querygoal['QueryGoal']['metadata']['pipelineStages']}")

        # 2. Runtime Executor 실행
        from querygoal.runtime.executor import QueryGoalExecutor

        print("\n🚀 Step 2: Executing QueryGoal with Runtime Executor...")
        executor = QueryGoalExecutor()
        result = await executor.execute_querygoal(querygoal)

        # 3. 결과 확인
        print("\n📊 Step 3: Execution Results:")
        print(f"   Status: {result['executionLog']['status']}")
        print(f"   Goal ID: {result['executionLog']['goalId']}")
        print(f"   Stages Completed: {len(result['executionLog']['stages'])}")

        for stage_log in result['executionLog']['stages']:
            stage_name = stage_log['stage']
            stage_status = stage_log['status']
            print(f"   - {stage_name}: {stage_status}")

        # 4. 작업 디렉터리 확인
        work_dir = Path(result['workDirectory'])
        print(f"\n📁 Work Directory: {work_dir}")
        if work_dir.exists():
            print("   Files created:")
            for file in work_dir.glob("**/*"):
                if file.is_file():
                    print(f"   - {file.relative_to(work_dir)}")

        # 5. Outputs 확인
        if "outputs" in result['QueryGoal']:
            print("\n📤 QueryGoal Outputs:")
            outputs = result['QueryGoal']['outputs']
            for key, value in outputs.items():
                if isinstance(value, dict):
                    print(f"   - {key}: {type(value).__name__} with {len(value)} items")
                else:
                    print(f"   - {key}: {value}")

        print("\n" + "=" * 60)
        print("✅ Runtime Executor Test PASSED")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_runtime_executor())
    exit(0 if success else 1)