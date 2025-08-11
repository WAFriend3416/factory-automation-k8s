# Smart Factory Alpha Prototype

> Industry 4.0 Smart Factory Automation System using AAS (Asset Administration Shell) Standards

## 🎯 Overview
AAS v2 데이터와 온톨로지를 기반으로 한 스마트 팩토리 자동화 시스템 프로토타입

This prototype demonstrates how semantic web technologies and AAS standards can be used to create an intelligent factory automation system with ontology-driven workflow execution.

## 📋 Quick Start

### 1. Setup
```bash
cd factory-automation-prototype
./setup.sh
```

### 2. Run Servers
**Terminal 1 - Mock AAS Server:**
```bash
source venv/bin/activate
python aas_mock_server/server.py
```

**Terminal 2 - FastAPI Server:**
```bash
source venv/bin/activate
uvicorn api.main:app --reload
```

### 3. Test Goal 1
```bash
./test_goal1.sh
```

## 📁 Project Structure
```
factory-automation-prototype/
├── aas_mock_server/
│   ├── data/
│   │   └── aas_model_v2.json
│   └── server.py
├── api/
│   ├── __init__.py
│   ├── main.py
│   └── schemas.py
├── execution_engine/
│   ├── __init__.py
│   ├── agent.py
│   └── planner.py
├── ontology/
│   └── factory_ontology_v2.ttl
├── config.py
├── requirements.txt
├── setup.sh
└── test_goal1.sh
```

## 🧪 Test Example
```bash
curl -X POST "http://127.0.0.1:8000/execute-goal" \
-H "Content-Type: application/json" \
-d '{
  "goal": "query_failed_jobs_with_cooling",
  "date": "2025-07-17"
}'
```

Expected Response:
```json
{
  "goal": "query_failed_jobs_with_cooling",
  "params": {...},
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

## ✅ Implemented Features

### Goal 1: Failed Job Query
- Query jobs that failed during cooling process
- Filter by date and process steps
- Status: **Fully Implemented** ✅

### Goal 4: Product Position Tracking  
- Real-time product location tracking
- Support for multiple products (Product-C, Product-D)
- Dynamic URN generation based on product ID
- Status: **Fully Implemented** ✅

## 🚀 Future Goals
- Goal 2: AI-based anomaly detection (70% ready)
- Goal 3: Production time prediction with simulator (40% ready)

## 🏗️ Architecture

- **Ontology Engine**: RDF/Turtle-based knowledge graph
- **Execution Planner**: SPARQL queries for workflow generation
- **Agent System**: Handler-based execution with context management
- **Mock AAS Server**: Flask-based AAS data provider
- **API Server**: FastAPI REST endpoints

## 📚 Technologies Used

- Python 3.8+
- FastAPI (Main API)
- Flask (Mock AAS Server)
- RDFlib (Ontology processing)
- Pydantic (Data validation)

## 👥 Contributors

- Development: Claude Code & Human Developer
- Architecture Design: Industry 4.0 Standards
- Testing: Automated test suite included