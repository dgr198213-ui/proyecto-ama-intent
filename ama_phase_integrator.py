#!/usr/bin/env python3
"""
AMA-Intent FASE Integration Bridge
===================================
Puente de integración que conecta motores Qodeia con módulos FASE existentes.

Funcionalidades:
- Wrapper para FASE 1 (Procesamiento Inicial)
- Wrapper para FASE 2 (Procesamiento Intermedio)
- Wrapper para FASE 3 (Procesamiento Avanzado)
- Sistema de consolidación nocturna mejorado
- Dashboard de métricas en tiempo real
- Sistema de exportación de datos

Autor: AMA-Intent Team
Versión: 2.0.0
Fecha: 2026-01-04
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Importar Qodeia engines
try:
    from qodeia_engines import EngineBus
    from qodeia_engines.ama_g import AMAGEngine
    from qodeia_engines.cognitive_brain import CognitiveBrainEngine
    from qodeia_engines.associative_memory import AssociativeMemoryEngine
    from qodeia_engines.bdc_search import BDCSearchEngine
    from qodeia_engines.dmd import DMDEngine
    from qodeia_engines.adaptive_pruning import AdaptivePruningEngine
    from qodeia_engines.lfpi import LFPIEngine
    from qodeia_engines.rocketml_rml import RocketMLRMLEngine
except ImportError:
    print("ERROR: Ejecutar primero qodeia_ama_integrator.py")
    sys.exit(1)


class AMAPhaseIntegrator:
    """
    Integrador que conecta Qodeia Engines con arquitectura FASE de AMA-Intent.
    
    Proporciona:
    - Wrappers para FASE 1/2/3
    - Sistema de memoria mejorado
    - Consolidación nocturna automática
    - Métricas en tiempo real
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.bus = EngineBus()
        self.session_data = {
            "start_time": time.time(),
            "interactions": [],
            "metrics": [],
            "memory_snapshots": []
        }
        
        # Registrar todos los motores
        self._register_engines()
        
        # Estado de memoria
        self.short_term = []  # Últimas 10 interacciones
        self.medium_term = []  # Últimas 100 interacciones consolidadas
        self.long_term = []   # Conocimiento permanente
        
        print(f"[INIT] AMA-Intent v2.0 inicializado con {len(self.bus.list_engines())} motores")
    
    def _default_config(self) -> Dict[str, Any]:
        """Configuración por defecto"""
        return {
            "short_term_size": 10,
            "medium_term_size": 100,
            "pruning_threshold": 0.35,
            "lfpi_alert_threshold": 60.0,
            "cognitive_wm_size": 20,
            "bdc_top_k": 5,
            "enable_metrics": True,
            "enable_consolidation": True
        }
    
    def _register_engines(self):
        """Registra todos los motores Qodeia"""
        self.bus.register(AMAGEngine())
        self.bus.register(CognitiveBrainEngine(
            wm_size=self.config["cognitive_wm_size"]
        ))
        self.bus.register(AssociativeMemoryEngine())
        self.bus.register(BDCSearchEngine())
        self.bus.register(DMDEngine())
        self.bus.register(AdaptivePruningEngine())
        self.bus.register(LFPIEngine())
        self.bus.register(RocketMLRMLEngine())
    
    # ========================================================================
    # FASE 1: PROCESAMIENTO INICIAL
    # ========================================================================
    
    def fase1_process(self, user_input: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        FASE 1: Procesamiento Inicial con Qodeia
        
        Pipeline:
        1. AMA-G: Gobernanza y extracción de intención (I₀)
        2. Validación de entrada
        3. Registro en memoria corto plazo
        
        Returns:
            Dict con: intent, risk_level, audit_id, is_valid
        """
        print(f"\n[FASE 1] Procesando: '{user_input[:60]}...'")
        
        # 1. Gobernanza AMA-G
        result_g = self.bus.call("AMA-G", {
            "text": user_input,
            "requires_text": True,
            "metadata": metadata or {}
        })
        
        if not result_g.ok:
            return {
                "phase": "FASE1",
                "ok": False,
                "error": result_g.error,
                "intent": None
            }
        
        ama_g_data = result_g.data.get("ama_g", {})
        
        # 2. Registrar en memoria corto plazo
        interaction = {
            "timestamp": time.time(),
            "input": user_input,
            "intent": ama_g_data.get("intent"),
            "audit_id": ama_g_data.get("audit_id"),
            "risk_level": ama_g_data.get("risk_level"),
            "metadata": metadata
        }
        
        self.short_term.append(interaction)
        if len(self.short_term) > self.config["short_term_size"]:
            # Consolidar a medio plazo
            oldest = self.short_term.pop(0)
            self.medium_term.append(oldest)
        
        print(f"  ✓ Intent: {ama_g_data.get('intent')}")
        print(f"  ✓ Risk: {ama_g_data.get('risk_level')}")
        
        return {
            "phase": "FASE1",
            "ok": True,
            "intent": ama_g_data.get("intent"),
            "risk_level": ama_g_data.get("risk_level"),
            "audit_id": ama_g_data.get("audit_id"),
            "ama_g": ama_g_data,
            "interaction_id": len(self.session_data["interactions"])
        }
    
    # ========================================================================
    # FASE 2: PROCESAMIENTO INTERMEDIO
    # ========================================================================
    
    def fase2_process(self, fase1_output: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        FASE 2: Procesamiento Intermedio con Cognición
        
        Pipeline:
        1. Cognitive-Brain: Análisis contextual y decisión
        2. BDC-Search: Búsqueda en base de conocimiento (si aplica)
        3. Asociación de memoria relevante
        
        Returns:
            Dict con: action, confidence, search_results, cognitive_state
        """
        print(f"\n[FASE 2] Procesamiento cognitivo...")
        
        if not fase1_output.get("ok"):
            return {"phase": "FASE2", "ok": False, "error": "FASE1 failed"}
        
        user_input = context.get("input") if context else ""
        
        # 1. Análisis cognitivo
        result_cog = self.bus.call("Cognitive-Brain", {
            "text": user_input,
            "intent": fase1_output.get("intent")
        })
        
        if not result_cog.ok:
            return {"phase": "FASE2", "ok": False, "error": result_cog.error}
        
        cognitive = result_cog.data.get("cognitive", {})
        action = cognitive.get("action")
        confidence = cognitive.get("confidence")
        
        print(f"  ✓ Action: {action} (confidence: {confidence:.2f})")
        
        # 2. Búsqueda en BDC si es necesario
        search_results = None
        if action in ["search", "analyze"] and user_input:
            result_bdc = self.bus.call("BDC-Search", {
                "op": "search",
                "query": user_input,
                "k": self.config["bdc_top_k"]
            })
            
            if result_bdc.ok:
                search_results = result_bdc.data.get("bdc", {}).get("results", [])
                print(f"  ✓ BDC Search: {len(search_results)} resultados")
        
        # 3. Memoria asociativa (contexto histórico)
        result_mem = self.bus.call("Associative-Memory", {
            "op": "query",
            "query": user_input,
            "k": 3
        })
        
        associative_memory = []
        if result_mem.ok:
            associative_memory = result_mem.data.get("associative", {}).get("results", [])
            print(f"  ✓ Associative Memory: {len(associative_memory)} matches")
        
        return {
            "phase": "FASE2",
            "ok": True,
            "action": action,
            "confidence": confidence,
            "cognitive": cognitive,
            "search_results": search_results,
            "associative_memory": associative_memory,
            "wm_depth": cognitive.get("context_depth", 0)
        }
    
    # ========================================================================
    # FASE 3: PROCESAMIENTO AVANZADO
    # ========================================================================
    
    def fase3_process(
        self, 
        fase2_output: Dict[str, Any], 
        alternatives: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        FASE 3: Procesamiento Avanzado - Decisión y Evaluación
        
        Pipeline:
        1. DMD: Selección de mejor respuesta/acción
        2. LFPI: Evaluación de calidad
        3. Registro de métricas
        
        Returns:
            Dict con: best_action, quality_score, metrics
        """
        print(f"\n[FASE 3] Decisión y evaluación...")
        
        if not fase2_output.get("ok"):
            return {"phase": "FASE3", "ok": False, "error": "FASE2 failed"}
        
        # 1. Decisión multi-criterio (si hay alternativas)
        best_choice = None
        if alternatives:
            result_dmd = self.bus.call("DMD", {
                "alternatives": alternatives,
                "weights": {
                    "relevancia": 0.5,
                    "claridad": 0.3,
                    "completitud": 0.2
                }
            })
            
            if result_dmd.ok:
                best_choice = result_dmd.data.get("dmd", {}).get("best")
                print(f"  ✓ Best choice: {best_choice.get('name')} (score: {best_choice.get('score'):.3f})")
        
        # 2. Evaluación de calidad LFPI
        confidence = fase2_output.get("confidence", 0.5)
        search_quality = 0.8 if fase2_output.get("search_results") else 0.5
        
        result_lfpi = self.bus.call("LFPI", {
            "gain": confidence,
            "loss": 0.1,
            "feedback": search_quality,
            "amplitude": 0.8
        })
        
        lfpi_data = {}
        if result_lfpi.ok:
            lfpi_data = result_lfpi.data.get("lfpi", {})
            quality_score = lfpi_data.get("value", 0.0)
            quality_level = lfpi_data.get("level", "unknown")
            
            print(f"  ✓ Quality: {quality_score:.1f}/100 ({quality_level})")
            
            # Alerta si calidad baja
            if quality_score < self.config["lfpi_alert_threshold"]:
                print(f"  ⚠️  LOW QUALITY ALERT: {quality_score:.1f}")
        
        # 3. Registrar métricas
        if self.config["enable_metrics"]:
            metric = {
                "timestamp": time.time(),
                "action": fase2_output.get("action"),
                "confidence": confidence,
                "quality_score": lfpi_data.get("value", 0.0),
                "quality_level": lfpi_data.get("level"),
                "best_choice": best_choice.get("name") if best_choice else None
            }
            self.session_data["metrics"].append(metric)
        
        return {
            "phase": "FASE3",
            "ok": True,
            "best_choice": best_choice,
            "quality_score": lfpi_data.get("value", 0.0),
            "quality_level": lfpi_data.get("level"),
            "lfpi": lfpi_data,
            "metrics_count": len(self.session_data["metrics"])
        }
    
    # ========================================================================
    # PIPELINE COMPLETO
    # ========================================================================
    
    def process_full(
        self, 
        user_input: str, 
        alternatives: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Pipeline completo FASE 1 → 2 → 3
        
        Args:
            user_input: Texto del usuario
            alternatives: Lista de alternativas para DMD (opcional)
            metadata: Metadatos adicionales (opcional)
        
        Returns:
            Dict con resultados de todas las fases
        """
        start = time.time()
        
        # FASE 1
        fase1 = self.fase1_process(user_input, metadata)
        if not fase1.get("ok"):
            return {"ok": False, "error": "FASE1 failed", "fase1": fase1}
        
        # FASE 2
        fase2 = self.fase2_process(fase1, context={"input": user_input})
        if not fase2.get("ok"):
            return {"ok": False, "error": "FASE2 failed", "fase1": fase1, "fase2": fase2}
        
        # FASE 3
        fase3 = self.fase3_process(fase2, alternatives)
        if not fase3.get("ok"):
            return {"ok": False, "error": "FASE3 failed", "fase1": fase1, "fase2": fase2, "fase3": fase3}
        
        elapsed = time.time() - start
        
        # Registrar interacción completa
        interaction = {
            "timestamp": time.time(),
            "input": user_input,
            "fase1": fase1,
            "fase2": fase2,
            "fase3": fase3,
            "elapsed_ms": elapsed * 1000
        }
        self.session_data["interactions"].append(interaction)
        
        print(f"\n[PIPELINE] Completado en {elapsed*1000:.1f}ms")
        
        return {
            "ok": True,
            "fase1": fase1,
            "fase2": fase2,
            "fase3": fase3,
            "elapsed_ms": elapsed * 1000,
            "interaction_id": len(self.session_data["interactions"]) - 1
        }
    
    # ========================================================================
    # CONSOLIDACIÓN NOCTURNA
    # ========================================================================
    
    def consolidate_nightly(self, force: bool = False) -> Dict[str, Any]:
        """
        Consolidación nocturna con Adaptive Pruning
        
        Proceso:
        1. Evaluar memoria medio plazo
        2. Aplicar poda adaptativa
        3. Mover items importantes a largo plazo
        4. Limpiar memoria corto plazo antigua
        
        Args:
            force: Forzar consolidación sin importar hora
        
        Returns:
            Dict con estadísticas de consolidación
        """
        print("\n" + "="*60)
        print("CONSOLIDACIÓN NOCTURNA")
        print("="*60)
        
        if not self.config["enable_consolidation"]:
            print("  Consolidación deshabilitada en config")
            return {"ok": False, "reason": "disabled"}
        
        # Verificar si es hora adecuada (entre 2-5 AM) o forzado
        current_hour = datetime.now().hour
        if not force and not (2 <= current_hour <= 5):
            print(f"  No es hora de consolidación (hora actual: {current_hour}h)")
            return {"ok": False, "reason": "wrong_time"}
        
        # Preparar items de memoria medio plazo para evaluación
        items = []
        for i, interaction in enumerate(self.medium_term):
            age_hours = (time.time() - interaction["timestamp"]) / 3600
            
            # Calcular importance (basado en intent y risk)
            intent_importance = {
                "search": 0.7,
                "analyze": 0.8,
                "optimize": 0.9,
                "simulate": 0.6,
                "general": 0.4
            }
            importance = intent_importance.get(interaction.get("intent", "general"), 0.5)
            
            # Calcular usage (qué tan reciente)
            usage = max(0.0, 1.0 - (age_hours / 720.0))  # Decay en 30 días
            
            items.append({
                "id": f"mem_{i}",
                "importance": importance,
                "usage": usage,
                "interaction": interaction,
                "age_hours": age_hours
            })
        
        if not items:
            print("  Sin items para consolidar")
            return {"ok": True, "kept": 0, "removed": 0, "reason": "empty"}
        
        # Aplicar Adaptive Pruning
        result = self.bus.call("Adaptive-Pruning", {
            "items": items,
            "alpha": 0.6,  # Priorizar importance
            "beta": 0.4,   # Menos peso a usage
            "threshold": self.config["pruning_threshold"]
        })
        
        if not result.ok:
            print(f"  ERROR: {result.error}")
            return {"ok": False, "error": result.error}
        
        pruning = result.data.get("pruning", {})
        kept = pruning.get("kept", [])
        removed = pruning.get("removed", [])
        
        # Mover kept a long_term
        for item in kept:
            interaction = item["interaction"]
            interaction["consolidated_at"] = time.time()
            interaction["prune_score"] = item["prune_score"]
            self.long_term.append(interaction)
        
        # Limpiar medium_term
        self.medium_term = []
        
        # Snapshot
        snapshot = {
            "timestamp": time.time(),
            "kept": len(kept),
            "removed": len(removed),
            "long_term_size": len(self.long_term),
            "efficiency": pruning.get("efficiency", 0.0)
        }
        self.session_data["memory_snapshots"].append(snapshot)
        
        print(f"\n  ✓ Kept: {len(kept)}")
        print(f"  ✓ Removed: {len(removed)}")
        print(f"  ✓ Long-term size: {len(self.long_term)}")
        print(f"  ✓ Efficiency: {pruning.get('efficiency', 0.0):.2%}")
        
        return {
            "ok": True,
            "kept": len(kept),
            "removed": len(removed),
            "long_term_size": len(self.long_term),
            "efficiency": pruning.get("efficiency", 0.0),
            "mean_score": pruning.get("mean_score", 0.0)
        }
    
    # ========================================================================
    # INGEST DE CONOCIMIENTO
    # ========================================================================
    
    def ingest_knowledge(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ingesta de documentos en BDC-Search y Associative-Memory
        
        Args:
            documents: Lista de {id, text, meta}
        
        Returns:
            Dict con estadísticas de ingesta
        """
        print(f"\n[INGEST] Procesando {len(documents)} documentos...")
        
        # Ingest en BDC
        result_bdc = self.bus.call("BDC-Search", {
            "op": "ingest",
            "docs": documents
        })
        
        # Ingest en Associative Memory (uno por uno)
        assoc_count = 0
        for doc in documents:
            result = self.bus.call("Associative-Memory", {
                "op": "ingest",
                "id": doc.get("id"),
                "text": doc.get("text"),
                "meta": doc.get("meta", {})
            })
            if result.ok:
                assoc_count += 1
        
        print(f"  ✓ BDC: {result_bdc.data.get('bdc', {}).get('count', 0)} docs")
        print(f"  ✓ Associative: {assoc_count} docs")
        
        return {
            "ok": True,
            "bdc_count": result_bdc.data.get("bdc", {}).get("count", 0),
            "associative_count": assoc_count,
            "total": len(documents)
        }
    
    # ========================================================================
    # MÉTRICAS Y DASHBOARD
    # ========================================================================
    


if __name__ == "__main__":
    # Demo rápido si se ejecuta directamente
    ama = AMAPhaseIntegrator()
    res = ama.process_full("Hola, necesito ayuda con el sistema")
    print(json.dumps(res, indent=2))
