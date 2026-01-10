"""
API Endpoints para el Knowledge Graph Plugin
"""

from typing import Dict, Any
from .orchestrator import KnowledgeGraphOrchestrator

# Nota: Estos handlers serían llamados por el sistema de plugins de AMA-Intent

async def endpoint_query(orchestrator: KnowledgeGraphOrchestrator, payload: Dict[str, Any]):
    """Ejecuta query GraphRAG"""
    query = payload.get("query")
    if not query:
        return {"error": "No query provided"}
    
    result = await orchestrator.query_with_ama_integration(query)
    return {
        "answer": result.answer,
        "query_type": result.query_type,
        "entities": result.entities_found,
        "confidence": result.confidence
    }

async def endpoint_analyze_file(orchestrator: KnowledgeGraphOrchestrator, payload: Dict[str, Any]):
    """Analiza archivo con contexto del KG"""
    file_path = payload.get("file_path")
    code = payload.get("code")
    
    if not file_path or not code:
        return {"error": "Missing file_path or code"}
    
    analysis = await orchestrator.analyze_code_with_kg_context(file_path, code)
    return analysis

async def endpoint_rebuild(orchestrator: KnowledgeGraphOrchestrator, payload: Dict[str, Any]):
    """Reconstruye el KG"""
    force = payload.get("force", False)
    await orchestrator.build_knowledge_graph(force=force)
    return {"status": "success", "message": "Knowledge Graph rebuilt"}

async def endpoint_overview(orchestrator: KnowledgeGraphOrchestrator, payload: Dict[str, Any]):
    """Overview del proyecto"""
    if not orchestrator.kg:
        return {"error": "KG not initialized"}
    
    return orchestrator.kg.get_complexity_metrics()

async def endpoint_refactoring_suggestions(orchestrator: KnowledgeGraphOrchestrator, payload: Dict[str, Any]):
    """Sugerencias de refactorización"""
    suggestions = await orchestrator.suggest_refactoring_opportunities()
    return {"suggestions": suggestions}
