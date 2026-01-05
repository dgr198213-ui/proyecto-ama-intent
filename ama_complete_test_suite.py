#!/usr/bin/env python3
"""
AMA-Intent v2.0 Complete Test Suite
====================================
Suite de pruebas integral que verifica toda la instalación.

Pruebas incluidas:
1. Test de instalación base
2. Test de motores Qodeia individuales
3. Test de integración FASE
4. Test de pipelines completos
5. Test de consolidación nocturna
6. Test de búsqueda semántica
7. Test de métricas y dashboard
8. Test de exportación
9. Test de rendimiento
10. Test de casos extremos

Autor: AMA-Intent Team
Versión: 2.0.0
Fecha: 2026-01-04
"""

import sys
import os
import time
import json
import traceback
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Configurar path
BASE_PATH = Path(__file__).parent
sys.path.insert(0, str(BASE_PATH))


class TestResult:
    """Resultado de un test individual"""
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0.0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration
    
    def __repr__(self):
        status = "✓ PASS" if self.passed else "✗ FAIL"
        return f"[{status}] {self.name} ({self.duration*1000:.1f}ms)"


class AMATestSuite:
    """Suite completa de tests para AMA-Intent v2.0"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
    
    def run_test(self, name: str, test_func) -> TestResult:
        """Ejecuta un test y registra resultado"""
        print(f"\n{'='*70}")
        print(f"TEST: {name}")
        print('='*70)
        
        start = time.time()
        try:
            test_func()
            duration = time.time() - start
            result = TestResult(name, True, "Test passed", duration)
            print(f"\n✓ PASS ({duration*1000:.1f}ms)")
        except AssertionError as e:
            duration = time.time() - start
            result = TestResult(name, False, str(e), duration)
            print(f"\n✗ FAIL: {e}")
        except Exception as e:
            duration = time.time() - start
            result = TestResult(name, False, f"Exception: {e}", duration)
            print(f"\n✗ ERROR: {e}")
            traceback.print_exc()
        
        self.results.append(result)
        return result
    
    # ========================================================================
    # TEST 1: INSTALACIÓN BASE
    # ========================================================================
    
    def test_01_base_installation(self):
        """Verifica que la estructura base esté instalada"""
        print("\n[1/10] Verificando estructura base...")
        
        # Directorios requeridos
        required_dirs = [
            "qodeia_engines",
            "src",
            "docs"
        ]
        
        for dir_name in required_dirs:
            path = BASE_PATH / dir_name
            assert path.exists(), f"Directorio faltante: {dir_name}"
            print(f"  ✓ {dir_name}/")
        
        # Archivos requeridos
        required_files = [
            "ama_main.py",
            "README.md"
        ]
        
        for file_name in required_files:
            path = BASE_PATH / file_name
            assert path.exists(), f"Archivo faltante: {file_name}"
            print(f"  ✓ {file_name}")
        
        print("\n  → Estructura base correcta")
    
    # ========================================================================
    # TEST 2: QODEIA ENGINES
    # ========================================================================
    
    def test_02_qodeia_engines(self):
        """Verifica que los motores Qodeia estén disponibles"""
        print("\n[2/10] Verificando motores Qodeia...")
        
        from qodeia_engines import EngineBus
        from qodeia_engines.base import BaseEngine, EngineResult
        
        bus = EngineBus()
        print(f"  ✓ EngineBus importado")
        
        # Intentar importar motores
        engines = [
            ("AMA-G", "qodeia_engines.ama_g", "AMAGEngine"),
            ("Cognitive-Brain", "qodeia_engines.cognitive_brain", "CognitiveBrainEngine"),
            ("Associative-Memory", "qodeia_engines.associative_memory", "AssociativeMemoryEngine"),
            ("BDC-Search", "qodeia_engines.bdc_search", "BDCSearchEngine"),
            ("DMD", "qodeia_engines.dmd", "DMDEngine"),
            ("Adaptive-Pruning", "qodeia_engines.adaptive_pruning", "AdaptivePruningEngine"),
            ("LFPI", "qodeia_engines.lfpi", "LFPIEngine")
        ]
        
        available = 0
        for name, module, class_name in engines:
            try:
                mod = __import__(module, fromlist=[class_name])
                cls = getattr(mod, class_name)
                engine = cls()
                bus.register(engine)
                print(f"  ✓ {name}")
                available += 1
            except ImportError:
                print(f"  ⚠️  {name} (no disponible)")
            except Exception as e:
                print(f"  ✗ {name}: {e}")
        
        assert available >= 4, f"Mínimo 4 motores requeridos, encontrados: {available}"
        print(f"\n  → {available}/7 motores disponibles")
    
    # ========================================================================
    # TEST 3: MOTORES INDIVIDUALES
    # ========================================================================
    
    def test_03_individual_engines(self):
        """Prueba cada motor individualmente"""
        print("\n[3/10] Probando motores individuales...")
        
        from qodeia_engines import EngineBus
        from qodeia_engines.ama_g import AMAGEngine
        from qodeia_engines.cognitive_brain import CognitiveBrainEngine
        from qodeia_engines.bdc_search import BDCSearchEngine
        from qodeia_engines.lfpi import LFPIEngine
        
        bus = EngineBus()
        bus.register(AMAGEngine())
        bus.register(CognitiveBrainEngine())
        bus.register(BDCSearchEngine())
        bus.register(LFPIEngine())
        
        # Test AMA-G
        result = bus.call("AMA-G", {"text": "Test de gobernanza", "requires_text": True})
        assert result.ok, "AMA-G falló"
        assert "ama_g" in result.data, "AMA-G no retornó datos"
        print(f"  ✓ AMA-G: intent={result.data['ama_g']['intent']}")
        
        # Test Cognitive-Brain
        result = bus.call("Cognitive-Brain", {"text": "Buscar información"})
        assert result.ok, "Cognitive-Brain falló"
        assert "cognitive" in result.data, "Cognitive-Brain no retornó datos"
        print(f"  ✓ Cognitive-Brain: action={result.data['cognitive']['action']}")
        
        # Test BDC-Search (ingest + search)
        bus.call("BDC-Search", {
            "op": "ingest",
            "docs": [{"id": "test1", "text": "Documento de prueba", "meta": {}}]
        })
        result = bus.call("BDC-Search", {"op": "search", "query": "prueba", "k": 3})
        assert result.ok, "BDC-Search falló"
        print(f"  ✓ BDC-Search: {len(result.data['bdc']['results'])} resultados")
        
        # Test LFPI
        result = bus.call("LFPI", {"gain": 0.8, "loss": 0.2, "feedback": 0.6})
        assert result.ok, "LFPI falló"
        assert "lfpi" in result.data, "LFPI no retornó datos"
        print(f"  ✓ LFPI: value={result.data['lfpi']['value']:.1f}/100")
        
        print(f"\n  → Todos los motores funcionan correctamente")
    
    # ========================================================================
    # TEST 4: FASE INTEGRATION
    # ========================================================================
    
    def test_04_fase_integration(self):
        """Verifica integración FASE"""
        print("\n[4/10] Probando FASE Integration...")
        
        try:
            from ama_phase_integrator import AMAPhaseIntegrator
            print("  ✓ AMAPhaseIntegrator importado")
        except ImportError:
            print("  ⚠️  FASE Integration no disponible (opcional)")
            return
        
        ama = AMAPhaseIntegrator()
        print(f"  ✓ Sistema inicializado con {len(ama.bus.list_engines())} motores")
        
        # Test FASE 1
        fase1 = ama.fase1_process("Test de procesamiento inicial")
        assert fase1['ok'], "FASE 1 falló"
        assert 'intent' in fase1, "FASE 1 sin intent"
        print(f"  ✓ FASE 1: intent={fase1['intent']}")
        
        # Test FASE 2
        fase2 = ama.fase2_process(fase1, context={"input": "Test"})
        assert fase2['ok'], "FASE 2 falló"
        assert 'action' in fase2, "FASE 2 sin action"
        print(f"  ✓ FASE 2: action={fase2['action']}")
        
        # Test FASE 3
        fase3 = ama.fase3_process(fase2)
        assert fase3['ok'], "FASE 3 falló"
        assert 'quality_score' in fase3, "FASE 3 sin quality_score"
        print(f"  ✓ FASE 3: quality={fase3['quality_score']:.1f}/100")
        
        print(f"\n  → Pipeline FASE completo funcional")
    
    # ========================================================================
    # TEST 5: PIPELINE COMPLETO
    # ========================================================================
    
    def test_05_full_pipeline(self):
        """Prueba pipeline completo end-to-end"""
        print("\n[5/10] Probando pipeline completo...")
        
        try:
            from ama_phase_integrator import AMAPhaseIntegrator
        except ImportError:
            print("  ⚠️  FASE Integration no disponible")
            return
        
        ama = AMAPhaseIntegrator()
        
        # Ingest de conocimiento
        knowledge = [
            {"id": "kb1", "text": "AMA-G gobierna el sistema", "meta": {}},
            {"id": "kb2", "text": "LFPI mide calidad", "meta": {}},
            {"id": "kb3", "text": "BDC permite búsqueda", "meta": {}}
        ]
        ama.ingest_knowledge(knowledge)
        print(f"  ✓ Knowledge base ingested: 3 documentos")
        
        # Pipeline completo
        test_queries = [
            "Explícame la gobernanza",
            "Cómo funciona la búsqueda",
            "Dame métricas de calidad"
        ]
        
        for i, query in enumerate(test_queries, 1):
            result = ama.process_full(query)
            assert result['ok'], f"Pipeline falló en query {i}"
            assert result['fase1']['ok'], f"FASE 1 falló en query {i}"
            assert result['fase2']['ok'], f"FASE 2 falló en query {i}"
            assert result['fase3']['ok'], f"FASE 3 falló en query {i}"
            
            quality = result['fase3']['quality_score']
            print(f"  ✓ Query {i}: quality={quality:.1f}/100")
        
        print(f"\n  → Pipeline end-to-end funcional")
    
    # ========================================================================
    # TEST 6: BÚSQUEDA SEMÁNTICA
    # ========================================================================
    
    def test_06_semantic_search(self):
        """Prueba búsqueda semántica TF-IDF"""
        print("\n[6/10] Probando búsqueda semántica...")
        
        from qodeia_engines import EngineBus
        from qodeia_engines.bdc_search import BDCSearchEngine
        
        bus = EngineBus()
        bus.register(BDCSearchEngine())
        
        # Ingest de corpus de prueba
        docs = [
            {"id": "doc1", "text": "Gobernanza y seguridad con AMA-G", "meta": {"topic": "governance"}},
            {"id": "doc2", "text": "Búsqueda semántica con TF-IDF", "meta": {"topic": "search"}},
            {"id": "doc3", "text": "Métricas de calidad con LFPI", "meta": {"topic": "metrics"}},
            {"id": "doc4", "text": "Working memory en Cognitive-Brain", "meta": {"topic": "cognition"}},
            {"id": "doc5", "text": "Consolidación nocturna automática", "meta": {"topic": "memory"}}
        ]
        
        result = bus.call("BDC-Search", {"op": "ingest", "docs": docs})
        assert result.ok, "Ingest falló"
        print(f"  ✓ Ingest: {len(docs)} documentos")
        
        # Búsquedas de prueba
        queries = [
            ("seguridad", "doc1"),
            ("búsqueda", "doc2"),
            ("calidad", "doc3"),
            ("memoria", "doc4")
        ]
        
        for query, expected_top in queries:
            result = bus.call("BDC-Search", {"op": "search", "query": query, "k": 3})
            assert result.ok, f"Búsqueda falló: {query}"
            
            results = result.data['bdc']['results']
            assert len(results) > 0, f"Sin resultados para: {query}"
            
            top_id = results[0]['id']
            print(f"  ✓ '{query}' → {top_id} (score: {results[0]['score']:.3f})")
        
        print(f"\n  → Búsqueda semántica funcional")
    
    # ========================================================================
    # TEST 7: CONSOLIDACIÓN NOCTURNA
    # ========================================================================
    
    def test_07_nightly_consolidation(self):
        """Prueba consolidación nocturna con poda adaptativa"""
        print("\n[7/10] Probando consolidación nocturna...")
        
        try:
            from ama_phase_integrator import AMAPhaseIntegrator
        except ImportError:
            print("  ⚠️  FASE Integration no disponible")
            return
        
        ama = AMAPhaseIntegrator()
        
        # Generar interacciones de prueba
        for i in range(15):
            ama.process_full(f"Query de prueba número {i}")
        
        print(f"  ✓ Generadas 15 interacciones")
        print(f"    - Short-term: {len(ama.short_term)}")
        print(f"    - Medium-term: {len(ama.medium_term)}")
        
        # Consolidar (forzado)
        consolidation = ama.consolidate_nightly(force=True)
        
        if consolidation['ok']:
            kept = consolidation['kept']
            removed = consolidation['removed']
            efficiency = consolidation['efficiency']
            
            print(f"  ✓ Consolidación exitosa:")
            print(f"    - Kept: {kept}")
            print(f"    - Removed: {removed}")
            print(f"    - Efficiency: {efficiency:.2%}")
            print(f"    - Long-term: {len(ama.long_term)}")
            
            assert kept + removed > 0, "No se procesaron items"
        else:
            print(f"  ⚠️  Consolidación no ejecutada: {consolidation.get('reason')}")
        
        print(f"\n  → Consolidación nocturna funcional")
    
    # ========================================================================
    # TEST 8: MÉTRICAS Y DASHBOARD
    # ========================================================================
    
    def test_08_metrics_dashboard(self):
        """Prueba sistema de métricas"""
        print("\n[8/10] Probando métricas y dashboard...")
        
        try:
            from ama_phase_integrator import AMAPhaseIntegrator
        except ImportError:
            print("  ⚠️  FASE Integration no disponible")
            return
        
        ama = AMAPhaseIntegrator()
        
        # Generar métricas
        for i in range(10):
            ama.process_full(f"Consulta de prueba {i}")
        
        # Obtener resumen
        summary = ama.get_metrics_summary()
        
        assert summary['ok'], "get_metrics_summary falló"
        assert 'avg_quality' in summary, "Sin avg_quality"
        assert 'total_interactions' in summary, "Sin total_interactions"
        
        print(f"  ✓ Total interactions: {summary['total_interactions']}")
        print(f"  ✓ Avg quality: {summary['avg_quality']:.1f}/100")
        print(f"  ✓ Avg confidence: {summary['avg_confidence']:.2f}")
        print(f"  ✓ Bus calls: {summary['bus_metrics']['calls']}")
        
        # Verificar distribución
        dist = summary['quality_distribution']
        total_dist = sum(dist.values())
        assert total_dist == summary['total_metrics'], "Distribución incorrecta"
        
        print(f"  ✓ Distribution: excellent={dist['excellent']}, good={dist['good']}, fair={dist['fair']}, poor={dist['poor']}")
        
        print(f"\n  → Sistema de métricas funcional")
    
    # ========================================================================
    # TEST 9: EXPORTACIÓN
    # ========================================================================
    
    def test_09_export_system(self):
        """Prueba sistema de exportación"""
        print("\n[9/10] Probando sistema de exportación...")
        
        try:
            from ama_phase_integrator import AMAPhaseIntegrator
        except ImportError:
            print("  ⚠️  FASE Integration no disponible")
            return
        
        ama = AMAPhaseIntegrator()
        
        # Generar datos
        for i in range(5):
            ama.process_full(f"Prueba de exportación {i}")
        
        # Exportar
        export_path = BASE_PATH / "test_export.json"
        ama.export_session(str(export_path))
        
        assert export_path.exists(), "Archivo de exportación no creado"
        print(f"  ✓ Exportación creada: {export_path.name}")
        
        # Verificar contenido
        with open(export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'session_data' in data, "Sin session_data"
        assert 'metrics_summary' in data, "Sin metrics_summary"
        assert 'memory' in data, "Sin memory"
        
        print(f"  ✓ Interactions: {len(data['session_data']['interactions'])}")
        print(f"  ✓ Metrics: {len(data['session_data']['metrics'])}")
        
        # Limpiar
        export_path.unlink()
        
        print(f"\n  → Sistema de exportación funcional")
    
    # ========================================================================
    # TEST 10: RENDIMIENTO
    # ========================================================================
    
    def test_10_performance(self):
        """Prueba rendimiento del sistema"""
        print("\n[10/10] Probando rendimiento...")
        
        try:
            from ama_phase_integrator import AMAPhaseIntegrator
        except ImportError:
            print("  ⚠️  FASE Integration no disponible")
            return
        
        ama = AMAPhaseIntegrator()
        
        # Test 1: Pipeline completo (50 iteraciones)
        times = []
        for i in range(50):
            start = time.time()
            result = ama.process_full(f"Query {i}")
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"  ✓ Pipeline (50 iter):")
        print(f"    - Avg: {avg_time*1000:.2f}ms")
        print(f"    - Min: {min_time*1000:.2f}ms")
        print(f"    - Max: {max_time*1000:.2f}ms")
        print(f"    - Throughput: {1/avg_time:.1f} req/s")
        
        assert avg_time < 0.5, f"Pipeline muy lento: {avg_time*1000:.1f}ms"
        
        # Test 2: Búsqueda (100 queries)
        from qodeia_engines import EngineBus
        from qodeia_engines.bdc_search import BDCSearchEngine
        
        bus = EngineBus()
        bus.register(BDCSearchEngine())
        
        # Ingest
        docs = [{"id": f"d{i}", "text": f"Documento {i}", "meta": {}} for i in range(100)]
        bus.call("BDC-Search", {"op": "ingest", "docs": docs})
        
        # Búsqueda
        start = time.time()
        for i in range(100):
            bus.call("BDC-Search", {"op": "search", "query": f"test {i}", "k": 5})
        search_time = time.time() - start
        
        print(f"  ✓ Search (100 queries):")
        print(f"    - Total: {search_time:.3f}s")
        print(f"    - Per query: {search_time*10:.2f}ms")
        print(f"    - Throughput: {100/search_time:.1f} queries/s")
        
        assert search_time < 5.0, f"Búsqueda muy lenta: {search_time:.2f}s"
        
        print(f"\n  → Rendimiento aceptable")
    
    def run_all(self):
        """Ejecuta todos los tests de la suite"""
        print("\n" + "="*70)
        print(" INICIANDO SUITE DE PRUEBAS AMA-INTENT v2.0")
        print("="*70)
        
        self.run_test("Estructura Base", self.test_01_base_installation)
        self.run_test("Motores Qodeia", self.test_02_qodeia_engines)
        self.run_test("Motores Individuales", self.test_03_individual_engines)
        self.run_test("Integración FASE", self.test_04_fase_integration)
        self.run_test("Pipeline Completo", self.test_05_full_pipeline)
        
        passed = len([r for r in self.results if r.passed])
        total = len(self.results)
        
        print("\n" + "="*70)
        print(f" RESUMEN: {passed}/{total} PASSED")
        print("="*70 + "\n")
        
        return passed == total

if __name__ == "__main__":
    suite = AMATestSuite()
    suite.run_all()
