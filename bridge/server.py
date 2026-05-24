import logging
import os
import shutil
from datetime import datetime

import uvicorn
from cryptography.fernet import Fernet
from dotenv import find_dotenv, load_dotenv, set_key
from fasthtml.common import *

from local_cortex.memory import (
    check_database_connection,
    cleanup_old_thoughts,
    get_last_thoughts,
    get_memory_stats,
    get_thoughts_by_intent,
    init_db,
    save_thought,
    search_thoughts,
)
from local_cortex.thought import LocalBrain

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
        logger.warning("[WARNING] AMA_SHARED_SECRET not properly configured")
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
    logger.info("[RELOAD] Environment variables reloaded")


def get_security_warnings():
    """Get list of security warnings for display."""
    warnings = []

    # Check shared secret
    shared_secret = os.getenv("AMA_SHARED_SECRET", "")
    if not shared_secret or shared_secret == "change-this-secret-in-production":
        warnings.append(
            "[WARNING] AMA_SHARED_SECRET no configurado o usando valor por defecto"
        )

    # Check Fernet key
    fernet_status = validate_fernet_key()
    if fernet_status is False:
        warnings.append("[WARNING] FERNET_KEY mal formateado o invalido")
    elif fernet_status is None:
        warnings.append("[INFO] FERNET_KEY no configurado (opcional)")

    return warnings


# Inicializacion del sistema
try:
    init_db()
    logger.info("[OK] Database initialized successfully")
except Exception as e:
    logger.warning(
        f"[WARNING] Database initialization failed: {e}. Memory features may be limited."
    )

brain = LocalBrain()
app, rt = fast_app()


@rt("/")
def get():
    return Titled(
        "AMA-Intent v3 (Local Brain)",
        Div(
            H1("[BRAIN] Sistema Biomimetico: OPERATIVO"),
            P("Conectado a puerto 5001. Esperando senal de Qodeia.com..."),
            Div(
                A("[STATS] Panel de Admin", href="/admin"),
                " | ",
                A("[LOCK] Gestionar Credenciales", href="/credenciales"),
                style="margin-bottom: 20px;",
            ),
            Div(
                id="logs",
                style="background: #111; color: #0f0; padding: 10px; font-family: monospace;",
            ),
        ),
    )


@rt("/api/health")
async def health(req):
    """Health check endpoint with shared secret validation."""
    if not validate_shared_secret(req):
        logger.warning("[BLOCKED] Unauthorized health check attempt")
        return JSONResponse({"error": "Unauthorized", "status": "error"}, status_code=401)

    try:
        stats = get_memory_stats()
        warnings = get_security_warnings()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "memory_stats": stats,
            "security_warnings": warnings,
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return JSONResponse({"error": str(e), "status": "error"}, status_code=500)


@rt("/api/db/check")
async def db_check():
    """
    Database connection check endpoint.
    Tests connectivity to the configured database (Supabase or SQLite).

    Returns appropriate HTTP status codes:
    - 200: Database connected successfully
    - 503: Database connection failed (service unavailable)
    - 500: Unexpected error during check
    """
    try:
        db_status = check_database_connection()

        # Determine appropriate HTTP status code
        if db_status["connected"]:
            http_status = 200
            status = "success"
        else:
            # Service unavailable - database is not accessible
            http_status = 503
            status = "unavailable"

        response = {
            "status": status,
            "database": db_status,
            "timestamp": datetime.now().isoformat(),
        }

        if http_status == 200:
            return response
        else:
            return JSONResponse(response, status_code=http_status)

    except Exception as e:
        logger.error(f"Error checking database connection: {e}")
        return JSONResponse(
            {
                "status": "error",
                "message": "Internal error during database check",
                "timestamp": datetime.now().isoformat(),
            },
            status_code=500,
        )


