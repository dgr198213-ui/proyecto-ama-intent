# AMA-Intent v2.0: Sistema de Cerebro Artificial Biomimético

## 🧠 Visión General del Proyecto

**AMA-Intent** es un sistema de inteligencia artificial biomimética diseñado para la orquestación de tareas complejas, utilizando una arquitectura cognitiva modular basada en **Motores Qodeia** [1]. La versión 2.0 introduce una capa de aplicación crítica: el **AMA-Intent Personal Dashboard**, una interfaz web robusta y segura para la productividad personal y el desarrollo de proyectos.

El sistema se divide en dos componentes principales:
1.  **Core Cognitivo**: La infraestructura de IA que gestiona la memoria, la decisión y la gobernanza.
2.  **Personal Dashboard**: La interfaz de usuario que expone las capacidades de IA a través de herramientas prácticas de desarrollo y contenido.

## 🚀 AMA-Intent Personal Dashboard v2.0

El Dashboard v2.0 representa una actualización fundamental, enfocada en la persistencia de datos, la seguridad y la extensibilidad.

### 🔑 Características Destacadas de la v2.0

| Característica | Descripción | Beneficio |
| :--- | :--- | :--- |
| **Persistencia con SQLite** | Migración de datos de configuración y usuario de JSON a una base de datos relacional (SQLAlchemy + SQLite). | Mayor integridad, escalabilidad y gestión de datos multiusuario. |
| **Autenticación JWT** | Implementación de un sistema de login seguro basado en JWT y bcrypt para el hashing de contraseñas. | Protección de acceso y aislamiento de datos por usuario. |
| **AMA Terminal** | Consola interactiva integrada con comandos preestablecidos (`status`, `plugins`, `analyze`, `todo`, `backup`). | Control rápido del sistema y ejecución de tareas sin salir de la interfaz. |
| **Sistema de Plugins** | Arquitectura extensible que permite añadir nuevas funcionalidades dinámicamente. | Personalización total según las necesidades del usuario. |
| **Code Companion** | Módulos de asistencia de código para *debugging*, análisis de calidad y generación de tests unitarios. | Aumento de la productividad y reducción del tiempo de *debugging*. |
| **Content Creator** | Herramientas para la generación de borradores de blog, optimización SEO y adaptación a redes sociales. | Automatización del flujo de trabajo de creación de contenido. |
| **Knowledge Graph & GraphRAG** | Construcción de grafos de conocimiento del código y sistema de consultas inteligentes. | Análisis profundo de arquitectura y dependencias mediante lenguaje natural. |

### 🔌 Plugins Incluidos (v2.0)

*   **Productivity Tracker**: Monitorea el tiempo dedicado a proyectos y sugiere optimizaciones de flujo de trabajo.
*   **Code Quality Analyzer**: Analiza la complejidad ciclomática y adherencia a PEP8 en proyectos Python.
*   **Wellness Assistant**: Asistente de bienestar que sugiere pausas activas y ejercicios de ergonomía.
*   **Knowledge Graph & GraphRAG**: Construye un grafo semántico del proyecto y permite realizar consultas complejas sobre la estructura del código usando IA contextualizada.

## 🚀 Integración Kimi K2: Capacidades Avanzadas de IA

Inspirado en las innovaciones de Kimi K2, AMA-Intent ahora incorpora un conjunto de componentes de vanguardia para mejorar radicalmente su rendimiento, estabilidad y capacidades de razonamiento a largo plazo.

| Componente | Descripción | Beneficio Principal |
| :--- | :--- | :--- |
| **MuonClip Optimizer** | Un optimizador de entrenamiento que previene *loss spikes* y estabiliza la convergencia de modelos. | Entrenamiento de *Reward Models* 100% estable y hasta un 15% más rápido. |
| **Long Horizon Agent** | Agente capaz de mantener la coherencia y el enfoque en tareas de hasta 300 pasos de ejecución. | Resolución de problemas complejos que antes eran inabordables (e.g., análisis de proyectos completos). |
| **Agentic Data Synthesizer** | Sistema que genera datos de entrenamiento sintéticos y verificables para *Reward Models* (RLVR). | Creación de datasets de alta calidad a gran escala, reduciendo la dependencia de datos humanos. |
| **Context Caching + MLA** | Un sistema de cacheo de prefijos de contexto y una arquitectura de atención latente (MLA). | Reducción de hasta un 90% en costos de API y latencia, permitiendo el uso de contextos de 256K tokens. |

