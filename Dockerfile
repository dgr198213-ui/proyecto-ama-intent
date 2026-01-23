# =============================================================================
# Dockerfile for AMA-Intent v3
# Biomimetic AI System with Local Cortex
# =============================================================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data logs backups

# Expose port
EXPOSE 5001

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=5001
ENV RELOAD=false
ENV OLLAMA_MODEL=llama3.1
ENV LOG_LEVEL=INFO

# Note: This container requires external Ollama service
# Set OLLAMA_BASE_URL environment variable to connect to Ollama
# Example: OLLAMA_BASE_URL=http://host.docker.internal:11434

# Run the application
CMD ["python", "-m", "bridge.server"]
