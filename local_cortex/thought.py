import ollama


class LocalBrain:
    def __init__(self, model="llama3.1"):
        self.model = model
        self.system_prompt = """
        Eres AMA-Intent v3. Eres un sistema de inteligencia biomimética local.
        Tu "cuerpo" es este servidor local. Tu "mente" es Qodeia.com.
        Responde de forma técnica, precisa y sin relleno.
        Si te piden código, da solo el código.
        """

    def think(self, user_input, context=""):
        """Procesa el input del usuario usando el modelo local."""
        print(f"⚡ [Cortex] Procesando: {user_input[:40]}...")

        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': f"Contexto previo: {context}\n\nPregunta: {user_input}"}
        ]

        response = ollama.chat(model=self.model, messages=messages)
        return response['message']['content']

    def fast_classify(self, text):
        """Decide qué tipo de tarea es sin gastar mucha energía."""
        res = ollama.generate(model=self.model, prompt=f"Clasifica en una palabra [CODIGO, CHAT, ANALISIS]: {text}")
        return res['response'].strip().upper()
