import os
import sys

from sqlalchemy.orm import Session

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_manager.credentials_manager import CredentialsManager
from src.personal_dashboard.database import DatabaseManager, ServiceCredential, User


def test_integration():
    print("Iniciando prueba de integración de credenciales...")
    db_manager = DatabaseManager()
    db_manager.init_db()
    session = db_manager.get_session()

    try:
        # 1. Asegurar que existe un usuario de prueba
        user = session.query(User).first()
        if not user:
            print("Creando usuario de prueba...")
            user = User(
                username="testuser", email="test@example.com", password_hash="hash"
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        print(f"Usando usuario: {user.username} (ID: {user.id})")

        # 2. Probar el CredentialsManager
        manager = CredentialsManager(session, secret_key="test-secret-key")

        # Guardar una credencial
        print("Guardando credencial de prueba para OpenAI...")
        result = manager.save_credential(
            user_id=user.id,
            service_name="openai",
            api_key="sk-test-12345",
            organization="org-test",
        )
        print(f"Resultado de guardado: {result}")

        # Recuperar la credencial
        print("Recuperando credencial...")
        cred = manager.get_credential(user.id, "openai", decrypt_key=True)
        if cred and cred["api_key"] == "sk-test-12345":
            print("✅ Credencial recuperada y descifrada correctamente")
        else:
            print(f"❌ Error al recuperar credencial: {cred}")

        # Listar todas
        all_creds = manager.get_all_credentials(user.id)
        print(f"Total de credenciales del usuario: {len(all_creds)}")

        # 3. Limpiar (opcional)
        # session.delete(session.query(ServiceCredential).filter_by(user_id=user.id).first())
        # session.commit()

        print("✅ Prueba de integración completada con éxito")

    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback

        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    test_integration()
