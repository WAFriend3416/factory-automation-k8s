"""
SWRL Selection Handler
Goal3의 swrlSelection 단계를 처리
"""
from typing import Dict, Any
from pathlib import Path

from .base_handler import BaseHandler
from ..exceptions import StageExecutionError


class SwrlSelectionHandler(BaseHandler):
    """SWRL 기반 모델 선택 핸들러"""

    def __init__(self):
        super().__init__()

    async def execute(self,
                     querygoal: Dict[str, Any],
                     context: 'ExecutionContext') -> Dict[str, Any]:
        """SWRL Selection 실행"""

        await self.pre_execute(querygoal, context)

        if not self.validate_prerequisites(querygoal, context):
            return self.create_error_result("Prerequisites validation failed")

        try:
            qg = querygoal["QueryGoal"]
            goal_type = qg["goalType"]

            # 이미 선택된 모델이 있는지 확인
            selected_model = qg.get("selectedModel")
            if not selected_model:
                return self.create_error_result(
                    f"No model selected for {goal_type}. SWRL selection should have been performed in pipeline."
                )

            self.logger.info(f"📦 Model already selected: {selected_model.get('modelId')}")

            # 메니페스트 경로 확인
            manifest_path = await self._load_model_manifest(selected_model, context)

            result_data = {
                "selectedModel": selected_model,
                "manifestPath": str(manifest_path),
                "selectionMethod": "pre_selected",
                "modelStatus": "ready"
            }

            await self.post_execute(result_data, context)
            return self.create_success_result(result_data)

        except Exception as e:
            self.logger.error(f"SWRL Selection failed: {e}")
            return self.create_error_result(
                f"SWRL Selection failed: {e}",
                {"goal_type": goal_type}
            )

    async def _load_model_manifest(self,
                                  selected_model: Dict[str, Any],
                                  context: 'ExecutionContext') -> Path:
        """모델 메니페스트 파일 로드"""

        try:
            # 최상위 레벨에서 metaDataFile 확인 (metadata 중첩 없음)
            metadata_file = selected_model.get("metaDataFile")

            # MetaData 키 변형도 확인
            if not metadata_file:
                metadata_file = selected_model.get("MetaData")

            if not metadata_file:
                raise StageExecutionError("Model metadata file not specified")

            # 메니페스트 파일 경로 결정
            if metadata_file.startswith("/"):
                manifest_path = Path(metadata_file)
            else:
                # 상대 경로 - config 디렉터리에서 찾기
                config_dir = Path(__file__).parent.parent.parent.parent / "config"
                manifest_path = config_dir / metadata_file

            # 파일 존재 확인
            if not manifest_path.exists():
                raise StageExecutionError(f"Manifest file not found: {manifest_path}")

            self.logger.info(f"📋 Loaded manifest: {manifest_path}")
            return manifest_path

        except Exception as e:
            raise StageExecutionError(f"Failed to load model manifest: {e}") from e

    def validate_prerequisites(self,
                              querygoal: Dict[str, Any],
                              context: 'ExecutionContext') -> bool:
        """SWRL Selection 전제조건 검증"""

        if not super().validate_prerequisites(querygoal, context):
            return False

        qg = querygoal["QueryGoal"]

        # Goal3에만 적용 가능한지 확인
        if not qg.get("goalType", "").startswith("goal3"):
            self.logger.error("SWRL Selection is only applicable to Goal3")
            return False

        return True