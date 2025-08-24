#!/usr/bin/env python3
"""
Goal 3 Simulator Comparison Test
Dummy Simulator vs AASX-Simple Simulator
"""

import json
import subprocess
import os
import sys

def run_curl_request(use_advanced=True):
    """Run API request with or without advanced simulator"""
    
    # Set environment variable
    if use_advanced:
        os.environ['USE_ADVANCED_SIMULATOR'] = 'true'
        simulator_type = "AASX-Simple"
    else:
        os.environ['USE_ADVANCED_SIMULATOR'] = 'false'
        simulator_type = "Dummy"
    
    # Curl command
    curl_cmd = [
        'curl', '-s', '-X', 'POST',
        'http://localhost:8000/execute-goal',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({
            "goal": "predict_first_completion_time",
            "product_id": "P1",
            "quantity": 100
        })
    ]
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Error running curl: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def compare_simulators():
    """Compare results from both simulators"""
    
    print("=" * 70)
    print("🔬 Goal 3: Production Time Prediction - Simulator Comparison")
    print("=" * 70)
    
    # Test with Dummy Simulator
    print("\n📦 Testing with DUMMY Simulator...")
    print("-" * 50)
    dummy_result = run_curl_request(use_advanced=False)
    
    if dummy_result and 'result' in dummy_result:
        result = dummy_result['result']
        print(f"✅ Predicted Time: {result.get('predicted_completion_time', 'N/A')}")
        print(f"📊 Confidence: {result.get('confidence', 'N/A')}")
        print(f"🏷️ Simulator Type: {result.get('simulator_type', 'N/A')}")
        print(f"📝 Details: {result.get('details', 'N/A')}")
        if 'machine_loads' in result:
            print(f"🏭 Machine Loads: {result.get('machine_loads', {})}")
    else:
        print("❌ Failed to get result from Dummy simulator")
    
    # Test with AASX Simulator
    print("\n🚀 Testing with AASX-SIMPLE Simulator...")
    print("-" * 50)
    aasx_result = run_curl_request(use_advanced=True)
    
    if aasx_result and 'result' in aasx_result:
        result = aasx_result['result']
        print(f"✅ Predicted Time: {result.get('predicted_completion_time', 'N/A')}")
        print(f"📊 Confidence: {result.get('confidence', 'N/A')}")
        print(f"🏷️ Simulator Type: {result.get('simulator_type', 'N/A')}")
        print(f"📝 Details: {result.get('details', 'N/A')}")
        if 'machine_loads' in result:
            print(f"🏭 Machine Loads: {result.get('machine_loads', {})}")
        if 'simulation_time_minutes' in result:
            print(f"⏱️ Total Simulation Time: {result.get('simulation_time_minutes')} minutes")
    else:
        print("❌ Failed to get result from AASX simulator")
    
    # Comparison Summary
    print("\n" + "=" * 70)
    print("📊 COMPARISON SUMMARY")
    print("=" * 70)
    
    if dummy_result and aasx_result:
        dummy_res = dummy_result.get('result', {})
        aasx_res = aasx_result.get('result', {})
        
        print("\n🎯 Key Differences:")
        print("-" * 30)
        
        # Compare completion times
        dummy_time = dummy_res.get('predicted_completion_time', 'N/A')
        aasx_time = aasx_res.get('predicted_completion_time', 'N/A')
        print(f"Completion Time:")
        print(f"  • Dummy: {dummy_time}")
        print(f"  • AASX:  {aasx_time}")
        
        # Compare confidence
        dummy_conf = dummy_res.get('confidence', 0)
        aasx_conf = aasx_res.get('confidence', 0)
        print(f"\nConfidence Score:")
        print(f"  • Dummy: {dummy_conf}")
        print(f"  • AASX:  {aasx_conf}")
        
        # Machine utilization (only AASX has this)
        if 'machine_loads' in aasx_res:
            print(f"\nMachine Utilization:")
            print(f"  • Dummy: Not available")
            print(f"  • AASX:  {aasx_res['machine_loads']}")
        
        # Analysis depth
        print(f"\nAnalysis Depth:")
        print(f"  • Dummy: Fixed/Static result")
        print(f"  • AASX:  Dynamic analysis with {aasx_res.get('details', 'N/A')}")
        
        print("\n✨ Advantages of AASX Simulator:")
        print("  1. Real scheduling logic based on actual job operations")
        print("  2. Machine load balancing and utilization tracking")
        print("  3. Dynamic confidence calculation")
        print("  4. Detailed metrics for optimization")
        print("  5. No heavy dependencies (pandas/numpy removed)")
    
    print("\n" + "=" * 70)
    print("✅ Comparison Test Complete!")
    print("=" * 70)

if __name__ == "__main__":
    compare_simulators()