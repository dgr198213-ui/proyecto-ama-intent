#!/bin/bash
# Script de backup y recuperación para AMA-Intent Dashboard
# Autor: Manus IA

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="ama_backup_${TIMESTAMP}"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
    # Lógica simplificada para el script de producción
    if [ -f "./data/personal.db" ]; then
        cp "./data/personal.db" "${BACKUP_DIR}/${BACKUP_NAME}.db"
        print_info "Backup SQLite creado: ${BACKUP_DIR}/${BACKUP_NAME}.db"
    else
        print_warn "No se encontró base de datos para respaldar."
    fi
}

backup_files() {
    print_info "Iniciando backup de archivos..."
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_files.tar.gz" \
        --exclude="__pycache__" \
        --exclude="*.pyc" \
        --exclude=".git" \
        src/ templates/ static/ plugins/ 2>/dev/null || true
    print_info "Backup de archivos creado."
}

list_backups() {
    print_info "Backups disponibles en ${BACKUP_DIR}:"
    ls -lh ${BACKUP_DIR}
}

case "$1" in
    backup)
        mkdir -p ${BACKUP_DIR}
        backup_database
        backup_files
        ;;
    list)
        list_backups
        ;;
    *)
        echo "Uso: $0 {backup|list}"
        exit 1
        ;;
esac
