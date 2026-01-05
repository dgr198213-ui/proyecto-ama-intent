from __future__ import annotations
from typing import Dict, Any, List, Optional
from .base import BaseEngine, EngineResult

class EngineBus:
    """
    Bus de orquestación de motores.
    
    Permite:
    - Registro dinámico de motores
    - Ejecución individual o en pipeline
    - Logging completo de operaciones
    - Métricas de rendimiento
    """
    
    def __init__(self):
        self._engines: Dict[str, BaseEngine] = {}
        self._log: List[EngineResult] = []
        self._metrics = {"calls": 0, "errors": 0, "avg_time": 0.0}
    
    @property
    def log(self) -> List[EngineResult]:
        """Historial completo de ejecuciones"""
        return list(self._log)
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Métricas agregadas"""
        return dict(self._metrics)
    
    def register(self, engine: BaseEngine) -> None:
        """Registra motor en el bus"""
        self._engines[engine.name] = engine
        print(f"[BUS] Registrado: {engine.name}")
    
    def has(self, name: str) -> bool:
        """Verifica si motor está registrado"""
        return name in self._engines
    
    def list_engines(self) -> List[str]:
        """Lista todos los motores disponibles"""
        return list(self._engines.keys())
    
    def call(self, name: str, payload: Optional[Dict[str, Any]] = None) -> EngineResult:
        """Ejecuta motor específico"""
        import time
        start = time.time()
        
        if name not in self._engines:
            res = EngineResult(
                ok=False, 
                engine=name, 
                error=f"Engine '{name}' not registered"
            )
            self._log.append(res)
            self._metrics["errors"] += 1
            return res
        
        res = self._engines[name].run(payload or {})
        elapsed = time.time() - start
        
        self._log.append(res)
        self._metrics["calls"] += 1
        if not res.ok:
            self._metrics["errors"] += 1
        
        # Actualizar promedio de tiempo
        n = self._metrics["calls"]
        self._metrics["avg_time"] = (
            (self._metrics["avg_time"] * (n-1) + elapsed) / n
        )
        
        return res
    
    def pipeline(self, names: List[str], payload: Dict[str, Any]) -> EngineResult:
        """Ejecuta pipeline secuencial de motores"""
        cur = dict(payload or {})
        last = None
        
        for n in names:
            last = self.call(n, cur)
            if not last.ok:
                return last  # Fallo inmediato
            # Merge para chaining
            cur.update(last.data or {})
        
        return last if last else EngineResult(
            ok=True, 
            engine="pipeline", 
            data=cur
        )
    
    def export_log(self, path: str):
        """Exporta log a JSON"""
        import json
        with open(path, 'w') as f:
            json.dump([r.to_dict() for r in self._log], f, indent=2)
