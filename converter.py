# converter.py (v5.0 - Final Spec-Compliant Converter)
import json
import zipfile
from pathlib import Path
import shutil

# --- 입력 및 출력 경로 설정 ---
BASE_DIR = Path(__file__).resolve().parent
SOURCE_JSON_PATH = BASE_DIR / "aas_mock_server" / "data" / "aas_model_final_expanded.json"
OUTPUT_DIR = BASE_DIR / "dist"
OUTPUT_AASX_PATH = OUTPUT_DIR / "factory_aas.aasx"

# --- OPC 표준에 필요한 XML 파일 내용 (고정값) ---
RELS_CONTENT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="aasx-origin" Target="/aasx/aasx-origin" Type="http://admin-shell.io/aasx/relationships/aasx-origin"/>
    <Relationship Id="aas-spec" Target="/aasx/data.json" Type="http://admin-shell.io/aasx/relationships/aas-spec"/>
</Relationships>"""

CONTENT_TYPES_CONTENT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="json" ContentType="application/json"/>
</Types>"""

def transform_data_according_to_spec(source_data: dict) -> dict:
    """
    "AAS 데이터 변환 지시사항"에 명시된 모든 규칙에 따라
    소스 JSON 데이터의 구조를 변환하는 함수.
    """
    # 원본 데이터를 깊은 복사하여 원본 파일의 수정을 방지합니다.
    data = json.loads(json.dumps(source_data))

    # 규칙 1: 최상위 구조에 conceptDescriptions 추가
    transformed = {"conceptDescriptions": []}

    # 규칙 2: AssetAdministrationShells 변환
    transformed_shells = []
    for shell in data.get('assetAdministrationShells', []):
        shell['modelType'] = {"name": "AssetAdministrationShell"}
        if 'assetInformation' in shell:
            shell['assetInformation']['globalAssetId'] = shell.get('id', '')
        
        new_submodel_refs = []
        for sm_ref in shell.get('submodels', []):
            new_submodel_refs.append({
                "type": "ModelReference",
                "keys": sm_ref.get('keys', [])
            })
        shell['submodels'] = new_submodel_refs
        transformed_shells.append(shell)
    transformed['assetAdministrationShells'] = transformed_shells

    # 규칙 3 & 4: Submodels 및 SubmodelElements 변환
    transformed_submodels = []
    for submodel in data.get('submodels', []):
        submodel['modelType'] = {"name": "Submodel"}
        submodel['kind'] = "Instance"
        
        new_elements = []
        for element in submodel.get('submodelElements', []):
            if 'modelType' in element:
                element['modelType'] = {"name": "Property"}
            
            # value가 객체나 배열이면 JSON 문자열로 변환 (핵심 규칙)
            if isinstance(element.get('value'), (dict, list)):
                element['value'] = json.dumps(element['value'], ensure_ascii=False)
            
            element['valueType'] = "xs:string"
            new_elements.append(element)
        submodel['submodelElements'] = new_elements
        transformed_submodels.append(submodel)
    transformed['submodels'] = transformed_submodels
    
    return transformed

def create_aasx_package():
    """메인 실행 함수: 데이터 변환 및 AASX 패키징 수행"""
    # 0. 준비 작업
    if not SOURCE_JSON_PATH.exists():
        print(f"❌ ERROR: 소스 파일이 없습니다: {SOURCE_JSON_PATH}")
        return

    if OUTPUT_DIR.exists(): 
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    print(f"📂 출력 폴더 '{OUTPUT_DIR}' 준비 완료.")

    # 1. 소스 JSON 파일 로드
    with open(SOURCE_JSON_PATH, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    print("📰 소스 JSON 파일을 성공적으로 읽었습니다.")

    # 2. 데이터 구조 변환 실행
    final_data_for_packaging = transform_data_according_to_spec(source_data)
    print("🔧 데이터 구조를 표준 명세에 맞게 변환했습니다.")

    # 3. AASX (ZIP) 파일 생성 및 패키징
    with zipfile.ZipFile(OUTPUT_AASX_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 3.1. OPC 표준 파일 추가
        zf.writestr('[Content_Types].xml', CONTENT_TYPES_CONTENT)
        zf.writestr('_rels/.rels', RELS_CONTENT)
        zf.writestr('aasx/aasx-origin', '') # 내용이 없는 빈 파일
        
        # 3.2. 변환된 메인 데이터 파일 추가
        zf.writestr('aasx/data.json', json.dumps(final_data_for_packaging, indent=2, ensure_ascii=False))
    
    print(f"\n✨ 최종 AASX 파일 생성 완료: {OUTPUT_AASX_PATH}")

if __name__ == "__main__":
    create_aasx_package()