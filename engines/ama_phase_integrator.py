import time


class AMAPhaseIntegrator:
    def __init__(self, bus):
        self.bus = bus
        self.short_term = []
        self.medium_term = []
        self.long_term = []
        self.st_limit = 10
        self.mt_limit = 100

    def fase1_process(self, user_input):
        # Gobernanza y Seguridad
        payload = {"text": user_input}
        ama_g_out = self.bus.call("AMA-G", payload)

        # Registro en memoria corto plazo
        self.short_term.append(
            {
                "input": user_input,
                "audit_id": ama_g_out["audit_id"],
                "timestamp": time.time(),
            }
        )
        if len(self.short_term) > self.st_limit:
            old = self.short_term.pop(0)
            self.medium_term.append(old)
            if len(self.medium_term) > self.mt_limit:
                self.medium_term.pop(0)

        return ama_g_out

    def fase2_process(self, fase1_output, user_input):
        # Análisis Cognitivo
        payload = {"text": user_input, "intent": fase1_output["intent"]}
        cognitive_out = self.bus.call("Cognitive-Brain", payload)

        # Búsqueda si aplica
        search_results = []
        if cognitive_out["action"] == "search":
            search_results = self.bus.call(
                "BDC-Search", {"op": "search", "query": user_input, "k": 3}
            )

        return {"cognitive": cognitive_out, "search_results": search_results}

    def fase3_process(self, fase2_output, alternatives=None):
        # Decisiones Multi-Criterio (si hay alternativas)
        dmd_out = None
        if alternatives:
            weights = {"relevancia": 0.5, "claridad": 0.3, "completitud": 0.2}
            dmd_out = self.bus.call(
                "DMD", {"alternatives": alternatives, "weights": weights}
            )

        # Evaluación LFPI (simulada para el ejemplo)
        lfpi_out = self.bus.call(
            "LFPI", {"gain": 0.8, "loss": 0.1, "feedback": 0.7, "amplitude": 1.0}
        )

        return {
            "dmd": dmd_out,
            "lfpi": lfpi_out,
            "best_response": (
                dmd_out["best"] if dmd_out else "Respuesta generada por defecto"
            ),
        }

    def process_full(self, user_input, alternatives=None):
        start_time = time.time()

        f1 = self.fase1_process(user_input)
        f2 = self.fase2_process(f1, user_input)
        f3 = self.fase3_process(f2, alternatives)

        duration = time.time() - start_time

        return {
            "fase1": f1,
            "fase2": f2,
            "fase3": f3,
            "performance": {"total_time_ms": duration * 1000},
        }

    def run(self, payload):
        user_input = payload.get("text", "")
        alternatives = payload.get("alternatives")
        return self.process_full(user_input, alternatives)
