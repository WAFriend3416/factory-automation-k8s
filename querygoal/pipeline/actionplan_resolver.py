"""
Action Plan Resolver Module
온톨로지에서 액션 시퀀스를 읽어와 QueryGoal에 주입하는 모듈
"""
from typing import Dict, Any, List, Optional
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
import os
from pathlib import Path


class ActionPlanResolver:
    """온톨로지 기반 액션 플랜 결정"""

    def __init__(self, ontology_path: Optional[str] = None):
        """
        Args:
            ontology_path: 온톨로지 파일 경로
        """
        self.graph = Graph()

        # 온톨로지 경로 설정
        if ontology_path:
            self.ontology_path = Path(ontology_path)
        else:
            # 기본 경로 - 현재 프로젝트의 온톨로지 사용
            base_dir = Path(__file__).parent.parent.parent
            self.ontology_path = base_dir / "ontology" / "factory_ontology_v2_final_corrected.ttl"

        # 네임스페이스 정의
        self.FACTORY = Namespace("http://www.example.org/factory-automation#")
        self.ACTION = Namespace("http://www.example.org/factory-automation/action#")

        # 온톨로지 로드
        if self.ontology_path.exists():
            self._load_ontology()
        else:
            print(f"Warning: Ontology file not found at {self.ontology_path}")

        # 기본 액션 플랜 정의 (온톨로지가 없을 경우 폴백)
        self.default_action_plans = {
            "goal1_query_cooling_failure": [
                {
                    "actionId": "action_001",
                    "actionType": "ActionQueryAAS",
                    "description": "Query AAS for cooling failure data",
                    "parameters": {"endpoint": "cooling/status"}
                },
                {
                    "actionId": "action_002",
                    "actionType": "ActionFilterData",
                    "description": "Filter failure events",
                    "parameters": {"filter": "status=failure"}
                },
                {
                    "actionId": "action_003",
                    "actionType": "ActionAnalyzeDiagnostics",
                    "description": "Analyze diagnostic data",
                    "parameters": {"mode": "cooling_diagnostics"}
                }
            ],
            "goal3_predict_production_time": [
                {
                    "actionId": "action_101",
                    "actionType": "ActionSelectModel",
                    "description": "Select SWRL prediction model",
                    "parameters": {"modelType": "production_time"}
                },
                {
                    "actionId": "action_102",
                    "actionType": "ActionBindData",
                    "description": "Bind YAML data sources",
                    "parameters": {"dataSource": "production_data.yaml"}
                },
                {
                    "actionId": "action_103",
                    "actionType": "ActionRunProductionSimulator",
                    "description": "Run production simulation",
                    "parameters": {"simulationType": "time_estimation"}
                },
                {
                    "actionId": "action_104",
                    "actionType": "ActionProcessResults",
                    "description": "Process simulation results",
                    "parameters": {"outputFormat": "json"}
                }
            ],
            "goal4_track_product_location": [
                {
                    "actionId": "action_201",
                    "actionType": "ActionQueryAAS",
                    "description": "Query AAS for product location",
                    "parameters": {"endpoint": "product/location"}
                },
                {
                    "actionId": "action_202",
                    "actionType": "ActionTrackMovement",
                    "description": "Track product movement",
                    "parameters": {"trackingMode": "realtime"}
                },
                {
                    "actionId": "action_203",
                    "actionType": "ActionUpdateLocation",
                    "description": "Update location information",
                    "parameters": {"updateFrequency": "5s"}
                }
            ]
        }

    def _load_ontology(self):
        """온톨로지 파일 로드"""
        try:
            self.graph.parse(self.ontology_path, format='turtle')
            self.graph.bind("factory", self.FACTORY)
            self.graph.bind("action", self.ACTION)
            print(f"Ontology loaded from {self.ontology_path}")
        except Exception as e:
            print(f"Error loading ontology: {e}")

    def get_action_sequence_from_ontology(self, goal_type: str) -> List[Dict[str, Any]]:
        """
        온톨로지에서 Goal에 해당하는 액션 시퀀스 조회

        Args:
            goal_type: Goal 타입

        Returns:
            액션 시퀀스 리스트
        """
        actions = []

        # SPARQL 쿼리로 액션 시퀀스 조회
        query = f"""
        PREFIX factory: <{self.FACTORY}>
        PREFIX action: <{self.ACTION}>

        SELECT ?action ?actionType ?description ?sequence
        WHERE {{
            factory:{goal_type} factory:hasActionSequence ?actionSeq .
            ?actionSeq factory:hasAction ?action .
            ?action rdf:type ?actionType ;
                    factory:description ?description ;
                    factory:sequenceNumber ?sequence .
        }}
        ORDER BY ?sequence
        """

        try:
            results = self.graph.query(query)

            for row in results:
                action_dict = {
                    "actionId": str(row.action).split("#")[-1] if row.action else f"action_{len(actions)}",
                    "actionType": str(row.actionType).split("#")[-1] if row.actionType else "UnknownAction",
                    "description": str(row.description) if row.description else "No description",
                    "parameters": {}
                }
                actions.append(action_dict)

        except Exception as e:
            print(f"Error querying ontology: {e}")

        # 온톨로지에서 못 찾으면 기본값 사용
        if not actions:
            actions = self.default_action_plans.get(goal_type, [])

        return actions

    def resolve_action_plan(self,
                            querygoal: Dict[str, Any],
                            goal_type: str) -> Dict[str, Any]:
        """
        QueryGoal에 액션 플랜 주입

        Args:
            querygoal: QueryGoal 딕셔너리
            goal_type: Goal 타입

        Returns:
            업데이트된 QueryGoal
        """
        qg = querygoal["QueryGoal"]

        # 온톨로지에서 액션 시퀀스 가져오기
        action_sequence = self.get_action_sequence_from_ontology(goal_type)

        # 모델 필요 여부에 따라 액션 조정
        requires_model = qg["metadata"].get("requiresModel", False)

        if requires_model:
            # 시뮬레이터 액션이 없으면 추가
            has_simulator = any("Simulator" in action.get("actionType", "") for action in action_sequence)
            if not has_simulator:
                action_sequence.append({
                    "actionId": f"action_{len(action_sequence)}",
                    "actionType": "ActionRunSimulator",
                    "description": "Run simulation with selected model",
                    "parameters": {"modelRef": "selectedModel"}
                })
        else:
            # 모델 불필요한 경우 시뮬레이터 관련 액션 제거
            action_sequence = [
                action for action in action_sequence
                if "Simulator" not in action.get("actionType", "") and
                   "Model" not in action.get("actionType", "")
            ]

        # QueryGoal에 액션 플랜 설정
        qg["metadata"]["actionPlan"] = action_sequence

        # 액션 플랜 요약 정보 추가
        qg["metadata"]["notes"] += f" | Action plan resolved: {len(action_sequence)} actions"

        return querygoal

    def validate_action_dependencies(self, action_plan: List[Dict[str, Any]]) -> tuple[bool, List[str]]:
        """
        액션 플랜의 의존성 검증

        Args:
            action_plan: 액션 플랜 리스트

        Returns:
            (검증 성공 여부, 문제점 리스트)
        """
        issues = []

        # 모델 선택 전에 시뮬레이션이 있는지 확인
        model_select_index = -1
        simulator_index = -1

        for i, action in enumerate(action_plan):
            action_type = action.get("actionType", "")
            if "SelectModel" in action_type:
                model_select_index = i
            elif "Simulator" in action_type:
                simulator_index = i

        if simulator_index != -1 and model_select_index == -1:
            issues.append("Simulator action found but no model selection action")
        elif simulator_index != -1 and model_select_index != -1 and simulator_index < model_select_index:
            issues.append("Simulator action appears before model selection")

        # 데이터 바인딩 검증
        bind_data_index = -1
        for i, action in enumerate(action_plan):
            if "BindData" in action.get("actionType", ""):
                bind_data_index = i
                break

        if simulator_index != -1 and bind_data_index == -1:
            issues.append("Simulator requires data binding but no bind data action found")

        return len(issues) == 0, issues

    def optimize_action_sequence(self, action_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        액션 시퀀스 최적화 (병렬 실행 가능한 액션 식별)

        Args:
            action_plan: 원본 액션 플랜

        Returns:
            최적화된 액션 플랜
        """
        optimized = []

        # 병렬 실행 가능한 액션 타입 정의
        parallelizable = ["ActionQueryAAS", "ActionFilterData"]

        for action in action_plan:
            action_copy = action.copy()

            # 병렬 실행 가능 여부 표시
            if action.get("actionType") in parallelizable:
                action_copy["parallelizable"] = True
            else:
                action_copy["parallelizable"] = False

            optimized.append(action_copy)

        return optimized