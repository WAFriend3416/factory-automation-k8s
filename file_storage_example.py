#!/usr/bin/env python3
"""
파일 저장 및 활용 예시
여러 파일을 저장하고 Goal 실행에서 입력으로 사용하는 방법을 보여줌
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from path_resolver import get_simulation_work_dir
from execution_engine.planner import ExecutionPlanner
from execution_engine.agent_refactored import ExecutionAgent

def setup_data_files():
    """다양한 데이터 파일들을 저장 공간에 준비"""
    
    work_dir = get_simulation_work_dir()
    data_dir = work_dir / "factory_data"
    data_dir.mkdir(exist_ok=True)
    
    print(f"📁 Setting up data files in: {data_dir}")
    
    # 1. 제품 사양 데이터
    product_specs = {
        "Product-A": {
            "processes": ["cutting", "drilling", "assembly"],
            "estimated_time_per_unit": 45,
            "quality_requirements": {"precision": 0.1, "surface_finish": "smooth"}
        },
        "Product-B": {
            "processes": ["molding", "curing", "painting"],
            "estimated_time_per_unit": 60,
            "quality_requirements": {"color_match": "exact", "durability": "high"}
        }
    }
    
    # 2. 기계 성능 데이터
    machine_performance = {
        "CNC-001": {
            "max_speed": 1000,
            "current_efficiency": 0.85,
            "maintenance_status": "good",
            "queue_length": 3
        },
        "CNC-002": {
            "max_speed": 800,
            "current_efficiency": 0.92,
            "maintenance_status": "excellent", 
            "queue_length": 1
        }
    }
    
    # 3. 작업 히스토리 데이터
    job_history = {
        "recent_jobs": [
            {"product": "Product-A", "quantity": 50, "actual_time": 2250, "date": "2025-08-20"},
            {"product": "Product-A", "quantity": 30, "actual_time": 1380, "date": "2025-08-21"},
            {"product": "Product-B", "quantity": 20, "actual_time": 1200, "date": "2025-08-22"}
        ],
        "average_performance": {
            "Product-A": {"avg_time_per_unit": 46, "success_rate": 0.95},
            "Product-B": {"avg_time_per_unit": 58, "success_rate": 0.88}
        }
    }
    
    # 4. 설정 파일
    factory_config = {
        "operation_hours": {"start": "08:00", "end": "18:00"},
        "break_times": ["12:00-13:00", "15:00-15:15"],
        "overtime_multiplier": 1.5,
        "max_queue_length": 10
    }
    
    # 파일들 저장
    files_to_save = {
        "product_specs.json": product_specs,
        "machine_performance.json": machine_performance, 
        "job_history.json": job_history,
        "factory_config.json": factory_config
    }
    
    saved_files = {}
    for filename, content in files_to_save.items():
        file_path = data_dir / filename
        with open(file_path, 'w') as f:
            json.dump(content, f, indent=2)
        saved_files[filename] = str(file_path)
        print(f"✅ Saved: {filename} ({file_path.stat().st_size} bytes)")
    
    return saved_files, data_dir

def demonstrate_file_usage():
    """저장된 파일들을 Goal 실행에서 활용하는 예시"""
    
    print("\n🎯 Demonstrating File Usage in Goal Execution")
    print("=" * 60)
    
    # 데이터 파일들 준비
    saved_files, data_dir = setup_data_files()
    
    # Goal 실행 준비
    planner = ExecutionPlanner()
    agent = ExecutionAgent()
    
    # 저장된 파일들 읽어서 Goal에 추가 정보 제공
    additional_data = {}
    for filename, file_path in saved_files.items():
        with open(file_path, 'r') as f:
            additional_data[filename.replace('.json', '')] = json.load(f)
    
    print(f"\n📊 Loaded data from {len(additional_data)} files:")
    for key, data in additional_data.items():
        print(f"  - {key}: {len(str(data))} characters")
    
    # Goal 3 실행 (생산 시간 예측) - 저장된 데이터 활용
    goal = 'predict_first_completion_time'
    params = {
        'goal': goal,
        'product_id': 'Product-A',
        'quantity': 25,
        'additional_data': additional_data  # 저장된 파일 데이터 추가
    }
    
    print(f"\n🚀 Executing Goal 3 with stored file data...")
    print(f"📋 Parameters: product={params['product_id']}, quantity={params['quantity']}")
    print(f"📁 Using data from: {data_dir}")
    
    try:
        action_plan = planner.create_plan(goal)
        if action_plan:
            result = agent.run(action_plan, params)
            
            if 'final_result' in result:
                print(f"\n✅ Success! Result: {result['final_result']}")
            else:
                print(f"\n📊 Execution completed: {result}")
                
            # 생성된 시뮬레이션 파일 확인
            current_dir = data_dir.parent / "current"
            if current_dir.exists():
                for sim_file in current_dir.glob("*.json"):
                    print(f"📄 Generated simulation file: {sim_file}")
                    
        else:
            print("❌ No action plan generated")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return data_dir

if __name__ == "__main__":
    print("📁 File Storage and Usage Demonstration")
    print("=" * 50)
    
    data_dir = demonstrate_file_usage()
    
    print(f"\n💡 Summary:")
    print(f"✅ Files are stored in: {data_dir}")
    print(f"✅ Files persist across Goal executions")
    print(f"✅ Can be used as input for multiple Goals")
    print(f"✅ Works in both local and Kubernetes environments")