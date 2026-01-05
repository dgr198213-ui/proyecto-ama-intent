from __future__ import annotations
from typing import Dict, Any, List
from .base import BaseEngine
from .utils import tokenize, mean

class CognitiveBrainEngine(BaseEngine):
    """
    Cerebro Cognitivo para AMA-Intent
    
    Implementa:
    - Working Memory (últimos 20 inputs)
    - Sistema de decisión por confianza
    - Análisis de tokens
    """
    name = "Cognitive-Brain"
    version = "1.0.0"
    
    def __init__(self, wm_size: int = 20):
        self.wm_size = int(wm_size)
        self.working_memory: List[Dict[str, Any]] = []
    
    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = str(payload.get("text", ""))
        toks = tokenize(text)
        
        # Actualizar working memory
        self._push_wm({"text": text, "tokens": toks})
        
        # Decisión basada en contenido
        action, confidence = self._decide(toks, payload)
        
        payload_out = dict(payload)
        payload_out["cognitive"] = {
            "tokens": toks[:200],
            "wm_len": len(self.working_memory),
            "action": action,
            "confidence": confidence,
            "context_depth": min(len(self.working_memory), self.wm_size)
        }
        return payload_out
    
    def _push_wm(self, item: Dict[str, Any]) -> None:
        """Añade item a working memory (FIFO)"""
        self.working_memory.append(item)
        if len(self.working_memory) > self.wm_size:
            self.working_memory = self.working_memory[-self.wm_size:]
    
    def _decide(self, toks: List[str], payload: Dict[str, Any]) -> tuple:
        """Decide acción y confianza basado en tokens"""
        if not toks:
            return ("idle", 0.2)
        
        # Patrones de acción
        patterns = {
            "search": ["buscar", "search", "bdc", "encontrar"],
            "simulate": ["simular", "simulation", "simulación", "ejecutar"],
            "optimize": ["optimizar", "mejorar", "performance", "rendimiento"],
            "analyze": ["analizar", "análisis", "diagnosticar", "revisar"]
        }
        
        for action, keywords in patterns.items():
            if any(t in toks for t in keywords):
                # Confianza basada en múltiples matches
                matches = sum(1 for k in keywords if k in toks)
                confidence = min(0.95, 0.65 + 0.1 * matches)
                return (action, confidence)
        
        # Confianza por densidad de señal
        density = min(1.0, len(set(toks)) / max(1.0, len(toks)))
        return ("general", 0.5 + 0.4 * density)
    
    def get_context(self, n: int = 5) -> List[str]:
        """Obtiene últimos N textos del working memory"""
        return [item["text"] for item in self.working_memory[-n:]]
