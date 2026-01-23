from fasthtml.common import *
from local_cortex.thought import LocalBrain
from local_cortex.memory import init_db, save_thought, get_last_thoughts
from datetime import datetime
import uvicorn
import os

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
    form = await req.form()
    user_input = form.get("input", "")

    if not user_input:
        return {"error": "Cortex recibió señal vacía"}

    # Recuperar memoria a corto plazo
    context = get_last_thoughts()

    # Pensar
    intent = brain.fast_classify(user_input)
    response_text = brain.think(user_input, context)

    # Guardar en memoria
    save_thought(user_input, response_text, intent)

    # Responder a la web
    return {
        "status": "success",
        "intent": intent,
        "response": response_text,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Get configuration from environment variables with secure defaults
    host = os.getenv("HOST", "127.0.0.1")  # Default to localhost for security
    port = int(os.getenv("PORT", "5001"))
    reload = os.getenv("RELOAD", "false").lower() == "true"  # Default to false for production

    uvicorn.run("bridge.server:app", host=host, port=port, reload=reload)
