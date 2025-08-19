#!/usr/bin/env python3
"""
Goal 4 테스트 스크립트
제품 C의 현재 위치를 추적하는 기능을 테스트합니다.
"""

import requests
import json
import sys

def test_goal4():
    """Goal 4: 제품 위치 추적 테스트"""
    
    # API 엔드포인트
    url = "http://127.0.0.1:8000/execute-goal"
    
    # 테스트 데이터
    test_data = {
        "goal": "track_product_position",
        "product_id": "Product-C"
    }
    
    print("🚀 Testing Goal 4: Track Product Position")
    print(f"📦 Product ID: {test_data['product_id']}")
    print("-" * 50)
    
    try:
        # API 요청
        response = requests.post(url, json=test_data, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        # 응답 파싱
        result = response.json()
        
        print("✅ API Response received successfully!")
        print("\n📊 Results:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 결과 검증
        if result.get("result"):
            tracking_info = result["result"]
            
            # 표준 서버 형식 처리 (CamelCase 키)
            if isinstance(tracking_info, dict):
                # Mock 서버와 표준 서버 모두 지원
                location = tracking_info.get("current_location") or tracking_info.get("CurrentLocation")
                process = tracking_info.get("current_process") or tracking_info.get("CurrentProcess")
                progress = tracking_info.get("progress_percentage") or tracking_info.get("ProgressPercentage")
                
                # progress가 문자열일 수 있으므로 int로 변환
                if isinstance(progress, str):
                    progress = int(progress)
                
                expected_location = "Painter-01"
                expected_process = "painting"
                expected_progress = 65
                
                if (location == expected_location and
                    process == expected_process and
                    progress == expected_progress):
                    print("\n✅ Test PASSED: Product-C is at expected location")
                    print(f"   📍 Location: {location}")
                    print(f"   ⚙️  Process: {process}")
                    print(f"   📈 Progress: {progress}%")
                    return True
                else:
                    print("\n❌ Test FAILED: Unexpected tracking data")
                    print(f"   Expected: Location={expected_location}, Process={expected_process}, Progress={expected_progress}")
                    print(f"   Got: Location={location}, Process={process}, Progress={progress}")
                    return False
            else:
                print(f"\n❌ Test FAILED: Unexpected result format: {type(tracking_info)}")
                return False
        else:
            print("\n❌ Test FAILED: No result in response")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to API server")
        print("💡 Make sure both servers are running:")
        print("   1. Mock AAS Server (port 5001): python aas_mock_server/server.py")
        print("   2. FastAPI Server (port 8000): uvicorn api.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_goal4()
    sys.exit(0 if success else 1)