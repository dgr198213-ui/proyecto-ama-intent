# AMA-Intent v2.0 🚀

Sistema de IA modular con gobernanza, cognición, búsqueda semántica y decisiones multi-criterio.

## 📁 Estructura del Proyecto
- `ama_main.py`: Punto de entrada y orquestador del sistema.
- `engines/`: Motores individuales (AMA-G, Cognitive, BDC-Search, DMD, LFPI, Pruning).
- `utils/`: Utilidades de procesamiento de texto, matemáticas y seguridad.
- `tests/`: Suite de pruebas unitarias.

## 🛠️ Funciones Principales
1. **Gobernanza (AMA-G):** Detección de intención y análisis de riesgo.
2. **Cognición:** Memoria de trabajo y toma de decisiones.
3. **Búsqueda Semántica:** Motor TF-IDF nativo sin dependencias externas.
4. **Decisiones (DMD):** Ranking de alternativas basado en múltiples criterios.
5. **Métricas (LFPI):** Evaluación de calidad de respuestas.
6. **Pipeline FASE:** Integración completa de procesamiento en 3 fases.

## 🚀 Ejecución
Para ejecutar la demostración:
```bash
python3 ama_main.py
```

Para ejecutar las pruebas:
```bash
python3 tests/test_system.py
```
