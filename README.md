# 🧠 AMA-Intent v3: Cerebro Local Biomimético

Sistema de inteligencia artificial biomimética diseñado para ejecutar procesos de manera local, funcionando como "Cortex" de Qodeia.com. 

Esta versión v3 representa una refactorización completa hacia una arquitectura minimalista y funcional, reduciendo las dependencias en un 84% y simplificando la estructura en un 80%.

## 🚀 Funcionalidad
- **Local**: Corre completamente en tu máquina usando Ollama con Llama 3.1
- **Inteligente**: Memoria SQLite persistente con clasificación de intención automática
- **Conectado**: HTTP API FastHTML para integración con aplicaciones externas
- **Seguro**: Ejecución localhost por defecto, sin exposición a internet

## 📁 Estructura del Proyecto

```plaintext
proyecto-ama-intent/
├── .env                  # (NO SUBIR A GITHUB) Claves y secretos
├── .gitignore            # Importante: para ignorar .env y __pycache__
├── README.md             # El manual de uso biomimético
├── requirements.txt      # Dependencias ligeras
├── start.py              # El único archivo que necesitas ejecutar
├── data/                 # Donde vive tu memoria (SQLite)
│   └── ama_memory.db
├── local_cortex/         # 🧠 LÓGICA PURA (Tu cerebro local)
│   ├── __init__.py
│   ├── thought.py        # Procesa texto con Llama 3
│   └── memory.py         # Gestiona recuerdos en SQLite
└── bridge/               # 🌉 CONEXIÓN (Servidor Web)
    ├── __init__.py
    └── server.py         # API FastHTML que habla con Qodeia.com
```

## 🛠️ Instalación

### Requisitos Previos
1. Python 3.8 o superior
2. Ollama instalado y corriendo

### Pasos de Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/dgr198213-ui/proyecto-ama-intent.git
cd proyecto-ama-intent

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Verificar que Ollama está corriendo
ollama serve  # En otra terminal

# 4. Descargar el modelo (si no lo tienes)
ollama pull llama3.1
```

## 🚀 Uso

### Iniciar el Sistema

```bash
python start.py
```

El sistema:
1. Verificará la carpeta `data/` (la creará si no existe)
2. Verificará que Ollama está disponible
3. Iniciará el servidor en puerto 5001

### Acceder a la Interfaz

Abre tu navegador en: http://localhost:5001

### Acceder al Panel de Administración

Para ver estadísticas y gestionar el sistema: http://localhost:5001/admin

### Panel de Gestión

Para gestionar credenciales: http://localhost:5001/credenciales

### API Endpoints

**GET** `/api/health` (Nuevo en v3.2)

Endpoint de health check con autenticación.

**Headers requeridos:**
- `X-AMA-Secret`: El secreto compartido configurado en `AMA_SHARED_SECRET`

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-23T20:35:16.064640",
  "memory_stats": {
    "total_interactions": 0,
    "by_intent": {},
    "first_interaction": null,
    "last_interaction": null
  },
  "security_warnings": [
    "ℹ️ FERNET_KEY no configurado (opcional)"
  ]
}
```

**POST** `/api/synapse` (Requiere autenticación en v3.2)

Endpoint principal que procesa solicitudes.

**Headers requeridos:**
- `X-AMA-Secret`: El secreto compartido configurado en `AMA_SHARED_SECRET`

**Parámetros:**
- `input` (string): El texto a procesar

**Respuesta:**
```json
{
  "status": "success",
  "intent": "CHAT|CODIGO|ANALISIS",
  "confidence": 0.8,
  "response": "Respuesta generada por el modelo",
  "timestamp": "2026-01-23T16:35:20.123456"
}
```

**GET** `/api/memory/search?q={query}&limit={limit}`

Busca en la memoria del sistema.

**Parámetros:**
- `q` (string): Término de búsqueda
- `limit` (int, opcional): Número máximo de resultados (default: 10)

**Respuesta:**
```json
{
  "status": "success",
  "query": "Python",
  "count": 3,
  "results": [
    {
      "timestamp": "2026-01-23T16:35:20.123456",
      "input": "What is Python?",
      "output": "Python is...",
      "intent": "CHAT"
    }
  ]
}
```

**GET** `/api/memory/stats`

Obtiene estadísticas de la memoria del sistema.

