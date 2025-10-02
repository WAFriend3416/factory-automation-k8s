# api/schemas.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum


# ========== 기존 DSL 스키마 ==========
class DslRequest(BaseModel):
    # Field의 ...은 필수 필드임을 의미합니다.
    goal: str = Field(..., example="query_failed_jobs_with_cooling")

    # 각 Goal에 따라 선택적으로 사용되는 파라미터들
    date: Optional[str] = Field(None, example="2025-07-17")
    product_id: Optional[str] = None
    date_range: Optional[Dict[str, str]] = None
    target_machine: Optional[str] = None
    quantity: Optional[int] = None


# ========== QueryGoal 스키마 ==========
class QueryGoalParameter(BaseModel):
    """QueryGoal 파라미터"""
    key: str
    value: Any
    type: Optional[str] = "string"
    required: Optional[bool] = False


class OutputSpecItem(BaseModel):
    """출력 스펙 아이템"""
    name: str
    type: str


class QueryGoalMetadata(BaseModel):
    """QueryGoal 메타데이터"""
    category: str
    requiresModel: bool = False
    actionPlan: List[Dict[str, Any]] = []
    selectedModel: Optional[Dict[str, Any]] = None
    pipelineStages: List[str] = []
    notes: Optional[str] = ""


class QueryGoalCore(BaseModel):
    """QueryGoal 핵심 데이터"""
    goalId: str
    goalType: str
    parameters: List[QueryGoalParameter] = []
    outputSpec: List[OutputSpecItem] = []
    metadata: QueryGoalMetadata
    selectedModelRef: Optional[str] = None
    selectedModel: Optional[Dict[str, Any]] = None
    selectionProvenance: Optional[Dict[str, Any]] = None


class QueryGoalRequest(BaseModel):
    """QueryGoal 요청 스키마"""
    QueryGoal: QueryGoalCore


# ========== 자연어 입력 스키마 ==========
class NaturalLanguageRequest(BaseModel):
    """자연어 입력 요청"""
    query: str = Field(..., example="Check cooling failure for machine M001")
    context: Optional[Dict[str, Any]] = None


# ========== 응답 스키마 ==========
class ApiResponse(BaseModel):
    """표준 API 응답"""
    goal: str
    params: Dict[str, Any]
    result: Any


class QueryGoalResponse(BaseModel):
    """QueryGoal 실행 응답"""
    goalId: str
    status: str  # success, partial, failed
    result: Any
    executionMetadata: Optional[Dict[str, Any]] = None
    pipelineMeta: Optional[Dict[str, Any]] = None


class PipelineStatus(BaseModel):
    """파이프라인 실행 상태"""
    stage: str
    status: str  # pending, in_progress, completed, failed
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str