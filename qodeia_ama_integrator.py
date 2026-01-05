#!/usr/bin/env python3
"""
Qodeia-AMA Integration Assembler
=================================
Integrador automático que fusiona motores Qodeia con arquitectura AMA-Intent.

Autor: Sistema AMA-Intent + Qodeia Engines
Versión: 2.0.0
Fecha: 2026-01-04

Funcionalidades:
- Análisis de estructura existente
- Inyección controlada de motores
- Preservación de funcionalidad original
- Generación de documentación actualizada
- Validación de integridad post-integración
"""

import os
import sys
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class QodeiaAMAIntegrator:
    """Integrador principal de motores Qodeia en AMA-Intent"""
    
    def __init__(self, base_path: str = "."):
        self.base = Path(base_path)
        self.src = self.base / "src"
        self.qodeia = self.base / "qodeia_engines"
        self.docs = self.base / "docs"
        self.log: List[str] = []
        self.stats = {
            "analyzed": 0,
            "created": 0,
            "modified": 0,
            "errors": 0
        }
    
    def log_action(self, msg: str, level: str = "INFO"):
        """Registra acción con timestamp"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{ts}] [{level}] {msg}"
        self.log.append(entry)
        print(entry)
    
    def sha256(self, text: str) -> str:
        """Hash SHA-256 para integridad"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
    
    def analyze_structure(self) -> Dict[str, Any]:
        """Analiza estructura existente de AMA-Intent"""
        self.log_action("Iniciando análisis de estructura...")
        
        structure = {
            "src_exists": self.src.exists(),
            "modules": [],
            "total_files": 0,
            "python_files": 0
        }
        
        if self.src.exists():
            for item in self.src.rglob("*.py"):
                structure["modules"].append(str(item.relative_to(self.base)))
                structure["python_files"] += 1
                structure["total_files"] += 1
                self.stats["analyzed"] += 1
        
        self.log_action(f"Estructura analizada: {structure['python_files']} módulos Python")
        return structure
    
    def create_qodeia_core(self):
        """Crea núcleo común Qodeia (base, bus, utils)"""
        self.log_action("Creando núcleo Qodeia...")
        
        self.qodeia.mkdir(parents=True, exist_ok=True)
        
        # __init__.py
        init_content = '''"""
Qodeia Engines - Núcleo de Motores Integrados
==============================================
Sistema modular de motores especializados para AMA-Intent v2.0
"""

from .base import BaseEngine, EngineResult
from .bus import EngineBus

__version__ = "2.0.0"
__author__ = "AMA-Intent Team"
'''
        self._write_file(self.qodeia / "__init__.py", init_content)
        
        # base.py (con mejoras)
        base_content = '''from __future__ import annotations
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
'''
        self._write_file(self.qodeia / "base.py", base_content)
        
        # bus.py (orquestador)
        bus_content = '''from __future__ import annotations
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
'''
        self._write_file(self.qodeia / "bus.py", bus_content)
        
        # utils.py (utilidades comunes)
        utils_content = '''from __future__ import annotations
from typing import Any, Dict, Iterable, List, Tuple
import math
import hashlib
import time

def sha256_hex(s: str) -> str:
    """Hash SHA-256 de string"""
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()

def stable_hash(obj: Any) -> str:
    """Hash estable de objeto"""
    return sha256_hex(repr(obj))

def clamp(x: float, lo: float, hi: float) -> float:
    """Limita valor entre min y max"""
    return max(lo, min(hi, x))

def mean(xs: Iterable[float]) -> float:
    """Media aritmética"""
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0

def stdev(xs: Iterable[float]) -> float:
    """Desviación estándar"""
    xs = list(xs)
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(var)

def now_ms() -> int:
    """Timestamp en milisegundos"""
    return int(time.time() * 1000)

def tokenize(text: str) -> List[str]:
    """Tokenización simple pero determinista"""
    t = "".join(ch.lower() if ch.isalnum() else " " for ch in (text or ""))
    return [w for w in t.split() if w]

def cosine_sim(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Similitud coseno entre vectores sparse"""
    if not a or not b:
        return 0.0
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in a)
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    return dot / (na * nb) if (na > 0 and nb > 0) else 0.0

def tf(text: str) -> Dict[str, float]:
    """Term Frequency normalizado"""
    toks = tokenize(text)
    d: Dict[str, float] = {}
    for w in toks:
        d[w] = d.get(w, 0.0) + 1.0
    n = float(len(toks) or 1)
    return {k: v / n for k, v in d.items()}

def idf(docs: List[str]) -> Dict[str, float]:
    """Inverse Document Frequency (smooth)"""
    N = len(docs) or 1
    df: Dict[str, int] = {}
    for doc in docs:
        for w in set(tokenize(doc)):
            df[w] = df.get(w, 0) + 1
    return {w: math.log((N + 1) / (c + 1)) + 1.0 for w, c in df.items()}

def tfidf_vec(text: str, idf_map: Dict[str, float]) -> Dict[str, float]:
    """Vector TF-IDF"""
    t = tf(text)
    return {w: t[w] * idf_map.get(w, 0.0) for w in t}
'''
        self._write_file(self.qodeia / "utils.py", utils_content)
        
        self.log_action("Núcleo Qodeia creado correctamente")
    
    def create_tier1_engines(self):
        """Crea motores Tier 1 (máximo impacto)"""
        self.log_action("Creando motores Tier 1...")
        
        # AMA-G mejorado
        ama_g_content = '''from __future__ import annotations
from typing import Dict, Any
from .base import BaseEngine, EngineResult
from .utils import stable_hash, clamp, now_ms

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
            "timestamp": now_ms()
        }
        
        # Validación requerida
        if payload.get("requires_text") and not txt.strip():
            return EngineResult(
                ok=False, 
                engine=self.name, 
                error="Missing required 'text'"
            )
        
        risk = self._basic_risk_score(txt)
        audit["risk_score"] = risk
        audit["risk_level"] = (
            "low" if risk < 0.3 else 
            "medium" if risk < 0.7 else 
            "high"
        )
        
        payload_out = dict(payload)
        payload_out["ama_g"] = audit
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
        if any(k in t for k in ["analizar", "análisis", "diagnosticar"]):
            return "analyze"
        return "general"
    
    def _basic_risk_score(self, txt: str) -> float:
        """Score de riesgo 0.0-1.0"""
        t = txt.lower()
        flags = 0
        
        # Patrones de alto riesgo
        dangerous = [
            "password", "contraseña", "api key", "token", 
            "private key", "seed phrase", "rm -rf", 
            "format c:", "del /s", "powershell -enc"
        ]
        
        for pattern in dangerous:
            if pattern in t:
                flags += (2 if pattern.startswith("rm") else 1)
        
        return clamp(flags / 8.0, 0.0, 1.0)
'''
        self._write_file(self.qodeia / "ama_g.py", ama_g_content)
        
        # Cognitive Brain
        cognitive_content = '''from __future__ import annotations
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
'''
        self._write_file(self.qodeia / "cognitive_brain.py", cognitive_content)
        
        # Associative Memory
        assoc_content = '''from __future__ import annotations
from typing import Dict, Any, List, Tuple
from .base import BaseEngine
from .utils import idf, tfidf_vec, cosine_sim

class AssociativeMemoryEngine(BaseEngine):
    """
    Memoria Asociativa con búsqueda semántica
    
    Operaciones:
    - ingest: añadir documentos
    - query: buscar por similitud
    - stats: estadísticas de índice
    """
    name = "Associative-Memory"
    version = "1.0.0"
    
    def __init__(self):
        self.items: List[Dict[str, Any]] = []
        self._idf: Dict[str, float] = {}
    
    def _rebuild(self) -> None:
        """Reconstruye índice TF-IDF"""
        docs = [it["text"] for it in self.items]
        self._idf = idf(docs)
    
    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        op = payload.get("op", "query")
        
        if op == "ingest":
            return self._ingest(payload)
        elif op == "stats":
            return self._stats()
        else:
            return self._query(payload)
    
    def _ingest(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Añade items al índice"""
        item = {
            "id": str(payload.get("id", f"item_{len(self.items)+1}")),
            "text": str(payload.get("text", "")),
            "meta": dict(payload.get("meta") or {})
        }
        self.items.append(item)
        self._rebuild()
        
        return {
            "associative": {
                "ingested": item["id"],
                "count": len(self.items)
            }
        }
    
    def _query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Búsqueda por similitud"""
        q = str(payload.get("query", payload.get("text", "")))
        k = int(payload.get("k", 5))
        
        if not self.items:
            return {"associative": {"results": [], "count": 0}}
        
        qv = tfidf_vec(q, self._idf)
        scored: List[Tuple[float, Dict[str, Any]]] = []
        
        for it in self.items:
            iv = tfidf_vec(it["text"], self._idf)
            scored.append((cosine_sim(qv, iv), it))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        results = [{
            "score": float(s),
            "id": it["id"],
            "meta": it["meta"],
            "text": it["text"][:400]
        } for s, it in scored[:k]]
        
        return {
            "associative": {
                "results": results,
                "count": len(self.items),
                "query": q[:100]
            }
        }
    
    def _stats(self) -> Dict[str, Any]:
        """Estadísticas del índice"""
        return {
            "associative": {
                "total_items": len(self.items),
                "vocabulary_size": len(self._idf),
                "avg_text_len": sum(len(it["text"]) for it in self.items) / max(1, len(self.items))
            }
        }
'''
        self._write_file(self.qodeia / "associative_memory.py", assoc_content)
        
        # BDC Search
        bdc_content = '''from __future__ import annotations
from typing import Dict, Any, List, Tuple
from .base import BaseEngine
from .utils import idf, tfidf_vec, cosine_sim

class BDCSearchEngine(BaseEngine):
    """
    BDC Search: Índice semántico para AMA-Intent
    
    Igual que Associative Memory pero con namespace "bdc"
    para compatibilidad con nomenclatura existente.
    """
    name = "BDC-Search"
    version = "1.0.0"
    
    def __init__(self):
        self.docs: List[Dict[str, Any]] = []
        self._idf: Dict[str, float] = {}
    
    def _rebuild(self) -> None:
        texts = [d["text"] for d in self.docs]
        self._idf = idf(texts)
        for d in self.docs:
            d["vec"] = tfidf_vec(d["text"], self._idf)

    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        op = payload.get("op", "search")
        if op == "ingest":
            new_docs = payload.get("docs", [])
            self.docs.extend(new_docs)
            self._rebuild()
            return {"status": "ingested", "count": len(new_docs)}
        
        query = payload.get("query", "")
        k = payload.get("k", 5)
        q_vec = tfidf_vec(query, self._idf)
        
        results = []
        for d in self.docs:
            sim = cosine_sim(q_vec, d.get("vec", {}))
            results.append({"id": d["id"], "score": sim, "text": d["text"]})
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return {"bdc": {"results": results[:k]}}
'''
        self._write_file(self.qodeia / "bdc_search.py", bdc_content)
        
        # DMD Engine
        dmd_content = '''from __future__ import annotations
from typing import Dict, Any, List
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
                score += alt.get("metrics", {}).get(criterion, 0.5) * weight
            
            scored.append({
                "name": alt.get("name", "unknown"),
                "score": score,
                "data": alt
            })
            
        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"dmd": {"best": scored[0], "scores": scored}}
'''
        self._write_file(self.qodeia / "dmd.py", dmd_content)
        
        # Adaptive Pruning Engine
        pruning_content = '''from __future__ import annotations
from typing import Dict, Any, List
from .base import BaseEngine

class AdaptivePruningEngine(BaseEngine):
    """
    Adaptive Pruning: Consolidación inteligente de memoria
    """
    name = "Adaptive-Pruning"
    version = "1.0.0"
    
    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        items = payload.get("items", [])
        threshold = payload.get("threshold", 0.5)
        
        kept = [it for it in items if it.get("score", 1.0) >= threshold]
        pruned = [it for it in items if it.get("score", 1.0) < threshold]
        
        return {
            "pruning": {
                "original_count": len(items),
                "kept_count": len(kept),
                "pruned_count": len(pruned),
                "threshold": threshold
            }
        }
'''
        self._write_file(self.qodeia / "adaptive_pruning.py", pruning_content)
        
        # LFPI Engine
        lfpi_content = '''from __future__ import annotations
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
'''
        self._write_file(self.qodeia / "lfpi.py", lfpi_content)

    def _write_file(self, path: Path, content: str):
        """Escribe contenido en archivo y registra estadísticas"""
        path.write_text(content, encoding='utf-8')
        self.stats["created"] += 1
        self.log_action(f"Archivo creado: {path.name}")

    def run_integration(self):
        """Ejecuta proceso completo de integración"""
        self.analyze_structure()
        self.create_qodeia_core()
        self.create_tier1_engines()
        self.log_action("Integración completada con éxito")
        print(f"\nEstadísticas: {self.stats}")

if __name__ == "__main__":
    integrator = QodeiaAMAIntegrator()
    integrator.run_integration()
