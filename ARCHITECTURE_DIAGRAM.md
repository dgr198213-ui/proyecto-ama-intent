# 🏗️ AMA-Intent v3 Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AMA-Intent v3 System                         │
│                  Biomimetic Intelligence System                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ User runs
                              ▼
                      ┌──────────────┐
                      │  start.py    │
                      │  (Launcher)  │
                      └──────────────┘
                              │
                ┌─────────────┼─────────────┐
                │                           │
                ▼                           ▼
        ┌─────────────┐           ┌─────────────────┐
        │ Verify      │           │ Start Server    │
        │ Ollama      │           │ (bridge)        │
        └─────────────┘           └─────────────────┘
                                          │
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    │                                           │
                    │        bridge/server.py                   │
                    │        FastHTML Application               │
                    │                                           │
                    │  GET  / ────────► Web Interface           │
                    │  GET  /admin ───► Admin Dashboard         │
                    │  GET  /credenciales ► Credentials Panel   │
                    │                                           │
                    │  POST /api/synapse ─► Process Request     │
                    │                                           │
                    └───────────────────┬───────────────────────┘
                                        │
                           ┌────────────┼────────────┐
                           │                         │
                           ▼                         ▼
                  ┌──────────────────┐    ┌──────────────────┐
                  │ local_cortex/    │    │ local_cortex/    │
                  │ thought.py       │    │ memory.py        │
                  │                  │    │                  │
                  │ LocalBrain       │    │ SQLite DB        │
                  │ ├─ think()       │    │ ├─ init_db()    │
                  │ └─ fast_classify│    │ ├─ save_thought()│
                  │                  │    │ └─ get_last...() │
                  └────────┬─────────┘    └─────────┬────────┘
                           │                        │
                           │                        │
                           ▼                        ▼
                  ┌─────────────────┐      ┌─────────────────┐
                  │ Ollama          │      │ data/           │
                  │ (Llama 3.1)     │      │ ama_memory.db   │
                  └─────────────────┘      └─────────────────┘
```

## Component Details

### 1. Entry Point: `start.py`
**Purpose**: System launcher and health checker
- Checks Ollama availability
- Creates data directory if needed
- Launches the bridge server
- Handles graceful shutdown

### 2. Bridge Layer: `bridge/server.py`
**Purpose**: HTTP API for external communication
- **GET /**: Web interface showing system status
- **POST /api/synapse**: Main processing endpoint
  - Receives user input
  - Coordinates with brain and memory
  - Returns structured response

### 3. Brain Layer: `local_cortex/thought.py`
**Purpose**: AI processing and classification
- **LocalBrain class**:
  - `think()`: Processes user input with context
  - `fast_classify()`: Quick intent classification
- Uses Ollama for LLM inference
- System prompt defines biomimetic behavior

### 4. Memory Layer: `local_cortex/memory.py`
**Purpose**: Persistent storage and retrieval
- **Database**: SQLite (lightweight, serverless)
- **Functions**:
  - `init_db()`: Creates schema
  - `save_thought()`: Stores interactions
  - `get_last_thoughts()`: Context retrieval
- Uses context managers for safe transactions

## Data Flow

### Processing a Request

```
1. Client Request
   POST /api/synapse
   { "input": "What is Python?" }
        │
        ▼
2. Bridge receives request
   bridge/server.py::synapse()
        │
        ├─► Get context from memory
        │   memory.get_last_thoughts()
        │
        ├─► Classify intent
        │   brain.fast_classify()
        │
        ├─► Process with LLM
        │   brain.think()
        │
        └─► Save to memory
            memory.save_thought()
        │
        ▼
3. Client Response
   {
     "status": "success",
     "intent": "CHAT",
     "response": "Python is...",
     "timestamp": "2026-01-23T..."
   }
```

## File Structure

```
proyecto-ama-intent/
│
├── start.py                    # 🚀 Entry point
│
├── bridge/                     # 🌉 HTTP Layer
│   ├── __init__.py
│   └── server.py              # FastHTML app, /api/synapse endpoint
│
├── local_cortex/              # 🧠 Intelligence Layer
│   ├── __init__.py
│   ├── thought.py             # LocalBrain class, LLM processing
│   └── memory.py              # SQLite operations
│
├── data/                      # 💾 Persistence Layer
│   └── ama_memory.db         # SQLite database (auto-created)
│
├── requirements.txt           # 📦 Dependencies (4 only)
├── .env.example              # ⚙️ Configuration template
├── .gitignore                # 🚫 Exclude patterns
├── .flake8                   # 📏 Linting config
├── README.md                 # 📖 User documentation
├── REFACTORING_SUMMARY.md    # 📊 v2→v3 comparison
├── ARCHITECTURE_DIAGRAM.md   # 🏗️ This file
└── test_ama_v3.py           # 🧪 Test suite
```

## Configuration

### Environment Variables (.env)
```bash
HOST=127.0.0.1      # Server binding (localhost for security)
PORT=5001           # Server port
RELOAD=false        # Auto-reload (dev only)
OLLAMA_MODEL=llama3.1  # LLM model to use
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Server** | FastHTML + Uvicorn | Lightweight async HTTP |
| **Brain** | Ollama (Llama 3.1) | Local LLM inference |
| **Memory** | SQLite | Embedded database |
| **Config** | python-dotenv | Environment management |

## Design Principles

### 1. Biomimetic Architecture
- **Brain** (local_cortex): Processes and thinks
- **Memory** (data): Stores and recalls
- **Bridge** (HTTP): Communicates with outside world

### 2. Local-First
- No cloud dependencies
- All processing happens locally
- Data stays on your machine

### 3. Simplicity
- 4 dependencies only
- ~200 lines of core code
- No complex abstractions

### 4. Security
- Localhost binding by default
- Context managers for safety
- No secrets in code
- Subprocess isolation

### 5. Maintainability
- Clear separation of concerns
- Comprehensive tests
- Type hints and documentation
- Consistent code style

## Scalability Considerations

### Current (v3)
- Single-threaded server
- Local SQLite database
- One model at a time

### Future Enhancements
- Multi-model support
- Concurrent request handling
- Remote deployment option
- Plugin architecture
- Multi-user support

---

**Note**: This architecture prioritizes simplicity and local operation. 
For production deployments with high concurrency needs, consider:
- Using a connection pool for SQLite
- Adding Redis for session management
- Implementing request queuing
- Containerizing with Docker
