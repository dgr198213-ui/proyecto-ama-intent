# Dockerfile
# Multi-stage build for AMA-Intent v2.0 + SDDCS-Kaprekar
# Optimizado para producción con seguridad y performance

# =============================================================================
# STAGE 1: Builder
# =============================================================================
FROM python:3.11-slim as builder

ARG PYTHON_VERSION=3.11
ARG ENABLE_SDDCS=true

LABEL maintainer="AMA-Intent Team <team@ama-intent.org>"
LABEL version="2.0-sddcs"

# Instalar dependencias de sistema necesarias para compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /build

# Copiar requirements
COPY requirements_dashboard.txt requirements.txt ./

# Instalar dependencias en entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements_dashboard.txt && \
    pip install --no-cache-dir -r requirements.txt

# Si SDDCS está habilitado, no necesitamos deps adicionales (usa stdlib)
RUN if [ "$ENABLE_SDDCS" = "true" ]; then \
        echo "✅ SDDCS habilitado (sin deps adicionales)"; \
    fi

# =============================================================================
# STAGE 2: Runtime
# =============================================================================
FROM python:3.11-slim

# Metadata
LABEL org.opencontainers.image.title="AMA-Intent Dashboard"
LABEL org.opencontainers.image.description="Sistema de IA Biomimética con SDDCS"
LABEL org.opencontainers.image.version="2.0"

# Crear usuario no-root para seguridad
RUN groupadd -r ama && useradd -r -g ama -u 1000 ama

# Instalar solo dependencias runtime necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copiar virtualenv desde builder
COPY --from=builder /opt/venv /opt/venv

# Configurar PATH
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Crear estructura de directorios
WORKDIR /app

RUN mkdir -p /app/data /app/logs /app/uploads /app/backups /app/static /app/templates && \
    chown -R ama:ama /app

# Copiar código de la aplicación
COPY --chown=ama:ama . /app/

# Copiar integración SDDCS
COPY --chown=ama:ama integrations/ /app/integrations/

# Ejecutar migración de base de datos en build time (solo estructura)
RUN python scripts/sddcs_migration.py --create-schema-only || true

# Cambiar a usuario no-root
USER ama

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Script de inicio
COPY --chown=ama:ama docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

# Comando por defecto: Gunicorn con workers
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "/app/logs/access.log", \
     "--error-logfile", "/app/logs/error.log", \
     "--log-level", "info", \
     "ama_personal_dashboard:app"]