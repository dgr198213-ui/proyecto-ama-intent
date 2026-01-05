"""
Web Dashboard for Personal Development Tools v2
FastAPI-based interface with Database and Auth
"""

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
import json

from .database import get_db, User, Project, DebugSession, ContentEntry
from .auth import router as auth_router, get_current_user_from_session
from .plugin_system import router as plugin_router

app = FastAPI(title="AMA-Intent Personal Dashboard v2")

# Incluir rutas de autenticación
app.include_router(auth_router)
app.include_router(plugin_router)

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
    # Intentar obtener token de cookie
    token = request.cookies.get("session_token")
    if token:
        from .auth import decode_access_token
        payload = decode_access_token(token)
        if payload:
            db_manager = next(get_db())
            user = db_manager.query(User).filter(User.id == payload.get("sub")).first()
            request.state.user = user
        else:
            request.state.user = None
    else:
        request.state.user = None
    
    response = await call_next(request)
    return response

# ==================== RUTAS DE INTERFAZ ====================

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page"""
    user = getattr(request.state, "user", None)
    if not user:
        return RedirectResponse(url="/login")
    
    # Cargar datos del usuario
    projects = db.query(Project).filter(Project.user_id == user.id).all()
    debug_sessions = db.query(DebugSession).filter(DebugSession.user_id == user.id).limit(5).all()
    
    overview = {
        "projects": projects,
        "debug_sessions": debug_sessions,
        "last_updated": datetime.now().isoformat(),
        "user": user
    }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "overview": overview,
        "user": user
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/debug", response_class=HTMLResponse)
async def debug_assistant(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("debug.html", {"request": request, "user": user})

@app.get("/projects", response_class=HTMLResponse)
async def projects_view(request: Request, db: Session = Depends(get_db)):
    user = getattr(request.state, "user", None)
    if not user:
        return RedirectResponse(url="/login")
    
    projects = db.query(Project).filter(Project.user_id == user.id).all()
    return templates.TemplateResponse("projects.html", {
        "request": request,
        "projects": projects,
        "user": user
    })

@app.get("/content", response_class=HTMLResponse)
async def content_creator(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("content.html", {"request": request, "user": user})

# ==================== API ENDPOINTS = :D ====================

@app.get("/api/overview")
async def get_overview(request: Request, db: Session = Depends(get_db)):
    user = getattr(request.state, "user", None)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "No autenticado"})
    
    project_count = db.query(Project).filter(Project.user_id == user.id).count()
    debug_count = db.query(DebugSession).filter(DebugSession.user_id == user.id).count()
    
    return {
        "total_projects": project_count,
        "total_debug_sessions": debug_count,
        "username": user.username
    }
