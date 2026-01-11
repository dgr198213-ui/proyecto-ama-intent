#!/usr/bin/env python3
"""
Script rápido para crear un backup manual
Uso: python3 scripts/backup_now.py
"""

import sys
from pathlib import Path

# Añadir directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.backup_manager import BackupManager


def main():
    print("💾 Creando backup manual...")
    print("-" * 50)

    manager = BackupManager()
    backup_path = manager.create_backup("manual")

    print("-" * 50)

    if backup_path:
        print(f"✅ Backup creado exitosamente:")
        print(f"   📁 {backup_path}")

        size_mb = backup_path.stat().st_size / (1024 * 1024)
        print(f"   📊 Tamaño: {size_mb:.2f} MB")

        # Mostrar lista de backups
        print("\n📦 Backups disponibles:")
        backups = manager.list_backups()
        for b in backups[-5:]:  # Mostrar últimos 5
            print(f"   • {b['name']} ({b['size_mb']} MB)")

        if len(backups) > 5:
            print(f"   ... y {len(backups) - 5} más")

        print(f"\n💡 Total de backups: {len(backups)}")
        return 0
    else:
        print("❌ Error al crear el backup")
        print("   Verifica los logs para más detalles")
        return 1


if __name__ == "__main__":
    sys.exit(main())
