# sensing/kalman.py - Filtro Sensorial (Tálamo)
"""
Implementa el filtro de Kalman para reducir ruido en observaciones.
ŷₜ = Kalman(yₜ; Σₜ)

Este módulo actúa como el tálamo: filtra y estabiliza la entrada sensorial
antes de que llegue a la corteza.
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass

@dataclass
class KalmanState:
    """Estado del filtro de Kalman"""
    x: np.ndarray      # Estado estimado
    P: np.ndarray      # Covarianza del error
    F: np.ndarray      # Matriz de transición
    H: np.ndarray      # Matriz de observación
    Q: np.ndarray      # Ruido del proceso
    R: np.ndarray      # Ruido de la observación
    
class ThalamicFilter:
    """
    Filtro de Kalman para procesamiento sensorial.
    Reduce ruido y estabiliza observaciones antes del procesamiento cortical.
    """
    
    def __init__(self, dim_state: int, dim_obs: int, 
                 process_noise: float = 0.01,
                 measurement_noise: float = 0.1):
        """
        Args:
            dim_state: dimensión del estado latente
            dim_obs: dimensión de la observación
            process_noise: ruido del proceso Q
            measurement_noise: ruido de medición R
        """
        self.dim_state = dim_state
        self.dim_obs = dim_obs
        
        # Inicialización de matrices
        self.state = KalmanState(
            x=np.zeros(dim_state),
            P=np.eye(dim_state),
            F=np.eye(dim_state),  # Modelo lineal simple
            H=np.eye(dim_obs, dim_state) if dim_obs <= dim_state else np.random.randn(dim_obs, dim_state),
            Q=process_noise * np.eye(dim_state),
            R=measurement_noise * np.eye(dim_obs)
        )
        
        self.initialized = False
    
    def predict(self) -> np.ndarray:
        """
        Paso de predicción del filtro de Kalman.
        x̂⁻ₜ = F·x̂ₜ₋₁
        P⁻ₜ = F·Pₜ₋₁·Fᵀ + Q
        
        Returns:
            Estado predicho
        """
        s = self.state
        
        # Predicción del estado
        x_pred = s.F @ s.x
        
        # Predicción de la covarianza
        P_pred = s.F @ s.P @ s.F.T + s.Q
        
        # Actualizar estado
        self.state.x = x_pred
        self.state.P = P_pred
        
        return x_pred
    
    def update(self, y: np.ndarray) -> np.ndarray:
        """
        Paso de actualización del filtro de Kalman.
        Kₜ = P⁻ₜ·Hᵀ·(H·P⁻ₜ·Hᵀ + R)⁻¹
        x̂ₜ = x̂⁻ₜ + Kₜ·(yₜ - H·x̂⁻ₜ)
        Pₜ = (I - Kₜ·H)·P⁻ₜ
        
        Args:
            y: observación actual (puede ser embedding de texto)
        
        Returns:
            ŷₜ: observación filtrada
        """
        s = self.state
        
        # Asegurar que y es array numpy
        if not isinstance(y, np.ndarray):
            y = np.array(y)
        
        # Ajustar dimensiones si es necesario
        if y.shape[0] != self.dim_obs:
            # Proyectar o truncar
            if y.shape[0] > self.dim_obs:
                y = y[:self.dim_obs]
            else:
                y = np.pad(y, (0, self.dim_obs - y.shape[0]))
        
        # Inicialización en primera observación
        if not self.initialized:
            if self.dim_obs <= self.dim_state:
                self.state.x[:self.dim_obs] = y
            else:
                # Proyección PCA simplificada
                self.state.x = s.H.T @ y / np.linalg.norm(s.H.T @ y + 1e-9)
            self.initialized = True
            return y
        
        # Innovación (residual)
        y_pred = s.H @ s.x
        innovation = y - y_pred
        
        # Covarianza de la innovación
        S = s.H @ s.P @ s.H.T + s.R
        
        # Ganancia de Kalman
        K = s.P @ s.H.T @ np.linalg.inv(S)
        
        # Actualizar estado
        self.state.x = s.x + K @ innovation
        
        # Actualizar covarianza
        I_KH = np.eye(self.dim_state) - K @ s.H
        self.state.P = I_KH @ s.P
        
        # Observación filtrada
        y_filtered = s.H @ self.state.x
        
        return y_filtered
    
    def filter(self, y: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
        Filtrado completo: predict + update
        
        Args:
            y: observación ruidosa
        
        Returns:
            ŷₜ: observación filtrada
            metrics: métricas del filtro
        """
        # Predicción
        x_pred = self.predict()
        
        # Actualización
        y_filtered = self.update(y)
        
        # Calcular métricas
        metrics = {
            'state_norm': np.linalg.norm(self.state.x),
            'uncertainty': np.trace(self.state.P),
            'innovation_norm': np.linalg.norm(y - (self.state.H @ x_pred)) if self.initialized else 0.0
        }
        
        return y_filtered, metrics
    
    def get_state(self) -> np.ndarray:
        """Retorna el estado latente actual"""
        return self.state.x.copy()
    
    def get_uncertainty(self) -> float:
        """Retorna la incertidumbre total (traza de P)"""
        return np.trace(self.state.P)
    
    def adapt_noise(self, innovation_norm: float, window_size: int = 10):
        """
        Adaptación automática del ruido basado en la innovación.
        Si la innovación es alta → aumentar Q (más flexible)
        Si la innovación es baja → reducir Q (más confianza)
        """
        # Heurística simple de adaptación
        if innovation_norm > 2.0:
            self.state.Q *= 1.1
        elif innovation_norm < 0.5:
            self.state.Q *= 0.95
        
        # Límites de estabilidad
        self.state.Q = np.clip(self.state.Q, 1e-4, 1.0)