**Respuesta:**
```json
{
  "status": "success",
  "stats": {
    "total_interactions": 150,
    "by_intent": {
      "CHAT": 80,
      "CODIGO": 50,
      "ANALISIS": 20
    },
    "first_interaction": "2026-01-20T10:00:00",
    "last_interaction": "2026-01-23T16:35:20"
  }
}
```

**POST** `/api/memory/cleanup`

Limpia pensamientos antiguos de la memoria.

**Parámetros:**
- `days` (int, opcional): Días de antigüedad para limpiar (default: 30)

**Respuesta:**
```json
{
  "status": "success",
  "deleted_count": 25,
  "message": "Cleaned up 25 thoughts older than 30 days"
}
```

**GET** `/api/memory/by-intent/{intent}`

Obtiene pensamientos filtrados por tipo de intención.

**Parámetros:**
- `intent` (string): CHAT, CODIGO, o ANALISIS
- `limit` (int, opcional): Número máximo de resultados (default: 10)

**Respuesta:**
```json
{
  "status": "success",
  "intent": "CODIGO",
  "count": 10,
  "results": [
    {
      "timestamp": "2026-01-23T16:35:20",
      "input": "Write a function",
      "output": "def example(): ..."
    }
  ]
}
```

## 🧠 Arquitectura

### Local Cortex (Cerebro Local)
- **thought.py**: Procesa entradas usando Llama 3.1 a través de Ollama
  - `LocalBrain.think()`: Genera respuestas contextualizadas
  - `LocalBrain.fast_classify()`: Clasifica el tipo de solicitud

- **memory.py**: Gestiona la memoria persistente
  - `init_db()`: Inicializa la base de datos SQLite
  - `save_thought()`: Guarda interacciones
  - `get_last_thoughts()`: Recupera contexto reciente

### Bridge (Puente HTTP)
- **server.py**: API FastHTML que conecta con el mundo exterior
  - Endpoint `/`: Interfaz de monitoreo
  - Endpoint `/api/synapse`: Procesa solicitudes

## 🔧 Configuración

### Variables de Entorno (.env)

```bash
# Server Configuration
HOST=127.0.0.1      # Server binding (localhost for security)
PORT=5001           # Server port
RELOAD=false        # Auto-reload (dev only)

# Security Configuration (Doctrina Howard) - NEW in v3.2
AMA_SHARED_SECRET=change-this-secret-in-production  # Shared secret for bridge authentication
FERNET_KEY=         # Optional: Leave empty to auto-generate, or provide a valid Fernet key

# Ollama Configuration
OLLAMA_MODEL=llama3.1  # LLM model to use

# Memory Configuration
MEMORY_CONTEXT_LIMIT=5     # Number of recent thoughts to use as context
MEMORY_MAX_ENTRIES=1000    # Maximum entries before triggering cleanup
MEMORY_ARCHIVE_DAYS=30     # Archive thoughts older than N days

# Logging Configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 🔐 Gestión de Credenciales (v3.2)

AMA-Intent v3.2 incluye un panel web para gestionar credenciales de forma segura:

1. **Acceder al Panel**: Navega a `http://localhost:5001/credenciales`
2. **Editar Claves**: Modifica `AMA_SHARED_SECRET`, `FERNET_KEY`, u `OLLAMA_MODEL`
3. **Hot Reload**: Los cambios se aplican inmediatamente sin reiniciar el servidor
4. **Validación**: El sistema valida automáticamente el formato de las claves

**Nota de Seguridad**: El panel está diseñado para entornos locales protegidos. Configura adecuadamente `AMA_SHARED_SECRET` en producción.

## 📊 Base de Datos

El sistema usa SQLite para persistir interacciones:

**Tabla: interactions**
- `id`: INTEGER PRIMARY KEY
- `timestamp`: TEXT (ISO 8601)
- `input`: TEXT (entrada del usuario)
- `output`: TEXT (respuesta del sistema)
- `intent`: TEXT (clasificación: CODIGO, CHAT, ANALISIS)

## 🐛 Solución de Problemas

### "Ollama no parece estar instalado"
Asegúrate de que Ollama está instalado y corriendo:
```bash
ollama serve
```

### "Error al conectar con Ollama"
Verifica que el modelo está descargado:
```bash
ollama pull llama3.1
```

### Puerto 5001 en uso
Cambia el puerto en `bridge/server.py` o usa la variable de entorno `PORT`:
```bash
PORT=5002 python start.py
```

### Error al importar módulos
Si ves errores de importación, reinstala las dependencias:
```bash
pip install -r requirements.txt --force-reinstall
```

