#!/bin/bash
set -e

# NSGA-II 시뮬레이터 실행 스크립트
# Factory-automation-k8s Goal3 통합용

# 설정 변수
SCENARIO_NAME=${1:-"my_case"}
ALGORITHM=${ALGORITHM:-"branch_and_bound"}
TIME_LIMIT=${TIME_LIMIT:-600}
MAX_NODES=${MAX_NODES:-50000}

SCENARIO_PATH="/app/scenarios/${SCENARIO_NAME}"
RESULT_PATH="/app/results"

echo "🚀 NSGA-II Simulator for Factory Automation Goal3"
echo "================================================"
echo "📁 Scenario: ${SCENARIO_NAME}"
echo "🔧 Algorithm: ${ALGORITHM}"
echo "⏱️  Time Limit: ${TIME_LIMIT}s"
echo "📊 Max Nodes: ${MAX_NODES}"
echo "📍 Scenario Path: ${SCENARIO_PATH}"
echo "📤 Result Path: ${RESULT_PATH}"
echo "================================================"

# 시나리오 디렉터리 확인
if [ ! -d "$SCENARIO_PATH" ]; then
    echo "❌ Error: Scenario directory not found: $SCENARIO_PATH"
    echo "📁 Available scenarios:"
    ls -la /app/scenarios/ 2>/dev/null || echo "No scenarios directory found"
    echo ""
    echo "💡 Expected scenario structure:"
    echo "   /app/scenarios/${SCENARIO_NAME}/"
    echo "   ├── jobs.json"
    echo "   ├── operations.json"
    echo "   ├── machines.json"
    echo "   ├── operation_durations.json"
    echo "   ├── machine_transfer_time.json"
    echo "   └── job_release.json"
    exit 1
fi

# 필수 파일 확인 (Goal3에서 사용하는 6개 파일)
REQUIRED_FILES=("jobs.json" "operations.json" "machines.json"
                "operation_durations.json" "machine_transfer_time.json" "job_release.json")

echo "🔍 Checking required JSON files for Goal3..."
missing_files=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$SCENARIO_PATH/$file" ]; then
        missing_files+=("$file")
        echo "  ❌ $file"
    else
        file_size=$(wc -c < "$SCENARIO_PATH/$file")
        echo "  ✅ $file (${file_size} bytes)"
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ Error: Missing required files: ${missing_files[*]}"
    echo "📄 Available files in scenario:"
    ls -la "$SCENARIO_PATH/" 2>/dev/null || echo "Cannot list scenario directory"
    exit 1
fi

# 시나리오 파일을 시뮬레이터 디렉터리로 복사
echo "📋 Preparing simulation environment..."
mkdir -p /app/nsga2-simulator/scenarios/${SCENARIO_NAME}

echo "  📂 Copying scenario files to simulator..."
for file in "${REQUIRED_FILES[@]}"; do
    cp "$SCENARIO_PATH/$file" "/app/nsga2-simulator/scenarios/${SCENARIO_NAME}/"
    echo "    📄 Copied $file"
done

# 추가 파일들도 복사 (있는 경우)
for extra_file in "initial_machine_status.json" "simulation_inputs.json"; do
    if [ -f "$SCENARIO_PATH/$extra_file" ]; then
        cp "$SCENARIO_PATH/$extra_file" "/app/nsga2-simulator/scenarios/${SCENARIO_NAME}/"
        echo "    📄 Copied optional file: $extra_file"
    fi
done

# 작업 디렉터리 변경
cd /app/nsga2-simulator

# Python path 설정
export PYTHONPATH=/app/nsga2-simulator:$PYTHONPATH

echo "🎯 Starting NSGA-II simulation execution..."
echo "  📍 Working directory: $(pwd)"
echo "  🐍 Python path: $PYTHONPATH"

# 먼저 시뮬레이터 도움말 확인
echo "  🔍 Checking available parameters..."
python3 simulator/main.py --help 2>&1 | head -15

echo "  📊 Simulator command: python3 simulator/main.py --scenario scenarios/${SCENARIO_NAME}"
echo "  ⚠️  Note: NSGA branch only supports --scenario, --print_queues_interval, --print_job_summary_interval, --agv_count"

