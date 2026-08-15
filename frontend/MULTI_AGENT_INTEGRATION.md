# Multi-Agent RAG Integration

This document describes the integration between the frontend chatbot and the Multi-Agent RAG backend system.

## 🔗 **Integration Overview**

The frontend chatbot now connects to a sophisticated Multi-Agent RAG system with:
- **6 Specialized Agents**: Measurement, Metadata, Semantic, Analysis, Refinement, and Coordinator
- **Session Management**: Conversation memory and context awareness
- **Cyclic Refinement**: Up to 3 cycles of quality improvement
- **Multi-Database**: CockroachDB, Neo4j, and Pinecone integration

## 🧠 **Session Management Features**

### **Automatic Session Creation**
- New sessions are created automatically when no session ID is provided
- Each session maintains conversation history and context
- Sessions persist for 1 hour of inactivity

### **Conversation Memory**
The system remembers:
- **Regions Discussed**: Arabian Sea, Bay of Bengal, etc.
- **Floats Analyzed**: All float IDs mentioned in conversation
- **Parameters of Interest**: Temperature, salinity, pressure, etc.
- **Query Patterns**: Types of analysis requested
- **User Preferences**: Detail level, output format, focus areas

### **Context Awareness**
- Follow-up queries automatically include previous context
- "Compare this with Arabian Sea" works because the system remembers previous floats
- Context is displayed in the sidebar for transparency

## 🚀 **Getting Started**

### **1. Start the Backend API**
```bash
cd backend-chatbot-test/api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **2. Test the API Connection**
```bash
cd frontend
node test-multi-agent-api.js
```

### **3. Start the Frontend**
```bash
cd frontend
npm run dev
```

### **4. Access the Application**
- Frontend: http://localhost:9002
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🎯 **New Features**

### **Session Sidebar**
- **New Chat Button**: Creates a new session with fresh context
- **Session List**: Shows all previous conversations
- **Context Display**: Shows current conversation context (regions, floats, parameters)
- **Session Management**: Delete sessions, switch between conversations

### **Enhanced Chat Interface**
- **Multi-Agent Indicators**: Shows when context is being used
- **Response Metadata**: Displays response time, cycles used, agent type
- **Session Status**: Shows active session ID
- **Example Queries**: Predefined queries to get started

### **Smart Context Handling**
- **Automatic Context**: Previous conversation informs new queries
- **Context Visualization**: See what the system remembers
- **Session Continuity**: Pick up conversations where you left off

## 📡 **API Integration**

### **Backend API Service** (`lib/backend-api.ts`)
```typescript
// Create new session
await backendApi.createSession(userPreferences);

// Send message with session
await backendApi.sendChatMessage(query, sessionId, userPreferences);

// Get conversation history
await backendApi.getConversationHistory(sessionId);
```

### **Session Manager Hook** (`hooks/use-session-manager.ts`)
```typescript
const {
  sessions,
  currentSessionId,
  currentMessages,
  createNewSession,
  sendMessage,
  switchToSession
} = useSessionManager();
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Frontend (.env)
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Backend (api/.env)
SESSION_TIMEOUT=3600
MAX_MESSAGES_PER_SESSION=100
MAX_CYCLES=3
QUALITY_THRESHOLD=0.7
```

## 🧪 **Example Usage**

### **1. Simple Query**
```
User: "Show me temperature data for float 7902073"
→ System creates session, analyzes float, returns comprehensive analysis
```

### **2. Follow-up with Context**
```
User: "How does this compare to Arabian Sea patterns?"
→ System remembers float 7902073, adds Arabian Sea context, provides comparison
```

### **3. Parameter Focus**
```
User: "What about salinity trends?"
→ System remembers both float and region, focuses on salinity analysis
```

## 🎨 **UI Components**

### **Session Context Display**
Shows active conversation context with badges for:
- **Regions**: Arabian Sea, Bay of Bengal
- **Floats**: 7902073, 5906432
- **Parameters**: temperature, salinity, pressure

### **Response Metadata**
Each assistant response shows:
- **Response Time**: How long the analysis took
- **Context Used**: Whether previous conversation informed the response
- **Cycles**: Number of refinement cycles used
- **Agent Type**: Multi-agent system identifier

### **Session Management**
- **Session List**: All previous conversations
- **Delete Sessions**: Remove old conversations
- **Switch Sessions**: Jump between different conversations
- **New Chat**: Start fresh conversation

## 🔍 **Debugging**

### **Check API Health**
```bash
curl http://localhost:8000/health/detailed
```

### **Test Session Creation**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/create \
  -H "Content-Type: application/json" \
  -d '{"user_preferences": {"detail_level": "comprehensive"}}'
```

### **Test Chat Message**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me temperature data for float 7902073",
    "session_id": "your-session-id"
  }'
```

## 📊 **Performance**

### **Response Times**
- Simple queries: 5-15 seconds
- Complex multi-agent queries: 15-60 seconds
- Context-aware follow-ups: 10-30 seconds

### **Session Limits**
- Session timeout: 1 hour
- Max messages per session: 100
- Max concurrent sessions: Unlimited (memory-based)

## 🚨 **Error Handling**

### **Session Expiration**
- Automatically creates new session if current session expires
- Graceful fallback with user notification

### **API Errors**
- Network errors: Retry with exponential backoff
- Server errors: Display user-friendly error messages
- Timeout errors: Suggest simpler queries

### **Connection Issues**
- Health check integration
- Automatic reconnection attempts
- Offline mode indicators

## 🔮 **Future Enhancements**

### **Planned Features**
- **Session Persistence**: Save sessions to database
- **Session Sharing**: Share conversations with colleagues
- **Export Conversations**: Download chat history
- **Advanced Preferences**: More granular user settings
- **Real-time Streaming**: Live response updates
- **Voice Integration**: Speech-to-text input

### **Scalability**
- **Redis Integration**: Distributed session storage
- **Load Balancing**: Multiple backend instances
- **Caching**: Response caching for common queries
- **Analytics**: Usage tracking and optimization

## 📚 **Resources**

- **Backend API Documentation**: http://localhost:8000/docs
- **Health Monitoring**: http://localhost:8000/health/detailed
- **Metrics**: http://localhost:8000/metrics
- **Session Statistics**: http://localhost:8000/api/v1/sessions/

The integration provides a seamless, intelligent chatbot experience with conversation memory and sophisticated multi-agent analysis capabilities! 🌊🧠