from fasthtml.common import *
from local_cortex.thought import LocalBrain
from local_cortex.memory import (
    init_db, save_thought, get_last_thoughts,
    search_thoughts, get_memory_stats, cleanup_old_thoughts,
    get_thoughts_by_intent
)
from datetime import datetime
from dotenv import load_dotenv, set_key, find_dotenv
from cryptography.fernet import Fernet, InvalidToken
import uvicorn
import os
import logging

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Security utilities
def validate_shared_secret(req):
    """Validate AMA shared secret from request headers."""
    expected_secret = os.getenv("AMA_SHARED_SECRET", "")
    if not expected_secret or expected_secret == "change-this-secret-in-production":
        logger.warning("⚠️ AMA_SHARED_SECRET not properly configured")
        return False
    
    provided_secret = req.headers.get("X-AMA-Secret", "")
    return provided_secret == expected_secret

def validate_fernet_key():
    """Validate that FERNET_KEY is properly formatted."""
    fernet_key = os.getenv("FERNET_KEY", "")
    if not fernet_key:
        return None  # No key configured
    
    try:
        Fernet(fernet_key.encode())
        return True
    except Exception:
        return False

def reload_env():
    """Hot reload environment variables from .env file."""
    load_dotenv(override=True)
    logger.info("♻️ Environment variables reloaded")

def get_security_warnings():
    """Get list of security warnings for display."""
    warnings = []
    
    # Check shared secret
    shared_secret = os.getenv("AMA_SHARED_SECRET", "")
    if not shared_secret or shared_secret == "change-this-secret-in-production":
        warnings.append("⚠️ AMA_SHARED_SECRET no configurado o usando valor por defecto")
    
    # Check Fernet key
    fernet_status = validate_fernet_key()
    if fernet_status is False:
        warnings.append("⚠️ FERNET_KEY mal formateado o inválido")
    elif fernet_status is None:
        warnings.append("ℹ️ FERNET_KEY no configurado (opcional)")
    
    return warnings

# Inicialización del sistema
try:
    init_db()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.warning(f"⚠️ Database initialization failed: {e}. Memory features may be limited.")

brain = LocalBrain()
app, rt = fast_app()


@rt("/")
def get():
    return Titled("AMA-Intent v3 (Local Brain)",
                  Div(
                      H1("🧠 Sistema Biomimético: OPERATIVO"),
                      P("Conectado a puerto 5001. Esperando señal de Qodeia.com..."),
                      Div(id="logs", style="background: #111; color: #0f0; padding: 10px; font-family: monospace;")
                  )
                  )


@rt("/api/health")
async def health(req):
    """Health check endpoint with shared secret validation."""
    if not validate_shared_secret(req):
        logger.warning("🚫 Unauthorized health check attempt")
        return {"error": "Unauthorized", "status": "error"}, 401
    
    try:
        stats = get_memory_stats()
        warnings = get_security_warnings()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "memory_stats": stats,
            "security_warnings": warnings
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {"error": str(e), "status": "error"}, 500


