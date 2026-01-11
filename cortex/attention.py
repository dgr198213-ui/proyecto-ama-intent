# cortex/attention.py - Mecanismo de Atención Basado en LSI
"""
Implementa el mecanismo de atención cortical basado en LSI (sensibilidad).
αₜ = softmax(λ·LSI(δₜ))

Este módulo determina qué dimensiones de la entrada son más relevantes
basándose en la sorpresa (error de predicción δₜ).
"""

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


@dataclass
class AttentionState:
    """Estado del mecanismo de atención"""

    alpha: np.ndarray  # Vector de atención actual [0,1]
    sensitivity_history: list  # Historial de sensibilidades
    focus_entropy: float  # Entropía del foco atencional
    lambda_param: float  # Parámetro de temperatura


class CorticalAttention:
    """
    Mecanismo de atención cortical basado en sensibilidad (LSI).

    La atención se dirige hacia las dimensiones donde hay mayor sorpresa,
    pero modulada por la sensibilidad estructural del sistema.
    """

    def __init__(self, dim: int, lambda_init: float = 1.0, history_size: int = 100):
        """
        Args:
            dim: dimensión del espacio de entrada
            lambda_init: temperatura inicial para softmax
            history_size: tamaño del historial de sensibilidades
        """
        self.dim = dim
        self.lambda_param = lambda_init
        self.history_size = history_size

        # Estado inicial
        self.state = AttentionState(
            alpha=np.ones(dim) / dim,  # Atención uniforme inicial
            sensitivity_history=[],
            focus_entropy=np.log(dim),  # Máxima entropía inicial
            lambda_param=lambda_init,
        )

        # Parámetros adaptativos
        self.lambda_min = 0.1
        self.lambda_max = 10.0

    def compute_LSI(self, delta: np.ndarray, epsilon: float = 1e-9) -> np.ndarray:
        """
        Calcula el índice de sensibilidad local (LSI) para cada dimensión.

        LSI mide cuánto "cambia" el sistema en cada dimensión ante perturbaciones.
        Para señales unidimensionales: LSI ≈ |δ| normalizado
        Para señales multidimensionales: LSI considera gradiente local

        Args:
            delta: vector de error/sorpresa δₜ = ŷₜ - ỹₜ
            epsilon: término de estabilidad numérica

        Returns:
            LSI: vector de sensibilidad por dimensión [0,1]
        """
        # Magnitud absoluta del error en cada dimensión
        abs_delta = np.abs(delta)

        # Normalización robusta (evita división por cero)
        max_delta = np.max(abs_delta)
        if max_delta < epsilon:
            # Sin cambio significativo → sensibilidad uniforme
            return np.ones_like(delta) / len(delta)

        # LSI básico: sensibilidad proporcional al error
        lsi = abs_delta / (max_delta + epsilon)

        # Suavizado espacial (considera vecindad)
        if len(delta) > 3:
            # Convolución con kernel gaussiano simple [0.25, 0.5, 0.25]
            lsi_smooth = np.copy(lsi)
            lsi_smooth[1:-1] = 0.25 * lsi[:-2] + 0.5 * lsi[1:-1] + 0.25 * lsi[2:]
            lsi = lsi_smooth

        # Normalización final [0, 1]
        lsi = lsi / (np.sum(lsi) + epsilon)

        return lsi

    def compute_attention(
        self, delta: np.ndarray, modulation: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, dict]:
        """
        Calcula el vector de atención basado en sorpresa y sensibilidad.

        αₜ = softmax(λ·LSI(δₜ) ⊙ modulation)

        Args:
            delta: error de predicción (sorpresa)
            modulation: modulación externa opcional (ej: relevancia de tarea)

        Returns:
            alpha: vector de atención normalizado
            metrics: métricas del mecanismo atencional
        """
        # Calcular sensibilidad
        lsi = self.compute_LSI(delta)

        # Aplicar modulación si existe
        if modulation is not None:
            lsi = lsi * modulation

        # Escalar por λ (temperatura)
        scaled_lsi = self.lambda_param * lsi

        # Softmax para normalizar en distribución de probabilidad
        exp_lsi = np.exp(scaled_lsi - np.max(scaled_lsi))  # Truco numérico
        alpha = exp_lsi / (np.sum(exp_lsi) + 1e-9)

        # Calcular entropía del foco atencional
        # H = -Σ αᵢ·log(αᵢ)
        # Baja entropía = foco concentrado, Alta entropía = foco difuso
        entropy = -np.sum(alpha * np.log(alpha + 1e-9))

        # Actualizar estado
        self.state.alpha = alpha
        self.state.focus_entropy = entropy
        self.state.sensitivity_history.append(lsi)

        # Mantener historial acotado
        if len(self.state.sensitivity_history) > self.history_size:
            self.state.sensitivity_history.pop(0)

        # Métricas
        metrics = {
            "lsi_mean": np.mean(lsi),
            "lsi_max": np.max(lsi),
            "lsi_std": np.std(lsi),
            "attention_entropy": entropy,
            "attention_max": np.max(alpha),
            "focus_index": self._compute_focus_index(alpha),
        }

        return alpha, metrics

    def _compute_focus_index(self, alpha: np.ndarray) -> float:
        """
        Índice de concentración del foco: 0 = completamente difuso, 1 = totalmente concentrado

        FI = 1 - H(α)/H_max
        donde H_max = log(n) es la entropía máxima (distribución uniforme)
        """
        H_current = -np.sum(alpha * np.log(alpha + 1e-9))
        H_max = np.log(len(alpha))

        focus_index = 1.0 - (H_current / H_max) if H_max > 0 else 0.0
        return max(0.0, min(1.0, focus_index))

    def modulate_alpha(self, alpha: np.ndarray, mode: str = "sharp") -> np.ndarray:
        """
        Modula el vector de atención según el modo operativo.

        Args:
            alpha: vector de atención base
            mode: 'sharp' (foco agudo), 'broad' (foco amplio), 'adaptive'

        Returns:
            alpha_mod: vector de atención modulado
        """
        if mode == "sharp":
            # Incrementar λ para foco más concentrado
            temp_lambda = self.lambda_param * 2.0
        elif mode == "broad":
            # Reducir λ para foco más difuso
            temp_lambda = self.lambda_param * 0.5
        else:  # adaptive
            # Mantener λ actual
            temp_lambda = self.lambda_param

        # Recalcular con nuevo λ
        scaled = temp_lambda * alpha
        exp_scaled = np.exp(scaled - np.max(scaled))
        alpha_mod = exp_scaled / (np.sum(exp_scaled) + 1e-9)

        return alpha_mod

    def adapt_lambda(self, performance_metric: float, target: float = 0.7):
        """
        Adapta λ basándose en el rendimiento del sistema.

        Si el sistema va bien → puede permitirse foco más concentrado (↑λ)
        Si el sistema va mal → necesita explorar más (↓λ)

        Args:
            performance_metric: métrica de rendimiento [0,1]
            target: objetivo de rendimiento
        """
        error = target - performance_metric

        # Control proporcional simple
        if error > 0.1:  # Rendimiento bajo
            self.lambda_param *= 0.95  # Reducir concentración
        elif error < -0.1:  # Rendimiento alto
            self.lambda_param *= 1.05  # Aumentar concentración

        # Mantener en rango válido
        self.lambda_param = np.clip(self.lambda_param, self.lambda_min, self.lambda_max)

        self.state.lambda_param = self.lambda_param

    def get_attention_mask(self, threshold: float = 0.1) -> np.ndarray:
        """
        Retorna máscara binaria de atención.
        Útil para gating: solo pasar dimensiones con atención > threshold

        Args:
            threshold: umbral mínimo de atención

        Returns:
            mask: array booleano
        """
        return self.state.alpha > threshold

    def apply_attention(self, x: np.ndarray, mode: str = "modulate") -> np.ndarray:
        """
        Aplica el vector de atención a una entrada.

        Args:
            x: vector de entrada
            mode: 'modulate' (α⊙x), 'gate' (mask·x), 'soft' (α^γ⊙x)

        Returns:
            x_attended: entrada modulada por atención
        """
        if mode == "modulate":
            return self.state.alpha * x

        elif mode == "gate":
            mask = self.get_attention_mask()
            return mask.astype(float) * x

        elif mode == "soft":
            # Atención suavizada (γ < 1 suaviza, γ > 1 agudiza)
            gamma = 0.5
            alpha_soft = np.power(self.state.alpha, gamma)
            alpha_soft = alpha_soft / (np.sum(alpha_soft) + 1e-9)
            return alpha_soft * x

        else:
            return x


