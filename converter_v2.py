# converter_v2.py - Enhanced Standard AAS Compliant Converter
import json
import zipfile
from pathlib import Path
import shutil

# --- 입력 및 출력 경로 설정 ---
BASE_DIR = Path(__file__).resolve().parent
SOURCE_JSON_PATH = BASE_DIR / "aas_mock_server" / "data" / "aas_model_final_expanded.json"
OUTPUT_DIR = BASE_DIR / "dist"
OUTPUT_AASX_PATH = OUTPUT_DIR / "factory_aas_v2.aasx"

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
    Enhanced transformation with better standard compliance
    """
    # 원본 데이터를 깊은 복사
    data = json.loads(json.dumps(source_data))

    # 규칙 1: 최상위 구조에 conceptDescriptions 추가
    transformed = {"conceptDescriptions": []}

    # 규칙 2: AssetAdministrationShells 변환
    transformed_shells = []
    for shell in data.get('assetAdministrationShells', []):
        shell['modelType'] = {"name": "AssetAdministrationShell"}
        
        # assetInformation 처리
        if 'assetInformation' in shell:
            shell['assetInformation']['globalAssetId'] = shell.get('id', '')
            # assetType 추가 (표준 준수)
            if 'assetType' not in shell['assetInformation']:
                shell['assetInformation']['assetType'] = "Type"
        
        # Submodel References 처리
        new_submodel_refs = []
        for sm_ref in shell.get('submodels', []):
            # Keys에 idType 추가
            enhanced_keys = []
            for key in sm_ref.get('keys', []):
                enhanced_key = {
                    "type": key.get('type', 'Submodel'),
                    "value": key.get('value', ''),
                    "idType": "IRI"  # 표준 준수를 위해 추가
                }
                enhanced_keys.append(enhanced_key)
            
            new_submodel_refs.append({
                "type": "ModelReference",
                "keys": enhanced_keys
            })
        shell['submodels'] = new_submodel_refs
        transformed_shells.append(shell)
    transformed['assetAdministrationShells'] = transformed_shells

    # 규칙 3 & 4: Submodels 및 SubmodelElements 변환
    transformed_submodels = []
    for submodel in data.get('submodels', []):
        submodel['modelType'] = {"name": "Submodel"}
        submodel['kind'] = "Instance"
        
        # Optional: Add basic semanticId for standard compliance
        if 'semanticId' not in submodel:
            submodel['semanticId'] = {
                "type": "ModelReference",
                "keys": [{
                    "type": "GlobalReference",
                    "value": f"urn:factory:semantic:{submodel.get('idShort', 'unknown')}",
                    "idType": "IRI"
                }]
            }
        
        new_elements = []
        for element in submodel.get('submodelElements', []):
            # modelType 처리
            if 'modelType' in element:
                element['modelType'] = {"name": "Property"}
            
            # value가 객체나 배열이면 JSON 문자열로 변환
            if isinstance(element.get('value'), (dict, list)):
                element['value'] = json.dumps(element['value'], ensure_ascii=False)
            
            # valueType 수정: xs:string → string
            element['valueType'] = "string"  # xs: 접두사 제거
            
            # Optional: Add category
            if 'category' not in element:
                element['category'] = "VARIABLE"
            
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

    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)
    print(f"📂 출력 폴더 '{OUTPUT_DIR}' 준비 완료.")

    # 1. 소스 JSON 파일 로드
    with open(SOURCE_JSON_PATH, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    print("📰 소스 JSON 파일을 성공적으로 읽었습니다.")

    # 2. 데이터 구조 변환 실행
    final_data_for_packaging = transform_data_according_to_spec(source_data)
    print("🔧 데이터 구조를 표준 명세에 맞게 변환했습니다.")
    print("  ✅ valueType: xs:string → string")
    print("  ✅ Keys에 idType 추가")
    print("  ✅ semanticId 추가")
    print("  ✅ assetType 추가")

    # 3. AASX (ZIP) 파일 생성 및 패키징
    with zipfile.ZipFile(OUTPUT_AASX_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 3.1. OPC 표준 파일 추가
        zf.writestr('[Content_Types].xml', CONTENT_TYPES_CONTENT)
        zf.writestr('_rels/.rels', RELS_CONTENT)
        zf.writestr('aasx/aasx-origin', '') # 내용이 없는 빈 파일
        
        # 3.2. 변환된 메인 데이터 파일 추가
        zf.writestr('aasx/data.json', json.dumps(final_data_for_packaging, indent=2, ensure_ascii=False))
    
    print(f"\n✨ 최종 AASX 파일 생성 완료: {OUTPUT_AASX_PATH}")
    print("📋 표준 AAS 서버 호환성 개선 사항:")
    print("  - valueType 형식 수정")
    print("  - ModelReference keys에 idType 추가")
    print("  - semanticId 기본값 추가")
    print("  - assetType 추가")

if __name__ == "__main__":
    create_aasx_package()