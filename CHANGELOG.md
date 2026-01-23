# 📝 Changelog - AMA-Intent v3

## [v3.2.0] - 2026-01-23

### 🎉 Major Enhancements - Doctrina Howard (Production-Ready)

#### Security & Authentication
- **Secure Health Checks**: Added `/api/health` endpoint with shared secret authentication
- **Request Authentication**: All critical endpoints now require `X-AMA-Secret` header validation
- **Security Warnings System**: Real-time security status monitoring in admin dashboard
- **Credential Validation**: Automatic validation of Fernet keys and shared secrets

#### Credentials Management
- **Web Panel**: Minimalist credentials management interface at `/credenciales`
- **Hot Reload**: Immediate application of configuration changes without server restart
- **Secure Display**: Password masking for sensitive credentials
- **Validation Feedback**: Real-time validation of credential formats

#### Deployment Support
- **ASGI Entrypoint**: Added `asgi.py` for serverless deployment on Vercel
- **Vercel Configuration**: Included `vercel.json` with optimized settings
- **Production-Ready**: Secure defaults for production deployments

#### Improved Error Handling
- **Structured Logging**: Enhanced logging with configurable levels
- **HTTP Status Codes**: Proper error responses (401, 500) for different failure types
- **Detailed Error Messages**: Clear error descriptions for debugging

### 📊 Statistics

| Metric | v3.1 | v3.2 |
|--------|------|------|
| **API Endpoints** | 6 | 8 |
| **Security Features** | Basic | Production-Grade |
| **Deployment Options** | Local Only | Local + Serverless |
| **Configuration Management** | Manual | Web UI + Hot Reload |

### 🔧 Technical Improvements

- Added `validate_shared_secret()` for request authentication
- Added `validate_fernet_key()` for credential validation
- Added `reload_env()` for hot configuration reloading
- Added `get_security_warnings()` for security status monitoring
- Created deployment-ready ASGI application structure

### 📝 Documentation Updates

- Added Vercel deployment section to README
- Updated API documentation with authentication requirements
- Enhanced security configuration documentation

---

## [v3.1.0] - 2026-01-23

### 🎉 Major Enhancements

#### Memory Management System
- **Search Functionality**: Added `search_thoughts()` to find previous interactions by keyword
- **Statistics Dashboard**: Implemented `get_memory_stats()` for system usage analytics
- **Automatic Cleanup**: Added `cleanup_old_thoughts()` for memory archival
- **Intent Filtering**: New `get_thoughts_by_intent()` to retrieve specific interaction types

#### API Expansion
- **GET `/api/memory/search`**: Search through stored memories with query parameter
- **GET `/api/memory/stats`**: Retrieve system statistics and usage patterns
- **POST `/api/memory/cleanup`**: Clean up old memories based on configurable days
- **GET `/api/memory/by-intent/{intent}`**: Filter memories by intent type (CHAT, CODIGO, ANALISIS)
- **GET `/admin`**: Admin dashboard for system monitoring

#### Enhanced Processing
- **Confidence Scoring**: Classification now returns confidence levels
- **Better Error Handling**: Proper HTTP status codes (400, 500) with detailed error messages
- **Configurable Logging**: Environment variable `LOG_LEVEL` for adjustable logging
- **Context Management**: Configurable `MEMORY_CONTEXT_LIMIT` for flexible context windows

#### Configuration Improvements
Enhanced `.env.example` with new options:
- `OLLAMA_TIMEOUT`: Configure LLM request timeout
- `MEMORY_CONTEXT_LIMIT`: Number of recent thoughts for context
- `MEMORY_MAX_ENTRIES`: Maximum database entries before cleanup
- `MEMORY_ARCHIVE_DAYS`: Age threshold for memory archival
- `LOG_LEVEL`: Logging verbosity control

#### Testing
- Added 4 new comprehensive tests
- **Test Coverage**: 11/11 tests passing (100% success rate)
- Tests for search, statistics, cleanup, and intent filtering

#### Documentation
- Updated README.md with all new API endpoints
- Added detailed configuration documentation
- Included API response examples
- Updated test suite information

### 🔧 Technical Improvements

#### Code Quality
- Added proper exception handling throughout
- Implemented structured logging
- Type-safe dictionary returns from functions
- Context manager usage for database operations

#### Architecture
- Maintained minimalist philosophy (still ~4 core dependencies)
- Backward compatible with v3.0 API
- Clean separation of concerns
- RESTful API design

### 📊 Statistics

| Metric | Before (v3.0) | After (v3.1) |
|--------|---------------|--------------|
| **API Endpoints** | 1 | 6 |
| **Memory Functions** | 3 | 8 |
| **Test Coverage** | 7 tests | 11 tests |
| **Configuration Options** | 4 | 9 |
| **Error Handling** | Basic | HTTP Status Codes |

### 🎯 What's Next (v3.2 Planned)

- Multi-turn conversation tracking
- Request validation and sanitization
- Rate limiting for production deployments
- Integration tests with live Ollama
- Performance benchmarks
- WebSocket support for real-time processing

---

## [v3.0.0] - 2026-01-20

### Initial Release
- Complete refactoring from v2
- 84% reduction in dependencies (25+ → 4)
- 80% simplification in structure
- Biomimetic architecture (Brain, Memory, Bridge)
- Local-first with Ollama integration
- SQLite persistent memory
- FastHTML API server
- 7 comprehensive tests
