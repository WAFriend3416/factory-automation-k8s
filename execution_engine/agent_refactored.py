# execution_engine/agent_refactored.py
"""
리팩토링된 Agent 모듈 - Mock과 Standard AAS 서버 모두 지원
Mock 서버와의 기존 호환성을 유지하면서 표준 서버 지원 추가
"""
import requests, sys, time, json, uuid, base64
from pathlib import Path
from typing import Dict, Any, Optional
from kubernetes import client, config as k8s_config

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import (
    AAS_SERVER_URL, 
    AAS_SERVER_IP, 
    AAS_SERVER_PORT, 
    AAS_SERVER_TYPE,
    USE_STANDARD_SERVER
)

# 표준 서버를 사용할 경우에만 AASQueryClient 임포트
if USE_STANDARD_SERVER:
    from aas_query_client import AASQueryClient

# --- 핸들러 클래스들 ---

class AASQueryHandler:
    """
    AAS 서버에 데이터를 요청하는 핸들러
    Mock과 Standard 서버 모두 지원
    """
    def __init__(self):
        self.server_type = AAS_SERVER_TYPE
        
        if USE_STANDARD_SERVER:
            # 표준 서버 사용 시 AASQueryClient 인스턴스 생성
            self.client = AASQueryClient(AAS_SERVER_IP, AAS_SERVER_PORT)
            print(f"🔄 AASQueryHandler: Using STANDARD server client")
        else:
            # Mock 서버 사용 시 기존 방식 유지
            self.client = None
            print(f"📦 AASQueryHandler: Using MOCK server (direct HTTP)")
    
    def _to_base64url(self, s: str) -> str:
        """Base64 URL 인코딩 (Mock 서버용)"""
        return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")
    
    def _query_mock_server(self, target_sm_id: str) -> Dict[str, Any]:
        """Mock 서버에 직접 쿼리 (기존 로직)"""
        b64id = self._to_base64url(target_sm_id)
        url = f"{AAS_SERVER_URL}/submodels/{b64id}"
        
        print(f"INFO: Requesting from MOCK server: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _query_standard_server(self, target_sm_id: str) -> Dict[str, Any]:
        """표준 서버에 AASQueryClient를 통해 쿼리"""
        print(f"INFO: Requesting from STANDARD server: {target_sm_id}")
        
        try:
            # AASQueryClient의 get_submodel_by_id 메소드 사용
            result = self.client.get_submodel_by_id(target_sm_id)
            if result:
                return result
            else:
                raise ValueError(f"Submodel {target_sm_id} not found on standard server")
        except Exception as e:
            print(f"ERROR: Standard server query failed: {e}")
            raise
    
    def execute(self, step_details: dict, context: dict) -> dict:
        params = step_details.get('params', {})
        goal = params.get('goal')
        action_id = step_details.get('action_id')
        
        # ActionFetchAllMachineData 같은 복합 조회를 위한 로직
        if action_id == 'ActionFetchAllMachineData':
            print("INFO: Simulating fetch of all machine data.")
            target_sm_id = "urn:factory:submodel:capability:cnc-01"
        else:
            target_sm_id = step_details.get('target_submodel_id')
            if not target_sm_id:
                if goal == 'track_product_position':
                    product_id = params.get('product_id')
                    if not product_id:
                        raise ValueError("product_id is required for track_product_position")
                    target_sm_id = f"urn:factory:submodel:tracking_data:{product_id.lower()}"
                elif goal == 'detect_anomaly_for_product':
                    target_machine = params.get('target_machine')
                    if not target_machine:
                        raise ValueError("target_machine is required for detect_anomaly_for_product")
                    target_sm_id = f"urn:factory:submodel:sensor_data:{target_machine.lower()}"
                else:
                    raise ValueError(f"Cannot determine target for goal: {goal}")
        
        # 서버 타입에 따라 다른 쿼리 방식 사용
        if USE_STANDARD_SERVER:
            return self._query_standard_server(target_sm_id)
        else:
            return self._query_mock_server(target_sm_id)

class DataFilteringHandler:
    """AAS에서 가져온 데이터를 DSL 조건에 맞게 필터링하거나 가공하는 핸들러"""
    
    def _parse_value(self, data: Any) -> Any:
        """
        서버 응답의 value 필드를 파싱
        Mock과 Standard 서버의 다른 응답 형식 처리
        """
        if isinstance(data, dict):
            # submodelElements가 있는 경우 (표준 형식)
            if 'submodelElements' in data:
                elements = data.get('submodelElements', [])
                if elements and len(elements) > 0:
                    value = elements[0].get('value')
                    # value가 문자열이면 JSON 파싱 시도
                    if isinstance(value, str):
                        try:
                            return json.loads(value)
                        except json.JSONDecodeError:
                            return value
                    return value
            # 직접 value가 있는 경우
            elif 'value' in data:
                value = data.get('value')
                if isinstance(value, str):
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                return value
        return data
    
    def execute(self, step_details: dict, context: dict) -> dict:
        params = step_details.get('params', {})
        goal = params.get('goal')
        
        # Goal 1: 실패한 냉각 Job 필터링 로직
        if goal == 'query_failed_jobs_with_cooling':
            data_to_filter = None
            for key, value in context.items():
                if 'ActionFetchJobLog' in key:
                    data_to_filter = self._parse_value(value)
                    break
            
            if data_to_filter is None:
                raise ValueError("Could not find data from previous step for Goal 1.")
            
            # 리스트가 아니면 리스트로 변환
            if not isinstance(data_to_filter, list):
                data_to_filter = [data_to_filter] if data_to_filter else []

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
            print(f"DEBUG: Processing Goal 4, context keys: {list(context.keys())}")
            
            for key, value in context.items():
                if 'ActionFetchTrackingData' in key:
                    print(f"DEBUG: Found tracking data in {key}")
                    print(f"DEBUG: Value type: {type(value)}, has submodelElements: {'submodelElements' in value if isinstance(value, dict) else False}")
                    
                    # 표준 서버의 경우 직접 사용, Mock의 경우 파싱
                    if isinstance(value, dict) and 'submodelElements' in value:
                        # 표준 서버 형식 - submodelElements에서 데이터 추출
                        elements = value.get('submodelElements', [])
                        tracking_info = {}
                        for element in elements:
                            id_short = element.get('idShort')
                            elem_value = element.get('value')
                            if id_short and elem_value:
                                tracking_info[id_short] = elem_value
                        tracking_data = tracking_info
                        print(f"DEBUG: Extracted tracking_info from standard format: {tracking_info}")
                    else:
                        # Mock 서버 형식 - _parse_value 사용
                        tracking_data = self._parse_value(value)
                        print(f"DEBUG: Parsed value from mock format: {tracking_data}")
                    break
            
            if tracking_data is None:
                print(f"ERROR: No tracking data found in context: {context}")
                raise ValueError("Could not find tracking data from previous step for Goal 4.")
            
            print(f"DEBUG: Returning final_result: {tracking_data}")
            return {"final_result": tracking_data}
        
        # 어떤 조건에도 해당하지 않을 경우
        return {"final_result": "No applicable filter or processing logic for this goal."}

class SimulationInputHandler:
    """여러 소스의 데이터를 조합하여 시뮬레이터 입력 파일을 생성하는 핸들러"""
    def execute(self, step_details: dict, context: dict) -> dict:
        params = step_details.get('params', {})
        job_id = str(uuid.uuid4())
        
        # 고정된 경로 사용
        shared_dir = Path("/data")
        current_dir = shared_dir / "current"
        current_dir.mkdir(parents=True, exist_ok=True)
        
        # 컨텍스트에서 이전 단계들의 결과 수집
        input_data = {
            "process_spec": context.get("step_1_ActionFetchProductSpec", {}),
            "machine_data": context.get("step_2_ActionFetchAllMachineData", {}),
            "order": params,
            "job_id": job_id
        }

        # 고정 경로에 입력 파일 작성
        input_file_path = current_dir / "simulation_inputs.json"
        with open(input_file_path, 'w') as f:
            json.dump(input_data, f, indent=2)

        print(f"INFO: Created simulation input file at {input_file_path} (job_id: {job_id})")
        return {"simulation_job_id": job_id}

class K8sJobHandler:
    """쿠버네티스 클러스터에 시뮬레이터 Job을 생성하고 결과를 받아오는 핸들러"""
    def __init__(self):
        try: 
            k8s_config.load_incluster_config()
        except k8s_config.ConfigException: 
            k8s_config.load_kube_config()
        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()
        self.namespace = "default"

    def execute(self, step_details: dict, context: dict) -> dict:
        sim_context = context.get("step_3_ActionAssembleSimulatorInputs", {})
        job_id = sim_context.get("simulation_job_id")
        if not job_id: 
            raise ValueError("Simulation Job ID not found in context.")
        
        job_name = f"simulator-job-{job_id[:6]}"
        
        # 공유 볼륨(PVC)을 Job의 Pod에 마운트
        volume_mount = client.V1VolumeMount(
            name="shared-data-volume", 
            mount_path="/data"
        )
        volume = client.V1Volume(
            name="shared-data-volume",
            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                claim_name="factory-shared-pvc"
            )
        )

        container = client.V1Container(
            name="simulator", 
            image="simulator:latest", 
            image_pull_policy="Never",
            volume_mounts=[volume_mount]
        )
        pod_spec = client.V1PodSpec(
            restart_policy="Never", 
            containers=[container], 
            volumes=[volume]
        )
        pod_template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": "simulator"}), 
            spec=pod_spec
        )
        job_spec = client.V1JobSpec(template=pod_template, backoff_limit=1)
        job = client.V1Job(
            api_version="batch/v1", 
            kind="Job", 
            metadata=client.V1ObjectMeta(name=job_name), 
            spec=job_spec
        )

        print(f"INFO: Creating Kubernetes Job: {job_name}")
        self.batch_v1.create_namespaced_job(body=job, namespace=self.namespace)

        print("INFO: Waiting for Job to complete...")
        job_completed = False
        while not job_completed:
            time.sleep(2)
            job_status = self.batch_v1.read_namespaced_job_status(
                name=job_name, 
                namespace=self.namespace
            )
            if job_status.status.succeeded is not None and job_status.status.succeeded >= 1:
                job_completed = True
        print("INFO: Job completed successfully.")

        # 로그 수집
        pod_label_selector = f"job-name={job_name}"
        pods_list = self.core_v1.list_namespaced_pod(
            namespace=self.namespace, 
            label_selector=pod_label_selector
        )
        if not pods_list.items:
            raise RuntimeError(f"Could not find completed pod for job {job_name}")
        pod_name = pods_list.items[0].metadata.name
        
        result = None
        for i in range(5):
            print(f"INFO: Attempting to fetch logs for pod {pod_name} (Attempt {i+1}/5)")
            time.sleep(1)
            pod_log = self.core_v1.read_namespaced_pod_log(
                name=pod_name, 
                namespace=self.namespace
            )
            
            if pod_log:
                for line in pod_log.split('\n'):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            result = json.loads(line)
                            print("INFO: Successfully fetched and parsed logs.")
                            break
                        except json.JSONDecodeError:
                            continue
                
                if result:
                    break

        if result is None:
            raise RuntimeError(f"Failed to retrieve valid JSON result from pod {pod_name}")

        self.batch_v1.delete_namespaced_job(
            name=job_name, 
            namespace=self.namespace, 
            body=client.V1DeleteOptions()
        )
        print(f"INFO: Deleted Job: {job_name}")

        return {"final_result": result}

class AIModelHandler:
    def execute(self, step_details: dict, context: dict) -> dict:
        print("INFO: AI Model Handler (Not Implemented)")
        return {"result": "AI model placeholder"}

# --- ExecutionAgent 최종본 ---
class ExecutionAgent:
    def __init__(self):
        print(f"🚀 Initializing ExecutionAgent with {AAS_SERVER_TYPE} server")
        
        self.handlers = {
            "aas_query": AASQueryHandler(),
            "aas_query_multiple": AASQueryHandler(),
            "internal_processing": SimulationInputHandler(),
            "docker_run": K8sJobHandler(),
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
            
            try:
                step_result = handler.execute(step, execution_context)
                execution_context[f"step_{i+1}_{step['action_id']}"] = step_result

                if "final_result" in step_result:
                    final_result = step_result
                    
            except Exception as e:
                print(f"ERROR: Step {i+1} ({step.get('action_id')}) failed: {e}")
                raise

        return final_result if final_result else execution_context