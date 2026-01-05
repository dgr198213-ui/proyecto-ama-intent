"""
Módulo de base de datos para AMA-Intent Personal Dashboard v2
Autor: Manus IA
Fecha: Enero 2026
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import json
from typing import Optional

Base = declarative_base()

# ==================== MODELOS DE DATOS ====================

class User(Base):
    """Modelo de usuario del sistema"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relaciones
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    debug_sessions = relationship("DebugSession", back_populates="user")
    content_entries = relationship("ContentEntry", back_populates="user")
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Project(Base):
    """Modelo de proyecto personal"""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default='active')  # active, completed, archived
    tags = Column(Text, nullable=True)  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="projects")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'tags': json.loads(self.tags) if self.tags else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DebugSession(Base):
    """Registro de sesiones de debugging"""
    __tablename__ = 'debug_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    error_type = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=False)
    language = Column(String(20), default='python')
    solution_provided = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.0)
    time_saved_minutes = Column(Integer, default=0)  # tiempo estimado ahorrado
    code_snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="debug_sessions")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'error_type': self.error_type,
            'error_message': self.error_message[:100] + '...' if len(self.error_message) > 100 else self.error_message,
            'language': self.language,
            'confidence_score': self.confidence_score,
            'time_saved_minutes': self.time_saved_minutes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ContentEntry(Base):
    """Registro de contenido generado"""
    __tablename__ = 'content_entries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content_type = Column(String(30), nullable=False)  # blog, social, seo
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    metrics = Column(Text, nullable=True)  # JSON con métricas
    exported = Column(Boolean, default=False)
    export_formats = Column(Text, nullable=True)  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="content_entries")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content_type': self.content_type,
            'title': self.title,
            'content_preview': self.content[:150] + '...' if len(self.content) > 150 else self.content,
            'metrics': json.loads(self.metrics) if self.metrics else {},
            'exported': self.exported,
            'export_formats': json.loads(self.export_formats) if self.export_formats else [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SystemLog(Base):
    """Logs del sistema"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    level = Column(String(10), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    module = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'module': self.module,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ==================== GESTIÓN DE BASE DE DATOS ====================

class DatabaseManager:
    """Gestor centralizado de base de datos"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Ruta por defecto
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(base_dir, 'data', 'dashboard.db')
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def init_db(self):
        """Inicializa la base de datos creando todas las tablas"""
        Base.metadata.create_all(bind=self.engine)
        print(f"✅ Base de datos inicializada en: {self.db_path}")
        
    def get_session(self):
        """Obtiene una nueva sesión de base de datos"""
        return self.SessionLocal()
    
    def migrate_from_json(self, json_path: str):
        """Migra datos desde archivos JSON antiguos"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = self.get_session()
            
            # Migrar proyectos si existen
            if 'projects' in data:
                for proj_data in data['projects']:
                    project = Project(
                        user_id=1,  # Asignar al usuario admin por defecto
                        name=proj_data.get('name', 'Proyecto migrado'),
                        description=proj_data.get('description', ''),
                        status=proj_data.get('status', 'active'),
                        tags=json.dumps(proj_data.get('tags', []))
                    )
                    session.add(project)
            
            session.commit()
            session.close()
            print(f"✅ Migración completada desde {json_path}")
            
        except Exception as e:
            print(f"❌ Error en migración: {e}")
    
    def backup_database(self, backup_path: str = None):
        """Crea una copia de seguridad de la base de datos"""
        import shutil
        import datetime
        
        if backup_path is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, f'dashboard_backup_{timestamp}.db')
        
        shutil.copy2(self.db_path, backup_path)
        print(f"✅ Copia de seguridad creada en: {backup_path}")
        return backup_path


# ==================== FUNCIONES DE AYUDA ====================

def get_db():
    """Dependency para FastAPI para obtener sesión de DB"""
    db = DatabaseManager()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


def create_admin_user(session, username: str = "admin", email: str = "admin@ama-intent.com", password: str = "admin123"):
    """Crea un usuario administrador por defecto (solo para desarrollo)"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Verificar si ya existe
    existing = session.query(User).filter_by(username=username).first()
    if existing:
        return existing
    
    # Crear nuevo usuario
    admin = User(
        username=username,
        email=email,
        password_hash=pwd_context.hash(password[:72]),
        is_active=True
    )
    session.add(admin)
    session.commit()
    return admin


# Inicialización automática al importar
if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_manager.init_db()
    print("Base de datos lista para usar.")