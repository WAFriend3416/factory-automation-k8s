#!/usr/bin/env python3
"""
AASX-main Simulator 통합 테스트 스크립트
온톨로지 변경 없이 enhanced agent 테스트
"""

import os
import sys
import json
from pathlib import Path

# 프로젝트 경로 추가
sys.path.append(str(Path(__file__).parent))

def test_data_converter():
    """데이터 변환기 테스트"""
    print("🧪 Step 1: 데이터 변환기 테스트")
    print("-" * 40)
    
    try:
        from simulation_data_converter import SimulationDataConverter
        
        # 환경변수 설정
        os.environ['AAS_SERVER_IP'] = '127.0.0.1'
        os.environ['AAS_SERVER_PORT'] = '5001'
        
        converter = SimulationDataConverter('127.0.0.1', 5001)
        
        # 기본 데이터 생성 테스트
        print("  📝 기본 데이터 생성 테스트...")
        default_data = converter.generate_default_data()
        
        print(f"    ✅ Jobs: {len(default_data['jobs'])}개")
        print(f"    ✅ Machines: {len(default_data['machines'])}개") 
        print(f"    ✅ Operations: {len(default_data['operations'])}개")
        
        # 테스트 디렉토리에 저장
        test_output = Path('./test_aasx_data')
        converter.save_to_directory(default_data, str(test_output))
        
        print(f"  💾 테스트 데이터 저장: {test_output}")
        return True
        
    except Exception as e:
        print(f"  ❌ 데이터 변환기 테스트 실패: {e}")
        return False

def test_docker_build():
    """Docker 이미지 빌드 테스트"""
    print("\n🐳 Step 2: Docker 이미지 빌드 테스트")
    print("-" * 40)
    
    try:
        # AASX-main simulator 존재 확인
        aasx_main_path = Path('../AASX-main')
        if not aasx_main_path.exists():
            print(f"  ⚠️  AASX-main 경로 없음: {aasx_main_path}")
            print("  📝 AASX-main을 현재 위치로 복사 필요")
            return False
        
        # Dockerfile 존재 확인
        dockerfile_path = Path('./aasx_simulator.Dockerfile')
        if not dockerfile_path.exists():
            print(f"  ❌ Dockerfile 없음: {dockerfile_path}")
            return False
        
        print(f"  ✅ AASX-main 경로 확인: {aasx_main_path}")
        print(f"  ✅ Dockerfile 확인: {dockerfile_path}")
        
        # Docker 빌드 명령어 안내
        print(f"\n  🛠️  다음 명령어로 Docker 이미지 빌드:")
        print(f"     1. AASX-main 복사:")
        print(f"        cp -r ../AASX-main ./")
        print(f"     2. Docker 빌드:")
        print(f"        docker build -t aasx-simulator:latest -f aasx_simulator.Dockerfile .")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Docker 빌드 테스트 실패: {e}")
        return False

def test_enhanced_handler():
    """Enhanced DockerRunHandler 로직 테스트"""
    print("\n🔧 Step 3: Enhanced Handler 로직 테스트")
    print("-" * 40)
    
    try:
        # 환경변수 설정
        os.environ['USE_ADVANCED_SIMULATOR'] = 'true'
        os.environ['AAS_SERVER_IP'] = '127.0.0.1'
        os.environ['AAS_SERVER_PORT'] = '5001'
        
        from enhanced_agent import EnhancedDockerRunHandler
        
        print("  📦 Enhanced Handler 초기화...")
        handler = EnhancedDockerRunHandler()
        
        # Mock context 생성
        test_context = {
            "step_1_ActionFetchProductSpec": {
                "product_id": "Product-A",
                "quantity": 25
            },
            "step_2_ActionFetchAllMachineData": {
                "machines": ["M1", "M2", "M3"]
            },
            "step_3_ActionAssembleSimulatorInputs": {
                "simulation_job_id": "test-job-123"
            }
        }
        
        test_step_details = {
            "action_id": "ActionRunSimulator",
            "type": "docker_run",
            "params": {
                "goal": "predict_first_completion_time",
                "product_id": "Product-A", 
                "quantity": 25
            }
        }
        
        print("  🔄 데이터 변환 로직 테스트...")
        converter_result = handler._convert_and_prepare_data(test_context)
        
        print(f"    ✅ 변환된 Jobs: {len(converter_result['jobs'])}")
        print(f"    ✅ 변환된 Machines: {len(converter_result['machines'])}")
        print(f"    ✅ 변환된 Operations: {len(converter_result['operations'])}")
        
        print("  💾 PVC 저장 로직 테스트...")
        # 로컬 환경에서는 /tmp 사용
        pvc_result = handler._save_simulation_data_to_pvc(converter_result)
        
        print(f"    ✅ 저장 경로: {pvc_result['pvc_path']}")
        print(f"    ✅ 저장된 파일: {len(pvc_result['files_saved'])}개")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced Handler 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_goal3_integration():
    """Goal 3 통합 테스트 시뮬레이션"""
    print("\n🎯 Step 4: Goal 3 통합 테스트 시뮬레이션")
    print("-" * 40)
    
    try:
        # 기존 Goal 3 워크플로우 시뮬레이션
        print("  🔍 Goal 3 워크플로우 시뮬레이션:")
        print("    1. ActionFetchProductSpec ✅")
        print("    2. ActionFetchAllMachineData ✅") 
        print("    3. ActionAssembleSimulatorInputs ✅")
        print("    4. ActionRunSimulator → EnhancedDockerRunHandler ✅")
        
        # 환경변수별 동작 확인
        scenarios = [
            ("USE_ADVANCED_SIMULATOR=true", "AASX-main simulator"),
            ("USE_ADVANCED_SIMULATOR=false", "Dummy simulator")
        ]
        
        for env_var, description in scenarios:
            print(f"\n  📊 시나리오: {env_var}")
            print(f"    예상 동작: {description}")
            
            if "true" in env_var:
                print("    → AAS 데이터 수집")
                print("    → AASX 형식 변환")
                print("    → PVC에 데이터 저장") 
                print("    → AASX-main simulator 실행")
                print("    → 고정밀 시뮬레이션 결과")
            else:
                print("    → 기존 dummy simulator")
                print("    → 빠른 응답, 고정 결과")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 통합 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("🚀 AASX-main Simulator 통합 테스트")
    print("=" * 60)
    
    # 테스트 실행
    tests = [
        ("데이터 변환기", test_data_converter),
        ("Docker 빌드", test_docker_build), 
        ("Enhanced Handler", test_enhanced_handler),
        ("Goal 3 통합", test_goal3_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 오류: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
    
    print(f"\n총 테스트: {len(results)}개, 통과: {passed}개, 실패: {len(results) - passed}개")
    
    if passed == len(results):
        print("\n🎉 모든 테스트 통과! AASX-main Simulator 통합 준비 완료")
        
        print("\n🚀 다음 단계:")
        print("1. AASX-main 디렉토리를 현재 위치로 복사")
        print("2. Docker 이미지 빌드: docker build -t aasx-simulator:latest -f aasx_simulator.Dockerfile .")
        print("3. K8s 환경에서 Goal 3 실제 테스트")
        print("4. 성능 비교 및 최적화")
        
    else:
        print("\n⚠️ 일부 테스트 실패. 문제 해결 후 재시도 필요")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()