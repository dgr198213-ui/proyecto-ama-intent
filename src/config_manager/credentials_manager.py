import base64
import os
from typing import Dict, List, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.orm import Session


class CredentialsManager:
    """Gestor seguro de credenciales de servicios externos"""

    def __init__(self, db_session: Session, secret_key: str = None):
        self.db = db_session
        self.secret_key = secret_key or os.getenv(
            "CREDENTIALS_SECRET_KEY", "default-key-change-me"
        )
        self.cipher = self._init_cipher()

    def _init_cipher(self):
        """Inicializar cifrado Fernet"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"ama_intent_credentials",
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
        return Fernet(key)

    def encrypt(self, text: str) -> str:
        """Cifrar texto"""
        return self.cipher.encrypt(text.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        """Descifrar texto"""
        return self.cipher.decrypt(encrypted_text.encode()).decode()

    def save_credential(
        self,
        user_id: int,
        service_name: str,
        api_key: str,
        api_base: str = "",
        api_version: str = "",
        organization: str = "",
        project_id: str = "",
        region: str = "",
    ) -> Dict:
        """Guardar credencial cifrada"""
        from src.personal_dashboard.database import ServiceCredential

        # Verificar si ya existe
        existing = (
            self.db.query(ServiceCredential)
            .filter_by(user_id=user_id, service_name=service_name)
            .first()
        )

        # Cifrar API key
        encrypted_key = self.encrypt(api_key)

        if existing:
            # Actualizar existente
            existing.api_key = encrypted_key
            existing.api_base = api_base
            existing.api_version = api_version
            existing.organization = organization
            existing.project_id = project_id
            existing.region = region
            self.db.commit()
            return {"status": "updated", "credential_id": existing.id}
        else:
            # Crear nuevo
            credential = ServiceCredential(
                user_id=user_id,
                service_name=service_name,
                api_key=encrypted_key,
                api_base=api_base,
                api_version=api_version,
                organization=organization,
                project_id=project_id,
                region=region,
            )
            self.db.add(credential)
            self.db.commit()
            return {"status": "created", "credential_id": credential.id}

    def get_credential(
        self, user_id: int, service_name: str, decrypt_key: bool = False
    ) -> Optional[Dict]:
        """Obtener credencial (opcionalmente descifrada)"""
        from src.personal_dashboard.database import ServiceCredential

        credential = (
            self.db.query(ServiceCredential)
            .filter_by(user_id=user_id, service_name=service_name, is_active=True)
            .first()
        )

        if not credential:
            return None

        result = credential.to_dict()

        if decrypt_key:
            try:
                result["api_key"] = self.decrypt(credential.api_key)
            except Exception as e:
                result["api_key"] = f"Error decrypting: {str(e)}"
        else:
            result["api_key"] = "********"  # Ocultar clave

        return result

    def get_all_credentials(self, user_id: int) -> List[Dict]:
        """Obtener todas las credenciales del usuario"""
        from src.personal_dashboard.database import ServiceCredential

        credentials = (
            self.db.query(ServiceCredential)
            .filter_by(user_id=user_id)
            .order_by(ServiceCredential.service_name)
            .all()
        )

        return [
            {**c.to_dict(), "api_key": "********"}  # No mostrar clave real
            for c in credentials
        ]

    def delete_credential(self, user_id: int, credential_id: int) -> bool:
        """Eliminar credencial"""
        from src.personal_dashboard.database import ServiceCredential

        credential = (
            self.db.query(ServiceCredential)
            .filter_by(id=credential_id, user_id=user_id)
            .first()
        )

        if credential:
            self.db.delete(credential)
            self.db.commit()
            return True

        return False

    def toggle_credential(self, user_id: int, credential_id: int) -> bool:
        """Activar/desactivar credencial"""
        from src.personal_dashboard.database import ServiceCredential

        credential = (
            self.db.query(ServiceCredential)
            .filter_by(id=credential_id, user_id=user_id)
            .first()
        )

        if credential:
            credential.is_active = not credential.is_active
            self.db.commit()
            return credential.is_active

        return False

    def get_available_services(self) -> List[Dict]:
        """Servicios soportados con sus configuraciones"""
        return [
            {
                "name": "openai",
                "display_name": "OpenAI",
                "description": "GPT-4, GPT-3.5, DALL-E, etc.",
                "fields": [
                    {
                        "name": "api_key",
                        "label": "API Key",
                        "type": "password",
                        "required": True,
                    },
                    {
                        "name": "api_base",
                        "label": "API Base URL",
                        "type": "text",
                        "required": False,
                    },
                    {
                        "name": "organization",
                        "label": "Organization ID",
                        "type": "text",
                        "required": False,
                    },
                ],
            },
            {
                "name": "anthropic",
                "display_name": "Anthropic Claude",
                "description": "Claude 3, Claude 2, etc.",
                "fields": [
                    {
                        "name": "api_key",
                        "label": "API Key",
                        "type": "password",
                        "required": True,
                    },
                    {
                        "name": "api_base",
                        "label": "API Base URL",
                        "type": "text",
                        "required": False,
                    },
                ],
            },
            {
                "name": "google",
                "display_name": "Google AI",
                "description": "Gemini, Vertex AI",
                "fields": [
                    {
                        "name": "api_key",
                        "label": "API Key",
                        "type": "password",
                        "required": True,
                    },
                    {
                        "name": "project_id",
                        "label": "Project ID",
                        "type": "text",
                        "required": False,
                    },
                    {
                        "name": "region",
                        "label": "Region",
                        "type": "text",
                        "required": False,
                    },
                ],
            },
            {
                "name": "cohere",
                "display_name": "Cohere",
                "description": "Cohere Command, Embed",
                "fields": [
                    {
                        "name": "api_key",
                        "label": "API Key",
                        "type": "password",
                        "required": True,
                    },
                ],
            },
            {
                "name": "huggingface",
                "display_name": "Hugging Face",
                "description": "Models, Inference API",
                "fields": [
                    {
                        "name": "api_key",
                        "label": "API Key",
                        "type": "password",
                        "required": True,
                    },
                ],
            },
            {
                "name": "replicate",
                "display_name": "Replicate",
                "description": "Open-source models",
                "fields": [
                    {
                        "name": "api_key",
                        "label": "API Key",
                        "type": "password",
                        "required": True,
                    },
                ],
            },
        ]
