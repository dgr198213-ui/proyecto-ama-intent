#!/usr/bin/env python3
"""
Health Check para AMA-Intent v2.0
Verifica el estado del sistema y detecta problemas
"""

import os
import sqlite3
import sys
from pathlib import Path


def check_system():
    print("🏥 Verificando salud del sistema...")

    # Verificar base de datos
    db_path = Path("data/ama_intent.db")
    if not db_path.exists():
        print("❌ Error: Base de datos no encontrada")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()

        if result[0] == "ok":
            print("✅ Integridad de base de datos: OK")
        else:
            print(f"❌ Error de integridad: {result[0]}")
            return False
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False

    # Verificar .env
    if not Path(".env").exists():
        print("❌ Error: Archivo .env no encontrado")
        return False
    print("✅ Archivo de configuración: OK")

    return True


if __name__ == "__main__":
    if check_system():
        sys.exit(0)
    else:
        sys.exit(1)
