# Knowledge Graph Plugin para AMA-Intent

## Descripción

Plugin avanzado que construye un **Knowledge Graph semántico** del código del proyecto y proporciona capacidades de **GraphRAG** (Retrieval-Augmented Generation) para análisis profundo.

## Características Principales

### 🔍 Construcción Automática de KG
- **Análisis AST completo** de código Python
- Extracción de entidades: módulos, clases, funciones, métodos
- Detección de relaciones: imports, calls, herencia, decoradores
- **Detección de patrones de diseño**: Singleton, Factory, Observer, Decorator

### 🧠 GraphRAG Inteligente
- Responde preguntas sobre el código usando contexto del grafo
- Clasificación automática de queries (what_is, how_works, dependencies, impact)
- Retrieval de subgrafos relevantes
- Generación de respuestas con LLM contextualizado

### 🔗 Integración con AMA-Intent Core
- **CorticalAttention**: Prioriza contexto relevante
- **DMD**: Selecciona mejores acciones de refactorización
- **AMAGAuditor**: Valida respuestas y sugerencias

### 📊 Análisis Avanzados
- Análisis de impacto de cambios
- Detección de dependencias circulares
- Métricas de acoplamiento y complejidad
- Sugerencias de refactorización automáticas

## Estructura del Plugin

```
plugins/knowledge_graph/
├── plugin.json                 # Configuración del plugin
├── __init__.py
├── project_kg.py              # Constructor del KG
├── graphrag.py                # Sistema GraphRAG
├── orchestrator.py            # Orquestador principal
├── api.py                     # Endpoints HTTP
├── widgets/
│   ├── kg_visualizer.tsx      # Visualización del grafo
│   └── query_interface.tsx    # Interfaz de queries
└── tests/
    ├── test_kg_builder.py
    └── test_graphrag.py
```

## Instalación

### 1. Dependencias

```bash
pip install networkx rdflib gitpython
```

### 2. Configuración
El plugin se configura a través del archivo `plugin.json` o mediante la interfaz del Dashboard. Los parámetros principales incluyen:
- `project_path`: Directorio raíz del proyecto a analizar.
- `file_patterns`: Lista de extensiones a incluir (por defecto `["**/*.py"]`).
- `max_query_depth`: Profundidad de búsqueda en el grafo para respuestas GraphRAG.

### 3. Uso de la API
El plugin expone varios endpoints para interactuar con el grafo:
- `POST /api/v1/kg/query`: Realiza una consulta semántica al grafo.
- `POST /api/v1/kg/rebuild`: Fuerza la reconstrucción del grafo de conocimiento.
- `GET /api/v1/kg/overview`: Obtiene estadísticas del proyecto analizado.

### 4. Integración con AMA-Intent
Cuando `use_ama_core` está habilitado, el plugin utiliza el motor de atención del core para priorizar nodos del grafo que son más relevantes para la intención actual (I₀).
