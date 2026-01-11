# docker/backup/Dockerfile
# Servicio de backup automatizado para AMA-Intent

FROM python:3.11-slim

LABEL maintainer="AMA-Intent Team"
LABEL description="Automated backup service with S3 support"

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
RUN pip install --no-cache-dir \
    boto3 \
    requests

# Crear directorios
WORKDIR /app
RUN mkdir -p /app/backups /app/logs /app/data

# Copiar scripts
COPY backup_script.py /app/
COPY restore_script.py /app/
COPY verify_backup.py /app/

# Copiar configuración de cron
COPY backup-cron /etc/cron.d/backup-cron

# Dar permisos al cron
RUN chmod 0644 /etc/cron.d/backup-cron && \
    crontab /etc/cron.d/backup-cron

# Crear archivo de log para cron
RUN touch /var/log/cron.log

# Script de inicio
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Ejecutar cron en foreground
CMD ["/app/entrypoint.sh"]

