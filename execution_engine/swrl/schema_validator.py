"""
스키마 검증 모듈: QueryGoal 구조 유효성 검사
"""
import json
import re
from typing import Dict, Any, List


class ValidationError(ValueError):
    """스키마 검증 에러"""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error in '{field}': {message}")


def validate_query_goal_schema(query_goal: Dict[str, Any]) -> bool:
    """
    QueryGoal 객체의 스키마 유효성 검사

    Args:
        query_goal: QueryGoal 딕셔너리

    Returns:
        검증 성공시 True

    Raises:
        ValidationError: 스키마 검증 실패시
    """
    # 최상위 QueryGoal 존재 확인
    if "QueryGoal" not in query_goal:
        raise ValidationError("QueryGoal", "Root 'QueryGoal' field missing")

    goal_obj = query_goal["QueryGoal"]

    # 1. 필수 필드 존재 확인
    _validate_required_fields(goal_obj)

    # 2. 필드별 타입 검증
    _validate_field_types(goal_obj)

    # 3. 배열 내 객체 구조 검증
    _validate_parameters(goal_obj.get("parameters", []))
    _validate_output_spec(goal_obj.get("outputSpec", []))

    # 4. termination 필드 (Optional)
    if "termination" in goal_obj:
        _validate_termination(goal_obj["termination"])

    return True


def _validate_required_fields(goal_obj: Dict[str, Any]) -> None:
    """필수 필드 존재 확인"""
    required_fields = ["goalId", "goalType", "parameters", "outputSpec"]

    for field in required_fields:
        if field not in goal_obj:
            raise ValidationError(field, "Required field missing")


def _validate_field_types(goal_obj: Dict[str, Any]) -> None:
    """필드별 타입 검증"""
    # goalId, goalType: string
    for field in ["goalId", "goalType"]:
        if not isinstance(goal_obj.get(field), str):
            raise ValidationError(field, "Must be a string")
        if not goal_obj[field].strip():
            raise ValidationError(field, "Cannot be empty string")

    # parameters, outputSpec: array
    for field in ["parameters", "outputSpec"]:
        if not isinstance(goal_obj.get(field), list):
            raise ValidationError(field, "Must be an array")

    # termination: array (optional)
    if "termination" in goal_obj and not isinstance(goal_obj["termination"], list):
        raise ValidationError("termination", "Must be an array")


def _validate_parameters(parameters: List[Dict[str, Any]]) -> None:
    """parameters 배열 검증"""
    for i, param in enumerate(parameters):
        field_path = f"parameters[{i}]"

        if not isinstance(param, dict):
            raise ValidationError(field_path, "Must be an object")

        # 필수 필드: key, value
        for required_field in ["key", "value"]:
            if required_field not in param:
                raise ValidationError(f"{field_path}.{required_field}", "Required field missing")

            if not isinstance(param[required_field], str):
                raise ValidationError(f"{field_path}.{required_field}", "Must be a string")

        # key는 빈 문자열 불가
        if not param["key"].strip():
            raise ValidationError(f"{field_path}.key", "Cannot be empty string")


def _validate_output_spec(output_spec: List[Dict[str, Any]]) -> None:
    """outputSpec 배열 검증"""
    allowed_datatypes = {"datetime", "number", "boolean", "string", "array", "object"}

    for i, spec in enumerate(output_spec):
        field_path = f"outputSpec[{i}]"

        if not isinstance(spec, dict):
            raise ValidationError(field_path, "Must be an object")

        # 필수 필드: name, datatype
        for required_field in ["name", "datatype"]:
            if required_field not in spec:
                raise ValidationError(f"{field_path}.{required_field}", "Required field missing")

            if not isinstance(spec[required_field], str):
                raise ValidationError(f"{field_path}.{required_field}", "Must be a string")

        # name은 빈 문자열 불가
        if not spec["name"].strip():
            raise ValidationError(f"{field_path}.name", "Cannot be empty string")

        # datatype 유효성 검사
        if spec["datatype"] not in allowed_datatypes:
            raise ValidationError(
                f"{field_path}.datatype",
                f"Invalid datatype '{spec['datatype']}'. Allowed: {', '.join(sorted(allowed_datatypes))}"
            )


def _validate_termination(termination: List[Dict[str, Any]]) -> None:
    """termination 배열 검증 (Optional)"""
    allowed_keys = {"condition", "timeout"}
    allowed_conditions = {"on_job_completed", "on_deadline", "manual"}

    for i, term in enumerate(termination):
        field_path = f"termination[{i}]"

        if not isinstance(term, dict):
            raise ValidationError(field_path, "Must be an object")

        # 필수 필드: key, value
        for required_field in ["key", "value"]:
            if required_field not in term:
                raise ValidationError(f"{field_path}.{required_field}", "Required field missing")

            if not isinstance(term[required_field], str):
                raise ValidationError(f"{field_path}.{required_field}", "Must be a string")

        # key 유효성 검사
        if term["key"] not in allowed_keys:
            raise ValidationError(
                f"{field_path}.key",
                f"Invalid key '{term['key']}'. Allowed: {', '.join(sorted(allowed_keys))}"
            )

        # value 유효성 검사
        if term["key"] == "condition" and term["value"] not in allowed_conditions:
            raise ValidationError(
                f"{field_path}.value",
                f"Invalid condition '{term['value']}'. Allowed: {', '.join(sorted(allowed_conditions))}"
            )

        if term["key"] == "timeout" and not _is_valid_iso8601_duration(term["value"]):
            raise ValidationError(
                f"{field_path}.value",
                f"Invalid ISO 8601 duration pattern: '{term['value']}'. Expected format like 'PT4H', 'PT30M'"
            )


def _is_valid_iso8601_duration(duration: str) -> bool:
    """ISO 8601 Duration 패턴 매칭 검증"""
    # 기본 패턴: PT4H, PT30M, PT2H30M 등
    pattern = r'^PT(\d+H)?(\d+M)?(\d+S)?$'
    return bool(re.match(pattern, duration))


def main():
    """테스트를 위한 메인 함수"""
    try:
        with open("user_input.json", "r", encoding="utf-8") as f:
            test_input = json.load(f)

        print("=== 스키마 검증 테스트 ===")
        print("입력:")
        print(json.dumps(test_input, indent=2, ensure_ascii=False))

        result = validate_query_goal_schema(test_input)
        print(f"\n검증 결과: {'✅ 성공' if result else '❌ 실패'}")

    except FileNotFoundError:
        print("user_input.json 파일을 찾을 수 없습니다.")
    except ValidationError as e:
        print(f"❌ 검증 실패: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")


if __name__ == "__main__":
    main()