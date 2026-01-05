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
