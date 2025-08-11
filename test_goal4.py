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
            expected_location = "Painter-01"
            expected_process = "painting"
            expected_progress = 65
            
            if (tracking_info.get("current_location") == expected_location and
                tracking_info.get("current_process") == expected_process and
                tracking_info.get("progress_percentage") == expected_progress):
                print("\n✅ Test PASSED: Product-C is at expected location")
                print(f"   📍 Location: {expected_location}")
                print(f"   ⚙️  Process: {expected_process}")
                print(f"   📈 Progress: {expected_progress}%")
                return True
            else:
                print("\n❌ Test FAILED: Unexpected tracking data")
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