@rt("/api/synapse", methods=["POST"])
async def synapse(req):
    """Endpoint principal que recibe datos de tu web."""
    # Validate shared secret for production security
    if not validate_shared_secret(req):
        logger.warning("[BLOCKED] Unauthorized synapse request")
        return JSONResponse({"error": "Unauthorized", "status": "error"}, status_code=401)

    try:
        form = await req.form()
        user_input = form.get("input", "")

        if not user_input:
            return {"error": "Cortex recibio senal vacia", "status": "error"}

        # Get context limit from environment
        context_limit = int(os.getenv("MEMORY_CONTEXT_LIMIT", "5"))

        # Recuperar memoria a corto plazo
        context = get_last_thoughts(context_limit)

        # Pensar y clasificar
        classification = brain.fast_classify(user_input)
        intent = (
            classification["intent"]
            if isinstance(classification, dict)
            else classification
        )
        confidence = (
            classification.get("confidence", 0.8)
            if isinstance(classification, dict)
            else 0.8
        )

        response_text = brain.think(user_input, context)

        # Guardar en memoria
        save_thought(user_input, response_text, intent)

        # Responder a la web
        return {
            "status": "success",
            "intent": intent,
            "confidence": confidence,
            "response": response_text,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {"error": str(e), "status": "error"}


@rt("/api/memory/search")
async def memory_search(req):
    """Search through stored memories."""
    if not validate_shared_secret(req):
        logger.warning("[BLOCKED] Unauthorized memory search attempt")
        return JSONResponse({"error": "Unauthorized", "status": "error"}, status_code=401)

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
            "results": results,
        }
    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        return {"error": str(e), "status": "error"}


@rt("/api/memory/stats")
async def memory_stats(req):
    """Get memory statistics."""
    if not validate_shared_secret(req):
        logger.warning("[BLOCKED] Unauthorized memory stats attempt")
        return JSONResponse({"error": "Unauthorized", "status": "error"}, status_code=401)

    try:
        stats = get_memory_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        return {"error": str(e), "status": "error"}


@rt("/api/memory/cleanup", methods=["POST"])
async def memory_cleanup(req):
    """Cleanup old memories."""
    if not validate_shared_secret(req):
        logger.warning("[BLOCKED] Unauthorized memory cleanup attempt")
        return JSONResponse({"error": "Unauthorized", "status": "error"}, status_code=401)

    try:
        form = await req.form()
        days = int(form.get("days", os.getenv("MEMORY_ARCHIVE_DAYS", "30")))

        deleted_count = cleanup_old_thoughts(days)
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"Cleaned up {deleted_count} thoughts older than {days} days",
        }
    except Exception as e:
        logger.error(f"Error cleaning up memory: {e}")
        return {"error": str(e), "status": "error"}


