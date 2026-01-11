#!/usr/bin/env python3
"""
Script de configuración inicial para AMA-Intent v2.0
Ejecutar solo la primera vez para configurar seguridad básica
"""

import getpass
import os
import secrets
from pathlib import Path

import bcrypt


def generate_secret_key():
    """Genera una SECRET_KEY segura para JWT"""
    return secrets.token_urlsafe(32)


def create_env_file():
    """Crea el archivo .env con valores seguros"""
    env_path = Path(".env")

    if env_path.exists():
        overwrite = input("⚠️  .env ya existe. ¿Sobrescribir? (s/N): ").lower()
        if overwrite != "s":
            print("❌ Configuración cancelada")
            return False

    secret_key = generate_secret_key()

    env_content = f"""# AMA-Intent v2.0 - Configuración
# Generado automáticamente - NO COMPARTIR

# Seguridad
SECRET_KEY={secret_key}
JWT_SECRET_KEY={generate_secret_key()}

# Base de datos
DATABASE_PATH=data/ama_intent.db
BACKUP_PATH=data/backups

# Dashboard
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=8000
DEBUG_MODE=False

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/ama_intent.log
"""

    env_path.write_text(env_content)
    print(f"✅ Archivo .env creado con SECRET_KEY segura")
    return True


def setup_admin_password():
    """Solicita y configura la contraseña de administrador"""
    print("\n🔐 Configuración de Contraseña de Administrador")
    print("=" * 50)

    while True:
        password = getpass.getpass("Nueva contraseña para 'admin': ")

        if len(password) < 8:
            print("❌ La contraseña debe tener al menos 8 caracteres")
            continue

        password_confirm = getpass.getpass("Confirmar contraseña: ")

        if password != password_confirm:
            print("❌ Las contraseñas no coinciden")
            continue

        break

    # Hashear contraseña
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    # Guardar en archivo temporal para que migrate_and_upgrade.py lo use
    password_file = Path("data/.admin_password_hash")
    password_file.parent.mkdir(exist_ok=True)
    password_file.write_bytes(hashed)

    print("✅ Contraseña configurada correctamente")
    return True


def create_directories():
    """Crea las carpetas necesarias"""
    directories = ["data", "data/backups", "logs", "static", "templates"]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    print("✅ Directorios creados")


def create_gitignore():
    """Actualiza .gitignore para proteger datos sensibles"""
    gitignore_content = """# AMA-Intent v2.0 - Archivos a ignorar

# Seguridad
.env
*.key
*.pem

# Base de datos
data/*.db
data/*.db-journal
data/.admin_password_hash

# Backups
data/backups/*
!data/backups/.gitkeep

# Logs
logs/*
!logs/.gitkeep

# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""

    Path(".gitignore").write_text(gitignore_content)
    print("✅ .gitignore actualizado")


def create_gitkeep_files():
    """Crea archivos .gitkeep para mantener estructura de carpetas"""
    paths = ["data/backups/.gitkeep", "logs/.gitkeep"]
    for path in paths:
        Path(path).touch()


def main():
    print("=" * 60)
    print("🚀 AMA-Intent v2.0 - Configuración Inicial")
    print("=" * 60)

    print("\nEste script configurará:")
    print("  • Claves de seguridad")
    print("  • Contraseña de administrador")
    print("  • Estructura de directorios")
    print("  • Protección de archivos sensibles")

    input("\nPresiona ENTER para continuar...")

    # Ejecutar pasos
    print("\n📁 Creando directorios...")
    create_directories()

    print("\n🔑 Generando configuración de seguridad...")
    if not create_env_file():
        return

    print("\n🔐 Configurando credenciales...")
    if not setup_admin_password():
        return

    print("\n🛡️  Actualizando .gitignore...")
    create_gitignore()
    create_gitkeep_files()

    print("\n" + "=" * 60)
    print("✅ Configuración inicial completada")
    print("=" * 60)
    print("\n📝 Próximos pasos:")
    print("  1. Ejecutar: python3 scripts/migrate_and_upgrade.py")
    print("  2. Iniciar dashboard: python3 ama_personal_dashboard.py")
    print("  3. Acceder a: http://localhost:8000")
    print("\n⚠️  IMPORTANTE: No compartas el archivo .env con nadie")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Configuración cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante la configuración: {e}")
