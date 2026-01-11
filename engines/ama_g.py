import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engines.ama_intent import RequestType, extract_intent


class AMAGovernance:
    def __init__(self):
        self.policy = "deterministic-governance-v2"

    def _basic_risk_score(self, text):
        score = 0.0
        # Detectar patrones sospechosos
        dangerous_patterns = [
            "password",
            "contraseña",
            "rm -rf",
            "sudo",
            "delete all",
            "drop table",
        ]
        for pattern in dangerous_patterns:
            if pattern in text.lower():
                score += 0.4
        return min(1.0, score)

    def run(self, payload):
        text = payload.get("text", "")

        # Usar el nuevo módulo de intención
        intent_obj = extract_intent(text)

        risk_score = self._basic_risk_score(text)

        return {
            "audit_id": intent_obj.intent_hash,
            "intent": intent_obj.request_type.value,
            "intent_details": {
                "type": intent_obj.request_type.value,
                "goal": intent_obj.core_goal,
                "entities": intent_obj.key_entities,
                "ambiguity": intent_obj.ambiguity_score,
                "complexity": intent_obj.complexity_score,
            },
            "risk_score": risk_score,
            "risk_level": (
                "high" if risk_score > 0.7 else "medium" if risk_score > 0.3 else "low"
            ),
            "len": len(text),
            "policy": self.policy,
        }
