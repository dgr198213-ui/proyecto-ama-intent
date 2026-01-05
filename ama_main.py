import sys
import os
import json
import time

# Añadir el directorio actual al path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.engine_bus import EngineBus
from engines.ama_g import AMAGovernance
from engines.cognitive_brain import CognitiveBrain
from engines.bdc_search import BDCSearch
from engines.dmd import DMD
from engines.lfpi import LFPI
from engines.adaptive_pruning import AdaptivePruning
from engines.ama_phase_integrator import AMAPhaseIntegrator

class AMAIntentSystem:
    def __init__(self):
        self.bus = EngineBus()
        self._init_engines()
        self.start_time = time.time()

    def _init_engines(self):
        # Instanciar motores
        self.ama_g = AMAGovernance()
        self.cognitive = CognitiveBrain()
        self.bdc = BDCSearch()
        self.dmd = DMD()
        self.lfpi = LFPI()
        self.pruning = AdaptivePruning()
        
        # Registrar en el bus
        self.bus.register("AMA-G", self.ama_g)
        self.bus.register("Cognitive-Brain", self.cognitive)
        self.bus.register("BDC-Search", self.bdc)
        self.bus.register("DMD", self.dmd)
        self.bus.register("LFPI", self.lfpi)
        self.bus.register("Adaptive-Pruning", self.pruning)
        
        # Integrador de fases (también actúa como motor)
        self.integrator = AMAPhaseIntegrator(self.bus)
        self.bus.register("Phase-Integrator", self.integrator)

    def print_dashboard(self):
        metrics = self.bus.get_metrics()
        duration = (time.time() - self.start_time) / 3600
        
        print("=" * 70)
        print(" AMA-INTENT v2.0 - DASHBOARD DE MÉTRICAS")
        print("=" * 70)
        print(f"\n📊 SESIÓN")
        print(f"  Duración: {duration:.2f}h")
        print(f"  Interacciones: {metrics['calls']}")
        
        print(f"\n🧠 MEMORIA")
        print(f"  Corto plazo:  {len(self.integrator.short_term)}")
        print(f"  Medio plazo:  {len(self.integrator.medium_term)}")
        print(f"  Largo plazo:  {len(self.integrator.long_term)}")
        
        print(f"\n🚌 BUS")
        print(f"  Total calls: {metrics['calls']}")
        print(f"  Errores:     {metrics['errors']}")
        print(f"  Avg time:    {metrics['avg_time']*1000:.2f}ms")
        print("=" * 70)

    def run_demo(self):
        print("Iniciando demostración de AMA-Intent v2.0...\n")
        
        # 1. Ingesta de conocimiento
        print("Ingestando documentos en BDC-Search...")
        docs = [
            {"id": "doc1", "text": "La inteligencia artificial es el futuro de la tecnología.", "meta": {"cat": "tech"}},
            {"id": "doc2", "text": "El procesamiento de lenguaje natural permite a las máquinas entender el texto.", "meta": {"cat": "nlp"}},
            {"id": "doc3", "text": "Python es un lenguaje versátil para el desarrollo de IA.", "meta": {"cat": "dev"}}
        ]
        self.bus.call("BDC-Search", {"op": "ingest", "docs": docs})
        
        # 2. Procesamiento de una consulta
        print("\nProcesando consulta: 'Buscar información sobre IA en Python'")
        alternatives = [
            {"name": "Respuesta A", "criteria": {"relevancia": 0.9, "claridad": 0.8, "completitud": 0.7}},
            {"name": "Respuesta B", "criteria": {"relevancia": 0.7, "claridad": 0.9, "completitud": 0.6}}
        ]
        
        result = self.bus.call("Phase-Integrator", {
            "text": "Buscar información sobre IA en Python",
            "alternatives": alternatives
        })
        
        print("\nResultado del Pipeline:")
        print(f"  Intención detectada: {result['fase1']['intent']}")
        print(f"  Nivel de riesgo: {result['fase1']['risk_level']}")
        print(f"  Acción decidida: {result['fase2']['cognitive']['action']}")
        print(f"  Mejor respuesta (DMD): {result['fase3']['best_response']}")
        print(f"  Calidad (LFPI): {result['fase3']['lfpi']['value']:.2f} ({result['fase3']['lfpi']['level']})")
        print(f"  Tiempo total: {result['performance']['total_time_ms']:.2f}ms")
        
        print("\n")
        self.print_dashboard()

if __name__ == "__main__":
    ama = AMAIntentSystem()
    ama.run_demo()
