#!/usr/bin/env python3
"""
Goal 3 상세 실행 결과 테스트
각 단계별 입력/출력을 자세히 확인
"""

import json
import subprocess
import os
import sys
from datetime import datetime

def run_detailed_test():
    """Goal 3 상세 테스트 실행"""
    
    print("=" * 80)
    print("🔬 Goal 3: 생산 시간 예측 - 단계별 상세 실행 결과")
    print("=" * 80)
    print(f"📅 테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # 환경변수 설정
    os.environ['USE_ADVANCED_SIMULATOR'] = 'true'
    os.environ['DEBUG_MODE'] = 'true'
    
    # API 요청 데이터
    request_data = {
        "goal": "predict_first_completion_time",
        "product_id": "P1",
        "quantity": 100
    }
    
    print("\n📤 [INPUT] API 요청 데이터:")
    print("-" * 40)
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    # Curl 명령 실행
    curl_cmd = [
        'curl', '-s', '-X', 'POST',
        'http://localhost:8000/execute-goal',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(request_data)
    ]
    
    print("\n🔄 API 호출 중...")
    print("-" * 40)
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            response = json.loads(result.stdout)
            
            print("\n📥 [OUTPUT] API 응답:")
            print("-" * 40)
            print(json.dumps(response, indent=2, ensure_ascii=False))
            
            # 결과 상세 분석
            if 'result' in response:
                analyze_result(response['result'])
            
            return response
        else:
            print(f"❌ 오류: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        return None

def analyze_result(result):
    """결과 상세 분석"""
    
    print("\n" + "=" * 80)
    print("📊 시뮬레이션 결과 상세 분석")
    print("=" * 80)
    
    # 기본 정보
    print("\n🎯 기본 정보:")
    print("-" * 40)
    print(f"• 예측 완료 시간: {result.get('predicted_completion_time', 'N/A')}")
    print(f"• 신뢰도: {result.get('confidence', 0) * 100:.1f}%")
    print(f"• 시뮬레이터 타입: {result.get('simulator_type', 'N/A')}")
    print(f"• 실행 모드: {result.get('execution_mode', 'N/A')}")
    
    # 시뮬레이션 시간 분석
    if 'simulation_time_minutes' in result:
        print("\n⏱️ 시간 분석:")
        print("-" * 40)
        total_minutes = result['simulation_time_minutes']
        hours = total_minutes // 60
        minutes = total_minutes % 60
        print(f"• 총 시뮬레이션 시간: {total_minutes}분 ({hours}시간 {minutes}분)")
        
        # 시작 시간 계산 (08:00 기준)
        from datetime import datetime, timedelta
        start_time = datetime(2025, 8, 11, 8, 0)
        end_time = start_time + timedelta(minutes=total_minutes)
        print(f"• 시작 시간: {start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"• 완료 시간: {end_time.strftime('%Y-%m-%d %H:%M')}")
    
    # 머신 로드 분석
    if 'machine_loads' in result:
        print("\n🏭 머신별 작업 부하:")
        print("-" * 40)
        machine_loads = result['machine_loads']
        total_load = sum(machine_loads.values())
        
        for machine, load in machine_loads.items():
            percentage = (load / total_load * 100) if total_load > 0 else 0
            bar_length = int(percentage / 5)  # 20칸 막대그래프
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"• {machine}: {load:3d}분 [{bar}] {percentage:.1f}%")
        
        print(f"\n• 총 작업량: {total_load}분")
        print(f"• 평균 부하: {total_load / len(machine_loads):.1f}분/머신")
        print(f"• 최대 부하: {max(machine_loads.values())}분 ({max(machine_loads, key=machine_loads.get)})")
        print(f"• 최소 부하: {min(machine_loads.values())}분 ({min(machine_loads, key=machine_loads.get)})")
    
    # 상세 정보
    if 'details' in result:
        print("\n📝 상세 정보:")
        print("-" * 40)
        print(f"• {result['details']}")
    
    # Job 정보
    if 'job_name' in result:
        print("\n🔧 실행 정보:")
        print("-" * 40)
        print(f"• Job 이름: {result['job_name']}")

def check_simulation_data():
    """시뮬레이션 데이터 파일 확인"""
    
    print("\n" + "=" * 80)
    print("📁 시뮬레이션 데이터 파일 확인")
    print("=" * 80)
    
    # 데이터 경로 확인
    data_paths = [
        "/tmp/factory_automation/current",
        "/tmp/factory_automation/scenarios/my_case"
    ]
    
    for path in data_paths:
        print(f"\n📂 경로: {path}")
        print("-" * 40)
        
        if os.path.exists(path):
            files = ['jobs.json', 'machines.json', 'operations.json', 
                    'operation_durations.json', 'routing_result.json']
            
            for file in files:
                file_path = os.path.join(path, file)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            
                        if isinstance(data, list):
                            print(f"  ✅ {file}: {len(data)} items")
                            # 첫 번째 아이템 샘플 출력
                            if data and len(str(data[0])) < 200:
                                print(f"     샘플: {data[0]}")
                        elif isinstance(data, dict):
                            print(f"  ✅ {file}: {len(data)} keys")
                            # 키 목록 출력
                            if len(data) < 10:
                                print(f"     키: {list(data.keys())}")
                    except Exception as e:
                        print(f"  ❌ {file}: 읽기 실패 - {e}")
                else:
                    print(f"  ⚠️ {file}: 파일 없음")
        else:
            print("  ❌ 경로가 존재하지 않음")

def show_execution_flow():
    """실행 흐름 다이어그램"""
    
    print("\n" + "=" * 80)
    print("🔄 Goal 3 실행 흐름")
    print("=" * 80)
    
    flow = """
    [1] API 요청 수신
         ↓
         Input: {
           "goal": "predict_first_completion_time",
           "product_id": "P1",
           "quantity": 100
         }
         
    [2] 온톨로지 기반 실행 계획 생성 (Planner)
         ↓
         Output: [
           ActionFetchProcessSpec,
           ActionFetchAllMachineData,
           ActionAssembleSimulatorInputs,
           ActionRunSimulator
         ]
         
    [3] 각 Action 실행 (Agent)
         ↓
         3.1) ActionFetchProcessSpec
              → AAS에서 P1의 프로세스 스펙 조회
              → Output: ProcessSpecification Submodel
              
         3.2) ActionFetchAllMachineData
              → AAS에서 M1, M2, M3 머신 데이터 조회
              → Output: MachineCapability Submodels
              
         3.3) ActionAssembleSimulatorInputs
              → 수집된 데이터를 시뮬레이터 입력 형식으로 변환
              → Output: simulation_inputs.json
              
         3.4) ActionRunSimulator (EnhancedDockerRunHandler)
              ↓
              4.1) AAS 데이터 → AASX 형식 변환
                   • J1, J2, J3 → jobs.json
                   • M1, M2, M3 → machines.json
                   • Operations → operations.json
                   
              4.2) 데이터 저장 (/tmp/factory_automation/)
                   
              4.3) AASX 시뮬레이터 실행
                   • 스케줄링 알고리즘 적용
                   • 머신 부하 분산
                   • 완료 시간 계산
                   
              4.4) 결과 수집
                   Output: {
                     "predicted_completion_time": "2025-08-11T11:00:00Z",
                     "confidence": 0.95,
                     "machine_loads": {...}
                   }
                   
    [4] 최종 응답 반환
         ↓
         Client에게 JSON 응답 전송
    """
    
    print(flow)

def main():
    """메인 실행 함수"""
    
    # 실행 흐름 보여주기
    show_execution_flow()
    
    # 상세 테스트 실행
    result = run_detailed_test()
    
    # 시뮬레이션 데이터 확인
    if result:
        check_simulation_data()
    
    print("\n" + "=" * 80)
    print("✅ 상세 테스트 완료!")
    print("=" * 80)

if __name__ == "__main__":
    main()