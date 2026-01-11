"""
Módulo de autenticación para AMA-Intent Personal Dashboard v2
Autor: Manus IA
Fecha: Enero 2026
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import User, get_db

# ==================== CONFIGURACIÓN ====================

# Claves secretas (en producción usar variables de entorno)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_urlsafe(32))

# Contexto para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de bearer para JWT
security = HTTPBearer()

# ==================== FUNCIONES DE AYUDA ====================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera hash de una contraseña"""
    return pwd_context.hash(password[:72])


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Crea un token JWT de acceso"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodifica y valida un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Dependency para obtener el usuario actual desde JWT"""
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_from_session(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    """Obtiene usuario desde sesión de navegador"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user if user and user.is_active else None


def require_login(user: Optional[User] = None) -> User:
    """Valida que el usuario esté autenticado"""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ==================== MODELOS PYDANTIC ====================

from typing import Optional as Opt

from pydantic import BaseModel, EmailStr, validator


class UserRegister(BaseModel):
    """Modelo para registro de usuario"""

    username: str
    email: EmailStr
    password: str
    confirm_password: str

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        if "password" in values and v != values["password"]:
            raise ValueError("Las contraseñas no coinciden")
        return v

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        # Aquí podrías añadir más validaciones de fortaleza
        return v


class UserLogin(BaseModel):
    """Modelo para login de usuario"""

    username: str
    password: str


class UserUpdate(BaseModel):
    """Modelo para actualización de usuario"""

    email: Opt[EmailStr] = None
    current_password: Opt[str] = None
    new_password: Opt[str] = None


class TokenResponse(BaseModel):
    """Respuesta con token JWT"""

    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


class UserResponse(BaseModel):
    """Respuesta con datos de usuario"""

    id: int
    username: str
    email: str
    is_active: bool
    created_at: str
    last_login: Opt[str] = None


# ==================== ENDPOINTS DE AUTENTICACIÓN ====================

from fastapi import APIRouter, Form, Response
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Registra un nuevo usuario"""
    # Verificar si el usuario ya existe
    existing_user = (
        db.query(User)
        .filter((User.username == user_data.username) | (User.email == user_data.email))
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario o email ya existen",
        )

    # Crear nuevo usuario
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user.to_dict()


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_data: UserLogin, response: Response, db: Session = Depends(get_db)
):
    """Inicia sesión y retorna token JWT"""
    user = db.query(User).filter(User.username == user_data.username).first()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo"
        )

    # Actualizar último login
    user.last_login = datetime.utcnow()
    db.commit()

    # Crear token JWT
    access_token = create_access_token(data={"sub": user.id})

    # Configurar cookie de sesión para navegador
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False,  # En producción debería ser True (HTTPS)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
    }


@router.post("/logout")
async def logout_user(response: Response):
    """Cierra la sesión del usuario"""
    response.delete_cookie(key="session_token")
    return {"message": "Sesión cerrada exitosamente"}


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Obtiene el perfil del usuario actual"""
    return current_user.to_dict()


@router.put("/profile")
async def update_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualiza el perfil del usuario"""
    update_dict = {}

    if update_data.email:
        # Verificar que el email no esté en uso
        existing = (
            db.query(User)
            .filter(User.email == update_data.email, User.id != current_user.id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso",
            )
        update_dict["email"] = update_data.email

    if update_data.new_password:
        if not update_data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere la contraseña actual para cambiarla",
            )

        if not verify_password(
            update_data.current_password, current_user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña actual incorrecta",
            )

        update_dict["password_hash"] = get_password_hash(update_data.new_password)

    for key, value in update_dict.items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return current_user.to_dict()
