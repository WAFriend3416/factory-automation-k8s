# config.py
import os
from pathlib import Path

# 이 파일이 있는 디렉토리를 기준으로 모든 경로를 설정합니다.
BASE_DIR = Path(__file__).resolve().parent

# 온톨로지 및 AAS 데이터 파일 경로
ONTOLOGY_FILE_PATH = BASE_DIR / "ontology" / "factory_ontology_v2_final_corrected.ttl"
AAS_DATA_FILE_PATH = BASE_DIR / "aas_mock_server" / "data" / "aas_model_final_expanded.json"

# Mock AAS 서버의 주소. 환경변수에서 읽거나 기본값 사용
AAS_SERVER_URL = os.environ.get("AAS_SERVER_URL", "http://127.0.0.1:5001")