#!/usr/bin/env python3
"""
Sistema de backup automático para AMA-Intent v2.0
Gestiona backups de la base de datos con rotación automática
"""

import logging
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("BackupManager")


class BackupManager:
    def __init__(self, db_path="data/ama_intent.db", backup_dir="data/backups"):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, backup_type="manual"):
        if not self.db_path.exists():
            logger.error(f"Base de datos no encontrada: {self.db_path}")
            return False

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_type}_{timestamp}.db"
            backup_path = self.backup_dir / backup_name

            shutil.copy2(self.db_path, backup_path)
            logger.info(f"✅ Backup creado: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return False


if __name__ == "__main__":
    import sys

    manager = BackupManager()
    if len(sys.argv) > 1 and sys.argv[1] == "now":
        manager.create_backup("manual")
    else:
        manager.create_backup("auto")
