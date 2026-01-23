# Deploying AMA-Intent v3 to Vercel

## ⚠️ Important Limitations

AMA-Intent v3 requires **Ollama** to be running locally, which is **not compatible** with Vercel's serverless environment. This deployment guide is provided for reference, but you'll need to consider alternative approaches:

### Recommended Deployment Options:

1. **Local/On-Premise Deployment** (Recommended)
   - Run on your own server with Ollama installed
   - Best for full functionality with local LLM models
   - See main README.md for installation instructions

2. **Docker Container Deployment**
   - Use the provided Dockerfile
   - Deploy to services like:
     - Digital Ocean App Platform
     - AWS ECS/Fargate
     - Google Cloud Run
     - Azure Container Instances
   - Requires external Ollama service or API endpoint

3. **Vercel Deployment with External Ollama** (Limited)
   - Deploy API endpoints to Vercel
   - Configure OLLAMA_BASE_URL to point to external Ollama service
   - Requires publicly accessible Ollama instance (security considerations)

## Vercel Configuration

If you still want to deploy to Vercel (with external Ollama), follow these steps:

### 1. Prerequisites

- Vercel account
- External Ollama service accessible via URL
- Environment variables configured

### 2. Environment Variables

Add these to your Vercel project settings:

```bash
# Required
AMA_SHARED_SECRET=your-secure-secret-here
OLLAMA_BASE_URL=https://your-ollama-service.com
OLLAMA_MODEL=llama3.1

# Optional
FERNET_KEY=your-fernet-key-here
LOG_LEVEL=INFO
MEMORY_CONTEXT_LIMIT=5
MEMORY_MAX_ENTRIES=1000
MEMORY_ARCHIVE_DAYS=30
```

### 3. Deploy

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### 4. Known Issues with Vercel

- **No Ollama Service**: Vercel doesn't support running Ollama
- **Serverless Limitations**: Functions have time limits (10-60s)
- **Cold Starts**: First request may be slow
- **SQLite in Serverless**: Database persistence may not work as expected
- **Memory Storage**: May need to use external database

## Alternative: Docker Deployment

For production use, we recommend Docker deployment:

```bash
# Build image
docker build -t ama-intent:latest .

# Run with external Ollama
docker run -p 5001:5001 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e AMA_SHARED_SECRET=your-secret \
  -v $(pwd)/data:/app/data \
  ama-intent:latest
```

## Support

For deployment questions, open an issue on GitHub.

---

**Note**: This system is designed for local execution with Ollama. Cloud deployment requires significant architecture changes or external LLM API services.