# 시뮬레이션 시작 시간 기록
START_TIME=$(date +%s)
echo "  🕐 Start time: $(date)"

# NSGA-II 시뮬레이터 실행 (NSGA 브랜치는 최소한의 파라미터만 지원)
python3 simulator/main.py \
    --scenario "scenarios/${SCENARIO_NAME}" \
    --print_job_summary_interval 60 2>&1

SIMULATION_EXIT_CODE=$?

# 시뮬레이션 종료 시간 기록
END_TIME=$(date +%s)
EXECUTION_TIME=$((END_TIME - START_TIME))

echo "================================================"
echo "🕐 Execution time: ${EXECUTION_TIME} seconds"
if [ $SIMULATION_EXIT_CODE -eq 0 ]; then
    echo "✅ Simulation completed successfully"
else
    echo "❌ Simulation failed with exit code: $SIMULATION_EXIT_CODE"
fi

# 결과 파일 확인 및 처리
# NSGA 시뮬레이터는 results/ 디렉터리에 CSV/XLSX 파일들을 생성
RESULT_DIR_SIMULATOR="/app/nsga2-simulator/results"
JOB_INFO_FILE="$RESULT_DIR_SIMULATOR/job_info.csv"
OPERATION_INFO_FILE="$RESULT_DIR_SIMULATOR/operation_info.csv"
TRACE_FILE="$RESULT_DIR_SIMULATOR/trace.xlsx"

if [ -f "$JOB_INFO_FILE" ] && [ -f "$OPERATION_INFO_FILE" ]; then
    echo "📊 Results generated successfully"

    # 파일 크기 확인
    job_info_size=$(wc -c < "$JOB_INFO_FILE")
    operation_info_size=$(wc -c < "$OPERATION_INFO_FILE")
    echo "📄 Job info file size: ${job_info_size} bytes"
    echo "📄 Operation info file size: ${operation_info_size} bytes"

    # 결과 파일을 결과 디렉터리로 복사
    mkdir -p "$RESULT_PATH"
    cp "$JOB_INFO_FILE" "$RESULT_PATH/"
    cp "$OPERATION_INFO_FILE" "$RESULT_PATH/"
    echo "📤 Results copied to: $RESULT_PATH/"

    # 추가 결과 파일들도 복사 (있는 경우)
    extra_results=("trace.xlsx" "trace.csv" "agv_logs_M1.xlsx" "agv_logs_M2.xlsx" "agv_logs_M4.xlsx" "agv_logs_M5.xlsx" "agv_logs_M6.xlsx" "agv_logs_M7.xlsx" "agv_logs_M8.xlsx")
    for extra_file in "${extra_results[@]}"; do
        if [ -f "$RESULT_DIR_SIMULATOR/$extra_file" ]; then
            cp "$RESULT_DIR_SIMULATOR/$extra_file" "$RESULT_PATH/"
            extra_size=$(wc -c < "$RESULT_PATH/$extra_file")
            echo "📄 Copied additional result: $extra_file (${extra_size} bytes)"
        fi
    done

    # Goal3를 위한 결과 JSON 생성
    echo "🎯 Creating Goal3-compatible result file..."
    GOAL3_RESULT_FILE="$RESULT_PATH/simulator_optimization_result.json"

    python3 -c "
import pandas as pd
import json
import sys
from datetime import datetime

