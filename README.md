# AMA-Intent v2.0: Sistema de Cerebro Artificial Biomimético

## 🧠 Visión General del Proyecto

**AMA-Intent** es un sistema de inteligencia artificial biomimética diseñado para la orquestación de tareas complejas, utilizando una arquitectura cognitiva modular basada en **Motores Qodeia** [1]. La versión 2.0 introduce una capa de aplicación crítica: el **AMA-Intent Personal Dashboard**, una interfaz web robusta y segura para la productividad personal y el desarrollo de proyectos.

El sistema se divide en tres componentes principales:
1.  **Core Cognitivo**: La infraestructura de IA que gestiona la memoria, la decisión y la gobernanza.
2.  **Personal Dashboard**: La interfaz de usuario que expone las capacidades de IA a través de herramientas prácticas de desarrollo y contenido.
3.  **MiniMax Multimodal Integration**: Una nueva capa de servicios que dota al sistema de capacidades de voz, generación de imágenes y notificaciones inteligentes.

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
| **Credential Manager** | Panel de gestión segura de claves API para servicios externos (OpenAI, Anthropic, Google, etc.). | Almacenamiento cifrado y centralizado de credenciales de IA. |

## 🎙️ Integración MiniMax: Capacidades Multimodales (Dashboard v2.1)

AMA-Intent ahora cuenta con una integración profunda con **MiniMax**, permitiendo una interacción más rica y humana a través de múltiples canales en el Dashboard v2.1.

### 🛠️ Servicios MiniMax Implementados

*   **AudioService**: Síntesis de voz de alta fidelidad (Español/Inglés). Permite la lectura de resultados de análisis, guías de voz y **resúmenes de actividad de GitHub**.
*   **ImageService**: Generación dinámica de imágenes, diagramas de arquitectura e **informes visuales de productividad**.
*   **NotificationService**: Sistema de alertas multimodales que combina texto, audio emocional e iconos visuales, ahora con **persistencia en base de datos**.
*   **Analytics Manager**: Nuevo módulo que genera informes de productividad automáticos con soporte visual y de voz.

### 🔌 Plugins Potenciados con MiniMax

*   **Voice Assistant (Nuevo)**: Un asistente de voz completo que puede leer tareas, resultados de código y proporcionar notificaciones audibles.
*   **Wellness Assistant v2.0**: Ahora incluye **pausas guiadas por voz** y sesiones de meditación, mejorando significativamente la experiencia de bienestar del desarrollador.

## 🚀 Integración Kimi K2: Capacidades Avanzadas de IA

Inspirado en las innovaciones de Kimi K2, AMA-Intent incorpora componentes de vanguardia para mejorar su rendimiento y estabilidad.

| Componente | Descripción | Beneficio Principal |
| :--- | :--- | :--- |
| **MuonClip Optimizer** | Un optimizador de entrenamiento que previene *loss spikes* y estabiliza la convergencia. | Entrenamiento de *Reward Models* estable y hasta un 15% más rápido. |
| **Long Horizon Agent** | Agente capaz de mantener el enfoque en tareas de hasta 300 pasos de ejecución. | Resolución de problemas complejos de arquitectura completa. |
| **Agentic Data Synthesizer** | Sistema que genera datos de entrenamiento sintéticos y verificables (RLVR). | Creación de datasets de alta calidad a gran escala. |
| **Context Caching + MLA** | Cacheo de prefijos de contexto y arquitectura de atención latente (MLA). | Reducción de hasta un 90% en costos de API y latencia. |

## 🔐 Integración SDDCS-Kaprekar: Seguridad y Sincronización

AMA-Intent v2.0 incorpora el **protocolo SDDCS-Kaprekar** para una validación y sincronización ultra-eficiente.

| Componente | Descripción | Beneficio Principal |
| :--- | :--- | :--- |
| **Agent State Sync** | Sincronización de estado con checkpoints de 4 bytes. | Validación ligera y eficiente del estado del agente. |
| **Context Cache Validation** | Integridad de contextos mediante fingerprints SDDCS. | Detección inmediata de corrupción de datos. |
| **JWT with Rolling Seeds** | Autenticación JWT con semillas rotativas basadas en Kaprekar. | Tokens de sesión dinámicos y más seguros. |

---

## 🛠️ Instalación y Uso

### 1. Clonar e Instalar

```bash
git clone https://github.com/dgr198213-ui/proyecto-ama-intent.git
cd proyecto-ama-intent
# Instalación recomendada en modo editable
pip install -e .
```

### 2. Configuración Inicial

```bash
cp .env.example .env
python3 scripts/migrate_and_upgrade.py
python3 scripts/migrate_credentials.py
```

### 3. Iniciar el Dashboard

```bash
python3 ama_personal_dashboard.py
```

Accede en **http://localhost:8000** (Admin: `admin` / `admin123`).

### 🧪 Ejecutar Pruebas y Demos

```bash
# Ejecutar suite de pruebas completa
pytest tests/

# Probar integración MiniMax básica
python3 demo_minimax_integration.py

# Probar integración Dashboard v2.1 + MiniMax
python3 test_dashboard_minimax_integration.py
```

## 📦 Estructura del Proyecto

```
proyecto-ama-intent/
├── minimax_integration/      # 🎙️ Nuevo: Servicios de Audio, Imagen y Notificaciones
├── agents/                   # 🧠 Agentes autónomos (Long Horizon Agent)
├── cortex/                   # 💡 Core cognitivo y modelos de atención
├── plugins/                  # 🧩 Plugins (Voice Assistant, Wellness v2.0)
├── src/                      # 📦 Código fuente principal
├── tests/                    # 🧪 Suite de pruebas unitarias e integración
├── demo_minimax_integration.py # 🚀 Demo de capacidades multimodales
└── setup.py                  # ⚙️ Configuración de instalación y dependencias
```

## 📚 Documentación Adicional

- **RESUMEN_MEJORAS_MINIMAX.md**: Impacto y detalles de la integración multimodal.
- **docs/MINIMAX_INTEGRATION.md**: Guía técnica de los servicios MiniMax.
- **docs/SDDCS_FORMULATION.md**: Formulación matemática del sistema.
- **DASHBOARD_README.md**: Guía completa del Personal Dashboard.

## 📞 Soporte y Contribución

Este proyecto es parte de la iniciativa AMA-Intent. Para reportar problemas o contribuir, consulte la documentación interna.

## Referencias

[1] AMA-Intent v2.0: Sistema de Cerebro Artificial Biomimético (Documentación Interna).
[2] Reporte de Actualización - AMA-Intent Personal Dashboard v2 (Documento Interno).
