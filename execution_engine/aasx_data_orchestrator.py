"""
AASX Data Orchestrator
AASX 서버에서 NSGA-II 시뮬레이션을 위한 6개 JSON 파일을 생성하는 오케스트레이터
"""

import json
import yaml
import requests
import base64
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class AASXDataOrchestrator:
    def __init__(self, config_path: str = "config/NSGA2Model_sources.yaml", base_url: str = "http://127.0.0.1:5001"):
        """
        AASX Data Orchestrator 초기화
        
        Args:
            config_path: NSGA2Model_sources.yaml 파일 경로
            base_url: AASX 서버 기본 URL
        """
        self.base_url = base_url
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.session = requests.Session()
        self.session.timeout = self.config.get('aasx_server', {}).get('timeout', 30)
        
    def _load_config(self) -> Dict[str, Any]:
        """YAML 설정 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            raise
    
    def _encode_id(self, id_string: str) -> str:
        """AAS ID를 Base64 URL-safe 형태로 인코딩"""
        return base64.urlsafe_b64encode(id_string.encode()).decode().rstrip('=')
    
    def _get_submodel_element_value(self, shell_id: str, submodel_id: str, element_id: str) -> Optional[str]:
        """
        서브모델 엘리먼트 값 조회 (서브모델 직접 접근)

        Args:
            shell_id: AAS Shell ID (사용되지 않음, 호환성 유지용)
            submodel_id: Submodel ID
            element_id: Element ID

        Returns:
            Element 값 (문자열)
        """
        try:
            # 서브모델에 직접 접근 (Shell을 거치지 않음)
            encoded_submodel = self._encode_id(submodel_id)
            
            # 서브모델 직접 조회 API 사용
            submodel_url = urljoin(self.base_url + "/", f"submodels/{encoded_submodel}")
            
            logger.info(f"Requesting submodel: {submodel_url}")
            response = self.session.get(submodel_url)

            if response.status_code == 200:
                try:
                    submodel_data = response.json()
                    submodel_elements = submodel_data.get('submodelElements', [])
                    
                    # element_id와 일치하는 엘리먼트 찾기
                    for element in submodel_elements:
                        if element.get('idShort') == element_id:
                            if element.get('modelType') == 'Property' and 'value' in element:
                                logger.info(f"✅ Found element {element_id} with value")
                                return element['value']
                            else:
                                logger.warning(f"Element {element_id} is not a Property or has no value field")
                                return None
                    
                    logger.warning(f"Element {element_id} not found in submodel {submodel_id}")
                    return None
                    
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response for submodel {submodel_id}")
                    return None
            else:
                logger.warning(f"Failed to get submodel {submodel_id}: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error getting element value: {e}")
            return None
    
    def _get_machine_data(self, machine_id: str) -> Dict[str, Any]:
        """
        개별 머신의 capability와 status 데이터 조회
        
        Args:
            machine_id: 머신 ID (예: M1, M2, M3, M4)
            
        Returns:
            머신 데이터 딕셔너리
        """
        machine_data = {
            "id": machine_id,
            "type": None,
            "status": "unknown",
            "capabilities": [],
            "efficiency": 1.0,
            "next_available_time": 0,
            "queue_length": 0
        }
        
        try:
            shell_id = f"urn:factory:machine:{machine_id}"
            
            # Capability 서브모델에서 데이터 조회
            capability_submodel = f"urn:factory:submodel:capability:{machine_id}"
            
            # machine_type 조회
            machine_type = self._get_submodel_element_value(shell_id, capability_submodel, "machine_type")
            if machine_type:
                machine_data["type"] = machine_type
            
            # performable_operations 조회 (리스트 형태)
            # 실제 구현에서는 SubmodelElementList를 처리해야 할 수도 있음
            operations = self._get_submodel_element_value(shell_id, capability_submodel, "performable_operations")
            if operations:
                try:
                    if isinstance(operations, str):
                        machine_data["capabilities"] = [operations]
                    else:
                        machine_data["capabilities"] = operations
                except:
                    machine_data["capabilities"] = ["drilling", "welding", "testing", "assembly"]  # 기본값
            
            # efficiency 조회
            efficiency = self._get_submodel_element_value(shell_id, capability_submodel, "efficiency")
            if efficiency:
                try:
                    machine_data["efficiency"] = float(efficiency)
                except:
                    pass
            
            # Status 서브모델에서 데이터 조회
            status_submodel = f"urn:factory:submodel:status:{machine_id}"
            
            # status 조회
            status = self._get_submodel_element_value(shell_id, status_submodel, "status")
            if status:
                machine_data["status"] = status
            
            # next_available_time 조회
            next_time = self._get_submodel_element_value(shell_id, status_submodel, "next_available_time")
            if next_time:
                try:
                    machine_data["next_available_time"] = int(next_time)
                except:
                    pass
            
            # queue_length 조회
            queue_len = self._get_submodel_element_value(shell_id, status_submodel, "queue_length")
            if queue_len:
                try:
                    machine_data["queue_length"] = int(queue_len)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Error getting machine data for {machine_id}: {e}")
        
        return machine_data
    
    def generate_simulation_files(self, output_dir: str = "temp/simulation_scenario") -> Dict[str, str]:
        """
        AASX 서버에서 데이터를 추출하여 NSGA-II용 6개 JSON 파일 생성
        
        Args:
            output_dir: 출력 디렉토리
            
        Returns:
            생성된 파일 경로 딕셔너리
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        generated_files = {}
        sources = self.config.get('sources', {})
        
        try:
            # 1. jobs.json 생성
            logger.info("Generating jobs.json...")
            jobs_data = self._get_submodel_element_value(
                "urn:factory:simulation:main",
                "urn:factory:submodel:simulation_data",
                "jobs_data"
            )
            if jobs_data:
                jobs_json = json.loads(jobs_data)
                jobs_file = output_path / "jobs.json"
                with open(jobs_file, 'w', encoding='utf-8') as f:
                    json.dump({"jobs": jobs_json}, f, indent=2, ensure_ascii=False)
                generated_files["jobs.json"] = str(jobs_file)
                logger.info(f"✅ jobs.json generated with {len(jobs_json)} jobs")
            
            # 2. operations.json 생성
            logger.info("Generating operations.json...")
            operations_data = self._get_submodel_element_value(
                "urn:factory:simulation:main",
                "urn:factory:submodel:simulation_data",
                "operations_data"
            )
            if operations_data:
                operations_json = json.loads(operations_data)
                operations_file = output_path / "operations.json"
                with open(operations_file, 'w', encoding='utf-8') as f:
                    json.dump({"operations": operations_json}, f, indent=2, ensure_ascii=False)
                generated_files["operations.json"] = str(operations_file)
                logger.info(f"✅ operations.json generated with {len(operations_json)} operations")
            
            # 3. operation_durations.json 생성
            logger.info("Generating operation_durations.json...")
            durations_data = self._get_submodel_element_value(
                "urn:factory:simulation:main",
                "urn:factory:submodel:simulation_data",
                "operation_durations_data"
            )
            if durations_data:
                durations_json = json.loads(durations_data)
                durations_file = output_path / "operation_durations.json"
                with open(durations_file, 'w', encoding='utf-8') as f:
                    json.dump(durations_json, f, indent=2, ensure_ascii=False)
                generated_files["operation_durations.json"] = str(durations_file)
                logger.info(f"✅ operation_durations.json generated")
            
            # 4. machine_transfer_time.json 생성
            logger.info("Generating machine_transfer_time.json...")
            transfer_data = self._get_submodel_element_value(
                "urn:factory:simulation:main",
                "urn:factory:submodel:simulation_data",
                "machine_transfer_time_data"
            )
            if transfer_data:
                transfer_json = json.loads(transfer_data)
                transfer_file = output_path / "machine_transfer_time.json"
                with open(transfer_file, 'w', encoding='utf-8') as f:
                    json.dump(transfer_json, f, indent=2, ensure_ascii=False)
                generated_files["machine_transfer_time.json"] = str(transfer_file)
                logger.info(f"✅ machine_transfer_time.json generated")
            
            # 5. job_release.json 생성
            logger.info("Generating job_release.json...")
            release_data = self._get_submodel_element_value(
                "urn:factory:simulation:main",
                "urn:factory:submodel:simulation_data",
                "job_release_data"
            )
            if release_data:
                release_json = json.loads(release_data)
                release_file = output_path / "job_release.json"
                with open(release_file, 'w', encoding='utf-8') as f:
                    json.dump({"job_releases": release_json}, f, indent=2, ensure_ascii=False)
                generated_files["job_release.json"] = str(release_file)
                logger.info(f"✅ job_release.json generated with {len(release_json)} releases")
            
            # 6. machines.json 생성 (개별 머신 데이터 조합)
            logger.info("Generating machines.json...")
            machine_ids = ["M1", "M2", "M3", "M4"]
            machines_data = []
            
            for machine_id in machine_ids:
                machine_data = self._get_machine_data(machine_id)
                machines_data.append(machine_data)
            
            machines_file = output_path / "machines.json"
            with open(machines_file, 'w', encoding='utf-8') as f:
                json.dump({"machines": machines_data}, f, indent=2, ensure_ascii=False)
            generated_files["machines.json"] = str(machines_file)
            logger.info(f"✅ machines.json generated with {len(machines_data)} machines")
            
        except Exception as e:
            logger.error(f"Error generating simulation files: {e}")
            raise
        
        return generated_files
    
    def test_aasx_connection(self) -> Dict[str, Any]:
        """
        AASX 서버 연결 및 데이터 접근 테스트
        
        Returns:
            테스트 결과 딕셔너리
        """
        test_results = {
            "server_accessible": False,
            "factory_simulation_accessible": False,
            "machine_data_accessible": False,
            "errors": []
        }
        
        try:
            # 1. 기본 서버 접속 테스트
            response = self.session.get(f"{self.base_url}/shells", timeout=10)
            if response.status_code == 200:
                test_results["server_accessible"] = True
                logger.info("✅ AASX server is accessible")
            else:
                test_results["errors"].append(f"Server returned {response.status_code}")
                
        except Exception as e:
            test_results["errors"].append(f"Server connection failed: {e}")
        
        # 2. FactorySimulation 데이터 접근 테스트
        try:
            jobs_data = self._get_submodel_element_value(
                "urn:factory:simulation:main",
                "urn:factory:submodel:simulation_data", 
                "jobs_data"
            )
            if jobs_data:
                test_results["factory_simulation_accessible"] = True
                logger.info("✅ FactorySimulation data is accessible")
            else:
                test_results["errors"].append("Could not access FactorySimulation jobs_data")
        except Exception as e:
            test_results["errors"].append(f"FactorySimulation access failed: {e}")
        
        # 3. 머신 데이터 접근 테스트
        try:
            machine_data = self._get_machine_data("M1")
            if machine_data.get("type"):
                test_results["machine_data_accessible"] = True
                logger.info("✅ Machine data is accessible")
            else:
                test_results["errors"].append("Could not access machine M1 data")
        except Exception as e:
            test_results["errors"].append(f"Machine data access failed: {e}")
        
        return test_results

def main():
    """테스트 실행"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    orchestrator = AASXDataOrchestrator()
    
    # 연결 테스트
    print("🔍 Testing AASX server connection...")
    test_results = orchestrator.test_aasx_connection()
    print(f"Test results: {json.dumps(test_results, indent=2)}")
    
    if test_results.get("factory_simulation_accessible"):
        # 파일 생성 테스트
        print("📁 Generating simulation files...")
        try:
            generated_files = orchestrator.generate_simulation_files("temp/test_scenario")
            print("✅ Successfully generated files:")
            for filename, filepath in generated_files.items():
                print(f"  - {filename}: {filepath}")
        except Exception as e:
            print(f"❌ Failed to generate files: {e}")
    else:
        print("❌ Cannot generate files due to connection issues")

if __name__ == "__main__":
    main()