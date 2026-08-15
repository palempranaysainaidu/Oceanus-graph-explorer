# Oceanus Insights - Multi-Agent Oceanographic Data Analysis System

A sophisticated AI-powered platform for analyzing Argo float oceanographic data using multi-agent RAG (Retrieval-Augmented Generation) architecture with cyclic refinement capabilities.

## 🌊 Overview

Oceanus Insights is a comprehensive system that combines advanced AI agents with oceanographic databases to provide research-grade analysis of marine data. The system features a modern web interface with interactive visualizations and an intelligent chatbot powered by specialized AI agents.

**CognoDB graph extension:** See [COGNODB.md](./COGNODB.md) for the knowledge-graph schema, seed script, Cypher queries, agent integration, and UI explorer added for graph-database-backed retrieval over 88 Argo floats.

### Key Features

- **Multi-Agent RAG System**: Specialized AI agents for measurements, metadata, and semantic analysis
- **Cyclic Refinement**: Iterative quality improvement with up to 3 analysis cycles
- **Interactive Map Visualization**: Real-time oceanographic data visualization
- **Conversational AI Interface**: Natural language queries with context-aware responses
- **Multi-Database Integration**: CockroachDB, CognoDB (Neo4j-compatible graph), and Pinecone vector database
- **Session Management**: Persistent conversation history and context
- **Real-time Status Monitoring**: Backend health monitoring and error recovery

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  Agent System   │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (Multi-Agent)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Map Visualiz.  │    │ Session Manager │    │   Tool Factory  │
│   (Leaflet)     │    │   (In-Memory)   │    │   (DB Tools)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                        ┌──────────────────────────────┼──────────────────────────────┐
                        │                              │                              │
                        ▼                              ▼                              ▼
                ┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
                │  CockroachDB    │          │    CognoDB      │          │    Pinecone     │
                │ (Time-series)   │          │  (Graph/RAG)    │          │   (Vectors)     │
                └─────────────────┘          └─────────────────┘          └─────────────────┘
```

### Multi-Agent System

1. **Main Agent**: Entry point, handles conversation and routing
2. **Measurement Agent**: Analyzes time-series oceanographic data
3. **Metadata Agent**: Retrieves float and deployment information
4. **Semantic Agent**: Performs pattern matching and similarity search
5. **Analysis Agent**: Evaluates result quality and suggests improvements
6. **Refinement Agent**: Adjusts parameters for better results
7. **Coordinator Agent**: Synthesizes findings into research-grade responses

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm/yarn
- **Python** 3.9+
- **CockroachDB** (for oceanographic measurements)
- **Neo4j** (for metadata and relationships)
- **Pinecone** (for vector embeddings)
- **Groq API Key** (for LLM inference)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd oceanus-insights
   ```

2. **Backend Setup**
   ```bash
   cd backend-chatbot-test
   
   # Create virtual environment
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your database credentials and API keys
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   
   # Install dependencies
   npm install
   
   # Configure environment
   cp .env.example .env.local
   # Edit .env.local with backend URL
   ```

4. **Database Setup**
   - Set up CockroachDB with oceanographic data schema
   - Configure Neo4j with float metadata
   - Initialize Pinecone index for vector embeddings
   - Run data population scripts in `Data_populating/`

### Running the Application

1. **Start the Backend**
   ```bash
   cd backend-chatbot-test/API
   python main.py
   ```
   Backend will be available at `http://localhost:8000`

2. **Start the Frontend**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will be available at `http://localhost:3000`

## 📁 Project Structure

```
oceanus-insights/
├── frontend/                          # Next.js frontend application
│   ├── app/                          # App router pages
│   ├── components/                   # React components
│   │   ├── chatbot.tsx              # Main chatbot interface
│   │   ├── map-visualization.tsx    # Interactive map
│   │   └── ui/                      # UI components
│   ├── hooks/                       # Custom React hooks
│   │   ├── use-session-manager.ts   # Session management
│   │   └── use-backend-status.ts    # Backend monitoring
│   └── lib/                         # Utilities and API client
│       └── backend-api.ts           # Backend API service
│
├── backend-chatbot-test/             # Backend services
│   ├── API/                         # FastAPI application
│   │   ├── main.py                  # Application entry point
│   │   ├── routers/                 # API route handlers
│   │   │   ├── chat.py             # Chat endpoints
│   │   │   ├── sessions.py         # Session management
│   │   │   └── health.py           # Health monitoring
│   │   └── core/                    # Core services
│   │       ├── agent_manager.py    # Agent system manager
│   │       ├── session_manager.py  # Session persistence
│   │       └── config.py           # Configuration
│   │
│   ├── agent/                       # Multi-agent system
│   │   ├── main_agent.py           # Main routing agent
│   │   ├── cyclic_multi_agent.py   # Cyclic refinement system
│   │   └── multi_agent_rag.py      # Specialized agents
│   │
│   └── tools/                       # Database tools
│       ├── cockroach_tool.py       # CockroachDB interface
│       ├── neo4j_tool.py           # Neo4j interface
│       └── pinecone_tool.py        # Pinecone interface
│
└── Data_populating/                 # Data ingestion scripts
    ├── cockroach_populate.py       # Load measurement data
    ├── neo4j_populate.py           # Load metadata
    └── pinecone_populate.py        # Create embeddings
```

