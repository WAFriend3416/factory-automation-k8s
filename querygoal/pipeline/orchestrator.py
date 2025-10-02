"""
Pipeline Orchestrator Module
QueryGoal 파이프라인 전체를 조율하고 Stage-Gated 성공 판정을 수행하는 모듈
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from .pattern_matcher import PatternMatcher
from .template_loader import TemplateLoader
from .parameter_filler import ParameterFiller
from .actionplan_resolver import ActionPlanResolver
from .model_selector import ModelSelector
from .validator import QueryGoalValidator


class PipelineOrchestrator:
    """QueryGoal 파이프라인 오케스트레이터"""

    def __init__(self):
        """파이프라인 컴포넌트 초기화"""
        self.pattern_matcher = PatternMatcher()
        self.template_loader = TemplateLoader()
        self.parameter_filler = ParameterFiller()
        self.actionplan_resolver = ActionPlanResolver()
        self.model_selector = ModelSelector()
        self.validator = QueryGoalValidator()

        # Stage-Gated 성공 판정 기준
        self.stage_criteria = {
            "aasQuery": {
                "required_for": ["goal1_query_cooling_failure", "goal4_track_product_location"],
                "success_criteria": lambda result: result.get("data") is not None
            },
            "dataFiltering": {
                "required_for": ["goal1_query_cooling_failure", "goal4_track_product_location"],
                "success_criteria": lambda result: result.get("filtered_count", 0) > 0
            },
            "swrlSelection": {
                "required_for": ["goal3_predict_production_time"],
                "success_criteria": lambda result: result.get("selectedModel") is not None
            },
            "yamlBinding": {
                "required_for": ["goal3_predict_production_time"],
                "success_criteria": lambda result: result.get("success_rate", 0) >= 1.0
            },
            "simulation": {
                "required_for": ["goal3_predict_production_time"],
                "success_criteria": lambda result: result.get("status") == "completed"
            }
        }

    def process_natural_language(self, input_text: str) -> Dict[str, Any]:
        """
        자연어 입력을 QueryGoal로 변환

        Args:
            input_text: 사용자 자연어 입력

        Returns:
            완성된 QueryGoal 딕셔너리
        """
        pipeline_log = {
            "input": input_text,
            "stages": [],
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Stage 1: 패턴 매칭
            analysis_result = self.pattern_matcher.analyze(input_text)
            goal_type = analysis_result["goalType"]
            metadata = analysis_result["metadata"]
            extracted_params = analysis_result["extractedParameters"]

            pipeline_log["stages"].append({
                "stage": "patternMatching",
                "status": "completed",
                "result": analysis_result
            })

            # Stage 2: 템플릿 로드 및 초기화
            querygoal = self.template_loader.create_querygoal(
                goal_type=goal_type,
                category=metadata.get("category", "unknown"),
                requires_model=metadata.get("requiresModel", False),
                pipeline_stages=metadata.get("pipelineStages", [])
            )

            pipeline_log["stages"].append({
                "stage": "templateLoading",
                "status": "completed",
                "result": {"goalId": querygoal["QueryGoal"]["goalId"]}
            })

            # Stage 3: 파라미터 채움
            querygoal = self.parameter_filler.process(
                querygoal=querygoal,
                extracted_params=extracted_params,
                goal_type=goal_type
            )

            pipeline_log["stages"].append({
                "stage": "parameterFilling",
                "status": "completed",
                "result": {"paramCount": len(querygoal["QueryGoal"]["parameters"])}
            })

            # Stage 4: 액션 플랜 결정
            querygoal = self.actionplan_resolver.resolve_action_plan(
                querygoal=querygoal,
                goal_type=goal_type
            )

            pipeline_log["stages"].append({
                "stage": "actionPlanResolution",
                "status": "completed",
                "result": {"actionCount": len(querygoal["QueryGoal"]["metadata"]["actionPlan"])}
            })

            # Stage 5: 모델 선택 (필요한 경우)
            querygoal = self.model_selector.bind_model_to_querygoal(
                querygoal=querygoal,
                goal_type=goal_type
            )

            model_status = "selected" if querygoal["QueryGoal"].get("selectedModel") else "not_required"
            pipeline_log["stages"].append({
                "stage": "modelSelection",
                "status": "completed",
                "result": {"modelStatus": model_status}
            })

            # Stage 6: 최종 검증
            validation_result = self.validator.validate(querygoal)

            pipeline_log["stages"].append({
                "stage": "validation",
                "status": "completed" if validation_result["isValid"] else "failed",
                "result": validation_result["summary"]
            })

            # 공통 문제 자동 수정
            if not validation_result["isValid"]:
                querygoal = self.validator.fix_common_issues(querygoal)
                # 재검증
                validation_result = self.validator.validate(querygoal)

            # 파이프라인 메타 정보 추가
            querygoal["pipelineLog"] = pipeline_log
            querygoal["validationResult"] = validation_result

            return querygoal

        except Exception as e:
            pipeline_log["stages"].append({
                "stage": "error",
                "status": "failed",
                "error": str(e)
            })
            raise

    def execute_querygoal(self, querygoal: Dict[str, Any]) -> Dict[str, Any]:
        """
        QueryGoal 실행 및 Stage-Gated 성공 판정

        Args:
            querygoal: QueryGoal 딕셔너리

        Returns:
            실행 결과 및 판정 정보
        """
        qg = querygoal["QueryGoal"]
        goal_type = qg["goalType"]
        pipeline_stages = qg["metadata"]["pipelineStages"]

        # 실행 결과 구조
        execution_result = {
            "goalId": qg["goalId"],
            "goalType": goal_type,
            "stages": {},
            "pipeline_meta": {
                "success": False,
                "completed_stages": [],
                "failed_stages": [],
                "success_rate": 0.0,
                "fail_reason": None
            }
        }

        # 각 스테이지 실행 및 판정
        for stage in pipeline_stages:
            stage_result = self._execute_stage(stage, qg)
            execution_result["stages"][stage] = stage_result

            # 성공 여부 판정
            if self._evaluate_stage_success(stage, stage_result, goal_type):
                execution_result["pipeline_meta"]["completed_stages"].append(stage)
            else:
                execution_result["pipeline_meta"]["failed_stages"].append(stage)
                execution_result["pipeline_meta"]["fail_reason"] = f"Stage '{stage}' failed"
                break

        # 전체 성공 판정
        required_stages = [s for s in pipeline_stages if self._is_stage_required(s, goal_type)]
        completed_required = all(s in execution_result["pipeline_meta"]["completed_stages"]
                                 for s in required_stages)

        execution_result["pipeline_meta"]["success"] = completed_required
        execution_result["pipeline_meta"]["success_rate"] = (
            len(execution_result["pipeline_meta"]["completed_stages"]) /
            len(pipeline_stages) if pipeline_stages else 0
        )

        return execution_result

    def _execute_stage(self, stage: str, querygoal_core: Dict[str, Any]) -> Dict[str, Any]:
        """
        개별 스테이지 실행 (시뮬레이션)

        Args:
            stage: 스테이지 이름
            querygoal_core: QueryGoal 코어 데이터

        Returns:
            스테이지 실행 결과
        """
        # 실제 구현에서는 각 스테이지별 실행 엔진과 연동
        # 여기서는 시뮬레이션 결과 반환

        stage_results = {
            "aasQuery": {
                "status": "completed",
                "data": {"machines": ["M001", "M002"], "records": 150},
                "timestamp": datetime.now().isoformat()
            },
            "dataFiltering": {
                "status": "completed",
                "filtered_count": 23,
                "criteria": "status=failure",
                "timestamp": datetime.now().isoformat()
            },
            "swrlSelection": {
                "status": "completed",
                "selectedModel": querygoal_core.get("selectedModel"),
                "timestamp": datetime.now().isoformat()
            },
            "yamlBinding": {
                "status": "completed",
                "success_rate": 1.0,
                "bound_sources": ["production_data.yaml", "machine_config.yaml"],
                "timestamp": datetime.now().isoformat()
            },
            "simulation": {
                "status": "completed",
                "result": {"estimatedTime": 45.5, "confidence": 0.92},
                "timestamp": datetime.now().isoformat()
            }
        }

        return stage_results.get(stage, {
            "status": "unknown",
            "error": f"Unknown stage: {stage}"
        })

    def _evaluate_stage_success(self, stage: str, result: Dict[str, Any], goal_type: str) -> bool:
        """
        스테이지 성공 여부 판정

        Args:
            stage: 스테이지 이름
            result: 스테이지 실행 결과
            goal_type: Goal 타입

        Returns:
            성공 여부
        """
        if stage not in self.stage_criteria:
            # 정의되지 않은 스테이지는 성공으로 간주
            return True

        criteria = self.stage_criteria[stage]

        # Goal 타입에 해당 스테이지가 필요한지 확인
        if goal_type not in criteria.get("required_for", []):
            return True

        # 성공 기준 평가
        success_fn = criteria.get("success_criteria")
        if success_fn:
            return success_fn(result)

        # 기본값: status가 completed면 성공
        return result.get("status") == "completed"

    def _is_stage_required(self, stage: str, goal_type: str) -> bool:
        """
        특정 Goal에 스테이지가 필수인지 확인

        Args:
            stage: 스테이지 이름
            goal_type: Goal 타입

        Returns:
            필수 여부
        """
        if stage not in self.stage_criteria:
            return False

        required_for = self.stage_criteria[stage].get("required_for", [])
        return goal_type in required_for

    def generate_execution_report(self, execution_result: Dict[str, Any]) -> str:
        """
        실행 결과 리포트 생성

        Args:
            execution_result: 실행 결과

        Returns:
            포맷된 리포트 문자열
        """
        meta = execution_result["pipeline_meta"]

        report = f"""
========================================
QueryGoal Execution Report
========================================
Goal ID: {execution_result['goalId']}
Goal Type: {execution_result['goalType']}
Overall Status: {'SUCCESS' if meta['success'] else 'FAILED'}
Success Rate: {meta['success_rate']:.1%}

Completed Stages: {', '.join(meta['completed_stages']) if meta['completed_stages'] else 'None'}
Failed Stages: {', '.join(meta['failed_stages']) if meta['failed_stages'] else 'None'}

Stage Details:
"""
        for stage, result in execution_result["stages"].items():
            status_emoji = "✅" if result.get("status") == "completed" else "❌"
            report += f"  {status_emoji} {stage}: {result.get('status', 'unknown')}\n"

        if meta.get("fail_reason"):
            report += f"\nFailure Reason: {meta['fail_reason']}\n"

        report += "========================================"

        return report