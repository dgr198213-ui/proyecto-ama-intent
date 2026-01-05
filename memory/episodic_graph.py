# memory/episodic_graph.py - Memoria Episódica con Grafo y PageRank
"""
Implementa memoria episódica como grafo Gₜ con recuperación basada en:
Score(v) = sim(zₜ, v) ⊕ PageRank(G) ⊕ LFPI(v) ⊕ LSI(v)

Este módulo simula el hipocampo: almacena episodios con contexto
y los recupera según relevancia estructural.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

@dataclass
class Episode:
    """Episodio individual en memoria"""
    id: str
    state: np.ndarray          # Estado zₜ cuando ocurrió
    context: Dict              # Contexto (acción, recompensa, etc.)
    timestamp: str
    access_count: int = 0
    last_accessed: Optional[str] = None
    importance: float = 1.0    # Peso inicial
    
    # Metadata
    tags: Set[str] = field(default_factory=set)
    embedding: Optional[np.ndarray] = None

@dataclass
class MemoryEdge:
    """Arista entre episodios"""
    source: str
    target: str
    weight: float
    edge_type: str  # "temporal", "causal", "similarity"

class EpisodicMemoryGraph:
    """
    Memoria Episódica basada en Grafo con PageRank.
    
    Funcionalidades:
    1. Almacenar episodios como nodos
    2. Crear conexiones basadas en similaridad, temporalidad, causalidad
    3. Recuperar TopK episodios usando score compuesto
    4. Actualizar importancia con PageRank
    5. Poda adaptativa de episodios irrelevantes
    """
    
    def __init__(self, 
                 max_episodes: int = 10000,
                 similarity_threshold: float = 0.7):
        """
        Args:
            max_episodes: capacidad máxima de memoria
            similarity_threshold: umbral para crear conexiones
        """
        self.max_episodes = max_episodes
        self.similarity_threshold = similarity_threshold
        
        # Almacenamiento
        self.episodes: Dict[str, Episode] = {}
        self.edges: List[MemoryEdge] = []
        
        # Índices
        self.adjacency: Dict[str, List[str]] = {}  # Para PageRank
        self.temporal_order: List[str] = []         # Orden cronológico
        
        # PageRank cache
        self.pagerank_scores: Dict[str, float] = {}
        self.pagerank_dirty = True
        
        # Estadísticas
        self.total_stored = 0
        self.total_pruned = 0
    
    def add_episode(self,
                   state: np.ndarray,
                   context: Dict,
                   tags: Optional[Set[str]] = None,
                   importance: float = 1.0) -> str:
        """
        Añade un episodio a la memoria.
        
        Args:
            state: estado cortical zₜ
            context: información contextual (acción, reward, etc.)
            tags: etiquetas semánticas
            importance: peso inicial
        
        Returns:
            episode_id: identificador del episodio
        """
        # Generar ID único
        timestamp = datetime.now().isoformat()
        episode_id = self._generate_episode_id(state, timestamp)
        
        # Crear episodio
        episode = Episode(
            id=episode_id,
            state=state.copy(),
            context=context.copy(),
            timestamp=timestamp,
            importance=importance,
            tags=tags or set()
        )
        
        # Almacenar
        self.episodes[episode_id] = episode
        self.temporal_order.append(episode_id)
        self.adjacency[episode_id] = []
        
        # Crear conexiones con episodios existentes
        self._create_connections(episode_id)
        
        self.total_stored += 1
        self.pagerank_dirty = True
        
        # Verificar capacidad
        if len(self.episodes) > self.max_episodes:
            self._prune_least_important()
        
        return episode_id
    
    def _generate_episode_id(self, state: np.ndarray, timestamp: str) -> str:
        """Genera ID único para episodio"""
        content = f"{state.tobytes()}{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _create_connections(self, new_episode_id: str):
        """
        Crea conexiones entre el nuevo episodio y los existentes.
        
        Tipos de conexiones:
        1. Temporal: episodios cercanos en tiempo
        2. Similarity: episodios con estados similares
        3. Causal: episodios relacionados por contexto
        """
        new_episode = self.episodes[new_episode_id]
        new_state = new_episode.state
        
        # Conectar con episodios recientes y similares
        recent_ids = self.temporal_order[-20:]  # Últimos 20
        
        for ep_id in recent_ids:
            if ep_id == new_episode_id:
                continue
            
            episode = self.episodes[ep_id]
            
            # 1. Conexión temporal (episodios consecutivos)
            if ep_id == self.temporal_order[-2]:
                self._add_edge(ep_id, new_episode_id, weight=0.8, edge_type="temporal")
            
            # 2. Conexión por similaridad
            similarity = self._compute_similarity(new_state, episode.state)
            if similarity > self.similarity_threshold:
                weight = similarity
                self._add_edge(ep_id, new_episode_id, weight=weight, edge_type="similarity")
            
            # 3. Conexión causal (mismo tag o contexto)
            if new_episode.tags.intersection(episode.tags):
                self._add_edge(ep_id, new_episode_id, weight=0.6, edge_type="causal")
    
    def _add_edge(self, source: str, target: str, weight: float, edge_type: str):
        """Añade arista al grafo"""
        edge = MemoryEdge(
            source=source,
            target=target,
            weight=weight,
            edge_type=edge_type
        )
        self.edges.append(edge)
        
        # Actualizar adjacency
        if source in self.adjacency:
            self.adjacency[source].append(target)
        if target not in self.adjacency:
            self.adjacency[target] = []
    
    def _compute_similarity(self, state1: np.ndarray, state2: np.ndarray) -> float:
        """Calcula similaridad coseno entre estados"""
        norm1 = np.linalg.norm(state1)
        norm2 = np.linalg.norm(state2)
        
        if norm1 < 1e-9 or norm2 < 1e-9:
            return 0.0
        
        similarity = np.dot(state1, state2) / (norm1 * norm2)
        return float(np.clip(similarity, 0.0, 1.0))
    
    def compute_pagerank(self, 
                        damping: float = 0.85,
                        max_iterations: int = 100,
                        tolerance: float = 1e-6) -> Dict[str, float]:
        """
        Calcula PageRank para todos los episodios.
        
        PR(v) = (1-d)/N + d * Σ PR(u)/|Out(u)|
        
        Args:
            damping: factor de amortiguación
            max_iterations: máximo de iteraciones
            tolerance: convergencia
        
        Returns:
            pagerank_scores: dict de scores por episodio
        """
        if not self.pagerank_dirty and self.pagerank_scores:
            return self.pagerank_scores
        
        n = len(self.episodes)
        if n == 0:
            return {}
        
        # Inicialización uniforme
        pr = {ep_id: 1.0 / n for ep_id in self.episodes.keys()}
        
        # Iteración power method
        for iteration in range(max_iterations):
            pr_new = {}
            max_diff = 0.0
            
            for v in self.episodes.keys():
                # Contribución de nodos entrantes
                incoming_sum = 0.0
                
                for edge in self.edges:
                    if edge.target == v:
                        source = edge.source
                        out_degree = len(self.adjacency.get(source, []))
                        if out_degree > 0:
                            incoming_sum += edge.weight * pr[source] / out_degree
                
                # Fórmula PageRank
                pr_new[v] = (1 - damping) / n + damping * incoming_sum
                
                # Verificar convergencia
                max_diff = max(max_diff, abs(pr_new[v] - pr[v]))
            
            pr = pr_new
            
            if max_diff < tolerance:
                break
        
        # Normalizar
        total = sum(pr.values())
        if total > 0:
            pr = {k: v / total for k, v in pr.items()}
        
        self.pagerank_scores = pr
        self.pagerank_dirty = False
        
        return pr
    
    def retrieve(self,
                query_state: np.ndarray,
                top_k: int = 5,
                use_pagerank: bool = True,
                use_lfpi: bool = False,
                use_lsi: bool = False) -> List[Tuple[str, float, Episode]]:
        """
        Recupera TopK episodios más relevantes.
        
        Score(v) = w_sim·sim(z, v) + w_pr·PageRank(v) [+ w_lfpi·LFPI + w_lsi·LSI]
        
        Args:
            query_state: estado actual zₜ
            top_k: número de episodios a recuperar
            use_pagerank: incluir PageRank en score
            use_lfpi: incluir LFPI (eficiencia)
            use_lsi: incluir LSI (sensibilidad)
        
        Returns:
            List de (episode_id, score, episode)
        """
        if not self.episodes:
            return []
        
        # Actualizar PageRank si es necesario
        if use_pagerank:
            pr_scores = self.compute_pagerank()
        else:
            pr_scores = {ep_id: 0.0 for ep_id in self.episodes.keys()}
        
        # Calcular scores
        scores = []
        
        for ep_id, episode in self.episodes.items():
            # 1. Similaridad
            sim_score = self._compute_similarity(query_state, episode.state)
            
            # 2. PageRank
            pr_score = pr_scores.get(ep_id, 0.0)
            
            # 3. LFPI (placeholder - requiere más contexto)
            lfpi_score = episode.importance if use_lfpi else 0.0
            
            # 4. LSI (placeholder - requiere gradientes)
            lsi_score = 0.0 if use_lsi else 0.0
            
            # Score compuesto (ponderado)
            w_sim = 0.5
            w_pr = 0.3 if use_pagerank else 0.0
            w_lfpi = 0.1 if use_lfpi else 0.0
            w_lsi = 0.1 if use_lsi else 0.0
            
            # Normalizar pesos
            total_weight = w_sim + w_pr + w_lfpi + w_lsi
            if total_weight > 0:
                w_sim /= total_weight
                w_pr /= total_weight
                w_lfpi /= total_weight
                w_lsi /= total_weight
            
            final_score = (w_sim * sim_score + 
                          w_pr * pr_score + 
                          w_lfpi * lfpi_score + 
                          w_lsi * lsi_score)
            
            scores.append((ep_id, final_score, episode))
            
            # Actualizar metadata de acceso
            episode.access_count += 1
            episode.last_accessed = datetime.now().isoformat()
        
        # Ordenar por score descendente
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]
    
    def _prune_least_important(self, n_to_prune: int = 100):
        """
        Poda episodios menos importantes.
        
        Criterios:
        - Bajo PageRank
        - Bajo acceso
        - Antigüedad
        """
        if len(self.episodes) <= n_to_prune:
            return
        
        # Calcular score de importancia
        pr_scores = self.compute_pagerank()
        
        importance_scores = []
        for ep_id, episode in self.episodes.items():
            # Factores de importancia
            pr_factor = pr_scores.get(ep_id, 0.0)
            access_factor = min(episode.access_count / 10.0, 1.0)
            recency_factor = 1.0 / (len(self.temporal_order) - self.temporal_order.index(ep_id) + 1)
            
            importance = 0.5 * pr_factor + 0.3 * access_factor + 0.2 * recency_factor
            importance_scores.append((ep_id, importance))
        
        # Ordenar por importancia
        importance_scores.sort(key=lambda x: x[1])
        
        # Eliminar los menos importantes
        to_remove = [ep_id for ep_id, _ in importance_scores[:n_to_prune]]
        
        for ep_id in to_remove:
            self._remove_episode(ep_id)
        
        self.total_pruned += len(to_remove)
        self.pagerank_dirty = True
    
    def _remove_episode(self, episode_id: str):
        """Elimina un episodio y sus conexiones"""
        if episode_id in self.episodes:
            del self.episodes[episode_id]
        
        if episode_id in self.adjacency:
            del self.adjacency[episode_id]
        
        if episode_id in self.temporal_order:
            self.temporal_order.remove(episode_id)
        
        # Eliminar aristas relacionadas
        self.edges = [e for e in self.edges 
                     if e.source != episode_id and e.target != episode_id]
        
        # Limpiar adjacency
        for adj_list in self.adjacency.values():
            if episode_id in adj_list:
                adj_list.remove(episode_id)
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas de la memoria"""
        return {
            'total_episodes': len(self.episodes),
            'total_edges': len(self.edges),
            'total_stored': self.total_stored,
            'total_pruned': self.total_pruned,
            'avg_connections': np.mean([len(adj) for adj in self.adjacency.values()]) if self.adjacency else 0,
            'memory_usage_pct': len(self.episodes) / self.max_episodes * 100
        }


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test de Memoria Episódica con PageRank ===\n")
    
    np.random.seed(42)
    
    # Crear memoria
    memory = EpisodicMemoryGraph(max_episodes=100, similarity_threshold=0.7)
    
    print("Configuración:")
    print(f"  Capacidad: {memory.max_episodes} episodios")
    print(f"  Umbral similaridad: {memory.similarity_threshold}")
    
    # Almacenar episodios simulados
    print("\n--- Almacenando Episodios ---")
    
    for i in range(20):
        state = np.random.randn(32) * 0.5
        context = {
            'action': f'action_{i}',
            'reward': np.random.rand(),
            'step': i
        }
        tags = {f'tag_{i % 3}'}  # Tags repetidos para crear clusters
        
        ep_id = memory.add_episode(state, context, tags=tags, importance=1.0)
        
        if i < 3:
            print(f"  Episodio {i+1}: {ep_id[:8]}... almacenado")
    
    print(f"  ... ({len(memory.episodes)} episodios totales)")
    
    # Calcular PageRank
    print("\n--- Calculando PageRank ---")
    pr_scores = memory.compute_pagerank()
    
    top_pr = sorted(pr_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    print("Top 3 episodios por PageRank:")
    for ep_id, score in top_pr:
        print(f"  {ep_id[:8]}: {score:.4f}")
    
    # Recuperar episodios
    print("\n--- Recuperación de Episodios ---")
    query_state = np.random.randn(32) * 0.5
    
    results = memory.retrieve(query_state, top_k=5, use_pagerank=True)
    
    print(f"Query state norm: {np.linalg.norm(query_state):.3f}")
    print(f"\nTop 5 episodios recuperados:")
    for i, (ep_id, score, episode) in enumerate(results):
        print(f"  {i+1}. {ep_id[:8]} - Score: {score:.4f}")
        print(f"     Context: {episode.context['action']}")
        print(f"     Accesos: {episode.access_count}")
    
    # Estadísticas
    print("\n--- Estadísticas de Memoria ---")
    stats = memory.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ Memoria Episódica funcional - Hipocampo activo")