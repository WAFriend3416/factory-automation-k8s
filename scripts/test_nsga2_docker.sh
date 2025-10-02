#!/bin/bash
# NSGA-II Docker 컨테이너 빌드 및 테스트 스크립트
# Factory-automation-k8s Goal3 통합

set -e

echo "🐳 NSGA-II Docker Container Build & Test"
echo "========================================"
echo "📅 $(date)"
echo "📍 Working directory: $(pwd)"
echo ""

# 빌드 변수
IMAGE_NAME="factory-nsga2"
TAG="latest"
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

# Step 1: Docker 이미지 빌드
echo "🔨 Step 1: Building NSGA-II Docker Image"
echo "----------------------------------------"
echo "📦 Image: ${FULL_IMAGE_NAME}"
echo "📄 Dockerfile: Dockerfile.nsga2"

if [ ! -f "Dockerfile.nsga2" ]; then
    echo "❌ Error: Dockerfile.nsga2 not found"
    exit 1
fi

docker build -f Dockerfile.nsga2 -t ${FULL_IMAGE_NAME} .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Step 2: 테스트 시나리오 준비 확인
echo ""
echo "🔍 Step 2: Verifying Test Scenario"
echo "----------------------------------"
SCENARIO_NAME="my_case"
LOCAL_SCENARIO_PATH="./test_scenarios/${SCENARIO_NAME}"

if [ ! -d "$LOCAL_SCENARIO_PATH" ]; then
    echo "❌ Error: Test scenario directory not found: $LOCAL_SCENARIO_PATH"
    exit 1
fi

# 필수 파일 확인
REQUIRED_FILES=("jobs.json" "operations.json" "machines.json"
                "operation_durations.json" "machine_transfer_time.json" "job_release.json")

echo "📋 Checking required files:"
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$LOCAL_SCENARIO_PATH/$file" ]; then
        echo "  ❌ Missing: $file"
        exit 1
    else
        size=$(wc -c < "$LOCAL_SCENARIO_PATH/$file")
        echo "  ✅ $file (${size} bytes)"
    fi
done

# Step 3: 결과 디렉터리 준비
echo ""
echo "📁 Step 3: Preparing Result Directory"
echo "------------------------------------"
RESULT_DIR="./test_results"
mkdir -p "$RESULT_DIR"
echo "📤 Results will be saved to: $RESULT_DIR"

# Step 4: Docker 컨테이너 실행
echo ""
echo "🚀 Step 4: Running NSGA-II Simulation"
echo "------------------------------------"
echo "🐳 Container: ${FULL_IMAGE_NAME}"
echo "📁 Scenario: ${SCENARIO_NAME}"
echo "📊 Algorithm: branch_and_bound"
echo "⏱️  Time limit: 600s"

# 현재 시간 기록
START_TIME=$(date +%s)
echo "🕐 Start time: $(date)"

# Docker 실행
docker run --rm \
    -v "$(pwd)/test_scenarios:/app/scenarios" \
    -v "$(pwd)/${RESULT_DIR}:/app/results" \
    -e ALGORITHM=branch_and_bound \
    -e TIME_LIMIT=600 \
    -e MAX_NODES=50000 \
    ${FULL_IMAGE_NAME} ${SCENARIO_NAME}

DOCKER_EXIT_CODE=$?
END_TIME=$(date +%s)
EXECUTION_TIME=$((END_TIME - START_TIME))

echo ""
echo "⏱️  Total execution time: ${EXECUTION_TIME} seconds"

# Step 5: 결과 검증
echo ""
echo "🔍 Step 5: Verifying Results"
echo "---------------------------"

if [ $DOCKER_EXIT_CODE -eq 0 ]; then
    echo "✅ Docker container executed successfully"

    # 결과 파일 확인
    RESULT_FILE="${RESULT_DIR}/simulator_optimization_result.json"
    if [ -f "$RESULT_FILE" ]; then
        echo "📊 Result file generated successfully"

        # 파일 크기 확인
        result_size=$(wc -c < "$RESULT_FILE")
        echo "📄 Result file size: ${result_size} bytes"

        # 결과 파일 내용 미리보기
        echo "📈 Result preview:"
        echo "=================="
        if command -v jq >/dev/null; then
            jq . "$RESULT_FILE" | head -20
        else
            head -20 "$RESULT_FILE"
        fi

        # manifest 파일 확인
        MANIFEST_FILE="${RESULT_DIR}/goal3_manifest.json"
        if [ -f "$MANIFEST_FILE" ]; then
            echo ""
            echo "📋 Goal3 manifest generated:"
            if command -v jq >/dev/null; then
                jq . "$MANIFEST_FILE"
            else
                cat "$MANIFEST_FILE"
            fi
        fi

        echo ""
        echo "🎯 Goal3 Integration Status: READY"
        echo "✅ NSGA-II simulator container is working correctly"

    else
        echo "❌ Result file not generated: $RESULT_FILE"
        echo "📁 Available files in result directory:"
        ls -la "$RESULT_DIR/" || echo "Result directory is empty"
        exit 1
    fi
else
    echo "❌ Docker container failed with exit code: $DOCKER_EXIT_CODE"
    exit 1
fi

# Step 6: 정리 및 요약
echo ""
echo "🧹 Step 6: Summary and Cleanup"
echo "==============================="
echo "📊 Test Results Summary:"
echo "  🐳 Docker Image: ${FULL_IMAGE_NAME}"
echo "  📁 Scenario: ${SCENARIO_NAME}"
echo "  ⏱️  Execution Time: ${EXECUTION_TIME} seconds"
echo "  📤 Results: ${RESULT_DIR}/"
echo "  🎯 Goal3 Ready: YES"

# Docker 이미지 정보
echo ""
echo "🐳 Docker Image Info:"
docker images ${FULL_IMAGE_NAME}

echo ""
echo "✅ NSGA-II Docker Container Test Completed Successfully"
echo "🎯 Ready for Goal3 Integration and Kubernetes Deployment"
echo "========================================"