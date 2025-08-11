# Smart Factory Alpha Prototype - Usage Guide

## 🚀 Quick Start

### 1. Setup Virtual Environment
```bash
cd factory-automation-prototype
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start Servers

**Option A: Using the convenience script (Unix/Mac)**
```bash
./start_servers.sh
```

**Option B: Manual start (2 terminals)**

Terminal 1 - Mock AAS Server:
```bash
python aas_mock_server/server.py
```

Terminal 2 - FastAPI Server:
```bash
uvicorn api.main:app --reload
```

### 3. Test Goal 1
```bash
python test_goal1.py
```

Or using curl:
```bash
curl -X POST "http://127.0.0.1:8000/execute-goal" \
-H "Content-Type: application/json" \
-d '{
  "goal": "query_failed_jobs_with_cooling",
  "date": "2025-07-17"
}'
```

## 📊 Expected Result

```json
{
  "goal": "query_failed_jobs_with_cooling",
  "params": {
    "goal": "query_failed_jobs_with_cooling",
    "date": "2025-07-17"
  },
  "result": [
    {
      "job_id": "J-1002",
      "date": "2025-07-17",
      "status": "FAILED",
      "process_steps": ["cutting", "cooling", "assembly"],
      "failed_at": "cooling"
    }
  ]
}
```

## 🔍 API Documentation

Visit http://127.0.0.1:8000/docs for interactive API documentation.

## 📁 Project Structure

```
factory-automation-prototype/
├── aas_mock_server/       # Mock AAS Server (Flask)
│   ├── server.py
│   └── data/
│       └── aas_model_v2.json
├── api/                   # Main API Server (FastAPI)
│   ├── main.py
│   └── schemas.py
├── execution_engine/      # Core Logic
│   ├── planner.py        # Ontology-based planning
│   └── agent.py          # Action execution
├── ontology/             # Knowledge Base
│   └── factory_ontology_v2.ttl
├── config.py             # Configuration
├── requirements.txt      # Dependencies
└── test_goal1.py        # Test script
```

## 🛠️ Troubleshooting

1. **Port already in use**: Change ports in `config.py` and server files
2. **Module not found**: Ensure virtual environment is activated
3. **Connection refused**: Check that both servers are running
4. **No results**: Verify date parameter matches data in aas_model_v2.json

## 📈 Future Goals

- **Goal 2**: Anomaly detection with AI models
- **Goal 3**: Production time prediction with simulation
- **Goal 4**: Product location tracking