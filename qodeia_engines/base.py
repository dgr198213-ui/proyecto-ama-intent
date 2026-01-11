from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class EngineResult:
    """Resultado estandarizado de ejecución de motor"""

    ok: bool
    engine: str
    ts: float = field(default_factory=lambda: time.time())
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    trace: Optional[str] = None

    def __getitem__(self, key):
        """Permite acceso tipo diccionario para compatibilidad"""
        if key in self.data:
            return self.data[key]
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __contains__(self, key):
        return key in self.data or hasattr(self, key)

    def __len__(self):
        return len(self.data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "engine": self.engine,
            "ts": self.ts,
            "data": self.data,
            "error": self.error,
            "trace": self.trace,
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
                ok=False, engine=self.name, error=str(e), trace=traceback.format_exc()
            )

    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Implementación específica del motor (override)"""
        raise NotImplementedError(f"{self.name} must implement _run()")

    def info(self) -> Dict[str, str]:
        """Información del motor"""
        return {
            "name": self.name,
            "version": self.version,
            "class": self.__class__.__name__,
        }
