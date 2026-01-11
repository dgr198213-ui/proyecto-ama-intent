#!/usr/bin/env python3
"""
AMA-Intent Backup System
========================

Sistema completo de backup para AMA-Intent + SDDCS con:
- Backup de base de datos SQLite
- Backup de archivos de configuración
- Upload a S3 (opcional)
- Retención automática
- Verificación de integridad
- Restauración automatizada

Uso:
    python backup_script.py --manual
    python backup_script.py --auto
    python backup_script.py --verify
"""

import os
import sys
import sqlite3
import shutil
import gzip
import json
import hashlib
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess

# Intentar importar boto3 (AWS S3)
try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    print("⚠️  boto3 no instalado, backups S3 deshabilitados")

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

class BackupConfig:
    """Configuración centralizada del sistema de backup"""
    
    # Directorios
    APP_DIR = Path("/app")
    DATA_DIR = APP_DIR / "data"
    BACKUP_DIR = APP_DIR / "backups"
    LOGS_DIR = APP_DIR / "logs"
    
    # Base de datos
    DB_PATH = DATA_DIR / "ama_dashboard.db"
    
    # Archivos críticos
    CRITICAL_FILES = [
        DATA_DIR / "ama_dashboard.db",
        APP_DIR / ".env",
        APP_DIR / "config.json",
    ]
    
    # Directorios a incluir
    BACKUP_DIRS = [
        DATA_DIR,
        LOGS_DIR / "important",  # Solo logs importantes
    ]
    
    # S3 Configuration
    S3_BUCKET = os.getenv("BACKUP_S3_BUCKET", "ama-intent-backups")
    S3_PREFIX = os.getenv("BACKUP_S3_PREFIX", "production/")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    
    # Retención (días)
    RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
    RETENTION_WEEKS = 4  # Mantener 1 backup semanal
    RETENTION_MONTHS = 6  # Mantener 1 backup mensual
    
    # Compresión
    COMPRESSION_LEVEL = 9  # 0-9, 9 = máxima compresión
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=getattr(logging, BackupConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BackupConfig.LOGS_DIR / "backup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("AMA-Backup")


# ============================================================================
# UTILIDADES
# ============================================================================

def calculate_checksum(file_path: Path) -> str:
    """Calcula SHA-256 checksum de un archivo"""
    sha256 = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def get_db_size() -> int:
    """Obtiene el tamaño de la base de datos en bytes"""
    try:
        return BackupConfig.DB_PATH.stat().st_size
    except FileNotFoundError:
        return 0


def format_size(size_bytes: int) -> str:
    """Formatea tamaño en bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


# ============================================================================
# BACKUP DE BASE DE DATOS
# ============================================================================

class DatabaseBackup:
    """Maneja backups de la base de datos SQLite"""
    
    @staticmethod
    def backup_online(db_path: Path, backup_path: Path) -> bool:
        """
        Backup online de SQLite usando .backup() API
        No requiere detener la aplicación
        """
        logger.info(f"Iniciando backup online de {db_path}")
        
        try:
            # Conexión a DB source
            source_conn = sqlite3.connect(str(db_path))
            
            # Crear backup
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Usar API de backup (seguro durante escrituras)
            with backup_conn:
                source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            logger.info(f"✅ Backup online completado: {backup_path}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error en backup de DB: {e}")
            return False
    
    @staticmethod
    def verify_backup(backup_path: Path) -> Tuple[bool, str]:
        """
        Verifica integridad del backup
        Retorna: (is_valid, message)
        """
        try:
            # Intentar abrir la base de datos
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()
            
            # Verificar integridad con PRAGMA
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            
            if result == "ok":
                # Contar tablas como validación adicional
                cursor.execute(
                    "SELECT count(*) FROM sqlite_master WHERE type='table'"
                )
                table_count = cursor.fetchone()[0]
                
                conn.close()
                
                return True, f"Integridad OK, {table_count} tablas"
            else:
                conn.close()
                return False, f"Integridad fallida: {result}"
                
        except sqlite3.Error as e:
            return False, f"Error al verificar: {str(e)}"
    
    @staticmethod
    def get_db_stats(db_path: Path) -> Dict:
        """Obtiene estadísticas de la base de datos"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Contar tablas
            cursor.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table'"
            )
            table_count = cursor.fetchone()[0]
            
            # Tamaño de página
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            # Número de páginas
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            
            # Contar registros en tablas principales
            tables_info = {}
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            for (table_name,) in cursor.fetchall():
                if not table_name.startswith('sqlite_'):
                    cursor.execute(f"SELECT count(*) FROM {table_name}")
                    tables_info[table_name] = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'table_count': table_count,
                'page_size': page_size,
                'page_count': page_count,
                'db_size': page_size * page_count,
                'tables': tables_info
            }
            
        except sqlite3.Error as e:
            logger.error(f"Error obteniendo stats de DB: {e}")
            return {}


