# execution_engine/agent.py
import requests
import sys
import json
import time
import uuid
from pathlib import Path

# Kubernetes support - check if available
try:
    from kubernetes import client, config
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False
    print("WARNING: kubernetes library not available. DockerRunHandler will use fallback mode.")

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import AAS_SERVER_URL

class AASQueryHandler:
    """AAS 서버에 Submodel 데이터를 요청하는 핸들러. 동적 ID 생성을 지원합니다."""
    def execute(self, step_details: dict, context: dict) -> dict:
        target_sm_id = step_details.get('target_submodel_id')
        params = step_details.get('params', {})
        action_type = step_details.get('type')

        # 1. target_submodel_id가 온톨로지에 고정되어 있는지 확인
        if target_sm_id:
            # Goal 1, 3처럼 고정된 Submodel을 조회하는 경우
            url = f"{AAS_SERVER_URL}/submodels/{target_sm_id}"
        else:
            # 2. ID가 없다면, DSL 파라미터를 보고 동적으로 생성
            goal = params.get('goal')
            
            # Handle Goal 3's multiple machine data query
            if goal == 'predict_first_completion_time' and action_type == 'aas_query_multiple':
                # Fetch capability and status for all machines
                all_machine_data = {}
                machines = ['cnc-01', 'cnc-02', 'cnc-pro-03', 'press-01', 
                           'welder-01', 'welder-02', 'painter-01', 'inspector-01']
                
                for machine in machines:
                    # Fetch capability
                    cap_url = f"{AAS_SERVER_URL}/submodels/urn:factory:submodel:capability:{machine}"
                    try:
                        response = requests.get(cap_url)
                        response.raise_for_status()
                        all_machine_data[f"capability_{machine}"] = response.json()
                    except:
                        pass
                    
                    # Fetch status
                    status_url = f"{AAS_SERVER_URL}/submodels/urn:factory:submodel:status:{machine}"
                    try:
                        response = requests.get(status_url)
                        response.raise_for_status()
                        all_machine_data[f"status_{machine}"] = response.json()
                    except:
                        pass
                
                return all_machine_data
            
            elif goal == 'track_product_position':
                product_id = params.get('product_id')
                if not product_id:
                    raise ValueError("product_id is required for track_product_position goal.")
                # product_id를 기반으로 Submodel URN 동적 생성
                target_sm_id = f"urn:factory:submodel:tracking_data:{product_id.lower()}"
                url = f"{AAS_SERVER_URL}/submodels/{target_sm_id}"

            elif goal == 'detect_anomaly_for_product':
                target_machine = params.get('target_machine')
                if not target_machine:
                    raise ValueError("target_machine is required for detect_anomaly_for_product goal.")
                # target_machine을 기반으로 Submodel URN 동적 생성
                target_sm_id = f"urn:factory:submodel:sensor_data:{target_machine.lower()}"
                url = f"{AAS_SERVER_URL}/submodels/{target_sm_id}"
            
            else:
                raise ValueError(f"Cannot dynamically determine target submodel for goal: {goal}")

        print(f"INFO: Requesting AAS data from: {url}")
        
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

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
        
        # Goal 3: 시뮬레이터 입력 조립 로직
        elif goal == 'predict_first_completion_time':
            # Collect data from previous steps
            process_spec = None
            machine_data = None
            
            for key, value in context.items():
                if 'ActionFetchProductSpec' in key:
                    process_spec = value
                elif 'ActionFetchAllMachineData' in key:
                    machine_data = value
            
            if not process_spec or not machine_data:
                raise ValueError("Could not find required data for Goal 3 simulator inputs.")
            
            # Prepare simulator input (simplified for prototype)
            simulator_input = {
                "product_id": params.get('product_id'),
                "quantity": params.get('quantity'),
                "process_spec": process_spec,
                "machine_data": machine_data,
                "timestamp": "2025-08-11T12:00:00Z"
            }
            
            return {"simulator_input": simulator_input}
        
        # 어떤 조건에도 해당하지 않을 경우
        return {"final_result": "No applicable filter or processing logic for this goal."}

