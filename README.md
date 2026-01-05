# 🧠 Cerebro Artificial + IA Local Gobernada

## Guía Completa de Instalación y Uso

---

## 📋 Tabla de Contenidos

1. [Descripción del Sistema](#descripción)
2. [Requisitos](#requisitos)
3. [Instalación](#instalación)
4. [Configuración](#configuración)
5. [Uso Básico](#uso-básico)
6. [Comandos Avanzados](#comandos-avanzados)
7. [Estructura del Proyecto](#estructura)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Descripción del Sistema {#descripción}

Este sistema integra un **Cerebro Artificial biomimético** con **LLMs locales** (Ollama/LM Studio) para crear una IA completamente gobernada que:

✅ **Filtra y valida** cada entrada del usuario (AMA-G Fase 1)
✅ **Añade contexto de seguridad** sin modificar el prompt (Shadow Prompt)
✅ **Valida cada respuesta** contra la intención original (AMA-G Fase 3)
✅ **Aprende continuamente** de cada interacción
✅ **Consolida memoria** mediante ciclos de "sueño"
✅ **Se auto-regula** con homeostasis PID

### Arquitectura del Sistema

```
Usuario → AMA-Intent → Cerebro (Fase 1) → Shadow Prompt 
    ↓
Ollama/LM Studio (Generación)
    ↓
Cerebro (Fase 3 Validación) → Consolidación → Usuario
```

---

## 💻 Requisitos {#requisitos}

### Hardware Mínimo

- **RAM**: 8 GB (16 GB recomendado)
- **Almacenamiento**: 10 GB libres
- **GPU** (opcional): Acelera modelos locales

### Software

- **Python**: 3.8 o superior
- **Ollama** O **LM Studio**: Motor de IA local
- **Sistema Operativo**: Windows 10/11, macOS, Linux

---

## 📦 Instalación {#instalación}

### Paso 1: Instalar Python

**Windows:**
```bash
# Descargar desde python.org
# Marcar "Add Python to PATH" durante instalación
python --version  # Verificar
```

**macOS/Linux:**
```bash
# Python suele venir preinstalado
python3 --version
```

### Paso 2: Instalar Ollama O LM Studio

#### Opción A: Ollama (Recomendado)

**Windows/macOS/Linux:**
```bash
# Descargar desde https://ollama.ai
# Instalar ejecutable

# Verificar instalación
ollama --version

# Descargar modelo (ejemplo: Gemma 2B)
ollama pull gemma2:2b

# Otros modelos disponibles:
# ollama pull qwen2.5:3b
# ollama pull llama3.2:3b
# ollama pull mistral:7b
```

#### Opción B: LM Studio

1. Descargar desde: https://lmstudio.ai
2. Instalar aplicación
3. Descargar modelos desde la interfaz
4. Iniciar servidor local (puerto 1234 por defecto)

### Paso 3: Instalar Dependencias Python

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install numpy requests

# Opcional (mejora embeddings):
pip install sentence-transformers scikit-learn
```

### Paso 4: Descargar el Código del Cerebro

```bash
# Crear directorio del proyecto
mkdir cerebro_artificial
cd cerebro_artificial

# Copiar todos los archivos .py del proyecto:
# - sensing/kalman.py
# - cortex/attention.py
# - cortex/state.py
# - memory/episodic_graph.py
# - memory/semantic_matrix.py
# - memory/working_memory.py
# - memory/pruning.py
# - decision/q_value.py
# - decision/dmd.py
# - governance/amag_audit.py
# - control/pid_homeostasis.py
# - learning/loss.py
# - learning/stability.py
# - learning/consolidation.py
# - ama_intent.py
# - brain_complete.py
# - ollama_brain_interface.py
# - cli_interactive.py
```

---

## ⚙️ Configuración {#configuración}

### Configuración de Ollama

```bash
# Asegúrate de que Ollama esté ejecutándose
ollama serve  # Si no se inició automáticamente

# Verificar modelos instalados
ollama list

# El servidor corre en: http://localhost:11434
```

### Configuración de LM Studio

1. Abrir LM Studio
2. Ir a "Local Server"
3. Click en "Start Server"
4. Copiar la URL (normalmente `http://localhost:1234`)

### Variables de Entorno (Opcional)

```bash
# Windows (PowerShell):
$env:OLLAMA_HOST = "http://localhost:11434"

# macOS/Linux:
export OLLAMA_HOST="http://localhost:11434"
```

---

## 🚀 Uso Básico {#uso-básico}

### Iniciar el Sistema

```bash
# Activar entorno virtual (si lo creaste)
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Ejecutar CLI interactiva
python cli_interactive.py
```

### Primera Configuración

Al iniciar, el sistema te preguntará:

```
Configuración del LLM:
  Provider (ollama/lmstudio) [ollama]: ollama
  URL [http://localhost:11434]: [Enter para default]
  Modelo [gemma2:2b]: [Enter o escribe tu modelo]
  Temperature [0.7]: [Enter para default]
```

### Ejemplo de Conversación

```
🧑 Tú: ¿Qué es la inteligencia artificial?

[El sistema procesa...]

🤖 IA: La inteligencia artificial (IA) es...

   ⏱️  Tiempo: 3.45s
   ✓ Confianza: 0.82
```

### Comandos Especiales

Durante el chat, puedes usar:

```
/help      - Muestra ayuda
/stats     - Estadísticas del sistema
/config    - Muestra configuración
/sleep     - Fuerza consolidación
/history   - Historial de conversación
/export    - Exporta estadísticas a JSON
/exit      - Salir
```

---

## 🔧 Comandos Avanzados {#comandos-avanzados}

### Ver Estadísticas Detalladas

```
🧑 Tú: /stats

📊 ESTADÍSTICAS DEL SISTEMA

💬 Conversación:
  Total de mensajes: 15
  Tasa de aprobación: 93.3%

🧠 Cerebro:
  Ticks ejecutados: 30
  Episodios en memoria: 25
  Conceptos semánticos: 8
  Ciclos de sueño: 1

🛡️ Gobernanza (AMA-G):
  Auditorías totales: 30
  Tasa de aprobación: 90.0%
  Tasa de revisión: 6.7%
  Tasa de fallo: 3.3%
```

### Forzar Ciclo de Sueño

```
🧑 Tú: /sleep

💤 Iniciando ciclo de sueño forzado...

[FASE 1/4] NREM - Consolidación sistemática...
[FASE 2/4] REM - Procesamiento creativo...
[FASE 3/4] Reorganización de memoria...
[FASE 4/4] Homeostasis y preparación...

✅ Ciclo de sueño completado
  Episodios consolidados: 150
  Conceptos fusionados: 2
  Items podados: 5
```

### Exportar Datos

```
🧑 Tú: /export

✅ Estadísticas exportadas a: brain_stats_20250103_143022.json
```

---

## 📁 Estructura del Proyecto {#estructura}

```
cerebro_artificial/
│
├── sensing/
│   └── kalman.py              # Filtro talámico (Kalman)
│
├── cortex/
│   ├── attention.py           # Atención cortical (LSI)
│   └── state.py               # Estado latente
│
├── memory/
│   ├── episodic_graph.py      # Memoria episódica (PageRank)
│   ├── semantic_matrix.py     # Memoria semántica
│   ├── working_memory.py      # Working memory (PFC)
│   └── pruning.py             # Sistema de poda
│
├── decision/
│   ├── q_value.py             # Evaluación Q (MIEM)
│   └── dmd.py                 # Decisión matricial
│
├── governance/
│   └── amag_audit.py          # Auditor AMA-G
│
├── control/
│   └── pid_homeostasis.py     # Control PID homeostático
│
├── learning/
│   ├── loss.py                # Función de pérdida
│   ├── stability.py           # Control de estabilidad
│   └── consolidation.py       # Ciclo de sueño
│
├── ama_intent.py              # Extractor de intención
├── brain_complete.py          # Cerebro integrado
├── ollama_brain_interface.py # Interfaz con LLM
├── cli_interactive.py         # CLI interactiva
│
└── venv/                      # Entorno virtual
```

---

## 🔍 Troubleshooting {#troubleshooting}

### Problema: "No se puede conectar a Ollama"

**Solución:**
```bash
# Verificar que Ollama esté ejecutándose
ollama serve

# Verificar puerto
curl http://localhost:11434/api/tags

# Si usa otro puerto, especificarlo:
# En cli_interactive.py, cambiar base_url
```

### Problema: "Modelo no encontrado"

**Solución:**
```bash
# Listar modelos instalados
ollama list

# Descargar modelo necesario
ollama pull gemma2:2b
```

### Problema: "Out of Memory" o lentitud

**Solución:**
- Usar modelos más pequeños (2B-3B en lugar de 7B-13B)
- Reducir `max_episodes` y `max_concepts` en `brain_config`
- Cerrar otras aplicaciones

```python
# En cli_interactive.py, línea ~150:
brain_config = CompleteBrainConfig(
    max_episodes=500,      # Reducir de 1000
    max_concepts=100,      # Reducir de 200
    sleep_interval=100     # Aumentar intervalo
)
```

### Problema: "ModuleNotFoundError"

**Solución:**
```bash
# Asegurarse de estar en el entorno virtual
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstalar dependencias
pip install numpy requests
```

### Problema: Respuestas siempre bloqueadas

**Solución:**
- Revisar umbrales de AMA-G
- Ver logs de auditoría con `/stats`
- Ajustar `GovernanceThresholds`:

```python
# En ollama_brain_interface.py:
self.auditor = AMAGAuditor(
    thresholds=GovernanceThresholds(
        min_confidence=0.3,    # Reducir de 0.5
        max_surprise=5.0,      # Aumentar de 3.0
        max_risk=0.9           # Aumentar de 0.7
    )
)
```

---

## 📚 Recursos Adicionales

### Modelos Recomendados

| Modelo | Tamaño | RAM Requerida | Velocidad | Calidad |
|--------|--------|---------------|-----------|---------|
| gemma2:2b | 2B | 4 GB | ⚡⚡⚡ | ⭐⭐⭐ |
| qwen2.5:3b | 3B | 6 GB | ⚡⚡ | ⭐⭐⭐⭐ |
| llama3.2:3b | 3B | 6 GB | ⚡⚡ | ⭐⭐⭐⭐ |
| mistral:7b | 7B | 12 GB | ⚡ | ⭐⭐⭐⭐⭐ |

### Enlaces Útiles

- **Ollama**: https://ollama.ai
- **LM Studio**: https://lmstudio.ai
- **Modelos disponibles**: https://ollama.ai/library

---

## 🎓 Próximos Pasos

1. ✅ **Instalar y probar** el sistema básico
2. ✅ **Experimentar** con diferentes modelos
3. ✅ **Ajustar parámetros** de gobernanza según necesidad
4. 🔜 **Personalizar** para casos de uso específicos
5. 🔜 **Integrar** con otras aplicaciones

---

## 📝 Notas de Versión

**v1.0.0** - Versión inicial completa
- FASE 1: Percepción + Decisión + Gobernanza ✅
- FASE 2: Sistema de Memoria completo ✅
- FASE 3: Aprendizaje + Homeostasis ✅
- Integración con Ollama/LM Studio ✅
- CLI interactiva ✅

---

## 🤝 Soporte

¿Problemas o preguntas?
- Revisa la sección **Troubleshooting**
- Verifica que todos los módulos estén instalados correctamente
- Asegúrate de que Ollama/LM Studio esté ejecutándose

---

**¡Disfruta de tu IA local gobernada!** 🧠🚀