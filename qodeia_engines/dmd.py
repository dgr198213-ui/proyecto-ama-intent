from __future__ import annotations

from typing import Any, Dict, List

from .base import BaseEngine


class DMDEngine(BaseEngine):
    """
    DMD: Decision Matrix Driver

    Selecciona la mejor alternativa basada en pesos y criterios.
    """

    name = "DMD"
    version = "1.0.0"

    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        alternatives = payload.get("alternatives", [])
        weights = payload.get("weights", {"relevancia": 1.0})

        if not alternatives:
            return {"dmd": {"best": None, "scores": []}}

        scored = []
        for alt in alternatives:
            score = 0.0
            for criterion, weight in weights.items():
                # Intentar obtener de 'criteria' o 'metrics'
                val = alt.get("criteria", {}).get(criterion)
                if val is None:
                    val = alt.get("metrics", {}).get(criterion, 0.5)
                score += val * weight

            scored.append(
                {"name": alt.get("name", "unknown"), "score": score, "data": alt}
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        best_name = scored[0]["name"]
        return {"best": best_name, "dmd": {"best": scored[0], "scores": scored}}
