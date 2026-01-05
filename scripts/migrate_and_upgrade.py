#!/usr/bin/env python3
"""
Script de migración y actualización para AMA-Intent Personal Dashboard v2
"""

import os
import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_dashboard.database import DatabaseManager, create_admin_user

def main():
    print("🚀 Iniciando actualización a AMA-Intent Personal Dashboard v2...")
    
    # 1. Inicializar base de datos
    db_manager = DatabaseManager()
    db_manager.init_db()
    
    # 2. Crear usuario admin por defecto
    session = db_manager.get_session()
    admin = create_admin_user(session)
    print(f"👤 Usuario admin verificado: {admin.username}")
    
    # 3. Intentar migrar datos antiguos si existen
    json_data = Path(__file__).parent.parent / "data" / "personal" / "projects.json"
    if json_data.exists():
        print(f"📂 Detectados datos antiguos en {json_data}. Migrando...")
        db_manager.migrate_from_json(str(json_data))
    
    session.close()
    print("\n✅ Actualización completada exitosamente.")
    print("💡 Puedes iniciar el dashboard con: python3 ama_personal_dashboard.py")

if __name__ == "__main__":
    main()