## 🧪 Pruebas

Para verificar que todo funciona correctamente, ejecuta la suite de pruebas:

```bash
python test_ama_v3.py
```

Esta suite verifica:
- Estructura de directorios
- Importación de módulos
- Dependencias correctas
- Sintaxis de Python
- Funciones de memoria (init, save, retrieve)
- Búsqueda en memoria
- Estadísticas de memoria
- Limpieza de memoria
- Filtrado por intención

### Tests Actuales: 11/11 ✅

## 📋 Novedades en v3

### Cambios Principales desde v2
- ✅ **Reducción de dependencias**: De 25+ paquetes a solo 4
- ✅ **Simplificación estructural**: De 15+ directorios a 3 módulos core
- ✅ **Código más limpio**: ~200 líneas vs ~10,000 líneas anteriores
- ✅ **Seguridad mejorada**: Localhost por defecto, context managers, subprocess seguro
- ✅ **Tests automatizados**: Suite completa con 11 tests (100% cobertura core)
- ✅ **API expandida**: 6 endpoints para gestión completa del sistema
- ✅ **Panel de administración**: Dashboard web para monitoreo
- ✅ **Búsqueda en memoria**: Encuentra interacciones previas por palabras clave
- ✅ **Gestión automática**: Limpieza de memoria antigua
- ✅ **Configuración flexible**: Variables de entorno para personalización

### Nuevas Características en v3.1
- ✅ **Sistema de búsqueda**: Busca en memoria histórica
- ✅ **Estadísticas avanzadas**: Análisis de uso por tipo de intención
- ✅ **Limpieza automática**: Gestión de memoria con archivado
- ✅ **Filtros por intención**: Recupera interacciones específicas
- ✅ **Panel de admin**: Interfaz web para monitoreo del sistema
- ✅ **Mejor manejo de errores**: Códigos HTTP apropiados y logging
- ✅ **Confidence scoring**: Las clasificaciones incluyen nivel de confianza

### Nuevas Características en v3.2 - Doctrina Howard (Producción)
- ✅ **Panel de Gestión de Credenciales**: Interfaz minimalista en `/credenciales` para editar claves críticas
- ✅ **Hot Reload de Configuración**: Recarga inmediata de variables .env sin reiniciar el servidor
- ✅ **Blindaje del Túnel Seguro**: Validación de secreto compartido (`AMA_SHARED_SECRET`) en endpoints críticos
- ✅ **Health Check Seguro**: Endpoint `/api/health` con autenticación para monitoreo
- ✅ **Validación de Credenciales**: Verificación automática de formato de claves (Fernet)
- ✅ **Dashboard con Advertencias**: Panel de admin muestra alertas de seguridad en tiempo real
- ✅ **Sin Frameworks Adicionales**: Implementación pura con FastHTML, sin dependencias extras

### Características Eliminadas
- ❌ Dashboard web complejo
- ❌ Sistema de plugins v2
- ❌ Autenticación multi-usuario
- ❌ Integración MiniMax
- ❌ Soporte Docker (por ahora)

Ver `REFACTORING_SUMMARY.md` para detalles completos.

## 🚀 Despliegue en Vercel

AMA-Intent v3.2 incluye soporte para despliegue en plataformas serverless como Vercel:

### Archivos de Despliegue

- **asgi.py**: Punto de entrada ASGI para despliegue serverless
- **vercel.json**: Configuración de Vercel para el despliegue

### Configuración para Vercel

1. **Crea una cuenta en Vercel** (si no tienes una)
2. **Conecta tu repositorio** a Vercel
3. **Configura las variables de entorno** en el dashboard de Vercel:
   - `AMA_SHARED_SECRET`: Tu secreto compartido
   - `FERNET_KEY`: Clave de encriptación (opcional)
   - `OLLAMA_MODEL`: Modelo a utilizar (default: llama3.1)
   
4. **Despliega**: Vercel detectará automáticamente la configuración

**Nota**: Para usar Ollama en Vercel, necesitarás configurar un endpoint externo de Ollama accesible desde internet, ya que Vercel no permite procesos persistentes.

## 🎯 Próximos Pasos

- Integración con interfaces web externas
- Soporte para múltiples modelos
- Sistema de plugins expandible
- Análisis de código avanzado

## 📞 Soporte

Para reportar problemas o contribuir, abre un issue en el repositorio.

---

**AMA-Intent v3** - Sistema de Inteligencia Biomimética Local
