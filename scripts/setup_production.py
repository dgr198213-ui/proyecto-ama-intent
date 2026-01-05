```python
#!/usr/bin/env python3
"""
Script de configuración segura para producción
Autor: Manus IA
Fecha: Enero 2026
"""

import os
import sys
import secrets
import subprocess
import string
import json
from pathlib import Path
from cryptography.fernet import Fernet
import base64
import hashlib
import getpass

def print_header(text):
    """Imprime un encabezado"""
    print("\n" + "="*70)
    print(f" 🔐 {text}")
    print("="*70)

def generate_secure_random(length=64):
    """Genera una cadena segura aleatoria"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret():
    """Genera un secreto JWT seguro"""
    return secrets.token_urlsafe(64)

def generate_session_secret():
    """Genera un secreto de sesión seguro"""
    return secrets.token_urlsafe(32)

def generate_encryption_key():
    """Genera una clave de encriptación Fernet"""
    return Fernet.generate_key().decode()

def hash_password(password):
    """Genera hash de contraseña"""
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.b64encode(salt + key).decode()

def validate_github_token(token):
    """Valida formato básico de token de GitHub"""
    if not token:
        return False
    # Tokens de GitHub tienen prefijos específicos
    prefixes = ['ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_']
    return any(token.startswith(prefix) for prefix in prefixes)

def create_production_env():
    """Crea archivo .env para producción"""
    print_header("CONFIGURACIÓN DE ENTORNO DE PRODUCCIÓN")
    
    print("\n📝 Vamos a configurar las variables de entorno seguras...")
    
    env_config = {}
    
    # 1. Secreto JWT
    print("\n🔑 Generando JWT Secret...")
    jwt_secret = generate_jwt_secret()
    env_config['JWT_SECRET_KEY'] = jwt_secret
    print(f"   ✅ JWT Secret generado (64 caracteres)")
    
    # 2. Secreto de sesión
    print("\n🔑 Generando Session Secret...")
    session_secret = generate_session_secret()
    env_config['SESSION_SECRET'] = session_secret
    print(f"   ✅ Session Secret generado (32 caracteres)")
    
    # 3. GitHub Token
    print("\n🔑 Configuración de GitHub Token")
    print("   ℹ️  Necesario para integración con repositorios")
    print("   ℹ️  Obtén uno en: https://github.com/settings/tokens")
    print("   ℹ️  Requiere permisos: repo, read:user")
    
    github_token = input("\n   ¿Tienes un token de GitHub? (s/n): ").lower()
    if github_token == 's':
        token = getpass.getpass("   Ingresa tu GitHub Token (no se mostrará): ")
        if validate_github_token(token):
            env_config['GITHUB_TOKEN'] = token
            print("   ✅ Token de GitHub configurado")
        else:
            print("   ⚠️  Token no parece válido, omitiendo...")
    else:
        print("   ⚠️  Sin token de GitHub, integración limitada")
        env_config['GITHUB_TOKEN'] = ''
    
    # 4. Clave de encriptación
    print("\n🔑 Generando clave de encriptación...")
    encryption_key = generate_encryption_key()
    env_config['ENCRYPTION_KEY'] = encryption_key
    print(f"   ✅ Clave de encriptación generada")
    
    # 5. Configuración de base de datos
    print("\n🗄️  Configuración de base de datos")
    print("   ℹ️  Por defecto usaremos SQLite, pero puedes cambiar a PostgreSQL")
    
    db_choice = input("   ¿Usar PostgreSQL? (s/n): ").lower()
    if db_choice == 's':
        print("\n   Configuración PostgreSQL:")
        env_config['DB_ENGINE'] = 'postgresql'
        env_config['DB_HOST'] = input("   Host (default: localhost): ") or 'localhost'
        env_config['DB_PORT'] = input("   Port (default: 5432): ") or '5432'
        env_config['DB_NAME'] = input("   Database name: ") or 'ama_dashboard'
        env_config['DB_USER'] = input("   Username: ") or 'ama_user'
        env_config['DB_PASSWORD'] = getpass.getpass("   Password: ")
        env_config['DATABASE_URL'] = f"postgresql://{env_config['DB_USER']}:{env_config['DB_PASSWORD']}@{env_config['DB_HOST']}:{env_config['DB_PORT']}/{env_config['DB_NAME']}"
    else:
        env_config['DB_ENGINE'] = 'sqlite'
        env_config['DB_PATH'] = './data/production.db'
        env_config['DATABASE_URL'] = f"sqlite:///{env_config['DB_PATH']}"
    
    # 6. Configuración de Redis (opcional, para cache)
    print("\n🔴 Configuración de Redis (Cache)")
    print("   ℹ️  Recomendado para producción, mejora rendimiento")
    
    redis_choice = input("   ¿Usar Redis? (s/n): ").lower()
    if redis_choice == 's':
        env_config['REDIS_ENABLED'] = 'True'
        env_config['REDIS_HOST'] = input("   Redis Host (default: localhost): ") or 'localhost'
        env_config['REDIS_PORT'] = input("   Redis Port (default: 6379): ") or '6379'
        env_config['REDIS_PASSWORD'] = getpass.getpass("   Redis Password (opcional, enter para omitir): ") or ''
        env_config['REDIS_DB'] = input("   Redis DB (default: 0): ") or '0'
        print("   ✅ Redis configurado")
    else:
        env_config['REDIS_ENABLED'] = 'False'
        print("   ⚠️  Redis deshabilitado, usando cache en memoria")
    
    # 7. Configuración de seguridad
    print("\n🛡️  Configuración de seguridad avanzada")
    
    # CORS
    print("\n   Configuración CORS (Cross-Origin Resource Sharing)")
    cors_origins = input("   Orígenes permitidos (separados por coma, * para todos): ") or '*'
    env_config['CORS_ORIGINS'] = cors_origins
    
    # Rate limiting
    print("\n   Rate Limiting (límite de peticiones)")
    env_config['RATE_LIMIT_PER_MINUTE'] = input("   Peticiones por minuto por IP (default: 100): ") or '100'
    env_config['RATE_LIMIT_PER_HOUR'] = input("   Peticiones por hora por usuario (default: 1000): ") or '1000'
    
    # HTTPS/SSL
    print("\n   Configuración HTTPS")
    ssl_choice = input("   ¿Forzar HTTPS? (s/n): ").lower()
    env_config['FORCE_HTTPS'] = 'True' if ssl_choice == 's' else 'False'
    
    # 8. Configuración del servidor
    print("\n🚀 Configuración del servidor")
    
    env_config['HOST'] = input("   Host (default: 0.0.0.0): ") or '0.0.0.0'
    env_config['PORT'] = input("   Port (default: 8000): ") or '8000'
    
    workers = input("   Número de workers (default: 4): ") or '4'
    env_config['WORKERS'] = workers
    
    # 9. Configuración de logging
    print("\n📝 Configuración de logging")
    
    log_level = input("   Nivel de log (DEBUG, INFO, WARNING, ERROR): ") or 'INFO'
    env_config['LOG_LEVEL'] = log_level
    
    log_file = input("   Archivo de log (default: logs/ama_dashboard.log): ") or 'logs/ama_dashboard.log'
    env_config['LOG_FILE'] = log_file
    
    # 10. Configuración de AMA-Intent Core
    print("\n🧠 Configuración de AMA-Intent Core")
    
    core_url = input("   URL del Core (ej: http://localhost:8001): ") or 'http://localhost:8001'
    env_config['AMA_CORE_URL'] = core_url
    
    core_api_key = getpass.getpass("   API Key del Core (opcional, enter para omitir): ") or ''
    if core_api_key:
        env_config['AMA_CORE_API_KEY'] = core_api_key
    
    # Valores por defecto adicionales
    env_config.update({
        'ENVIRONMENT': 'production',
        'DEBUG': 'False',
        'RELOAD': 'False',
        'JWT_ALGORITHM': 'HS256',
        'ACCESS_TOKEN_EXPIRE_MINUTES': '30',
        'ENABLE_PLUGINS': 'True',
        'ENABLE_ANALYTICS': 'True',
        'EXPORT_ENABLED': 'True',
        'DARK_MODE_ENABLED': 'True',
        'DEFAULT_THEME': 'light',
        'SITE_NAME': 'AMA-Intent Dashboard',
        'SITE_DESCRIPTION': 'Herramientas personales de desarrollo y creación de contenido',
        'CONTACT_EMAIL': 'admin@ama-intent.com',
        'MAX_UPLOAD_SIZE': '10485760',  # 10MB
        'SESSION_TIMEOUT_MINUTES': '120',
        'PASSWORD_MIN_LENGTH': '12',
        'REQUIRE_EMAIL_VERIFICATION': 'False',
        'BACKUP_ENABLED': 'True',
        'BACKUP_SCHEDULE': '0 2 * * *',  # 2 AM daily
        'METRICS_ENABLED': 'True',
        'ALERTING_ENABLED': 'True',
    })
    
    # Crear archivo .env.production
    env_content = "# ============================================\n"
    env_content += "# AMA-Intent Dashboard v2 - PRODUCTION\n"
    env_content += "# Configuración segura - NO COMPARTIR\n"
    env_content += "# ============================================\n\n"
    
    for key, value in env_config.items():
        env_content += f"{key}={value}\n"
    
    env_file = ".env.production"
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print(f"\n✅ Archivo de configuración creado: {env_file}")
    
    # Crear versión segura sin valores sensibles para desarrollo
    safe_env = env_config.copy()
    for key in ['JWT_SECRET_KEY', 'SESSION_SECRET', 'ENCRYPTION_KEY', 
                'GITHUB_TOKEN', 'DB_PASSWORD', 'REDIS_PASSWORD', 
                'AMA_CORE_API_KEY']:
        if key in safe_env and safe_env[key]:
            safe_env[key] = '***SECRET***'
    
    safe_file = ".env.example.production"
    with open(safe_file, "w", encoding="utf-8") as f:
        f.write("# ============================================\n")
        f.write("# EJEMPLO de .env.production (valores seguros)\n")
        f.write("# ============================================\n\n")
        for key, value in safe_env.items():
            f.write(f"{key}={value}\n")
    
    print(f"📄 Ejemplo seguro creado: {safe_file}")
    
    return env_config
