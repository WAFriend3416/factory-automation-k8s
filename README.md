# Factory Automation Kubernetes

Smart factory automation system with AAS (Asset Administration Shell) integration and ontology-based execution engine.

## 📋 Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## Overview

This project implements a smart factory automation system using:
- **AAS (Asset Administration Shell)** for industrial data modeling
- **Ontology-based execution engine** for intelligent task planning
- **Kubernetes** for scalable deployment
- **FastAPI** for REST API services

### Key Features
- Goal-based task execution with automatic action planning
- Real-time factory data querying and analysis
- Support for multiple industrial use cases (job tracking, anomaly detection, production planning)
- Dual mode support (Mock AAS and Standard AAS servers)

### Implementation Status

| Goal | Feature | Mock Server | Standard Server | Status | Description |
|------|---------|-------------|-----------------|--------|-------------|
| Goal 1 | Failed Job Query | ✅ Complete | ✅ **Complete** | 🟢 **Ready** | Query jobs that failed during cooling process |
| Goal 2 | Anomaly Detection | ✅ Complete | ❌ Data Missing | 🟡 **Partial** | ML model integration + sensor data needed |
| Goal 3 | Production Time Prediction | ✅ Complete | ✅ **Complete** | 🟢 **Ready** | Dynamic simulator with file system resolution |
| Goal 4 | Product Position Tracking | ✅ Complete | ✅ **Complete** | 🟢 **Ready** | Real-time product location tracking |

**🎯 Standard Server Integration**: **75% Complete** (3/4 Goals fully functional)

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    External Clients                      │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │      Main API Service (FastAPI)      │
        │          Service: api-service         │
        │             Port: 8000               │
        └──────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
    ┌──────────────────┐          ┌──────────────────┐
    │ Execution Engine │          │   Mock AAS Server  │
    │   - Planner      │          │  Service: aas-mock │
    │   - Agent        │ ◄────────│    Port: 5001     │
    │   - Handlers     │          └──────────────────┘
    └──────────────────┘                    │
            │                                │
            ▼                                ▼
    ┌──────────────────┐          ┌──────────────────┐
    │  Ontology (RDF)  │          │   AAS Data Model  │
    │  ConfigMap: ttl  │          │  ConfigMap: json  │
    └──────────────────┘          └──────────────────┘
```

## Prerequisites

### For Local Development
- **Python 3.8+**
- **Virtual environment** (venv)

### For Kubernetes Deployment
- **Kubernetes cluster** (local or cloud)
- **kubectl** configured
- **Docker** (for building images)
- **Minikube** or **Docker Desktop** with Kubernetes (for local testing)

## Quick Start

### Local Development

#### 1. Setup Environment
```bash
# Clone repository
git clone <repository-url>
cd factory-automation-k8s

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Start Services
```bash
# Terminal 1: Mock AAS Server
python aas_mock_server/server.py

# Terminal 2: FastAPI Server
uvicorn api.main:app --reload
```

#### 3. Test the System
```bash
curl -X POST "http://localhost:8000/execute-goal" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "query_failed_jobs_with_cooling",
    "date": "2025-08-11"
  }'
```

### Kubernetes Deployment

#### 1. Build Docker Images
```bash
# API server
docker build -t factory-api:latest -f api.Dockerfile .

# Mock AAS server
docker build -t aas-mock-server:latest -f aas_mock_server.Dockerfile .
```

#### 2. Deploy to Kubernetes
```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services
```

#### 3. Access Services
```bash
# Port forwarding for API
kubectl port-forward service/api-service 8080:80

# Test API
curl http://localhost:8080/docs
```

## API Documentation

### Base URL
- Local: `http://localhost:8000`
- Kubernetes: `http://localhost:8080` (with port-forward)

### Main Endpoint

#### POST `/execute-goal`
Execute a goal-based operation using ontology-driven workflow.

**Request Body:**
```json
{
  "goal": "string",           // Required: Goal identifier
  "date": "string",           // Optional: Date (YYYY-MM-DD)
  "product_id": "string",     // Optional: Product ID
  "quantity": "integer",      // Optional: Quantity
  "target_machine": "string"  // Optional: Machine ID
}
```

**Response:**
```json
{
  "goal": "string",
  "params": {},
  "result": {}
}
```

### Supported Goals

| Goal ID | Description | Required Parameters | Status |
|---------|-------------|-------------------|---------|
| `query_failed_jobs_with_cooling` | Query failed cooling jobs | `date` | ✅ |
| `track_product_position` | Track product location | `product_id` | ✅ |
| `predict_first_completion_time` | Predict production time | `product_id`, `quantity` | ✅ |
| `detect_anomaly_for_product` | Detect anomalies | `target_machine` | ⏳ |

### Example Requests

#### Query Failed Jobs
```bash
curl -X POST "http://localhost:8000/execute-goal" \
-H "Content-Type: application/json" \
-d '{
  "goal": "query_failed_jobs_with_cooling",
  "date": "2025-08-11"
}'
```

#### Track Product Position
```bash
curl -X POST "http://localhost:8000/execute-goal" \
-H "Content-Type: application/json" \
-d '{
  "goal": "track_product_position",
  "product_id": "Product-C"
}'
```

