#!/bin/bash
set -e

echo "🚀 Starting AMA-Intent Dashboard with SDDCS..."

# Esperar a que Redis esté listo
if [ -n "$REDIS_HOST" ]; then
    echo "⏳ Waiting for Redis..."
    while ! nc -z $REDIS_HOST ${REDIS_PORT:-6379}; do
        sleep 1
    done
    echo "✅ Redis is ready"
fi

# Inicializar base de datos si no existe
if [ ! -f /app/data/ama_dashboard.db ]; then
    echo "📦 Initializing database..."
    python scripts/migrate_and_upgrade.py
    echo "✅ Database initialized"
fi

# Ejecutar migraciones SDDCS
echo "🔄 Running SDDCS migrations..."
python scripts/sddcs_migration.py
echo "✅ SDDCS tables ready"

# Verificar configuración SDDCS
if [ "$SDDCS_ENABLE_CHECKPOINTS" = "true" ]; then
    echo "✅ SDDCS Checkpoints: ENABLED"
fi

if [ "$SDDCS_ENABLE_ROLLING_JWT" = "true" ]; then
    echo "✅ SDDCS Rolling JWT: ENABLED"
fi

# Crear directorios necesarios
mkdir -p /app/logs /app/uploads /app/backups

# Verificar permisos
if [ ! -w /app/data ]; then
    echo "⚠️  Warning: /app/data is not writable"
fi

echo "🎯 Starting application..."

# Ejecutar comando
exec "$@"
