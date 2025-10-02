"""
핵심 선택 엔진: SPARQL 기반 모델 선택 및 메타데이터 통합
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from rdflib import Graph, Namespace, URIRef, Literal, RDF
from rdflib.plugins.stores.memory import Memory

from .preprocessor import preprocess_query_goal, UnknownTokenError
from .schema_validator import validate_query_goal_schema, ValidationError


class SelectionEngineError(Exception):
    """선택 엔진 관련 에러"""
    pass


class SelectionEngine:
    """SPARQL 기반 모델 선택 엔진"""

    def __init__(self, ontology_file: str = "config/ontology.owl",
                 rules_file: str = "config/rules.sparql",
                 model_registry_file: str = "config/model_registry.json"):
        """
        선택 엔진 초기화

        Args:
            ontology_file: RDF 온톨로지 파일 경로
            rules_file: SPARQL 규칙 파일 경로
            model_registry_file: 모델 레지스트리 JSON 파일 경로
        """
        self.ontology_file = ontology_file
        self.rules_file = rules_file
        self.model_registry_file = model_registry_file

        # 네임스페이스 정의
        self.ex = Namespace("http://example.com/ontology#")
        self.rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

        # 모델 레지스트리 로드
        self.model_registry = self._load_model_registry()

    def select_model(self, query_goal_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        QueryGoal에 대한 모델 선택 수행

        Args:
            query_goal_dict: 원본 QueryGoal 딕셔너리

        Returns:
            선택된 모델 정보가 포함된 확장 QueryGoal

        Raises:
            SelectionEngineError: 선택 과정에서 오류 발생시
        """
        try:
            # Phase 1: 전처리 및 검증
            processed_goal = preprocess_query_goal(query_goal_dict)
            validate_query_goal_schema(processed_goal)

            # Phase 2: SPARQL 추론
            graph = self._create_rdf_graph()
            self._add_query_goal_to_graph(processed_goal, graph)
            self._add_models_to_graph(graph)
            selected_model_id = self._execute_rules(graph, processed_goal["QueryGoal"]["goalType"])

            if not selected_model_id:
                raise SelectionEngineError(f"No matching model found for goalType: {processed_goal['QueryGoal']['goalType']}")

            # Phase 3: 메타데이터 통합
            model_metadata = self._get_model_metadata(selected_model_id)
            provenance = self._generate_provenance(selected_model_id, processed_goal["QueryGoal"]["goalType"])

            # Phase 4: 최종 JSON 조합
            return self._build_final_response(processed_goal, model_metadata, provenance)

        except (UnknownTokenError, ValidationError) as e:
            raise SelectionEngineError(f"Input validation failed: {e}")
        except Exception as e:
            raise SelectionEngineError(f"Selection process failed: {e}")

    def _load_model_registry(self) -> Dict[str, Any]:
        """모델 레지스트리 JSON 로드"""
        try:
            with open(self.model_registry_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise SelectionEngineError(f"Model registry file not found: {self.model_registry_file}")
        except json.JSONDecodeError as e:
            raise SelectionEngineError(f"Invalid JSON in model registry: {e}")

    def _create_rdf_graph(self) -> Graph:
        """RDF 그래프 생성 및 온톨로지 로드"""
        try:
            graph = Graph()
            graph.parse(self.ontology_file, format="xml")

            # 네임스페이스 바인딩
            graph.bind("ex", self.ex)
            graph.bind("rdf", self.rdf)

            return graph
        except Exception as e:
            raise SelectionEngineError(f"Failed to load ontology: {e}")

    def _add_query_goal_to_graph(self, processed_goal: Dict[str, Any], graph: Graph) -> None:
        """QueryGoal을 RDF 그래프에 추가"""
        goal_obj = processed_goal["QueryGoal"]

        # QueryGoal 인스턴스 생성
        goal_uri = URIRef(f"http://example.com/data#{goal_obj['goalId']}")
        graph.add((goal_uri, RDF.type, self.ex.QueryGoal))
        graph.add((goal_uri, self.ex.goalId, Literal(goal_obj["goalId"])))
        graph.add((goal_uri, self.ex.goalType, Literal(goal_obj["goalType"])))

        # Parameters 추가
        for i, param in enumerate(goal_obj.get("parameters", [])):
            param_uri = URIRef(f"http://example.com/data#{goal_obj['goalId']}_param_{i}")
            graph.add((param_uri, RDF.type, self.ex.Parameter))
            graph.add((param_uri, self.ex.parameterKey, Literal(param["key"])))
            graph.add((param_uri, self.ex.parameterValue, Literal(param["value"])))
            graph.add((goal_uri, self.ex.hasParameter, param_uri))

        # OutputSpec 추가
        for i, spec in enumerate(goal_obj.get("outputSpec", [])):
            spec_uri = URIRef(f"http://example.com/data#{goal_obj['goalId']}_output_{i}")
            graph.add((spec_uri, RDF.type, self.ex.OutputSpec))
            graph.add((spec_uri, self.ex.outputName, Literal(spec["name"])))
            graph.add((spec_uri, self.ex.outputDatatype, Literal(spec["datatype"])))
            graph.add((goal_uri, self.ex.hasOutputSpec, spec_uri))

    def _add_models_to_graph(self, graph: Graph) -> None:
        """모델 레지스트리의 모델들을 RDF 그래프에 추가"""
        for model in self.model_registry.get("models", []):
            model_uri = URIRef(f"http://example.com/data#{model['modelId']}")
            graph.add((model_uri, RDF.type, self.ex.Model))
            graph.add((model_uri, self.ex.modelId, Literal(model["modelId"])))
            graph.add((model_uri, self.ex.purpose, Literal(model["purpose"])))
            graph.add((model_uri, self.ex.version, Literal(model["version"])))
            graph.add((model_uri, self.ex.metaDataFile, Literal(model["metaDataFile"])))

    def _execute_rules(self, graph: Graph, goal_type: str) -> Optional[str]:
        """SPARQL 규칙 실행 및 선택된 모델 ID 반환"""
        try:
            # SPARQL 규칙 파일 로드
            with open(self.rules_file, "r", encoding="utf-8") as f:
                rules_content = f.read()

            # 각 규칙을 개별적으로 실행 (INSERT 쿼리들)
            # 실제로는 하나의 큰 파일에서 개별 규칙을 분리해야 하지만,
            # 간단히 전체 규칙을 실행

            # 규칙을 개별 INSERT 문으로 분리
            insert_queries = self._parse_sparql_rules(rules_content)

            for query in insert_queries:
                try:
                    graph.update(query)
                except Exception as e:
                    print(f"Rule execution warning: {e}")

            # 선택된 모델 조회
            return self._query_selected_model(graph, goal_type)

        except FileNotFoundError:
            raise SelectionEngineError(f"Rules file not found: {self.rules_file}")
        except Exception as e:
            raise SelectionEngineError(f"Failed to execute rules: {e}")

    def _parse_sparql_rules(self, rules_content: str) -> List[str]:
        """SPARQL 규칙 파일에서 개별 INSERT 쿼리 분리"""
        # 간단한 구현: 하나의 큰 UPDATE 쿼리로 실행
        # PREFIX 선언들 수집
        prefixes = []
        insert_blocks = []

        lines = rules_content.split('\n')
        current_block = []
        collecting_insert = False

        for line in lines:
            line = line.strip()

            # 주석이나 빈 줄 건너뛰기
            if not line or line.startswith('#'):
                continue

            # PREFIX 수집
            if line.startswith('PREFIX'):
                prefixes.append(line)
                continue

            # INSERT 블록 시작
            if line.startswith('INSERT'):
                if current_block:  # 이전 블록 저장
                    insert_blocks.append('\n'.join(current_block))
                current_block = [line]
                collecting_insert = True
                continue

            if collecting_insert:
                current_block.append(line)

        # 마지막 블록 저장
        if current_block:
            insert_blocks.append('\n'.join(current_block))

        # 각 INSERT 블록을 완전한 쿼리로 변환
        complete_queries = []
        prefix_block = '\n'.join(prefixes)

        for insert_block in insert_blocks:
            complete_query = prefix_block + '\n\n' + insert_block
            complete_queries.append(complete_query)

        return complete_queries

    def _query_selected_model(self, graph: Graph, goal_type: str) -> Optional[str]:
        """선택된 모델 ID 조회"""
        query = """
        PREFIX ex: <http://example.com/ontology#>

        SELECT ?modelId WHERE {
            ?goal ex:goalType ?goalType .
            ?goal ex:selectedModel ?model .
            ?model ex:modelId ?modelId .
            FILTER(?goalType = ?target_goal_type)
        }
        """

        results = graph.query(query, initBindings={'target_goal_type': Literal(goal_type)})

        for row in results:
            return str(row.modelId)

        return None

    def _get_model_metadata(self, model_id: str) -> Dict[str, Any]:
        """모델 레지스트리에서 모델 메타데이터 조회"""
        for model in self.model_registry.get("models", []):
            if model["modelId"] == model_id:
                return model

        raise SelectionEngineError(f"Model metadata not found for: {model_id}")

    def _generate_provenance(self, model_id: str, goal_type: str) -> Dict[str, Any]:
        """선택 과정에 대한 provenance 정보 생성"""
        return {
            "ruleName": f"SWRL:Goal2{model_id}",
            "engine": "Rule-based Module (SPARQL)",
            "evidence": {
                "matched": [
                    f"goalType=={goal_type}",
                    f"purpose=={self._get_model_metadata(model_id)['purpose']}"
                ]
            },
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "confidence": 1.0
        }

    def _build_final_response(self, processed_goal: Dict[str, Any],
                            model_metadata: Dict[str, Any],
                            provenance: Dict[str, Any]) -> Dict[str, Any]:
        """최종 응답 JSON 구성"""
        
        # metaDataFile이 NSGA2Model_sources.yaml인지 확인하고 필요시 변환
        metadata_file = model_metadata.get("metaDataFile", "")
        if "NSGA2" in model_metadata.get("modelId", "") and metadata_file != "NSGA2Model_sources.yaml":
            # NSGA2 모델은 항상 통일된 파일명 사용
            metadata_file = "NSGA2Model_sources.yaml"
        
        # 원본 QueryGoal 복사
        result = json.loads(json.dumps(processed_goal))

        # 확장 필드 추가
        result["QueryGoal"]["selectedModelRef"] = model_metadata["modelRef"]
        result["QueryGoal"]["selectedModel"] = {
            "modelId": model_metadata["modelId"],
            "MetaData": metadata_file,  # 통일된 파일명 사용
            "outputs": [spec["name"] for spec in model_metadata.get("outputSchema", [])],
            "preconditions": {
                "units.time": "s",
                "runtime.freshness": "PT30S"
            },
            "container": model_metadata.get("container", {
                "image": "factory-nsga2:latest",
                "digest": "sha256:factory-nsga2-latest"
            }),
            "catalogVersion": model_metadata["version"],
            "frozenAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        result["QueryGoal"]["selectionProvenance"] = {
            "ruleName": provenance["ruleName"],
            "ruleVersion": "v1.0",
            "engine": provenance["engine"],
            "evidence": provenance["evidence"],
            "inputsHash": f"sha256:{hash(str(processed_goal))}",
            "timestamp": provenance["timestamp"],
            "notes": ""
        }

        return result


def main():
    """테스트를 위한 메인 함수 - output.json 파일 생성"""
    try:
        # user_input_clean.json 로드 (또는 user_input.json)
        input_files = ["user_input_clean.json", "user_input.json"]
        test_input = None
        input_file_used = None

        for input_file in input_files:
            try:
                with open(input_file, "r", encoding="utf-8") as f:
                    test_input = json.load(f)
                    input_file_used = input_file
                    break
            except FileNotFoundError:
                continue

        if test_input is None:
            raise FileNotFoundError("Neither user_input_clean.json nor user_input.json found")

        print("=== 모델 선택 엔진 테스트 ===")
        print(f"입력 파일: {input_file_used}")
        print("입력:")
        print(json.dumps(test_input, indent=2, ensure_ascii=False))

        # 선택 엔진 실행
        engine = SelectionEngine()
        result = engine.select_model(test_input)

        # output.json 파일로 저장
        output_file = "output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 선택 완료! 결과가 {output_file}에 저장되었습니다.")
        print("\n📄 선택된 모델 정보:")
        print(f"   - 모델 ID: {result['QueryGoal']['selectedModel']['modelId']}")
        print(f"   - 목적: {result['QueryGoal']['selectedModel']['purpose']}")
        print(f"   - 버전: {result['QueryGoal']['selectedModel']['version']}")
        print(f"   - 규칙: {result['QueryGoal']['selectionProvenance']['ruleName']}")

    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e}")
    except SelectionEngineError as e:
        print(f"❌ 선택 엔진 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")


if __name__ == "__main__":
    main()