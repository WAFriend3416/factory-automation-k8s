#!/bin/bash

# 서버 시작 스크립트
echo "🚀 Starting Smart Factory Automation Servers..."

# Terminal 1: Mock AAS Server
echo "📦 Starting Mock AAS Server on port 5001..."
python aas_mock_server/server.py &
AAS_PID=$!
echo "   PID: $AAS_PID"

# 잠시 대기
sleep 2

# Terminal 2: FastAPI Server
echo "🌐 Starting FastAPI Server on port 8000..."
uvicorn api.main:app --reload &
API_PID=$!
echo "   PID: $API_PID"

echo ""
echo "✅ Both servers are running!"
echo ""
echo "📝 Server URLs:"
echo "   - Mock AAS Server: http://127.0.0.1:5001"
echo "   - FastAPI Server: http://127.0.0.1:8000"
echo "   - API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "🛑 To stop servers, run: kill $AAS_PID $API_PID"
echo "   Or press Ctrl+C"

# Wait for interrupt
wait