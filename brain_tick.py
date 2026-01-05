# brain_tick.py - Orquestador del Ciclo Cerebral Completo
"""
Implementa el tick cerebral completo 𝓑ₜ:

𝓑ₜ: (zₜ₋₁, wₜ₋₁, Mₜ₋₁, Gₜ₋₁, Πₜ₋₁, θₜ₋₁) --[yₜ]→ (zₜ, wₜ, Mₜ, Gₜ, Πₜ, θₜ, aₜ)

Pipeline completo:
1. Kalman filter (tálamo)
2. Bayesian belief update
3. Prediction + surprise
4. Attention (LSI)
5. Cortical state update
6. Action evaluation (Q-value)
7. Decision (DMD)
8. Audit (AMA-G)
9. Execute or revise
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys
import os

# Importar módulos del cerebro
# En producción, ajustar paths según estructura del proyecto
try:
    from sensing.kalman import ThalamicFilter, create_thalamic_filter
    from cortex.attention import CorticalAttention, create_attention_mechanism
    from cortex.state import CorticalState, create_cortical_state
    from decision.q_value import QValueEstimator, ActionCandidate
    from decision.dmd import DecisionMatrixDeterministic, DecisionCriteria, create_safety_constraint
    from governance.amag_audit import AMAGAuditor, GovernanceThresholds, AuditResult
except ImportError:
    print("⚠ Módulos del cerebro no encontrados. Asegúrate de tener la estructura correcta.")
    print("  Este código asume: sensing/, cortex/, decision/, governance/")

@dataclass
class BrainConfig:
    """Configuración del cerebro"""
    dim_observation: int = 384      # Dimensión de embeddings
    dim_latent: int = 128          # Dimensión estado z
    dim_working_memory: int = 64   # Dimensión memoria trabajo
    dim_action: int = 32           # Dimensión espacio acciones
    
    # Hiperparámetros
    lambda_attention: float = 1.0
    leak_rate: float = 0.05
    gamma_reward: float = 0.95
    risk_aversion: float = 0.6

@dataclass
class BrainState:
    """Estado completo del cerebro"""
    z: np.ndarray                  # Estado cortical
    w: Optional[np.ndarray]        # Memoria de trabajo
    belief: Optional[np.ndarray]   # Creencias bayesianas
    
    # Métricas
    surprise: float
    uncertainty: float
    confidence: float

class ArtificialBrain:
    """
    Cerebro Artificial Completo con Gobernanza AMA-G.
    
    Implementa el ciclo perceptual-decisional completo:
    Sensing → Attention → State → Memory → Decision → Governance → Action
    """
    
    def __init__(self, config: Optional[BrainConfig] = None):
        """
        Args:
            config: configuración del cerebro
        """
        self.config = config or BrainConfig()
        
        print("🧠 Inicializando Cerebro Artificial...")
        
        # === CAPA 1: SENSING (Tálamo) ===
        print("  Tálamo (filtro sensorial)...")
        self.thalamus = create_thalamic_filter(
            embedding_dim=self.config.dim_observation,
            latent_dim=self.config.dim_latent
        )
        
        # === CAPA 2: ATTENTION (Corteza) ===
        print("  Atención cortical (LSI)...")
        self.attention = create_attention_mechanism(
            dim=self.config.dim_observation,
            temperature=self.config.lambda_attention
        )
        
        # === CAPA 3: STATE (Corteza) ===
        print("  Estado cortical latente...")
        self.cortex = create_cortical_state(
            dim_latent=self.config.dim_latent,
            dim_input=self.config.dim_observation,
            dim_wm=self.config.dim_working_memory,
            activation='tanh',
            leak=self.config.leak_rate
        )
        
        # === CAPA 4: DECISION (Ganglios Basales) ===
        print("  Sistema de evaluación de acciones...")
        self.q_estimator = QValueEstimator(
            dim_state=self.config.dim_latent,
            dim_action=self.config.dim_action,
            gamma=self.config.gamma_reward,
            risk_aversion=self.config.risk_aversion
        )
        
        print("  Motor de decisión (DMD)...")
        self.decision_engine = DecisionMatrixDeterministic(
            criteria=DecisionCriteria(
                Q_value=1.0,
                efficiency=0.4,
                safety=0.6,
                modularity=0.2
            )
        )
        
        # === CAPA 5: GOVERNANCE (PFC Metacognitivo) ===
        print("  Auditor AMA-G (gobernanza)...")
        self.auditor = AMAGAuditor(
            thresholds=GovernanceThresholds(
                min_confidence=0.5,
                max_surprise=3.0,
                max_risk=0.7
            )
        )
        
        # Estado interno
        self.state = BrainState(
            z=np.zeros(self.config.dim_latent),
            w=np.zeros(self.config.dim_working_memory),
            belief=None,
            surprise=0.0,
            uncertainty=0.0,
            confidence=1.0
        )
        
        # Historial
        self.tick_count = 0
        self.history = []
        
        print("✅ Cerebro inicializado correctamente\n")
    
    def tick(self, 
             observation: np.ndarray,
             action_candidates: Optional[List[Dict]] = None,
             reward_model: Optional[callable] = None) -> Dict:
        """
        Ejecuta un ciclo completo del cerebro.
        
        Args:
            observation: observación sensorial yₜ (embedding)
            action_candidates: acciones candidatas (opcional)
            reward_model: modelo de recompensa externo (opcional)
        
        Returns:
            Dict con:
                - action: acción seleccionada aₜ
                - audit_result: resultado de AMA-G
                - metrics: métricas del ciclo
        """
        self.tick_count += 1
        
        # ===========================================
        # 1. SENSING: Filtro Talámico (Kalman)
        # ===========================================
        y_filtered, kalman_metrics = self.thalamus.filter(observation)
        
        # ===========================================
        # 2. PREDICTION: Predicción del modelo
        # ===========================================
        y_predicted = self.cortex.predict_next_observation()
        
        # ===========================================
        # 3. SURPRISE: Error de predicción
        # ===========================================
        delta, surprise = self.cortex.compute_surprise(y_filtered, y_predicted)
        self.state.surprise = surprise
        
        # ===========================================
        # 4. ATTENTION: Mecanismo LSI
        # ===========================================
        alpha, attention_metrics = self.attention.compute_attention(delta)
        
        # ===========================================
        # 5. STATE UPDATE: Actualización cortical
        # ===========================================
        z_new, cortex_metrics = self.cortex.update(
            y_hat=y_filtered,
            alpha=alpha,
            w=self.state.w
        )
        self.state.z = z_new
        
        # ===========================================
        # 6. ACTION GENERATION: Evaluar candidatos
        # ===========================================
        if action_candidates is None:
            # Generar acciones default
            action_candidates = self._generate_default_actions()
        
        # Evaluar Q-values
        q_results = []
        for candidate in action_candidates:
            Q_val, components = self.q_estimator.compute_Q(
                z=self.state.z,
                a=candidate['action'],
                metadata=candidate.get('metadata', {}),
                reward_model=reward_model
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
        
        # ===========================================
        # 7. DECISION: DMD (Ganglios Basales)
        # ===========================================
        decision_result = self.decision_engine.decide(
            action_candidates=q_results,
            constraints=[create_safety_constraint(max_magnitude=3.0)]
        )
        
        # ===========================================
        # 8. GOVERNANCE: Auditoría AMA-G
        # ===========================================
        selected_candidate = next(
            c for c in q_results if c['id'] == decision_result.selected_action_id
        )
        
        audit_report = self.auditor.audit(
            z=self.state.z,
            w=self.state.w,
            R=None,  # Memoria episódica (FASE 2)
            action_candidate=selected_candidate,
            surprise=surprise,
            kl_divergence=None  # Bayesian update (simplificado)
        )
        
        self.state.confidence = audit_report.confidence
        
        # ===========================================
        # 9. EXECUTION: Ejecutar o revisar
        # ===========================================
        final_action = None
        execution_mode = "normal"
        
        if audit_report.result == AuditResult.PASS:
            final_action = decision_result.selected_action
            execution_mode = "approved"
            
        elif audit_report.result == AuditResult.WARNING:
            final_action = decision_result.selected_action
            execution_mode = "approved_with_warning"
            
        elif audit_report.result == AuditResult.REVISED:
            final_action = audit_report.revised_action
            execution_mode = "revised"
            
        elif audit_report.result == AuditResult.FAIL:
            final_action = audit_report.safe_action
            execution_mode = "safe_mode"
        
        # ===========================================
        # 10. METRICS: Recopilar métricas del ciclo
        # ===========================================
        cycle_metrics = {
            'tick': self.tick_count,
            'execution_mode': execution_mode,
            
            # Sensing
            'kalman_uncertainty': kalman_metrics['uncertainty'],
            'kalman_innovation': kalman_metrics['innovation_norm'],
            
            # Attention
            'attention_entropy': attention_metrics['attention_entropy'],
            'attention_focus': attention_metrics['focus_index'],
            
            # State
            'state_norm': cortex_metrics['z_norm'],
            'state_change': cortex_metrics['z_change'],
            'sparsity': cortex_metrics['sparsity'],
            
            # Prediction
            'surprise': surprise,
            
            # Decision
            'decision_score': decision_result.score,
            'q_value': selected_candidate['Q_value'],
            
            # Governance
            'audit_result': audit_report.result.value,
            'confidence': audit_report.confidence,
            'n_issues': len(audit_report.issues),
            
            # Action
            'action_magnitude': np.linalg.norm(final_action)
        }
        
        # Guardar en historial
        self.history.append(cycle_metrics)
        if len(self.history) > 1000:
            self.history.pop(0)
        
        # ===========================================
        # RETURN: Resultado del tick
        # ===========================================
        return {
            'action': final_action,
            'action_id': decision_result.selected_action_id,
            'execution_mode': execution_mode,
            'audit_report': audit_report,
            'decision_result': decision_result,
            'metrics': cycle_metrics,
            'state': {
                'z': self.state.z.copy(),
                'w': self.state.w.copy() if self.state.w is not None else None,
                'surprise': self.state.surprise,
                'confidence': self.state.confidence
            }
        }
    
    def _generate_default_actions(self) -> List[Dict]:
        """Genera acciones candidatas por defecto"""
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
    
    def reset(self):
        """Resetea el cerebro a estado inicial"""
        self.cortex.reset()
        self.state = BrainState(
            z=np.zeros(self.config.dim_latent),
            w=np.zeros(self.config.dim_working_memory),
            belief=None,
            surprise=0.0,
            uncertainty=0.0,
            confidence=1.0
        )
        self.tick_count = 0
        print("🔄 Cerebro reseteado")
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas del cerebro"""
        if not self.history:
            return {}
        
        recent = self.history[-100:]
        
        return {
            'total_ticks': self.tick_count,
            'avg_confidence': np.mean([h['confidence'] for h in recent]),
            'avg_surprise': np.mean([h['surprise'] for h in recent]),
            'execution_modes': {
                'approved': sum(1 for h in recent if h['execution_mode'] == 'approved'),
                'revised': sum(1 for h in recent if h['execution_mode'] == 'revised'),
                'safe_mode': sum(1 for h in recent if h['execution_mode'] == 'safe_mode')
            },
            'auditor_stats': self.auditor.get_statistics()
        }


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("="*60)
    print("🧠 TEST COMPLETO DEL CEREBRO ARTIFICIAL")
    print("="*60 + "\n")
    
    np.random.seed(42)
    
    # Crear cerebro
    brain = ArtificialBrain(
        config=BrainConfig(
            dim_observation=64,
            dim_latent=32,
            dim_working_memory=16,
            dim_action=16
        )
    )
    
    # Simular ciclos
    print("--- Ejecutando 5 ciclos cerebrales ---\n")
    
    for t in range(5):
        # Observación simulada (embedding)
        observation = np.random.randn(64) * 0.5
        
        # Tick cerebral
        result = brain.tick(observation)
        
        print(f"⏱ Tick {t+1}:")
        print(f"  Modo: {result['execution_mode']}")
        print(f"  Acción: {result['action_id']}")
        print(f"  Confianza: {result['metrics']['confidence']:.3f}")
        print(f"  Sorpresa: {result['metrics']['surprise']:.3f}")
        print(f"  Q-value: {result['metrics']['q_value']:.3f}")
        
        if result['audit_report'].issues:
            print(f"  ⚠ Issues: {len(result['audit_report'].issues)}")
        
        print()
    
    # Estadísticas
    print("\n--- Estadísticas del Cerebro ---")
    stats = brain.get_statistics()
    
    print(f"Total de ciclos: {stats['total_ticks']}")
    print(f"Confianza promedio: {stats['avg_confidence']:.3f}")
    print(f"Sorpresa promedio: {stats['avg_surprise']:.3f}")
    print(f"\nModos de ejecución:")
    for mode, count in stats['execution_modes'].items():
        print(f"  {mode}: {count}")
    
    print("\n" + "="*60)
    print("✅ FASE 1 MVP COMPLETA - Cerebro funcional con gobernanza")
    print("="*60)