import sys
import os
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_database():
    print("🔍 Probando Base de Datos...")
    try:
        from personal_dashboard.database import DatabaseManager, User
        db = DatabaseManager()
        session = db.get_session()
        user_count = session.query(User).count()
        print(f"✅ DB OK: {user_count} usuarios encontrados.")
        session.close()
        return True
    except Exception as e:
        print(f"❌ Error DB: {e}")
        return False

def test_auth():
    print("🔍 Probando Autenticación...")
    try:
        from personal_dashboard.auth import get_password_hash, verify_password
        pwd = "test_password"
        h = get_password_hash(pwd)
        if verify_password(pwd, h):
            print("✅ Auth OK: Hashing y verificación correctos.")
            return True
        else:
            print("❌ Auth Error: Verificación fallida.")
            return False
    except Exception as e:
        print(f"❌ Error Auth: {e}")
        return False

def test_plugins():
    print("🔍 Probando Sistema de Plugins...")
    try:
        from personal_dashboard.plugin_system import PluginManager
        pm = PluginManager()
        manifests = pm.discover_plugins()
        print(f"✅ Plugins OK: {len(manifests)} plugins descubiertos.")
        pm.load_all_plugins()
        if len(pm.plugins) > 0:
            print(f"✅ Plugins OK: {len(pm.plugins)} plugins cargados.")
            return True
        else:
            print("⚠️ Plugins: No se cargaron plugins (esto puede ser normal si no hay plugins válidos).")
            return True
    except Exception as e:
        print(f"❌ Error Plugins: {e}")
        return False

def test_web_ui():
    print("🔍 Probando Web UI (FastAPI)...")
    try:
        from personal_dashboard.web_ui import app
        print("✅ Web UI OK: App instanciada correctamente.")
        return True
    except Exception as e:
        print(f"❌ Error Web UI: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando Comprobación del Sistema AMA-Intent v2.1\n")
    results = [
        test_database(),
        test_auth(),
        test_plugins(),
        test_web_ui()
    ]
    
    if all(results):
        print("\n✨ SISTEMA INTEGRALMENTE VALIDADO ✨")
        sys.exit(0)
    else:
        print("\n⚠️ SE DETECTARON ERRORES EN EL SISTEMA")
        sys.exit(1)