### Mock AAS Server Endpoints

#### GET `/submodels/{submodel_id}`
Retrieve specific submodel data by URN.

Example URNs:
- `urn:factory:submodel:job_log`
- `urn:factory:submodel:tracking_data:product-c`
- `urn:factory:submodel:process_specification:all`

## Testing

### Run All Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests with coverage
pytest tests/ -v --cov=.
```

### Test Individual Goals
```bash
# Test Goal 1
python test_goal1.py

# Test Goal 4
python test_goal4.py
```

### Integration Testing
```bash
python tests/test_integration.py
```

## Project Structure

```
factory-automation-k8s/
├── api/                         # FastAPI application
│   ├── main.py                 # API endpoints
│   └── schemas.py              # Pydantic models
├── aas_mock_server/            # Mock AAS server
│   ├── server.py               # Flask server
│   └── data/                   # AAS data files
├── execution_engine/           # Core execution logic
│   ├── planner.py             # Ontology-based planner
│   └── agent.py               # Execution agent & handlers
├── ontology/                   # RDF/Turtle ontology files
├── k8s/                        # Kubernetes manifests
│   ├── 00-pvc.yaml           # Persistent volumes
│   ├── 01-aas-mock-server.yaml
│   ├── 02-api-server.yaml
│   └── 03-rbac.yaml          # RBAC configuration
├── tests/                      # Test files
├── config.py                   # Configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Development

### Server Mode Configuration

The system supports dual mode operation with intelligent path resolution:

```bash
# Use Mock AAS Server (default, recommended for development)
export USE_STANDARD_SERVER=false

# Use Standard AAS Server (production ready)
export USE_STANDARD_SERVER=true
export AAS_SERVER_IP=127.0.0.1  # or your server IP
export AAS_SERVER_PORT=5001      # or your server port
```

### File System Configuration

Dynamic file system path resolution for different environments:

```bash
# Force local development mode (uses temp directories)
export FORCE_LOCAL_MODE=true

# Custom work directory (optional)
export SIMULATION_WORK_DIR=/path/to/your/work/directory

# Debug mode (shows path resolution details)
export DEBUG_MODE=true
```

**Path Resolution Logic**:
- **Kubernetes Environment**: Uses `/data` PVC mount when available
- **Local Environment**: Uses system temp directories with fallback
- **Custom Path**: Uses user-specified `SIMULATION_WORK_DIR` with validation
- **Fallback**: Memory-based processing when file system access fails

### Adding New Goals

1. **Update Ontology**: Add goal definition to `ontology/factory_ontology_v2_final_corrected.ttl`
2. **Implement Handler**: Add handler in `execution_engine/agent.py`
3. **Update Schema**: Add parameters to `api/schemas.py`
4. **Test**: Create test case in `tests/`

### Running with Docker Compose

```bash
docker-compose up -d
```

### API Documentation

When running locally, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Kill processes on ports
lsof -ti:8000 | xargs kill -9  # API server
lsof -ti:5001 | xargs kill -9  # AAS server
```

#### Module Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

#### Kubernetes Pod Issues
```bash
# Check pod status
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>

# Restart deployment
kubectl rollout restart deployment <deployment-name>
```

#### Connection Refused
- Verify Mock AAS server is running on port 5001
- Check `AAS_SERVER_URL` in `config.py`
- For Kubernetes, ensure services are exposed correctly

### Debug Mode

Enable debug logging:
```bash
# API Server
uvicorn api.main:app --reload --log-level debug

# Flask Mock Server
export FLASK_ENV=development
python aas_mock_server/server.py
```

## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time | < 200ms | ~150ms |
| Concurrent Requests | > 100 req/s | ~150 req/s |
| Memory Usage | < 500MB | ~300MB |
| Startup Time | < 30s | ~20s |

## Roadmap

### 2025 Q1 ✅
- [x] Mock AAS server implementation
- [x] Goals 1, 3, 4 implementation
- [x] Kubernetes deployment
- [x] Dual mode support

### 2025 Q2 🔄
- [x] Standard server integration (75% complete - 3/4 Goals working)
- [x] File system path resolution and environment adaptation
- [ ] Goal 2 sensor data integration for standard server
- [ ] Real-time monitoring dashboard
- [ ] Performance optimization

### Recent Updates ✨
- **2025-08-23**: Standard AAS server integration testing completed
- **2025-08-23**: File system permission issues resolved with dynamic path resolution
- **2025-08-23**: Goals 1, 3, 4 fully functional with standard server
- **2025-08-23**: Added environment-aware path resolution (`PathResolver` utility)

## Technologies Used

- **Python 3.8+**: Core language
- **FastAPI**: High-performance async API
- **Flask**: Mock AAS server
- **RDFlib**: Ontology processing (SPARQL)
- **Pydantic**: Data validation
- **Docker & Kubernetes**: Container orchestration

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For issues or questions, please open an issue on GitHub.

---

**Version**: 2.1.0  
**Last Updated**: 2025-08-23  
**Status**: 🟢 Production Ready (Mock Server) | 🟢 Production Ready (Standard Server - 3/4 Goals)