# =========================
# Funciones de utilidad
# =========================


def create_attention_mechanism(dim: int, temperature: float = 1.0) -> CorticalAttention:
    """
    Crea un mecanismo de atención preconfigurado.

    Args:
        dim: dimensión del espacio
        temperature: λ inicial (mayor = más concentrado)

    Returns:
        CorticalAttention configurado
    """
    return CorticalAttention(dim=dim, lambda_init=temperature)


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test del Mecanismo de Atención Cortical (LSI) ===\n")

    np.random.seed(42)

    # Crear mecanismo de atención
    dim = 10
    attention = CorticalAttention(dim=dim, lambda_init=1.0)

    # Simular error de predicción con pico en dimensión 3 y 7
    delta = np.random.randn(dim) * 0.1
    delta[3] = 2.0  # Alta sorpresa en dim 3
    delta[7] = 1.5  # Media sorpresa en dim 7

    print(f"Error de predicción δₜ: {delta}")

    # Computar atención
    alpha, metrics = attention.compute_attention(delta)

    print(f"\nVector de atención αₜ: {alpha}")
    print(f"Dimensión con mayor atención: {np.argmax(alpha)}")
    print(f"\nMétricas:")
    for key, value in metrics.items():
        print(f"  {key}: {value:.4f}")

    # Test de modulación
    print("\n--- Modulación de Foco ---")
    alpha_sharp = attention.modulate_alpha(alpha, mode="sharp")
    alpha_broad = attention.modulate_alpha(alpha, mode="broad")

    print(f"Foco agudo (sharp): max={np.max(alpha_sharp):.4f}")
    print(f"Foco amplio (broad): max={np.max(alpha_broad):.4f}")

    # Test de aplicación
    print("\n--- Aplicación de Atención ---")
    x_input = np.random.randn(dim)
    x_attended = attention.apply_attention(x_input, mode="modulate")

    print(f"Entrada original: {x_input[:5]}...")
    print(f"Entrada atendida: {x_attended[:5]}...")
    print(
        f"Proporción atendida: {np.linalg.norm(x_attended)/np.linalg.norm(x_input):.3f}"
    )

    print("\n✅ Mecanismo de Atención funcional - Corteza activa")
