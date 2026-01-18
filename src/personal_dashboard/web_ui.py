"""
Web Dashboard for Personal Development Tools v2
FastAPI-based interface with Database and Auth
"""

import json
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .auth import get_current_user_from_session
from .auth import router as auth_router
from .database import ContentEntry, DebugSession, Project, User, get_db
from .plugin_system import router as plugin_router
from .routers.analytics import router as analytics_router
from .routers.credentials import router as credentials_router

app = FastAPI(title="AMA-Intent Personal Dashboard v2")

# Incluir rutas de autenticación
app.include_router(auth_router)
app.include_router(plugin_router)
app.include_router(credentials_router)
app.include_router(analytics_router)

# Mount static files
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)


# Middleware para inyectar usuario en templates
@app.middleware("http")
async def add_user_to_templates(request: Request, call_next):
    # AMA-Intent v2.0: Acceso directo sin login (Modo PC Local)
    # Siempre asignamos el usuario administrador por defecto
    db_manager = next(get_db())
    user = db_manager.query(User).filter(User.username == "admin").first()
    
    if not user:
        # Si no existe el admin, lo creamos para asegurar operatividad
        from .auth import get_password_hash
        user = User(
            username="admin",
            email="admin@ama-intent.local",
            password_hash=get_password_hash("admin123"),
            is_active=True
        )
        db_manager.add(user)
        db_manager.commit()
        db_manager.refresh(user)
    
    request.state.user = user

    response = await call_next(request)
    return response


# ==================== RUTAS DE INTERFAZ ====================


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page"""
    user = getattr(request.state, "user", None)

    # Cargar datos del usuario
    projects = db.query(Project).filter(Project.user_id == user.id).all()
    debug_sessions = (
        db.query(DebugSession).filter(DebugSession.user_id == user.id).limit(5).all()
    )

    overview = {
        "projects": projects,
        "debug_sessions": debug_sessions,
        "last_updated": datetime.now().isoformat(),
        "user": user,
    }

    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "overview": overview, "user": user}
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/debug", response_class=HTMLResponse)
async def debug_assistant(request: Request):
    user = getattr(request.state, "user", None)
    return templates.TemplateResponse("debug.html", {"request": request, "user": user})


@app.get("/projects", response_class=HTMLResponse)
async def projects_view(request: Request, db: Session = Depends(get_db)):
    user = getattr(request.state, "user", None)
    projects = db.query(Project).filter(Project.user_id == user.id).all()
    return templates.TemplateResponse(
        "projects.html", {"request": request, "projects": projects, "user": user}
    )


@app.get("/content", response_class=HTMLResponse)
async def content_creator(request: Request):
    user = getattr(request.state, "user", None)
    return templates.TemplateResponse(
        "content.html", {"request": request, "user": user}
    )


# ==================== API ENDPOINTS = :D ====================


@app.get("/api/overview")
async def get_overview(request: Request, db: Session = Depends(get_db)):
    user = getattr(request.state, "user", None)

    project_count = db.query(Project).filter(Project.user_id == user.id).count()
    debug_count = db.query(DebugSession).filter(DebugSession.user_id == user.id).count()

    return {
        "total_projects": project_count,
        "total_debug_sessions": debug_count,
        "username": user.username,
    }
