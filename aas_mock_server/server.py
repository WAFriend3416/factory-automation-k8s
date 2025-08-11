# aas_mock_server/server.py
import json
from flask import Flask, jsonify, abort
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 경로에 추가합니다.
sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import AAS_DATA_FILE_PATH

app = Flask(__name__)

# 서버 시작 시 AAS 데이터를 메모리에 로드합니다.
try:
    with open(AAS_DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        aas_data = json.load(f)
        # 빠른 조회를 위해 Submodel을 id 기준으로 딕셔너리로 만듭니다.
        submodels_by_id = {sm['id']: sm for sm in aas_data.get('submodels', [])}
        print("✅ AAS Mock Data loaded successfully.")
except FileNotFoundError:
    print(f"❌ ERROR: AAS data file not found at {AAS_DATA_FILE_PATH}")
    aas_data = {}
    submodels_by_id = {}


@app.route('/submodels/<path:submodel_id>', methods=['GET'])
def get_submodel_by_id(submodel_id: str):
    """
    URL 경로로 받은 URN ID를 사용하여 Submodel을 찾습니다.
    예: /submodels/urn:factory:submodel:job_log (실제로는 URL 인코딩되어 전달됨)
    """
    # URL 인코딩된 URN을 디코딩할 필요는 Flask가 자동으로 처리해 줍니다.
    if submodel_id in submodels_by_id:
        return jsonify(submodels_by_id[submodel_id])
    
    abort(404, description=f"Submodel with id '{submodel_id}' not found.")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)