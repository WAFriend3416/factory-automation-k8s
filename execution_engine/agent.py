# execution_engine/agent.py
import requests, sys, time, json, uuid, base64
from pathlib import Path
from kubernetes import client, config

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import AAS_SERVER_URL

# --- 핸들러 클래스들 ---
class AASQueryHandler:
    def _to_base64url(self, s: str) -> str: return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")
    def execute(self, step_details: dict, context: dict) -> dict:
        params = step_details.get('params', {})
        goal = params.get('goal')
        action_id = step_details.get('action_id')
        
        # ActionFetchAllMachineData 같은 복합 조회를 위한 로직
        if action_id == 'ActionFetchAllMachineData':
            # 실제로는 모든 기계의 Capability/Status Submodel을 조회해야 함
            # 프로토타입에서는 대표로 하나의 데이터만 조회하여 반환
            print("INFO: Simulating fetch of all machine data.")
            sm_id = "urn:factory:submodel:capability:cnc-01"
            b64id = self._to_base64url(sm_id)
            url = f"{AAS_SERVER_URL}/submodels/{b64id}"
        else:
            target_sm_id = step_details.get('target_submodel_id')
            if not target_sm_id:
                if goal == 'track_product_position': target_sm_id = f"urn:factory:submodel:tracking_data:{params['product_id'].lower()}"
                elif goal == 'detect_anomaly_for_product': target_sm_id = f"urn:factory:submodel:sensor_data:{params['target_machine'].lower()}"
                else: raise ValueError(f"Cannot determine target for goal: {goal}")
            b64id = self._to_base64url(target_sm_id)
            url = f"{AAS_SERVER_URL}/submodels/{b64id}"

        print(f"INFO: Requesting AAS data from: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

class SimulationInputHandler:
    """여러 소스의 데이터를 조합하여 시뮬레이터 입력 파일을 생성하는 핸들러"""
    def execute(self, step_details: dict, context: dict) -> dict:
        params = step_details.get('params', {})
        job_id = str(uuid.uuid4())  # 로깅 및 추적용으로 유지
        
        # 고정된 경로 사용 - 모든 시뮬레이션이 같은 경로 사용
        shared_dir = Path("/data")
        current_dir = shared_dir / "current"
        current_dir.mkdir(parents=True, exist_ok=True)
        
        # 컨텍스트에서 이전 단계들의 결과 수집
        input_data = {
            "process_spec": context.get("step_1_ActionFetchProductSpec", {}),
            "machine_data": context.get("step_2_ActionFetchAllMachineData", {}),
            "order": params,
            "job_id": job_id  # 추적용 ID 포함
        }

        # 고정 경로에 입력 파일 작성 (덮어쓰기)
        input_file_path = current_dir / "simulation_inputs.json"
        with open(input_file_path, 'w') as f:
            json.dump(input_data, f, indent=2)

        print(f"INFO: Created simulation input file at {input_file_path} (job_id: {job_id})")
        # 다음 Job 생성 단계에 필요한 작업 ID 반환
        return {"simulation_job_id": job_id}

class K8sJobHandler: # 이전 DockerRunHandler의 새 이름
    """쿠버네티스 클러스터에 시뮬레이터 Job을 생성하고 결과를 받아오는 핸들러"""
    def __init__(self):
        try: config.load_incluster_config()
        except config.ConfigException: config.load_kube_config()
        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()
        self.namespace = "default"

    def execute(self, step_details: dict, context: dict) -> dict:
        # 이전 단계(SimulationInputHandler)에서 생성한 작업 ID와 경로를 가져옴
        sim_context = context.get("step_3_ActionAssembleSimulatorInputs", {})
        job_id = sim_context.get("simulation_job_id")
        if not job_id: raise ValueError("Simulation Job ID not found in context.")
        
        job_name = f"simulator-job-{job_id[:6]}"
        
        # 공유 볼륨(PVC)을 Job의 Pod에 마운트 - 전체 /data 디렉토리 마운트
        volume_mount = client.V1VolumeMount(
            name="shared-data-volume", 
            mount_path="/data"  # 전체 /data 볼륨을 그대로 마운트
        )
        volume = client.V1Volume(
            name="shared-data-volume",
            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name="factory-shared-pvc")
        )

        container = client.V1Container(
            name="simulator", image="simulator:latest", image_pull_policy="Never",
            volume_mounts=[volume_mount] # 컨테이너에 볼륨 마운트
        )
        pod_spec = client.V1PodSpec(restart_policy="Never", containers=[container], volumes=[volume])
        pod_template = client.V1PodTemplateSpec(metadata=client.V1ObjectMeta(labels={"app": "simulator"}), spec=pod_spec)
        job_spec = client.V1JobSpec(template=pod_template, backoff_limit=1)
        job = client.V1Job(api_version="batch/v1", kind="Job", metadata=client.V1ObjectMeta(name=job_name), spec=job_spec)

        print(f"INFO: Creating Kubernetes Job: {job_name}")
        self.batch_v1.create_namespaced_job(body=job, namespace=self.namespace)

        print("INFO: Waiting for Job to complete...")
        job_completed = False
        while not job_completed:
            time.sleep(2)
            job_status = self.batch_v1.read_namespaced_job_status(name=job_name, namespace=self.namespace)
            if job_status.status.succeeded is not None and job_status.status.succeeded >= 1: job_completed = True
        print("INFO: Job completed successfully.")

        # ▼▼▼▼▼ 로그 수집 로직 수정 ▼▼▼▼▼
        pod_label_selector = f"job-name={job_name}"
        pods_list = self.core_v1.list_namespaced_pod(namespace=self.namespace, label_selector=pod_label_selector)
        if not pods_list.items:
            raise RuntimeError(f"Could not find completed pod for job {job_name}")
        pod_name = pods_list.items[0].metadata.name
        
        result = None
        # 로그가 준비될 때까지 최대 5번, 1초 간격으로 재시도
        for i in range(5):
            print(f"INFO: Attempting to fetch logs for pod {pod_name} (Attempt {i+1}/5)")
            time.sleep(1) # 로그가 집계될 시간을 벌어줌
            pod_log = self.core_v1.read_namespaced_pod_log(name=pod_name, namespace=self.namespace)
            
            if pod_log:
                # Parse JSON from the log output - find the line that starts with {
                for line in pod_log.split('\n'):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            result = json.loads(line)
                            print("INFO: Successfully fetched and parsed logs.")
                            break # 성공하면 내부 루프 탈출
                        except json.JSONDecodeError:
                            print(f"WARN: Could not parse line as JSON: {line}")
                            continue # 파싱 실패 시 다음 줄 시도
                
                if result:
                    break # 결과를 찾았으면 외부 루프도 탈출
                else:
                    print(f"WARN: No valid JSON found in log. Full log: {pod_log[:200]}...")
            else:
                print("WARN: Pod log is empty. Retrying...")

        if result is None:
            raise RuntimeError(f"Failed to retrieve valid JSON result from pod {pod_name} after multiple attempts.")
        # ▲▲▲▲▲ 여기까지 수정 ▲▲▲▲▲

        self.batch_v1.delete_namespaced_job(name=job_name, namespace=self.namespace, body=client.V1DeleteOptions())
        print(f"INFO: Deleted Job: {job_name}")

        # 공유 드라이브의 임시 파일 정리
        # import shutil; shutil.rmtree(Path(sim_context["shared_dir_path"]) / job_id)

        return {"final_result": result}

