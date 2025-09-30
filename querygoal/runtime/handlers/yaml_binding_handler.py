"""
YAML Binding Handler
Goal3의 yamlBinding 단계 - AAS 서버에서 데이터 수집 및 JSON 파일 생성
"""
import json
from typing import Dict, Any, List
from pathlib import Path

from .base_handler import BaseHandler
from ..clients.aas_client import AASClient
from ..utils.manifest_parser import ManifestParser
from ..exceptions import StageExecutionError, AASConnectionError


class YamlBindingHandler(BaseHandler):
    """YAML 메니페스트 기반 데이터 바인딩 핸들러"""

    def __init__(self):
        super().__init__()
        self.aas_client = AASClient()
        self.manifest_parser = ManifestParser()

    async def execute(self,
                     querygoal: Dict[str, Any],
                     context: 'ExecutionContext') -> Dict[str, Any]:
        """YAML Binding 실행"""

        await self.pre_execute(querygoal, context)

        if not self.validate_prerequisites(querygoal, context):
            return self.create_error_result("Prerequisites validation failed")

        try:
            qg = querygoal["QueryGoal"]

            # 이전 단계에서 생성된 메니페스트 경로 확인
            manifest_path = context.stage_results.get("swrlSelection", {}).get("manifestPath")
            if not manifest_path:
                return self.create_error_result("Manifest path not found from previous stage")

            # 메니페스트 파싱
            self.logger.info(f"📋 Parsing manifest: {manifest_path}")
            manifest_data = await self.manifest_parser.parse_manifest(Path(manifest_path))

            # 데이터 소스 목록 추출
            data_sources = manifest_data.get("data_sources", [])
            if not data_sources:
                return self.create_error_result("No data sources found in manifest")

            # 작업 디렉터리에 JSON 파일 생성
            json_files = {}
            success_count = 0

            # Required/Optional 소스 분류
            required_sources = [s for s in data_sources if s.get("required", True)]
            optional_sources = [s for s in data_sources if not s.get("required", True)]

            required_count = len(required_sources)
            required_success = 0

            for source in data_sources:
                try:
                    source_name = source["name"]
                    source_type = source["type"]
                    is_required = source.get("required", True)

                    self.logger.info(f"🔍 Processing data source: {source_name} (required={is_required})")

                    if source_type == "aas_property":
                        json_data = await self._fetch_aas_property_data(source)
                    elif source_type == "aas_shell_collection":
                        json_data = await self._fetch_aas_shell_collection(source)
                    else:
                        raise StageExecutionError(f"Unknown data source type: {source_type}")

                    # JSON 파일 저장
                    json_file_path = context.work_directory / f"{source_name}.json"
                    with open(json_file_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)

                    json_files[source_name] = {
                        "path": str(json_file_path),
                        "size": json_file_path.stat().st_size,
                        "record_count": len(json_data) if isinstance(json_data, list) else 1
                    }

                    success_count += 1
                    if is_required:
                        required_success += 1

                    self.logger.info(f"✅ Created {source_name}.json")

                except Exception as e:
                    self.logger.error(f"❌ Failed to process {source.get('name', 'unknown')}: {e}")
                    json_files[source.get('name', 'unknown')] = {"error": str(e)}

            # 전체 성공률 및 필수 소스 성공률 계산
            total_sources = len(data_sources)
            success_rate = success_count / total_sources if total_sources > 0 else 0
            required_success_rate = required_success / required_count if required_count > 0 else 0

            result_data = {
                "manifestPath": manifest_path,
                "totalDataSources": total_sources,
                "successfulSources": success_count,
                "success_rate": success_rate,
                # Required-flag filtering 정보
                "required_sources_count": required_count,
                "optional_sources_count": len(optional_sources),
                "required_success_count": required_success,
                "required_success_rate": required_success_rate,
                "jsonFiles": json_files,
                "workDirectory": str(context.work_directory)
            }

            await self.post_execute(result_data, context)
            return self.create_success_result(result_data)

        except Exception as e:
            self.logger.error(f"YAML Binding failed: {e}")
            return self.create_error_result(
                f"YAML Binding failed: {e}",
                {"work_directory": str(context.work_directory)}
            )

    async def _fetch_aas_property_data(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """AAS Property에서 데이터 수집"""
        submodel_id = source["config"]["submodel_id"]
        property_path = source["config"]["property_path"]

        try:
            property_data = await self.aas_client.get_submodel_property(
                submodel_id, property_path
            )

            if isinstance(property_data, str):
                return json.loads(property_data)
            elif isinstance(property_data, (list, dict)):
                return property_data
            else:
                return [{"value": property_data}]

        except Exception as e:
            raise AASConnectionError(f"Failed to fetch AAS property {property_path}: {e}") from e

    async def _fetch_aas_shell_collection(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """AAS Shell 컬렉션에서 데이터 수집"""
        shell_filter = source["config"].get("shell_filter", {})
        combination_rules = source["config"].get("combination_rules", [])

        try:
            shells = await self.aas_client.list_shells()

            filtered_shells = []
            for shell in shells:
                if self._matches_shell_filter(shell, shell_filter):
                    filtered_shells.append(shell)

            combined_data = []
            for shell in filtered_shells:
                shell_data = await self._apply_combination_rules(shell, combination_rules)
                combined_data.append(shell_data)

            self.logger.info(f"📦 Collected {len(combined_data)} records from {len(shells)} shells")
            return combined_data

        except Exception as e:
            raise AASConnectionError(f"Failed to fetch AAS shell collection: {e}") from e

    def _matches_shell_filter(self, shell: Dict[str, Any], filter_config: Dict[str, Any]) -> bool:
        """Shell이 필터 조건에 맞는지 확인"""
        if "id_pattern" in filter_config:
            shell_id = shell.get("idShort", "")
            pattern = filter_config["id_pattern"]
            if pattern not in shell_id:
                return False
        return True

    async def _apply_combination_rules(self, shell: Dict[str, Any], rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """조합 규칙을 적용하여 최종 데이터 구조 생성"""
        result = {
            "shell_id": shell.get("idShort"),
            "shell_identification": shell.get("identification", {})
        }

        for rule in rules:
            rule_type = rule.get("type")

            if rule_type == "submodel_property":
                submodel_id = rule["submodel_id"]
                property_path = rule["property_path"]
                result_key = rule["result_key"]

                try:
                    property_value = await self.aas_client.get_submodel_property(
                        submodel_id, property_path, shell_id=shell.get("idShort")
                    )
                    result[result_key] = property_value
                except Exception as e:
                    self.logger.warning(f"Failed to get property {property_path}: {e}")
                    result[result_key] = None

        return result

    def validate_prerequisites(self,
                              querygoal: Dict[str, Any],
                              context: 'ExecutionContext') -> bool:
        """YAML Binding 전제조건 검증"""
        if not super().validate_prerequisites(querygoal, context):
            return False

        if "swrlSelection" not in context.stage_results:
            self.logger.error("swrlSelection stage must be completed first")
            return False

        return True