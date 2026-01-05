from __future__ import annotations
from typing import Dict, Any, List
from .base import BaseEngine
from .utils import clamp, mean

class AdaptivePruningEngine(BaseEngine):
    """
    Adaptive Pruning: Consolidación inteligente de memoria

    Compatible con consolidate_nightly() del integrador:
    - Espera items con importance (0..1) y usage (0..1)
    - Usa alpha/beta/threshold
    - Devuelve kept/removed + métricas (efficiency, mean_score)
    """
    name = "Adaptive-Pruning"
    version = "1.1.0"

    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        items: List[Dict[str, Any]] = list(payload.get("items", []) or [])
        alpha = float(payload.get("alpha", 0.6))
        beta = float(payload.get("beta", 0.4))
        threshold = float(payload.get("threshold", 0.5))

        scored: List[Dict[str, Any]] = []
        for it in items:
            importance = float(it.get("importance", 0.5))
            usage = float(it.get("usage", 0.5))
            prune_score = clamp(alpha * importance + beta * usage, 0.0, 1.0)

            it2 = dict(it)
            it2["prune_score"] = prune_score
            scored.append(it2)

        kept = [it for it in scored if it["prune_score"] >= threshold]
        removed = [it for it in scored if it["prune_score"] < threshold]

        scores = [it["prune_score"] for it in scored]
        mean_score = mean(scores) if scores else 0.0
        efficiency = (len(kept) / len(scored)) if scored else 0.0

        return {
            "pruning": {
                "original_count": len(scored),
                "kept": kept,
                "removed": removed,
                "kept_count": len(kept),
                "removed_count": len(removed),
                "threshold": threshold,
                "alpha": alpha,
                "beta": beta,
                "mean_score": mean_score,
                "efficiency": efficiency,
            }
        }
