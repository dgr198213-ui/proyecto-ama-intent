from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List
import json

from ..database import get_db, User
from ..auth import get_current_user_from_session
from ...config_manager.credentials_manager import CredentialsManager

router = APIRouter(prefix="/credentials", tags=["credentials"])

async def get_user_or_redirect(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    if not user:
        raise HTTPException(status_code=303, detail="Not authenticated", headers={"Location": "/login"})
    return user

@router.get("/", response_class=HTMLResponse)
async def credentials_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    """Panel principal de credenciales"""
    user = get_current_user_from_session(request, db)
    if not user:
        return RedirectResponse(url="/login")
        
    manager = CredentialsManager(db)
    
    credentials = manager.get_all_credentials(user.id)
    available_services = manager.get_available_services()
    
    from ..web_ui import templates
    return templates.TemplateResponse(
        "credentials/dashboard.html",
        {
            "request": request,
            "user": user,
            "credentials": credentials,
            "available_services": available_services,
            "active_page": "credentials"
        }
    )

@router.get("/add/{service_name}", response_class=HTMLResponse)
async def add_credential_form(
    request: Request,
    service_name: str,
    db: Session = Depends(get_db)
):
    """Formulario para agregar credencial"""
    user = get_current_user_from_session(request, db)
    if not user:
        return RedirectResponse(url="/login")
        
    manager = CredentialsManager(db)
    
    # Verificar si el servicio es soportado
    available_services = manager.get_available_services()
    service_config = next((s for s in available_services if s["name"] == service_name), None)
    
    if not service_config:
        raise HTTPException(status_code=404, detail="Servicio no soportado")
    
    # Verificar si ya existe
    existing = manager.get_credential(user.id, service_name)
    
    from ..web_ui import templates
    return templates.TemplateResponse(
        "credentials/add_edit.html",
        {
            "request": request,
            "user": user,
            "service_config": service_config,
            "existing": existing,
            "mode": "edit" if existing else "add",
            "active_page": "credentials"
        }
    )

@router.post("/save")
async def save_credential(
    request: Request,
    db: Session = Depends(get_db)
):
    """Guardar credencial (crear o actualizar)"""
    user = get_current_user_from_session(request, db)
    if not user:
        return RedirectResponse(url="/login")
        
    form_data = await request.form()
    
    service_name = form_data.get("service_name")
    api_key = form_data.get("api_key")
    api_base = form_data.get("api_base", "")
    api_version = form_data.get("api_version", "")
    organization = form_data.get("organization", "")
    project_id = form_data.get("project_id", "")
    region = form_data.get("region", "")
    
    if not service_name or not api_key:
        raise HTTPException(status_code=400, detail="Servicio y API key requeridos")
    
    manager = CredentialsManager(db)
    
    manager.save_credential(
        user_id=user.id,
        service_name=service_name,
        api_key=api_key,
        api_base=api_base,
        api_version=api_version,
        organization=organization,
        project_id=project_id,
        region=region
    )
    
    return RedirectResponse(url="/credentials", status_code=303)

@router.post("/delete/{credential_id}")
async def delete_credential(
    request: Request,
    credential_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar credencial"""
    user = get_current_user_from_session(request, db)
    if not user:
        return {"status": "error", "message": "No autenticado"}
        
    manager = CredentialsManager(db)
    
    success = manager.delete_credential(user.id, credential_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Credencial no encontrada")
    
    return {"status": "success", "message": "Credencial eliminada"}

@router.post("/toggle/{credential_id}")
async def toggle_credential(
    request: Request,
    credential_id: int,
    db: Session = Depends(get_db)
):
    """Activar/desactivar credencial"""
    user = get_current_user_from_session(request, db)
    if not user:
        return {"status": "error", "message": "No autenticado"}
        
    manager = CredentialsManager(db)
    
    new_state = manager.toggle_credential(user.id, credential_id)
    
    state_text = "activada" if new_state else "desactivada"
    return {"status": "success", "is_active": new_state, "message": f"Credencial {state_text}"}

@router.get("/api/services")
async def get_available_services(
    request: Request,
    db: Session = Depends(get_db)
):
    """Obtener servicios disponibles (API)"""
    user = get_current_user_from_session(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    manager = CredentialsManager(db)
    return manager.get_available_services()

@router.get("/api/user")
async def get_user_credentials(
    request: Request,
    db: Session = Depends(get_db)
):
    """Obtener credenciales del usuario (API)"""
    user = get_current_user_from_session(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    manager = CredentialsManager(db)
    return manager.get_all_credentials(user.id)
