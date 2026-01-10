# 🧩 Guía de Desarrollo de Plugins para AMA-Intent

El Dashboard de AMA-Intent v2.0 cuenta con un sistema de plugins modular que permite extender las capacidades del cerebro artificial.

## 1. Estructura de un Plugin
Cada plugin debe residir en su propia carpeta dentro del directorio `plugins/` y contener al menos un archivo `plugin.json`.

```
plugins/mi_nuevo_plugin/
├── plugin.json         # Manifiesto del plugin
├── main.py             # Lógica principal
└── requirements.txt    # Dependencias (opcional)
```

## 2. El Manifiesto (`plugin.json`)
Define los metadatos y puntos de entrada del plugin.

```json
{
  "name": "mi_nuevo_plugin",
  "version": "1.0.0",
  "author": "Tu Nombre",
  "description": "Descripción de lo que hace el plugin",
  "plugin_type": "utility",
  "entry_point": "mi_nuevo_plugin.main.PluginMain",
  "dependencies": [],
  "permissions": ["read"]
}
```

## 3. Tipos de Plugins Soportados
*   `DEBUG_ASSISTANT`: Herramientas de depuración.
*   `CONTENT_CREATOR`: Generación de contenido.
*   `INTEGRATION`: Conectores con servicios externos.
*   `ANALYTICS`: Análisis de datos y métricas.
*   `UTILITY`: Herramientas generales de sistema.

## 4. Ciclo de Vida y Hooks
Los plugins pueden registrarse en diferentes "hooks" del sistema para interceptar acciones:
*   `pre_request`: Antes de procesar una solicitud.
*   `post_request`: Después de procesar una solicitud.
*   `error_analysis`: Durante la fase de depuración.

## 5. Ejemplo de Clase Principal
```python
class PluginMain:
    def __init__(self):
        self.enabled = True

    def register_hooks(self, manager):
        manager.register_hook('pre_request', self.on_pre_request)

    def on_pre_request(self, data):
        print(f"Plugin procesando datos: {data}")
        return data
```

---
Para más detalles, consulta el código fuente en `src/personal_dashboard/plugin_system.py`.
