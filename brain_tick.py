# learning/loss.py - Función de Pérdida Compuesta
"""
Implementa la función de pérdida total del cerebro:
ℒₜ = ℒpred + ℒmem + ℒpol + ℒgov

Cada componente penaliza diferentes aspectos del rendimiento.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class LossWeights:
    """Pesos de cada componente de pérdida"""
    prediction: float = 1.0      # ℒpred
    memory: float = 0.5          # ℒmem
    policy: float = 0.8          # ℒpol
    governance: float = 0.3      # ℒgov

class CompositeLoss:
    """
    Función de Pérdida Compuesta para el cerebro.
    
    Componentes:
    1. ℒpred: Error de predicción (modelo del mundo)
    2. ℒmem: Pérdida de memoria (retrieval, consolidación)
    3. ℒpol: Pérdida de política (decisión subóptima)
    4. ℒgov: Pérdida de gobernanza (violaciones AMA-G)
    """
    
    def __init__(self, weights: Optional[LossWeights] = None):
        """
        Args:
            weights: ponderaciones de cada componente
        """
        self.weights = weights or LossWeights()
        
        # Historial
        self.loss_history = []
    
    def compute_prediction_loss(self,
                                y_predicted: np.ndarray,
                                y_actual: np.ndarray,
                                loss_type: str = 'mse') -> float:
        """
        ℒpred: Pérdida de predicción.
        
        Mide qué tan bien el modelo interno predice observaciones.
        
        Args:
            y_predicted: predicción ỹₜ
            y_actual: observación real ŷₜ
            loss_type: 'mse', 'mae', 'huber'
        
        Returns:
            loss: pérdida de predicción
        """
        # Asegurar misma dimensión
        min_len = min(len(y_predicted), len(y_actual))
        y_pred = y_predicted[:min_len]
        y_act = y_actual[:min_len]
        
        error = y_pred - y_act
        
        if loss_type == 'mse':
            # Mean Squared Error
            loss = np.mean(error ** 2)
        
        elif loss_type == 'mae':
            # Mean Absolute Error
            loss = np.mean(np.abs(error))
        
        elif loss_type == 'huber':
            # Huber loss (robusto a outliers)
            delta = 1.0
            abs_error = np.abs(error)
            quadratic = np.minimum(abs_error, delta)
            linear = abs_error - quadratic
            loss = np.mean(0.5 * quadratic**2 + delta * linear)
        
        else:
            loss = np.mean(error ** 2)
        
        return float(loss)
    
    def compute_memory_loss(self,
                           retrieval_accuracy: float,
                           consolidation_rate: float,
                           retrieval_target: float = 0.8) -> float:
        """
        ℒmem: Pérdida de memoria.
        
        Penaliza:
        - Baja precisión de recuperación
        - Baja tasa de consolidación
        
        Args:
            retrieval_accuracy: [0,1] - precisión de retrieval
            consolidation_rate: [0,1] - tasa de consolidación exitosa
            retrieval_target: objetivo de precisión
        
        Returns:
            loss: pérdida de memoria
        """
        # Componente 1: Error de retrieval
        retrieval_error = (retrieval_target - retrieval_accuracy) ** 2
        
        # Componente 2: Consolidación insuficiente
        consolidation_penalty = (1.0 - consolidation_rate) ** 2
        
        # Pérdida total de memoria
        loss = 0.6 * retrieval_error + 0.4 * consolidation_penalty
        
        return float(loss)
    
    def compute_policy_loss(self,
                           Q_selected: float,
                           Q_optimal: float,
                           reward_actual: Optional[float] = None,
                           reward_predicted: Optional[float] = None) -> float:
        """
        ℒpol: Pérdida de política.
        
        Penaliza decisiones subóptimas.
        
        Args:
            Q_selected: Q-value de acción seleccionada
            Q_optimal: Q-value de mejor acción
            reward_actual: recompensa real obtenida
            reward_predicted: recompensa predicha
        
        Returns:
            loss: pérdida de política
        """
        # Componente 1: Regret (diferencia con óptimo)
        regret = max(0, Q_optimal - Q_selected)
        
        # Componente 2: Error de predicción de recompensa (si disponible)
        reward_error = 0.0
        if reward_actual is not None and reward_predicted is not None:
            reward_error = (reward_predicted - reward_actual) ** 2
        
        # TD-error aproximado
        td_error = regret ** 2
        
        loss = td_error + 0.5 * reward_error
        
        return float(loss)
    
    def compute_governance_loss(self,
                               confidence: float,
                               n_violations: int,
                               audit_result: str,
                               min_confidence: float = 0.5) -> float:
        """
        ℒgov: Pérdida de gobernanza.
        
        Penaliza:
        - Baja confianza
        - Violaciones de restricciones
        - Fallos de auditoría
        
        Args:
            confidence: confianza de AMA-G [0,1]
            n_violations: número de violaciones
            audit_result: 'pass', 'warning', 'fail', 'revised'
            min_confidence: umbral mínimo de confianza
        
        Returns:
            loss: pérdida de gobernanza
        """
        # Componente 1: Baja confianza
        confidence_penalty = max(0, min_confidence - confidence) ** 2
        
        # Componente 2: Violaciones
        violation_penalty = n_violations * 0.1
        
        # Componente 3: Resultado de auditoría
        audit_penalties = {
            'pass': 0.0,
            'warning': 0.1,
            'revised': 0.3,
            'fail': 1.0
        }
        audit_penalty = audit_penalties.get(audit_result, 0.5)
        
        loss = confidence_penalty + violation_penalty + audit_penalty
        
        return float(loss)
    
    def compute_total_loss(self,
                          prediction_metrics: Dict,
                          memory_metrics: Dict,
                          policy_metrics: Dict,
                          governance_metrics: Dict) -> Tuple[float, Dict]:
        """
        Calcula pérdida total compuesta.
        
        ℒₜ = w₁·ℒpred + w₂·ℒmem + w₃·ℒpol + w₄·ℒgov
        
        Args:
            prediction_metrics: métricas de predicción
            memory_metrics: métricas de memoria
            policy_metrics: métricas de política
            governance_metrics: métricas de gobernanza
        
        Returns:
            total_loss: pérdida total
            components: desglose por componente
        """
        w = self.weights
        
        # 1. Pérdida de predicción
        L_pred = self.compute_prediction_loss(
            y_predicted=prediction_metrics.get('y_predicted', np.array([0.0])),
            y_actual=prediction_metrics.get('y_actual', np.array([0.0]))
        )
        
        # 2. Pérdida de memoria
        L_mem = self.compute_memory_loss(
            retrieval_accuracy=memory_metrics.get('retrieval_accuracy', 0.5),
            consolidation_rate=memory_metrics.get('consolidation_rate', 0.5)
        )
        
        # 3. Pérdida de política
        L_pol = self.compute_policy_loss(
            Q_selected=policy_metrics.get('Q_selected', 0.0),
            Q_optimal=policy_metrics.get('Q_optimal', 0.0),
            reward_actual=policy_metrics.get('reward_actual'),
            reward_predicted=policy_metrics.get('reward_predicted')
        )
        
        # 4. Pérdida de gobernanza
        L_gov = self.compute_governance_loss(
            confidence=governance_metrics.get('confidence', 0.5),
            n_violations=governance_metrics.get('n_violations', 0),
            audit_result=governance_metrics.get('audit_result', 'pass')
        )
        
        # Pérdida total ponderada
        total_loss = (
            w.prediction * L_pred +
            w.memory * L_mem +
            w.policy * L_pol +
            w.governance * L_gov
        )
        
        # Componentes
        components = {
            'L_pred': L_pred,
            'L_mem': L_mem,
            'L_pol': L_pol,
            'L_gov': L_gov,
            'L_total': total_loss,
            'weighted': {
                'pred': w.prediction * L_pred,
                'mem': w.memory * L_mem,
                'pol': w.policy * L_pol,
                'gov': w.governance * L_gov
            }
        }
        
        # Guardar en historial
        self.loss_history.append(components)
        if len(self.loss_history) > 1000:
            self.loss_history.pop(0)
        
        return total_loss, components
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas de pérdida"""
        if not self.loss_history:
            return {}
        
        recent = self.loss_history[-100:]
        
        return {
            'avg_total': np.mean([h['L_total'] for h in recent]),
            'avg_pred': np.mean([h['L_pred'] for h in recent]),
            'avg_mem': np.mean([h['L_mem'] for h in recent]),
            'avg_pol': np.mean([h['L_pol'] for h in recent]),
            'avg_gov': np.mean([h['L_gov'] for h in recent]),
            'std_total': np.std([h['L_total'] for h in recent]),
            'trend': self._compute_trend(recent)
        }
    
    def _compute_trend(self, recent_history: List[Dict]) -> str:
        """Calcula tendencia de la pérdida"""
        if len(recent_history) < 10:
            return 'insufficient_data'
        
        losses = [h['L_total'] for h in recent_history]
        first_half = np.mean(losses[:len(losses)//2])
        second_half = np.mean(losses[len(losses)//2:])
        
        change = (second_half - first_half) / (first_half + 1e-9)
        
        if change < -0.1:
            return 'improving'
        elif change > 0.1:
            return 'degrading'
        else:
            return 'stable'


class AdamOptimizer:
    """
    Optimizador Adam para actualización de parámetros.
    
    θ ← θ - η · Adam(∇ℒₜ)
    """
    
    def __init__(self,
                 learning_rate: float = 0.001,
                 beta1: float = 0.9,
                 beta2: float = 0.999,
                 epsilon: float = 1e-8):
        """
        Args:
            learning_rate: η
            beta1: momento de primer orden
            beta2: momento de segundo orden
            epsilon: estabilidad numérica
        """
        self.lr = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon
        
        # Momentos
        self.m = {}  # Primer momento (media)
        self.v = {}  # Segundo momento (varianza no centrada)
        self.t = 0   # Paso de tiempo
    
    def update(self,
              params: Dict[str, np.ndarray],
              grads: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Actualiza parámetros con Adam.
        
        Args:
            params: parámetros actuales θ
            grads: gradientes ∇ℒ
        
        Returns:
            params_new: parámetros actualizados
        """
        self.t += 1
        params_new = {}
        
        for name, param in params.items():
            if name not in grads:
                params_new[name] = param
                continue
            
            grad = grads[name]
            
            # Inicializar momentos si es necesario
            if name not in self.m:
                self.m[name] = np.zeros_like(param)
                self.v[name] = np.zeros_like(param)
            
            # Actualizar momentos
            self.m[name] = self.beta1 * self.m[name] + (1 - self.beta1) * grad
            self.v[name] = self.beta2 * self.v[name] + (1 - self.beta2) * (grad ** 2)
            
            # Corrección de bias
            m_hat = self.m[name] / (1 - self.beta1 ** self.t)
            v_hat = self.v[name] / (1 - self.beta2 ** self.t)
            
            # Actualización
            params_new[name] = param - self.lr * m_hat / (np.sqrt(v_hat) + self.epsilon)
        
        return params_new
    
    def set_learning_rate(self, new_lr: float):
        """Actualiza learning rate (controlado por PID)"""
        self.lr = new_lr


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test de Función de Pérdida Compuesta ===\n")
    
    np.random.seed(42)
    
    # Crear loss
    loss_fn = CompositeLoss(
        weights=LossWeights(
            prediction=1.0,
            memory=0.5,
            policy=0.8,
            governance=0.3
        )
    )
    
    print("Pesos de pérdida:")
    print(f"  Predicción: {loss_fn.weights.prediction}")
    print(f"  Memoria: {loss_fn.weights.memory}")
    print(f"  Política: {loss_fn.weights.policy}")
    print(f"  Gobernanza: {loss_fn.weights.governance}")
    
    # Simular secuencia de ticks
    print("\n--- Secuencia de Evaluación de Pérdida ---\n")
    
    for t in range(10):
        # Métricas simuladas
        pred_metrics = {
            'y_predicted': np.random.randn(32) * 0.5,
            'y_actual': np.random.randn(32) * 0.5
        }
        
        mem_metrics = {
            'retrieval_accuracy': 0.7 + 0.1 * np.sin(t / 3),
            'consolidation_rate': 0.8 + 0.1 * np.cos(t / 4)
        }
        
        pol_metrics = {
            'Q_selected': 0.6 + 0.2 * np.random.rand(),
            'Q_optimal': 0.8 + 0.1 * np.random.rand(),
            'reward_actual': 0.5 + 0.3 * np.random.rand(),
            'reward_predicted': 0.6 + 0.2 * np.random.rand()
        }
        
        gov_metrics = {
            'confidence': 0.7 + 0.2 * np.random.rand(),
            'n_violations': np.random.randint(0, 2),
            'audit_result': np.random.choice(['pass', 'warning', 'pass', 'pass'])
        }
        
        # Calcular pérdida
        total_loss, components = loss_fn.compute_total_loss(
            pred_metrics, mem_metrics, pol_metrics, gov_metrics
        )
        
        if t < 3 or t % 3 == 0:
            print(f"Tick {t}:")
            print(f"  ℒ_total = {total_loss:.4f}")
            print(f"  Componentes:")
            print(f"    ℒ_pred = {components['L_pred']:.4f}")
            print(f"    ℒ_mem = {components['L_mem']:.4f}")
            print(f"    ℒ_pol = {components['L_pol']:.4f}")
            print(f"    ℒ_gov = {components['L_gov']:.4f}")
            print()
    
    # Estadísticas
    print("--- Estadísticas de Pérdida ---")
    stats = loss_fn.get_statistics()
    
    for key, value in stats.items():
        if key != 'trend':
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # Test de optimizador
    print("\n--- Test de Optimizador Adam ---")
    
    optimizer = AdamOptimizer(learning_rate=0.01)
    
    # Parámetros simulados
    params = {
        'W': np.random.randn(10, 10) * 0.1
    }
    
    for step in range(5):
        # Gradientes simulados
        grads = {
            'W': np.random.randn(10, 10) * 0.01
        }
        
        params = optimizer.update(params, grads)
        
        print(f"Step {step}: param_norm = {np.linalg.norm(params['W']):.4f}")
    
    print("\n✅ Sistema de Pérdida y Optimización funcional")