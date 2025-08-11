#!/bin/bash

# Test script for Goal 1: Query failed cooling jobs

echo "🧪 Testing Goal 1: Query failed cooling jobs"
echo "============================================"
echo ""
echo "📅 Testing with date: 2025-07-17"
echo ""

curl -X POST "http://127.0.0.1:8000/execute-goal" \
-H "Content-Type: application/json" \
-d '{
  "goal": "query_failed_jobs_with_cooling",
  "date": "2025-07-17"
}' | python3 -m json.tool

echo ""
echo "✅ Test complete!"
echo ""
echo "Expected result: Job J-1002 with FAILED status and cooling in process_steps"