## 🔧 Configuration

### Environment Variables

**Backend (.env)**
```env
# Database Configuration
DATABASE_URL=postgresql://user:pass@host:port/db
NEO4J_USER=neo4j
NEO4J_PASS=password
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENV=your-environment
PINECONE_INDEX=argo-embeddings

# LLM Configuration
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama3-70b-8192

# Agent Configuration
MAX_CYCLES=3
QUALITY_THRESHOLD=0.7
AGENT_TIMEOUT=120

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
```

**Frontend (.env.local)**
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## 🤖 Agent System

### Query Processing Flow

1. **Query Reception**: Main agent receives user query
2. **Intent Classification**: Determines if routing to specialists is needed
3. **Agent Execution**: Relevant agents process the query
4. **Quality Analysis**: Results are evaluated for completeness
5. **Refinement Cycle**: If quality is low, parameters are adjusted
6. **Response Synthesis**: Final response is generated and returned

### Supported Query Types

- **Measurement Queries**: "Show temperature data for float 1901442"
- **Metadata Queries**: "What instruments are on float 1901442?"
- **Semantic Queries**: "Find profiles with temperature inversions"
- **Comparative Analysis**: "Compare Arabian Sea vs Bay of Bengal patterns"
- **Regional Analysis**: "Analyze salinity trends in the Arabian Sea"

## 🗺️ Map Visualization

The interactive map provides:
- Real-time Argo float positions
- Temperature and salinity overlays
- Regional boundary visualization
- Float trajectory tracking
- Data point clustering
- Custom marker styling

## 💬 Chat Interface

Features include:
- **Session Management**: Persistent conversation history
- **Context Awareness**: Remembers previous queries and responses
- **Real-time Status**: Backend connectivity monitoring
- **Error Recovery**: Automatic session cleanup and recreation
- **Response Streaming**: Real-time updates for long queries

## 🔍 API Documentation

### Chat Endpoints

**POST /api/v1/chat**
```json
{
  "query": "Show me temperature data for float 1901442",
  "session_id": "optional-session-id",
  "timeout": 300,
  "user_preferences": {
    "detail_level": "comprehensive",
    "preferred_regions": ["Arabian Sea"]
  }
}
```

**Response**
```json
{
  "response": "Analysis results...",
  "session_id": "session-uuid",
  "metadata": {
    "response_time": 2.5,
    "agent_type": "multi_agent",
    "max_cycles": 3,
    "has_context": true
  },
  "status": "success"
}
```

### Session Endpoints

- `POST /api/v1/sessions/create` - Create new session
- `GET /api/v1/sessions/{id}` - Get session info
- `GET /api/v1/sessions/{id}/history` - Get conversation history
- `DELETE /api/v1/sessions/{id}` - Delete session

## 🧪 Testing

### Backend Tests
```bash
cd backend-chatbot-test
python -m pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
# Test multi-agent system
python test_multi_agent.py

# Test cyclic refinement
python test_cyclic_agent.py
```

## 📊 Monitoring & Health

### Health Endpoints

- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system status
- `GET /metrics` - Performance metrics

### Monitoring Features

- Agent system health monitoring
- Database connection status
- Response time tracking
- Error rate monitoring
- Session statistics

## 🚨 Troubleshooting

### Common Issues

1. **404 Session Errors**
   - Sessions are stored in memory and lost on restart
   - Frontend automatically cleans up invalid sessions
   - New sessions are created automatically

2. **Backend Connection Issues**
   - Check if backend is running on port 8000
   - Verify environment variables are set
   - Check database connections

3. **Agent Timeout Errors**
   - Increase `AGENT_TIMEOUT` in configuration
   - Check database query performance
   - Verify API key limits

### Error Recovery

The system includes automatic error recovery:
- Session validation and cleanup
- Backend health monitoring
- Graceful degradation when services are unavailable
- Automatic retry mechanisms

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Guidelines

- Follow Python PEP 8 for backend code
- Use TypeScript for frontend development
- Add comprehensive error handling
- Include unit tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Argo Program**: For providing oceanographic data
- **LangChain**: For agent framework
- **FastAPI**: For high-performance API development
- **Next.js**: For modern React framework
- **Groq**: For fast LLM inference

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**Built with ❤️ for oceanographic research and marine science**
