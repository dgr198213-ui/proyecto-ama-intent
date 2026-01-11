"""
Project Knowledge Graph System para AMA-Intent
Construcción automática de grafos de conocimiento del código
Integración con GraphRAG para análisis profundo
"""

import ast
import json
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

try:
    from rdflib import Graph, Literal, Namespace, URIRef
    from rdflib.namespace import OWL, RDF, RDFS

    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False


class NodeType(Enum):
    """Tipos de nodos en el grafo de conocimiento"""

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    DECORATOR = "decorator"
    PATTERN = "pattern"  # Design patterns detectados


class RelationType(Enum):
    """Tipos de relaciones entre nodos"""

    IMPORTS = "imports"
    DEFINES = "defines"
    CALLS = "calls"
    INHERITS = "inherits"
    USES = "uses"
    DEPENDS_ON = "depends_on"
    IMPLEMENTS = "implements"
    DECORATED_BY = "decorated_by"
    HAS_PARAMETER = "has_parameter"
    RETURNS = "returns"
    RAISES = "raises"


@dataclass
class CodeEntity:
    """Representa una entidad en el código"""

    name: str
    type: NodeType
    file_path: str
    line_number: int
    docstring: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_uri(self, base_uri: str) -> str:
        """Genera URI única para la entidad"""
        safe_path = self.file_path.replace("/", "_").replace(".", "_")
        return (
            f"{base_uri}/{self.type.value}/{safe_path}_{self.name}_{self.line_number}"
        )


@dataclass
class CodeRelation:
    """Representa una relación entre entidades"""

    source: str  # URI o nombre
    target: str
    relation_type: RelationType
    metadata: Dict[str, Any] = field(default_factory=dict)


class ASTAnalyzer(ast.NodeVisitor):
    """
    Analiza AST de Python para extraer entidades y relaciones
    """

    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.entities: List[CodeEntity] = []
        self.relations: List[CodeRelation] = []
        self.current_class: Optional[str] = None
        self.imports: Dict[str, str] = {}  # alias -> module

    def analyze(self) -> Tuple[List[CodeEntity], List[CodeRelation]]:
        """Ejecuta el análisis del AST"""
        try:
            tree = ast.parse(self.source_code)
            self.visit(tree)
        except SyntaxError as e:
            print(f"Error parsing {self.file_path}: {e}")

        return self.entities, self.relations

    def visit_Import(self, node: ast.Import):
        """Procesa declaraciones import"""
        for alias in node.names:
            module_name = alias.name
            alias_name = alias.asname or alias.name

            self.imports[alias_name] = module_name

            entity = CodeEntity(
                name=module_name,
                type=NodeType.IMPORT,
                file_path=self.file_path,
                line_number=node.lineno,
                metadata={"alias": alias_name},
            )
            self.entities.append(entity)

            self.relations.append(
                CodeRelation(
                    source=self.file_path,
                    target=module_name,
                    relation_type=RelationType.IMPORTS,
                )
            )

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Procesa declaraciones from X import Y"""
        module = node.module or ""

        for alias in node.names:
            name = alias.name
            alias_name = alias.asname or name

            full_name = f"{module}.{name}" if module else name
            self.imports[alias_name] = full_name

            entity = CodeEntity(
                name=full_name,
                type=NodeType.IMPORT,
                file_path=self.file_path,
                line_number=node.lineno,
                metadata={"from": module, "alias": alias_name},
            )
            self.entities.append(entity)

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Procesa definiciones de clase"""
        entity = CodeEntity(
            name=node.name,
            type=NodeType.CLASS,
            file_path=self.file_path,
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            metadata={
                "bases": [self._get_name(base) for base in node.bases],
                "decorators": [self._get_name(dec) for dec in node.decorator_list],
            },
        )
        self.entities.append(entity)

        # Relaciones de herencia
        for base in node.bases:
            base_name = self._get_name(base)
            self.relations.append(
                CodeRelation(
                    source=node.name,
                    target=base_name,
                    relation_type=RelationType.INHERITS,
                )
            )

        # Decoradores
        for decorator in node.decorator_list:
            dec_name = self._get_name(decorator)
            self.relations.append(
                CodeRelation(
                    source=node.name,
                    target=dec_name,
                    relation_type=RelationType.DECORATED_BY,
                )
            )

        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Procesa definiciones de función/método"""
        is_method = self.current_class is not None

        entity = CodeEntity(
            name=node.name,
            type=NodeType.METHOD if is_method else NodeType.FUNCTION,
            file_path=self.file_path,
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            metadata={
                "class": self.current_class,
                "parameters": [arg.arg for arg in node.args.args],
                "decorators": [self._get_name(dec) for dec in node.decorator_list],
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            },
        )
        self.entities.append(entity)

        # Analizar llamadas dentro de la función
        call_visitor = CallVisitor()
        call_visitor.visit(node)

        for called_func in call_visitor.called_functions:
            self.relations.append(
                CodeRelation(
                    source=node.name,
                    target=called_func,
                    relation_type=RelationType.CALLS,
                    metadata={"in_class": self.current_class},
                )
            )

        self.generic_visit(node)

    def _get_name(self, node) -> str:
        """Extrae nombre de un nodo AST"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return str(node)