class DataFilteringHandler:
    """AAS에서 가져온 데이터를 DSL 조건에 맞게 필터링하거나 가공하는 핸들러"""
    def execute(self, step_details: dict, context: dict) -> dict:
        params = step_details.get('params', {})
        goal = params.get('goal')
        
        # Goal 1: 실패한 냉각 Job 필터링 로직
        if goal == 'query_failed_jobs_with_cooling':
            data_to_filter = None
            for key, value in context.items():
                if 'ActionFetchJobLog' in key:
                    data_to_filter = value.get('submodelElements', [{}])[0].get('value', [])
                    break
            
            if data_to_filter is None:
                raise ValueError("Could not find data from previous step for Goal 1.")

            request_date = params.get('date')
            filtered_jobs = [
                job for job in data_to_filter
                if job.get('date') == request_date
                and job.get('status') == 'FAILED'
                and 'cooling' in job.get('process_steps', [])
            ]
            return {"final_result": filtered_jobs}
        
        # Goal 4: 제품 위치 추적 로직
        elif goal == 'track_product_position':
            tracking_data = None
            # 컨텍스트에서 ActionFetchTrackingData의 실행 결과를 찾습니다.
            for key, value in context.items():
                if 'ActionFetchTrackingData' in key:
                    # TrackingData Submodel의 Position 정보를 추출합니다.
                    tracking_data = value.get('submodelElements', [{}])[0].get('value', {})
                    break
            
            if tracking_data is None:
                raise ValueError("Could not find tracking data from previous step for Goal 4.")

            # Goal 4는 특별한 필터링 없이 조회된 위치 정보를 그대로 최종 결과로 반환합니다.
            return {"final_result": tracking_data}
        
        # 어떤 조건에도 해당하지 않을 경우
        return {"final_result": "No applicable filter or processing logic for this goal."}

class AIModelHandler:
    def execute(self, step_details: dict, context: dict) -> dict:
        print("INFO: AI Model Handler (Not Implemented)")
        return {"result": "AI model placeholder"}

# --- ExecutionAgent 최종본 ---
class ExecutionAgent:
    def __init__(self):
        self.handlers = {
            "aas_query": AASQueryHandler(),
            "aas_query_multiple": AASQueryHandler(),
            "internal_processing": SimulationInputHandler(),
            "docker_run": K8sJobHandler(), # docker_run 타입을 K8sJobHandler가 처리
            "data_filtering": DataFilteringHandler(),
            "ai_model_inference": AIModelHandler(),
        }
    def run(self, plan: list, initial_params: dict) -> dict:
        execution_context = {}
        final_result = {}
        
        for i, step in enumerate(plan):
            step['params'] = initial_params

            action_type = step.get("type")
            handler = self.handlers.get(action_type)

            if not handler:
                print(f"WARN: No handler for action type '{action_type}', skipping.")
                continue
            
            step_result = handler.execute(step, execution_context)
            
            execution_context[f"step_{i+1}_{step['action_id']}"] = step_result

            if "final_result" in step_result:
                final_result = step_result

        return final_result if final_result else execution_context