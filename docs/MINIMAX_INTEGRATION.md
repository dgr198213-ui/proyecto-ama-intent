# Integración MiniMax en AMA-Intent

## Visión General

La integración de MiniMax en AMA-Intent añade capacidades multimodales avanzadas al sistema, incluyendo síntesis de voz, generación de imágenes, videos y música. Esta integración mejora significativamente la accesibilidad, la experiencia de usuario y las capacidades de comunicación del sistema.

## Arquitectura de la Integración

La integración se estructura en varios componentes modulares que interactúan con la API de MiniMax a través del cliente MCP (Model Context Protocol).

### Componentes Principales

#### 1. Audio Service (`minimax_integration/audio_service.py`)

El servicio de audio proporciona capacidades de síntesis de voz (text-to-speech), clonación de voces y diseño de voces personalizadas.

**Características principales:**

- **Síntesis de voz:** Conversión de texto a audio con control de emoción, velocidad, tono y calidad
- **Listado de voces:** Acceso a todas las voces disponibles en el sistema
- **Diseño de voces:** Creación de voces personalizadas basadas en descripciones textuales
- **Notificaciones audibles:** Generación automática de sonidos de notificación según el tipo

**Ejemplo de uso:**

```python
from minimax_integration import AudioService

audio_service = AudioService()

# Síntesis de voz básica
result = audio_service.text_to_speech(
    text="Bienvenido al sistema AMA-Intent",
    emotion="happy",
    speed=1.0
)

# Listar voces disponibles
voices = audio_service.list_available_voices()

# Generar notificación de éxito
notification = audio_service.generate_notification_sound(
    notification_type="success",
    message="Tarea completada"
)
```

**Parámetros de configuración:**

| Parámetro | Tipo | Valores | Descripción |
|-----------|------|---------|-------------|
| `emotion` | str | happy, sad, angry, fearful, disgusted, surprised, neutral | Emoción de la voz |
| `speed` | float | 0.5 - 2.0 | Velocidad de reproducción |
| `pitch` | int | -12 a 12 | Tono de la voz |
| `volume` | float | 0 - 10 | Volumen del audio |
| `sample_rate` | int | 8000, 16000, 22050, 24000, 32000, 44100 | Tasa de muestreo |
| `format` | str | mp3, wav, flac, pcm | Formato de salida |

#### 2. Image Service (`minimax_integration/image_service.py`)

El servicio de imágenes permite generar visualizaciones, diagramas, iconos y otros elementos gráficos mediante prompts de texto.

**Características principales:**

- **Generación de imágenes:** Creación de imágenes a partir de descripciones textuales
- **Diagramas de arquitectura:** Visualización automática de componentes y relaciones
- **Grafos de conocimiento:** Representación visual de estructuras de datos
- **Generación de iconos:** Creación de iconos personalizados para la interfaz
- **Fondos para widgets:** Generación de fondos temáticos para el dashboard
- **Logos de proyectos:** Diseño de logos basados en descripciones

**Ejemplo de uso:**

```python
from minimax_integration import ImageService

image_service = ImageService()

# Generar diagrama de arquitectura
components = ["Dashboard", "Core Cognitivo", "Plugins", "Base de Datos"]
relationships = [
    {"from": "Dashboard", "to": "Core Cognitivo", "type": "uses"},
    {"from": "Core Cognitivo", "to": "Plugins", "type": "manages"}
]

diagram = image_service.generate_architecture_diagram(
    components=components,
    relationships=relationships
)

# Generar icono
icon = image_service.generate_icon(
    description="artificial brain with neural connections",
    style="modern"
)

# Generar logo
logo = image_service.generate_project_logo(
    project_name="AMA-Intent",
    project_description="biomimetic AI system"
)
```

**Parámetros de configuración:**

| Parámetro | Tipo | Valores | Descripción |
|-----------|------|---------|-------------|
| `aspect_ratio` | str | 1:1, 16:9, 4:3, 3:2, 2:3, 3:4, 9:16, 21:9 | Relación de aspecto |
| `n` | int | 1 - 9 | Número de imágenes a generar |
| `prompt_optimizer` | bool | true, false | Optimización automática del prompt |
| `style` | str | modern, flat, 3d, minimalist | Estilo visual |

#### 3. Notification Service (`minimax_integration/notification_service.py`)

