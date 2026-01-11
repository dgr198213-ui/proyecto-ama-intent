# Script para configurar monitoreo completo
# =============================================================================
#!/bin/bash

set -e

echo "🚀 Setting up AMA-Intent Monitoring Stack"
echo "=========================================="

# Crear directorios necesarios
echo "📁 Creating directories..."
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources
mkdir -p monitoring/prometheus/data

# Copiar dashboard JSON
echo "📊 Configuring Grafana dashboard..."
if [ ! -f "monitoring/grafana/dashboards/ama-intent-sddcs.json" ]; then
    cat > monitoring/grafana/dashboards/ama-intent-sddcs.json << 'EOF'
{
  "dashboard": {
    ...DASHBOARD JSON AQUÍ...
  }
}
EOF
fi

# Configurar datasource
echo "🔌 Configuring Prometheus datasource..."
cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

# Configurar dashboard provider
cat > monitoring/grafana/dashboards/dashboard-provider.yml << 'EOF'
apiVersion: 1
providers:
  - name: 'AMA-Intent'
    folder: 'Production'
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

# Generar contraseñas si no existen
if [ ! -f ".env" ]; then
    echo "🔐 Generating secrets..."
    
    GRAFANA_PASSWORD=$(openssl rand -hex 16)
    
    echo "GRAFANA_PASSWORD=$GRAFANA_PASSWORD" >> .env
    echo ""
    echo "✅ Grafana password: $GRAFANA_PASSWORD"
    echo "   (guardado en .env)"
fi

# Verificar que Prometheus está corriendo
echo "🔍 Checking Prometheus..."
if ! docker-compose ps prometheus | grep -q "Up"; then
    echo "⚠️  Prometheus no está corriendo. Iniciando..."
    docker-compose up -d prometheus
    sleep 5
fi

# Verificar que Grafana está corriendo
echo "🔍 Checking Grafana..."
if ! docker-compose ps grafana | grep -q "Up"; then
    echo "⚠️  Grafana no está corriendo. Iniciando..."
    docker-compose up -d grafana
    sleep 10
fi

# Importar dashboard vía API
echo "📤 Importing dashboard to Grafana..."
sleep 5  # Esperar a que Grafana esté listo

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS=$(grep GRAFANA_PASSWORD .env | cut -d '=' -f2)

# Crear API key
API_KEY_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -u "$GRAFANA_USER:$GRAFANA_PASS" \
    -d '{"name":"provisioning","role":"Admin"}' \
    "$GRAFANA_URL/api/auth/keys")

API_KEY=$(echo $API_KEY_RESPONSE | grep -o '"key":"[^"]*' | cut -d '"' -f4)

if [ -n "$API_KEY" ]; then
    echo "✅ Grafana API key created"
    
    # Importar dashboard
    curl -s -X POST \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d @monitoring/grafana/dashboards/ama-intent-sddcs.json \
        "$GRAFANA_URL/api/dashboards/db"
    
    echo "✅ Dashboard imported"
else
    echo "⚠️  Could not create API key (may already exist)"
fi

echo ""
echo "=========================================="
echo "✅ Monitoring setup complete!"
echo ""
echo "Access Grafana at: http://localhost:3000"
echo "Username: admin"
echo "Password: $GRAFANA_PASS"
echo ""
echo "Dashboard: AMA-Intent + SDDCS Production Dashboard"
echo "=========================================="