class CallVisitor(ast.NodeVisitor):
    """Visitor especializado para detectar llamadas a funciones"""

    def __init__(self):
        self.called_functions: Set[str] = set()

    def visit_Call(self, node: ast.Call):
        func_name = self._get_func_name(node.func)
        if func_name:
            self.called_functions.add(func_name)
        self.generic_visit(node)

    def _get_func_name(self, node) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_func_name(node.value)}.{node.attr}"
        return None


class PatternDetector:
    """
    Detecta patrones de diseño en el código
    """

    def __init__(self, entities: List[CodeEntity], relations: List[CodeRelation]):
        self.entities = entities
        self.relations = relations
        self.patterns: List[CodeEntity] = []

    def detect_patterns(self) -> List[CodeEntity]:
        """Detecta patrones conocidos"""
        self._detect_singleton()
        self._detect_factory()
        self._detect_decorator_pattern()
        self._detect_observer()

        return self.patterns

    def _detect_singleton(self):
        """Detecta patrón Singleton"""
        for entity in self.entities:
            if entity.type != NodeType.CLASS:
                continue

            # Buscar método __new__ o _instance
            has_instance_control = False

            methods = [
                e
                for e in self.entities
                if e.type == NodeType.METHOD and e.metadata.get("class") == entity.name
            ]

            for method in methods:
                if method.name in ["__new__", "get_instance", "instance"]:
                    has_instance_control = True
                    break

            if has_instance_control:
                pattern = CodeEntity(
                    name=f"Singleton_{entity.name}",
                    type=NodeType.PATTERN,
                    file_path=entity.file_path,
                    line_number=entity.line_number,
                    metadata={"pattern_type": "Singleton", "class": entity.name},
                )
                self.patterns.append(pattern)

    def _detect_factory(self):
        """Detecta patrón Factory"""
        for entity in self.entities:
            if entity.type != NodeType.FUNCTION:
                continue

            # Buscar funciones create_*, make_*, build_*
            if any(
                entity.name.startswith(prefix)
                for prefix in ["create_", "make_", "build_", "factory_"]
            ):

                pattern = CodeEntity(
                    name=f"Factory_{entity.name}",
                    type=NodeType.PATTERN,
                    file_path=entity.file_path,
                    line_number=entity.line_number,
                    metadata={"pattern_type": "Factory", "function": entity.name},
                )
                self.patterns.append(pattern)

    def _detect_decorator_pattern(self):
        """Detecta patrón Decorator"""
        for entity in self.entities:
            if entity.type != NodeType.CLASS:
                continue

            # Si hereda de algo y recibe una instancia del mismo tipo en __init__
            bases = entity.metadata.get("bases", [])
            if not bases:
                continue

            init_method = next(
                (
                    e
                    for e in self.entities
                    if e.type == NodeType.METHOD
                    and e.metadata.get("class") == entity.name
                    and e.name == "__init__"
                ),
                None,
            )

            if init_method:
                # Análisis simplificado
                pattern = CodeEntity(
                    name=f"Decorator_{entity.name}",
                    type=NodeType.PATTERN,
                    file_path=entity.file_path,
                    line_number=entity.line_number,
                    metadata={"pattern_type": "Decorator", "class": entity.name},
                )
                self.patterns.append(pattern)

    def _detect_observer(self):
        """Detecta patrón Observer"""
        for entity in self.entities:
            if entity.type != NodeType.CLASS:
                continue

            methods = [
                e.name
                for e in self.entities
                if e.type == NodeType.METHOD and e.metadata.get("class") == entity.name
            ]

            if any(m in ["attach", "detach", "notify", "subscribe"] for m in methods):
                pattern = CodeEntity(
                    name=f"Observer_{entity.name}",
                    type=NodeType.PATTERN,
                    file_path=entity.file_path,
                    line_number=entity.line_number,
                    metadata={"pattern_type": "Observer", "class": entity.name},
                )
                self.patterns.append(pattern)


