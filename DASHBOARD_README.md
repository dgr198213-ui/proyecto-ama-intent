# AMA-Intent Personal Dashboard

## Descripción

El **Personal Dashboard** es una extensión del proyecto AMA-Intent que proporciona herramientas de desarrollo personal integradas en una interfaz web moderna.

## Componentes Integrados

### 1. Code Companion - Debug Assistant

Sistema de asistencia para debugging y análisis de código que incluye:

- **Debug Assistant** (`src/code_companion/debug_assistant.py`): Analiza errores de Python y sugiere soluciones
- **Code Explainer** (`src/code_companion/code_explainer.py`): Explica código complejo en lenguaje natural
- **Test Generator** (`src/code_companion/test_generator.py`): Genera tests unitarios automáticamente

**Características principales:**
- Análisis de tracebacks de Python con sugerencias de solución
- Detección de errores comunes (ModuleNotFoundError, ImportError, SyntaxError, etc.)
- Análisis de calidad de código (imports peligrosos, secretos hardcodeados, funciones largas)
- Generación de stubs de tests para pytest y unittest
- Reportes de debugging en formato Markdown

### 2. Content Creator

Suite de herramientas para creación de contenido:

- **Blog Writer** (`src/content_creator/blog_writer.py`): Generador de borradores de posts
- **SEO Optimizer** (`src/content_creator/seo_optimizer.py`): Optimización de contenido para SEO
- **Social Craft** (`src/content_creator/social_craft.py`): Creador de posts para redes sociales

**Características principales:**
- Generación de borradores con múltiples estilos (tutorial, opinión, listicle, how-to)
- Análisis de densidad de keywords
- Sugerencias de mejora SEO
- Adaptación de contenido para diferentes plataformas sociales (Twitter, LinkedIn, Facebook, Instagram)

### 3. Personal Dashboard

Interfaz web unificada construida con FastAPI:

- **Web UI** (`src/personal_dashboard/web_ui.py`): Servidor FastAPI con rutas y API
- **Templates HTML**: Interfaz responsive con Tailwind CSS

**Rutas disponibles:**
- `/` - Dashboard principal con overview de proyectos
- `/debug` - Interfaz del Debug Assistant
- `/content` - Interfaz del Content Creator
- `/projects` - Gestión de proyectos
- `/api/overview` - API endpoint para datos del dashboard

## Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements_dashboard.txt
```

### 2. Iniciar el servidor

```bash
python3 ama_personal_dashboard.py
```

El dashboard estará disponible en `http://localhost:8000`

## Estructura de Archivos

```
proyecto-ama-intent/
├── src/
│   ├── code_companion/
│   │   ├── __init__.py
│   │   ├── debug_assistant.py
│   │   ├── code_explainer.py
│   │   └── test_generator.py
│   ├── content_creator/
│   │   ├── __init__.py
│   │   ├── blog_writer.py
│   │   ├── seo_optimizer.py
│   │   └── social_craft.py
│   └── personal_dashboard/
│       ├── __init__.py
│       └── web_ui.py
├── templates/
│   ├── dashboard.html
│   ├── debug.html
│   └── projects.html
├── ama_personal_dashboard.py
├── requirements_dashboard.txt
└── DASHBOARD_README.md
```

## Uso

### Debug Assistant

**Analizar un error:**

```python
from src.code_companion.debug_assistant import DebugAssistant

assistant = DebugAssistant()
error_info = assistant.analyze_error(traceback_string)
print(error_info['quick_fix'])
```

**Analizar código:**

```python
analysis = assistant.analyze_code_snippet(code_string)
print(f"Issues found: {analysis['issues_found']}")
```

**Generar test:**

```python
test_code = assistant.generate_test_stub(function_code)
print(test_code)
```

### Content Creator

**Generar borrador de blog:**

```python
from src.content_creator.blog_writer import BlogWriter

writer = BlogWriter()
draft = writer.generate_draft("Python Best Practices", style="tutorial")
print(draft['content'])
```

**Optimizar para SEO:**

```python
from src.content_creator.seo_optimizer import SEOOptimizer

optimizer = SEOOptimizer()
analysis = optimizer.analyze_content(content, keywords=["python", "tutorial"])
print(analysis['suggestions'])
```

**Crear post social:**

```python
from src.content_creator.social_craft import SocialCraft

social = SocialCraft()
post = social.create_post("Check out my new blog post!", platform="twitter")
print(post['content'])
```

## Integración con AMA-Intent

Estos módulos están diseñados para integrarse con el sistema cognitivo existente de AMA-Intent. Pueden ser invocados desde el motor principal mediante operaciones específicas:

- `debug_analyze_error`: Analizar errores
- `debug_analyze_code`: Analizar calidad de código
- `debug_generate_test`: Generar tests
- `content_generate_blog`: Generar contenido de blog
- `content_optimize_seo`: Optimizar SEO
- `content_create_social`: Crear posts sociales

## Próximos Pasos

1. **Integración con LLM**: Conectar con modelos de lenguaje para mejorar explicaciones y sugerencias
2. **Persistencia de datos**: Implementar base de datos para guardar proyectos y análisis
3. **Autenticación**: Añadir sistema de usuarios si se despliega públicamente
4. **API REST completa**: Expandir endpoints para integración con otras herramientas
5. **Tests automatizados**: Añadir suite de tests para todos los módulos

## Licencia

Este proyecto es parte de AMA-Intent y sigue la misma licencia del proyecto principal.
