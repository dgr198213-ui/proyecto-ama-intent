# MiniMax Integration Module

Este módulo proporciona integración completa con los servicios de MiniMax para AMA-Intent v2.0.

## Componentes

### Audio Service
Síntesis de voz, clonación y diseño de voces personalizadas.

### Image Service
Generación de imágenes, diagramas, iconos y visualizaciones.

### Notification Service
Sistema de notificaciones multimodales que combina texto, voz e imágenes.

## Instalación

No se requieren dependencias adicionales. El módulo utiliza el cliente MCP ya configurado en el sistema.

## Uso Rápido

```python
from minimax_integration import AudioService, ImageService, NotificationService

# Audio
audio = AudioService()
audio.text_to_speech("Hola mundo", emotion="happy")

# Imágenes
images = ImageService()
images.generate_image("Un cerebro artificial futurista")

# Notificaciones
notifications = NotificationService()
notifications.send_notification("success", "Tarea completada", "Todo OK")
```

## Documentación Completa

Ver [docs/MINIMAX_INTEGRATION.md](../docs/MINIMAX_INTEGRATION.md) para documentación completa.
