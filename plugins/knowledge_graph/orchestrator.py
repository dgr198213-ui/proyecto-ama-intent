"""
Knowledge Graph Plugin - Integración Completa
Plugin para AMA-Intent Dashboard
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

# Importaciones locales
try:
    from .project_kg import ProjectKnowledgeGraph, CodeEntity, NodeType
    from .graphrag import GraphRAG, QueryType
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from project_kg import ProjectKnowledgeGraph, CodeEntity, NodeType
    from graphrag import GraphRAG, QueryType


@dataclass
class KGBuildConfig:
    """Configuración para construcción del KG"""
    project_path: Path
    file_patterns: List[str]
    auto_rebuild: bool = False
    rebuild_interval_hours: int = 24
    enable_rdf: bool = True
    detect_patterns: bool = True


@dataclass
class KGQueryResult:
    """Resultado de una query GraphRAG"""
    query: str
    answer: str
    query_type: str
    entities_found: List[str]
    context_used: Dict[str, Any]
    timestamp: str
    confidence: float


class KnowledgeGraphOrchestrator:
    """
    Orquestador principal del plugin KG
    """
    
    def __init__(self, config: KGBuildConfig, llm_hub=None, use_ama_core: bool = True):
        self.config = config
        self.llm_hub = llm_hub
        self.use_ama_core = use_ama_core
        
        # Componentes del plugin
        self.kg: Optional[ProjectKnowledgeGraph] = None
        self.graph_rag: Optional[GraphRAG] = None
        
        # Estado
        self.last_build_time: Optional[datetime] = None
        self.query_history: List[KGQueryResult] = []
    
    async def initialize(self):
        """Inicializa el sistema completo"""
        print("🚀 Inicializando Knowledge Graph Plugin...")
        
        # 1. Construir KG inicial
        await self.build_knowledge_graph()
        
        # 2. Inicializar GraphRAG
        self.graph_rag = GraphRAG(self.kg, self.llm_hub)
        
        print("✅ Plugin inicializado correctamente")
    
    async def build_knowledge_graph(self, force: bool = False):
        """
        Construye o reconstruye el Knowledge Graph
        """
        if not force and self.last_build_time:
            hours_since = (datetime.now() - self.last_build_time).total_seconds() / 3600
            if hours_since < self.config.rebuild_interval_hours:
                print(f"ℹ️  KG actualizado hace {hours_since:.1f}h, no requiere rebuild")
                return
        
        print(f"📊 Construyendo Knowledge Graph en: {self.config.project_path}")
        
        self.kg = ProjectKnowledgeGraph(
            project_path=self.config.project_path,
            base_uri="http://ama-intent.dev/kg"
        )
        
        self.kg.build_graph(file_patterns=self.config.file_patterns)
        self.last_build_time = datetime.now()
        
        metrics = self.kg.get_complexity_metrics()
        print(f"✅ KG construido: {metrics['total_functions']} funciones, {metrics['total_classes']} clases")
        
        # Exportar
        export_path = Path("./data/kg")
        export_path.mkdir(parents=True, exist_ok=True)
        self.kg.export_to_json(export_path / "project_kg.json")
        
        if self.config.enable_rdf:
            self.kg.export_to_rdf(export_path / "project_kg.ttl")
    
    async def query_with_ama_integration(self, user_query: str) -> KGQueryResult:
        """
        Ejecuta query usando GraphRAG
        """
        if not self.graph_rag:
            raise RuntimeError("GraphRAG no inicializado. Ejecuta initialize() primero")
        
        query_type, entities = self.graph_rag.classifier.classify(user_query)
        
        if not entities:
            return KGQueryResult(
                query=user_query,
                answer="No pude identificar entidades en tu pregunta",
                query_type="unknown",
                entities_found=[],
                context_used={},
                timestamp=datetime.now().isoformat(),
                confidence=0.0
            )
        
        answer = await self.graph_rag.query(user_query)
        
        result = KGQueryResult(
            query=user_query,
            answer=answer,
            query_type=query_type.value,
            entities_found=entities,
            context_used={"kg_nodes": len(self.kg.entities)},
            timestamp=datetime.now().isoformat(),
            confidence=1.0
        )
        
        self.query_history.append(result)
        return result
    
    async def analyze_code_with_kg_context(self, file_path: str, code: str) -> Dict[str, Any]:
        """
        Analiza código usando contexto del KG
        """
        file_entities = [e for e in self.kg.entities if e.file_path == file_path]
        
        dependencies = {}
        for entity in file_entities:
            deps = self.kg.query_dependencies(entity.name)
            dependencies[entity.name] = deps
        
        impact = {}
        for entity in file_entities:
            affected = self.kg.impact_analysis(entity.name)
            if len(affected) > 0:
                impact[entity.name] = list(affected)
        
        patterns = [e for e in self.kg.entities 
                   if e.type == NodeType.PATTERN 
                   and e.file_path == file_path]
        
        return {
            "file_path": file_path,
            "entities": [{"name": e.name, "type": e.type.value, "line": e.line_number} for e in file_entities],
            "dependencies": dependencies,
            "impact_analysis": impact,
            "patterns": [{"name": p.name, "type": p.metadata.get("pattern_type")} for p in patterns],
            "risk_score": self._calculate_risk_score(file_entities, impact)
        }
    
    def _calculate_risk_score(self, entities: List, impact: Dict) -> float:
        total_affected = sum(len(affected) for affected in impact.values())
        return min(1.0, total_affected / 20.0)
    
    async def suggest_refactoring_opportunities(self) -> List[Dict[str, Any]]:
        """
        Sugiere oportunidades de refactorización usando el KG
        """
        suggestions = []
        
        # 1. Detectar dependencias circulares
        cycles = self.kg.find_circular_dependencies()
        for cycle in cycles:
            suggestions.append({
                "type": "circular_dependency",
                "severity": "high",
                "description": f"Dependencia circular detectada: {' -> '.join(cycle)}",
                "entities": cycle,
                "recommendation": "Refactorizar para eliminar el ciclo"
            })
        
        # 2. Detectar alta complejidad
        metrics = self.kg.get_complexity_metrics()
        if metrics['avg_degree'] > 5:
            suggestions.append({
                "type": "high_coupling",
                "severity": "medium",
                "description": f"El proyecto tiene un acoplamiento alto (grado promedio: {metrics['avg_degree']:.2f})",
                "recommendation": "Considerar desacoplar componentes mediante interfaces o eventos"
            })
            
        return suggestions
