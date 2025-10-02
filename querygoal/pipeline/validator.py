"""
Validator Module
QueryGoal 최종 검증을 수행하는 모듈
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime
from enum import Enum


class ParameterType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    OBJECT = "object"
    ARRAY = "array"


class QueryGoalParameter(BaseModel):
    """QueryGoal 파라미터 스키마"""
    key: str
    value: Any
    type: Optional[ParameterType] = ParameterType.STRING
    required: Optional[bool] = False


class OutputSpecItem(BaseModel):
    """출력 스펙 아이템 스키마"""
    name: str
    datatype: str


class QueryGoalMetadata(BaseModel):
    """QueryGoal 메타데이터 스키마"""
    category: str
    requiresModel: bool = False
    actionPlan: List[Dict[str, Any]] = []
    selectedModel: Optional[Dict[str, Any]] = None
    pipelineStages: List[str] = []
    notes: Optional[str] = ""


class QueryGoalCore(BaseModel):
    """QueryGoal 코어 스키마"""
    goalId: str
    goalType: str
    parameters: List[QueryGoalParameter] = []
    outputSpec: List[OutputSpecItem] = []
    metadata: QueryGoalMetadata
    selectedModelRef: Optional[str] = None
    selectedModel: Optional[Dict[str, Any]] = None
    selectionProvenance: Optional[Dict[str, Any]] = None


class QueryGoalSchema(BaseModel):
    """전체 QueryGoal 스키마"""
    templateId: Optional[str] = "base_querygoal"
    QueryGoal: QueryGoalCore


class QueryGoalValidator:
    """QueryGoal 검증기"""

    def __init__(self):
        """검증 규칙 초기화"""
        self.validation_rules = {
            "goal1_query_cooling_failure": {
                "required_params": ["machineId"],
                "required_stages": ["aasQuery", "dataFiltering"],
                "requires_model": False
            },
            "goal3_predict_production_time": {
                "required_params": ["productType", "quantity"],
                "required_stages": ["swrlSelection", "yamlBinding", "simulation"],
                "requires_model": True
            },
            "goal4_track_product_location": {
                "required_params": ["productId"],
                "required_stages": ["aasQuery", "dataFiltering"],
                "requires_model": False
            }
        }

    def validate_schema(self, querygoal: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Pydantic 스키마 검증

        Args:
            querygoal: QueryGoal 딕셔너리

        Returns:
            (검증 성공 여부, 오류 메시지 리스트)
        """
        errors = []

        try:
            # Pydantic 모델로 검증
            QueryGoalSchema(**querygoal)
            return True, []
        except ValidationError as e:
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                errors.append(f"Schema error at {field_path}: {error['msg']}")
            return False, errors

    def validate_business_rules(self, querygoal: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        비즈니스 규칙 검증

        Args:
            querygoal: QueryGoal 딕셔너리

        Returns:
            (검증 성공 여부, 오류 메시지 리스트)
        """
        errors = []
        qg = querygoal.get("QueryGoal", {})
        goal_type = qg.get("goalType", "")

        # Goal 타입별 규칙 확인
        rules = self.validation_rules.get(goal_type)
        if not rules:
            errors.append(f"Unknown goal type: {goal_type}")
            return False, errors

        # 필수 파라미터 검증
        param_keys = {p.get("key") for p in qg.get("parameters", [])}
        missing_params = [p for p in rules["required_params"] if p not in param_keys]
        if missing_params:
            errors.append(f"Missing required parameters: {missing_params}")

        # 파이프라인 스테이지 검증
        pipeline_stages = qg.get("metadata", {}).get("pipelineStages", [])
        missing_stages = [s for s in rules["required_stages"] if s not in pipeline_stages]
        if missing_stages:
            errors.append(f"Missing required pipeline stages: {missing_stages}")

        # 모델 요구사항 검증
        requires_model = qg.get("metadata", {}).get("requiresModel", False)
        if rules["requires_model"] != requires_model:
            errors.append(f"Model requirement mismatch: expected {rules['requires_model']}, got {requires_model}")

        if requires_model and not qg.get("selectedModel"):
            errors.append("Model required but no model selected")

        return len(errors) == 0, errors

    def validate_consistency(self, querygoal: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        일관성 검증

        Args:
            querygoal: QueryGoal 딕셔너리

        Returns:
            (검증 성공 여부, 오류 메시지 리스트)
        """
        errors = []
        qg = querygoal.get("QueryGoal", {})

        # 모델 참조 일관성
        model_ref = qg.get("selectedModelRef")
        selected_model = qg.get("selectedModel")

        if model_ref and selected_model:
            model_id = selected_model.get("modelId")
            if model_ref != model_id:
                errors.append(f"Model reference inconsistency: ref={model_ref}, model.modelId={model_id}")

        # 액션 플랜과 파이프라인 스테이지 일관성
        action_plan = qg.get("metadata", {}).get("actionPlan", [])
        pipeline_stages = qg.get("metadata", {}).get("pipelineStages", [])

        if "swrlSelection" in pipeline_stages:
            has_model_action = any("Model" in a.get("actionType", "") for a in action_plan)
            if not has_model_action:
                errors.append("Pipeline includes swrlSelection but no model selection action in plan")

        if "simulation" in pipeline_stages:
            has_sim_action = any("Simulator" in a.get("actionType", "") for a in action_plan)
            if not has_sim_action:
                errors.append("Pipeline includes simulation but no simulator action in plan")

        return len(errors) == 0, errors

    def validate_completeness(self, querygoal: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        완전성 검증

        Args:
            querygoal: QueryGoal 딕셔너리

        Returns:
            (검증 성공 여부, 경고 메시지 리스트)
        """
        warnings = []
        qg = querygoal.get("QueryGoal", {})

        # Goal ID 확인
        if not qg.get("goalId") or qg.get("goalId") == "{auto-generated}":
            warnings.append("Goal ID not properly generated")

        # Goal Type 확인
        if not qg.get("goalType") or qg.get("goalType") == "{dynamic}":
            warnings.append("Goal type not properly set")

        # 빈 파라미터 값 확인
        for param in qg.get("parameters", []):
            if param.get("required") and not param.get("value"):
                warnings.append(f"Required parameter '{param.get('key')}' has empty value")

        # 출력 스펙 확인
        if not qg.get("outputSpec"):
            warnings.append("No output specification defined")

        # 액션 플랜 확인
        if not qg.get("metadata", {}).get("actionPlan"):
            warnings.append("No action plan defined")

        return len(warnings) == 0, warnings

    def validate(self, querygoal: Dict[str, Any]) -> Dict[str, Any]:
        """
        전체 검증 수행

        Args:
            querygoal: QueryGoal 딕셔너리

        Returns:
            검증 결과 딕셔너리
        """
        validation_result = {
            "isValid": True,
            "errors": [],
            "warnings": [],
            "validatedAt": datetime.now().isoformat()
        }

        # 스키마 검증
        schema_valid, schema_errors = self.validate_schema(querygoal)
        if not schema_valid:
            validation_result["isValid"] = False
            validation_result["errors"].extend([f"[Schema] {e}" for e in schema_errors])

        # 비즈니스 규칙 검증
        business_valid, business_errors = self.validate_business_rules(querygoal)
        if not business_valid:
            validation_result["isValid"] = False
            validation_result["errors"].extend([f"[Business] {e}" for e in business_errors])

        # 일관성 검증
        consistency_valid, consistency_errors = self.validate_consistency(querygoal)
        if not consistency_valid:
            validation_result["isValid"] = False
            validation_result["errors"].extend([f"[Consistency] {e}" for e in consistency_errors])

        # 완전성 검증 (경고 수준)
        complete_valid, completeness_warnings = self.validate_completeness(querygoal)
        if not complete_valid:
            validation_result["warnings"].extend([f"[Completeness] {w}" for w in completeness_warnings])

        # 검증 요약
        validation_result["summary"] = {
            "errorCount": len(validation_result["errors"]),
            "warningCount": len(validation_result["warnings"]),
            "schemaValid": schema_valid,
            "businessRulesValid": business_valid,
            "consistencyValid": consistency_valid,
            "completenessValid": complete_valid
        }

        return validation_result

    def fix_common_issues(self, querygoal: Dict[str, Any]) -> Dict[str, Any]:
        """
        일반적인 문제 자동 수정

        Args:
            querygoal: QueryGoal 딕셔너리

        Returns:
            수정된 QueryGoal
        """
        qg = querygoal.get("QueryGoal", {})

        # Goal ID 자동 생성
        if not qg.get("goalId") or qg.get("goalId") == "{auto-generated}":
            from ..pipeline.template_loader import TemplateLoader
            loader = TemplateLoader()
            qg["goalId"] = loader.generate_goal_id()

        # Goal Type 정리
        if qg.get("goalType") == "{dynamic}":
            qg["goalType"] = "unknown"

        # 카테고리 정리
        metadata = qg.get("metadata", {})
        if metadata.get("category") == "{dynamic}":
            metadata["category"] = "unknown"

        # 빈 리스트 초기화
        if not qg.get("parameters"):
            qg["parameters"] = []
        if not qg.get("outputSpec"):
            qg["outputSpec"] = []
        if not metadata.get("actionPlan"):
            metadata["actionPlan"] = []
        if not metadata.get("pipelineStages"):
            metadata["pipelineStages"] = []

        return querygoal
