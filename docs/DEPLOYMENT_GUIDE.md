# Guía de Deployment: AMA-Intent + SDDCS
## Docker Compose + GitHub Actions CI/CD

**Versión:** 2.0  
**Fecha:** Enero 2026  
**Stack:** Docker, GitHub Actions, Nginx, Prometheus, Grafana

---

## 📋 Contenido

1. [Quick Start](#quick-start)
2. [Configuración Inicial](#configuración-inicial)
3. [Deployment Local](#deployment-local)
4. [Deployment en Producción](#deployment-en-producción)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Monitoreo](#monitoreo)
7. [Troubleshooting](#troubleshooting)

---

## 1. Quick Start

### Requisitos Previos

```bash
# Verificar instalaciones
docker --version          # >= 24.0
docker-compose --version  # >= 2.20
git --version            # >= 2.40
```

### Clonar e Iniciar (30 segundos)

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/ama-intent.git
cd ama-intent

# Generar configuración
make setup

# Iniciar servicios
make up
```

**Acceder:**
- Dashboard: http://localhost:8000
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

---

## 2. Configuración Inicial

### 2.1 Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Generar secretos
./scripts/generate_secrets.sh
```

**Contenido de `.env`:**

```bash
# =============================================================================
# SECURITY (⚠️ CAMBIAR EN PRODUCCIÓN)
# =============================================================================
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
SDDCS_NETWORK_SALT=$(openssl rand -hex 32)

# =============================================================================
# SDDCS CONFIGURATION
# =============================================================================
SDDCS_AGENT_ID=1
SDDCS_ENABLE_CHECKPOINTS=true
SDDCS_ENABLE_CACHE_VALIDATION=true
SDDCS_ENABLE_ROLLING_JWT=true
SDDCS_CHECKPOINT_INTERVAL=50
SDDCS_CACHE_TTL=3600

# =============================================================================
# LLM APIS
# =============================================================================
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514

# =============================================================================
# REDIS
# =============================================================================
REDIS_PASSWORD=$(openssl rand -hex 16)

# =============================================================================
# MONITORING
# =============================================================================
GRAFANA_PASSWORD=$(openssl rand -hex 16)

# =============================================================================
# BACKUP (AWS S3)
# =============================================================================
BACKUP_S3_BUCKET=ama-intent-backups
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# =============================================================================
# DOMAIN (Production only)
# =============================================================================
DOMAIN=ama.yourdomain.com
```

### 2.2 Estructura de Directorios

```bash
proyecto-ama-intent/
├── .github/
│   └── workflows/              # GitHub Actions CI/CD
│       ├── ci-cd.yml
│       ├── security-scan.yml
│       ├── backup-verify.yml
│       └── ...
├── docker/
│   ├── entrypoint.sh          # Script de inicio
│   └── backup/
│       └── Dockerfile
├── nginx/
│   ├── nginx.conf             # Reverse proxy config
│   └── ssl/                   # Certificados SSL
│       ├── fullchain.pem
│       └── privkey.pem
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│       ├── dashboards/
│       └── datasources/
├── data/                      # Database (volumen)
├── logs/                      # Logs de aplicación
├── uploads/                   # Archivos subidos
├── backups/                   # Backups locales
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── .env
```

---

## 3. Deployment Local

### 3.1 Inicio Completo

```bash
# Usando Makefile
make build    # Build imágenes
make up       # Iniciar servicios
make logs     # Ver logs

# O manualmente
docker-compose build
docker-compose up -d
docker-compose logs -f ama-dashboard
```

### 3.2 Verificar Servicios

```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/api/sddcs/health

# Verificar SDDCS
docker-compose exec ama-dashboard python -c "
from integrations.sddcs_kaprekar import kaprekar_routine
print('SDDCS OK:', kaprekar_routine(3524))
"
```

### 3.3 Crear Usuario Admin

```bash
docker-compose exec ama-dashboard python scripts/create_admin.py \
  --username admin \
  --password "ChangeMe123!" \
  --email admin@ama-intent.local
```

### 3.4 Tests de Integración

```bash
# Tests unitarios
make test

# Tests completos
docker-compose exec ama-dashboard pytest tests/ -v

# Tests específicos SDDCS
docker-compose exec ama-dashboard pytest tests/test_sddcs_integration.py -v
```

---

## 4. Deployment en Producción

### 4.1 Preparación del Servidor

```bash
# En servidor de producción
# Ubuntu 22.04 LTS recomendado

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar
docker --version
docker-compose --version
```

### 4.2 Configuración de Firewall

```bash
# UFW (Ubuntu Firewall)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

### 4.3 SSL con Let's Encrypt

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot certonly --standalone \
  -d ama.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos

# Copiar certificados
sudo cp /etc/letsencrypt/live/ama.yourdomain.com/fullchain.pem \
  /opt/ama-intent/nginx/ssl/
sudo cp /etc/letsencrypt/live/ama.yourdomain.com/privkey.pem \
  /opt/ama-intent/nginx/ssl/

# Auto-renewal
sudo crontab -e
# Añadir: 0 3 * * * certbot renew --post-hook "docker-compose -f /opt/ama-intent/docker-compose.yml restart nginx"
```

### 4.4 Deploy Inicial

```bash
# En servidor de producción
cd /opt
git clone https://github.com/tu-usuario/ama-intent.git
cd ama-intent

# Configurar .env (usar valores de producción)
nano .env

# Build y arranque
docker-compose build
docker-compose up -d

# Verificar
docker-compose ps
curl https://ama.yourdomain.com/health
```

### 4.5 Configurar Backups Automáticos

```bash
# El servicio de backup ya está configurado en docker-compose.yml
# Verificar que se ejecuta

docker-compose logs backup

# Forzar backup manual
docker-compose exec backup python /app/backup_script.py --manual

# Verificar en S3
aws s3 ls s3://ama-intent-backups/
```

---

## 5. CI/CD Pipeline

### 5.1 Configurar GitHub Actions

**Requisitos:**
1. Repositorio en GitHub
2. Acceso a servidor de producción vía SSH
3. Secrets configurados

### 5.2 Configurar Secrets en GitHub

```
Settings > Secrets and variables > Actions > New repository secret
```

**Secrets necesarios:**

| Secret | Descripción | Ejemplo |
|--------|-------------|---------|
| `STAGING_SSH_KEY` | Clave SSH para staging | Contenido de `id_rsa` |
| `STAGING_HOST` | Host de staging | `staging.ama.com` |
| `STAGING_USER` | Usuario SSH staging | `deploy` |
| `PRODUCTION_SSH_KEY` | Clave SSH producción | Contenido de `id_rsa` |
| `PRODUCTION_HOST` | Host de producción | `ama.com` |
| `PRODUCTION_USER` | Usuario SSH producción | `deploy` |
| `SLACK_WEBHOOK` | Webhook para notificaciones | `https://hooks.slack.com/...` |
| `CODECOV_TOKEN` | Token de Codecov | `abc123...` |

### 5.3 Flujo de Trabajo

```
┌─────────────┐
│  Git Push   │
│  to develop │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  CI Tests   │ ← Lint, Unit Tests, Security Scan
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Build Docker│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Deploy Stage │ ← Automatic
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Perf Tests   │
└─────────────┘

┌─────────────┐
│Git Release  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Backup Prod  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Deploy Prod  │ ← Manual Approval
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Smoke Tests  │
└─────────────┘
```

### 5.4 Crear Release

```bash
# Tag nueva versión
git tag -a v2.0.0 -m "Release AMA-Intent v2.0 with SDDCS"
git push origin v2.0.0

# Crear release en GitHub
# Esto dispara deployment automático a producción
```

### 5.5 Monitorear Pipeline

```bash
# Ver estado en tiempo real
https://github.com/tu-usuario/ama-intent/actions

# Recibir notificaciones en Slack
# Configurar webhook en .github/workflows/ci-cd.yml
```

---

## 6. Monitoreo

### 6.1 Acceder a Grafana

```
URL: http://your-server:3000
Usuario: admin
Password: [ver .env]
```

**Dashboards Incluidos:**

1. **AMA-Intent Overview**
   - Requests/segundo
   - Latencia p50, p95, p99
   - Tasa de error
   - CPU y memoria

2. **SDDCS Metrics**
   - Checkpoints creados
   - Validaciones exitosas/fallidas
   - Rolling JWT refreshes
   - Cache hit rate

3. **System Health**
   - Docker containers
   - Disk usage
   - Network I/O
   - Redis connections

### 6.2 Prometheus Queries Útiles

```promql
# Latencia p95 de checkpoints SDDCS
histogram_quantile(0.95, rate(sddcs_checkpoint_duration_seconds_bucket[5m]))

# Tasa de validación exitosa
sddcs_validation_success_rate

# Requests por segundo
rate(http_requests_total[1m])

# Memoria usada por container
container_memory_usage_bytes{container="ama-dashboard"}
```

### 6.3 Alertas

```bash
# Configurar en monitoring/prometheus-alerts.yml

groups:
  - name: ama-intent
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: SDDCSValidationFailures
        expr: sddcs_validation_success_rate < 0.9
        for: 10m
        annotations:
          summary: "SDDCS validation rate below 90%"
```

---

## 7. Troubleshooting

### Problema 1: Container No Inicia

```bash
# Ver logs detallados
docker-compose logs ama-dashboard

# Errores comunes:
# - "database locked" → Otro proceso está usando la DB
docker-compose restart ama-dashboard

# - "permission denied" → Problemas de permisos
sudo chown -R 1000:1000 ./data ./logs
```

### Problema 2: SDDCS No Inicializa

```bash
# Verificar migración
docker-compose exec ama-dashboard python -c "
import sqlite3
conn = sqlite3.connect('/app/data/ama_dashboard.db')
cursor = conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'sddcs%'\")
print('SDDCS Tables:', cursor.fetchall())
"

# Re-ejecutar migración
docker-compose exec ama-dashboard python scripts/sddcs_migration.py
```

### Problema 3: SSL/HTTPS No Funciona

```bash
# Verificar certificados
ls -la nginx/ssl/

# Verificar configuración Nginx
docker-compose exec nginx nginx -t

# Reload Nginx
docker-compose exec nginx nginx -s reload
```

### Problema 4: Alto Uso de Memoria

```bash
# Ver uso por container
docker stats

# Optimizar configuración
# En docker-compose.yml, añadir:
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 512M
```

### Problema 5: CI/CD Pipeline Falla

```bash
# Verificar SSH key
ssh -i ~/.ssh/production_key deploy@production-server

# Verificar secrets en GitHub
# Settings > Secrets > Verificar PRODUCTION_SSH_KEY

# Logs de GitHub Actions
# Ver en https://github.com/tu-usuario/ama-intent/actions
```

---

## 📞 Comandos Útiles

```bash
# Makefile shortcuts
make help       # Ver todos los comandos
make build      # Build imágenes
make up         # Iniciar servicios
make down       # Detener servicios
make logs       # Ver logs
make restart    # Reiniciar
make clean      # Limpiar todo
make test       # Ejecutar tests
make deploy     # Deploy a producción
make backup     # Backup manual

# Docker Compose directo
docker-compose ps                      # Estado de servicios
docker-compose exec ama-dashboard bash # Shell en container
docker-compose logs -f --tail=100      # Últimos 100 logs
docker-compose pull                    # Actualizar imágenes
docker-compose up -d --build           # Rebuild y reiniciar

# Debugging
docker-compose exec ama-dashboard python manage.py shell
docker-compose exec ama-dashboard pytest tests/ -v -s
docker-compose exec redis redis-cli -a $REDIS_PASSWORD

# Mantenimiento
docker system prune -a                 # Limpiar recursos no usados
docker volume prune                    # Limpiar volúmenes
docker-compose down -v                 # Detener y eliminar volúmenes
```

---

## 🎯 Checklist de Producción

- [ ] ✅ Variables de entorno configuradas
- [ ] ✅ Secretos generados (no usar defaults)
- [ ] ✅ SSL/TLS configurado
- [ ] ✅ Firewall configurado
- [ ] ✅ Backups automáticos funcionando
- [ ] ✅ Monitoreo (Prometheus + Grafana) activo
- [ ] ✅ Alertas configuradas
- [ ] ✅ CI/CD pipeline testeado
- [ ] ✅ Health checks funcionando
- [ ] ✅ Logs centralizados
- [ ] ✅ Documentación actualizada

---

**Última Actualización:** Enero 2026  
**Mantenido por:** AMA-Intent DevOps Team  
**Soporte:** devops@ama-intent.org