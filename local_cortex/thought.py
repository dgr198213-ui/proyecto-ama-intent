import logging
import os
import time

import ollama

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level), format="%(message)s")
logger = logging.getLogger(__name__)


class LocalBrain:
    def __init__(self, model=None, max_retries=3, retry_delay=2):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1")
        self.system_prompt = """
        Eres AMA-Intent v3. Eres un sistema de inteligencia biomimética local.
        Tu "cuerpo" es este servidor local. Tu "mente" es Qodeia.com.
        Responde de forma técnica, precisa y sin relleno.
        Si te piden código, da solo el código.
        """

    def _call_ollama(self, func, **kwargs):
        """Wrapper para llamadas a Ollama con reintentos."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return func(**kwargs)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"⚠️ Error en Ollama (intento {attempt+1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

        logger.error(f"❌ Fallo definitivo tras {self.max_retries} intentos: {last_error}")
        raise last_error

    def think(self, user_input, context=""):
        """Procesa el input del usuario usando el modelo local."""
        logger.info(f"⚡ [Cortex] Procesando: {user_input[:40]}...")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": f"Contexto previo: {context}\n\nPregunta: {user_input}",
            },
        ]

        response = self._call_ollama(
            ollama.chat, model=self.model, messages=messages
        )
        return response["message"]["content"]

    def fast_classify(self, text):
        """Decide qué tipo de tarea es sin gastar mucha energía."""
        res = self._call_ollama(
            ollama.generate,
            model=self.model,
            prompt=f"Clasifica en una palabra [CODIGO, CHAT, ANALISIS]: {text}",
        )
        classification = res["response"].strip().upper()

        # Extract confidence if model provides it, otherwise return default
        confidence = 0.8  # Default confidence

        # Return structured classification
        return {"intent": classification, "confidence": confidence}
