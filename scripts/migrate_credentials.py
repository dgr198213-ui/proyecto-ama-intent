import sys
import os

# Agregar el directorio raíz al path para poder importar src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.personal_dashboard.database import DatabaseManager, ServiceCredential

def upgrade():
    """Agregar tabla de credenciales"""
    print("Iniciando migración de base de datos...")
    db_manager = DatabaseManager()
    print(f"Usando base de datos en: {db_manager.db_path}")
    
    # Crear la tabla si no existe
    ServiceCredential.__table__.create(bind=db_manager.engine, checkfirst=True)
    print("✅ Tabla 'service_credentials' creada o ya existente")

def downgrade():
    """Eliminar tabla de credenciales"""
    print("Eliminando tabla service_credentials...")
    db_manager = DatabaseManager()
    ServiceCredential.__table__.drop(bind=db_manager.engine, checkfirst=True)
    print("✅ Tabla eliminada")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
