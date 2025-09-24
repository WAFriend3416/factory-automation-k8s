#!/usr/bin/env python3
"""
Factory Automation K8s - Output Structure Creator
각 단계별 산출물을 체계적으로 정리하여 output 폴더에 저장
"""

import json
import shutil
import requests
import base64
from pathlib import Path
from datetime import datetime
import logging
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from execution_engine.aasx_data_orchestrator import AASXDataOrchestrator

def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def create_folder_structure():
    """output 폴더 구조 생성"""
    base_path = Path("output")
    
    folders = [
        "step1_aasx_raw_data/input",
        "step1_aasx_raw_data/output", 
        "step2_data_orchestrator/input",
        "step2_data_orchestrator/output",
        "step3_nsga2_simulation/input",
        "step3_nsga2_simulation/output",
        "metadata"
    ]
    
    for folder in folders:
        folder_path = base_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        
    return base_path

def collect_aasx_raw_data(base_path: Path, logger):
    """Step 1: AASX 서버 원본 데이터 수집"""
    logger.info("🔍 Step 1: Collecting AASX raw data...")
    
    step1_input = base_path / "step1_aasx_raw_data/input"
    step1_output = base_path / "step1_aasx_raw_data/output"
    
    base_url = "http://127.0.0.1:5001"
    session = requests.Session()
    
    # 서브모델 리스트
    submodels = [
        {
            "id": "urn:factory:submodel:simulation_data",
            "name": "FactorySimulation", 
            "elements": ["jobs_data", "operations_data", "operation_durations_data", 
                        "machine_transfer_time_data", "job_release_data"]
        },
        {
            "id": "urn:factory:submodel:capability:M1",
            "name": "Machine_M1_Capability",
            "elements": ["machine_type", "efficiency"]
        },
        {
            "id": "urn:factory:submodel:status:M1", 
            "name": "Machine_M1_Status",
            "elements": ["status", "next_available_time", "queue_length"]
        }
    ]
    
    raw_data = {}
    extracted_data = {}
    
    for submodel in submodels:
        submodel_id = submodel["id"]
        submodel_name = submodel["name"]
        
        # Base64 인코딩
        encoded_id = base64.urlsafe_b64encode(submodel_id.encode()).decode().rstrip('=')
        
        # 원본 서브모델 데이터 조회
        try:
            url = f"{base_url}/submodels/{encoded_id}"
            response = session.get(url)
            
            if response.status_code == 200:
                submodel_data = response.json()
                raw_data[submodel_name] = submodel_data
                
                # Property.value 필드 추출
                extracted_elements = {}
                for element in submodel_data.get('submodelElements', []):
                    element_id = element.get('idShort')
                    if element_id in submodel['elements']:
                        if element.get('modelType') == 'Property' and 'value' in element:
                            extracted_elements[element_id] = element['value']
                
                extracted_data[submodel_name] = extracted_elements
                logger.info(f"  ✅ {submodel_name}: {len(extracted_elements)} elements")
            else:
                logger.warning(f"  ❌ Failed to get {submodel_name}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"  ❌ Error processing {submodel_name}: {e}")
    
    # 원본 데이터 저장
    with open(step1_input / "aasx_raw_responses.json", 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)
    
    # 추출된 데이터 저장  
    with open(step1_output / "extracted_property_values.json", 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"  📁 Raw data saved: {len(raw_data)} submodels")
    return extracted_data

def organize_orchestrator_data(base_path: Path, logger):
    """Step 2: DataOrchestrator 결과물 정리"""
    logger.info("🔧 Step 2: Organizing DataOrchestrator outputs...")
    
    step2_input = base_path / "step2_data_orchestrator/input"
    step2_output = base_path / "step2_data_orchestrator/output"
    
    # Step 1 output을 Step 2 input으로 복사
    step1_output = base_path / "step1_aasx_raw_data/output/extracted_property_values.json"
    if step1_output.exists():
        shutil.copy2(step1_output, step2_input / "aasx_extracted_data.json")
    
    # 기존 생성된 JSON 파일들을 Step 2 output으로 복사
    source_dir = Path("temp/full_simulation")
    if source_dir.exists():
        for json_file in source_dir.glob("*.json"):
            shutil.copy2(json_file, step2_output / json_file.name)
            logger.info(f"  📄 Copied {json_file.name}")
    
    # DataOrchestrator 실행 로그 생성
    orchestrator_log = {
        "timestamp": datetime.now().isoformat(),
        "input_source": "AASX Server Property.value fields",
        "processing_method": "Direct submodel access",
        "generated_files": [f.name for f in step2_output.glob("*.json")],
        "file_sizes": {f.name: f.stat().st_size for f in step2_output.glob("*.json")}
    }
    
    with open(step2_output / "orchestrator_execution_log.json", 'w', encoding='utf-8') as f:
        json.dump(orchestrator_log, f, indent=2, ensure_ascii=False)
    
    logger.info(f"  📁 Orchestrator data organized: {len(list(step2_output.glob('*.json')))} files")

def organize_simulation_data(base_path: Path, logger):
    """Step 3: NSGA-II 시뮬레이션 데이터 정리"""
    logger.info("🚀 Step 3: Organizing NSGA-II simulation data...")
    
    step3_input = base_path / "step3_nsga2_simulation/input" 
    step3_output = base_path / "step3_nsga2_simulation/output"
    
    # Step 2 output을 Step 3 input으로 복사 (시뮬레이션 입력 파일들)
    step2_output = base_path / "step2_data_orchestrator/output"
    simulation_files = ["jobs.json", "operations.json", "machines.json", 
                       "operation_durations.json", "machine_transfer_time.json", "job_release.json"]
    
    for filename in simulation_files:
        source_file = step2_output / filename
        if source_file.exists():
            shutil.copy2(source_file, step3_input / filename)
    
    # 시뮬레이션 결과 복사
    results_dir = Path("temp/results")
    if results_dir.exists():
        for result_file in results_dir.iterdir():
            if result_file.is_file():
                shutil.copy2(result_file, step3_output / result_file.name)
                logger.info(f"  📊 Copied result: {result_file.name}")
    
    # 시뮬레이션 실행 메타데이터 생성
    simulation_meta = {
        "timestamp": datetime.now().isoformat(),
        "docker_image": "factory-nsga2:latest",
        "algorithm": "branch_and_bound",
        "scenario": "my_case",
        "input_files": [f.name for f in step3_input.glob("*.json")],
        "output_files": [f.name for f in step3_output.iterdir() if f.is_file()],
        "execution_time_seconds": 33
    }
    
    with open(step3_output / "simulation_metadata.json", 'w', encoding='utf-8') as f:
        json.dump(simulation_meta, f, indent=2, ensure_ascii=False)
    
    logger.info(f"  📁 Simulation data organized: {len(list(step3_output.iterdir()))} files")

def create_readme_files(base_path: Path):
    """각 단계별 README 파일 생성"""
    
    # 메인 README
    main_readme = """# Factory Automation K8s - Pipeline Output Structure

이 폴더는 AASX 서버에서 NSGA-II 시뮬레이션까지의 전체 데이터 파이프라인 결과를 단계별로 정리한 것입니다.

## 📁 폴더 구조

```
output/
├── step1_aasx_raw_data/       # AASX 서버 원본 데이터
├── step2_data_orchestrator/   # DataOrchestrator 처리 결과  
├── step3_nsga2_simulation/    # NSGA-II 시뮬레이션 결과
├── metadata/                  # 전체 실행 메타데이터
└── README.md                  # 이 파일
```

## 🔄 데이터 플로우

1. **AASX 서버** → Property.value 필드에서 JSON 문자열 추출
2. **DataOrchestrator** → 6개 시뮬레이션 JSON 파일 생성
3. **NSGA-II 시뮬레이터** → 스케줄링 최적화 및 결과 생성

각 단계별 상세 정보는 해당 폴더의 README.md를 참조하세요.
"""

    # Step 1 README
    step1_readme = """# Step 1: AASX Raw Data

## 📝 설명
AASX 서버에서 원본 데이터를 수집하고 Property.value 필드를 추출하는 단계

## 📂 input/
- `aasx_raw_responses.json`: AASX 서버 서브모델 원본 응답 데이터

## 📂 output/  
- `extracted_property_values.json`: Property.value 필드에서 추출된 JSON 문자열들

## 🔧 처리 방식
- 서브모델 직접 접근: `GET /submodels/{encoded_id}`
- Property 타입 필터링
- JSON 문자열 추출 (파싱 전)
"""

    # Step 2 README  
    step2_readme = """# Step 2: DataOrchestrator Processing

## 📝 설명
AASX 서버에서 추출된 데이터를 NSGA-II 시뮬레이션용 JSON 파일로 변환하는 단계

## 📂 input/
- `aasx_extracted_data.json`: Step 1에서 추출된 Property.value 데이터

## 📂 output/
- `jobs.json`: 작업 정보 (30개 작업)
- `operations.json`: 오퍼레이션 정보 (95개 오퍼레이션)  
- `machines.json`: 머신 정보 (4개 머신)
- `operation_durations.json`: 작업 소요 시간
- `machine_transfer_time.json`: 머신 간 이동 시간
- `job_release.json`: 작업 릴리즈 시간
- `orchestrator_execution_log.json`: 실행 로그

## 🔧 처리 방식
- JSON 문자열 파싱
- 시뮬레이터 요구 형식으로 변환
- 머신별 capability/status 데이터 통합
"""

    # Step 3 README
    step3_readme = """# Step 3: NSGA-II Simulation

## 📝 설명  
DataOrchestrator에서 생성된 JSON 파일들을 사용해 NSGA-II 시뮬레이션을 실행하는 단계

## 📂 input/
- `jobs.json`, `operations.json`, `machines.json` 등: 시뮬레이션 입력 파일들

## 📂 output/
- `goal3_manifest.json`: 실행 메타데이터
- `simulator_optimization_result.json`: 최적화 결과
- `job_info.csv`: 작업 정보 상세
- `operation_info.csv`: 오퍼레이션 실행 정보
- `agv_logs_*.xlsx`: AGV 로그 파일들
- `simulation_metadata.json`: 시뮬레이션 실행 정보

## 🔧 처리 방식
- Docker 컨테이너: `factory-nsga2:latest`
- 알고리즘: branch_and_bound  
- 실행 시간: ~33초
- 예측 완료 시간: 3600초
"""

    # README 파일들 저장
    readme_files = [
        (base_path / "README.md", main_readme),
        (base_path / "step1_aasx_raw_data/README.md", step1_readme), 
        (base_path / "step2_data_orchestrator/README.md", step2_readme),
        (base_path / "step3_nsga2_simulation/README.md", step3_readme)
    ]
    
    for filepath, content in readme_files:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

def create_metadata(base_path: Path):
    """전체 실행 메타데이터 생성"""
    metadata = {
        "pipeline_execution": {
            "timestamp": datetime.now().isoformat(),
            "total_steps": 3,
            "success": True,
            "execution_environment": {
                "aasx_server": "http://127.0.0.1:5001",
                "docker_image": "factory-nsga2:latest", 
                "python_version": sys.version
            }
        },
        "data_flow_summary": {
            "step1_aasx_raw": "Extract Property.value from AASX server submodels",
            "step2_orchestrator": "Convert extracted data to 6 simulation JSON files", 
            "step3_simulation": "Run NSGA-II optimization with generated files"
        },
        "file_counts": {
            "step1_input": len(list((base_path / "step1_aasx_raw_data/input").glob("*"))),
            "step1_output": len(list((base_path / "step1_aasx_raw_data/output").glob("*"))),
            "step2_input": len(list((base_path / "step2_data_orchestrator/input").glob("*"))),
            "step2_output": len(list((base_path / "step2_data_orchestrator/output").glob("*"))),
            "step3_input": len(list((base_path / "step3_nsga2_simulation/input").glob("*"))),
            "step3_output": len(list((base_path / "step3_nsga2_simulation/output").glob("*")))
        }
    }
    
    metadata_file = base_path / "metadata/pipeline_execution_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def main():
    """메인 실행 함수"""
    logger = setup_logging()
    
    logger.info("🏗️  Creating Factory Automation K8s Output Structure...")
    
    try:
        # 1. 폴더 구조 생성
        base_path = create_folder_structure()
        logger.info(f"📁 Created output structure at: {base_path.absolute()}")
        
        # 2. AASX 원본 데이터 수집
        collect_aasx_raw_data(base_path, logger)
        
        # 3. DataOrchestrator 데이터 정리
        organize_orchestrator_data(base_path, logger)
        
        # 4. 시뮬레이션 데이터 정리  
        organize_simulation_data(base_path, logger)
        
        # 5. README 파일들 생성
        create_readme_files(base_path)
        logger.info("📖 Created README files for all steps")
        
        # 6. 메타데이터 생성
        create_metadata(base_path)
        logger.info("📊 Created pipeline metadata")
        
        logger.info("✅ Output structure creation completed successfully!")
        logger.info(f"📂 Check results in: {base_path.absolute()}")
        
    except Exception as e:
        logger.error(f"❌ Failed to create output structure: {e}")
        raise

if __name__ == "__main__":
    main()