# --- 향후 확장을 위한 플레이스홀더 ---
class AIModelHandler:
    def execute(self, step_details: dict, context: dict) -> dict:
        print("INFO: AI Model Handler (Not Implemented)")
        return {"result": "AI model placeholder"}

class DockerRunHandler:
    """쿠버네티스 클러스터에 시뮬레이터 Job을 생성하고 결과를 받아오는 핸들러"""
    def __init__(self):
        if KUBERNETES_AVAILABLE:
            try:
                # 클러스터 내부에서 실행 중인지 확인
                config.load_incluster_config()
            except config.ConfigException:
                # 로컬에서 kubectl 설정 사용
                config.load_kube_config()
            self.batch_v1 = client.BatchV1Api()
            self.core_v1 = client.CoreV1Api()
            self.namespace = "default"
    
    def execute(self, step_details: dict, context: dict) -> dict:
        if not KUBERNETES_AVAILABLE:
            # Fallback mode - return dummy result
            print("INFO: Docker Run Handler (Fallback Mode - Kubernetes not available)")
            return {"final_result": {
                "predicted_completion_time": "2025-08-11T16:30:00Z",
                "confidence": 0.85,
                "note": "This is a fallback result - Kubernetes not available"
            }}
        
        # Create unique job name
        job_name = f"simulator-job-{uuid.uuid4().hex[:6]}"
        
        # Define container
        container = client.V1Container(
            name="simulator",
            image="simulator:latest",
            image_pull_policy="Never",  # Use local image
        )
        
        # Define pod template
        pod_template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": "simulator"}),
            spec=client.V1PodSpec(restart_policy="Never", containers=[container]),
        )
        
        # Define job spec
        job_spec = client.V1JobSpec(template=pod_template, backoff_limit=1)
        
        # Create job object
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=job_name),
            spec=job_spec,
        )
        
        print(f"INFO: Creating Kubernetes Job: {job_name}")
        self.batch_v1.create_namespaced_job(body=job, namespace=self.namespace)
        
        # Wait for job completion
        print("INFO: Waiting for Job to complete...")
        job_completed = False
        while not job_completed:
            time.sleep(2)
            job_status = self.batch_v1.read_namespaced_job_status(
                name=job_name, namespace=self.namespace
            )
            if job_status.status.succeeded is not None and job_status.status.succeeded >= 1:
                job_completed = True
        
        print("INFO: Job completed successfully.")
        
        # Get pod logs
        pod_label_selector = f"job-name={job_name}"
        pods_list = self.core_v1.list_namespaced_pod(
            namespace=self.namespace, label_selector=pod_label_selector
        )
        pod_name = pods_list.items[0].metadata.name
        
        # Read pod log
        pod_log = self.core_v1.read_namespaced_pod_log(
            name=pod_name, namespace=self.namespace
        )
        
        # Parse JSON result - strip any whitespace
        try:
            # First try direct JSON parsing
            result = json.loads(pod_log.strip())
        except json.JSONDecodeError as e:
            # If that fails, try evaluating as Python dict and converting
            try:
                import ast
                result = ast.literal_eval(pod_log.strip())
                print(f"INFO: Parsed output as Python dict")
            except:
                print(f"ERROR: Failed to parse simulator output: {e}")
                print(f"Raw output: {repr(pod_log)}")
                # Return a fallback result
                result = {
                    "predicted_completion_time": "2025-08-11T16:30:00Z",
                    "confidence": 0.85,
                    "note": "Fallback result due to parsing error"
                }
        
        # Clean up job
        self.batch_v1.delete_namespaced_job(
            name=job_name, namespace=self.namespace, 
            body=client.V1DeleteOptions()
        )
        print(f"INFO: Deleted Job: {job_name}")
        
        return {"final_result": result}
# ------------------------------------

class ExecutionAgent:
    def __init__(self):
        self.handlers = {
            "aas_query": AASQueryHandler(),
            "data_filtering": DataFilteringHandler(),
            "ai_model_inference": AIModelHandler(),
            "docker_run": DockerRunHandler(),
            "aas_query_multiple": AASQueryHandler(),
            "internal_processing": DataFilteringHandler(),
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