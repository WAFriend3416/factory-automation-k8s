#!/bin/bash

echo "🚀 Starting Goal 4 Test Environment..."

# Activate virtual environment
source venv/bin/activate

# Kill any existing servers
echo "🔧 Cleaning up old processes..."
pkill -f "aas_mock_server" 2>/dev/null
pkill -f "uvicorn" 2>/dev/null
sleep 2

# Start Mock AAS Server
echo "📦 Starting Mock AAS Server (port 5001)..."
python aas_mock_server/server.py &
AAS_PID=$!
sleep 3

# Start FastAPI Server
echo "🌐 Starting FastAPI Server (port 8000)..."
uvicorn api.main:app --reload &
API_PID=$!
sleep 5

# Run test
echo "🧪 Running Goal 4 Test..."
echo "=" * 50
python test_goal4.py

# Store test result
TEST_RESULT=$?

# Kill servers
echo ""
echo "🛑 Stopping servers..."
kill $AAS_PID $API_PID 2>/dev/null

# Exit with test result
exit $TEST_RESULT