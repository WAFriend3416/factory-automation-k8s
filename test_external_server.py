#!/usr/bin/env python3
"""
외부 표준 AAS 서버 테스트 스크립트
"""
import requests
import json
import base64

BASE_URL = "http://YOUR_SERVER_ADDRESS:5001"

def to_base64url(s):
    """Base64 URL 인코딩"""
    return base64.urlsafe_b64encode(s.encode('utf-8')).rstrip(b'=').decode('ascii')

def test_server():
    print("="*60)
    print("🔍 외부 AAS 서버 테스트")
    print("="*60)
    
    # 1. 서버 연결 테스트
    print("\n1️⃣ 서버 연결 테스트...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ 서버 응답: {response.status_code}")
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return
    
    # 2. /shells 엔드포인트 테스트
    print("\n2️⃣ /shells 엔드포인트 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/shells")
        print(f"상태 코드: {response.status_code}")
        if response.status_code == 200:
            shells = response.json()
            if 'result' in shells:
                shells = shells['result']
            print(f"✅ Shell 개수: {len(shells)}")
            for i, shell in enumerate(shells[:2]):  # 처음 2개만
                print(f"\n  Shell {i+1}:")
                print(f"    - ID: {shell.get('id', 'N/A')}")
                print(f"    - idShort: {shell.get('idShort', 'N/A')}")
                if 'submodels' in shell:
                    print(f"    - Submodels: {len(shell['submodels'])} 개")
        else:
            print(f"❌ 응답 실패: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 에러: {e}")
    
    # 3. /submodels 엔드포인트 테스트 (우리 URN 형식)
    print("\n3️⃣ 우리 팩토리 Submodel 조회 시도...")
    our_submodels = [
        "urn:factory:submodel:job_log",
        "urn:factory:submodel:tracking_data:product-c",
        "urn:factory:machine:cnc-01"
    ]
    
    for sm_id in our_submodels:
        encoded_id = to_base64url(sm_id)
        url = f"{BASE_URL}/submodels/{encoded_id}"
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"  ✅ {sm_id}: 존재함!")
            else:
                print(f"  ❌ {sm_id}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {sm_id}: 에러 - {e}")
    
    # 4. 실제 존재하는 Shell의 Submodel 조회
    print("\n4️⃣ 실제 서버에 있는 Submodel 조회...")
    try:
        # 먼저 shells를 가져옴
        response = requests.get(f"{BASE_URL}/shells")
        if response.status_code == 200:
            shells = response.json()
            if 'result' in shells:
                shells = shells['result']
            
            if shells and len(shells) > 0:
                first_shell = shells[0]
                shell_id = first_shell.get('id')
                
                if shell_id:
                    # Shell의 Submodel 조회
                    if 'submodels' in first_shell and len(first_shell['submodels']) > 0:
                        first_submodel_ref = first_shell['submodels'][0]
                        if 'keys' in first_submodel_ref and len(first_submodel_ref['keys']) > 0:
                            submodel_id = first_submodel_ref['keys'][0].get('value')
                            
                            if submodel_id:
                                print(f"  Submodel ID: {submodel_id}")
                                encoded_sm_id = to_base64url(submodel_id)
                                url = f"{BASE_URL}/submodels/{encoded_sm_id}"
                                
                                response = requests.get(url)
                                if response.status_code == 200:
                                    sm_data = response.json()
                                    print(f"  ✅ Submodel 조회 성공!")
                                    print(f"    - idShort: {sm_data.get('idShort', 'N/A')}")
                                    if 'submodelElements' in sm_data:
                                        print(f"    - Elements: {len(sm_data['submodelElements'])} 개")
                                else:
                                    print(f"  ❌ Submodel 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 에러: {e}")
    
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    print("• 서버는 작동 중이지만 우리 팩토리 데이터는 없음")
    print("• ExampleMotor 같은 다른 프로젝트의 데이터만 존재")
    print("• Mock 서버를 계속 사용해야 함")
    print("="*60)

if __name__ == "__main__":
    test_server()