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
