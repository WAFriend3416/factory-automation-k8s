#!/usr/bin/env python3
"""
Goal 1 테스트 스크립트
실패한 냉각 Job 조회 기능을 테스트합니다.
"""

import requests
import json
import sys

def test_goal1():
    """Goal 1: query_failed_jobs_with_cooling 테스트"""
    
    # API 엔드포인트
    url = "http://127.0.0.1:8000/execute-goal"
    
    # 테스트 데이터
    payload = {
        "goal": "query_failed_jobs_with_cooling",
        "date": "2025-07-17"
    }
    
    print("🚀 Testing Goal 1: Query Failed Cooling Jobs")
    print(f"📅 Date: {payload['date']}")
    print("-" * 50)
    
    try:
        # API 호출
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        # 결과 파싱
        result = response.json()
        
        print("✅ API Response received successfully!")
        print("\n📊 Results:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 결과 검증
        if result.get("result"):
            failed_jobs = result["result"]
            print(f"\n📈 Found {len(failed_jobs)} failed cooling job(s):")
            
            for job in failed_jobs:
                print(f"  - Job ID: {job['job_id']}")
                print(f"    Date: {job['date']}")
                print(f"    Status: {job['status']}")
                print(f"    Process Steps: {', '.join(job['process_steps'])}")
                print(f"    Failed At: {job.get('failed_at', 'N/A')}")
                
            # 예상 결과 확인 (J-1002가 있어야 함)
            expected_job_id = "J-1002"
            if any(job['job_id'] == expected_job_id for job in failed_jobs):
                print(f"\n✅ Test PASSED: Found expected job {expected_job_id}")
                return True
            else:
                print(f"\n❌ Test FAILED: Expected job {expected_job_id} not found")
                return False
        else:
            print("\n⚠️ No results returned")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server")
        print("Make sure both servers are running:")
        print("  1. Mock AAS Server: python aas_mock_server/server.py")
        print("  2. FastAPI Server: uvicorn api.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_goal1()
    sys.exit(0 if success else 1)