#!/bin/bash
# 서버 실행 스크립트

echo "🚀 Starting Factory Automation Servers..."

# Kill any existing servers
echo "Cleaning up existing processes..."
pkill -f "python aas_mock_server" 2>/dev/null
pkill -f "uvicorn api.main" 2>/dev/null
sleep 2

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Using local venv..."
    source venv/bin/activate
elif [ -d "../factory-automation-prototype/venv" ]; then
    echo "Using prototype venv..."
    source ../factory-automation-prototype/venv/bin/activate
else
    echo "⚠️ No virtual environment found. Using system Python."
fi

# Start Mock AAS Server
echo "Starting Mock AAS Server on port 5001..."
python aas_mock_server/server.py &
MOCK_PID=$!
echo "Mock AAS Server PID: $MOCK_PID"

# Wait for Mock server to start
sleep 2

# Start API Server
echo "Starting API Server on port 8000..."
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!
echo "API Server PID: $API_PID"

# Wait for API server to start
sleep 3

echo "✅ Both servers should be running now!"
echo ""
echo "To test, run: python test_goal4.py"
echo "To stop servers, run: pkill -f 'python aas_mock_server' && pkill -f 'uvicorn'"
echo ""
echo "Server PIDs:"
echo "  Mock AAS Server: $MOCK_PID"
echo "  API Server: $API_PID"

# Keep script running
wait