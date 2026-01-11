# control/pid_homeostasis.py - Control Homeostático PID (Cerebelo)
"""
Implementa control PID para homeostasis cerebral.
τₜ = PID(target_arousal - 𝓤ₜ)

Este módulo simula el cerebelo: regula parámetros críticos
para mantener el sistema en equilibrio dinámico.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np


class ControlledParameter(Enum):
    """Parámetros controlables del cerebro"""

    EXPLORATION = "exploration"  # τ exploración
    LEARNING_RATE = "learning_rate"  # η aprendizaje
    ATTENTION_LAMBDA = "attention_lambda"  # λ atención
    GATE_THRESHOLD = "gate_threshold"  # Umbral WM gating
    RISK_AVERSION = "risk_aversion"  # ρ aversión al riesgo


@dataclass
class PIDConfig:
    """Configuración del controlador PID"""

    Kp: float = 0.5  # Ganancia proporcional
    Ki: float = 0.1  # Ganancia integral
    Kd: float = 0.2  # Ganancia derivativa

    # Límites de salida
    output_min: float = 0.0
    output_max: float = 1.0

    # Anti-windup
    integral_limit: float = 10.0

    # Setpoint (objetivo)
    setpoint: float = 0.5


@dataclass
class PIDState:
    """Estado del controlador PID"""

    error: float = 0.0
    integral: float = 0.0
    derivative: float = 0.0
    previous_error: float = 0.0
    output: float = 0.5


class PIDController:
    """
    Controlador PID para un parámetro específico.

    Fórmula clásica:
    u(t) = Kp·e(t) + Ki·∫e(τ)dτ + Kd·de(t)/dt

    donde:
    - e(t) = setpoint - measurement (error)
    - u(t) = salida del controlador
    """

    def __init__(self, config: PIDConfig):
        """
        Args:
            config: configuración del PID
        """
        self.config = config
        self.state = PIDState()

        # Historial
        self.history = []

    def update(self, measurement: float, dt: float = 1.0) -> Tuple[float, Dict]:
        """
        Actualiza el controlador PID.

        Args:
            measurement: valor actual medido
            dt: paso de tiempo (normalmente 1.0 por tick)

        Returns:
            output: señal de control
            metrics: métricas del controlador
        """
        cfg = self.config

        # 1. Calcular error
        error = cfg.setpoint - measurement

        # 2. Componente Proporcional
        P = cfg.Kp * error

        # 3. Componente Integral (con anti-windup)
        self.state.integral += error * dt
        # Anti-windup: limitar acumulación
        self.state.integral = np.clip(
            self.state.integral, -cfg.integral_limit, cfg.integral_limit
        )
        I = cfg.Ki * self.state.integral

        # 4. Componente Derivativa
        if dt > 0:
            derivative = (error - self.state.previous_error) / dt
        else:
            derivative = 0.0
        D = cfg.Kd * derivative

        # 5. Salida total
        output_raw = P + I + D

        # 6. Saturación (limitar salida)
        output = np.clip(output_raw, cfg.output_min, cfg.output_max)

        # 7. Actualizar estado
        self.state.error = error
        self.state.derivative = derivative
        self.state.previous_error = error
        self.state.output = output

        # Métricas
        metrics = {
            "error": error,
            "P": P,
            "I": I,
            "D": D,
            "output": output,
            "integral": self.state.integral,
        }

        # Historial
        self.history.append(metrics)
        if len(self.history) > 1000:
            self.history.pop(0)

        return output, metrics

    def reset(self):
        """Resetea el estado del controlador"""
        self.state = PIDState()

    def set_setpoint(self, new_setpoint: float):
        """Cambia el objetivo del controlador"""
        self.config.setpoint = new_setpoint

    def tune(self, Kp: float, Ki: float, Kd: float):
        """Ajusta las ganancias del PID"""
        self.config.Kp = Kp
        self.config.Ki = Ki
        self.config.Kd = Kd

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del controlador"""
        if not self.history:
            return {}

        recent = self.history[-100:]

        return {
            "avg_error": np.mean([h["error"] for h in recent]),
            "std_error": np.std([h["error"] for h in recent]),
            "avg_output": np.mean([h["output"] for h in recent]),
            "integral_accumulated": self.state.integral,
            "settled": (
                np.std([h["error"] for h in recent[-10:]]) < 0.1
                if len(recent) >= 10
                else False
            ),
        }


