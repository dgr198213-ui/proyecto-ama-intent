from fasthtml.common import *
from local_cortex.thought import LocalBrain
from local_cortex.memory import (
    init_db, save_thought, get_last_thoughts,
    search_thoughts, get_memory_stats, cleanup_old_thoughts,
    get_thoughts_by_intent
)
from datetime import datetime
import uvicorn
import os
import logging

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Inicialización del sistema
init_db()
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


@rt("/api/synapse", methods=["POST"])
async def synapse(req):
    """Endpoint principal que recibe datos de tu web."""
    try:
        form = await req.form()
        user_input = form.get("input", "")

        if not user_input:
            return JSONResponse({"error": "Cortex recibió señal vacía"}, status_code=400)

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
        return JSONResponse({"error": str(e), "status": "error"}, status_code=500)


@rt("/api/memory/search")
async def memory_search(req):
    """Search through stored memories."""
    try:
        query = req.query_params.get("q", "")
        limit = int(req.query_params.get("limit", "10"))
        
        if not query:
            return JSONResponse({"error": "Query parameter 'q' is required"}, status_code=400)
        
        results = search_thoughts(query, limit)
        return {
            "status": "success",
            "query": query,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        return JSONResponse({"error": str(e), "status": "error"}, status_code=500)


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
        return JSONResponse({"error": str(e), "status": "error"}, status_code=500)


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
        return JSONResponse({"error": str(e), "status": "error"}, status_code=500)


@rt("/api/memory/by-intent/{intent}")
async def memory_by_intent(intent: str):
    """Get memories filtered by intent."""
    try:
        limit = 10
        results = get_thoughts_by_intent(intent.upper(), limit)
        return {
            "status": "success",
            "intent": intent.upper(),
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error retrieving memories by intent: {e}")
        return JSONResponse({"error": str(e), "status": "error"}, status_code=500)


@rt("/admin")
def admin():
    """Admin dashboard with system statistics."""
    try:
        stats = get_memory_stats()
        return Titled("AMA-Intent v3 - Admin Dashboard",
                      Div(
                          H1("🧠 Sistema de Administración"),
                          H2("📊 Estadísticas de Memoria"),
                          P(f"Total de interacciones: {stats['total_interactions']}"),
                          P(f"Por intención: {stats['by_intent']}"),
                          P(f"Primera interacción: {stats['first_interaction'] or 'N/A'}"),
                          P(f"Última interacción: {stats['last_interaction'] or 'N/A'}"),
                          H2("🔧 Endpoints API"),
                          Ul(
                              Li("POST /api/synapse - Procesamiento principal"),
                              Li("GET /api/memory/search?q=query - Buscar en memoria"),
                              Li("GET /api/memory/stats - Estadísticas de memoria"),
                              Li("POST /api/memory/cleanup - Limpiar memorias antiguas"),
                              Li("GET /api/memory/by-intent/{intent} - Filtrar por intención")
                          ),
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
