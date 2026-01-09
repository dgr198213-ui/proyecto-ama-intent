#!/bin/bash
# AMA-Intent v2.0 - Script de Workflow Personal
# Automatiza el arranque y gestión diaria del sistema

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_PORT=8000
DASHBOARD_URL="http://localhost:${DASHBOARD_PORT}"

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}🚀 AMA-Intent v2.0 - Workflow${NC}"
echo -e "${BLUE}=================================${NC}\n"

# Función: Verificar dependencias
check_dependencies() {
    echo -e "${YELLOW}🔍 Verificando dependencias...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 no encontrado${NC}"
        exit 1
    fi
    
    if [ ! -f "requirements_dashboard.txt" ]; then
        echo -e "${RED}❌ requirements_dashboard.txt no encontrado${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Dependencias OK${NC}\n"
}

# Función: Verificar configuración
check_configuration() {
    echo -e "${YELLOW}🔧 Verificando configuración...${NC}"
    
    if [ ! -f ".env" ]; then
        echo -e "${RED}❌ Archivo .env no encontrado${NC}"
        echo -e "${YELLOW}Ejecuta: python3 scripts/setup_first_time.py${NC}"
        exit 1
    fi
    
    if [ ! -f "data/ama_intent.db" ]; then
        echo -e "${RED}❌ Base de datos no encontrada${NC}"
        echo -e "${YELLOW}Ejecuta: python3 scripts/migrate_and_upgrade.py${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Configuración OK${NC}\n"
}

# Función: Crear backup
create_backup() {
    echo -e "${YELLOW}💾 Creando backup...${NC}"
    
    if python3 scripts/backup_manager.py now; then
        echo -e "${GREEN}✅ Backup creado${NC}\n"
    else
        echo -e "${RED}⚠️  Advertencia: No se pudo crear backup${NC}\n"
    fi
}

# Función: Verificar salud del sistema
health_check() {
    echo -e "${YELLOW}🏥 Verificando salud del sistema...${NC}"
    
    if python3 scripts/health_check.py; then
        echo -e "${GREEN}✅ Sistema saludable${NC}\n"
    else
        echo -e "${RED}⚠️  Se detectaron problemas${NC}\n"
        read -p "¿Continuar de todos modos? (s/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            exit 1
        fi
    fi
}

# Función: Iniciar dashboard
start_dashboard() {
    echo -e "${YELLOW}🎯 Iniciando dashboard...${NC}"
    
    # Verificar si ya está corriendo
    if lsof -Pi :${DASHBOARD_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Dashboard ya está corriendo en puerto ${DASHBOARD_PORT}${NC}"
        read -p "¿Reiniciar? (s/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            pkill -f "ama_personal_dashboard.py" || true
            sleep 2
        else
            echo -e "${GREEN}✅ Usando instancia existente${NC}"
            return 0
        fi
    fi
    
    # Iniciar en background
    nohup python3 ama_personal_dashboard.py > logs/dashboard.log 2>&1 &
    DASHBOARD_PID=$!
    
    echo -e "${GREEN}✅ Dashboard iniciado (PID: ${DASHBOARD_PID})${NC}"
    echo "$DASHBOARD_PID" > .dashboard.pid
    
    # Esperar a que el servidor esté listo
    echo -e "${YELLOW}⏳ Esperando que el servidor esté listo...${NC}"
    for i in {1..15}; do
        if curl -s "${DASHBOARD_URL}" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Servidor listo${NC}\n"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}⚠️  El servidor tardó en responder${NC}\n"
}

# Función: Abrir navegador
open_browser() {
    echo -e "${YELLOW}🌐 Abriendo navegador...${NC}"
    
    # Detectar sistema operativo y abrir navegador
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "${DASHBOARD_URL}" 2>/dev/null || sensible-browser "${DASHBOARD_URL}" 2>/dev/null
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        open "${DASHBOARD_URL}"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        start "${DASHBOARD_URL}"
    else
        echo -e "${YELLOW}Sistema operativo no detectado, abre manualmente: ${DASHBOARD_URL}${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Navegador abierto${NC}\n"
}

# Función: Mostrar estado
show_status() {
    echo -e "${BLUE}📊 Estado del Sistema${NC}\n"
    
    if lsof -Pi :${DASHBOARD_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Dashboard: Corriendo${NC}"
        echo -e "   Puerto: ${DASHBOARD_PORT}"
        echo -e "   URL: ${DASHBOARD_URL}"
    else
        echo -e "${RED}❌ Dashboard: Detenido${NC}"
    fi
    
    echo ""
    
    if [ -f "data/ama_intent.db" ]; then
        DB_SIZE=$(du -h data/ama_intent.db | cut -f1)
        echo -e "${GREEN}✅ Base de datos: ${DB_SIZE}${NC}"
    else
        echo -e "${RED}❌ Base de datos: No encontrada${NC}"
    fi
}

# Función principal
main() {
    case "${1:-start}" in
        start)
            check_dependencies
            check_configuration
            create_backup
            health_check
            start_dashboard
            sleep 2
            open_browser
            ;;
        stop)
            echo -e "${YELLOW}🛑 Deteniendo dashboard...${NC}"
            pkill -f "ama_personal_dashboard.py" && echo -e "${GREEN}✅ Dashboard detenido${NC}" || echo -e "${YELLOW}⚠️  No hay dashboard corriendo${NC}"
            ;;
        status)
            show_status
            ;;
        *)
            echo "Uso: $0 {start|stop|status}"
            exit 1
            ;;
    esac
}

# Ejecutar
main "$@"
