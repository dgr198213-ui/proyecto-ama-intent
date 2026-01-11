# decision/q_value.py - Evaluación de Acciones con MIEM
"""
Implementa la evaluación de valor de acciones con métricas integradas.
Qₜ(a) = 𝔼[R|zₜ,a] - Coste(a) - ρ(MIEM(zₜ,a,entorno))

Este módulo calcula el valor esperado de cada acción considerando
recompensa, coste y riesgo (MIEM).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np


class RewardType(Enum):
    """Tipos de recompensa"""

    IMMEDIATE = "inmediata"
    DISCOUNTED = "descontada"
    MULTI_OBJECTIVE = "multi-objetivo"


@dataclass
class ActionCandidate:
    """Candidato de acción"""

    id: str
    parameters: np.ndarray
    description: str
    metadata: Dict


@dataclass
class MIEMComponents:
    """Componentes de MIEM (Métrica Integrada de Eficiencia Modular)"""

    efficiency: float  # Eficiencia de ejecución
    impact: float  # Impacto esperado
    modularity: float  # Modularidad (reusabilidad)
    risk: float  # Riesgo estimado


class QValueEstimator:
    """
    Estimador de valor Q con integración MIEM.

    Evalúa acciones considerando:
    - Recompensa esperada
    - Coste de ejecución
    - Riesgo (vía MIEM)
    """

    def __init__(
        self,
        dim_state: int,
        dim_action: int,
        gamma: float = 0.95,
        risk_aversion: float = 0.5,
    ):
        """
        Args:
            dim_state: dimensión del estado z
            dim_action: dimensión del espacio de acciones
            gamma: factor de descuento temporal
            risk_aversion: ρ en [0,1] - aversión al riesgo
        """
        self.dim_state = dim_state
        self.dim_action = dim_action
        self.gamma = gamma
        self.risk_aversion = risk_aversion

        # Modelo de valor (aproximador de función)
        self.value_network = self._initialize_value_network()

        # Historial de recompensas para normalización
        self.reward_history = []
        self.reward_mean = 0.0
        self.reward_std = 1.0

    def _initialize_value_network(self) -> Dict[str, np.ndarray]:
        """Inicializa red de valor simple (lineal)"""
        limit = np.sqrt(6.0 / (self.dim_state + self.dim_action + 1))

        return {
            "W_state": np.random.uniform(-limit, limit, (64, self.dim_state)),
            "W_action": np.random.uniform(-limit, limit, (64, self.dim_action)),
            "W_output": np.random.uniform(-limit, limit, (1, 64)),
            "b_hidden": np.zeros(64),
            "b_output": np.zeros(1),
        }

    def compute_expected_reward(
        self, z: np.ndarray, a: np.ndarray, reward_model: Optional[Callable] = None
    ) -> float:
        """
        Calcula recompensa esperada 𝔼[R|zₜ,a].

        Args:
            z: estado actual
            a: acción candidata
            reward_model: modelo de recompensa externo (opcional)

        Returns:
            expected_reward: recompensa esperada
        """
        if reward_model is not None:
            return reward_model(z, a)

        # Modelo interno: aproximación con red de valor
        net = self.value_network

        # Forward pass
        h_state = net["W_state"] @ z
        h_action = net["W_action"] @ a
        h = np.tanh(h_state + h_action + net["b_hidden"])

        reward = float(net["W_output"] @ h + net["b_output"])

        return reward

    def compute_action_cost(
        self, a: np.ndarray, metadata: Optional[Dict] = None
    ) -> float:
        """
        Calcula el coste de ejecutar una acción.

        Args:
            a: acción
            metadata: metadatos adicionales (complejidad, recursos)

        Returns:
            cost: coste normalizado [0, inf)
        """
        # Componente 1: Magnitud de la acción
        magnitude_cost = np.linalg.norm(a)

        # Componente 2: Complejidad (si está en metadata)
        complexity_cost = 0.0
        if metadata and "complexity" in metadata:
            complexity_cost = metadata["complexity"]

        # Componente 3: Recursos requeridos
        resource_cost = 0.0
        if metadata and "resources" in metadata:
            resource_cost = np.sum(metadata["resources"])

        # Coste total (ponderado)
        total_cost = 0.5 * magnitude_cost + 0.3 * complexity_cost + 0.2 * resource_cost

        return total_cost

    def compute_MIEM(
        self, z: np.ndarray, a: np.ndarray, environment: Optional[Dict] = None
    ) -> MIEMComponents:
        """
        Calcula MIEM (Métrica Integrada de Eficiencia Modular).

        MIEM combina:
        - Eficiencia: qué tan bien usa recursos
        - Impacto: magnitud del cambio esperado
        - Modularidad: reusabilidad/composabilidad
        - Riesgo: incertidumbre y efectos adversos

        Args:
            z: estado actual
            a: acción
            environment: información del entorno

        Returns:
            MIEMComponents: componentes de la métrica
        """
        # 1. Eficiencia: ratio output/input
        action_magnitude = np.linalg.norm(a) + 1e-9
        expected_impact = self._estimate_impact(z, a)
        efficiency = expected_impact / action_magnitude

        # 2. Impacto: cambio esperado en el estado
        impact = expected_impact

        # 3. Modularidad: cuán "genérica" es la acción
        # Acciones específicas (dispersas) tienen baja modularidad
        # Acciones genéricas (concentradas) tienen alta modularidad
        modularity = 1.0 - self._compute_sparsity(a)

        # 4. Riesgo: varianza esperada + efectos adversos
        risk = self._estimate_risk(z, a, environment)

        return MIEMComponents(
            efficiency=efficiency, impact=impact, modularity=modularity, risk=risk
        )

    def _estimate_impact(self, z: np.ndarray, a: np.ndarray) -> float:
        """Estima el impacto de la acción en el estado"""
        # Modelo simplificado: proyección de acción en espacio de estado
        if len(a) != len(z):
            # Ajustar dimensiones
            a_proj = np.pad(a, (0, max(0, len(z) - len(a))))[: len(z)]
        else:
            a_proj = a

        # Impacto = norma del cambio proyectado
        impact = np.linalg.norm(a_proj)
        return float(impact)

    def _compute_sparsity(self, x: np.ndarray) -> float:
        """Calcula sparsity (proporción de elementos ~0)"""
        threshold = 0.01 * np.max(np.abs(x))
        return float(np.sum(np.abs(x) < threshold) / len(x))

    def _estimate_risk(
        self, z: np.ndarray, a: np.ndarray, environment: Optional[Dict] = None
    ) -> float:
        """
        Estima el riesgo de la acción.

        Factores de riesgo:
        - Magnitud de la acción (mayor = más riesgo)
        - Distancia del estado seguro
        - Incertidumbre del entorno
        """
        # Factor 1: Magnitud (acciones grandes = más riesgo)
        magnitude_risk = np.tanh(np.linalg.norm(a) / 10.0)

        # Factor 2: Desviación del estado nominal
        state_deviation = np.linalg.norm(z) / (np.sqrt(len(z)) + 1e-9)
        state_risk = np.tanh(state_deviation)

        # Factor 3: Incertidumbre del entorno
        env_risk = 0.0
        if environment and "uncertainty" in environment:
            env_risk = environment["uncertainty"]

        # Agregación
        total_risk = 0.4 * magnitude_risk + 0.4 * state_risk + 0.2 * env_risk

        return float(np.clip(total_risk, 0.0, 1.0))

    def compute_Q(
        self,
        z: np.ndarray,
        a: np.ndarray,
        metadata: Optional[Dict] = None,
        environment: Optional[Dict] = None,
        reward_model: Optional[Callable] = None,
    ) -> Tuple[float, Dict]:
        """
        Calcula el valor Q de una acción.

        Q(z,a) = 𝔼[R|z,a] - Coste(a) - ρ·Riesgo(MIEM)

        Args:
            z: estado actual
            a: acción candidata
            metadata: metadatos de la acción
            environment: información del entorno
            reward_model: modelo de recompensa externo

        Returns:
            Q_value: valor Q
            components: desglose de componentes
        """
        # 1. Recompensa esperada
        reward = self.compute_expected_reward(z, a, reward_model)

        # 2. Coste de acción
        cost = self.compute_action_cost(a, metadata)

        # 3. MIEM
        miem = self.compute_MIEM(z, a, environment)

        # 4. Penalización por riesgo
        risk_penalty = self.risk_aversion * miem.risk

        # 5. Valor Q total
        Q_value = reward - cost - risk_penalty

        # Componentes para análisis
        components = {
            "reward": reward,
            "cost": cost,
            "risk_penalty": risk_penalty,
            "miem_efficiency": miem.efficiency,
            "miem_impact": miem.impact,
            "miem_modularity": miem.modularity,
            "miem_risk": miem.risk,
            "Q_raw": Q_value,
        }

        # Actualizar historial de recompensas
        self.reward_history.append(reward)
        if len(self.reward_history) > 1000:
            self.reward_history.pop(0)

        # Actualizar estadísticas
        if len(self.reward_history) > 10:
            self.reward_mean = np.mean(self.reward_history)
            self.reward_std = np.std(self.reward_history) + 1e-9

        return Q_value, components

    def compute_Q_batch(
        self,
        z: np.ndarray,
        actions: List[ActionCandidate],
        environment: Optional[Dict] = None,
        reward_model: Optional[Callable] = None,
    ) -> List[Tuple[float, Dict]]:
        """
        Calcula Q para múltiples acciones.

        Args:
            z: estado actual
            actions: lista de acciones candidatas
            environment: información del entorno
            reward_model: modelo de recompensa

        Returns:
            List de (Q_value, components) para cada acción
        """
        results = []

        for action in actions:
            Q_val, components = self.compute_Q(
                z=z,
                a=action.parameters,
                metadata=action.metadata,
                environment=environment,
                reward_model=reward_model,
            )

            components["action_id"] = action.id
            components["action_desc"] = action.description

            results.append((Q_val, components))

        return results

    def normalize_Q_values(self, Q_values: List[float]) -> np.ndarray:
        """Normaliza valores Q usando estadísticas del historial"""
        Q_array = np.array(Q_values)

        if len(self.reward_history) > 10:
            Q_normalized = (Q_array - self.reward_mean) / self.reward_std
        else:
            # Sin suficiente historial, normalización min-max
            Q_min = np.min(Q_array)
            Q_max = np.max(Q_array)
            if Q_max - Q_min > 1e-9:
                Q_normalized = (Q_array - Q_min) / (Q_max - Q_min)
            else:
                Q_normalized = np.zeros_like(Q_array)

        return Q_normalized


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test del Estimador de Q-Value con MIEM ===\n")

    np.random.seed(42)

    # Crear estimador
    q_estimator = QValueEstimator(
        dim_state=32, dim_action=16, gamma=0.95, risk_aversion=0.6
    )

    print(f"Configuración:")
    print(f"  Dim estado: {q_estimator.dim_state}")
    print(f"  Dim acción: {q_estimator.dim_action}")
    print(f"  Aversión riesgo ρ: {q_estimator.risk_aversion}")

    # Estado simulado
    z = np.random.randn(32) * 0.5

    # Acciones candidatas
    actions = [
        ActionCandidate(
            id="a1",
            parameters=np.random.randn(16) * 0.3,
            description="Acción conservadora",
            metadata={"complexity": 0.2},
        ),
        ActionCandidate(
            id="a2",
            parameters=np.random.randn(16) * 1.5,
            description="Acción agresiva",
            metadata={"complexity": 0.8},
        ),
        ActionCandidate(
            id="a3",
            parameters=np.random.randn(16) * 0.7,
            description="Acción balanceada",
            metadata={"complexity": 0.5},
        ),
    ]

    # Evaluar acciones
    print("\n--- Evaluación de Acciones ---")
    results = q_estimator.compute_Q_batch(z, actions)

    for i, (Q_val, comp) in enumerate(results):
        print(f"\n{actions[i].description} ({actions[i].id}):")
        print(f"  Q-value: {Q_val:.4f}")
        print(f"  Recompensa: {comp['reward']:.4f}")
        print(f"  Coste: {comp['cost']:.4f}")
        print(f"  Penalización riesgo: {comp['risk_penalty']:.4f}")
        print(f"  MIEM:")
        print(f"    Eficiencia: {comp['miem_efficiency']:.4f}")
        print(f"    Impacto: {comp['miem_impact']:.4f}")
        print(f"    Modularidad: {comp['miem_modularity']:.4f}")
        print(f"    Riesgo: {comp['miem_risk']:.4f}")

    # Mejor acción
    best_idx = np.argmax([r[0] for r in results])
    print(
        f"\n✓ Mejor acción: {actions[best_idx].description} (Q={results[best_idx][0]:.4f})"
    )

    print("\n✅ Estimador Q-Value funcional con MIEM integrado")