class ProjectKnowledgeGraph:
    """
    Gestiona el Grafo de Conocimiento del Proyecto
    """

    def __init__(self, project_path: str, base_uri: str = "http://ama-intent.dev/kg"):
        self.project_path = Path(project_path)
        self.base_uri = base_uri
        self.entities: List[CodeEntity] = []
        self.relations: List[CodeRelation] = []
        self.graph = nx.MultiDiGraph()

    def build_graph(self, file_patterns: List[str] = ["**/*.py"]):
        """Construye el grafo analizando los archivos del proyecto"""
        print(f"Analizando proyecto en {self.project_path}...")

        for pattern in file_patterns:
            for file_path in self.project_path.glob(pattern):
                if any(
                    part.startswith(".") or part == "venv" or part == "__pycache__"
                    for part in file_path.parts
                ):
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        source = f.read()

                    analyzer = ASTAnalyzer(
                        str(file_path.relative_to(self.project_path)), source
                    )
                    entities, relations = analyzer.analyze()

                    self.entities.extend(entities)
                    self.relations.extend(relations)
                except Exception as e:
                    print(f"Error analizando {file_path}: {e}")

        # Detectar patrones
        detector = PatternDetector(self.entities, self.relations)
        patterns = detector.detect_patterns()
        self.entities.extend(patterns)

        # Construir grafo NetworkX
        self._sync_to_networkx()

    def _sync_to_networkx(self):
        """Sincroniza entidades y relaciones con NetworkX"""
        self.graph.clear()

        for entity in self.entities:
            self.graph.add_node(
                entity.name,
                type=entity.type.value,
                file=entity.file_path,
                line=entity.line_number,
                docstring=entity.docstring,
                **entity.metadata,
            )

        for rel in self.relations:
            self.graph.add_edge(
                rel.source, rel.target, type=rel.relation_type.value, **rel.metadata
            )

    def query_dependencies(self, entity_name: str) -> Dict[str, List[str]]:
        """Busca dependencias de una entidad"""
        deps = defaultdict(list)

        if entity_name not in self.graph:
            return dict(deps)

        for _, target, data in self.graph.out_edges(entity_name, data=True):
            deps[data["type"]].append(target)

        return dict(deps)

    def impact_analysis(self, entity_name: str, max_depth: int = 3) -> Set[str]:
        """Analiza qué entidades se ven afectadas si cambia esta entidad"""
        if entity_name not in self.graph:
            return set()

        # En un grafo de dependencias, el impacto viaja en dirección opuesta a las llamadas
        # Usamos el grafo invertido para encontrar quién depende de nosotros
        reverse_graph = self.graph.reverse()

        affected = set()
        try:
            # BFS para encontrar nodos alcanzables en el grafo invertido
            nodes = nx.single_source_shortest_path_length(
                reverse_graph, entity_name, cutoff=max_depth
            )
            affected = set(nodes.keys()) - {entity_name}
        except Exception:
            pass

        return affected

    def find_circular_dependencies(self) -> List[List[str]]:
        """Detecta ciclos en el grafo de dependencias"""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except Exception:
            return []

    def get_complexity_metrics(self) -> Dict[str, Any]:
        """Calcula métricas de complejidad del proyecto"""
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "total_classes": len(
                [e for e in self.entities if e.type == NodeType.CLASS]
            ),
            "total_functions": len(
                [
                    e
                    for e in self.entities
                    if e.type in [NodeType.FUNCTION, NodeType.METHOD]
                ]
            ),
            "total_patterns": len(
                [e for e in self.entities if e.type == NodeType.PATTERN]
            ),
            "avg_degree": (
                sum(dict(self.graph.degree()).values()) / len(self.graph.nodes())
                if self.graph.nodes()
                else 0
            ),
            "density": nx.density(self.graph),
        }

    def export_to_json(self, path: Path):
        """Exporta el KG a JSON"""
        data = {
            "entities": [
                {
                    "name": e.name,
                    "type": e.type.value,
                    "file": e.file_path,
                    "line": e.line_number,
                    "docstring": e.docstring,
                    "metadata": e.metadata,
                }
                for e in self.entities
            ],
            "relations": [
                {
                    "source": r.source,
                    "target": r.target,
                    "type": r.relation_type.value,
                    "metadata": r.metadata,
                }
                for r in self.relations
            ],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def export_to_rdf(self, path: Path, format: str = "turtle"):
        """Exporta el KG a formato RDF (requiere rdflib)"""
        if not RDFLIB_AVAILABLE:
            print("rdflib no instalado. No se puede exportar a RDF.")
            return

        g = Graph()
        NS = Namespace(f"{self.base_uri}/")
        CODE = Namespace("http://ama-intent.dev/ontology/code#")

        g.bind("ama", NS)
        g.bind("code", CODE)

        for entity in self.entities:
            uri = URIRef(entity.to_uri(self.base_uri))
            g.add((uri, RDF.type, CODE[entity.type.value.capitalize()]))
            g.add((uri, RDFS.label, Literal(entity.name)))
            g.add((uri, CODE.filePath, Literal(entity.file_path)))

        for rel in self.relations:
            # Simplificación: buscar URIs por nombre
            source_entities = [e for e in self.entities if e.name == rel.source]
            target_entities = [e for e in self.entities if e.name == rel.target]

            if source_entities and target_entities:
                source_uri = URIRef(source_entities[0].to_uri(self.base_uri))
                target_uri = URIRef(target_entities[0].to_uri(self.base_uri))
                predicate = CODE[rel.relation_type.value]
                g.add((source_uri, predicate, target_uri))

        g.serialize(destination=str(path), format=format)
