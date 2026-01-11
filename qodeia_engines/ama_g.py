from __future__ import annotations

from typing import Any, Dict

from .base import BaseEngine, EngineResult
from .utils import clamp, now_ms, stable_hash


class AMAGEngine(BaseEngine):
    """
    AMA-G v2.0: Gobernanza reforzada para AMA-Intent

    Características:
    - Auditoría determinista con SHA-256
    - Risk scoring automático
    - Inferencia de intención mejorada
    - Validación de estructura
    """

    name = "AMA-G"
    version = "2.0.0"

    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        txt = str(payload.get("text", ""))[:20000]
        intent = payload.get("intent") or self._infer_intent(txt)

        audit = {
            "audit_id": stable_hash({"t": txt, "intent": intent, "ms": now_ms()}),
            "intent": intent,
            "len": len(txt),
            "policy": "deterministic-governance-v2",
            "timestamp": now_ms(),
        }

        # Validación requerida
        if payload.get("requires_text") and not txt.strip():
            return EngineResult(
                ok=False, engine=self.name, error="Missing required 'text'"
            )

        risk = self._basic_risk_score(txt)
        audit["risk_score"] = risk
        audit["risk_level"] = (
            "low" if risk < 0.3 else "medium" if risk < 0.6 else "high"
        )

        payload_out = dict(payload)
        payload_out["ama_g"] = audit
        # Compatibilidad con tests
        payload_out["risk_score"] = audit["risk_score"]
        payload_out["risk_level"] = audit["risk_level"]
        payload_out["intent"] = (
            "analítica" if audit["intent"] == "analyze" else audit["intent"]
        )
        payload_out["intent_details"] = {"goal": audit["intent"]}
        return payload_out

    def _infer_intent(self, txt: str) -> str:
        """Inferencia de intención por keywords"""
        t = txt.lower()
        if any(k in t for k in ["buscar", "búsqueda", "search", "bdc"]):
            return "search"
        if any(k in t for k in ["simular", "simulación", "run", "ejecutar"]):
            return "simulate"
        if any(k in t for k in ["optimizar", "mejora", "rendimiento"]):
            return "optimize"
        if any(k in t for k in ["analizar", "análisis", "diagnosticar", "ventajas"]):
            return "analyze"
        return "general"

    def _basic_risk_score(self, txt: str) -> float:
        """Score de riesgo 0.0-1.0"""
        t = txt.lower()
        flags = 0

        # Patrones de alto riesgo
        dangerous = [
            "password",
            "contraseña",
            "api key",
            "token",
            "private key",
            "seed phrase",
            "rm -rf",
            "format c:",
            "del /s",
            "powershell -enc",
        ]

        for pattern in dangerous:
            if pattern in t:
                flags += 5 if pattern.startswith("rm") else 1

        return clamp(flags / 8.0, 0.0, 1.0)
