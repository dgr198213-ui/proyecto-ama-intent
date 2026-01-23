# 🧠 AMA-Intent v3: Cerebro Local Biomimético

Sistema diseñado para ejecutar procesos como "Cortex" de Qodeia.com.

## 🚀 Funcionalidad
- **Local**: Corre localmente usando Ollama Llama 3.1.
- **Inteligente**: Usa memoria SQLite y clasificación de intención rápida.
- **Conectado**: HTTP API FastHTML accesible globalmente.

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

### API Endpoint

**POST** `/api/synapse`

**Parámetros:**
- `input` (string): El texto a procesar

**Respuesta:**
```json
{
  "status": "success",
  "intent": "CHAT|CODIGO|ANALISIS",
  "response": "Respuesta generada por el modelo",
  "timestamp": "2026-01-23T16:35:20.123456"
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
# Opcional: configurar modelo diferente
OLLAMA_MODEL=llama3.1

# Opcional: cambiar puerto
PORT=5001
```

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
Cambia el puerto en `bridge/server.py` o usa la variable de entorno `PORT`.

## 🎯 Próximos Pasos

- Integración con interfaces web externas
- Soporte para múltiples modelos
- Sistema de plugins expandible
- Análisis de código avanzado

## 📞 Soporte

Para reportar problemas o contribuir, abre un issue en el repositorio.

---

**AMA-Intent v3** - Sistema de Inteligencia Biomimética Local
