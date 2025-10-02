"""
Base Handler for Runtime Stages
모든 Stage 핸들러의 기본 클래스
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ..executor import ExecutionContext

logger = logging.getLogger("querygoal.handlers")


class BaseHandler(ABC):
    """Stage 핸들러 기본 클래스"""

    def __init__(self):
        self.handler_name = self.__class__.__name__
        self.logger = logging.getLogger(f"querygoal.handlers.{self.handler_name}")

    @abstractmethod
    async def execute(self,
                     querygoal: Dict[str, Any],
                     context: 'ExecutionContext') -> Dict[str, Any]:
        """
        Stage 실행 로직 (하위 클래스에서 구현)

        Args:
            querygoal: 완성된 QueryGoal 객체
            context: 실행 컨텍스트

        Returns:
            Stage 실행 결과 딕셔너리
        """
        pass

    async def pre_execute(self,
                         querygoal: Dict[str, Any],
                         context: 'ExecutionContext'):
        """실행 전 공통 준비 작업"""
        self.logger.info(f"🔄 Starting {self.handler_name} for {context.goal_id}")

    async def post_execute(self,
                          result: Dict[str, Any],
                          context: 'ExecutionContext'):
        """실행 후 공통 정리 작업"""
        self.logger.info(f"✅ Completed {self.handler_name} for {context.goal_id}")

    def validate_prerequisites(self,
                              querygoal: Dict[str, Any],
                              context: 'ExecutionContext') -> bool:
        """실행 전 전제조건 검증"""
        # 기본적인 QueryGoal 구조 검증
        qg = querygoal.get("QueryGoal", {})

        required_fields = ["goalId", "goalType", "metadata"]
        for field in required_fields:
            if field not in qg:
                self.logger.error(f"Missing required field in QueryGoal: {field}")
                return False

        return True

    def create_error_result(self, error_message: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """오류 결과 생성"""
        return {
            "status": "error",
            "error": error_message,
            "details": details or {},
            "handler": self.handler_name,
            "timestamp": datetime.utcnow().isoformat()
        }

    def create_success_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """성공 결과 생성"""
        return {
            "status": "success",
            "handler": self.handler_name,
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }