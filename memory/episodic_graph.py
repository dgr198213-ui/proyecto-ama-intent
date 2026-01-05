# learning/stability.py - Control de Estabilidad del Aprendizaje
"""
Implementa control de estabilidad mediante eigenvalues:
Si max|λ(J)| > λ_max → η↓, clip grad, rollback

Previene colapso catastrófico del aprendizaje.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import copy

@dataclass
class StabilityConfig:
    """Configuración de control de estabilidad"""
    max_spectral_radius: float = 1.0    # λ_max
    grad_clip_norm: float = 1.0         # Clip de gradientes
    lr_decay_factor: float = 0.5        # Factor de decay de η
    lr_min: float = 1e-5                # Learning rate mínimo
    check_interval: int = 10            # Cada cuántos steps verificar
    enable_rollback: bool = True        # Permitir rollback

@dataclass
class StabilityMetrics:
    """Métricas de estabilidad"""
    spectral_radius: float
    max_eigenvalue: float
    condition_number: float
    grad_norm: float
    is_stable: bool
    action_taken: str  # 'none', 'clip', 'decay_lr', 'rollback'

class StabilityController:
    """
    Controlador de Estabilidad para Aprendizaje.
    
    Monitorea:
    1. Radio espectral de matrices recurrentes
    2. Norma de gradientes
    3. Número de condición
    
    Interviene:
    1. Clipping de gradientes
    2. Reducción de learning rate
    3. Rollback a checkpoint estable
    """
    
    def __init__(self, config: Optional[StabilityConfig] = None):
        """
        Args:
            config: configuración de estabilidad
        """
        self.config = config or StabilityConfig()
        
        # Historial de checkpoints
        self.checkpoints = []
        self.max_checkpoints = 10
        
        # Estadísticas
        self.total_checks = 0
        self.instabilities_detected = 0
        self.rollbacks_performed = 0
        self.lr_decays_performed = 0
        
        # Historial de métricas
        self.metrics_history = []
    
    def check_stability(self,
                       jacobian: Optional[np.ndarray] = None,
                       recurrent_matrix: Optional[np.ndarray] = None,
                       gradients: Optional[Dict[str, np.ndarray]] = None) -> StabilityMetrics:
        """
        Verifica estabilidad del sistema.
        
        Args:
            jacobian: matriz jacobiana del sistema
            recurrent_matrix: matriz recurrente (W_rec)
            gradients: gradientes actuales
        
        Returns:
            StabilityMetrics: métricas de estabilidad
        """
        self.total_checks += 1
        
        # Determinar qué matriz analizar
        if jacobian is not None:
            matrix = jacobian
        elif recurrent_matrix is not None:
            matrix = recurrent_matrix
        else:
            # Sin matriz, solo verificar gradientes
            return self._check_gradients_only(gradients)
        
        # ==========================================
        # 1. ANÁLISIS DE EIGENVALUES
        # ==========================================
        eigenvalues = np.linalg.eigvals(matrix)
        
        # Radio espectral: max|λ|
        spectral_radius = np.max(np.abs(eigenvalues))
        
        # Eigenvalue con mayor magnitud
        max_eig_idx = np.argmax(np.abs(eigenvalues))
        max_eigenvalue = eigenvalues[max_eig_idx]
        
        # ==========================================
        # 2. NÚMERO DE CONDICIÓN
        # ==========================================
        try:
            condition_number = np.linalg.cond(matrix)
        except:
            condition_number = np.inf
        
        # ==========================================
        # 3. NORMA DE GRADIENTES
        # ==========================================
        grad_norm = 0.0
        if gradients:
            grad_norm = self._compute_grad_norm(gradients)
        
        # ==========================================
        # 4. DETERMINAR ESTABILIDAD
        # ==========================================
        is_stable = True
        action_taken = 'none'
        
        # Verificar radio espectral
        if spectral_radius > self.config.max_spectral_radius:
            is_stable = False
            self.instabilities_detected += 1
            action_taken = 'unstable_detected'
        
        # Verificar número de condición (matriz mal condicionada)
        if condition_number > 1e10:
            is_stable = False
            action_taken = 'ill_conditioned'
        
        # Verificar gradientes explosivos
        if grad_norm > 100.0:
            is_stable = False
            action_taken = 'exploding_gradients'
        
        # Crear métricas
        metrics = StabilityMetrics(
            spectral_radius=float(spectral_radius),
            max_eigenvalue=complex(max_eigenvalue),
            condition_number=float(condition_number),
            grad_norm=float(grad_norm),
            is_stable=is_stable,
            action_taken=action_taken
        )
        
        # Guardar en historial
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 1000:
            self.metrics_history.pop(0)
        
        return metrics
    
    def _check_gradients_only(self, 
                              gradients: Optional[Dict[str, np.ndarray]]) -> StabilityMetrics:
        """Verifica solo gradientes cuando no hay matriz"""
        if gradients is None:
            return StabilityMetrics(
                spectral_radius=0.0,
                max_eigenvalue=0.0,
                condition_number=1.0,
                grad_norm=0.0,
                is_stable=True,
                action_taken='none'
            )
        
        grad_norm = self._compute_grad_norm(gradients)
        is_stable = grad_norm < 100.0
        
        return StabilityMetrics(
            spectral_radius=0.0,
            max_eigenvalue=0.0,
            condition_number=1.0,
            grad_norm=grad_norm,
            is_stable=is_stable,
            action_taken='none' if is_stable else 'exploding_gradients'
        )
    
    def _compute_grad_norm(self, gradients: Dict[str, np.ndarray]) -> float:
        """Calcula norma L2 total de gradientes"""
        total_norm = 0.0
        for grad in gradients.values():
            if grad is not None:
                total_norm += np.sum(grad ** 2)
        return float(np.sqrt(total_norm))
    
    def clip_gradients(self,
                      gradients: Dict[str, np.ndarray],
                      max_norm: Optional[float] = None) -> Dict[str, np.ndarray]:
        """
        Clip gradientes por norma global.
        
        Args:
            gradients: gradientes originales
            max_norm: norma máxima (None = usar config)
        
        Returns:
            gradients_clipped: gradientes clipeados
        """
        if max_norm is None:
            max_norm = self.config.grad_clip_norm
        
        # Calcular norma total
        total_norm = self._compute_grad_norm(gradients)
        
        if total_norm <= max_norm:
            return gradients
        
        # Factor de scaling
        clip_coef = max_norm / (total_norm + 1e-9)
        
        # Clip todos los gradientes
        gradients_clipped = {}
        for name, grad in gradients.items():
            if grad is not None:
                gradients_clipped[name] = grad * clip_coef
            else:
                gradients_clipped[name] = grad
        
        return gradients_clipped
    
    def save_checkpoint(self, 
                       params: Dict[str, np.ndarray],
                       step: int,
                       metrics: StabilityMetrics):
        """
        Guarda checkpoint del estado actual.
        
        Args:
            params: parámetros del modelo
            step: paso de entrenamiento
            metrics: métricas de estabilidad
        """
        checkpoint = {
            'params': copy.deepcopy(params),
            'step': step,
            'metrics': metrics,
            'spectral_radius': metrics.spectral_radius
        }
        
        self.checkpoints.append(checkpoint)
        
        # Mantener solo los N más recientes
        if len(self.checkpoints) > self.max_checkpoints:
            self.checkpoints.pop(0)
    
    def rollback_to_stable(self) -> Optional[Dict]:
        """
        Hace rollback al último checkpoint estable.
        
        Returns:
            checkpoint: checkpoint restaurado (None si no hay)
        """
        if not self.checkpoints:
            return None
        
        # Buscar último checkpoint estable
        for checkpoint in reversed(self.checkpoints):
            if checkpoint['metrics'].is_stable:
                self.rollbacks_performed += 1
                return checkpoint
        
        # Si no hay estable, retornar el más antiguo
        return self.checkpoints[0]
    
    def adjust_learning_rate(self,
                            current_lr: float,
                            metrics: StabilityMetrics) -> float:
        """
        Ajusta learning rate basándose en estabilidad.
        
        Args:
            current_lr: learning rate actual
            metrics: métricas de estabilidad
        
        Returns:
            new_lr: learning rate ajustado
        """
        if metrics.is_stable:
            return current_lr
        
        # Reducir learning rate
        new_lr = current_lr * self.config.lr_decay_factor
        new_lr = max(new_lr, self.config.lr_min)
        
        self.lr_decays_performed += 1
        
        return new_lr
    
    def intervene(self,
                 params: Dict[str, np.ndarray],
                 gradients: Dict[str, np.ndarray],
                 learning_rate: float,
                 metrics: StabilityMetrics,
                 step: int) -> Tuple[Dict, Dict, float, str]:
        """
        Interviene si detecta inestabilidad.
        
        Args:
            params: parámetros actuales
            gradients: gradientes actuales
            learning_rate: learning rate actual
            metrics: métricas de estabilidad
            step: paso actual
        
        Returns:
            params: parámetros (posiblemente con rollback)
            gradients: gradientes (posiblemente clipeados)
            learning_rate: learning rate (posiblemente ajustado)
            action: acción tomada
        """
        if metrics.is_stable:
            return params, gradients, learning_rate, 'none'
        
        # ==========================================
        # ESTRATEGIA DE INTERVENCIÓN
        # ==========================================
        
        # Nivel 1: Clip gradientes (siempre)
        gradients_clipped = self.clip_gradients(gradients)
        action = 'clip_gradients'
        
        # Nivel 2: Reducir learning rate
        if metrics.spectral_radius > self.config.max_spectral_radius * 1.5:
            learning_rate = self.adjust_learning_rate(learning_rate, metrics)
            action = 'clip_and_decay_lr'
        
        # Nivel 3: Rollback (solo si muy inestable)
        if (metrics.spectral_radius > self.config.max_spectral_radius * 2.0 
            and self.config.enable_rollback):
            
            checkpoint = self.rollback_to_stable()
            if checkpoint is not None:
                params = copy.deepcopy(checkpoint['params'])
                learning_rate = learning_rate * 0.1  # Reducir agresivamente
                action = 'rollback'
        
        return params, gradients_clipped, learning_rate, action
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas de control de estabilidad"""
        if not self.metrics_history:
            return {
                'total_checks': self.total_checks,
                'instabilities_detected': self.instabilities_detected
            }
        
        recent = self.metrics_history[-100:]
        
        return {
            'total_checks': self.total_checks,
            'instabilities_detected': self.instabilities_detected,
            'rollbacks': self.rollbacks_performed,
            'lr_decays': self.lr_decays_performed,
            'avg_spectral_radius': np.mean([m.spectral_radius for m in recent]),
            'max_spectral_radius': np.max([m.spectral_radius for m in recent]),
            'avg_grad_norm': np.mean([m.grad_norm for m in recent]),
            'stability_rate': np.mean([m.is_stable for m in recent]),
            'checkpoints_saved': len(self.checkpoints)
        }


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test de Control de Estabilidad ===\n")
    
    np.random.seed(42)
    
    # Crear controlador
    controller = StabilityController(
        config=StabilityConfig(
            max_spectral_radius=1.0,
            grad_clip_norm=1.0,
            enable_rollback=True
        )
    )
    
    print("Configuración:")
    print(f"  Max spectral radius: {controller.config.max_spectral_radius}")
    print(f"  Grad clip norm: {controller.config.grad_clip_norm}")
    
    # Simular secuencia de entrenamiento
    print("\n--- Simulación de Entrenamiento ---\n")
    
    learning_rate = 0.01
    params = {'W': np.random.randn(10, 10) * 0.1}
    
    for step in range(15):
        # Matriz recurrente (con estabilidad variable)
        if step < 5:
            # Estable
            W_rec = np.random.randn(20, 20) * 0.3
        elif step < 10:
            # Ligeramente inestable
            W_rec = np.random.randn(20, 20) * 0.8
        else:
            # Muy inestable
            W_rec = np.random.randn(20, 20) * 1.5
        
        # Gradientes simulados
        gradients = {
            'W': np.random.randn(10, 10) * (0.1 if step < 10 else 2.0)
        }
        
        # Verificar estabilidad
        metrics = controller.check_stability(
            recurrent_matrix=W_rec,
            gradients=gradients
        )
        
        # Guardar checkpoint si estable
        if metrics.is_stable and step % 2 == 0:
            controller.save_checkpoint(params, step, metrics)
        
        # Intervenir si necesario
        params, gradients, learning_rate, action = controller.intervene(
            params, gradients, learning_rate, metrics, step
        )
        
        status = "✓ STABLE" if metrics.is_stable else "✗ UNSTABLE"
        
        print(f"Step {step}: {status}")
        print(f"  ρ(W) = {metrics.spectral_radius:.3f}")
        print(f"  ‖∇‖ = {metrics.grad_norm:.3f}")
        print(f"  η = {learning_rate:.5f}")
        
        if action != 'none':
            print(f"  ⚠ Action: {action}")
        
        print()
    
    # Estadísticas finales
    print("\n--- Estadísticas Finales ---")
    stats = controller.get_statistics()
    
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ Control de Estabilidad funcional")