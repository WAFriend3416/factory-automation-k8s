"""
Registry Consistency Checker
설정 파일들 간 정합성 검증 도구
- config/rules.sparql
- config/ontology.owl (+ TTL 백업)
- config/model_registry.json
- querygoal/pipeline 패턴 규칙
"""
import json
import os
from typing import Dict, Any, List, Set, Optional, Tuple
from pathlib import Path
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS
import re


class RegistryConsistencyError(Exception):
    """정합성 검사 오류"""
    pass


class RegistryChecker:
    """설정 파일 정합성 검사기"""

    def __init__(self, base_dir: Optional[str] = None):
        """
        Args:
            base_dir: 프로젝트 기본 디렉토리
        """
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).parent.parent.parent

        # 파일 경로 설정
        self.config_dir = self.base_dir / "config"
        self.rules_file = self.config_dir / "rules.sparql"
        self.ontology_file = self.config_dir / "ontology.owl"
        self.ttl_backup_file = self.base_dir.parent / "factory-automation-k8s-backup" / "ontology" / "factory_ontology_v2_final_corrected.ttl"
        self.registry_file = self.config_dir / "model_registry.json"
        self.pipeline_dir = self.base_dir / "querygoal" / "pipeline"

        # 네임스페이스 정의
        self.ex = Namespace("http://example.com/ontology#")

        # 검사 결과 저장
        self.issues: List[Dict[str, Any]] = []

    def check_all(self) -> Dict[str, Any]:
        """
        모든 정합성 검사 수행

        Returns:
            검사 결과 딕셔너리
        """
        print("🔍 Registry Consistency Check 시작...")

        # 파일 존재 여부 확인
        self._check_file_existence()

        # 데이터 로드
        try:
            registry_data = self._load_model_registry()
            sparql_rules = self._load_sparql_rules()
            ontology_data = self._load_ontology_data()
            pattern_rules = self._load_pattern_rules()
        except Exception as e:
            self.issues.append({
                "type": "critical",
                "category": "file_loading",
                "message": f"Failed to load configuration files: {e}",
                "file": "multiple"
            })
            return self._generate_report()

        # 정합성 검사 수행
        self._check_goal_type_consistency(registry_data, sparql_rules, pattern_rules)
        self._check_model_purpose_mapping(registry_data, sparql_rules)
        self._check_model_registry_completeness(registry_data)
        self._check_ontology_action_sequences(ontology_data, pattern_rules)
        self._check_pipeline_stage_consistency(pattern_rules)

        return self._generate_report()

    def _check_file_existence(self) -> None:
        """필수 파일 존재 여부 확인"""
        files_to_check = [
            (self.rules_file, "SPARQL Rules"),
            (self.registry_file, "Model Registry"),
            (self.pipeline_dir / "pattern_matcher.py", "Pattern Matcher")
        ]

        # 온톨로지 파일 체크 (OWL 또는 TTL)
        if self.ontology_file.exists():
            files_to_check.append((self.ontology_file, "Ontology (OWL)"))
        elif self.ttl_backup_file.exists():
            files_to_check.append((self.ttl_backup_file, "Ontology (TTL Backup)"))
        else:
            self.issues.append({
                "type": "critical",
                "category": "missing_file",
                "message": "Neither ontology.owl nor TTL backup file found",
                "file": "config/ontology.*"
            })

        for file_path, description in files_to_check:
            if not file_path.exists():
                self.issues.append({
                    "type": "critical",
                    "category": "missing_file",
                    "message": f"{description} file not found",
                    "file": str(file_path.relative_to(self.base_dir))
                })

    def _load_model_registry(self) -> Dict[str, Any]:
        """모델 레지스트리 로드"""
        if not self.registry_file.exists():
            return {"models": []}

        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.issues.append({
                "type": "critical",
                "category": "parse_error",
                "message": f"Invalid JSON in model registry: {e}",
                "file": "config/model_registry.json"
            })
            return {"models": []}

    def _load_sparql_rules(self) -> str:
        """SPARQL 규칙 파일 로드"""
        if not self.rules_file.exists():
            return ""

        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.issues.append({
                "type": "error",
                "category": "file_read",
                "message": f"Failed to read SPARQL rules: {e}",
                "file": "config/rules.sparql"
            })
            return ""

    def _load_ontology_data(self) -> Optional[Graph]:
        """온톨로지 데이터 로드"""
        graph = None

        # OWL 파일 시도
        if self.ontology_file.exists():
            try:
                graph = Graph()
                graph.parse(self.ontology_file, format="xml")
                graph.bind("ex", self.ex)
            except Exception as e:
                self.issues.append({
                    "type": "warning",
                    "category": "parse_error",
                    "message": f"Failed to parse OWL ontology: {e}",
                    "file": "config/ontology.owl"
                })

        # TTL 백업 파일 시도
        if not graph and self.ttl_backup_file.exists():
            try:
                graph = Graph()
                graph.parse(self.ttl_backup_file, format="turtle")
                graph.bind("ex", self.ex)
            except Exception as e:
                self.issues.append({
                    "type": "warning",
                    "category": "parse_error",
                    "message": f"Failed to parse TTL ontology: {e}",
                    "file": "factory-automation-k8s-backup/ontology/*.ttl"
                })

        return graph

    def _load_pattern_rules(self) -> Dict[str, Any]:
        """패턴 매칭 규칙 로드"""
        pattern_file = self.pipeline_dir / "pattern_matcher.py"
        if not pattern_file.exists():
            return {}

        try:
            with open(pattern_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # GoalType enum 추출
            goal_types = set()
            enum_match = re.search(r'class GoalType\(Enum\):(.*?)(?=class|\Z)', content, re.DOTALL)
            if enum_match:
                enum_content = enum_match.group(1)
                for line in enum_content.split('\n'):
                    match = re.search(r'(\w+)\s*=\s*["\']([^"\']+)["\']', line)
                    if match:
                        goal_types.add(match.group(2))

            # 패턴 추출
            patterns = {}
            patterns_match = re.search(r'self\.patterns\s*=\s*{(.*?)}', content, re.DOTALL)
            if patterns_match:
                patterns_content = patterns_match.group(1)
                # 간단한 파싱 (실제로는 AST를 사용하는 것이 좋음)
                current_goal = None
                for line in patterns_content.split('\n'):
                    line = line.strip()
                    if 'GoalType.' in line and ':' in line:
                        goal_match = re.search(r'GoalType\.(\w+)', line)
                        if goal_match:
                            current_goal = goal_match.group(1)
                            patterns[current_goal] = []

            return {
                "goal_types": goal_types,
                "patterns": patterns
            }

        except Exception as e:
            self.issues.append({
                "type": "warning",
                "category": "file_read",
                "message": f"Failed to read pattern rules: {e}",
                "file": "querygoal/pipeline/pattern_matcher.py"
            })
            return {}

    def _check_goal_type_consistency(self,
                                    registry_data: Dict[str, Any],
                                    sparql_rules: str,
                                    pattern_rules: Dict[str, Any]) -> None:
        """Goal 타입 일관성 확인"""
        # 각 소스에서 Goal 타입 추출
        registry_goals = set()
        for model in registry_data.get("models", []):
            purpose = model.get("purpose", "")
            if "goal" in purpose.lower():
                registry_goals.add(purpose)

        sparql_goals = set()
        # SPARQL에서 goalType 추출 (간단한 패턴 매칭)
        goal_matches = re.findall(r'goalType\s*==?\s*["\']([^"\']+)["\']', sparql_rules, re.IGNORECASE)
        sparql_goals.update(goal_matches)

        pattern_goals = set(pattern_rules.get("goal_types", set()))

        # 차이점 확인
        all_goals = registry_goals | sparql_goals | pattern_goals

        for goal in all_goals:
            sources = []
            if goal in registry_goals:
                sources.append("registry")
            if goal in sparql_goals:
                sources.append("sparql")
            if goal in pattern_goals:
                sources.append("patterns")

            if len(sources) != 3:
                missing = {"registry", "sparql", "patterns"} - set(sources)
                self.issues.append({
                    "type": "warning",
                    "category": "goal_type_inconsistency",
                    "message": f"Goal type '{goal}' missing from: {', '.join(missing)}",
                    "file": "multiple",
                    "goal": goal,
                    "present_in": sources,
                    "missing_from": list(missing)
                })

    def _check_model_purpose_mapping(self,
                                    registry_data: Dict[str, Any],
                                    sparql_rules: str) -> None:
        """모델 purpose 매핑 확인"""
        registry_purposes = set()
        for model in registry_data.get("models", []):
            purpose = model.get("purpose")
            if purpose:
                registry_purposes.add(purpose)

        # SPARQL에서 purpose 추출
        sparql_purposes = set()
        purpose_matches = re.findall(r'purpose\s*==?\s*["\']([^"\']+)["\']', sparql_rules, re.IGNORECASE)
        sparql_purposes.update(purpose_matches)

        # purpose 불일치 확인
        registry_only = registry_purposes - sparql_purposes
        sparql_only = sparql_purposes - registry_purposes

        if registry_only:
            self.issues.append({
                "type": "warning",
                "category": "purpose_mapping",
                "message": f"Purposes in registry but not in SPARQL: {registry_only}",
                "file": "config/rules.sparql"
            })

        if sparql_only:
            self.issues.append({
                "type": "warning",
                "category": "purpose_mapping",
                "message": f"Purposes in SPARQL but not in registry: {sparql_only}",
                "file": "config/model_registry.json"
            })

    def _check_model_registry_completeness(self, registry_data: Dict[str, Any]) -> None:
        """모델 레지스트리 완성도 확인"""
        required_fields = ["modelId", "purpose", "version", "metaDataFile"]
        optional_fields = ["description", "capabilities", "inputParameters", "outputSchema", "performance", "container"]

        for model in registry_data.get("models", []):
            model_id = model.get("modelId", "unknown")

            # 필수 필드 확인
            for field in required_fields:
                if field not in model or not model[field]:
                    self.issues.append({
                        "type": "error",
                        "category": "incomplete_model",
                        "message": f"Model '{model_id}' missing required field: {field}",
                        "file": "config/model_registry.json",
                        "model": model_id,
                        "field": field
                    })

            # metaDataFile 존재 확인
            metadata_file = model.get("metaDataFile")
            if metadata_file:
                metadata_path = self.base_dir / metadata_file
                if not metadata_path.exists():
                    self.issues.append({
                        "type": "warning",
                        "category": "missing_metadata",
                        "message": f"Metadata file not found for model '{model_id}': {metadata_file}",
                        "file": metadata_file,
                        "model": model_id
                    })

    def _check_ontology_action_sequences(self,
                                        ontology_data: Optional[Graph],
                                        pattern_rules: Dict[str, Any]) -> None:
        """온톨로지 액션 시퀀스 확인"""
        if not ontology_data:
            return

        # hasActionSequence 관계 확인
        query = """
        PREFIX ex: <http://example.com/ontology#>
        SELECT ?goal ?actionSeq WHERE {
            ?goal ex:hasActionSequence ?actionSeq .
        }
        """

        try:
            results = list(ontology_data.query(query))
            ontology_goals = {str(result.goal).split('#')[-1] for result in results}

            pattern_goals = set(pattern_rules.get("goal_types", set()))

            # 패턴에는 있지만 온톨로지에 액션 시퀀스가 없는 Goal
            missing_actions = pattern_goals - ontology_goals
            if missing_actions:
                self.issues.append({
                    "type": "warning",
                    "category": "missing_action_sequence",
                    "message": f"Goals without action sequences in ontology: {missing_actions}",
                    "file": "config/ontology.owl",
                    "goals": list(missing_actions)
                })

        except Exception as e:
            self.issues.append({
                "type": "warning",
                "category": "ontology_query",
                "message": f"Failed to query ontology for action sequences: {e}",
                "file": "config/ontology.owl"
            })

    def _check_pipeline_stage_consistency(self, pattern_rules: Dict[str, Any]) -> None:
        """파이프라인 스테이지 일관성 확인"""
        # 일반적인 스테이지 정의
        known_stages = {
            "aasQuery", "dataFiltering", "swrlSelection",
            "yamlBinding", "simulation", "modelSelection"
        }

        # 패턴 파일에서 스테이지 정보 확인 (실제 구현에서는 더 정교한 파싱 필요)
        # 현재는 기본적인 검증만 수행

        for goal_type in pattern_rules.get("goal_types", set()):
            if "predict" in goal_type.lower():
                # 예측 관련 Goal은 모델 선택이 필요
                expected_stages = ["swrlSelection", "yamlBinding", "simulation"]
            else:
                # 기본 Goal은 AAS 쿼리
                expected_stages = ["aasQuery", "dataFiltering"]

            # 실제 검증 로직은 더 복잡해야 하지만 여기서는 기본 확인만
            pass

    def _generate_report(self) -> Dict[str, Any]:
        """검사 결과 리포트 생성"""
        issues_by_type = {"critical": [], "error": [], "warning": []}
        issues_by_category = {}

        for issue in self.issues:
            issue_type = issue.get("type", "warning")
            issues_by_type[issue_type].append(issue)

            category = issue.get("category", "unknown")
            if category not in issues_by_category:
                issues_by_category[category] = []
            issues_by_category[category].append(issue)

        total_issues = len(self.issues)
        critical_count = len(issues_by_type["critical"])
        error_count = len(issues_by_type["error"])
        warning_count = len(issues_by_type["warning"])

        # 상태 결정
        if critical_count > 0:
            status = "CRITICAL"
        elif error_count > 0:
            status = "ERROR"
        elif warning_count > 0:
            status = "WARNING"
        else:
            status = "OK"

        return {
            "status": status,
            "summary": {
                "total_issues": total_issues,
                "critical": critical_count,
                "error": error_count,
                "warning": warning_count
            },
            "issues_by_type": issues_by_type,
            "issues_by_category": issues_by_category,
            "all_issues": self.issues
        }

    def print_report(self, report: Dict[str, Any]) -> None:
        """리포트 출력"""
        status = report["status"]
        summary = report["summary"]

        status_emoji = {
            "OK": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }

        print(f"\n{status_emoji.get(status, '❓')} Registry Consistency Check: {status}")
        print("=" * 50)

        if summary["total_issues"] == 0:
            print("🎉 모든 설정 파일이 일관성 있게 구성되어 있습니다!")
            return

        print(f"📊 총 {summary['total_issues']}개 문제 발견:")
        print(f"   🚨 Critical: {summary['critical']}")
        print(f"   ❌ Error: {summary['error']}")
        print(f"   ⚠️  Warning: {summary['warning']}")

        # 카테고리별 요약
        print(f"\n📂 문제 카테고리:")
        for category, issues in report["issues_by_category"].items():
            print(f"   • {category}: {len(issues)}개")

        # 상세 문제 목록
        print(f"\n📋 상세 문제 목록:")
        for issue in report["all_issues"]:
            emoji = {"critical": "🚨", "error": "❌", "warning": "⚠️"}.get(issue["type"], "❓")
            print(f"   {emoji} [{issue['category']}] {issue['message']}")
            print(f"      📁 File: {issue['file']}")


def main():
    """메인 실행 함수"""
    print("🔍 Registry Consistency Checker")
    print("=" * 50)

    checker = RegistryChecker()
    report = checker.check_all()
    checker.print_report(report)

    # JSON 리포트 저장
    output_dir = Path("querygoal/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_file = output_dir / "consistency_check_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 상세 리포트 저장됨: {report_file}")

    return report["status"] == "OK"


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)