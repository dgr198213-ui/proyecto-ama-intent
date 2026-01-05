# cortex/state.py - Estado Cortical Latente
"""
Implementa el estado latente cortical y su dinámica de actualización.
zₜ = f(zₜ₋₁, αₜ⊙eₜ, wₜ₋₁)

Este módulo mantiene y actualiza la representación interna del "mundo" 
que el cerebro construye a partir de observaciones filtradas.
"""

import numpy as np
from typing import Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class ActivationFunction(Enum):
    """Funciones de activación disponibles"""
    TANH = "tanh"
    RELU = "relu"
    GELU = "gelu"
    SWISH = "swish"

@dataclass
class CorticalStateConfig:
    """Configuración del estado cortical"""
    dim_latent: int
    dim_input: int
    dim_working_memory: int
    activation: ActivationFunction
    leak_rate: float  # Tasa de olvido (0=sin olvido, 1=reseteo total)
    
@dataclass
class CorticalDynamics:
    """Parámetros de la dinámica cortical"""
    W_input: np.ndarray      # Pesos entrada → latente
    W_recurrent: np.ndarray  # Pesos recurrentes
    W_memory: np.ndarray     # Pesos memoria → latente
    b: np.ndarray            # Bias
    
class CorticalState:
    """
    Estado latente cortical con dinámica recurrente.
    
    El estado z representa la "comprensión" interna que el sistema
    tiene del mundo en base a observaciones pasadas y presentes.
    """
    
    def __init__(self, config: CorticalStateConfig):
        """
        Args:
            config: configuración del estado cortical
        """
        self.config = config
        
        # Estado actual
        self.z = np.zeros(config.dim_latent)
        self.z_history = []
        
        # Inicialización de parámetros (Xavier/Glorot)
        self.dynamics = self._initialize_dynamics()
        
        # Codificador de entrada (φ)
        self.encoder = self._create_encoder()
        
        # Funciones de activación
        self.activation_fn = self._get_activation_function()
        
    def _initialize_dynamics(self) -> CorticalDynamics:
        """Inicializa los parámetros de la dinámica cortical"""
        cfg = self.config
        
        # Límites para inicialización Xavier
        limit_input = np.sqrt(6.0 / (cfg.dim_input + cfg.dim_latent))
        limit_rec = np.sqrt(6.0 / (2 * cfg.dim_latent))
        limit_mem = np.sqrt(6.0 / (cfg.dim_working_memory + cfg.dim_latent))
        
        return CorticalDynamics(
            W_input=np.random.uniform(-limit_input, limit_input, 
                                     (cfg.dim_latent, cfg.dim_input)),
            W_recurrent=np.random.uniform(-limit_rec, limit_rec,
                                         (cfg.dim_latent, cfg.dim_latent)),
            W_memory=np.random.uniform(-limit_mem, limit_mem,
                                      (cfg.dim_latent, cfg.dim_working_memory)),
            b=np.zeros(cfg.dim_latent)
        )
    
    def _create_encoder(self) -> Callable:
        """Crea el encoder φ(ŷₜ) para transformar observaciones"""
        def encoder(y_hat: np.ndarray) -> np.ndarray:
            """
            Encoder simple: proyección lineal + activación
            eₜ = φ(ŷₜ)
            """
            # Asegurar dimensión correcta
            if len(y_hat) != self.config.dim_input:
                # Ajustar dimensión
                if len(y_hat) > self.config.dim_input:
                    y_hat = y_hat[:self.config.dim_input]
                else:
                    y_hat = np.pad(y_hat, (0, self.config.dim_input - len(y_hat)))
            
            # Normalización L2
            norm = np.linalg.norm(y_hat)
            if norm > 1e-9:
                y_hat = y_hat / norm
            
            return y_hat
        
        return encoder
    
    def _get_activation_function(self) -> Callable:
        """Retorna la función de activación configurada"""
        act = self.config.activation
        
        if act == ActivationFunction.TANH:
            return np.tanh
        elif act == ActivationFunction.RELU:
            return lambda x: np.maximum(0, x)
        elif act == ActivationFunction.GELU:
            # Aproximación de GELU
            return lambda x: 0.5 * x * (1 + np.tanh(np.sqrt(2/np.pi) * (x + 0.044715 * x**3)))
        elif act == ActivationFunction.SWISH:
            return lambda x: x / (1 + np.exp(-x))
        else:
            return lambda x: x
    
    def update(self, 
               y_hat: np.ndarray,
               alpha: np.ndarray,
               w: Optional[np.ndarray] = None) -> Tuple[np.ndarray, dict]:
        """
        Actualiza el estado cortical.
        
        zₜ = (1-leak)·f(W_rec·zₜ₋₁ + W_in·(αₜ⊙eₜ) + W_mem·wₜ₋₁ + b)
        
        Args:
            y_hat: observación filtrada (del tálamo)
            alpha: vector de atención (de attention.py)
            w: memoria de trabajo (opcional)
        
        Returns:
            z_new: nuevo estado latente
            metrics: métricas de la actualización
        """
        d = self.dynamics
        cfg = self.config
        
        # 1. Codificar observación: eₜ = φ(ŷₜ)
        e_t = self.encoder(y_hat)
        
        # 2. Modular por atención: αₜ⊙eₜ
        e_attended = alpha * e_t
        
        # 3. Componente recurrente
        z_rec = d.W_recurrent @ self.z
        
        # 4. Componente de entrada atendida
        z_input = d.W_input @ e_attended
        
        # 5. Componente de memoria de trabajo
        if w is not None and len(w) == cfg.dim_working_memory:
            z_memory = d.W_memory @ w
        else:
            z_memory = np.zeros(cfg.dim_latent)
        
        # 6. Pre-activación
        z_pre = z_rec + z_input + z_memory + d.b
        
        # 7. Activación no-lineal
        z_activated = self.activation_fn(z_pre)
        
        # 8. Leak (permite olvido gradual)
        z_new = (1 - cfg.leak_rate) * z_activated + cfg.leak_rate * self.z
        
        # Guardar historial
        self.z_history.append(self.z.copy())
        if len(self.z_history) > 1000:  # Límite de memoria
            self.z_history.pop(0)
        
        # Actualizar estado
        z_old = self.z
        self.z = z_new
        
        # Calcular métricas
        metrics = {
            'z_norm': np.linalg.norm(z_new),
            'z_change': np.linalg.norm(z_new - z_old),
            'z_mean': np.mean(z_new),
            'z_std': np.std(z_new),
            'sparsity': np.sum(np.abs(z_new) < 0.01) / len(z_new),
            'activation_mean': np.mean(z_activated),
            'input_contribution': np.linalg.norm(z_input) / (np.linalg.norm(z_pre) + 1e-9),
            'recurrent_contribution': np.linalg.norm(z_rec) / (np.linalg.norm(z_pre) + 1e-9)
        }
        
        return z_new, metrics
    
    def predict_next_observation(self, a: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Predice la siguiente observación basándose en el estado actual.
        ỹₜ = g(zₜ₋₁, aₜ₋₁)
        
        Args:
            a: acción previa (opcional)
        
        Returns:
            y_pred: observación predicha
        """
        # Modelo generativo simple: proyección lineal del estado
        # En producción, esto sería una red neuronal decodificadora
        
        # Matriz de proyección (pseudo-inversa de W_input)
        W_decode = np.linalg.pinv(self.dynamics.W_input)
        
        y_pred = W_decode @ self.z
        
        # Si hay acción, modular predicción (modelo forward)
        if a is not None:
            # Simplificado: acción solo escala la predicción
            action_scale = 1.0 + 0.1 * np.mean(a)
            y_pred = action_scale * y_pred
        
        return y_pred
    
    def compute_surprise(self, y_hat: np.ndarray, y_pred: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Calcula la sorpresa (error de predicción).
        δₜ = ŷₜ - ỹₜ
        𝓤ₜ = ‖δₜ‖²
        
        Args:
            y_hat: observación filtrada
            y_pred: predicción del modelo
        
        Returns:
            delta: vector de error
            surprise: magnitud escalar de sorpresa
        """
        # Asegurar misma dimensión
        min_len = min(len(y_hat), len(y_pred))
        delta = y_hat[:min_len] - y_pred[:min_len]
        
        # Sorpresa = energía del error
        surprise = np.sum(delta**2)
        
        return delta, surprise
    
    def get_state(self) -> np.ndarray:
        """Retorna copia del estado actual"""
        return self.z.copy()
    
    def set_state(self, z_new: np.ndarray):
        """Establece un nuevo estado (útil para reset o carga)"""
        if len(z_new) != self.config.dim_latent:
            raise ValueError(f"Dimensión incorrecta: esperado {self.config.dim_latent}, recibido {len(z_new)}")
        self.z = z_new.copy()
    
    def reset(self):
        """Resetea el estado a cero"""
        self.z = np.zeros(self.config.dim_latent)
        self.z_history = []
    
    def get_stability_metric(self) -> float:
        """
        Calcula métrica de estabilidad basada en eigenvalues de W_recurrent.
        
        Returns:
            stability: ρ(W_rec) - radio espectral
                      < 1.0 = estable, > 1.0 = inestable
        """
        eigenvalues = np.linalg.eigvals(self.dynamics.W_recurrent)
        spectral_radius = np.max(np.abs(eigenvalues))
        return float(spectral_radius)


# =========================
# Funciones de utilidad
# =========================

def create_cortical_state(dim_latent: int = 128,
                          dim_input: int = 384,
                          dim_wm: int = 64,
                          activation: str = 'tanh',
                          leak: float = 0.1) -> CorticalState:
    """
    Crea un estado cortical preconfigurado.
    
    Args:
        dim_latent: dimensión del estado latente z
        dim_input: dimensión de entrada (embeddings)
        dim_wm: dimensión de memoria de trabajo
        activation: función de activación
        leak: tasa de leak (olvido)
    
    Returns:
        CorticalState configurado
    """
    config = CorticalStateConfig(
        dim_latent=dim_latent,
        dim_input=dim_input,
        dim_working_memory=dim_wm,
        activation=ActivationFunction[activation.upper()],
        leak_rate=leak
    )
    
    return CorticalState(config)


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test del Estado Cortical Latente ===\n")
    
    np.random.seed(42)
    
    # Crear estado cortical
    cortex = create_cortical_state(
        dim_latent=32,
        dim_input=64,
        dim_wm=16,
        activation='tanh',
        leak=0.05
    )
    
    print(f"Configuración:")
    print(f"  Dim latente: {cortex.config.dim_latent}")
    print(f"  Dim entrada: {cortex.config.dim_input}")
    print(f"  Activación: {cortex.config.activation.value}")
    print(f"  Leak rate: {cortex.config.leak_rate}")
    
    # Verificar estabilidad
    stability = cortex.get_stability_metric()
    print(f"\nEstabilidad inicial (ρ): {stability:.4f} {'✓' if stability < 1.0 else '✗ INESTABLE'}")
    
    # Simular secuencia de observaciones
    print("\n--- Procesamiento de Secuencia ---")
    
    for t in range(5):
        # Observación simulada
        y_hat = np.random.randn(64) * 0.5
        
        # Atención simulada (más en primeras dimensiones)
        alpha = np.exp(-np.arange(64) / 20.0)
        alpha = alpha / np.sum(alpha)
        
        # Memoria de trabajo simulada
        w = np.random.randn(16) * 0.3
        
        # Actualizar estado
        z_new, metrics = cortex.update(y_hat, alpha, w)
        
        print(f"\nTick t={t}:")
        print(f"  ‖z‖ = {metrics['z_norm']:.4f}")
        print(f"  Δz = {metrics['z_change']:.4f}")
        print(f"  Sparsity = {metrics['sparsity']:.2%}")
        print(f"  Input contrib. = {metrics['input_contribution']:.2%}")
    
    # Test de predicción
    print("\n--- Predicción ---")
    y_pred = cortex.predict_next_observation()
    y_actual = np.random.randn(64) * 0.5
    delta, surprise = cortex.compute_surprise(y_actual, y_pred)
    
    print(f"Sorpresa 𝓤ₜ: {surprise:.4f}")
    print(f"Error máximo |δ|: {np.max(np.abs(delta)):.4f}")
    
    print("\n✅ Estado Cortical funcional - Representación latente activa")
