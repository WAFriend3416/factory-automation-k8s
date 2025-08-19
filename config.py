# config.py
import os
from pathlib import Path

# 이 파일이 있는 디렉토리를 기준으로 모든 경로를 설정합니다.
BASE_DIR = Path(__file__).resolve().parent

# 온톨로지 및 AAS 데이터 파일 경로
ONTOLOGY_FILE_PATH = BASE_DIR / "ontology" / "factory_ontology_v2_final_corrected.ttl"
AAS_DATA_FILE_PATH = BASE_DIR / "aas_mock_server" / "data" / "aas_model_final_expanded.json"

# ============================================================
# AAS 서버 설정 - Mock과 Standard 서버 병행 운영 지원
# ============================================================

# 서버 타입 선택: "mock" 또는 "standard"
# 환경변수 USE_STANDARD_SERVER가 "true"면 표준 서버 사용
USE_STANDARD_SERVER = os.environ.get("USE_STANDARD_SERVER", "false").lower() == "true"

if USE_STANDARD_SERVER:
    # ===== 표준 AAS 서버 설정 =====
    AAS_SERVER_TYPE = "standard"
    
    # 표준 서버 IP와 포트
    # 주의: 외부 서버(YOUR_SERVER_ADDRESS)는 현재 제대로 작동하지 않음
    # 로컬에 표준 서버를 설치하거나 다른 서버 주소를 사용하세요
    AAS_SERVER_IP = os.environ.get("AAS_SERVER_IP", "127.0.0.1")  
    AAS_SERVER_PORT = int(os.environ.get("AAS_SERVER_PORT", 51310))  # 표준 서버 기본 포트
    
    # URL 형식으로도 제공 (기존 코드 호환성)
    AAS_SERVER_URL = f"http://{AAS_SERVER_IP}:{AAS_SERVER_PORT}"
    
    print(f"🔄 Using STANDARD AAS Server at {AAS_SERVER_URL}")
else:
    # ===== Mock AAS 서버 설정 (기본값) =====
    AAS_SERVER_TYPE = "mock"
    
    # Mock 서버 URL
    AAS_SERVER_URL = os.environ.get("AAS_SERVER_URL", "http://127.0.0.1:5001")
    
    # IP와 포트로 분리 (표준 서버와 일관성 유지)
    from urllib.parse import urlparse
    parsed = urlparse(AAS_SERVER_URL)
    AAS_SERVER_IP = parsed.hostname or "127.0.0.1"
    AAS_SERVER_PORT = parsed.port or 5001
    
    print(f"📦 Using MOCK AAS Server at {AAS_SERVER_URL}")

# 디버그 정보 출력 (개발 중에만 사용)
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"
if DEBUG_MODE:
    print(f"[DEBUG] Server Type: {AAS_SERVER_TYPE}")
    print(f"[DEBUG] Server IP: {AAS_SERVER_IP}")
    print(f"[DEBUG] Server Port: {AAS_SERVER_PORT}")
    print(f"[DEBUG] Ontology Path: {ONTOLOGY_FILE_PATH}")
    print(f"[DEBUG] AAS Data Path: {AAS_DATA_FILE_PATH}")