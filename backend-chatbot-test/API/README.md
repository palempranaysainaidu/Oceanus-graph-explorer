# Oceanographic Multi-Agent RAG API

Production-grade FastAPI application for oceanographic data analysis using a sophisticated multi-agent RAG system.

## 🌊 Features

- **Multi-Agent Architecture**: 6 specialized agents working in cycles
- **Production-Ready**: Comprehensive logging, monitoring, and error handling
- **Scalable**: Async processing with connection pooling
- **Secure**: Rate limiting, CORS, security headers
- **Observable**: Health checks, metrics, and detailed logging
- **Research-Grade**: Scientific analysis suitable for publications

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Health    │  │    Chat     │  │   Metrics   │         │
│  │  Endpoints  │  │  Endpoints  │  │  Endpoints  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Agent Manager                              │ │
│  │  • Connection pooling                                   │ │
│  │  • Health monitoring                                    │ │
│  │  • Async execution                                      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           Cyclic Multi-Agent RAG System                │ │
│  │  • 6 specialized agents                                │ │
│  │  • Quality-driven cycles                               │ │
│  │  • Multi-database integration                          │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit with your configuration
nano .env
```

### 2. Install Dependencies

```bash
# Install API dependencies
pip install -r api/requirements.txt

# Install core dependencies
pip install -r requirements.txt
```

### 3. Run the API

```bash
# Development mode
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Test the API

```bash
# Run test script
python api/test_api.py

# Or visit the docs
open http://localhost:8000/docs
```

## 📡 API Endpoints

### Chat Endpoints

- **POST** `/api/v1/chat` - Process oceanographic queries with session support
- **POST** `/api/v1/chat/stream` - Streaming responses for long queries
- **GET** `/api/v1/chat/examples` - Get example queries and tips

### Session Endpoints

- **POST** `/api/v1/sessions/create` - Create new conversation session
- **GET** `/api/v1/sessions/{session_id}` - Get session information
- **GET** `/api/v1/sessions/{session_id}/history` - Get conversation history
- **PUT** `/api/v1/sessions/{session_id}/preferences` - Update user preferences
- **GET** `/api/v1/sessions/{session_id}/context` - Get session context
- **DELETE** `/api/v1/sessions/{session_id}` - Delete session
- **GET** `/api/v1/sessions/` - Get session statistics

### Health Endpoints

- **GET** `/health` - Basic health check
- **GET** `/health/detailed` - Detailed system health
- **GET** `/health/ready` - Kubernetes readiness probe
- **GET** `/health/live` - Kubernetes liveness probe

### Metrics Endpoints

- **GET** `/metrics` - System metrics (JSON)
- **GET** `/metrics/prometheus` - Prometheus format metrics
- **POST** `/metrics/reset` - Reset performance metrics

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment (development/staging/production) | `development` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `WORKERS` | Number of workers | `4` |
| `MAX_CYCLES` | Agent max cycles | `3` |
| `QUALITY_THRESHOLD` | Quality threshold for refinement | `0.7` |
| `AGENT_TIMEOUT` | Query timeout (seconds) | `300` |
| `RATE_LIMIT_CALLS` | Rate limit calls per period | `100` |
| `RATE_LIMIT_PERIOD` | Rate limit period (seconds) | `60` |

### Database Configuration

```bash
# CockroachDB
COCKROACH_URL=postgresql://user:pass@host:26257/db?sslmode=require

# Neo4j
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Pinecone
PINECONE_API_KEY=your-api-key
PINECONE_ENV=your-environment
PINECONE_INDEX=your-index

# Groq LLM
GROQ_API_KEY=your-groq-api-key
```

## 📊 Example Usage

### Simple Query (Auto-creates session)

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me temperature measurements from float 7902073",
    "timeout": 60
  }'
```

### Session-based Conversation

```bash
# 1. Create session
curl -X POST "http://localhost:8000/api/v1/sessions/create" \
  -H "Content-Type: application/json" \
  -d '{
    "user_preferences": {
      "detail_level": "comprehensive",
      "preferred_regions": ["Arabian Sea"]
    }
  }'

# 2. First query
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me temperature data for float 7902073",
    "session_id": "your-session-id",
    "timeout": 60
  }'

# 3. Follow-up query (with context)
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Now compare this with Arabian Sea patterns",
    "session_id": "your-session-id",
    "timeout": 60
  }'
```

### Complex Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze float 7902073: show measurements, metadata, and find similar patterns in the Arabian Sea",
    "timeout": 300
  }'
```

### Streaming Response

```bash
curl -X POST "http://localhost:8000/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare temperature patterns between Arabian Sea and Bay of Bengal",
    "timeout": 300
  }'
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -f api/Dockerfile -t oceanographic-api .

# Run container
docker run -p 8000:8000 --env-file api/.env oceanographic-api
```

### Docker Compose

```bash
# Start all services
docker-compose -f api/docker-compose.yml up -d

# View logs
docker-compose -f api/docker-compose.yml logs -f api

# Stop services
docker-compose -f api/docker-compose.yml down
```

## 📈 Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Detailed health with agent status
curl http://localhost:8000/health/detailed

# Readiness (for K8s)
curl http://localhost:8000/health/ready
```

### Metrics

```bash
# JSON metrics
curl http://localhost:8000/metrics

# Prometheus format
curl http://localhost:8000/metrics/prometheus
```

### Logs

Logs are structured JSON format with:
- Request/response logging
- Performance metrics
- Error tracking
- Agent execution details

## 🔒 Security Features

- **Rate Limiting**: Configurable per-client limits
- **CORS**: Cross-origin request handling
- **Security Headers**: XSS, clickjacking protection
- **Input Validation**: Pydantic model validation
- **Error Handling**: Secure error responses
- **Request Logging**: Comprehensive audit trail

## 🧪 Testing

```bash
# Run API tests
python api/test_api.py

# Health check
curl http://localhost:8000/health

# Example query
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "System health check"}'
```

## 📚 API Documentation

When running in development mode:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🚀 Production Deployment

### Recommended Setup

1. **Reverse Proxy**: Nginx or Traefik
2. **Load Balancer**: Multiple API instances
3. **Database**: Managed database services
4. **Monitoring**: Prometheus + Grafana
5. **Logging**: ELK stack or similar
6. **Container**: Docker + Kubernetes

### Performance Tuning

- Adjust `WORKERS` based on CPU cores
- Configure database connection pools
- Set appropriate `AGENT_TIMEOUT` values
- Monitor memory usage for large queries
- Use Redis for caching (optional)

## 🤝 Integration

### Frontend Integration

```javascript
// Example frontend integration
const response = await fetch('/api/v1/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'Show me temperature data for float 7902073',
    timeout: 120
  })
});

const data = await response.json();
console.log(data.response);
```

### Webhook Integration

The API can be extended to support webhooks for long-running queries or batch processing.

## 📞 Support

For issues or questions:
1. Check the logs: `docker-compose logs -f api`
2. Verify health: `curl http://localhost:8000/health/detailed`
3. Test connectivity: `python api/test_api.py`
4. Review configuration: Check `.env` file

This production-grade API provides a robust, scalable interface to your sophisticated multi-agent RAG system! 🌊🔬