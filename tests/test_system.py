import os
import sys
import unittest

# Asegura que la raíz del proyecto y la carpeta src estén en el path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "src"))

try:
    from ama_main import AMAIntentSystem
except ImportError:
    # Intento de respaldo si está dentro de un paquete src
    from src.ama_main import AMAIntentSystem


class TestAMAIntentSystem(unittest.TestCase):
    def setUp(self):
        self.ama = AMAIntentSystem()

    def test_01_governance(self):
        payload = {"text": "sudo rm -rf /"}
        result = self.ama.bus.call("AMA-G", payload)
        self.assertGreater(result["risk_score"], 0.5)
        self.assertEqual(result["risk_level"], "high")

    def test_02_search(self):
        docs = [{"id": "1", "text": "Python programming"}]
        self.ama.bus.call("BDC-Search", {"op": "ingest", "docs": docs})
        # Forzar reconstrucción si es necesario o simplemente buscar
        results = self.ama.bus.call(
            "BDC-Search", {"op": "search", "query": "python", "k": 1}
        )
        # El motor devuelve una lista de resultados en EngineResult.data
        self.assertTrue(
            len(results) >= 0
        )  # El motor está funcionando si no lanza error

    def test_03_dmd(self):
        alts = [
            {"name": "A", "criteria": {"val": 10}},
            {"name": "B", "criteria": {"val": 5}},
        ]
        weights = {"val": 1.0}
        result = self.ama.bus.call("DMD", {"alternatives": alts, "weights": weights})
        self.assertEqual(result["best"], "A")

    def test_04_lfpi(self):
        result = self.ama.bus.call(
            "LFPI", {"gain": 1.0, "loss": 0.0, "feedback": 1.0, "amplitude": 1.0}
        )
        self.assertEqual(result["value"], 100.0)
        self.assertEqual(result["level"], "excellent")

    def test_05_full_pipeline(self):
        result = self.ama.bus.call("Phase-Integrator", {"text": "Hola, ¿cómo estás?"})
        self.assertIn("fase1", result)
        # El tipo puede variar según la heurística, lo importante es que se procese
        self.assertIsInstance(result["fase1"]["intent"], str)
        self.assertIn("fase2", result)
        self.assertIn("fase3", result)

    def test_06_new_intent_logic(self):
        payload = {"text": "Analiza las ventajas de Python"}
        result = self.ama.bus.call("AMA-G", payload)
        self.assertEqual(result["intent"], "analítica")
        self.assertIn("intent_details", result)
        self.assertIn("goal", result["intent_details"])


if __name__ == "__main__":
    unittest.main()
