"""
GraphRAG System para AMA-Intent
Retrieval-Augmented Generation usando Knowledge Graph
Integración con LLM Hub para respuestas contextuales sobre código
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import networkx as nx
import re

# Importaciones locales
try:
    from .project_kg import ProjectKnowledgeGraph, CodeEntity, NodeType, RelationType
except ImportError:
    # Para ejecución directa o tests
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from project_kg import ProjectKnowledgeGraph, CodeEntity, NodeType, RelationType


class QueryType(Enum):
    """Tipos de consultas soportadas"""
    WHAT_IS = "what_is"  # ¿Qué es X?
    HOW_WORKS = "how_works"  # ¿Cómo funciona X?
    WHERE_USED = "where_used"  # ¿Dónde se usa X?
    DEPENDENCIES = "dependencies"  # ¿De qué depende X?
    IMPACT = "impact"  # ¿Qué afecta si cambio X?
    PATTERNS = "patterns"  # ¿Qué patrones usa X?
    EXAMPLES = "examples"  # Dame ejemplos de uso de X
    REFACTOR = "refactor"  # ¿Cómo mejorar X?


@dataclass
class SubgraphContext:
    """Contexto extraído del subgrafo relevante"""
    central_entity: str
    related_entities: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    code_snippets: List[str]
    metadata: Dict[str, Any]
    
    def serialize(self) -> str:
        """Serializa el contexto para el LLM"""
        context = f"# Análisis de: {self.central_entity}\n\n"
        
        # Entidades relacionadas
        if self.related_entities:
            context += "## Entidades Relacionadas:\n"
            for entity in self.related_entities[:10]:  # Top 10
                context += f"- {entity['name']} ({entity['type']})\n"
                if entity.get('docstring'):
                    context += f"  Doc: {entity['docstring'][:100]}...\n"
        
        # Relaciones
        if self.relations:
            context += "\n## Relaciones:\n"
            for rel in self.relations[:15]:
                context += f"- {rel['source']} --[{rel['type']}]--> {rel['target']}\n"
        
        # Snippets de código
        if self.code_snippets:
            context += "\n## Fragmentos de Código Relevantes:\n"
            for i, snippet in enumerate(self.code_snippets[:3], 1):
                context += f"\n### Snippet {i}:\n```python\n{snippet}\n```\n"
        
        return context


class QueryClassifier:
    """
    Clasifica queries en lenguaje natural
    Detecta intención y entidades clave
    """
    
    def __init__(self, llm_hub=None):
        self.llm = llm_hub
        
        # Patrones simples (se pueden mejorar con LLM)
        self.patterns = {
            QueryType.WHAT_IS: ["qué es", "what is", "define", "explicar"],
            QueryType.HOW_WORKS: ["cómo funciona", "how works", "cómo opera"],
            QueryType.WHERE_USED: ["dónde se usa", "where used", "quién llama"],
            QueryType.DEPENDENCIES: ["depende de", "depends on", "necesita"],
            QueryType.IMPACT: ["impacto", "impact", "qué afecta", "rompe"],
            QueryType.PATTERNS: ["patrones", "patterns", "diseño"],
            QueryType.EXAMPLES: ["ejemplos", "examples", "cómo usar"],
            QueryType.REFACTOR: ["mejorar", "refactor", "optimizar"]
        }
    
    def classify(self, query: str) -> Tuple[QueryType, List[str]]:
        """
        Clasifica el query y extrae entidades
        """
        query_lower = query.lower()
        
        # Clasificar tipo
        detected_type = QueryType.WHAT_IS  # Default
        
        for qtype, keywords in self.patterns.items():
            if any(kw in query_lower for kw in keywords):
                detected_type = qtype
                break
        
        # Extraer entidades (nombres en mayúsculas, CamelCase, snake_case)
        # Patrones para nombres de código
        camel_case = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', query)
        snake_case = re.findall(r'\b[a-z]+(?:_[a-z]+)+\b', query)
        upper_case = re.findall(r'\b[A-Z_]{2,}\b', query)
        
        entities = list(set(camel_case + snake_case + upper_case))
        
        return detected_type, entities


class SubgraphRetriever:
    """
    Recupera subgrafos relevantes del KG
    """
    
    def __init__(self, kg: ProjectKnowledgeGraph):
        self.kg = kg
    
    def retrieve_for_query(self, query_type: QueryType, 
                          entity: str, 
                          max_depth: int = 2) -> SubgraphContext:
        """
        Recupera subgrafo según el tipo de query
        """
        if query_type == QueryType.WHAT_IS:
            return self._retrieve_entity_info(entity)
        elif query_type == QueryType.HOW_WORKS:
            return self._retrieve_implementation(entity)
        elif query_type == QueryType.WHERE_USED:
            return self._retrieve_usage(entity)
        elif query_type == QueryType.DEPENDENCIES:
            return self._retrieve_dependencies(entity)
        elif query_type == QueryType.IMPACT:
            return self._retrieve_impact(entity, max_depth)
        elif query_type == QueryType.PATTERNS:
            return self._retrieve_patterns(entity)
        else:
            return self._retrieve_general(entity, max_depth)
    
    def _retrieve_entity_info(self, entity: str) -> SubgraphContext:
        """Información básica de la entidad"""
        entity_data = next((e for e in self.kg.entities if e.name == entity), None)
        
        if not entity_data:
            return SubgraphContext(entity, [], [], [], {"found": False})
        
        related = []
        relations = []
        
        for rel in self.kg.relations:
            if rel.source == entity:
                relations.append({
                    "source": rel.source,
                    "target": rel.target,
                    "type": rel.relation_type.value
                })
                
                target_e = next((e for e in self.kg.entities if e.name == rel.target), None)
                if target_e:
                    related.append({
                        "name": target_e.name,
                        "type": target_e.type.value,
                        "docstring": target_e.docstring
                    })
        
        return SubgraphContext(
            central_entity=entity,
            related_entities=related,
            relations=relations,
            code_snippets=[],
            metadata={
                "type": entity_data.type.value,
                "file": entity_data.file_path,
                "line": entity_data.line_number,
                "docstring": entity_data.docstring
            }
        )

    def _retrieve_implementation(self, entity: str) -> SubgraphContext:
        context = self._retrieve_entity_info(entity)
        internal_calls = [
            {"source": r.source, "target": r.target, "type": "calls"}
            for r in self.kg.relations 
            if r.source == entity and r.relation_type.value == "calls"
        ]
        context.relations.extend(internal_calls)
        return context

    def _retrieve_usage(self, entity: str) -> SubgraphContext:
        context = self._retrieve_entity_info(entity)
        callers = []
        for rel in self.kg.relations:
            if rel.target == entity and rel.relation_type.value == "calls":
                callers.append({"source": rel.source, "target": rel.target, "type": "calls"})
                caller_e = next((e for e in self.kg.entities if e.name == rel.source), None)
                if caller_e:
                    context.related_entities.append({
                        "name": caller_e.name,
                        "type": caller_e.type.value,
                        "file": caller_e.file_path
                    })
        context.relations = callers
        return context

    def _retrieve_dependencies(self, entity: str) -> SubgraphContext:
        deps = self.kg.query_dependencies(entity)
        context = self._retrieve_entity_info(entity)
        for dep_type, dep_list in deps.items():
            for dep in dep_list:
                context.relations.append({"source": entity, "target": dep, "type": dep_type})
        return context

    def _retrieve_impact(self, entity: str, max_depth: int) -> SubgraphContext:
        affected = self.kg.impact_analysis(entity, max_depth)
        context = self._retrieve_entity_info(entity)
        context.metadata["affected_entities"] = list(affected)
        for affected_name in list(affected)[:20]:
            aff_e = next((e for e in self.kg.entities if e.name == affected_name), None)
            if aff_e:
                context.related_entities.append({
                    "name": aff_e.name, "type": aff_e.type.value, "file": aff_e.file_path
                })
        return context

    def _retrieve_patterns(self, entity: str) -> SubgraphContext:
        context = self._retrieve_entity_info(entity)
        patterns = [e for e in self.kg.entities if e.type == NodeType.PATTERN and 
                   (e.metadata.get('class') == entity or e.metadata.get('function') == entity)]
        for p in patterns:
            context.related_entities.append({
                "name": p.name, "type": "pattern", "pattern_type": p.metadata.get("pattern_type")
            })
        return context

    def _retrieve_general(self, entity: str, max_depth: int) -> SubgraphContext:
        return self._retrieve_entity_info(entity)


class GraphRAG:
    """
    Orquestador de GraphRAG
    """
    
    def __init__(self, kg: ProjectKnowledgeGraph, llm_hub=None):
        self.kg = kg
        self.llm = llm_hub
        self.classifier = QueryClassifier(llm_hub)
        self.retriever = SubgraphRetriever(kg)
        
    async def query(self, user_query: str) -> str:
        """
        Procesa una query completa
        """
        # 1. Clasificar y extraer entidades
        query_type, entities = self.classifier.classify(user_query)
        
        if not entities:
            return "No pude identificar ninguna entidad de código en tu pregunta. Por favor, especifica una clase, función o módulo."
            
        # 2. Recuperar contexto para cada entidad
        full_context = ""
        for entity in entities:
            subgraph = self.retriever.retrieve_for_query(query_type, entity)
            full_context += subgraph.serialize() + "\n---\n"
            
        # 3. Generar respuesta con LLM
        if self.llm:
            prompt = f"""
            Eres un experto arquitecto de software analizando el proyecto AMA-Intent.
            Usa el siguiente contexto extraído del Grafo de Conocimiento del código para responder la pregunta del usuario.
            
            Contexto:
            {full_context}
            
            Pregunta: {user_query}
            
            Respuesta técnica y detallada:
            """
            # Aquí se llamaría al LLM real
            # return await self.llm.generate(prompt)
            return f"[Simulación] Respuesta basada en el contexto de {', '.join(entities)} para una consulta de tipo {query_type.value}."
        else:
            return f"He encontrado información sobre {', '.join(entities)}. (LLM no configurado para generar respuesta completa)"
