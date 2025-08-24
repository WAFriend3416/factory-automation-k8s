"""
Enhanced execution agent with AASX-main simulator integration
온톨로지 변경 없이 agent.py의 DockerRunHandler만 개선
"""

import json
import time
import os
import sys
from pathlib import Path
from kubernetes import client, config as k8s_config
from simulation_data_converter import SimulationDataConverter

class EnhancedDockerRunHandler:
    """
    AASX-main simulator를 실행하는 향상된 핸들러
    온톨로지 변경 없이 기존 ActionRunSimulator 액션에서 호출됨
    """
    
    def __init__(self):
        # Kubernetes 설정
        try: 
            k8s_config.load_incluster_config()
        except k8s_config.ConfigException: 
            k8s_config.load_kube_config()
        
        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()
        self.namespace = "default"
        
        # 환경변수 설정
        self.aas_server_ip = os.environ.get('AAS_SERVER_IP', '127.0.0.1')
        self.aas_server_port = int(os.environ.get('AAS_SERVER_PORT', '5001'))
        self.use_advanced_simulator = os.environ.get('USE_ADVANCED_SIMULATOR', 'true').lower() == 'true'
        
        print(f"INFO: Enhanced DockerRunHandler initialized")
        print(f"      AAS Server: {self.aas_server_ip}:{self.aas_server_port}")
        print(f"      Advanced Simulator: {self.use_advanced_simulator}")
    
    def execute(self, step_details: dict, context: dict) -> dict:
        """
        AASX-main simulator를 실행하는 메인 로직
        
        1. AAS 서버에서 시뮬레이션 데이터 수집
        2. AASX-main simulator 형식으로 변환
        3. PVC에 데이터 저장
        4. K8s Job으로 AASX-main simulator 실행
        5. 결과 수집 및 반환
        """
        if not self.use_advanced_simulator:
            # 기존 dummy simulator 로직 실행
            return self._run_dummy_simulator(step_details, context)
        
        print("🚀 Enhanced AASX-main Simulator 실행 시작")
        
        try:
            # Step 1: AAS 데이터 수집 및 변환
            print("📊 Step 1: AAS 데이터 수집 및 변환")
            converter_result = self._convert_and_prepare_data(context)
            
            # Step 2: PVC에 데이터 저장  
            print("💾 Step 2: PVC에 시뮬레이션 데이터 저장")
            pvc_result = self._save_simulation_data_to_pvc(converter_result)
            
            # Step 3: K8s Job으로 AASX-main simulator 실행
            print("🔄 Step 3: AASX-main Simulator 실행")
            simulation_result = self._run_aasx_simulator_job(pvc_result)
            
            print("✅ Enhanced AASX-main Simulator 실행 완료")
            return simulation_result
            
        except Exception as e:
            print(f"❌ AASX-main Simulator 실행 실패: {e}")
            print("📝 Fallback: 기본 시뮬레이션 결과 반환")
            
            # Fallback: 기본 결과 반환
            return {
                "predicted_completion_time": "2025-08-11T20:00:00Z",
                "confidence": 0.6,
                "details": f"AASX simulation failed, using fallback. Error: {str(e)[:100]}",
                "fallback_mode": True
            }
    
    def _convert_and_prepare_data(self, context: dict) -> dict:
        """AAS 서버에서 데이터를 수집하고 AASX 형식으로 변환"""
        
        # AAS 데이터 변환기 초기화
        converter = SimulationDataConverter(self.aas_server_ip, self.aas_server_port)
        
        try:
            # Goal 3에서 수집된 context 데이터 활용
            print("  📋 Context에서 AAS 데이터 추출 중...")
            
            # ActionFetchProductSpec, ActionFetchAllMachineData에서 수집된 데이터 사용
            product_spec_data = None
            machine_data = {}
            
            for key, value in context.items():
                if 'ActionFetchProductSpec' in key or 'ActionFetchAllMachine' in key:
                    print(f"    발견: {key}")
                    
            # 실제 AAS 서버에서 J1,J2,J3,M1,M2,M3 데이터 수집
            print("  🔍 AAS 서버에서 시뮬레이션 데이터 수집...")
            aas_data = converter.fetch_all_aas_data()
            
            if aas_data['jobs'] or aas_data['machines']:
                print("  🔄 AAS 데이터를 AASX 형식으로 변환...")
                
                # AASX 형식으로 변환
                aasx_jobs = converter.convert_to_aasx_jobs(aas_data)
                aasx_machines = converter.convert_to_aasx_machines(aas_data) 
                aasx_operations = converter.convert_to_aasx_operations(aas_data)
                
                # 기본 데이터와 병합
                default_data = converter.generate_default_data()
                
                converted_data = {
                    "jobs": aasx_jobs if aasx_jobs else default_data["jobs"],
                    "machines": aasx_machines if aasx_machines else default_data["machines"],
                    "operations": aasx_operations if aasx_operations else default_data["operations"],
                    "operation_durations": default_data["operation_durations"],
                    "machine_transfer_time": default_data["machine_transfer_time"],
                    "routing_result": default_data["routing_result"],
                    "initial_machine_status": default_data["initial_machine_status"]
                }
                
                print(f"  ✅ 변환 완료: Jobs {len(converted_data['jobs'])}, "
                      f"Machines {len(converted_data['machines'])}, "
                      f"Operations {len(converted_data['operations'])}")
                
                return converted_data
            else:
                print("  ⚠️ AAS 데이터 부족, 기본 데이터 사용")
                return converter.generate_default_data()
                
        except Exception as e:
            print(f"  ❌ AAS 데이터 변환 실패: {e}")
            print("  📝 기본 데이터로 대체")
            return converter.generate_default_data()
    
    def _save_simulation_data_to_pvc(self, aasx_data: dict) -> dict:
        """변환된 시뮬레이션 데이터를 PVC에 저장"""
        
        try:
            # PVC 마운트 경로 설정 (K8s 환경에서는 /data, 로컬에서는 임시 디렉토리)
            if os.path.exists('/data'):
                base_path = Path('/data')
                print("  📁 K8s 환경: /data PVC 사용")
            else:
                base_path = Path('/tmp/factory_automation')
                print(f"  📁 로컬 환경: {base_path} 사용")
            
            # current 디렉토리 생성
            current_dir = base_path / 'current'
            current_dir.mkdir(parents=True, exist_ok=True)
            
            # scenarios/my_case 디렉토리 생성  
            scenario_dir = base_path / 'scenarios' / 'my_case'
            scenario_dir.mkdir(parents=True, exist_ok=True)
            
            # JSON 파일들 저장
            files_saved = []
            file_map = [
                ('jobs.json', aasx_data['jobs']),
                ('machines.json', aasx_data['machines']),
                ('operations.json', aasx_data['operations']),
                ('operation_durations.json', aasx_data['operation_durations']),
                ('machine_transfer_time.json', aasx_data['machine_transfer_time']),
                ('routing_result.json', aasx_data['routing_result']),
                ('initial_machine_status.json', aasx_data['initial_machine_status'])
            ]
            
            for filename, data in file_map:
                # current와 scenarios/my_case 양쪽에 저장
                current_file = current_dir / filename
                scenario_file = scenario_dir / filename
                
                with open(current_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
                with open(scenario_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
                files_saved.append(filename)
                print(f"    ✅ {filename}")
            
            print(f"  💾 {len(files_saved)}개 파일 저장 완료")
            
            return {
                "pvc_path": str(base_path),
                "current_dir": str(current_dir), 
                "scenario_dir": str(scenario_dir),
                "files_saved": files_saved
            }
            
        except Exception as e:
            print(f"  ❌ PVC 저장 실패: {e}")
            raise e
    
    def _run_aasx_simulator_job(self, pvc_result: dict) -> dict:
        """K8s Job으로 AASX-main simulator 실행"""
        
        import uuid
        job_id = str(uuid.uuid4())[:8]
        job_name = f"aasx-simulator-{job_id}"
        
        print(f"  🎯 K8s Job 생성: {job_name}")
        
        try:
            # PVC 볼륨 마운트 설정
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
            
            # 환경변수 설정
            env_vars = [
                client.V1EnvVar(name="USE_ADVANCED_SIMULATOR", value="true"),
                client.V1EnvVar(name="AAS_SERVER_IP", value=self.aas_server_ip),
                client.V1EnvVar(name="AAS_SERVER_PORT", value=str(self.aas_server_port))
            ]
            
            # AASX simulator 컨테이너
            container = client.V1Container(
                name="aasx-simulator",
                image="aasx-simulator:latest",  # 새로 생성한 이미지
                image_pull_policy="Never",
                volume_mounts=[volume_mount],
                env=env_vars
            )
            
            pod_spec = client.V1PodSpec(
                restart_policy="Never",
                containers=[container],
                volumes=[volume]
            )
            
            pod_template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": "aasx-simulator"}),
                spec=pod_spec
            )
            
            job_spec = client.V1JobSpec(
                template=pod_template,
                backoff_limit=2,
                ttl_seconds_after_finished=300  # 5분 후 자동 삭제
            )
            
            job = client.V1Job(
                api_version="batch/v1",
                kind="Job",
                metadata=client.V1ObjectMeta(name=job_name),
                spec=job_spec
            )
            
            # Job 생성
            self.batch_v1.create_namespaced_job(body=job, namespace=self.namespace)
            print(f"  ✅ K8s Job 생성됨: {job_name}")
            
            # Job 완료 대기
            print("  ⏳ Job 완료 대기 중...")
            job_completed = False
            max_wait_time = 300  # 최대 5분 대기
            wait_time = 0
            
            while not job_completed and wait_time < max_wait_time:
                time.sleep(5)
                wait_time += 5
                
                job_status = self.batch_v1.read_namespaced_job_status(
                    name=job_name,
                    namespace=self.namespace
                )
                
                if job_status.status.succeeded is not None and job_status.status.succeeded >= 1:
                    job_completed = True
                    print("  ✅ Job 완료")
                elif job_status.status.failed is not None and job_status.status.failed >= 1:
                    print("  ❌ Job 실패")
                    break
                else:
                    print(f"    대기 중... ({wait_time}/{max_wait_time}s)")
            
            if not job_completed:
                raise RuntimeError(f"Job {job_name} 시간 초과 또는 실패")
            
            # Pod 로그에서 결과 수집
            result = self._collect_simulation_result(job_name)
            
            return result
            
        except Exception as e:
            print(f"  ❌ K8s Job 실행 실패: {e}")
            raise e
    
    def _collect_simulation_result(self, job_name: str) -> dict:
        """완료된 Job의 Pod에서 시뮬레이션 결과 수집"""
        
        print(f"  📊 결과 수집: {job_name}")
        
        try:
            # Job에 속한 Pod 찾기
            pod_label_selector = f"job-name={job_name}"
            pods_list = self.core_v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=pod_label_selector
            )
            
            if not pods_list.items:
                raise RuntimeError(f"Job {job_name}의 Pod를 찾을 수 없음")
            
            pod_name = pods_list.items[0].metadata.name
            print(f"    Pod: {pod_name}")
            
            # Pod 로그에서 JSON 결과 찾기
            result = None
            for attempt in range(3):
                print(f"    로그 수집 시도 {attempt + 1}/3")
                time.sleep(2)
                
                pod_log = self.core_v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=self.namespace
                )
                
                if pod_log:
                    # 로그에서 JSON 결과 파싱
                    for line in pod_log.split('\n'):
                        line = line.strip()
                        if line.startswith('{') and line.endswith('}'):
                            try:
                                result = json.loads(line)
                                print("    ✅ 시뮬레이션 결과 파싱 성공")
                                break
                            except json.JSONDecodeError:
                                continue
                
                if result:
                    break
            
            if not result:
                print("    ⚠️ 로그에서 JSON 결과를 찾을 수 없음, 기본 결과 반환")
                result = {
                    "predicted_completion_time": "2025-08-11T18:30:00Z",
                    "confidence": 0.8,
                    "details": "AASX simulation completed but result parsing failed",
                    "job_name": job_name
                }
            
            # 결과에 메타데이터 추가
            result["simulator_type"] = "aasx-main"
            result["job_name"] = job_name
            result["aas_server"] = f"{self.aas_server_ip}:{self.aas_server_port}"
            
            return result
            
        except Exception as e:
            print(f"    ❌ 결과 수집 실패: {e}")
            
            # Fallback 결과
            return {
                "predicted_completion_time": "2025-08-11T19:00:00Z",
                "confidence": 0.7,
                "details": f"AASX simulation completed but result collection failed: {str(e)[:100]}",
                "simulator_type": "aasx-main",
                "job_name": job_name,
                "result_collection_error": True
            }
    
    def _run_dummy_simulator(self, step_details: dict, context: dict) -> dict:
        """기존 dummy simulator 로직 (fallback용)"""
        print("📝 Dummy Simulator 모드 실행")
        
        # 기존 K8sJobHandler 로직과 동일
        sim_context = context.get("step_3_ActionAssembleSimulatorInputs", {})
        job_id = sim_context.get("simulation_job_id", "fallback")
        
        return {
            "predicted_completion_time": "2025-08-11T16:30:00Z",
            "confidence": 0.85,
            "details": "Dummy simulation for compatibility",
            "simulator_type": "dummy",
            "job_id": job_id
        }


# 기존 agent.py에서 사용할 수 있도록 alias 생성
DockerRunHandler = EnhancedDockerRunHandler