"""
Container Client - Docker 시뮬레이션 실행 (Docker-only)
"""
import asyncio
import json
import logging
import uuid
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

from ..exceptions import SimulationExecutionError

logger = logging.getLogger("querygoal.container_client")


class ContainerClient:
    """컨테이너 실행 클라이언트 (Docker-only)"""

    def __init__(self, execution_mode: str = "docker"):
        self.execution_mode = execution_mode  # "docker" only

    async def run_simulation(self,
                           image: str,
                           input_data: Dict[str, Any],
                           work_directory: Path,
                           goal_id: str) -> Dict[str, Any]:
        """시뮬레이션 컨테이너 실행"""

        execution_id = f"{goal_id}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()

        logger.info(f"🚀 Starting simulation container: {image}")
        logger.info(f"📋 Execution ID: {execution_id}")

        try:
            if self.execution_mode == "docker":
                result = await self._run_docker_container(
                    image, input_data, work_directory, execution_id
                )
            else:
                raise SimulationExecutionError(
                    "Kubernetes execution is not currently supported. Use Docker (execution_mode=docker)"
                )

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            result.update({
                "execution_id": execution_id,
                "execution_time": execution_time,
                "start_time": start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat()
            })

            logger.info(f"✅ Simulation completed in {execution_time:.2f}s")
            return result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"❌ Simulation failed after {execution_time:.2f}s: {e}")
            raise SimulationExecutionError(f"Container execution failed: {e}") from e

    async def _run_docker_container(self,
                                  image: str,
                                  input_data: Dict[str, Any],
                                  work_directory: Path,
                                  execution_id: str) -> Dict[str, Any]:
        """Docker 컨테이너 실행"""

        try:
            # Docker 실행 명령어 구성 (환경변수는 이미지 이름 앞에 위치)
            docker_cmd = [
                "docker", "run",
                "--rm",  # 컨테이너 자동 삭제
                "-v", f"{work_directory}:/workspace",  # 볼륨 마운트
                "--name", f"simulation-{execution_id}"
            ]

            # 환경 변수로 입력 데이터 전달 (이미지 이름 앞에 추가)
            for key, value in input_data.get("parameters", {}).items():
                docker_cmd.extend(["-e", f"{key.upper()}={value}"])

            # 이미지 이름은 마지막에 추가
            docker_cmd.append(image)

            logger.info(f"🐳 Docker command: {' '.join(docker_cmd)}")

            # 비동기 프로세스 실행
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_directory
            )

            stdout, stderr = await process.communicate()

            # 결과 저장
            logs_file = work_directory / f"container_logs_{execution_id}.txt"
            with open(logs_file, 'w', encoding='utf-8') as f:
                f.write(f"=== STDOUT ===\n{stdout.decode('utf-8', errors='replace')}\n")
                f.write(f"=== STDERR ===\n{stderr.decode('utf-8', errors='replace')}\n")

            if process.returncode != 0:
                raise SimulationExecutionError(
                    f"Docker container failed with exit code {process.returncode}: "
                    f"{stderr.decode('utf-8', errors='replace')}"
                )

            # 출력 결과 파싱 시도
            output_data = {}
            try:
                stdout_str = stdout.decode('utf-8', errors='replace')
                for line in stdout_str.split('\n'):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        output_data = json.loads(line)
                        break
            except json.JSONDecodeError:
                output_data = {"raw_output": stdout.decode('utf-8', errors='replace')}

            return {
                "execution_mode": "docker",
                "container_image": image,
                "exit_code": process.returncode,
                "output": output_data,
                "logs_path": str(logs_file)
            }

        except Exception as e:
            raise SimulationExecutionError(f"Docker execution failed: {e}") from e