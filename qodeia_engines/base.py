from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time
import traceback

@dataclass
class EngineResult:
    """Resultado estandarizado de ejecución de motor"""
    ok: bool
    engine: str
    ts: float = field(default_factory=lambda: time.time())
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "engine": self.engine,
            "ts": self.ts,
            "data": self.data,
            "error": self.error,
            "trace": self.trace
        }

class BaseEngine:
    """
    Interfaz base para todos los motores Qodeia.
    
    Garantiza:
    - Manejo de errores unificado
    - Logging consistente
    - Resultados estandarizados
    """
    name: str = "BaseEngine"
    version: str = "1.0.0"
    
    def run(self, payload: Dict[str, Any]) -> EngineResult:
        """Ejecuta motor con manejo de errores automático"""
        try:
            out = self._run(payload or {})
            if isinstance(out, EngineResult):
                return out
            return EngineResult(ok=True, engine=self.name, data=dict(out or {}))
        except Exception as e:
            return EngineResult(
                ok=False,
                engine=self.name,
                error=str(e),
                trace=traceback.format_exc()
            )
    
    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Implementación específica del motor (override)"""
        raise NotImplementedError(f"{self.name} must implement _run()")
    
    def info(self) -> Dict[str, str]:
        """Información del motor"""
        return {
            "name": self.name,
            "version": self.version,
            "class": self.__class__.__name__
        }
