#!/bin/bash
# Script de backup y recuperación para AMA-Intent Dashboard
# Autor: Manus IA

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="ama_backup_${TIMESTAMP}"

# Colores para output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

backup_database() {
    print_info "Iniciando backup de base de datos..."
    
    if [ "$DB_ENGINE" = "postgresql" ]; then
        # Backup PostgreSQL
        PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
            -d "$DB_NAME" -F c -f "${BACKUP_DIR}/${BACKUP_NAME}.dump"
        
        if [ $? -eq 0 ]; then
            print_info "Backup PostgreSQL creado: ${BACKUP_DIR}/${BACKUP_NAME}.dump"
        else
            print_error "Error creando backup PostgreSQL"
            return 1
        fi
    else
        # Backup SQLite
        if [ -f "$DB_PATH" ]; then
            cp "$DB_PATH" "${BACKUP_DIR}/${BACKUP_NAME}.db"
            print_info "Backup SQLite creado: ${BACKUP_DIR}/${BACKUP_NAME}.db"
        else
            print_warn "Archivo de base de datos SQLite no encontrado: $DB_PATH"
        fi
    fi
}

backup_files() {
    print_info "Iniciando backup de archivos..."
    
    # Crear archivo tar con archivos importantes
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_files.tar.gz" \
        --exclude="__pycache__" \
        --exclude="*.pyc" \
        --exclude=".git" \
        --exclude="data/*.db" \
        --exclude="backups" \
        src/ \
        templates/ \
        static/ \
        plugins/ \
        *.py \
        *.txt \
        *.md \
        .env.production 2>/dev/null || true
    
    print_info "Backup de archivos creado: ${BACKUP_DIR}/${BACKUP_NAME}_files.tar.gz"
}

backup_env() {
    print_info "Creando backup de configuración..."
    
    # Backup de variables sensibles
    cp .env.production "${BACKUP_DIR}/${BACKUP_NAME}.env" 2>/dev/null || true
    
    # Crear archivo de metadatos
    cat > "${BACKUP_DIR}/${BACKUP_NAME}.meta.json" << EOF
{
    "backup_name": "${BACKUP_NAME}",
    "timestamp": "${TIMESTAMP}",
    "version": "2.0.0",
    "components": ["database", "files", "env"],
    "database_engine": "${DB_ENGINE}"
}
EOF
    
    print_info "Backup de configuración creado"
}

list_backups() {
    print_info "Backups disponibles:"
    echo "========================================"
    
    for meta in "${BACKUP_DIR}"/*.meta.json; do
        if [ -f "$meta" ]; then
            name=$(basename "$meta" .meta.json)
            timestamp=$(jq -r '.timestamp' "$meta" 2>/dev/null || echo "N/A")
            engine=$(jq -r '.database_engine' "$meta" 2>/dev/null || echo "N/A")
            echo "• ${name} | ${timestamp} | ${engine}"
        fi
    done
    
    echo "========================================"
}

restore_backup() {
    local backup_name=$1
    
    if [ -z "$backup_name" ]; then
        print_error "Debes especificar un nombre de backup"
        list_backups
        return 1
    fi
    
    print_warn "⚠️  ADVERTENCIA: Esto restaurará desde el backup ${backup_name}"
    print_warn "               Los datos actuales serán sobrescritos"
    
    read -p "¿Continuar? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_info "Restauración cancelada"
        return 0
    fi
    
    # Verificar que exista el backup
    if [ ! -f "${BACKUP_DIR}/${backup_name}.meta.json" ]; then
        print_error "Backup no encontrado: ${backup_name}"
        return 1
    fi
  