import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.utils import stable_hash

class AMAGovernance:
    def __init__(self):
        self.policy = "deterministic-governance-v2"

    def _infer_intent(self, text):
        text = text.lower()
        if any(word in text for word in ["buscar", "search", "encuentra", "documentos"]):
            return "search"
        if any(word in text for word in ["simula", "simulate", "ejecuta", "corre"]):
            return "simulate"
        if any(word in text for word in ["optimiza", "mejora", "optimize"]):
            return "optimize"
        if any(word in text for word in ["analiza", "diagnostica", "analyze"]):
            return "analyze"
        return "general"

    def _basic_risk_score(self, text):
        score = 0.0
        # Detectar patrones sospechosos
        dangerous_patterns = ["password", "contraseña", "rm -rf", "sudo", "delete all", "drop table"]
        for pattern in dangerous_patterns:
            if pattern in text.lower():
                score += 0.4 # Aumentado para que dos patrones o uno crítico lleguen a high
        return min(1.0, score)

    def run(self, payload):
        text = payload.get("text", "")
        intent = self._infer_intent(text)
        risk_score = self._basic_risk_score(text)
        
        return {
            "audit_id": stable_hash(payload),
            "intent": intent,
            "risk_score": risk_score,
            "risk_level": "high" if risk_score > 0.7 else "medium" if risk_score > 0.3 else "low",
            "len": len(text),
            "policy": self.policy
        }
