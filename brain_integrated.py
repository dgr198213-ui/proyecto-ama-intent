# brain_integrated.py - Cerebro Completo con Sistema de Memoria (FASE 1 + FASE 2)
"""
Integración completa del cerebro artificial:
FASE 1: Sensing + Attention + State + Decision + Governance
FASE 2: Memoria Episódica + Semántica + Working + Poda

Este es el cerebro funcional completo con arquitectura biomimética.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Importar todos los módulos del cerebro
print("🧠 Cargando módulos del cerebro...")

# FASE 1
from sensing.kalman import ThalamicFilter, create_thalamic_filter
from cortex.attention import CorticalAttention, create_attention_mechanism
from cortex.state import CorticalState, create_cortical_state
from decision.q_value import QValueEstimator, ActionCandidate
from decision.dmd import DecisionMatrixDeterministic, DecisionCriteria, create_safety_constraint
from governance.amag_audit import AMAGAuditor, GovernanceThresholds, AuditResult

# FASE 2
from memory.episodic_graph import EpisodicMemoryGraph
from memory.semantic_matrix import SemanticMemoryMatrix
from memory.working_memory import WorkingMemory, WorkingMemoryConfig
from memory.pruning import AdaptivePruningSystem, PruningConfig, PruningStrategy

print("✅ Módulos cargados\n")

@dataclass
class IntegratedBrainConfig:
    """Configuración completa del cerebro integrado"""
    # Dimensiones
    dim_observation: int = 384
    dim_latent: int = 128
    dim_working_memory: int = 64
    dim_action: int = 32
    
    # Capacidades de memoria
    max_episodes: int = 5000
    max_concepts: int = 500
    
    # Hiperparámetros
    lambda_attention: float = 1.0
    leak_rate: float = 0.05
    gamma_reward: float = 0.95
    risk_aversion: float = 0.6
    
    # Memoria
    wm_capacity: int = 7
    semantic_learning_rate: float = 0.05
    prune_interval: int = 100

class IntegratedArtificialBrain:
    """
    Cerebro Artificial Completo con Memoria Integrada.
    
    Pipeline completo:
    1. Sensing (Tálamo) → Filtrado Kalman
    2. Attention (LSI) → Foco atencional
    3. State Update (Corteza) → Representación latente
    4. Memory Retrieval:
       - Episódica (Hipocampo) → Experiencias pasadas
       - Semántica (Neocorteza) → Conocimiento abstracto
       - Working (PFC) → Buffer activo
    5. Decision (Ganglios Basales) → Q-value + DMD
    6. Governance (PFC Meta) → AMA-G audit
    7. Learning & Consolidation:
       - Actualizar memoria semántica
       - Almacenar nuevo episodio
       - Poda adaptativa
    8. Action → Ejecutar o revisar
    """
    
    def __init__(self, config: Optional[IntegratedBrainConfig] = None):
        """
        Args:
            config: configuración del cerebro
        """
        self.config = config or IntegratedBrainConfig()
        
        print("="*60)
        print("🧠 INICIALIZANDO CEREBRO ARTIFICIAL INTEGRADO")
        print("="*60)
        
        # ============================================
        # CAPA 1: SENSING
        # ============================================
        print("\n[1/9] Tálamo (filtro sensorial)...")
        self.thalamus = create_thalamic_filter(
            embedding_dim=self.config.dim_observation,
            latent_dim=self.config.dim_latent
        )
        
        # ============================================
        # CAPA 2: ATTENTION
        # ============================================
        print("[2/9] Atención cortical (LSI)...")
        self.attention = create_attention_mechanism(
            dim=self.config.dim_observation,
            temperature=self.config.lambda_attention
        )
        
        # ============================================
        # CAPA 3: STATE
        # ============================================
        print("[3/9] Estado cortical latente...")
        self.cortex = create_cortical_state(
            dim_latent=self.config.dim_latent,
            dim_input=self.config.dim_observation,
            dim_wm=self.config.dim_working_memory,
            activation='tanh',
            leak=self.config.leak_rate
        )
        
        # ============================================
        # CAPA 4: MEMORIA EPISÓDICA (Hipocampo)
        # ============================================
        print("[4/9] Memoria episódica (hipocampo)...")
        self.episodic_memory = EpisodicMemoryGraph(
            max_episodes=self.config.max_episodes,
            similarity_threshold=0.7
        )
        
        # ============================================
        # CAPA 5: MEMORIA SEMÁNTICA (Neocorteza)
        # ============================================
        print("[5/9] Memoria semántica (neocorteza)...")
        self.semantic_memory = SemanticMemoryMatrix(
            dim_state=self.config.dim_latent,
            max_concepts=self.config.max_concepts,
            learning_rate=self.config.semantic_learning_rate,
            compression_dim=self.config.dim_latent // 2
        )
        
        # ============================================
        # CAPA 6: WORKING MEMORY (PFC)
        # ============================================
        print("[6/9] Memoria de trabajo (PFC)...")
        self.working_memory = WorkingMemory(
            dim=self.config.dim_working_memory,
            config=WorkingMemoryConfig(capacity=self.config.wm_capacity)
        )
        
        # ============================================
        # CAPA 7: DECISION
        # ============================================
        print("[7/9] Sistema de decisión...")
        self.q_estimator = QValueEstimator(
            dim_state=self.config.dim_latent,
            dim_action=self.config.dim_action,
            gamma=self.config.gamma_reward,
            risk_aversion=self.config.risk_aversion
        )
        
        self.decision_engine = DecisionMatrixDeterministic(
            criteria=DecisionCriteria(
                Q_value=1.0,
                efficiency=0.4,
                safety=0.6,
                modularity=0.2
            )
        )
        
        # ============================================
        # CAPA 8: GOVERNANCE (AMA-G)
        # ============================================
        print("[8/9] Auditor AMA-G (metacognición)...")
        self.auditor = AMAGAuditor(
            thresholds=GovernanceThresholds(
                min_confidence=0.5,
                max_surprise=3.0,
                max_risk=0.7
            )
        )
        
        # ============================================
        # CAPA 9: PODA ADAPTATIVA
        # ============================================
        print("[9/9] Sistema de poda adaptativa...")
        self.pruning_system = AdaptivePruningSystem(
            config=PruningConfig(
                strategy=PruningStrategy.COMPOSITE,
                check_interval=self.config.prune_interval
            )
        )
        
        # ============================================
        # ESTADO GLOBAL
        # ============================================
        self.tick_count = 0
        self.global_history = []
        
        print("\n" + "="*60)
        print("✅ CEREBRO INICIALIZADO CORRECTAMENTE")
        print("="*60 + "\n")
    
    def tick(self,
             observation: np.ndarray,
             action_candidates: Optional[List[Dict]] = None,
             reward: Optional[float] = None,
             context: Optional[Dict] = None) -> Dict:
        """
        Ciclo completo del cerebro integrado.
        
        Args:
            observation: observación sensorial yₜ
            action_candidates: candidatos de acción (opcional)
            reward: recompensa del tick anterior (opcional)
            context: contexto adicional
        
        Returns:
            Dict con resultado completo del tick
        """
        self.tick_count += 1
        self.pruning_system.tick()
        
        # ==========================================
        # 1. SENSING: Filtro Talámico
        # ==========================================
        y_filtered, kalman_metrics = self.thalamus.filter(observation)
        
        # ==========================================
        # 2. PREDICTION: Modelo del mundo
        # ==========================================
        y_predicted = self.cortex.predict_next_observation()
        
        # ==========================================
        # 3. SURPRISE: Error de predicción
        # ==========================================
        delta, surprise = self.cortex.compute_surprise(y_filtered, y_predicted)
        
        # ==========================================
        # 4. ATTENTION: Mecanismo LSI
        # ==========================================
        alpha, attention_metrics = self.attention.compute_attention(delta)
        
        # ==========================================
        # 5. MEMORY RETRIEVAL
        # ==========================================
        
        # 5a. Recuperar episodios relevantes
        episodic_results = self.episodic_memory.retrieve(
            query_state=self.cortex.get_state(),
            top_k=5,
            use_pagerank=True
        )
        
        # 5b. Recuperar conceptos semánticos
        semantic_results = self.semantic_memory.retrieve(
            query=self.cortex.get_state(),
            top_k=3,
            min_similarity=0.6
        )
        
        # 5c. Actualizar Working Memory
        wm_new, wm_metrics = self.working_memory.update(
            z=self.cortex.get_state(),
            retrieved_episodes=episodic_results
        )
        
        # ==========================================
        # 6. STATE UPDATE: Actualización cortical
        # ==========================================
        z_new, cortex_metrics = self.cortex.update(
            y_hat=y_filtered,
            alpha=alpha,
            w=wm_new
        )
        
        # ==========================================
        # 7. ACTION GENERATION & EVALUATION
        # ==========================================
        if action_candidates is None:
            action_candidates = self._generate_default_actions()
        
        q_results = []
        for candidate in action_candidates:
            Q_val, components = self.q_estimator.compute_Q(
                z=z_new,
                a=candidate['action'],
                metadata=candidate.get('metadata', {})
            )
            
            candidate_eval = {
                'id': candidate['id'],
                'action': candidate['action'],
                'Q_value': Q_val,
                'miem': {
                    'efficiency': components['miem_efficiency'],
                    'risk': components['miem_risk'],
                    'modularity': components['miem_modularity']
                }
            }
            q_results.append(candidate_eval)
        
        # ==========================================
        # 8. DECISION: DMD
        # ==========================================
        decision_result = self.decision_engine.decide(
            action_candidates=q_results,
            constraints=[create_safety_constraint(max_magnitude=3.0)]
        )
        
        # ==========================================
        # 9. GOVERNANCE: Auditoría AMA-G
        # ==========================================
        selected_candidate = next(
            c for c in q_results if c['id'] == decision_result.selected_action_id
        )
        
        audit_report = self.auditor.audit(
            z=z_new,
            w=wm_new,
            R=episodic_results,
            action_candidate=selected_candidate,
            surprise=surprise
        )
        
        # ==========================================
        # 10. EXECUTION DECISION
        # ==========================================
        final_action, execution_mode = self._resolve_execution(
            decision_result, audit_report
        )
        
        # ==========================================
        # 11. LEARNING & CONSOLIDATION
        # ==========================================
        
        # 11a. Consolidar en memoria semántica
        concept_id, is_new_concept = self.semantic_memory.consolidate(
            state=z_new,
            tags=context.get('tags') if context else None
        )
        
        # 11b. Almacenar episodio
        episode_context = {
            'action': decision_result.selected_action_id,
            'reward': reward if reward is not None else 0.0,
            'surprise': surprise,
            'confidence': audit_report.confidence
        }
        if context:
            episode_context.update(context)
        
        episode_id = self.episodic_memory.add_episode(
            state=z_new,
            context=episode_context,
            importance=audit_report.confidence
        )
        
        # 11c. Poda adaptativa (si es necesario)
        prune_stats = None
        if self.pruning_system.should_prune(
            len(self.episodic_memory.episodes),
            self.episodic_memory.max_episodes
        ):
            prune_stats = self.pruning_system.execute_pruning(
                self.episodic_memory,
                self.semantic_memory
            )
        
        # ==========================================
        # 12. METRICS & RETURN
        # ==========================================
        cycle_metrics = {
            'tick': self.tick_count,
            'execution_mode': execution_mode,
            
            # Sensing
            'surprise': surprise,
            'kalman_uncertainty': kalman_metrics['uncertainty'],
            
            # Attention
            'attention_focus': attention_metrics['focus_index'],
            
            # State
            'state_norm': cortex_metrics['z_norm'],
            
            # Memory
            'episodic_retrieved': len(episodic_results),
            'semantic_retrieved': len(semantic_results),
            'wm_active_slots': wm_metrics['active_slots'],
            'new_concept': is_new_concept,
            
            # Decision
            'q_value': selected_candidate['Q_value'],
            'decision_score': decision_result.score,
            
            # Governance
            'confidence': audit_report.confidence,
            'audit_result': audit_report.result.value,
            
            # Consolidation
            'episode_stored': episode_id,
            'concept_id': concept_id,
            'pruned': prune_stats['pruned_count'] if prune_stats else 0
        }
        
        # Guardar en historial
        self.global_history.append(cycle_metrics)
        if len(self.global_history) > 1000:
            self.global_history.pop(0)
        
        return {
            'action': final_action,
            'action_id': decision_result.selected_action_id,
            'execution_mode': execution_mode,
            'audit_report': audit_report,
            'metrics': cycle_metrics,
            'memory_state': {
                'episodic_count': len(self.episodic_memory.episodes),
                'semantic_count': self.semantic_memory.n_concepts,
                'wm_norm': np.linalg.norm(wm_new)
            }
        }
    
    def _generate_default_actions(self) -> List[Dict]:
        """Genera acciones por defecto"""
        return [
            {
                'id': 'conservative',
                'action': np.random.randn(self.config.dim_action) * 0.3,
                'metadata': {'complexity': 0.2}
            },
            {
                'id': 'moderate',
                'action': np.random.randn(self.config.dim_action) * 0.8,
                'metadata': {'complexity': 0.5}
            },
            {
                'id': 'exploratory',
                'action': np.random.randn(self.config.dim_action) * 1.5,
                'metadata': {'complexity': 0.8}
            }
        ]
    
    def _resolve_execution(self, decision_result, audit_report):
        """Resuelve qué acción ejecutar basándose en auditoría"""
        if audit_report.result == AuditResult.PASS:
            return decision_result.selected_action, "approved"
        elif audit_report.result == AuditResult.WARNING:
            return decision_result.selected_action, "approved_with_warning"
        elif audit_report.result == AuditResult.REVISED:
            return audit_report.revised_action, "revised"
        else:  # FAIL
            return audit_report.safe_action, "safe_mode"
    
    def get_complete_statistics(self) -> Dict:
        """Retorna estadísticas completas del cerebro"""
        return {
            'total_ticks': self.tick_count,
            'episodic_memory': self.episodic_memory.get_statistics(),
            'semantic_memory': self.semantic_memory.get_statistics(),
            'working_memory': self.working_memory.get_statistics(),
            'pruning_system': self.pruning_system.get_statistics(),
            'auditor': self.auditor.get_statistics()
        }


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧠 TEST COMPLETO DEL CEREBRO INTEGRADO (FASE 1 + FASE 2)")
    print("="*60 + "\n")
    
    np.random.seed(42)
    
    # Crear cerebro integrado
    brain = IntegratedArtificialBrain(
        config=IntegratedBrainConfig(
            dim_observation=64,
            dim_latent=32,
            dim_working_memory=16,
            dim_action=16,
            max_episodes=100,
            max_concepts=50
        )
    )
    
    # Ejecutar ciclos
    print("\n--- Ejecutando 10 Ciclos Cerebrales ---\n")
    
    for t in range(10):
        observation = np.random.randn(64) * 0.5
        reward = np.random.rand()
        context = {'tags': [f'tag_{t % 3}']}
        
        result = brain.tick(observation, reward=reward, context=context)
        
        print(f"⏱ Tick {t+1}:")
        print(f"  Modo: {result['execution_mode']}")
        print(f"  Confianza: {result['metrics']['confidence']:.3f}")
        print(f"  Sorpresa: {result['metrics']['surprise']:.3f}")
        print(f"  Memoria episódica: {result['memory_state']['episodic_count']} eps")
        print(f"  Memoria semántica: {result['memory_state']['semantic_count']} conceptos")
        print(f"  WM slots activos: {result['metrics']['wm_active_slots']}")
        
        if result['metrics']['pruned'] > 0:
            print(f"  🗑️ Podados: {result['metrics']['pruned']} items")
        
        print()
    
    # Estadísticas finales
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS FINALES DEL CEREBRO")
    print("="*60 + "\n")
    
    stats = brain.get_complete_statistics()
    
    print(f"Total de ciclos ejecutados: {stats['total_ticks']}")
    print(f"\nMemoria Episódica:")
    for key, val in stats['episodic_memory'].items():
        print(f"  {key}: {val if not isinstance(val, float) else f'{val:.2f}'}")
    
    print(f"\nMemoria Semántica:")
    for key, val in stats['semantic_memory'].items():
        print(f"  {key}: {val if not isinstance(val, float) else f'{val:.2f}'}")
    
    print(f"\nAuditor AMA-G:")
    for key, val in stats['auditor'].items():
        if isinstance(val, float):
            print(f"  {key}: {val:.2%}" if 'rate' in key else f"  {key}: {val:.3f}")
        else:
            print(f"  {key}: {val}")
    
    print("\n" + "="*60)
    print("✅ CEREBRO ARTIFICIAL COMPLETO FUNCIONAL")
    print("   FASE 1 + FASE 2 INTEGRADAS")
    print("="*60)