"""
전처리 모듈: QueryGoal의 특수 토큰 치환
"""
import json
from datetime import datetime
from typing import Dict, Any


class UnknownTokenError(ValueError):
    """알 수 없는 토큰 에러"""
    pass


def preprocess_query_goal(query_goal: Dict[str, Any]) -> Dict[str, Any]:
    """
    QueryGoal 객체의 특수 토큰을 실제 값으로 치환

    Args:
        query_goal: 원본 QueryGoal 딕셔너리

    Returns:
        전처리된 QueryGoal 딕셔너리

    Raises:
        UnknownTokenError: 알 수 없는 토큰 발견시
    """
    # Deep copy to avoid modifying original
    processed_goal = json.loads(json.dumps(query_goal))

    # QueryGoal 구조 확인
    if "QueryGoal" not in processed_goal:
        return processed_goal

    query_goal_obj = processed_goal["QueryGoal"]

    # parameters 배열 처리
    if "parameters" in query_goal_obj and isinstance(query_goal_obj["parameters"], list):
        for param in query_goal_obj["parameters"]:
            if isinstance(param, dict) and "value" in param:
                param["value"] = _process_token(param["value"])

    return processed_goal


def _process_token(value: str) -> str:
    """
    개별 토큰 처리

    Args:
        value: 처리할 값

    Returns:
        처리된 값

    Raises:
        UnknownTokenError: 알 수 없는 토큰 발견시
    """
    if not isinstance(value, str):
        return value

    if value == "@현재시간":
        # ISO 8601 UTC 형식으로 현재 시간 반환
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # @ 시작하는 다른 토큰들은 에러
    if value.startswith("@"):
        raise UnknownTokenError(f"Unknown token: {value}")

    # 일반 문자열은 그대로 반환
    return value


def main():
    """테스트를 위한 메인 함수"""
    # user_input.json 로드 및 테스트
    try:
        with open("user_input.json", "r", encoding="utf-8") as f:
            test_input = json.load(f)

        print("=== 전처리 테스트 ===")
        print("원본:")
        print(json.dumps(test_input, indent=2, ensure_ascii=False))

        processed = preprocess_query_goal(test_input)

        print("\n처리 후:")
        print(json.dumps(processed, indent=2, ensure_ascii=False))

    except FileNotFoundError:
        print("user_input.json 파일을 찾을 수 없습니다.")
    except UnknownTokenError as e:
        print(f"토큰 처리 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")


if __name__ == "__main__":
    main()