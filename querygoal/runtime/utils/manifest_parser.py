"""
Manifest Parser
YAML 메니페스트 파일 파싱 및 검증
"""
import logging
import yaml
from pathlib import Path
from typing import Dict, Any

from ..exceptions import ManifestParsingError

logger = logging.getLogger("querygoal.manifest_parser")


class ManifestParser:
    """YAML 메니페스트 파서"""

    async def parse_manifest(self, manifest_path: Path) -> Dict[str, Any]:
        """
        메니페스트 파일 파싱

        Args:
            manifest_path: YAML 메니페스트 파일 경로

        Returns:
            파싱된 메니페스트 데이터
        """
        try:
            if not manifest_path.exists():
                raise ManifestParsingError(f"Manifest file not found: {manifest_path}")

            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = yaml.safe_load(f)

            # 기본 구조 검증
            if not isinstance(manifest_data, dict):
                raise ManifestParsingError("Manifest must be a dictionary")

            # data_sources 필드 확인 (snake_case)
            if "data_sources" not in manifest_data:
                raise ManifestParsingError("Manifest must contain 'data_sources' field")

            # 각 데이터 소스 검증
            data_sources = manifest_data["data_sources"]
            if not isinstance(data_sources, list):
                raise ManifestParsingError("'data_sources' must be a list")

            for idx, source in enumerate(data_sources):
                self._validate_data_source(source, idx)

            logger.info(f"Parsed manifest: {len(data_sources)} data sources")
            return manifest_data

        except yaml.YAMLError as e:
            raise ManifestParsingError(f"YAML parsing error: {e}") from e
        except Exception as e:
            raise ManifestParsingError(f"Failed to parse manifest: {e}") from e

    def _validate_data_source(self, source: Dict[str, Any], index: int):
        """개별 데이터 소스 검증"""
        required_fields = ["name", "type", "config"]

        for field in required_fields:
            if field not in source:
                raise ManifestParsingError(
                    f"Data source {index} missing required field: {field}"
                )

        # 소스 타입 검증
        valid_types = ["aas_property", "aas_shell_collection", "local_file", "api_endpoint"]
        source_type = source["type"]
        if source_type not in valid_types:
            raise ManifestParsingError(
                f"Data source {index} has invalid type: {source_type}. "
                f"Valid types: {valid_types}"
            )

        # required 필드 검증 (있는 경우)
        if "required" in source and not isinstance(source["required"], bool):
            raise ManifestParsingError(
                f"Data source {index} 'required' field must be boolean"
            )

        # 타입별 config 검증
        config = source["config"]
        if source_type == "aas_property":
            if "submodel_id" not in config or "property_path" not in config:
                raise ManifestParsingError(
                    f"Data source {index} (aas_property) must have "
                    "'submodel_id' and 'property_path' in config"
                )

        elif source_type == "aas_shell_collection":
            if "combination_rules" not in config:
                raise ManifestParsingError(
                    f"Data source {index} (aas_shell_collection) must have "
                    "'combination_rules' in config"
                )

            # combination_rules 검증
            rules = config["combination_rules"]
            if not isinstance(rules, list):
                raise ManifestParsingError(
                    f"Data source {index} 'combination_rules' must be a list"
                )

            for rule_idx, rule in enumerate(rules):
                if "type" not in rule:
                    raise ManifestParsingError(
                        f"Data source {index} combination_rule {rule_idx} missing 'type'"
                    )

                # submodel_property 타입 검증
                if rule["type"] == "submodel_property":
                    required_rule_fields = ["submodel_id", "property_path", "result_key"]
                    for field in required_rule_fields:
                        if field not in rule:
                            raise ManifestParsingError(
                                f"Data source {index} combination_rule {rule_idx} "
                                f"(submodel_property) missing '{field}'"
                            )