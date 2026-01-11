# =============================================================================
#!/bin/bash
# Script para instalar plugins de Grafana

set -e

echo "📦 Installing Grafana plugins..."

# Plugins útiles para AMA-Intent
grafana-cli plugins install grafana-piechart-panel
grafana-cli plugins install grafana-worldmap-panel
grafana-cli plugins install natel-discrete-panel
grafana-cli plugins install briangann-gauge-panel

echo "✅ Plugins installed successfully"

# Reiniciar Grafana para cargar plugins
if command -v systemctl &> /dev/null; then
    systemctl restart grafana-server
fi

