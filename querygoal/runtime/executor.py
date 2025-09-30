"""
QueryGoal Runtime Executor
완성된 QueryGoal을 실제 실행하는 오케스트레이터
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

from .handlers.base_handler import BaseHandler
from .handlers.swrl_selection_handler import SwrlSelectionHandler
from .handlers.yaml_binding_handler import YamlBindingHandler
from .handlers.simulation_handler import SimulationHandler
from .utils.work_directory import WorkDirectoryManager
from .utils.stage_gate import StageGateValidator
from .exceptions import (
    RuntimeExecutionError,
    StageExecutionError,
    StageGateFailureError
)

logger = logging.getLogger("querygoal.runtime")


@dataclass
class ExecutionContext:
    """실행 컨텍스트 정보"""
    goal_id: str
    goal_type: str
    work_directory: Path
    start_time: datetime
    pipeline_stages: List[str]
    current_stage: Optional[str] = None
    stage_results: Dict[str, Any] = field(default_factory=dict)


class QueryGoalExecutor:
    """
    QueryGoal Runtime Executor
    완성된 QueryGoal을 받아 실제 실행을 수행
    """

    def __init__(self):
        self.work_dir_manager = WorkDirectoryManager()
        self.stage_gate_validator = StageGateValidator()

        # Stage 핸들러 매핑
        self.stage_handlers = {
            "swrlSelection": SwrlSelectionHandler(),
            "yamlBinding": YamlBindingHandler(),
            "simulation": SimulationHandler()
        }

        # Stage-Gate 성공 기준
        self.stage_criteria = {
            "swrlSelection": {
                "success_criteria": lambda result: result.get("selectedModel") is not None
            },
            "yamlBinding": {
                # Required-flag filtering: 필수(required=true) 소스만 검증
                # success_rate는 필수 소스의 성공률을 의미
                # 선택적(required=false) 소스의 실패는 무시
                #
                # 검증 순서:
                # 1. status가 "success"인지 확인 (hard failure 차단)
                # 2. required_sources_count == 0: 모든 소스가 선택적 → PASS
                # 3. required_sources_count > 0: 필수 소스의 100% 성공 요구
                "success_criteria": lambda result: (
                    result.get("status") == "success" and  # 먼저 에러 상태 차단
                    (result.get("required_sources_count", 0) == 0 or  # 필수 소스 없으면 통과
                     result.get("required_success_rate", 0) >= 1.0)    # 필수 소스 있으면 100% 성공
                )
            },
            "simulation": {
                "success_criteria": lambda result: result.get("status") == "completed"
            }
        }

    async def execute_querygoal(self, querygoal: Dict[str, Any]) -> Dict[str, Any]:
        """
        QueryGoal 실행 메인 엔트리포인트
        """
        start_time = datetime.utcnow()
        qg = querygoal["QueryGoal"]

        try:
            # 실행 컨텍스트 초기화
            context = ExecutionContext(
                goal_id=qg["goalId"],
                goal_type=qg["goalType"],
                work_directory=self.work_dir_manager.create_work_directory(qg["goalId"]),
                start_time=start_time,
                pipeline_stages=qg["metadata"]["pipelineStages"]
            )

            logger.info(f"🚀 Starting QueryGoal execution for {context.goal_id}")
            logger.info(f"📋 Pipeline stages: {context.pipeline_stages}")

            # Stage별 순차 실행
            execution_log = {
                "goalId": context.goal_id,
                "startTime": start_time.isoformat(),
                "stages": [],
                "status": "in_progress"
            }

            for stage_name in context.pipeline_stages:
                context.current_stage = stage_name

                try:
                    # Stage 실행
                    stage_result = await self._execute_stage(
                        stage_name, querygoal, context
                    )

                    # Stage-Gate 검증
                    gate_result = self.stage_gate_validator.validate_stage(
                        stage_name, stage_result, self.stage_criteria
                    )

                    if not gate_result.passed:
                        raise StageGateFailureError(
                            f"Stage-Gate failed for {stage_name}: {gate_result.reason}"
                        )

                    # 성공 시 결과 기록
                    context.stage_results[stage_name] = stage_result

                    execution_log["stages"].append({
                        "stage": stage_name,
                        "status": "completed",
                        "result": stage_result,
                        "gate_check": {
                            "passed": gate_result.passed,
                            "reason": gate_result.reason
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    })

                    logger.info(f"✅ Stage '{stage_name}' completed successfully")

                except Exception as e:
                    # Stage 실패 처리
                    error_info = {
                        "stage": stage_name,
                        "status": "failed",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }

                    execution_log["stages"].append(error_info)
                    execution_log["status"] = "failed"
                    execution_log["failedStage"] = stage_name
                    execution_log["endTime"] = datetime.utcnow().isoformat()

                    logger.error(f"❌ Stage '{stage_name}' failed: {e}")

                    raise RuntimeExecutionError(
                        f"QueryGoal execution failed at stage '{stage_name}': {e}"
                    ) from e

            # 전체 실행 성공
            execution_log["status"] = "completed"
            execution_log["endTime"] = datetime.utcnow().isoformat()

            # 최종 결과 구성
            final_result = {
                "QueryGoal": qg,
                "executionLog": execution_log,
                "results": context.stage_results,
                "workDirectory": str(context.work_directory)
            }

            logger.info(f"🎉 QueryGoal {context.goal_id} executed successfully")
            return final_result

        except Exception as e:
            logger.error(f"💥 QueryGoal execution failed: {e}")

            # 실패 시 정리 작업
            if 'context' in locals():
                await self._cleanup_on_failure(context, str(e))

            raise RuntimeExecutionError(f"QueryGoal execution failed: {e}") from e

        finally:
            # 리소스 정리 (성공/실패 무관)
            if 'context' in locals():
                await self._cleanup_resources(context)

    async def _execute_stage(self,
                           stage_name: str,
                           querygoal: Dict[str, Any],
                           context: ExecutionContext) -> Dict[str, Any]:
        """개별 Stage 실행"""

        if stage_name not in self.stage_handlers:
            raise StageExecutionError(f"Unknown stage: {stage_name}")

        handler = self.stage_handlers[stage_name]

        logger.info(f"📍 Executing stage: {stage_name}")
        stage_start_time = datetime.utcnow()

        try:
            # Stage 실행
            result = await handler.execute(querygoal, context)

            execution_time = (datetime.utcnow() - stage_start_time).total_seconds()

            # 실행 메타데이터 추가
            result.update({
                "stage": stage_name,
                "executionTime": execution_time,
                "timestamp": datetime.utcnow().isoformat()
            })

            return result

        except Exception as e:
            execution_time = (datetime.utcnow() - stage_start_time).total_seconds()

            logger.error(f"Stage {stage_name} execution failed after {execution_time:.2f}s: {e}")

            raise StageExecutionError(
                f"Stage '{stage_name}' execution failed: {e}"
            ) from e

    async def _cleanup_on_failure(self, context: ExecutionContext, error_message: str):
        """실행 실패 시 정리 작업"""
        try:
            # 실패 로그 저장
            failure_log_path = context.work_directory / "failure.log"
            with open(failure_log_path, 'w') as f:
                f.write(f"Execution failed at: {datetime.utcnow().isoformat()}\n")
                f.write(f"Failed stage: {context.current_stage}\n")
                f.write(f"Error: {error_message}\n")
                f.write(f"Stage results: {context.stage_results}\n")

            logger.info(f"💾 Failure log saved to {failure_log_path}")

        except Exception as cleanup_error:
            logger.error(f"Failed to save failure log: {cleanup_error}")

    async def _cleanup_resources(self, context: ExecutionContext):
        """리소스 정리"""
        try:
            # 필요시 작업 디렉터리 정리 (설정에 따라)
            # self.work_dir_manager.cleanup_work_directory(context.work_directory)

            logger.debug(f"🧹 Resources cleaned up for {context.goal_id}")

        except Exception as cleanup_error:
            logger.warning(f"Resource cleanup warning: {cleanup_error}")


def create_querygoal_executor() -> QueryGoalExecutor:
    """QueryGoalExecutor 팩토리 함수"""
    return QueryGoalExecutor()