El servicio de notificaciones combina texto, voz e imágenes para crear notificaciones multimodales ricas y efectivas.

**Características principales:**

- **Notificaciones multimodales:** Combinación de texto, audio e iconos
- **Notificaciones tipificadas:** Soporte para info, success, warning, error, critical
- **Notificaciones contextuales:** Adaptación automática de voz y estilo según el tipo
- **Notificaciones de tareas:** Alertas de finalización de tareas con métricas
- **Notificaciones de análisis:** Resúmenes audibles de resultados de análisis
- **Recordatorios de bienestar:** Alertas de salud y ergonomía

**Ejemplo de uso:**

```python
from minimax_integration import NotificationService

notification_service = NotificationService()

# Notificación de tarea completada
result = notification_service.notify_task_complete(
    task_name="Análisis de código",
    duration=45.3,
    with_audio=True
)

# Notificación de error
error = notification_service.notify_error(
    error_type="ImportError",
    error_message="Módulo no encontrado",
    with_audio=True
)

# Recordatorio de bienestar
wellness = notification_service.notify_wellness_reminder(
    reminder_type="break",
    message="Es hora de tomar un descanso",
    with_audio=True
)
```

## Plugins Mejorados

### Voice Assistant Plugin

El plugin de asistente de voz proporciona una interfaz completa de interacción por voz con el sistema.

**Capacidades:**

- Lectura en voz alta de resultados de análisis
- Lectura de listas de tareas pendientes
- Notificaciones audibles de eventos del sistema
- Selección y configuración de voces
- Control de volumen y velocidad

**Ejemplo de uso:**

```python
from plugins.voice_assistant import VoiceAssistantPlugin

voice_assistant = VoiceAssistantPlugin()

# Leer resultados de análisis
analysis_data = {
    "quality_score": 85,
    "issues_found": 3,
    "recommendations": ["Mejorar docs", "Añadir tests"]
}
voice_assistant.read_analysis_results(analysis_data)

# Leer lista de tareas
todos = [
    {"name": "Implementar feature X"},
    {"name": "Revisar PR #123"}
]
voice_assistant.read_todo_list(todos)

# Recordatorio de bienestar
voice_assistant.wellness_reminder(reminder_type="break")
```

### Wellness Assistant Plugin (Enhanced)

El plugin de asistente de bienestar ha sido mejorado con guías de audio completas para ejercicios, meditación y recordatorios.

**Capacidades:**

- **Pausas guiadas:** Instrucciones de audio para pausas activas
- **Sesiones de meditación:** Guías de respiración, escaneo corporal y mindfulness
- **Ejercicios de estiramiento:** Rutinas completas con instrucciones paso a paso
- **Recordatorios de postura:** Alertas para corregir la postura
- **Ejercicios visuales:** Guías para descansar la vista
- **Recordatorios de hidratación:** Alertas para beber agua

**Ejemplo de uso:**

```python
from plugins.wellness_assistant import WellnessAssistantPlugin

wellness = WellnessAssistantPlugin()

# Pausa guiada de 5 minutos
wellness.guided_break(duration_minutes=5)

# Sesión de meditación de respiración
wellness.meditation_session(session_type="breathing")

# Rutina de estiramientos
wellness.stretching_routine()

# Recordatorio de postura
wellness.posture_check_reminder()

# Ejercicio de descanso visual
wellness.eye_rest_exercise()
```

## Integración con el Dashboard

### Endpoints de API

Los nuevos servicios se exponen a través de endpoints RESTful en el dashboard.

#### Audio Endpoints

```
POST /api/voice/speak
POST /api/voice/list-voices
POST /api/voice/set-voice
POST /api/voice/design-voice
```

#### Image Endpoints

```
POST /api/images/generate
POST /api/images/diagram
POST /api/images/icon
POST /api/images/logo
```

#### Notification Endpoints

```
POST /api/notifications/send
POST /api/notifications/task-complete
POST /api/notifications/error
POST /api/notifications/wellness
```

### Interfaz de Usuario

Se recomienda añadir los siguientes elementos a la interfaz del dashboard:

**Panel de Control de Voz:**
- Toggle para habilitar/deshabilitar voz
- Selector de voz disponible
- Control de volumen y velocidad
- Botón de prueba de voz

**Galería de Visualizaciones:**
- Vista de imágenes generadas
- Filtros por tipo (diagrama, icono, logo)
- Opciones de descarga y compartir

