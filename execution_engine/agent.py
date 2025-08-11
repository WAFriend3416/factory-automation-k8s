# execution_engine/agent.py
import requests
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import AAS_SERVER_URL

class AASQueryHandler:
    """AAS 서버에 Submodel 데이터를 요청하는 핸들러. 동적 ID 생성을 지원합니다."""
    def execute(self, step_details: dict, context: dict) -> dict:
        target_sm_id = step_details.get('target_submodel_id')
        params = step_details.get('params', {})

        # 1. target_submodel_id가 온톨로지에 고정되어 있는지 확인
        if target_sm_id:
            # Goal 1, 3처럼 고정된 Submodel을 조회하는 경우
            url = f"{AAS_SERVER_URL}/submodels/{target_sm_id}"
        else:
            # 2. ID가 없다면, DSL 파라미터를 보고 동적으로 생성
            goal = params.get('goal')
            if goal == 'track_product_position':
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
        
        # 어떤 조건에도 해당하지 않을 경우
        return {"final_result": "No applicable filter or processing logic for this goal."}

# --- 향후 확장을 위한 플레이스홀더 ---
class AIModelHandler:
    def execute(self, step_details: dict, context: dict) -> dict:
        print("INFO: AI Model Handler (Not Implemented)")
        return {"result": "AI model placeholder"}

class DockerRunHandler:
    def execute(self, step_details: dict, context: dict) -> dict:
        print("INFO: Docker Run Handler (Not Implemented)")
        return {"result": "Docker simulator placeholder"}
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