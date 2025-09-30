"""
Simulation Handler
Goal3의 simulation 단계 - Docker 시뮬레이션 실행
"""
import json
from typing import Dict, Any
from pathlib import Path

from .base_handler import BaseHandler
from ..clients.container_client import ContainerClient
from ..exceptions import SimulationExecutionError


class SimulationHandler(BaseHandler):
    """시뮬레이션 실행 핸들러"""

    def __init__(self):
        super().__init__()
        self.container_client = ContainerClient()

    async def execute(self,
                     querygoal: Dict[str, Any],
                     context: 'ExecutionContext') -> Dict[str, Any]:
        """Simulation 실행"""

        await self.pre_execute(querygoal, context)

        if not self.validate_prerequisites(querygoal, context):
            return self.create_error_result("Prerequisites validation failed")

        try:
            qg = querygoal["QueryGoal"]
            selected_model = qg.get("selectedModel", {})

            # 컨테이너 이미지 정보 추출 (container.image 구조 사용)
            container_info = selected_model.get("container", {})
            container_image = container_info.get("image")

            if not container_image:
                return self.create_error_result("Container image not specified in selected model")

            # 이전 단계에서 생성된 JSON 파일들 확인
            yaml_binding_result = context.stage_results.get("yamlBinding", {})
            json_files = yaml_binding_result.get("jsonFiles", {})

            if not json_files:
                return self.create_error_result("No JSON files found from yamlBinding stage")

            # 시뮬레이션 입력 준비
            simulation_input = await self._prepare_simulation_input(
                qg, json_files, context.work_directory
            )

            # 컨테이너 실행
            self.logger.info(f"🚀 Starting simulation with container: {container_image}")

            execution_result = await self.container_client.run_simulation(
                image=container_image,
                input_data=simulation_input,
                work_directory=context.work_directory,
                goal_id=context.goal_id
            )

            # 시뮬레이션 결과 파싱
            simulation_output = await self._parse_simulation_output(
                execution_result, context.work_directory
            )

            # QueryGoal outputs 업데이트
            await self._update_querygoal_outputs(qg, simulation_output)

            result_data = {
                "containerImage": container_image,
                "executionId": execution_result.get("execution_id"),
                "status": "completed",
                "simulationOutput": simulation_output,
                "executionTime": execution_result.get("execution_time"),
                "containerLogs": execution_result.get("logs_path")
            }

            await self.post_execute(result_data, context)
            return self.create_success_result(result_data)

        except Exception as e:
            self.logger.error(f"Simulation execution failed: {e}")
            return self.create_error_result(
                f"Simulation execution failed: {e}",
                {"container_image": container_image if 'container_image' in locals() else None}
            )

    async def _prepare_simulation_input(self,
                                       qg: Dict[str, Any],
                                       json_files: Dict[str, Any],
                                       work_directory: Path) -> Dict[str, Any]:
        """시뮬레이션 입력 데이터 준비"""

        try:
            # QueryGoal 파라미터 추출
            parameters = {}
            for param in qg.get("parameters", []):
                parameters[param["key"]] = param["value"]

            # JSON 파일 경로 목록 생성
            data_files = {}
            for file_name, file_info in json_files.items():
                if "path" in file_info:  # 성공적으로 생성된 파일만
                    data_files[file_name] = file_info["path"]

            simulation_input = {
                "goal_id": qg["goalId"],
                "goal_type": qg["goalType"],
                "parameters": parameters,
                "data_files": data_files,
                "work_directory": str(work_directory)
            }

            # 시뮬레이션 입력 파일 저장
            input_file = work_directory / "simulation_input.json"
            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(simulation_input, f, indent=2, ensure_ascii=False)

            self.logger.info(f"📄 Simulation input prepared: {input_file}")
            return simulation_input

        except Exception as e:
            raise SimulationExecutionError(f"Failed to prepare simulation input: {e}") from e

    async def _parse_simulation_output(self,
                                      execution_result: Dict[str, Any],
                                      work_directory: Path) -> Dict[str, Any]:
        """시뮬레이션 출력 결과 파싱"""

        try:
            # 시뮬레이션 출력 파일 찾기
            output_files = ["simulation_output.json", "goal3_result.json", "result.json"]

            simulation_output = None
            for output_file in output_files:
                output_path = work_directory / output_file
                if output_path.exists():
                    with open(output_path, 'r', encoding='utf-8') as f:
                        simulation_output = json.load(f)
                    break

            if simulation_output is None:
                # 컨테이너 실행 결과에서 직접 추출
                simulation_output = execution_result.get("output", {})

            # Goal3 특화 결과 구조 확인
            if "goal3_data" in simulation_output:
                goal3_data = simulation_output["goal3_data"]
                return {
                    "predicted_completion_time": goal3_data.get("predicted_completion_time"),
                    "confidence": goal3_data.get("confidence", 0.95),
                    "simulator_type": goal3_data.get("simulator_type", "NSGA-II"),
                    "detailed_results": goal3_data.get("detailed_results", {}),
                    "execution_metadata": simulation_output.get("execution_metadata", {})
                }
            else:
                return simulation_output

        except Exception as e:
            raise SimulationExecutionError(f"Failed to parse simulation output: {e}") from e

    async def _update_querygoal_outputs(self,
                                       qg: Dict[str, Any],
                                       simulation_output: Dict[str, Any]):
        """QueryGoal outputs 필드 업데이트 (Goal3 outputSpec에 맞춰 매핑)"""

        try:
            if "outputs" not in qg:
                qg["outputs"] = {}

            # Goal3 outputSpec 매핑: estimatedTime, confidence, productionPlan, bottlenecks
            qg["outputs"].update({
                # predicted_completion_time → estimatedTime
                "estimatedTime": simulation_output.get("predicted_completion_time"),

                # confidence는 동일
                "confidence": simulation_output.get("confidence"),

                # detailed_results → productionPlan
                "productionPlan": simulation_output.get("detailed_results", {}),

                # bottlenecks 필드
                "bottlenecks": simulation_output.get("bottlenecks",
                                                   simulation_output.get("detailed_results", {}).get("bottlenecks", []))
            })

            self.logger.info("📤 QueryGoal outputs updated with Goal3 outputSpec mapping")

        except Exception as e:
            self.logger.warning(f"Failed to update QueryGoal outputs: {e}")

    def validate_prerequisites(self,
                              querygoal: Dict[str, Any],
                              context: 'ExecutionContext') -> bool:
        """Simulation 전제조건 검증"""

        if not super().validate_prerequisites(querygoal, context):
            return False

        # 이전 단계들이 완료되었는지 확인
        required_stages = ["swrlSelection", "yamlBinding"]
        for stage in required_stages:
            if stage not in context.stage_results:
                self.logger.error(f"Required stage '{stage}' must be completed first")
                return False

        # 컨테이너 이미지 확인
        qg = querygoal["QueryGoal"]
        selected_model = qg.get("selectedModel", {})
        container_info = selected_model.get("container", {})
        container_image = container_info.get("image")

        if not container_image:
            self.logger.error("Container image not specified in selected model")
            return False

        return True