class HomeostaticSystem:
    """
    Sistema Homeostático Multi-PID (Cerebelo).

    Controla múltiples parámetros del cerebro simultáneamente
    para mantener equilibrio dinámico.

    Parámetros controlados:
    1. Exploración τ: balance exploración-explotación
    2. Learning rate η: velocidad de aprendizaje
    3. Atención λ: concentración del foco atencional
    4. Gating: umbral de actualización WM
    5. Risk aversion ρ: tolerancia al riesgo
    """

    def __init__(self):
        """Inicializa sistema homeostático con múltiples PIDs"""

        # ============================================
        # PID 1: EXPLORACIÓN (basado en sorpresa)
        # ============================================
        self.exploration_pid = PIDController(
            PIDConfig(
                Kp=0.4,
                Ki=0.05,
                Kd=0.15,
                setpoint=1.0,  # Target: sorpresa moderada
                output_min=0.1,
                output_max=2.0,
            )
        )

        # ============================================
        # PID 2: LEARNING RATE (basado en estabilidad)
        # ============================================
        self.learning_rate_pid = PIDController(
            PIDConfig(
                Kp=0.3,
                Ki=0.02,
                Kd=0.1,
                setpoint=0.7,  # Target: estabilidad moderada
                output_min=0.001,
                output_max=0.1,
            )
        )

        # ============================================
        # PID 3: ATENCIÓN LAMBDA (basado en focus)
        # ============================================
        self.attention_pid = PIDController(
            PIDConfig(
                Kp=0.5,
                Ki=0.1,
                Kd=0.2,
                setpoint=0.6,  # Target: foco moderado
                output_min=0.1,
                output_max=5.0,
            )
        )

        # ============================================
        # PID 4: GATING THRESHOLD (basado en carga WM)
        # ============================================
        self.gating_pid = PIDController(
            PIDConfig(
                Kp=0.3,
                Ki=0.05,
                Kd=0.1,
                setpoint=0.5,  # Target: 50% capacidad WM
                output_min=0.2,
                output_max=0.9,
            )
        )

        # ============================================
        # PID 5: RISK AVERSION (basado en rendimiento)
        # ============================================
        self.risk_pid = PIDController(
            PIDConfig(
                Kp=0.4,
                Ki=0.08,
                Kd=0.15,
                setpoint=0.7,  # Target: éxito moderado
                output_min=0.0,
                output_max=1.0,
            )
        )

        # Estado actual de parámetros
        self.parameters = {
            ControlledParameter.EXPLORATION: 1.0,
            ControlledParameter.LEARNING_RATE: 0.01,
            ControlledParameter.ATTENTION_LAMBDA: 1.0,
            ControlledParameter.GATE_THRESHOLD: 0.5,
            ControlledParameter.RISK_AVERSION: 0.6,
        }

        # Historial
        self.update_count = 0

    def update_all(
        self,
        surprise: float,
        stability: float,
        attention_focus: float,
        wm_load: float,
        performance: float,
    ) -> Dict[ControlledParameter, float]:
        """
        Actualiza todos los controladores PID.

        Args:
            surprise: 𝓤ₜ (sorpresa actual)
            stability: estabilidad del sistema [0,1]
            attention_focus: índice de concentración [0,1]
            wm_load: carga de working memory [0,1]
            performance: rendimiento reciente [0,1]

        Returns:
            Dict con parámetros actualizados
        """
        self.update_count += 1

        # 1. Control de Exploración
        tau, _ = self.exploration_pid.update(surprise)
        self.parameters[ControlledParameter.EXPLORATION] = tau

        # 2. Control de Learning Rate
        eta, _ = self.learning_rate_pid.update(stability)
        self.parameters[ControlledParameter.LEARNING_RATE] = eta

        # 3. Control de Atención
        lambda_att, _ = self.attention_pid.update(attention_focus)
        self.parameters[ControlledParameter.ATTENTION_LAMBDA] = lambda_att

        # 4. Control de Gating
        gate_th, _ = self.gating_pid.update(wm_load)
        self.parameters[ControlledParameter.GATE_THRESHOLD] = gate_th

        # 5. Control de Risk Aversion
        rho, _ = self.risk_pid.update(performance)
        self.parameters[ControlledParameter.RISK_AVERSION] = rho

        return self.parameters.copy()

    def get_parameter(self, param: ControlledParameter) -> float:
        """Obtiene valor actual de un parámetro"""
        return self.parameters[param]

    def get_all_parameters(self) -> Dict[ControlledParameter, float]:
        """Obtiene todos los parámetros actuales"""
        return self.parameters.copy()

    def get_statistics(self) -> Dict:
        """Retorna estadísticas de todos los controladores"""
        return {
            "exploration": self.exploration_pid.get_statistics(),
            "learning_rate": self.learning_rate_pid.get_statistics(),
            "attention": self.attention_pid.get_statistics(),
            "gating": self.gating_pid.get_statistics(),
            "risk_aversion": self.risk_pid.get_statistics(),
            "update_count": self.update_count,
        }

    def adapt_to_context(self, context: str):
        """
        Adapta setpoints según contexto operativo.

        Args:
            context: 'learning', 'exploitation', 'exploration', 'emergency'
        """
        if context == "learning":
            # Priorizar aprendizaje: alta exploración, alta LR
            self.exploration_pid.set_setpoint(1.5)
            self.learning_rate_pid.set_setpoint(0.8)
            self.risk_pid.set_setpoint(0.5)  # Tolerar más riesgo

        elif context == "exploitation":
            # Priorizar rendimiento: baja exploración, baja LR
            self.exploration_pid.set_setpoint(0.5)
            self.learning_rate_pid.set_setpoint(0.3)
            self.risk_pid.set_setpoint(0.8)  # Menos riesgo

        elif context == "exploration":
            # Maximizar exploración
            self.exploration_pid.set_setpoint(2.0)
            self.risk_pid.set_setpoint(0.3)

        elif context == "emergency":
            # Modo seguro: mínima exploración, máxima aversión
            self.exploration_pid.set_setpoint(0.1)
            self.risk_pid.set_setpoint(0.95)


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test de Control PID Homeostático (Cerebelo) ===\n")

    np.random.seed(42)

    # Crear sistema homeostático
    homeostasis = HomeostaticSystem()

    print("Sistema Homeostático inicializado")
    print(f"Parámetros iniciales:")
    for param, value in homeostasis.get_all_parameters().items():
        print(f"  {param.value}: {value:.3f}")

    # Simular secuencia de estados
    print("\n--- Simulación de Control Homeostático ---\n")

    for t in range(20):
        # Métricas simuladas
        surprise = 1.0 + 0.5 * np.sin(t / 3) + np.random.randn() * 0.2
        stability = 0.7 + 0.2 * np.cos(t / 4) + np.random.randn() * 0.1
        attention_focus = 0.6 + 0.3 * np.sin(t / 5)
        wm_load = 0.5 + 0.2 * np.cos(t / 3)
        performance = 0.7 + 0.2 * np.sin(t / 6)

        # Actualizar controladores
        params = homeostasis.update_all(
            surprise=surprise,
            stability=stability,
            attention_focus=attention_focus,
            wm_load=wm_load,
            performance=performance,
        )

        if t < 5 or t % 5 == 0:
            print(f"Tick {t}:")
            print(f"  Inputs: surprise={surprise:.2f}, stability={stability:.2f}")
            print(f"  Outputs:")
            print(
                f"    τ (exploration) = {params[ControlledParameter.EXPLORATION]:.3f}"
            )
            print(
                f"    η (learning_rate) = {params[ControlledParameter.LEARNING_RATE]:.4f}"
            )
            print(
                f"    λ (attention) = {params[ControlledParameter.ATTENTION_LAMBDA]:.3f}"
            )
            print(
                f"    ρ (risk_aversion) = {params[ControlledParameter.RISK_AVERSION]:.3f}"
            )
            print()

    # Cambiar contexto
    print("\n--- Cambio de Contexto: LEARNING MODE ---")
    homeostasis.adapt_to_context("learning")

    for t in range(5):
        params = homeostasis.update_all(
            surprise=1.0,
            stability=0.7,
            attention_focus=0.6,
            wm_load=0.5,
            performance=0.7,
        )

    print(f"Parámetros después de learning mode:")
    for param, value in params.items():
        print(f"  {param.value}: {value:.3f}")

    # Estadísticas
    print("\n--- Estadísticas de Control ---")
    stats = homeostasis.get_statistics()

    for controller, controller_stats in stats.items():
        if controller != "update_count":
            print(f"\n{controller}:")
            for key, val in controller_stats.items():
                if isinstance(val, bool):
                    print(f"  {key}: {val}")
                elif isinstance(val, float):
                    print(f"  {key}: {val:.4f}")

    print(f"\nTotal updates: {stats['update_count']}")

    print("\n✅ Sistema PID Homeostático funcional - Cerebelo activo")
