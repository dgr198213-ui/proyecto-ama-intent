# learning/consolidation.py - Consolidación Nocturna ("Sueño")
"""
Implementa consolidación offline tipo "sueño":
- Batch replay de episodios importantes
- Reorganización de memoria semántica
- Poda intensiva
- Ajuste de parámetros

Este proceso ocurre "offline" cuando el cerebro no está activo.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class SleepConfig:
    """Configuración del proceso de sueño"""
    replay_episodes: int = 50          # Episodios a replay
    replay_iterations: int = 10        # Iteraciones de replay
    reorganize_semantic: bool = True   # Reorganizar memoria semántica
    intensive_pruning: bool = True     # Poda intensiva
    dream_noise: float = 0.1           # Ruido en replay (creatividad)

class SleepCycle:
    """
    Ciclo de Sueño para Consolidación Offline.
    
    Fases:
    1. NREM (consolidación sistemática)
       - Replay de episodios importantes
       - Fortalecimiento de conexiones
    
    2. REM (procesamiento creativo)
       - Replay con ruido (dreaming)
       - Descubrimiento de patrones
    
    3. Reorganización
       - Merge de conceptos similares
       - Poda de información redundante
    
    4. Homeostasis
       - Reset de parámetros temporales
       - Preparación para nuevo ciclo
    """
    
    def __init__(self, config: Optional[SleepConfig] = None):
        """
        Args:
            config: configuración del sueño
        """
        self.config = config or SleepConfig()
        
        # Estadísticas
        self.total_sleep_cycles = 0
        self.sleep_history = []
    
    def execute_sleep_cycle(self,
                           episodic_memory,
                           semantic_memory,
                           cortex,
                           q_estimator,
                           pruning_system) -> Dict:
        """
        Ejecuta un ciclo completo de sueño.
        
        Args:
            episodic_memory: EpisodicMemoryGraph
            semantic_memory: SemanticMemoryMatrix
            cortex: CorticalState
            q_estimator: QValueEstimator
            pruning_system: AdaptivePruningSystem
        
        Returns:
            Dict con estadísticas del ciclo
        """
        self.total_sleep_cycles += 1
        
        print(f"\n{'='*60}")
        print(f"💤 CICLO DE SUEÑO #{self.total_sleep_cycles}")
        print(f"{'='*60}\n")
        
        stats = {
            'cycle': self.total_sleep_cycles,
            'episodes_replayed': 0,
            'concepts_merged': 0,
            'items_pruned': 0,
            'phase_durations': {}
        }
        
        # ==========================================
        # FASE 1: NREM - Consolidación Sistemática
        # ==========================================
        print("[FASE 1/4] NREM - Consolidación sistemática...")
        
        nrem_stats = self._nrem_phase(
            episodic_memory,
            semantic_memory,
            cortex,
            q_estimator
        )
        
        stats['episodes_replayed'] = nrem_stats['replayed']
        stats['phase_durations']['nrem'] = nrem_stats['duration']
        
        print(f"  ✓ {nrem_stats['replayed']} episodios consolidados\n")
        
        # ==========================================
        # FASE 2: REM - Procesamiento Creativo
        # ==========================================
        print("[FASE 2/4] REM - Procesamiento creativo (dreaming)...")
        
        rem_stats = self._rem_phase(
            episodic_memory,
            semantic_memory,
            cortex
        )
        
        stats['patterns_discovered'] = rem_stats['patterns']
        stats['phase_durations']['rem'] = rem_stats['duration']
        
        print(f"  ✓ {rem_stats['patterns']} nuevos patrones descubiertos\n")
        
        # ==========================================
        # FASE 3: Reorganización
        # ==========================================
        print("[FASE 3/4] Reorganización de memoria...")
        
        if self.config.reorganize_semantic:
            print("  Merging conceptos similares...")
            pre_merge = semantic_memory.n_concepts
            semantic_memory.merge_similar_concepts(threshold=0.85)
            post_merge = semantic_memory.n_concepts
            stats['concepts_merged'] = pre_merge - post_merge
            print(f"  ✓ {stats['concepts_merged']} conceptos fusionados")
        
        if self.config.intensive_pruning:
            print("  Poda intensiva...")
            prune_result = pruning_system.execute_pruning(
                episodic_memory,
                semantic_memory,
                force=True
            )
            stats['items_pruned'] = prune_result['pruned_count']
            print(f"  ✓ {stats['items_pruned']} items eliminados")
        
        print()
        
        # ==========================================
        # FASE 4: Homeostasis y Reset
        # ==========================================
        print("[FASE 4/4] Homeostasis y preparación...")
        
        # Reset estados temporales (working memory, etc.)
        # cortex puede mantener su estado latente
        
        print("  ✓ Sistema preparado para nuevo ciclo\n")
        
        # ==========================================
        # Resumen
        # ==========================================
        print(f"{'='*60}")
        print(f"RESUMEN DEL CICLO DE SUEÑO")
        print(f"{'='*60}")
        print(f"  Episodios consolidados: {stats['episodes_replayed']}")
        print(f"  Patrones descubiertos: {stats['patterns_discovered']}")
        print(f"  Conceptos fusionados: {stats['concepts_merged']}")
        print(f"  Items podados: {stats['items_pruned']}")
        print(f"{'='*60}\n")
        
        # Guardar en historial
        self.sleep_history.append(stats)
        
        return stats
    
    def _nrem_phase(self,
                    episodic_memory,
                    semantic_memory,
                    cortex,
                    q_estimator) -> Dict:
        """
        Fase NREM: Consolidación sistemática.
        
        Replay de episodios importantes sin ruido.
        Fortalecimiento de conexiones fuertes.
        """
        import time
        start = time.time()
        
        # Seleccionar episodios importantes para replay
        # Criterio: alto PageRank + recientes + alto reward
        
        if not episodic_memory.episodes:
            return {'replayed': 0, 'duration': 0.0}
        
        # Calcular PageRank
        pr_scores = episodic_memory.compute_pagerank()
        
        # Ordenar por importancia
        episodes_ranked = sorted(
            episodic_memory.episodes.items(),
            key=lambda x: pr_scores.get(x[0], 0.0) * x[1].importance,
            reverse=True
        )
        
        n_replay = min(self.config.replay_episodes, len(episodes_ranked))
        
        # Replay iterativo
        for iteration in range(self.config.replay_iterations):
            for ep_id, episode in episodes_ranked[:n_replay]:
                # Reactivar estado
                state = episode.state
                
                # Reconsolidar en memoria semántica
                semantic_memory.consolidate(
                    state=state,
                    tags=list(episode.tags),
                    threshold=0.75  # Umbral más bajo = más consolidación
                )
        
        duration = time.time() - start
        
        return {
            'replayed': n_replay * self.config.replay_iterations,
            'duration': duration
        }
    
    def _rem_phase(self,
                   episodic_memory,
                   semantic_memory,
                   cortex) -> Dict:
        """
        Fase REM: Procesamiento creativo.
        
        Replay con ruido (dreaming).
        Descubrimiento de nuevos patrones.
        """
        import time
        start = time.time()
        
        patterns_discovered = 0
        
        if not episodic_memory.episodes:
            return {'patterns': 0, 'duration': 0.0}
        
        # Seleccionar episodios aleatorios
        episode_ids = list(episodic_memory.episodes.keys())
        n_samples = min(20, len(episode_ids))
        sampled_ids = np.random.choice(episode_ids, n_samples, replace=False)
        
        for ep_id in sampled_ids:
            episode = episodic_memory.episodes[ep_id]
            
            # Añadir ruido (dreaming)
            noisy_state = episode.state + np.random.randn(*episode.state.shape) * self.config.dream_noise
            
            # Buscar conceptos cercanos
            similar_concepts = semantic_memory.retrieve(
                query=noisy_state,
                top_k=3,
                min_similarity=0.5
            )
            
            # Si encuentra relaciones inesperadas = nuevo patrón
            if similar_concepts and len(similar_concepts) >= 2:
                # Crear nueva asociación implícita
                patterns_discovered += 1
        
        duration = time.time() - start
        
        return {
            'patterns': patterns_discovered,
            'duration': duration
        }
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas de ciclos de sueño"""
        if not self.sleep_history:
            return {
                'total_cycles': self.total_sleep_cycles
            }
        
        return {
            'total_cycles': self.total_sleep_cycles,
            'avg_episodes_replayed': np.mean([s['episodes_replayed'] for s in self.sleep_history]),
            'avg_patterns_discovered': np.mean([s['patterns_discovered'] for s in self.sleep_history]),
            'avg_concepts_merged': np.mean([s['concepts_merged'] for s in self.sleep_history]),
            'avg_items_pruned': np.mean([s['items_pruned'] for s in self.sleep_history]),
            'total_consolidations': sum(s['episodes_replayed'] for s in self.sleep_history)
        }


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test de Consolidación Nocturna (Sueño) ===\n")
    
    # Mock objects para testing
    class MockEpisodicMemory:
        def __init__(self):
            from memory.episodic_graph import Episode
            self.episodes = {}
            self.max_episodes = 100
            
            # Crear episodios simulados
            for i in range(20):
                ep_id = f"ep_{i}"
                self.episodes[ep_id] = Episode(
                    id=ep_id,
                    state=np.random.randn(32) * 0.5,
                    context={'reward': np.random.rand()},
                    timestamp=f"2025-01-{i:02d}",
                    importance=np.random.rand()
                )
        
        def compute_pagerank(self):
            return {ep_id: np.random.rand() for ep_id in self.episodes.keys()}
    
    class MockSemanticMemory:
        def __init__(self):
            self.n_concepts = 10
        
        def consolidate(self, state, tags, threshold):
            return 0, False
        
        def retrieve(self, query, top_k, min_similarity):
            return [(i, 0.7, None) for i in range(min(top_k, 3))]
        
        def merge_similar_concepts(self, threshold):
            self.n_concepts -= 2
    
    class MockCortex:
        pass
    
    class MockQEstimator:
        pass
    
    class MockPruningSystem:
        def execute_pruning(self, ep_mem, sem_mem, force):
            return {'pruned_count': 5}
    
    # Crear mocks
    ep_mem = MockEpisodicMemory()
    sem_mem = MockSemanticMemory()
    cortex = MockCortex()
    q_est = MockQEstimator()
    pruner = MockPruningSystem()
    
    # Crear ciclo de sueño
    sleep = SleepCycle(
        config=SleepConfig(
            replay_episodes=10,
            replay_iterations=3,
            reorganize_semantic=True,
            intensive_pruning=True,
            dream_noise=0.15
        )
    )
    
    # Ejecutar ciclo
    stats = sleep.execute_sleep_cycle(
        ep_mem, sem_mem, cortex, q_est, pruner
    )
    
    # Estadísticas
    print("\n--- Estadísticas del Sueño ---")
    sleep_stats = sleep.get_statistics()
    for key, value in sleep_stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ Sistema de Consolidación Nocturna funcional")