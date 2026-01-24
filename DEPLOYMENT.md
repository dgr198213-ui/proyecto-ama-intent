# Despliegue de AMA-Intent v3

## 🎯 Propósito del Proyecto

AMA-Intent v3 está diseñado para **ejecución local** usando Ollama con modelos de lenguaje locales. Este proyecto NO está diseñado para despliegue en servicios serverless como Vercel o AWS Lambda.

## ✅ Despliegue Local (Recomendado)

Este es el método recomendado y soportado:

### Requisitos
- Python 3.10 o superior
- Ollama instalado y ejecutándose
- Sistema operativo: Linux, macOS, o Windows

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/dgr198213-ui/proyecto-ama-intent.git
cd proyecto-ama-intent

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno (opcional)
cp .env.example .env
# Editar .env según tus necesidades

# 4. Iniciar Ollama (en otra terminal)
ollama serve

# 5. Iniciar el servidor
python start.py
```

El sistema estará disponible en `http://localhost:5001`

## ❌ Despliegue en Vercel/Serverless NO Soportado

AMA-Intent v3 **NO** es compatible con Vercel u otros servicios serverless porque:

1. **Requiere Ollama**: El sistema necesita una instancia de Ollama ejecutándose localmente
2. **Sin Supabase**: La versión actual solo usa SQLite local para persistencia
3. **Arquitectura Local**: Diseñado específicamente para ejecución en máquinas locales

### ¿Por qué no Vercel?

- Ollama no puede ejecutarse en entornos serverless
- El filesystem de Vercel es de solo lectura (excepto /tmp que es efímero)
- El modelo de ejecución serverless no es compatible con servicios de AI locales

## 🐳 Despliegue con Docker (Experimental)

Aunque existe un Dockerfile, ten en cuenta que:

```bash
# Construir la imagen
docker build -t ama-intent .

# Ejecutar (requiere acceso a Ollama)
docker run -p 5001:5001 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v $(pwd)/data:/app/data \
  ama-intent
```

**Nota**: Ollama debe estar ejecutándose en el host y accesible desde el contenedor.

## 🔧 Configuración

### Variables de Entorno Esenciales

```bash
# Servidor
HOST=127.0.0.1        # Local only
PORT=5001             # Puerto del servidor

# Seguridad
AMA_SHARED_SECRET=tu-secreto-aqui  # Para autenticación

# Ollama
OLLAMA_MODEL=llama3.1  # Modelo a usar

# Memoria
MEMORY_CONTEXT_LIMIT=5     # Contexto reciente
MEMORY_MAX_ENTRIES=1000    # Máximo de entradas
MEMORY_ARCHIVE_DAYS=30     # Días antes de archivar
```

## 📊 Base de Datos

El sistema usa **SQLite** para persistencia local:
- Ubicación: `data/ama_memory.db`
- Automáticamente creado en el primer inicio
- Backups recomendados de la carpeta `data/`

## 🚀 Producción Local

Para ejecutar en producción local:

```bash
# 1. Configurar secreto fuerte
export AMA_SHARED_SECRET=$(openssl rand -hex 32)

# 2. Ejecutar sin auto-reload
export RELOAD=false

# 3. Iniciar
python start.py
```

## 🔐 Seguridad

- ✅ El servidor se ejecuta en `127.0.0.1` por defecto (solo accesible localmente)
- ✅ Usa `AMA_SHARED_SECRET` para proteger endpoints sensibles
- ✅ Los datos se almacenan localmente en SQLite
- ❌ NO exponer el puerto 5001 a internet sin autenticación adicional

## 📝 Notas

- Este proyecto prioriza simplicidad y ejecución local
- No hay planes actuales para soportar despliegue serverless
- Para uso empresarial, considera ejecutar en un servidor dedicado

## 🆘 Soporte

Para problemas con el despliegue, abre un issue en GitHub describiendo:
- Sistema operativo
- Versión de Python
- Versión de Ollama
- Logs de error completos
