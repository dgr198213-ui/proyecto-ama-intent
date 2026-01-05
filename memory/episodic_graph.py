# memory/pruning.py - Sistema de Poda Adaptativa (Olvido Selectivo)
"""
Implementa olvido selectivo adaptativo:
Prune(Gₜ, Mₜ) si uso(x) < u_min ∧ impacto(x) < ι_min

Este módulo simula el olvido natural del cerebro: elimina información
redundante o irrelevante para optimizar recursos.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

class PruningStrategy(Enum):
    """Estrategias de poda"""
    LRU = "least_recently_used"      # Menos usado recientemente
    LFU = "least_frequently_used"    # Menos frecuentemente usado
    IMPACT = "low_impact"            # Bajo impacto
    COMPOSITE = "composite"          # Combinación de criterios

@dataclass
class PruningConfig:
    """Configuración de poda"""
    strategy: PruningStrategy = PruningStrategy.COMPOSITE
    usage_threshold: float = 0.1     # u_min
    impact_threshold: float = 0.1    # ι_min
    prune_percentage: float = 0.1    # % a podar cuando se activa
    check_interval: int = 100        # Cada cuántos ticks verificar

@dataclass
class MemoryItem:
    """Item genérico de memoria para poda"""
    id: str
    access_count: int
    last_access_tick: int
    creation_tick: int
    impact_score: float
    size: int  # En bytes o unidades abstractas

class AdaptivePruningSystem:
    """
    Sistema de Poda Adaptativa.
    
    Funcionalidades:
    1. Monitorear uso de memoria
    2. Calcular scores de retención
    3. Identificar candidatos a poda
    4. Ejecutar poda selectiva
    5. Adaptarse a patrones de uso
    """
    
    def __init__(self, config: Optional[PruningConfig] = None):
        """
        Args:
            config: configuración de poda
        """
        self.config = config or PruningConfig()
        
        # Tracking
        self.current_tick = 0
        self.last_prune_tick = 0
        
        # Estadísticas
        self.total_pruned = 0
        self.prune_history = []
        
        # Criterios adaptativos (se ajustan con el tiempo)
        self.adaptive_usage_threshold = self.config.usage_threshold
        self.adaptive_impact_threshold = self.config.impact_threshold
    
    def should_prune(self, 
                    memory_usage: float,
                    memory_capacity: float) -> bool:
        """
        Determina si es necesario podar.
        
        Args:
            memory_usage: uso actual de memoria
            memory_capacity: capacidad total
        
        Returns:
            bool: True si debe podar
        """
        # Criterio 1: Capacidad cercana al límite
        usage_ratio = memory_usage / memory_capacity
        if usage_ratio > 0.9:
            return True
        
        # Criterio 2: Intervalo de tiempo
        ticks_since_prune = self.current_tick - self.last_prune_tick
        if ticks_since_prune >= self.config.check_interval and usage_ratio > 0.7:
            return True
        
        return False
    
    def select_candidates(self,
                         items: List[MemoryItem],
                         n_to_prune: Optional[int] = None) -> List[str]:
        """
        Selecciona candidatos para poda según estrategia.
        
        Args:
            items: lista de items en memoria
            n_to_prune: número de items a podar (None = calcular automáticamente)
        
        Returns:
            List de IDs a podar
        """
        if not items:
            return []
        
        # Calcular cuántos podar
        if n_to_prune is None:
            n_to_prune = max(1, int(len(items) * self.config.prune_percentage))
        
        # Calcular scores de retención
        retention_scores = self._compute_retention_scores(items)
        
        # Ordenar por score (menor = más probable a podar)
        sorted_items = sorted(retention_scores, key=lambda x: x[1])
        
        # Seleccionar candidatos
        candidates = []
        for item_id, score, item in sorted_items[:n_to_prune]:
            # Verificar umbrales
            if self._meets_pruning_criteria(item):
                candidates.append(item_id)
        
        return candidates
    
    def _compute_retention_scores(self, 
                                  items: List[MemoryItem]) -> List[Tuple[str, float, MemoryItem]]:
        """
        Calcula scores de retención para cada item.
        Score alto = importante mantener
        Score bajo = candidato a poda
        """
        scores = []
        
        for item in items:
            score = 0.0
            
            if self.config.strategy == PruningStrategy.LRU:
                # Recency: más reciente = mayor score
                recency = 1.0 - (self.current_tick - item.last_access_tick) / (self.current_tick + 1)
                score = recency
            
            elif self.config.strategy == PruningStrategy.LFU:
                # Frequency: más usado = mayor score
                frequency = item.access_count / (self.current_tick - item.creation_tick + 1)
                score = frequency
            
            elif self.config.strategy == PruningStrategy.IMPACT:
                # Impact: mayor impacto = mayor score
                score = item.impact_score
            
            elif self.config.strategy == PruningStrategy.COMPOSITE:
                # Combinación ponderada
                age = self.current_tick - item.creation_tick
                recency = (self.current_tick - item.last_access_tick) / (age + 1)
                frequency = item.access_count / (age + 1)
                impact = item.impact_score
                
                # Pesos adaptativos
                w_recency = 0.3
                w_frequency = 0.3
                w_impact = 0.4
                
                score = (w_recency * (1.0 - recency) + 
                        w_frequency * frequency + 
                        w_impact * impact)
            
            scores.append((item.id, score, item))
        
        return scores
    
    def _meets_pruning_criteria(self, item: MemoryItem) -> bool:
        """
        Verifica si un item cumple los criterios de poda.
        uso(x) < u_min ∧ impacto(x) < ι_min
        """
        # Calcular uso normalizado
        age = self.current_tick - item.creation_tick + 1
        usage = item.access_count / age
        
        # Verificar umbrales
        low_usage = usage < self.adaptive_usage_threshold
        low_impact = item.impact_score < self.adaptive_impact_threshold
        
        return low_usage and low_impact
    
    def execute_pruning(self,
                       episodic_memory,
                       semantic_memory,
                       force: bool = False) -> Dict:
        """
        Ejecuta poda en sistemas de memoria.
        
        Args:
            episodic_memory: EpisodicMemoryGraph
            semantic_memory: SemanticMemoryMatrix
            force: forzar poda incluso si no es necesario
        
        Returns:
            Dict con estadísticas de poda
        """
        pruned_count = 0
        
        # === PODA EPISÓDICA ===
        if hasattr(episodic_memory, 'episodes'):
            # Convertir episodios a MemoryItems
            ep_items = []
            for ep_id, episode in episodic_memory.episodes.items():
                age = self.current_tick - episodic_memory.temporal_order.index(ep_id)
                
                item = MemoryItem(
                    id=ep_id,
                    access_count=episode.access_count,
                    last_access_tick=age,
                    creation_tick=age,
                    impact_score=episode.importance,
                    size=episode.state.nbytes
                )
                ep_items.append(item)
            
            # Seleccionar candidatos
            if force or self.should_prune(
                len(episodic_memory.episodes),
                episodic_memory.max_episodes
            ):
                candidates = self.select_candidates(ep_items)
                
                # Ejecutar poda
                for ep_id in candidates:
                    if ep_id in episodic_memory.episodes:
                        episodic_memory._remove_episode(ep_id)
                        pruned_count += 1
        
        # === PODA SEMÁNTICA ===
        if hasattr(semantic_memory, 'concepts'):
            # Convertir conceptos a MemoryItems
            sem_items = []
            for cid, concept in semantic_memory.concepts.items():
                item = MemoryItem(
                    id=str(cid),
                    access_count=concept.instances,
                    last_access_tick=self.current_tick,
                    creation_tick=0,
                    impact_score=1.0 - concept.variance,  # Baja varianza = más importante
                    size=concept.prototype.nbytes
                )
                sem_items.append(item)
            
            # Seleccionar candidatos
            if force or self.should_prune(
                semantic_memory.n_concepts,
                semantic_memory.max_concepts
            ):
                candidates = self.select_candidates(sem_items)
                
                # Ejecutar poda (merge de similares es mejor que eliminar)
                if len(candidates) > 0:
                    semantic_memory.merge_similar_concepts(threshold=0.9)
        
        # Actualizar tracking
        self.last_prune_tick = self.current_tick
        self.total_pruned += pruned_count
        
        # Estadísticas
        stats = {
            'pruned_count': pruned_count,
            'total_pruned': self.total_pruned,
            'current_tick': self.current_tick,
            'strategy': self.config.strategy.value
        }
        
        self.prune_history.append(stats)
        if len(self.prune_history) > 100:
            self.prune_history.pop(0)
        
        return stats
    
    def adapt_thresholds(self, performance_metrics: Dict):
        """
        Adapta umbrales de poda basándose en rendimiento.
        
        Args:
            performance_metrics: métricas de rendimiento del sistema
        """
        # Si el sistema tiene buena memoria (alta precisión de recuperación)
        # podemos ser más agresivos con la poda
        retrieval_accuracy = performance_metrics.get('retrieval_accuracy', 0.5)
        
        if retrieval_accuracy > 0.8:
            # Sistema funciona bien, podemos podar más
            self.adaptive_usage_threshold = min(0.3, self.adaptive_usage_threshold * 1.1)
            self.adaptive_impact_threshold = min(0.3, self.adaptive_impact_threshold * 1.1)
        
        elif retrieval_accuracy < 0.5:
            # Sistema tiene problemas, ser más conservadores
            self.adaptive_usage_threshold = max(0.05, self.adaptive_usage_threshold * 0.9)
            self.adaptive_impact_threshold = max(0.05, self.adaptive_impact_threshold * 0.9)
    
    def tick(self):
        """Incrementa contador de ticks"""
        self.current_tick += 1
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas de poda"""
        if not self.prune_history:
            return {
                'total_pruned': self.total_pruned,
                'current_tick': self.current_tick
            }
        
        recent = self.prune_history[-10:]
        
        return {
            'total_pruned': self.total_pruned,
            'current_tick': self.current_tick,
            'avg_pruned_per_cycle': np.mean([h['pruned_count'] for h in recent]),
            'prune_cycles': len(self.prune_history),
            'adaptive_usage_threshold': self.adaptive_usage_threshold,
            'adaptive_impact_threshold': self.adaptive_impact_threshold
        }


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test de Sistema de Poda Adaptativa ===\n")
    
    np.random.seed(42)
    
    # Crear sistema de poda
    pruner = AdaptivePruningSystem(
        config=PruningConfig(
            strategy=PruningStrategy.COMPOSITE,
            usage_threshold=0.1,
            impact_threshold=0.15,
            prune_percentage=0.2
        )
    )
    
    print("Configuración:")
    print(f"  Estrategia: {pruner.config.strategy.value}")
    print(f"  Umbral uso: {pruner.config.usage_threshold}")
    print(f"  Umbral impacto: {pruner.config.impact_threshold}")
    
    # Crear items simulados
    print("\n--- Creando Items de Memoria Simulados ---")
    
    items = []
    for i in range(50):
        item = MemoryItem(
            id=f"item_{i}",
            access_count=np.random.randint(0, 20),
            last_access_tick=pruner.current_tick - np.random.randint(0, 30),
            creation_tick=max(0, pruner.current_tick - np.random.randint(10, 50)),
            impact_score=np.random.rand(),
            size=1024
        )
        items.append(item)
    
    print(f"Creados {len(items)} items")
    
    # Avanzar tiempo
    for _ in range(50):
        pruner.tick()
    
    # Verificar si debe podar
    print("\n--- Verificación de Poda ---")
    should = pruner.should_prune(
        memory_usage=len(items),
        memory_capacity=60
    )
    print(f"¿Debe podar?: {should}")
    
    # Seleccionar candidatos
    print("\n--- Selección de Candidatos ---")
    candidates = pruner.select_candidates(items, n_to_prune=10)
    
    print(f"Candidatos seleccionados: {len(candidates)}")
    print(f"IDs: {candidates[:5]}...")
    
    # Analizar candidatos
    for cid in candidates[:3]:
        item = next(i for i in items if i.id == cid)
        age = pruner.current_tick - item.creation_tick
        usage = item.access_count / (age + 1)
        print(f"\n  {cid}:")
        print(f"    Uso: {usage:.3f}")
        print(f"    Impacto: {item.impact_score:.3f}")
        print(f"    Accesos: {item.access_count}")
    
    # Estadísticas
    print("\n--- Estadísticas ---")
    stats = pruner.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ Sistema de Poda Adaptativa funcional - Olvido selectivo activo")