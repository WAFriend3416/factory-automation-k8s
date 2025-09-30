"""
Stage-Gate Validation System
각 단계의 성공/실패를 판정하는 검증 로직
"""
import logging
from typing import Dict, Any, Callable
from dataclasses import dataclass

logger = logging.getLogger("querygoal.stage_gate")


@dataclass
class StageGateResult:
    """Stage-Gate 검증 결과"""
    stage_name: str
    passed: bool
    reason: str
    validation_details: Dict[str, Any]


class StageGateValidator:
    """Stage-Gate 검증기"""

    def validate_stage(self,
                      stage_name: str,
                      stage_result: Dict[str, Any],
                      stage_criteria: Dict[str, Dict]) -> StageGateResult:
        """
        Stage 결과를 기준에 따라 검증
        """

        if stage_name not in stage_criteria:
            logger.warning(f"No criteria defined for stage: {stage_name}")
            return StageGateResult(
                stage_name=stage_name,
                passed=True,  # 기준이 없으면 통과로 처리
                reason="No validation criteria defined",
                validation_details={}
            )

        criteria = stage_criteria[stage_name]
        success_criteria = criteria["success_criteria"]

        try:
            # 성공 조건 검증
            if callable(success_criteria):
                passed = success_criteria(stage_result)
            else:
                # 간단한 키-값 검증
                passed = stage_result.get(success_criteria, False)

            validation_details = {
                "stage_result_keys": list(stage_result.keys()),
                "validation_applied": str(success_criteria),
                "result_sample": {k: str(v)[:100] for k, v in list(stage_result.items())[:3]}
            }

            if passed:
                return StageGateResult(
                    stage_name=stage_name,
                    passed=True,
                    reason="Stage criteria satisfied",
                    validation_details=validation_details
                )
            else:
                return StageGateResult(
                    stage_name=stage_name,
                    passed=False,
                    reason=f"Stage criteria not met: {success_criteria}",
                    validation_details=validation_details
                )

        except Exception as e:
            logger.error(f"Stage-Gate validation error for {stage_name}: {e}")
            return StageGateResult(
                stage_name=stage_name,
                passed=False,
                reason=f"Validation error: {e}",
                validation_details={"error": str(e)}
            )