# ============================================================================
# GESTOR DE BACKUPS
# ============================================================================

class BackupManager:
    """Gestor principal del sistema de backups"""
    
    def __init__(self):
        self.config = BackupConfig
        self.s3_client = self._init_s3() if S3_AVAILABLE else None
        
        # Crear directorios si no existen
        self.config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _init_s3(self) -> Optional[boto3.client]:
        """Inicializa cliente S3"""
        try:
            client = boto3.client(
                's3',
                region_name=self.config.AWS_REGION,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            # Verificar acceso al bucket
            client.head_bucket(Bucket=self.config.S3_BUCKET)
            logger.info(f"✅ S3 configurado: {self.config.S3_BUCKET}")
            
            return client
            
        except Exception as e:
            logger.warning(f"⚠️  S3 no disponible: {e}")
            return None
    
    def create_backup(self, backup_type: str = "auto") -> Optional[Path]:
        """
        Crea un backup completo
        
        Args:
            backup_type: "auto", "manual", "pre-migration"
        
        Returns:
            Path del backup o None si falla
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"ama_backup_{backup_type}_{timestamp}"
        backup_dir = self.config.BACKUP_DIR / backup_name
        
        logger.info(f"🔄 Iniciando backup: {backup_name}")
        
        try:
            # Crear directorio temporal
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 1. Backup de base de datos
            logger.info("📦 Backing up database...")
            db_backup_path = backup_dir / "ama_dashboard.db"
            
            if not DatabaseBackup.backup_online(
                self.config.DB_PATH, 
                db_backup_path
            ):
                raise Exception("Database backup failed")
            
            # Verificar integridad
            is_valid, message = DatabaseBackup.verify_backup(db_backup_path)
            if not is_valid:
                raise Exception(f"Backup verification failed: {message}")
            
            logger.info(f"✅ DB backup verificado: {message}")
            
            # 2. Backup de archivos críticos
            logger.info("📄 Backing up critical files...")
            config_dir = backup_dir / "config"
            config_dir.mkdir(exist_ok=True)
            
            for file_path in self.config.CRITICAL_FILES:
                if file_path.exists():
                    dest = config_dir / file_path.name
                    shutil.copy2(file_path, dest)
                    logger.info(f"  ✓ {file_path.name}")
            
            # 3. Metadata del backup
            metadata = {
                'backup_type': backup_type,
                'timestamp': timestamp,
                'datetime': datetime.now().isoformat(),
                'db_stats': DatabaseBackup.get_db_stats(db_backup_path),
                'checksums': {
                    'database': calculate_checksum(db_backup_path)
                }
            }
            
            metadata_path = backup_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # 4. Comprimir backup
            logger.info("🗜️  Compressing backup...")
            archive_path = self.config.BACKUP_DIR / f"{backup_name}.tar.gz"
            
            shutil.make_archive(
                str(archive_path.with_suffix('')),
                'gztar',
                backup_dir
            )
            
            # Limpiar directorio temporal
            shutil.rmtree(backup_dir)
            
            # Información del backup
            backup_size = archive_path.stat().st_size
            logger.info(f"✅ Backup completado: {format_size(backup_size)}")
            logger.info(f"   Ubicación: {archive_path}")
            
            # 5. Upload a S3 (si está configurado)
            if self.s3_client:
                self._upload_to_s3(archive_path, metadata)
            
            # 6. Limpieza de backups antiguos
            self._cleanup_old_backups()
            
            return archive_path
            
        except Exception as e:
            logger.error(f"❌ Error en backup: {e}")
            
            # Limpiar en caso de error
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            
            return None
    
    def _upload_to_s3(self, backup_path: Path, metadata: Dict):
        """Upload backup a S3"""
        try:
            s3_key = f"{self.config.S3_PREFIX}{backup_path.name}"
            
            logger.info(f"☁️  Uploading to S3: {s3_key}")
            
            # Upload archivo
            self.s3_client.upload_file(
                str(backup_path),
                self.config.S3_BUCKET,
                s3_key,
                ExtraArgs={
                    'Metadata': {
                        'backup-type': metadata['backup_type'],
                        'timestamp': metadata['timestamp']
                    },
                    'StorageClass': 'STANDARD_IA'  # Infrequent Access
                }
            )
            
            # Upload metadata
            metadata_key = f"{self.config.S3_PREFIX}{backup_path.stem}_metadata.json"
            self.s3_client.put_object(
                Bucket=self.config.S3_BUCKET,
                Key=metadata_key,
                Body=json.dumps(metadata, indent=2),
                ContentType='application/json'
            )
            
            logger.info(f"✅ Uploaded to S3: s3://{self.config.S3_BUCKET}/{s3_key}")
            
        except ClientError as e:
            logger.error(f"❌ Error uploading to S3: {e}")
    
    def _cleanup_old_backups(self):
        """Limpia backups antiguos según política de retención"""
        logger.info("🧹 Cleaning old backups...")
        
        now = datetime.now()
        backups = sorted(self.config.BACKUP_DIR.glob("ama_backup_*.tar.gz"))
        
        # Agrupar backups por fecha
        daily_backups = []
        weekly_backups = []
        monthly_backups = []
        
        for backup_path in backups:
            # Extraer timestamp del nombre
            try:
                parts = backup_path.stem.split('_')
                date_str = parts[-2]  # YYYYMMDD
                backup_date = datetime.strptime(date_str, "%Y%m%d")
                
                age_days = (now - backup_date).days
                
                # Clasificar
                if age_days <= self.config.RETENTION_DAYS:
                    daily_backups.append(backup_path)
                elif age_days <= (self.config.RETENTION_WEEKS * 7):
                    # Mantener solo 1 por semana
                    week_num = backup_date.isocalendar()[1]
                    if not any(b for b in weekly_backups 
                              if datetime.strptime(b.stem.split('_')[-2], "%Y%m%d").isocalendar()[1] == week_num):
                        weekly_backups.append(backup_path)
                    else:
                        backup_path.unlink()
                        logger.info(f"  ✓ Deleted (weekly duplicate): {backup_path.name}")
                elif age_days <= (self.config.RETENTION_MONTHS * 30):
                    # Mantener solo 1 por mes
                    month = backup_date.month
                    if not any(b for b in monthly_backups 
                              if datetime.strptime(b.stem.split('_')[-2], "%Y%m%d").month == month):
                        monthly_backups.append(backup_path)
                    else:
                        backup_path.unlink()
                        logger.info(f"  ✓ Deleted (monthly duplicate): {backup_path.name}")
                else:
                    # Demasiado antiguo
                    backup_path.unlink()
                    logger.info(f"  ✓ Deleted (expired): {backup_path.name}")
                    
            except (ValueError, IndexError) as e:
                logger.warning(f"  ⚠️  Skip invalid backup name: {backup_path.name}")
        
        total_kept = len(daily_backups) + len(weekly_backups) + len(monthly_backups)
        logger.info(f"✅ Cleanup completado: {total_kept} backups mantenidos")
    
    def list_backups(self) -> List[Dict]:
        """Lista todos los backups disponibles"""
        backups = []
        
        for backup_path in sorted(self.config.BACKUP_DIR.glob("ama_backup_*.tar.gz"), reverse=True):
            metadata_path = backup_path.with_suffix('').with_suffix('.json')
            
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
            
            backups.append({
                'path': backup_path,
                'name': backup_path.name,
                'size': backup_path.stat().st_size,
                'size_formatted': format_size(backup_path.stat().st_size),
                'created': datetime.fromtimestamp(backup_path.stat().st_mtime),
                'metadata': metadata
            })
        
        return backups
    
    def restore_backup(self, backup_path: Path, verify: bool = True) -> bool:
        """
        Restaura un backup
        
        Args:
            backup_path: Path al archivo .tar.gz
            verify: Verificar integridad antes de restaurar
        
        Returns:
            True si la restauración fue exitosa
        """
        logger.info(f"🔄 Restaurando backup: {backup_path.name}")
        
        try:
            # Extraer backup
            temp_dir = self.config.BACKUP_DIR / "restore_temp"
            temp_dir.mkdir(exist_ok=True)
            
            shutil.unpack_archive(backup_path, temp_dir)
            
            # Encontrar el directorio extraído
            extracted_dirs = list(temp_dir.iterdir())
            if not extracted_dirs:
                raise Exception("No se encontró contenido en el backup")
            
            restore_dir = extracted_dirs[0]
            
            # Verificar integridad si se solicita
            db_backup = restore_dir / "ama_dashboard.db"
            
            if verify:
                is_valid, message = DatabaseBackup.verify_backup(db_backup)
                if not is_valid:
                    raise Exception(f"Backup corrupto: {message}")
                logger.info(f"✅ Verificación: {message}")
            
            # Backup de la DB actual antes de restaurar
            current_db_backup = self.config.DATA_DIR / f"ama_dashboard_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if self.config.DB_PATH.exists():
                shutil.copy2(self.config.DB_PATH, current_db_backup)
                logger.info(f"✅ DB actual respaldada en: {current_db_backup.name}")
            
            # Restaurar base de datos
            shutil.copy2(db_backup, self.config.DB_PATH)
            logger.info("✅ Base de datos restaurada")
            
            # Restaurar archivos de configuración
            config_dir = restore_dir / "config"
            if config_dir.exists():
                for config_file in config_dir.iterdir():
                    dest = self.config.APP_DIR / config_file.name
                    # No sobreescribir .env por seguridad
                    if config_file.name != ".env":
                        shutil.copy2(config_file, dest)
                        logger.info(f"  ✓ {config_file.name} restaurado")
            
            # Limpiar temporal
            shutil.rmtree(temp_dir)
            
            logger.info("✅ Restauración completada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en restauración: {e}")
            
            # Limpiar temporal
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            
            return False