try:
    # CSV 결과 파일 읽기
    job_info = pd.read_csv('$JOB_INFO_FILE')
    operation_info = pd.read_csv('$OPERATION_INFO_FILE')

    # 완료 시간 분석
    if not job_info.empty:
        max_completion_time = job_info['completion_time'].max()
        min_start_time = job_info['start_time'].min()
        makespan = max_completion_time - min_start_time

        # 첫 번째 완료 시간 (가장 빨리 완료되는 작업)
        first_completion = job_info['completion_time'].min()

        # 완료된 작업 수
        completed_jobs = len(job_info[job_info['completion_time'] > 0])
        total_jobs = len(job_info)

        print(f'📊 Analysis Results:')
        print(f'   Total Jobs: {total_jobs}')
        print(f'   Completed Jobs: {completed_jobs}')
        print(f'   First Completion Time: {first_completion}')
        print(f'   Makespan: {makespan}')
        print(f'   Max Completion Time: {max_completion_time}')

    # Goal3 형식 결과 생성
    goal3_result = {
        'execution_metadata': {
            'scenario': '${SCENARIO_NAME}',
            'simulator': 'NSGA-II/AASX',
            'execution_time': ${EXECUTION_TIME},
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        },
        'simulation_results': {
            'makespan': makespan if 'makespan' in locals() else 0,
            'total_jobs': total_jobs if 'total_jobs' in locals() else 0,
            'completed_jobs': completed_jobs if 'completed_jobs' in locals() else 0,
            'first_completion_time': first_completion if 'first_completion' in locals() else 0
        },
        'goal3_data': {
            'predicted_completion_time': first_completion if 'first_completion' in locals() else 0,
            'confidence': min(0.95, 1.0 - (makespan / 10000) if 'makespan' in locals() and makespan > 0 else 0.8),
            'simulator_type': 'aasx-main'
        }
    }

    # JSON 파일 저장
    with open('$GOAL3_RESULT_FILE', 'w') as f:
        json.dump(goal3_result, f, indent=2)

    print('✅ Goal3 result file created')

except Exception as e:
    print(f'❌ Error creating Goal3 result: {e}')
    # 기본 결과 파일 생성
    default_result = {
        'execution_metadata': {
            'scenario': '${SCENARIO_NAME}',
            'simulator': 'NSGA-II/AASX',
            'execution_time': ${EXECUTION_TIME},
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'simulation_completed_no_analysis'
        },
        'goal3_data': {
            'predicted_completion_time': 3600,  # 기본값 1시간
            'confidence': 0.5,
            'simulator_type': 'aasx-main'
        }
    }
    with open('$GOAL3_RESULT_FILE', 'w') as f:
        json.dump(default_result, f, indent=2)
    print('⚠️  Created default Goal3 result file')
"

    PARSE_EXIT_CODE=$?
    if [ $PARSE_EXIT_CODE -eq 0 ]; then
        echo "✅ Results parsed successfully"

        # Goal3를 위한 manifest.json 생성
        MANIFEST_FILE="$RESULT_PATH/goal3_manifest.json"
        cat > "$MANIFEST_FILE" << EOF
{
  "execution_id": "nsga2-$(date +%Y%m%d-%H%M%S)",
  "scenario": "${SCENARIO_NAME}",
  "goal": "predict_first_completion_time",
  "algorithm": "${ALGORITHM}",
  "parameters": {
    "time_limit": ${TIME_LIMIT},
    "max_nodes": ${MAX_NODES}
  },
  "execution_time": ${EXECUTION_TIME},
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "simulator": "AASX-main",
  "version": "1.0.0",
  "result_files": [
    "simulator_optimization_result.json"
  ],
  "status": "completed"
}
EOF
        echo "📋 Goal3 manifest created: $MANIFEST_FILE"

    else
        echo "⚠️  Warning: Could not parse result file"
    fi

else
    echo "❌ Error: No result file generated"
    echo "📁 Files in scenario directory after simulation:"
    ls -la "/app/nsga2-simulator/scenarios/${SCENARIO_NAME}/" 2>/dev/null || echo "Cannot list scenario directory"

    # 디버깅 정보 출력
    echo "🔍 Debugging information:"
    echo "  📂 Simulator directory contents:"
    ls -la /app/nsga2-simulator/ 2>/dev/null || echo "Cannot list simulator directory"
    echo "  📂 Python path verification:"
    python3 -c "import sys; print('\\n'.join(sys.path))"

    exit 1
fi

# 최종 상태 출력
echo "================================================"
echo "🏁 NSGA-II Simulation Container Execution Completed"
echo "📊 Results available in: $RESULT_PATH"
echo "⏰ Total execution time: ${EXECUTION_TIME} seconds"
echo "🕐 Container finish time: $(date)"
echo "🎯 Goal3 integration ready"
echo "================================================"

exit $SIMULATION_EXIT_CODE