# FILE: docker/backup/verify_backup.py
# =============================================================================
#!/usr/bin/env python3
"""
Script de verificación de backups
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import shutil

from backup_script import BackupManager, DatabaseBackup, logger


def main():
    manager = BackupManager()
    backups = manager.list_backups()

    if not backups:
        logger.error("❌ No backups to verify")
        sys.exit(1)

    latest = backups[0]
    logger.info(f"🔍 Verifying: {latest['name']}")

    # Extraer y verificar
    temp_dir = Path("/tmp/verify_backup")
    temp_dir.mkdir(exist_ok=True)

    try:
        shutil.unpack_archive(latest["path"], temp_dir)

        extracted_dir = list(temp_dir.iterdir())[0]
        db_path = extracted_dir / "ama_dashboard.db"

        is_valid, message = DatabaseBackup.verify_backup(db_path)

        if is_valid:
            logger.info(f"✅ Verification passed: {message}")

            # Verificar stats
            stats = DatabaseBackup.get_db_stats(db_path)
            logger.info(f"   Tables: {stats.get('table_count', 0)}")
            logger.info(f"   Size: {stats.get('db_size', 0) / 1024 / 1024:.2f} MB")

            sys.exit(0)
        else:
            logger.error(f"❌ Verification failed: {message}")
            sys.exit(1)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
