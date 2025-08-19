#!/usr/bin/env python3
"""
표준 AAS 서버 연결 테스트 스크립트
Standard AAS Server Connection Test Script

이 스크립트는 외부 표준 AAS 서버와의 연결을 테스트하고,
Mock 서버와의 데이터 포맷 차이를 확인합니다.
"""

import sys
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent))
from aas_query_client import AASQueryClient

def test_server_connection(ip: str, port: int) -> bool:
    """Test basic connectivity to the server"""
    print(f"\n🔍 Testing connection to {ip}:{port}...")
    
    try:
        url = f"http://{ip}:{port}"
        response = requests.get(url, timeout=5)
        print(f"✅ Server responded with status code: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {ip}:{port}")
        return False
    except requests.exceptions.Timeout:
        print(f"⏱️ Connection timeout to {ip}:{port}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_aas_endpoints(client: AASQueryClient) -> Dict[str, Any]:
    """Test various AAS server endpoints"""
    results = {}
    
    print("\n📋 Testing AAS Server Endpoints:")
    
    # Test 1: Get all shells
    print("\n1️⃣ Testing /shells endpoint...")
    try:
        shells = client.get_all_shells()
        if shells:
            results['shells'] = {
                'success': True,
                'count': len(shells),
                'sample': shells[0] if shells else None
            }
            print(f"   ✅ Found {len(shells)} shells")
        else:
            results['shells'] = {'success': False, 'error': 'No shells returned'}
            print("   ⚠️ No shells found or error occurred")
    except Exception as e:
        results['shells'] = {'success': False, 'error': str(e)}
        print(f"   ❌ Error: {e}")
    
    # Test 2: Get all submodels
    print("\n2️⃣ Testing /submodels endpoint...")
    try:
        submodels = client.get_all_submodels()
        if submodels:
            results['submodels'] = {
                'success': True,
                'count': len(submodels),
                'sample_ids': [sm.get('id', 'no-id')[:50] for sm in submodels[:3]]
            }
            print(f"   ✅ Found {len(submodels)} submodels")
        else:
            results['submodels'] = {'success': False, 'error': 'No submodels returned'}
            print("   ⚠️ No submodels found")
    except Exception as e:
        results['submodels'] = {'success': False, 'error': str(e)}
        print(f"   ❌ Error: {e}")
    
    # Test 3: Test specific submodel retrieval (if we have any)
    print("\n3️⃣ Testing specific submodel retrieval...")
    test_submodel_id = "urn:factory:submodel:job_log"  # Expected from our system
    
    try:
        submodel = client.get_submodel_by_id(test_submodel_id)
        if submodel:
            results['specific_submodel'] = {
                'success': True,
                'id': test_submodel_id,
                'has_elements': 'submodelElements' in submodel
            }
            print(f"   ✅ Successfully retrieved submodel: {test_submodel_id}")
        else:
            results['specific_submodel'] = {'success': False, 'error': 'Submodel not found'}
            print(f"   ⚠️ Submodel {test_submodel_id} not found")
    except Exception as e:
        results['specific_submodel'] = {'success': False, 'error': str(e)}
        print(f"   ❌ Error retrieving submodel: {e}")
    
    return results

def compare_with_mock_server():
    """Compare data format between Mock and Standard servers"""
    print("\n🔄 Comparing Mock Server vs Standard Server formats...")
    
    # Mock server test
    print("\n📦 Mock Server (localhost:5001):")
    mock_url = "http://127.0.0.1:5001/submodels/urn:factory:submodel:job_log"
    try:
        response = requests.get(mock_url, timeout=5)
        if response.status_code == 200:
            mock_data = response.json()
            print("   ✅ Mock server response structure:")
            print(f"   - Keys: {list(mock_data.keys())[:5]}")
            print(f"   - Has submodelElements: {'submodelElements' in mock_data}")
    except Exception as e:
        print(f"   ❌ Mock server error: {e}")
    
    print("\n" + "="*60)

def main():
    """Main test execution"""
    print("="*60)
    print("🚀 AAS Standard Server Connection Test")
    print("="*60)
    
    # Test configurations
    servers_to_test = [
        {"name": "Proposed External Server", "ip": "YOUR_SERVER_ADDRESS", "port": 5001},
        {"name": "Local Standard Server", "ip": "127.0.0.1", "port": 5001},
        {"name": "Docker Host", "ip": "host.docker.internal", "port": 5001},
    ]
    
    successful_server = None
    
    # Test each server configuration
    for server in servers_to_test:
        print(f"\n{'='*60}")
        print(f"Testing: {server['name']}")
        print(f"{'='*60}")
        
        if test_server_connection(server['ip'], server['port']):
            client = AASQueryClient(server['ip'], server['port'])
            results = test_aas_endpoints(client)
            
            # Check if this is a valid AAS server
            if results.get('shells', {}).get('success') or \
               results.get('submodels', {}).get('success'):
                successful_server = server
                print(f"\n✅ {server['name']} appears to be a valid AAS server!")
                
                # Save results
                output_file = Path("test_results_standard_server.json")
                with open(output_file, 'w') as f:
                    json.dump({
                        'server': server,
                        'results': results
                    }, f, indent=2)
                print(f"📝 Results saved to {output_file}")
                break
    
    # Compare with mock server if we found a working standard server
    if successful_server:
        compare_with_mock_server()
    
    # Final summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    if successful_server:
        print(f"✅ Successfully connected to: {successful_server['name']}")
        print(f"   Address: {successful_server['ip']}:{successful_server['port']}")
        print("\n📌 Next Steps:")
        print("   1. Update config.py with this server information")
        print("   2. Modify agent.py to use AASQueryClient")
        print("   3. Test Goal 4 with the standard server")
    else:
        print("❌ No working AAS standard server found")
        print("\n💡 Recommendations:")
        print("   1. Check if external server IP is correct")
        print("   2. Verify firewall/network settings")
        print("   3. Consider setting up local standard AAS server")
        print("   4. Continue using Mock server for now")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()