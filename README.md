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
| **Code Companion** | Módulos de asistencia de código para *debugging*, análisis de calidad y generación de tests unitarios. | Aumento de la productividad y reducción del tiempo de *debugging*. |
| **Content Creator** | Herramientas para la generación de borradores de blog, optimización SEO y adaptación a redes sociales. | Automatización del flujo de trabajo de creación de contenido. |
| **Arquitectura Modular** | Estructura preparada para la integración con el Core de AMA-Intent, sistemas de *plugins* y conectores externos (e.g., GitHub). | Extensibilidad y futuro crecimiento del sistema. |

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
├── qodeia_engines/          # Motores Qodeia (Core Cognitivo)
├── control/                 # Módulos de Control del Core
├── decision/                # Módulos de Decisión del Core
├── memory/                  # Módulos de Memoria del Core
├── src/                     # Código fuente principal
│   ├── code_companion/      # Módulos de asistencia de código
│   ├── content_creator/     # Módulos de creación de contenido
│   └── personal_dashboard/  # Módulos del Dashboard v2.0 (Auth, DB, Web UI)
├── templates/               # Templates HTML (Dashboard, Login, Debug, etc.)
├── static/                  # Archivos estáticos (CSS, JS)
├── data/                    # Base de datos SQLite y backups
├── scripts/                 # Scripts de migración y utilidad
├── ama_personal_dashboard.py# Punto de entrada del Dashboard
├── requirements_dashboard.txt # Dependencias del Dashboard
└── DASHBOARD_README.md      # Documentación detallada del Dashboard
```

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