@rt("/api/synapse", methods=["POST"])
async def synapse(req):
    """Endpoint principal que recibe datos de tu web."""
    # Validate shared secret for production security
    if not validate_shared_secret(req):
        logger.warning("🚫 Unauthorized synapse request")
        return {"error": "Unauthorized", "status": "error"}, 401
    
    try:
        form = await req.form()
        user_input = form.get("input", "")

        if not user_input:
            return {"error": "Cortex recibió señal vacía", "status": "error"}

        # Get context limit from environment
        context_limit = int(os.getenv("MEMORY_CONTEXT_LIMIT", "5"))
        
        # Recuperar memoria a corto plazo
        context = get_last_thoughts(context_limit)

        # Pensar y clasificar
        classification = brain.fast_classify(user_input)
        intent = classification["intent"] if isinstance(classification, dict) else classification
        confidence = classification.get("confidence", 0.8) if isinstance(classification, dict) else 0.8
        
        response_text = brain.think(user_input, context)

        # Guardar en memoria
        save_thought(user_input, response_text, intent)

        # Responder a la web
        return {
            "status": "success",
            "intent": intent,
            "confidence": confidence,
            "response": response_text,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {"error": str(e), "status": "error"}


@rt("/api/memory/search")
async def memory_search(req):
    """Search through stored memories."""
    try:
        query = req.query_params.get("q", "")
        limit = int(req.query_params.get("limit", "10"))
        
        if not query:
            return {"error": "Query parameter 'q' is required", "status": "error"}
        
        results = search_thoughts(query, limit)
        return {
            "status": "success",
            "query": query,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        return {"error": str(e), "status": "error"}


@rt("/api/memory/stats")
async def memory_stats():
    """Get memory statistics."""
    try:
        stats = get_memory_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        return {"error": str(e), "status": "error"}


@rt("/api/memory/cleanup", methods=["POST"])
async def memory_cleanup(req):
    """Cleanup old memories."""
    try:
        form = await req.form()
        days = int(form.get("days", os.getenv("MEMORY_ARCHIVE_DAYS", "30")))
        
        deleted_count = cleanup_old_thoughts(days)
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"Cleaned up {deleted_count} thoughts older than {days} days"
        }
    except Exception as e:
        logger.error(f"Error cleaning up memory: {e}")
        return {"error": str(e), "status": "error"}


@rt("/api/memory/by-intent/{intent}")
async def memory_by_intent(intent: str, req):
    """Get memories filtered by intent."""
    try:
        # Make limit configurable via query parameter
        limit = int(req.query_params.get("limit", "10"))
        results = get_thoughts_by_intent(intent.upper(), limit)
        return {
            "status": "success",
            "intent": intent.upper(),
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error retrieving memories by intent: {e}")
        return {"error": str(e), "status": "error"}


@rt("/credenciales")
def credenciales():
    """Panel de gestión de credenciales minimalista."""
    try:
        # Get current values (masked)
        shared_secret = os.getenv("AMA_SHARED_SECRET", "")
        fernet_key = os.getenv("FERNET_KEY", "")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1")
        
        # Mask secrets for display
        shared_secret_display = shared_secret[:8] + "..." if len(shared_secret) > 8 else shared_secret
        fernet_key_display = fernet_key[:8] + "..." if len(fernet_key) > 8 else "(vacío)"
        
        warnings = get_security_warnings()
        warning_html = ""
        if warnings:
            warning_html = Div(
                *[P(w, style="color: #dc2626; background: #fef2f2; padding: 8px; border-radius: 4px; margin: 5px 0;") for w in warnings],
                style="margin-bottom: 20px;"
            )
        
        return Titled("🔐 Gestión de Credenciales - AMA-Intent v3",
                      Div(
                          H1("🔐 Panel de Credenciales"),
                          P("Gestiona las claves críticas del sistema. Los cambios se aplican inmediatamente (hot reload).", 
                            style="color: #6b7280; margin-bottom: 20px;"),
                          warning_html,
                          Form(
                              Div(
                                  Label("AMA_SHARED_SECRET:", style="font-weight: bold; display: block; margin-top: 15px;"),
                                  P(f"Valor actual: {shared_secret_display}", style="color: #6b7280; font-size: 0.9em;"),
                                  Input(type="password", name="ama_shared_secret", placeholder="Dejar vacío para no cambiar", 
                                        style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;"),
                                  P("Secreto compartido para autenticación del bridge", 
                                    style="color: #6b7280; font-size: 0.85em; margin-top: 5px;")
                              ),
                              Div(
                                  Label("FERNET_KEY:", style="font-weight: bold; display: block; margin-top: 15px;"),
                                  P(f"Valor actual: {fernet_key_display}", style="color: #6b7280; font-size: 0.9em;"),
                                  Input(type="password", name="fernet_key", placeholder="Dejar vacío para no cambiar", 
                                        style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;"),
                                  P("Clave de encriptación Fernet (opcional)", 
                                    style="color: #6b7280; font-size: 0.85em; margin-top: 5px;")
                              ),
                              Div(
                                  Label("OLLAMA_MODEL:", style="font-weight: bold; display: block; margin-top: 15px;"),
                                  P(f"Valor actual: {ollama_model}", style="color: #6b7280; font-size: 0.9em;"),
                                  Input(type="text", name="ollama_model", placeholder="llama3.1", 
                                        style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;"),
                                  P("Modelo de Ollama a utilizar", 
                                    style="color: #6b7280; font-size: 0.85em; margin-top: 5px;")
                              ),
                              Button("💾 Guardar y Recargar", type="submit",
                                     style="margin-top: 20px; padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;"),
                              action="/api/credenciales/save",
                              method="POST",
                              style="max-width: 600px;"
                          ),
                          P(A("← Volver al Admin", href="/admin"), style="margin-top: 30px;"),
                          style="background: #ffffff; padding: 30px; font-family: sans-serif; max-width: 800px; margin: 0 auto;"
                      )
                      )
    except Exception as e:
        logger.error(f"Error loading credentials panel: {e}")
        return Titled("Error", P(f"Error: {str(e)}"))


@rt("/api/credenciales/save", methods=["POST"])
async def save_credenciales(req):
    """Save credentials to .env file and hot reload."""
    try:
        form = await req.form()
        
        # Find or create .env file
        env_path = find_dotenv()
        if not env_path:
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
            # Create .env from .env.example if it doesn't exist
            env_example_path = env_path + ".example"
            if os.path.exists(env_example_path) and not os.path.exists(env_path):
                import shutil
                shutil.copy(env_example_path, env_path)
        
        updated_keys = []
        
        # Update AMA_SHARED_SECRET if provided
        ama_secret = form.get("ama_shared_secret", "").strip()
        if ama_secret:
            set_key(env_path, "AMA_SHARED_SECRET", ama_secret)
            updated_keys.append("AMA_SHARED_SECRET")
        
        # Update FERNET_KEY if provided
        fernet_key = form.get("fernet_key", "").strip()
        if fernet_key:
            # Validate Fernet key format
            try:
                Fernet(fernet_key.encode())
                set_key(env_path, "FERNET_KEY", fernet_key)
                updated_keys.append("FERNET_KEY")
            except Exception as e:
                logger.warning(f"Invalid Fernet key provided: {e}")
                return Titled("Error de Validación",
                              Div(
                                  H1("❌ Error"),
                                  P("La clave FERNET_KEY proporcionada no es válida.", style="color: #dc2626;"),
                                  P(f"Detalle: {str(e)}", style="color: #6b7280; font-size: 0.9em;"),
                                  P(A("← Volver", href="/credenciales"), style="margin-top: 20px;")
                              ))
        
        # Update OLLAMA_MODEL if provided
        ollama_model = form.get("ollama_model", "").strip()
        if ollama_model:
            set_key(env_path, "OLLAMA_MODEL", ollama_model)
            updated_keys.append("OLLAMA_MODEL")
        
        # Hot reload environment variables
        reload_env()
        
        logger.info(f"✅ Credentials updated: {', '.join(updated_keys)}")
        
        return Titled("✅ Credenciales Actualizadas",
                      Div(
                          H1("✅ Cambios Guardados"),
                          P(f"Las siguientes claves han sido actualizadas: {', '.join(updated_keys)}", 
                            style="color: #059669; font-weight: bold;"),
                          P("Los cambios se han aplicado inmediatamente sin reiniciar el servidor.", 
                            style="color: #6b7280; margin-top: 10px;"),
                          P(A("← Volver al panel", href="/credenciales"), " | ", A("Ver Admin", href="/admin"), 
                            style="margin-top: 20px;"),
                          style="background: #f0fdf4; padding: 30px; border: 2px solid #059669; border-radius: 8px; max-width: 600px; margin: 50px auto;"
                      ))
    except Exception as e:
        logger.error(f"Error saving credentials: {e}")
        return Titled("Error",
                      Div(
                          H1("❌ Error al Guardar"),
                          P(f"Error: {str(e)}", style="color: #dc2626;"),
                          P(A("← Volver", href="/credenciales"), style="margin-top: 20px;")
                      ))


@rt("/admin")
def admin():
    """Admin dashboard with system statistics."""
    try:
        stats = get_memory_stats()
        warnings = get_security_warnings()
        
        # Build warning display
        warning_elements = []
        if warnings:
            warning_elements.append(H2("⚠️ Advertencias de Seguridad", style="color: #d97706;"))
            for warning in warnings:
                warning_elements.append(P(warning, style="color: #dc2626; background: #fef2f2; padding: 8px; border-radius: 4px;"))
        else:
            warning_elements.append(P("✅ No hay advertencias de seguridad", style="color: #059669;"))
        
        return Titled("AMA-Intent v3 - Admin Dashboard",
                      Div(
                          H1("🧠 Sistema de Administración"),
                          *warning_elements,
                          H2("📊 Estadísticas de Memoria"),
                          P(f"Total de interacciones: {stats['total_interactions']}"),
                          P(f"Por intención: {stats['by_intent']}"),
                          P(f"Primera interacción: {stats['first_interaction'] or 'N/A'}"),
                          P(f"Última interacción: {stats['last_interaction'] or 'N/A'}"),
                          H2("🔧 Endpoints API"),
                          Ul(
                              Li("GET /api/health - Health check con autenticación"),
                              Li("POST /api/synapse - Procesamiento principal (requiere secreto)"),
                              Li("GET /api/memory/search?q=query - Buscar en memoria"),
                              Li("GET /api/memory/stats - Estadísticas de memoria"),
                              Li("POST /api/memory/cleanup - Limpiar memorias antiguas"),
                              Li("GET /api/memory/by-intent/{intent} - Filtrar por intención")
                          ),
                          H2("🔐 Gestión"),
                          P(A("Panel de Credenciales", href="/credenciales"), " - Gestionar claves del sistema"),
                          style="background: #f5f5f5; padding: 20px; font-family: sans-serif;"
                      )
                      )
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        return Titled("Error", P(f"Error: {str(e)}"))


if __name__ == "__main__":
    # Get configuration from environment variables with secure defaults
    host = os.getenv("HOST", "127.0.0.1")  # Default to localhost for security
    port = int(os.getenv("PORT", "5001"))
    reload = os.getenv("RELOAD", "false").lower() == "true"  # Default to false for production

    uvicorn.run("bridge.server:app", host=host, port=port, reload=reload)
