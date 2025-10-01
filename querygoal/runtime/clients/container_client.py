"""
Container Client - Docker 시뮬레이션 실행 (Docker-only)
"""
import asyncio
import json
import logging
import shutil
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
            # Goal3 시나리오 디렉터리 준비
            # Docker 이미지가 기본값으로 "my_case"를 사용하므로 이에 맞춤
            scenario_name = "my_case"
            scenario_dir = work_directory / scenario_name
            scenario_dir.mkdir(exist_ok=True)

            logger.info(f"📁 Creating scenario directory: {scenario_dir}")

            # 파일 매핑 준비 (yamlBinding 출력 -> Docker 컨테이너 기대 형식)
            file_mappings = {
                "JobOrders": "jobs.json",
                "Machines": "machines.json",
                # 추가 필수 파일들은 기본값으로 생성
                "operations": "operations.json",
                "operation_durations": "operation_durations.json",
                "machine_transfer_time": "machine_transfer_time.json",
                "job_release": "job_release.json"
            }

            # yamlBinding에서 생성된 파일들 복사 및 이름 변경
            data_files = input_data.get("data_files", {})
            for source_name, target_name in file_mappings.items():
                if source_name in data_files:
                    # yamlBinding 파일 복사 및 이름 변경
                    source_path = Path(data_files[source_name])
                    if source_path.exists():
                        target_path = scenario_dir / target_name
                        shutil.copy2(source_path, target_path)
                        logger.info(f"📄 Copied {source_name}.json -> {target_name}")
                elif target_name in ["operations.json", "operation_durations.json",
                                     "machine_transfer_time.json", "job_release.json"]:
                    # 필수 파일이 없으면 기본값으로 생성
                    target_path = scenario_dir / target_name
                    await self._create_default_scenario_file(target_name, target_path, data_files)
                    logger.info(f"📄 Created default {target_name}")

            # 결과 디렉터리 준비
            results_dir = work_directory / "results"
            results_dir.mkdir(exist_ok=True)

            # Docker 실행 명령어 구성 (시나리오 디렉터리를 볼륨 마운트)
            docker_cmd = [
                "docker", "run",
                "--rm",  # 컨테이너 자동 삭제
                "-v", f"{scenario_dir}:/app/scenarios/{scenario_name}",  # 시나리오 볼륨 마운트
                "-v", f"{results_dir}:/app/results",  # 결과 디렉터리 마운트
                "-v", f"{work_directory}:/workspace",  # 작업 디렉터리 마운트
                "--name", f"simulation-{execution_id}",
                "-e", f"SCENARIO_NAME={scenario_name}",  # 시나리오 이름 환경변수
                "-e", f"TIME_LIMIT=300",  # 시간 제한
                "-e", f"MAX_NODES=100000",  # 최대 노드 수
                "-e", f"RESULT_PATH=/app/results"  # 결과 경로
            ]

            # 추가 파라미터 환경 변수로 전달
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

    async def _create_default_scenario_file(self,
                                           file_name: str,
                                           target_path: Path,
                                           data_files: Dict[str, Any]):
        """Goal3 시뮬레이션에 필요한 기본 시나리오 파일 생성"""

        # JobOrders와 Machines 데이터 로드
        jobs_data = []
        machines_data = []

        if "JobOrders" in data_files:
            jobs_path = Path(data_files["JobOrders"])
            if jobs_path.exists():
                with open(jobs_path, 'r', encoding='utf-8') as f:
                    jobs_data = json.load(f)

        if "Machines" in data_files:
            machines_path = Path(data_files["Machines"])
            if machines_path.exists():
                with open(machines_path, 'r', encoding='utf-8') as f:
                    machines_data = json.load(f)

        # 파일별 기본 데이터 생성
        default_data = {}

        if file_name == "operations.json":
            # JobOrders에서 operations 추출
            operations = set()
            for job in jobs_data:
                for op in job.get("operations", []):
                    operations.add(op)
            default_data = list(operations) if operations else ["drilling", "welding", "testing", "painting"]

        elif file_name == "operation_durations.json":
            # 기본 operation duration 매트릭스
            operations = ["drilling", "welding", "testing", "painting"]
            machine_types = ["CNC", "WeldingRobot", "VisionInspector", "PaintingRobot"]
            duration_matrix = {}

            for op in operations:
                duration_matrix[op] = {}
                for m_type in machine_types:
                    # 특정 머신이 특정 작업에 특화된 시간 설정
                    if (op == "drilling" and m_type == "CNC") or \
                       (op == "welding" and m_type == "WeldingRobot") or \
                       (op == "testing" and m_type == "VisionInspector") or \
                       (op == "painting" and m_type == "PaintingRobot"):
                        duration_matrix[op][m_type] = 5  # 특화 작업은 빠름
                    else:
                        duration_matrix[op][m_type] = 99999  # 불가능한 작업

            default_data = duration_matrix

        elif file_name == "machine_transfer_time.json":
            # 머신 간 이동 시간 매트릭스
            machine_ids = [m["id"] for m in machines_data] if machines_data else ["M1", "M2", "M3", "M4"]
            transfer_matrix = {}

            for m1 in machine_ids:
                transfer_matrix[m1] = {}
                for m2 in machine_ids:
                    if m1 == m2:
                        transfer_matrix[m1][m2] = 0
                    else:
                        # 인접 머신은 1, 멀리 있는 머신은 2-3
                        m1_idx = machine_ids.index(m1)
                        m2_idx = machine_ids.index(m2)
                        distance = abs(m1_idx - m2_idx)
                        transfer_matrix[m1][m2] = min(distance, 3)

            default_data = transfer_matrix

        elif file_name == "job_release.json":
            # Job release 시간 정보
            release_times = {}
            for i, job in enumerate(jobs_data):
                job_id = job.get("job_id", f"JOB{i:03d}")
                # 순차적으로 release time 설정
                release_times[job_id] = i * 2
            default_data = release_times if release_times else {"JOB001": 0, "JOB002": 5}

        # 파일 저장
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)