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
echo "  📊 Simulator command: python3 simulator/main.py --scenario scenarios/${SCENARIO_NAME} --algorithm ${ALGORITHM} --time_limit ${TIME_LIMIT} --max_nodes ${MAX_NODES}"

# 시뮬레이션 시작 시간 기록
START_TIME=$(date +%s)
echo "  🕐 Start time: $(date)"

# NSGA-II 시뮬레이터 실행
python3 simulator/main.py \
    --scenario "scenarios/${SCENARIO_NAME}" \
    --algorithm "${ALGORITHM}" \
    --time_limit "${TIME_LIMIT}" \
    --max_nodes "${MAX_NODES}" 2>&1

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
RESULT_FILE="/app/nsga2-simulator/scenarios/${SCENARIO_NAME}/simulator_optimization_result.json"
if [ -f "$RESULT_FILE" ]; then
    echo "📊 Results generated successfully"

    # 파일 크기 확인
    result_size=$(wc -c < "$RESULT_FILE")
    echo "📄 Result file size: ${result_size} bytes"

    # 결과 파일을 결과 디렉터리로 복사
    mkdir -p "$RESULT_PATH"
    cp "$RESULT_FILE" "$RESULT_PATH/"
    echo "📤 Result copied to: $RESULT_PATH/simulator_optimization_result.json"

    # 추가 결과 파일들도 복사 (있는 경우)
    extra_results=("trace.xlsx" "job_info.csv" "operation_info.csv" "timeline.png")
    for extra_file in "${extra_results[@]}"; do
        if [ -f "/app/nsga2-simulator/scenarios/${SCENARIO_NAME}/$extra_file" ]; then
            cp "/app/nsga2-simulator/scenarios/${SCENARIO_NAME}/$extra_file" "$RESULT_PATH/"
            extra_size=$(wc -c < "$RESULT_PATH/$extra_file")
            echo "📄 Copied additional result: $extra_file (${extra_size} bytes)"
        fi
    done

    # 결과 요약 파싱 및 출력
    echo "📈 Simulation Results Summary:"
    echo "================================================"
    python3 -c "
import json
import sys
try:
    with open('$RESULT_FILE', 'r') as f:
        result = json.load(f)

    print(f'🔧 Algorithm: {result.get(\"algorithm\", \"N/A\")}')
    print(f'🎯 Best Objective: {result.get(\"best_objective\", \"N/A\")}')
    print(f'⏱️  Search Time: {result.get(\"search_time\", \"N/A\")}s')
    print(f'🔍 Nodes Explored: {result.get(\"nodes_explored\", \"N/A\")}')

    schedule = result.get('best_schedule', [])
    print(f'📋 Schedule Length: {len(schedule)} actions')

    # Goal3를 위한 예상 완료 시간 계산
    if schedule:
        print(f'📅 First Action: {schedule[0] if schedule else \"N/A\"}')
        if len(schedule) > 1:
            print(f'📅 Last Action: {schedule[-1]}')

    # 추가 Goal3 관련 정보
    makespan = result.get('makespan', result.get('best_objective', 0))
    print(f'⏰ Makespan: {makespan}')

    # Goal3 응답 형식에 맞춘 정보
    print('\\n🎯 Goal3 Integration Info:')
    print(f'   predicted_completion_time: Available from schedule analysis')
    print(f'   confidence: Can be calculated from objective quality')
    print(f'   simulator_type: aasx-main')

except Exception as e:
    print(f'❌ Error parsing results: {e}')
    print('📄 Raw result file content (first 500 chars):')
    try:
        with open('$RESULT_FILE', 'r') as f:
            content = f.read(500)
            print(content)
    except:
        print('Cannot read result file')
    sys.exit(1)
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