Estos componentes trabajan en sinergia para llevar las capacidades de AMA-Intent a un nuevo nivel de eficiencia y autonomía.

---

## 🛠️ Instalación y Uso

Para poner en marcha el sistema, se recomienda seguir los siguientes pasos:

### 1. Clonar el Repositorio

```bash
git clone https://github.com/dgr198213-ui/proyecto-ama-intent.git
cd proyecto-ama-intent
```

### 2. Instalar Dependencias

El Dashboard v2.0 requiere dependencias adicionales para la base de datos y la autenticación.

```bash
# Instalar dependencias del Dashboard
pip install -r requirements_dashboard.txt
```

### 3. Configuración Inicial

Crea el archivo de configuración de entorno y ejecuta el script de migración.

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Ejecutar la migración para crear la base de datos y el usuario admin
python3 scripts/migrate_and_upgrade.py
```

### 4. Iniciar el Dashboard

El servidor web se iniciará en el puerto 8000.

```bash
python3 ama_personal_dashboard.py
```

El Dashboard estará accesible en **http://localhost:8000**.

### Credenciales por Defecto

| Rol | Usuario | Contraseña |
| :--- | :--- | :--- |
| **Administrador** | `admin` | `admin123` |

## 📦 Estructura del Proyecto

La estructura del proyecto ha sido consolidada para separar el Core Cognitivo de la capa de Aplicación (Dashboard).

```
proyecto-ama-intent/
├── agents/                  # 🧠 Agentes autónomos (Nuevo: Long Horizon Agent)
│   └── long_horizon/
├── cortex/                  # 💡 Core cognitivo y modelos de atención (Mejorado con MLA)
│   └── attention/
├── data/                    # 💾 Gestión de datos (Nuevo: Síntesis de datos agenticos)
│   └── synthesis/
├── llm/                     # 🔌 Conectores a LLMs (Nuevo: Caching de contexto)
│   └── connector/
├── training/                # 🏋️ Módulos de entrenamiento (Nuevo: MuonClip Optimizer)
│   └── optimizers/
├── plugins/                 # 🧩 Plugins del Dashboard
├── src/                     # 📦 Código fuente principal de la aplicación
├── templates/               # 📄 Templates HTML para el Dashboard
├── static/                  # 🎨 Archivos estáticos (CSS, JS)
├── scripts/                 # ⚙️ Scripts de utilidad y migración
├── kimi_k2_integration.py   # 🚀 Punto de entrada de la nueva integración
├── examples_kimi_k2.py      # 📚 Ejemplos de uso de los nuevos componentes
└── README.md                # 📖 Este archivo
```

## 🧠 Fundamentos Teóricos: El Sistema SDDCS

El núcleo de AMA-Intent v2.0 implementa el **Sistema de Diccionario Dinámico de Compensación Estocástica (SDDCS)**, basado en principios de geometría diferencial y teoría de la información para garantizar la preservación de la información mutua ante el ruido.

Para más detalles, consulte:
- **docs/SDDCS_FORMULATION.md**: Formulación matemática completa del sistema.

## 📚 Documentación Adicional

Para una comprensión más profunda de los componentes, consulte los siguientes documentos:

- **DASHBOARD_README.md**: Guía completa de la arquitectura, módulos y uso del Personal Dashboard v2.0.
- **docs/API.md**: Documentación de los *endpoints* de la API RESTful.
- **docs/PLUGINS.md**: Guía para el desarrollo de *plugins* para el Dashboard.

## 📞 Soporte y Contribución

Este proyecto es parte de la iniciativa AMA-Intent. Para reportar problemas, sugerir mejoras o contribuir, por favor consulte la documentación interna.

## Referencias

[1] AMA-Intent v2.0: Sistema de Cerebro Artificial Biomimético (Documentación Interna del Core).
[2] Reporte de Actualización - AMA-Intent Personal Dashboard v2 (Documento Interno).
