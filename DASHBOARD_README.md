# AMA-Intent Personal Dashboard v2

## Descripción

El **Personal Dashboard v2** es una evolución significativa del sistema de herramientas de desarrollo personal de AMA-Intent. Esta versión introduce persistencia de datos robusta, seguridad mediante autenticación JWT y una arquitectura preparada para integraciones externas.

## Nuevas Características v2

### 1. Persistencia con SQLite
- Migración de almacenamiento JSON a base de datos relacional SQLite.
- Modelos de datos para Usuarios, Proyectos, Sesiones de Debug y Entradas de Contenido.
- Sistema de backups automáticos y migración de datos antiguos.

### 2. Seguridad y Autenticación
- Sistema de login basado en JWT (JSON Web Tokens).
- Hashing de contraseñas con bcrypt.
- Gestión de sesiones mediante cookies seguras.
- Middleware de protección de rutas.

### 3. Arquitectura Modular Extendida
- **Integrations**: Conectores para GitHub y AMA-Intent Core.
- **Analytics**: Seguimiento de métricas de productividad y uso.
- **Plugins**: Sistema de carga dinámica de funcionalidades adicionales.
- **Multilingual**: Soporte extendido para múltiples lenguajes de programación.

## Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements_dashboard.txt
```

### 2. Configurar entorno

Copia el archivo `.env.example` a `.env` y ajusta las claves secretas.

```bash
cp .env.example .env
```

### 3. Ejecutar migración inicial

Este paso creará la base de datos y el usuario administrador por defecto.

```bash
python3 scripts/migrate_and_upgrade.py
```

### 4. Iniciar el servidor

```bash
python3 ama_personal_dashboard.py
```

## Credenciales por Defecto
- **Usuario**: `admin`
- **Contraseña**: `admin123`

## Estructura de Archivos v2

```
proyecto-ama-intent/
├── src/
│   ├── personal_dashboard/
│   │   ├── database.py         # Gestión de SQLAlchemy y modelos
│   │   ├── auth.py             # Lógica de JWT y seguridad
│   │   ├── web_ui.py           # Servidor FastAPI v2
│   │   └── integrations/       # Conectores externos
│   ├── code_companion/         # Herramientas de código
│   └── content_creator/        # Herramientas de contenido
├── templates/                  # Templates Jinja2 (Login, Dashboard, etc.)
├── static/                     # Archivos estáticos (JS, CSS)
├── data/                       # Base de datos SQLite
├── scripts/                    # Scripts de utilidad y migración
└── ama_personal_dashboard.py   # Punto de entrada principal
```

## Próximos Pasos
1. Implementar el panel de Analytics completo.
2. Finalizar los conectores de integración con GitHub.
3. Expandir el soporte multilenguaje en el Debug Assistant.

## Actualización v2.1: Ecosistema de Plugins e Integraciones

### 🔌 Sistema de Plugins
El Dashboard ahora soporta la carga dinámica de plugins. Puedes extender las capacidades del sistema sin modificar el núcleo.
- **Ubicación**: Carpeta `plugins/`
- **Estructura**: Cada plugin debe tener un `plugin.json` y un punto de entrada en Python.
- **API**: Los plugins pueden acceder a servicios de base de datos, analíticas y herramientas de IA.

### 🐙 Integración con GitHub
Conector inicial para sincronizar proyectos y automatizar flujos de trabajo con repositorios de GitHub.
- **Configuración**: Requiere `GITHUB_TOKEN` en el archivo `.env`.
- **Funciones**: Listado de repositorios, gestión de eventos y sincronización de código.

### 🔔 Sistema de Notificaciones (Beta)
Base para notificaciones en tiempo real dentro del dashboard para eventos del sistema y tareas completadas.

## Actualización v2.2: Preparación para Producción y Dockerización

### 🐳 Dockerización
El sistema ahora está completamente preparado para ser desplegado mediante contenedores.
- **Dockerfile.production**: Imagen optimizada basada en Python 3.11-slim.
- **Docker Compose**: Orquestación completa que incluye la aplicación, base de datos PostgreSQL, cache Redis y proxy inverso Nginx.

### 🔐 Seguridad de Producción
Se han incluido herramientas para garantizar un despliegue seguro:
- **setup_production.py**: Script interactivo para generar secretos, configurar DB y asegurar el entorno.
- **Nginx Proxy**: Configuración con headers de seguridad, SSL/TLS y optimización de archivos estáticos.

### 💾 Gestión de Backups
Nuevo sistema de respaldo y recuperación:
- **backup_manager.sh**: Script para realizar copias de seguridad de la base de datos y archivos críticos.
- **Automatización**: Preparado para ser ejecutado mediante tareas programadas (cron).

## Despliegue en Producción

1. Ejecutar el script de configuración:
   ```bash
   python3 scripts/setup_production.py
   ```
2. Iniciar con Docker Compose:
   ```bash
   docker-compose -f docker-compose.production.yml up -d
   ```