**Centro de Notificaciones:**
- Lista de notificaciones recientes
- Toggle de audio por notificación
- Configuración de tipos de notificación

**Panel de Bienestar:**
- Botones para iniciar ejercicios guiados
- Temporizador de pausas
- Historial de sesiones de bienestar

## Configuración

### Variables de Entorno

Las credenciales de MiniMax deben configurarse en el sistema de gestión de credenciales del dashboard:

```bash
# No es necesario configurar variables de entorno adicionales
# MiniMax se integra a través de MCP que ya está configurado
```

### Configuración de Plugins

Los plugins pueden configurarse a través del archivo de configuración del dashboard:

```json
{
  "plugins": {
    "voice_assistant": {
      "enabled": true,
      "default_voice": "audiobook_female_1",
      "default_speed": 1.0,
      "auto_read_notifications": true
    },
    "wellness_assistant": {
      "enabled": true,
      "audio_guides": true,
      "break_interval": 3600,
      "auto_reminders": true
    }
  }
}
```

## Consideraciones de Rendimiento

### Caché de Audio

Los archivos de audio generados se almacenan en caché para evitar regeneración:

```
ama_data/
├── audio/          # Archivos de audio generales
├── wellness/       # Audio de wellness assistant
│   └── audio/
└── notifications/  # Audio de notificaciones
    └── audio/
```

### Caché de Imágenes

Las imágenes generadas se almacenan localmente:

```
ama_data/
├── images/         # Imágenes generales
└── notifications/  # Iconos de notificaciones
    └── images/
```

### Optimización de Costos

Para minimizar los costos de API de MiniMax:

- Cachear contenido multimedia generado
- Reutilizar voces y estilos comunes
- Implementar rate limiting en endpoints
- Usar generación asíncrona para tareas no urgentes

## Seguridad

### Almacenamiento de Credenciales

Las credenciales de MiniMax se gestionan a través del Credential Manager cifrado del dashboard, que utiliza encriptación AES-256.

### Validación de Entrada

Todos los servicios validan y sanitizan las entradas del usuario para prevenir inyección de prompts maliciosos.

### Control de Acceso

El acceso a los servicios de MiniMax está protegido por el sistema de autenticación JWT del dashboard.

## Testing

### Tests Unitarios

Cada servicio incluye tests unitarios que pueden ejecutarse con:

```bash
python3 -m pytest tests/test_minimax_integration.py
```

### Tests de Integración

Los plugins incluyen ejemplos de uso que sirven como tests de integración:

```bash
python3 minimax_integration/audio_service.py
python3 minimax_integration/image_service.py
python3 plugins/voice_assistant/__init__.py
python3 plugins/wellness_assistant/__init__.py
```

## Troubleshooting

### Problema: Audio no se genera

**Solución:** Verificar que el servidor MCP de MiniMax está configurado y autenticado correctamente.

```bash
manus-mcp-cli tool list --server minimax
```

### Problema: Imágenes de baja calidad

**Solución:** Mejorar los prompts con más detalles descriptivos y usar `prompt_optimizer=True`.

### Problema: Latencia alta

**Solución:** Implementar generación asíncrona y caché agresivo de contenido frecuente.

## Roadmap Futuro

### Fase 1 (Completada)
- [x] Integración básica de audio
- [x] Integración básica de imágenes
- [x] Plugin de Voice Assistant
- [x] Mejora de Wellness Assistant

### Fase 2 (Planificada)
- [ ] Integración de generación de videos
- [ ] Integración de generación de música
- [ ] Tutorial Generator plugin
- [ ] Clonación de voz personalizada

### Fase 3 (Futura)
- [ ] Asistente de voz conversacional con IA
- [ ] Generación automática de documentación visual
- [ ] Sistema de música adaptativa según productividad
- [ ] Videos de onboarding personalizados

## Referencias

- [Documentación de MiniMax MCP](https://github.com/minimax-ai/mcp-server)
- [AMA-Intent Dashboard README](../DASHBOARD_README.md)
- [Sistema de Plugins](./PLUGINS.md)
- [Credential Manager](../src/config_manager/credentials_manager.py)

## Soporte

Para reportar problemas o sugerir mejoras relacionadas con la integración de MiniMax, por favor consulte la documentación interna del proyecto.