@rt("/api/memory/by-intent/{intent}")
async def memory_by_intent(intent: str, req):
    """Get memories filtered by intent."""
    if not validate_shared_secret(req):
        logger.warning("[BLOCKED] Unauthorized memory by-intent attempt")
        return JSONResponse({"error": "Unauthorized", "status": "error"}, status_code=401)

    try:
        # Make limit configurable via query parameter
        limit = int(req.query_params.get("limit", "10"))
        results = get_thoughts_by_intent(intent.upper(), limit)
        return {
            "status": "success",
            "intent": intent.upper(),
            "count": len(results),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Error retrieving memories by intent: {e}")
        return JSONResponse({"error": str(e), "status": "error"}, status_code=500)


@rt("/credenciales")
def credenciales():
    """Panel de gestion de credenciales minimalista."""
    try:
        # Get current values (masked)
        shared_secret = os.getenv("AMA_SHARED_SECRET", "")
        fernet_key = os.getenv("FERNET_KEY", "")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1")

        # Mask secrets for display
        shared_secret_display = (
            shared_secret[:8] + "..." if len(shared_secret) > 8 else shared_secret
        )
        fernet_key_display = (
            fernet_key[:8] + "..." if len(fernet_key) > 8 else "(vacio)"
        )

        warnings = get_security_warnings()
        warning_html = ""
        if warnings:
            warning_html = Div(
                *[
                    P(
                        w,
                        style="color: #dc2626; background: #fef2f2; padding: 8px; border-radius: 4px; margin: 5px 0;",
                    )
                    for w in warnings
                ],
                style="margin-bottom: 20px;",
            )

        return Titled(
            "[LOCK] Gestion de Credenciales - AMA-Intent v3",
            Div(
                H1("[LOCK] Panel de Credenciales"),
                P(
                    "Gestiona las claves criticas del sistema. Los cambios se aplican inmediatamente (hot reload).",
                    style="color: #6b7280; margin-bottom: 20px;",
                ),
                warning_html,
                Form(
                    Div(
                        Label(
                            "AMA_SHARED_SECRET:",
                            style="font-weight: bold; display: block; margin-top: 15px;",
                        ),
                        P(
                            f"Valor actual: {shared_secret_display}",
                            style="color: #6b7280; font-size: 0.9em;",
                        ),
                        Input(
                            type="password",
                            name="ama_shared_secret",
                            placeholder="Dejar vacio para no cambiar",
                            style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;",
                        ),
                        P(
                            "Secreto compartido para autenticacion del bridge",
                            style="color: #6b7280; font-size: 0.85em; margin-top: 5px;",
                        ),
                    ),
                    Div(
                        Label(
                            "FERNET_KEY:",
                            style="font-weight: bold; display: block; margin-top: 15px;",
                        ),
                        P(
                            f"Valor actual: {fernet_key_display}",
                            style="color: #6b7280; font-size: 0.9em;",
                        ),
                        Input(
                            type="password",
                            name="fernet_key",
                            placeholder="Dejar vacio para no cambiar",
                            style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;",
                        ),
                        P(
                            "Clave de encriptacion Fernet (opcional)",
                            style="color: #6b7280; font-size: 0.85em; margin-top: 5px;",
                        ),
                    ),
                    Div(
                        Label(
                            "OLLAMA_MODEL:",
                            style="font-weight: bold; display: block; margin-top: 15px;",
                        ),
                        P(
                            f"Valor actual: {ollama_model}",
                            style="color: #6b7280; font-size: 0.9em;",
                        ),
                        Input(
                            type="text",
                            name="ollama_model",
                            placeholder="llama3.1",
                            style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;",
                        ),
                        P(
                            "Modelo de Ollama a utilizar",
                            style="color: #6b7280; font-size: 0.85em; margin-top: 5px;",
                        ),
                    ),
                    Button(
                        "[SAVE] Guardar y Recargar",
                        type="submit",
                        style=(
                            "margin-top: 20px; padding: 10px 20px; background: #2563eb; "
                            "color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;"
                        ),
                    ),
                    action="/api/credenciales/save",
                    method="POST",
                    style="max-width: 600px;",
                ),
                P(A("[ARROW] Volver al Admin", href="/admin"), style="margin-top: 30px;"),
                style="background: #ffffff; padding: 30px; font-family: sans-serif; max-width: 800px; margin: 0 auto;",
            ),
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
            env_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
            )
            # Create .env from .env.example if it doesn't exist
            env_example_path = env_path + ".example"
            if os.path.exists(env_example_path) and not os.path.exists(env_path):
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
                return Titled(
                    "Error de Validacion",
                    Div(
                        H1("[X] Error"),
                        P(
                            "La clave FERNET_KEY proporcionada no es valida.",
                            style="color: #dc2626;",
                        ),
                        P(
                            f"Detalle: {str(e)}",
                            style="color: #6b7280; font-size: 0.9em;",
                        ),
                        P(
                            A("[ARROW] Volver", href="/credenciales"),
                            style="margin-top: 20px;",
                        ),
                    ),
                )

        # Update OLLAMA_MODEL if provided
        ollama_model = form.get("ollama_model", "").strip()
        if ollama_model:
            set_key(env_path, "OLLAMA_MODEL", ollama_model)
            updated_keys.append("OLLAMA_MODEL")

        # Hot reload environment variables
        reload_env()

        logger.info(f"[OK] Credentials updated: {', '.join(updated_keys)}")

        return Titled(
            "[OK] Credenciales Actualizadas",
            Div(
                H1("[OK] Cambios Guardados"),
                P(
                    f"Las siguientes claves han sido actualizadas: {', '.join(updated_keys)}",
                    style="color: #059669; font-weight: bold;",
                ),
                P(
                    "Los cambios se han aplicado inmediatamente sin reiniciar el servidor.",
                    style="color: #6b7280; margin-top: 10px;",
                ),
                P(
                    A("[ARROW] Volver al panel", href="/credenciales"),
                    " | ",
                    A("Ver Admin", href="/admin"),
                    style="margin-top: 20px;",
                ),
                style=(
                    "background: #f0fdf4; padding: 30px; border: 2px solid #059669; "
                    "border-radius: 8px; max-width: 600px; margin: 50px auto;"
                ),
            ),
        )
    except Exception as e:
        logger.error(f"Error saving credentials: {e}")
        return Titled(
            "Error",
            Div(
                H1("[X] Error al Guardar"),
                P(f"Error: {str(e)}", style="color: #dc2626;"),
                P(A("[ARROW] Volver", href="/credenciales"), style="margin-top: 20px;"),
            ),
        )


@rt("/admin")
def admin():
    """Admin dashboard with system statistics."""
    try:
        stats = get_memory_stats()
        warnings = get_security_warnings()
        db_status = check_database_connection()

        # Build warning display
        warning_elements = []
        if warnings:
            warning_elements.append(
                H2("[WARNING] Advertencias de Seguridad", style="color: #d97706;")
            )
            for warning in warnings:
                warning_elements.append(
                    P(
                        warning,
                        style="color: #dc2626; background: #fef2f2; padding: 8px; border-radius: 4px;",
                    )
                )
        else:
            warning_elements.append(
                P("[OK] No hay advertencias de seguridad", style="color: #059669;")
            )

        # Build database status display
        db_color = "#059669" if db_status["connected"] else "#dc2626"
        db_bg = "#f0fdf4" if db_status["connected"] else "#fef2f2"
        db_icon = "[OK]" if db_status["connected"] else "[X]"

        # Build database details elements
        db_details = [
            P(
                f"{db_icon} Tipo: {db_status['type'].upper()}",
                style="margin: 5px 0;",
            ),
            P(f"Conexion: {db_status['message']}", style="margin: 5px 0;"),
        ]

        # Add error type if present
        if db_status.get("error_type"):
            db_details.append(
                P(
                    f"Error Type: {db_status['error_type']}",
                    style="margin: 5px 0; font-weight: bold;",
                )
            )

        # Add details if present
        if db_status.get("details"):
            db_details.append(
                P(
                    f"Details: {db_status['details']}",
                    style="margin: 5px 0; font-size: 0.9em;",
                )
            )

        return Titled(
            "AMA-Intent v3 - Admin Dashboard",
            Div(
                H1("[BRAIN] Sistema de Administracion"),
                *warning_elements,
                H2("[DISK] Estado de la Base de Datos"),
                Div(
                    *db_details,
                    style=(
                        f"background: {db_bg}; color: {db_color}; padding: 15px; "
                        f"border-radius: 8px; margin: 15px 0; border: 2px solid {db_color};"
                    ),
                ),
                H2("[STATS] Estadisticas de Memoria"),
                P(f"Total de interacciones: {stats['total_interactions']}"),
                P(f"Por intencion: {stats['by_intent']}"),
                P(f"Primera interaccion: {stats['first_interaction'] or 'N/A'}"),
                P(f"Ultima interaccion: {stats['last_interaction'] or 'N/A'}"),
                H2("[WRENCH] Endpoints API"),
                Ul(
                    Li("GET /api/health - Health check con autenticacion"),
                    Li("GET /api/db/check - Verificar conexion a base de datos"),
                    Li(
                        "POST /api/synapse - Procesamiento principal (requiere secreto)"
                    ),
                    Li("GET /api/memory/search?q=query - Buscar en memoria"),
                    Li("GET /api/memory/stats - Estadisticas de memoria"),
                    Li("POST /api/memory/cleanup - Limpiar memorias antiguas"),
                    Li("GET /api/memory/by-intent/{intent} - Filtrar por intencion"),
                ),
                H2("[LOCK] Gestion"),
                P(
                    A("Panel de Credenciales", href="/credenciales"),
                    " - Gestionar claves del sistema",
                ),
                style="background: #f5f5f5; padding: 20px; font-family: sans-serif;",
            ),
        )
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        return Titled("Error", P(f"Error: {str(e)}"))


if __name__ == "__main__":
    # Get configuration from environment variables with secure defaults
    host = os.getenv("HOST", "127.0.0.1")  # Default to localhost for security
    port = int(os.getenv("PORT", "5001"))
    reload = (
        os.getenv("RELOAD", "false").lower() == "true"
    )  # Default to false for production

    uvicorn.run("bridge.server:app", host=host, port=port, reload=reload)
