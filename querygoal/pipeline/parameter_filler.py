"""
Parameter Filler Module
QueryGoal의 parameters와 outputSpec을 채우는 모듈
"""
from typing import Dict, Any, List, Optional


class ParameterFiller:
    """QueryGoal 파라미터 및 출력 스펙 채움"""

    def __init__(self):
        """파라미터 규칙 정의"""
        # Goal별 필수/선택 파라미터 정의
        self.parameter_rules = {
            "goal1_query_cooling_failure": {
                "required": ["machineId"],
                "optional": ["timestamp", "severity", "diagnosticMode"],
                "outputSpec": [
                    {"name": "failureType", "datatype": "string"},
                    {"name": "errorCode", "datatype": "string"},
                    {"name": "machineStatus", "datatype": "object"},
                    {"name": "recommendations", "datatype": "array"}
                ]
            },
            "goal3_predict_production_time": {
                "required": ["productType", "quantity"],
                "optional": ["machineId", "priority", "optimizationMode"],
                "outputSpec": [
                    {"name": "estimatedTime", "datatype": "number"},
                    {"name": "confidence", "datatype": "number"},
                    {"name": "productionPlan", "datatype": "object"},
                    {"name": "bottlenecks", "datatype": "array"}
                ]
            },
            "goal4_track_product_location": {
                "required": ["productId"],
                "optional": ["timestamp", "locationType", "includeHistory"],
                "outputSpec": [
                    {"name": "currentLocation", "datatype": "string"},
                    {"name": "status", "datatype": "string"},
                    {"name": "lastUpdate", "datatype": "string"},
                    {"name": "movementHistory", "datatype": "array"}
                ]
            }
        }

        # 파라미터 타입 추론 규칙
        self.type_inference_rules = {
            "id": "string",
            "Id": "string",
            "name": "string",
            "type": "string",
            "quantity": "number",
            "amount": "number",
            "count": "number",
            "timestamp": "datetime",
            "date": "datetime",
            "time": "datetime",
            "flag": "boolean",
            "enabled": "boolean",
            "active": "boolean"
        }

    def fill_parameters(self,
                        querygoal: Dict[str, Any],
                        extracted_params: Dict[str, Any],
                        goal_type: str) -> Dict[str, Any]:
        """
        QueryGoal에 파라미터 채우기

        Args:
            querygoal: QueryGoal 딕셔너리
            extracted_params: 추출된 파라미터
            goal_type: Goal 타입

        Returns:
            업데이트된 QueryGoal
        """
        qg = querygoal["QueryGoal"]

        # Goal 타입에 해당하는 규칙 가져오기
        rules = self.parameter_rules.get(goal_type, {})

        # 파라미터 리스트 생성
        parameters = []

        # 필수 파라미터 처리
        for param_name in rules.get("required", []):
            param_value = extracted_params.get(param_name)
            param_type = self._infer_type(param_name, param_value)

            parameters.append({
                "key": param_name,
                "value": param_value if param_value is not None else "",
                "type": param_type,
                "required": True
            })

        # 선택 파라미터 처리
        for param_name in rules.get("optional", []):
            if param_name in extracted_params:
                param_value = extracted_params[param_name]
                param_type = self._infer_type(param_name, param_value)

                parameters.append({
                    "key": param_name,
                    "value": param_value,
                    "type": param_type,
                    "required": False
                })

        # 추가 파라미터 처리 (규칙에 없지만 추출된 것들)
        for param_name, param_value in extracted_params.items():
            if param_name not in [p["key"] for p in parameters]:
                param_type = self._infer_type(param_name, param_value)

                parameters.append({
                    "key": param_name,
                    "value": param_value,
                    "type": param_type,
                    "required": False
                })

        # QueryGoal에 파라미터 설정
        qg["parameters"] = parameters

        return querygoal

    def fill_output_spec(self,
                         querygoal: Dict[str, Any],
                         goal_type: str) -> Dict[str, Any]:
        """
        QueryGoal에 출력 스펙 채우기

        Args:
            querygoal: QueryGoal 딕셔너리
            goal_type: Goal 타입

        Returns:
            업데이트된 QueryGoal
        """
        qg = querygoal["QueryGoal"]

        # Goal 타입에 해당하는 출력 스펙 가져오기
        rules = self.parameter_rules.get(goal_type, {})
        output_spec = rules.get("outputSpec", [])

        # QueryGoal에 출력 스펙 설정
        qg["outputSpec"] = output_spec

        return querygoal

    def _infer_type(self, param_name: str, param_value: Any) -> str:
        """
        파라미터 타입 추론

        Args:
            param_name: 파라미터 이름
            param_value: 파라미터 값

        Returns:
            추론된 타입 문자열
        """
        # 값 기반 타입 추론
        if param_value is not None:
            if isinstance(param_value, bool):
                return "boolean"
            elif isinstance(param_value, int):
                return "number"
            elif isinstance(param_value, float):
                return "number"
            elif isinstance(param_value, list):
                return "array"
            elif isinstance(param_value, dict):
                return "object"

        # 이름 기반 타입 추론
        param_lower = param_name.lower()
        for key_pattern, type_name in self.type_inference_rules.items():
            if key_pattern.lower() in param_lower:
                return type_name

        # 기본값
        return "string"

    def validate_required_parameters(self,
                                      querygoal: Dict[str, Any],
                                      goal_type: str) -> tuple[bool, List[str]]:
        """
        필수 파라미터 검증

        Args:
            querygoal: QueryGoal 딕셔너리
            goal_type: Goal 타입

        Returns:
            (검증 성공 여부, 누락된 파라미터 리스트)
        """
        qg = querygoal["QueryGoal"]
        rules = self.parameter_rules.get(goal_type, {})
        required_params = rules.get("required", [])

        # 현재 파라미터에서 키 추출
        current_params = {p["key"] for p in qg.get("parameters", [])}

        # 누락된 필수 파라미터 찾기
        missing = [p for p in required_params if p not in current_params]

        # 빈 값인 필수 파라미터 찾기
        empty_required = []
        for param in qg.get("parameters", []):
            if param.get("required", False) and not param.get("value"):
                empty_required.append(param["key"])

        missing.extend(empty_required)

        return len(missing) == 0, missing

    def process(self,
                querygoal: Dict[str, Any],
                extracted_params: Dict[str, Any],
                goal_type: str) -> Dict[str, Any]:
        """
        파라미터와 출력 스펙을 모두 처리

        Args:
            querygoal: QueryGoal 딕셔너리
            extracted_params: 추출된 파라미터
            goal_type: Goal 타입

        Returns:
            완성된 QueryGoal
        """
        # 파라미터 채우기
        querygoal = self.fill_parameters(querygoal, extracted_params, goal_type)

        # 출력 스펙 채우기
        querygoal = self.fill_output_spec(querygoal, goal_type)

        # 검증
        is_valid, missing_params = self.validate_required_parameters(querygoal, goal_type)

        if not is_valid:
            # 메타데이터에 경고 추가
            qg = querygoal["QueryGoal"]
            qg["metadata"]["notes"] += f" | Warning: Missing required parameters: {missing_params}"

        return querygoal
