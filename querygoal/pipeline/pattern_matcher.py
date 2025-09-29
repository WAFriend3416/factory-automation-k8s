"""
Pattern Matcher Module
자연어 입력에서 Goal 타입과 카테고리를 결정하는 모듈
"""
import re
from typing import Dict, Any, Tuple, Optional
from enum import Enum


class GoalType(Enum):
    GOAL1 = "goal1_query_cooling_failure"
    GOAL3 = "goal3_predict_production_time"
    GOAL4 = "goal4_track_product_location"
    UNKNOWN = "unknown"


class PatternMatcher:
    """자연어 입력을 분석하여 Goal 타입과 메타데이터를 결정"""

    def __init__(self):
        self.patterns = {
            GoalType.GOAL1: [
                r"cooling.*failure",
                r"냉각.*실패",
                r"machine.*problem",
                r"equipment.*issue",
                r"cooling.*issue",
                r"temperature.*problem"
            ],
            GoalType.GOAL3: [
                r"predict.*time",
                r"production.*time",
                r"estimate.*duration",
                r"how long.*produce",
                r"제조.*시간",
                r"생산.*예측",
                r"시간.*예측"
            ],
            GoalType.GOAL4: [
                r"track.*product",
                r"product.*location",
                r"where.*product",
                r"find.*product",
                r"locate.*item",
                r"제품.*위치",
                r"추적"
            ]
        }

        self.goal_metadata = {
            GoalType.GOAL1: {
                "category": "diagnostics",
                "requiresModel": False,
                "pipelineStages": ["aasQuery", "dataFiltering"]
            },
            GoalType.GOAL3: {
                "category": "prediction",
                "requiresModel": True,
                "pipelineStages": ["swrlSelection", "yamlBinding", "simulation"]
            },
            GoalType.GOAL4: {
                "category": "tracking",
                "requiresModel": False,
                "pipelineStages": ["aasQuery", "dataFiltering"]
            }
        }

    def match_goal_type(self, input_text: str) -> Tuple[GoalType, Dict[str, Any]]:
        """
        입력 텍스트에서 Goal 타입을 결정

        Args:
            input_text: 사용자 입력 자연어

        Returns:
            (GoalType, metadata dict)
        """
        input_lower = input_text.lower()

        # 각 Goal 타입의 패턴을 확인
        for goal_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, input_lower):
                    metadata = self.goal_metadata.get(goal_type, {})
                    return goal_type, metadata

        # 매칭되는 패턴이 없으면 UNKNOWN 반환
        return GoalType.UNKNOWN, {
            "category": "unknown",
            "requiresModel": False,
            "pipelineStages": ["aasQuery"]
        }

    def extract_parameters(self, input_text: str, goal_type: GoalType) -> Dict[str, Any]:
        """
        Goal 타입에 따라 입력에서 파라미터 추출

        Args:
            input_text: 사용자 입력
            goal_type: 결정된 Goal 타입

        Returns:
            추출된 파라미터 딕셔너리
        """
        parameters = {}

        if goal_type == GoalType.GOAL1:
            # Machine ID 추출
            machine_match = re.search(r"machine[_\s]*(?:id[_\s]*)?[:\s]*([A-Za-z0-9_-]+)", input_text, re.I)
            if machine_match:
                parameters["machineId"] = machine_match.group(1)

            # Timestamp 추출
            timestamp_match = re.search(r"time[:\s]*(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})", input_text, re.I)
            if timestamp_match:
                parameters["timestamp"] = timestamp_match.group(1)

        elif goal_type == GoalType.GOAL3:
            # Product type 추출
            product_match = re.search(r"product[_\s]*(?:type[_\s]*)?[:\s]*([A-Za-z0-9_-]+)", input_text, re.I)
            if product_match:
                parameters["productType"] = product_match.group(1)

            # Quantity 추출
            qty_match = re.search(r"(?:quantity|qty|amount)[:\s]*(\d+)", input_text, re.I)
            if qty_match:
                parameters["quantity"] = int(qty_match.group(1))

        elif goal_type == GoalType.GOAL4:
            # Product ID 추출
            product_match = re.search(r"product[_\s]*(?:id[_\s]*)?[:\s]*([A-Za-z0-9_-]+)", input_text, re.I)
            if product_match:
                parameters["productId"] = product_match.group(1)

            # Location type 추출
            location_match = re.search(r"location[_\s]*(?:type[_\s]*)?[:\s]*([A-Za-z0-9_-]+)", input_text, re.I)
            if location_match:
                parameters["locationType"] = location_match.group(1)

        return parameters

    def analyze(self, input_text: str) -> Dict[str, Any]:
        """
        입력 텍스트를 완전히 분석

        Args:
            input_text: 사용자 입력

        Returns:
            분석 결과 딕셔너리
        """
        goal_type, metadata = self.match_goal_type(input_text)
        parameters = self.extract_parameters(input_text, goal_type)

        return {
            "goalType": goal_type.value,
            "metadata": metadata,
            "extractedParameters": parameters,
            "originalInput": input_text
        }