# =========================
# Funciones de utilidad
# =========================

def create_thalamic_filter(embedding_dim: int = 384, 
                           latent_dim: Optional[int] = None) -> ThalamicFilter:
    """
    Crea un filtro talámico preconfigurado.
    
    Args:
        embedding_dim: dimensión del embedding de entrada (ej: 384 para sentence-transformers)
        latent_dim: dimensión del estado latente (None = mismo que embedding)
    
    Returns:
        ThalamicFilter configurado
    """
    if latent_dim is None:
        latent_dim = min(embedding_dim, 128)  # Compresión por defecto
    
    return ThalamicFilter(
        dim_state=latent_dim,
        dim_obs=embedding_dim,
        process_noise=0.01,
        measurement_noise=0.1
    )


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test del Filtro Talámico (Kalman) ===\n")
    
    # Simular observaciones ruidosas (embeddings)
    np.random.seed(42)
    true_signal = np.sin(np.linspace(0, 4*np.pi, 50))
    noise = np.random.normal(0, 0.3, 50)
    observations = true_signal + noise
    
    # Crear filtro
    thalamus = ThalamicFilter(dim_state=1, dim_obs=1, 
                              process_noise=0.01, 
                              measurement_noise=0.3**2)
    
    # Filtrar señal
    filtered = []
    uncertainties = []
    
    for y in observations:
        y_filt, metrics = thalamus.filter(np.array([y]))
        filtered.append(y_filt[0])
        uncertainties.append(metrics['uncertainty'])
    
    # Resultados
    print(f"Observaciones ruidosas (primeras 5): {observations[:5]}")
    print(f"Señal filtrada (primeras 5): {np.array(filtered[:5])}")
    print(f"\nRMSE sin filtro: {np.sqrt(np.mean((observations - true_signal)**2)):.4f}")
    print(f"RMSE con filtro: {np.sqrt(np.mean((np.array(filtered) - true_signal)**2)):.4f}")
    print(f"\nIncertidumbre final: {uncertainties[-1]:.6f}")
    print(f"Incertidumbre promedio: {np.mean(uncertainties):.6f}")
    
    print("\n✅ Filtro Kalman funcional - Tálamo activo")
