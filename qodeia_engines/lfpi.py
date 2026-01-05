from __future__ import annotations
from typing import Dict, Any
from .base import BaseEngine
from .utils import clamp

class LFPIEngine(BaseEngine):
    """
    LFPI: Linear Functional Performance Index
    """
    name = "LFPI"
    version = "1.0.0"
    
    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        gain = payload.get("gain", 0.0)
        loss = payload.get("loss", 0.0)
        feedback = payload.get("feedback", 0.0)
        amplitude = payload.get("amplitude", 1.0)
        
        value = 100 * (gain - loss + amplitude * feedback)
        score = clamp(value, 0, 100)
        
        level = (
            "excellent" if score >= 80 else
            "good" if score >= 60 else
            "fair" if score >= 40 else
            "poor"
        )
        
        return {
            "lfpi": {
                "value": score,
                "level": level,
                "gain": gain,
                "loss": loss
            }
        }
