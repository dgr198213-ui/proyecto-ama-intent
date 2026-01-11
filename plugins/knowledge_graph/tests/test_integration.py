import asyncio
import sys
from pathlib import Path

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from plugins.knowledge_graph.orchestrator import (KGBuildConfig,
                                                  KnowledgeGraphOrchestrator)


async def main():
    print("Iniciando test de integración...")

    # Configuración apuntando al propio repositorio
    project_root = Path(__file__).parent.parent.parent.parent
    config = KGBuildConfig(
        project_path=project_root, file_patterns=["plugins/knowledge_graph/*.py"]
    )

    orchestrator = KnowledgeGraphOrchestrator(config, use_ama_core=False)

    # 1. Inicializar
    await orchestrator.initialize()

    # 2. Verificar métricas
    metrics = orchestrator.kg.get_complexity_metrics()
    print(f"Métricas del KG: {metrics}")

    # 3. Probar query
    query = "¿Qué es ProjectKnowledgeGraph?"
    result = await orchestrator.query_with_ama_integration(query)
    print(f"Query: {query}")
    print(f"Respuesta: {result.answer}")
    print(f"Entidades encontradas: {result.entities_found}")

    # 4. Probar análisis de archivo
    test_file = "plugins/knowledge_graph/project_kg.py"
    with open(project_root / test_file, "r") as f:
        code = f.read()

    analysis = await orchestrator.analyze_code_with_kg_context(test_file, code)
    print(f"Análisis de {test_file}:")
    print(f"  Entidades: {len(analysis['entities'])}")
    print(f"  Riesgo: {analysis['risk_score']}")

    print("Test completado con éxito.")


if __name__ == "__main__":
    asyncio.run(main())
