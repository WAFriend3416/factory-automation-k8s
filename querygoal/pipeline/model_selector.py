"""
Model Selector Module
SWRL 모델 선택 및 바인딩을 처리하는 모듈
기존 SelectionEngine과 통합하여 SPARQL 기반 모델 선택 수행
"""
import json
import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

# 기존 SelectionEngine 임포트
sys.path.append(str(Path(__file__).parent.parent.parent))
from execution_engine.swrl.selection_engine import SelectionEngine, SelectionEngineError


class ModelSelectorError(Exception):
    """모델 선택 관련 에러"""
    pass


class ModelSelector:
    """SWRL 모델 선택 엔진 - 기존 SelectionEngine 통합"""

    def __init__(self, registry_path: Optional[str] = None):
        """
        Args:
            registry_path: 모델 레지스트리 파일 경로
        """
        # 기본 경로 설정
        base_dir = Path(__file__).parent.parent.parent

        # 기존 SelectionEngine 초기화
        ontology_file = str(base_dir / "config" / "ontology.owl")
        rules_file = str(base_dir / "config" / "rules.sparql")
        registry_file = registry_path or str(base_dir / "config" / "model_registry.json")

        # 레지스트리 경로 설정 (항상 필요)
        self.registry_path = Path(registry_file)
        self.model_registry = {}

        try:
            self.selection_engine = SelectionEngine(
                ontology_file=ontology_file,
                rules_file=rules_file,
                model_registry_file=registry_file
            )
            # SelectionEngine이 성공적으로 초기화된 경우에도 레지스트리 로드
            self._load_registry()
        except SelectionEngineError as e:
            # SelectionEngine 초기화 실패 시 fallback 모드
            print(f"Warning: SelectionEngine initialization failed: {e}")
            self.selection_engine = None
            self._load_registry()

        # 선택 규칙 정의 - 실제 모델 레지스트리와 맞춤
        self.selection_rules = {
            "goal3_predict_production_time": {
                "purpose": ["production_time_prediction", "DeliveryPrediction"],  # 다양한 목적 매칭
                "preferred_models": ["NSGA2SimulatorModel", "nsga2_production", "production_optimizer"],
                "scoring_criteria": {
                    "accuracy": 0.4,
                    "performance": 0.3,
                    "complexity": 0.3
                }
            },
            "goal1_query_cooling_failure": {
                "purpose": "diagnostics",
                "preferred_models": [],
                "scoring_criteria": {}
            },
            "goal4_track_product_location": {
                "purpose": "tracking",
                "preferred_models": [],
                "scoring_criteria": {}
            }
        }

    def _load_registry(self):
        """모델 레지스트리 파일 로드"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    models_list = data.get("models", [])

                    # 리스트를 딕셔너리로 변환
                    self.model_registry = {}
                    for model in models_list:
                        model_id = model.get("modelId")
                        if model_id:
                            self.model_registry[model_id] = model

                    print(f"Model registry loaded: {len(self.model_registry)} models")
            except Exception as e:
                print(f"Error loading model registry: {e}")
                self._create_default_registry()
        else:
            print(f"Registry file not found at {self.registry_path}")
            self._create_default_registry()

    def _create_default_registry(self):
        """기본 모델 레지스트리 생성"""
        self.model_registry = {
            "NSGA2SimulatorModel": {
                "modelId": "NSGA2SimulatorModel",
                "name": "NSGA-II Simulator Model",
                "purpose": "DeliveryPrediction",
                "version": "1.0.0",
                "container": "nsga2-optimizer:latest",
                "metaDataFile": "nsga2_production_sources.yaml",
                "outputSchema": {
                    "estimatedTime": "number",
                    "confidence": "number",
                    "paretoSolutions": "array"
                },
                "performance": {
                    "accuracy": 0.92,
                    "avgExecutionTime": 2.5,
                    "complexity": "medium"
                }
            },
            "production_optimizer": {
                "modelId": "production_optimizer",
                "name": "Production Time Optimizer",
                "purpose": "production_time_prediction",
                "version": "2.0.0",
                "container": "production-optimizer:latest",
                "metaDataFile": "production_optimizer_sources.yaml",
                "outputSchema": {
                    "estimatedTime": "number",
                    "confidence": "number",
                    "optimizationPlan": "object"
                },
                "performance": {
                    "accuracy": 0.88,
                    "avgExecutionTime": 1.8,
                    "complexity": "low"
                }
            }
        }

    def select_model(self,
                     goal_type: str,
                     parameters: List[Dict[str, Any]],
                     constraints: Optional[Dict[str, Any]] = None,
                     querygoal_dict: Optional[Dict[str, Any]] = None) -> tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Goal에 적합한 모델 선택 - SelectionEngine.select_model() 통합

        Args:
            goal_type: Goal 타입
            parameters: 입력 파라미터
            constraints: 선택 제약사항
            querygoal_dict: 전체 QueryGoal 딕셔너리 (SelectionEngine용)

        Returns:
            (선택된 모델, 선택 근거)

        Raises:
            ModelSelectorError: 모델이 필수인 Goal에서 선택 실패 시
        """
        # Goal에 대한 선택 규칙 가져오기
        rules = self.selection_rules.get(goal_type, {})
        purposes = rules.get("purpose", [])

        # purpose를 리스트로 변환
        if not isinstance(purposes, list):
            purposes = [purposes]

        if not purposes or purposes == ["diagnostics"] or purposes == ["tracking"]:
            # 모델이 필요 없는 Goal
            return None, {"reason": "Model not required for this goal type"}

        # SelectionEngine이 사용 가능한 경우 우선 사용
        if self.selection_engine and querygoal_dict:
            try:
                result = self.selection_engine.select_model(querygoal_dict)
                selected_model = result["QueryGoal"].get("selectedModel")
                provenance = result["QueryGoal"].get("selectionProvenance", {})

                if selected_model:
                    # SelectionEngine 결과를 우리 형식에 맞게 변환
                    model_info = {
                        "modelId": selected_model["modelId"],
                        "purpose": purposes[0],  # 첫 번째 목적 사용
                        "version": selected_model.get("catalogVersion", "1.0.0"),
                        "container": selected_model.get("container", {}),
                        "metaDataFile": selected_model.get("MetaData", ""),
                    }

                    formatted_provenance = {
                        "selectedAt": provenance.get("timestamp", datetime.now().isoformat()),
                        "selectionMethod": "SPARQL-based-rules",
                        "engine": provenance.get("engine", "SelectionEngine"),
                        "ruleName": provenance.get("ruleName", ""),
                        "evidence": provenance.get("evidence", {}),
                        "reason": f"Selected by SPARQL rules for {goal_type}"
                    }

                    return model_info, formatted_provenance

            except SelectionEngineError as e:
                print(f"SelectionEngine failed: {e}, falling back to legacy method")

        # Fallback: 기존 방식으로 모델 선택
        return self._legacy_select_model(goal_type, parameters, constraints, purposes)

    def _legacy_select_model(self,
                            goal_type: str,
                            parameters: List[Dict[str, Any]],
                            constraints: Optional[Dict[str, Any]],
                            purposes: List[str]) -> tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Legacy 모델 선택 방식 (SelectionEngine 실패 시 fallback)

        Args:
            goal_type: Goal 타입
            parameters: 입력 파라미터
            constraints: 선택 제약사항
            purposes: 목적 리스트

        Returns:
            (선택된 모델, 선택 근거)
        """
        # 적합한 모델 필터링
        candidate_models = []
        for model_id, model_info in self.model_registry.items():
            model_purpose = model_info.get("purpose")
            # purpose 매칭 (리스트 내 어느 하나라도 일치하면 OK)
            if model_purpose in purposes:
                candidate_models.append(model_info)

        if not candidate_models:
            return None, {"reason": f"No models found for purposes: {purposes}"}

        # 모델 점수 계산
        rules = self.selection_rules.get(goal_type, {})
        scored_models = []
        scoring_criteria = rules.get("scoring_criteria", {})

        for model in candidate_models:
            score = self._calculate_model_score(model, scoring_criteria, constraints)
            scored_models.append((model, score))

        # 최고 점수 모델 선택
        scored_models.sort(key=lambda x: x[1]["totalScore"], reverse=True)
        best_model, best_score = scored_models[0]

        # 선택 근거 생성
        provenance = {
            "selectedAt": datetime.now().isoformat(),
            "selectionMethod": "rule-based-scoring",
            "candidatesEvaluated": len(candidate_models),
            "scores": best_score,
            "reason": f"Highest scoring model for purposes: {purposes}",
            "alternatives": [
                {"modelId": m[0]["modelId"], "score": m[1]["totalScore"]}
                for m in scored_models[1:3] if len(scored_models) > 1
            ]
        }

        return best_model, provenance

    def _calculate_model_score(self,
                               model: Dict[str, Any],
                               criteria: Dict[str, float],
                               constraints: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        모델 점수 계산

        Args:
            model: 모델 정보
            criteria: 평가 기준
            constraints: 제약사항

        Returns:
            점수 딕셔너리
        """
        scores = {}
        performance = model.get("performance", {})

        # 정확도 점수
        if "accuracy" in criteria:
            accuracy = performance.get("accuracy", 0.5)
            scores["accuracy"] = accuracy * criteria["accuracy"]

        # 성능 점수
        if "performance" in criteria:
            exec_time = performance.get("avgExecutionTime", 10)
            # 실행 시간이 짧을수록 점수 높음
            perf_score = max(0, 1 - (exec_time / 10))
            scores["performance"] = perf_score * criteria["performance"]

        # 복잡도 점수
        if "complexity" in criteria:
            complexity_map = {"low": 1.0, "medium": 0.6, "high": 0.3}
            complexity = performance.get("complexity", "high")
            scores["complexity"] = complexity_map.get(complexity, 0.3) * criteria["complexity"]

        # 제약사항 체크
        if constraints:
            max_time = constraints.get("maxExecutionTime")
            if max_time and performance.get("avgExecutionTime", 0) > max_time:
                scores["penalty"] = -0.5

        # 총점 계산
        total_score = sum(scores.values())
        scores["totalScore"] = total_score

        return scores

    def bind_model_to_querygoal(self,
                                querygoal: Dict[str, Any],
                                goal_type: str) -> Dict[str, Any]:
        """
        QueryGoal에 모델 바인딩 - Fail-fast 로직 포함

        Args:
            querygoal: QueryGoal 딕셔너리
            goal_type: Goal 타입

        Returns:
            업데이트된 QueryGoal

        Raises:
            ModelSelectorError: 모델이 필수인 Goal에서 선택 실패 시 즉시 예외
        """
        qg = querygoal["QueryGoal"]

        # 모델 필요 여부 확인
        requires_model = qg["metadata"].get("requiresModel", False)
        if not requires_model:
            return querygoal

        # 파라미터 추출
        parameters = qg.get("parameters", [])

        # 모델 선택 - QueryGoal 전체를 전달 (SelectionEngine용)
        selected_model, provenance = self.select_model(
            goal_type=goal_type,
            parameters=parameters,
            querygoal_dict=querygoal
        )

        if selected_model:
            # 모델 정보 바인딩
            qg["selectedModelRef"] = selected_model["modelId"]
            qg["selectedModel"] = selected_model
            qg["selectionProvenance"] = provenance

            # 메타데이터 업데이트
            qg["metadata"]["selectedModel"] = {
                "modelId": selected_model["modelId"],
                "name": selected_model.get("name", selected_model["modelId"]),
                "version": selected_model.get("version", "1.0.0")
            }

            qg["metadata"]["notes"] += f" | Model selected: {selected_model['modelId']}"

        else:
            # **FAIL-FAST: 모델이 필수인 Goal에서 선택 실패 시 즉시 예외**
            error_msg = f"Model selection failed for goal type '{goal_type}' that requires a model"
            if provenance and provenance.get("reason"):
                error_msg += f": {provenance['reason']}"

            raise ModelSelectorError(error_msg)

        return querygoal

    def get_model_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        모델 메타데이터 조회

        Args:
            model_id: 모델 ID

        Returns:
            모델 메타데이터 또는 None
        """
        return self.model_registry.get(model_id)

    def validate_model_compatibility(self,
                                     model_id: str,
                                     input_params: List[Dict[str, Any]]) -> tuple[bool, List[str]]:
        """
        모델과 입력 파라미터 호환성 검증

        Args:
            model_id: 모델 ID
            input_params: 입력 파라미터

        Returns:
            (호환 여부, 문제점 리스트)
        """
        model = self.model_registry.get(model_id)
        if not model:
            return False, ["Model not found in registry"]

        issues = []

        # 필수 파라미터 체크
        required_params = model.get("requiredInputs", [])
        provided_keys = {p["key"] for p in input_params}

        missing = [p for p in required_params if p not in provided_keys]
        if missing:
            issues.append(f"Missing required parameters: {missing}")

        return len(issues) == 0, issues