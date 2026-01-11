"""
Kimi K2 Integration - AMA-Intent
Punto de entrada para los componentes inspirados en Kimi K2

Este módulo integra:
1. MuonClip Optimizer - Entrenamiento estable sin loss spikes
2. Long Horizon Agent - Tareas de 200-300 pasos con coherencia
3. Agentic Data Synthesizer - Generación de trayectorias sintéticas (RLVR)
4. Context Caching + MLA - Reducción de costos del 90% y contextos largos

Autor: AMA-Intent Team
Fecha: 2025
"""

from agents.long_horizon import (
    Action,
    ActionType,
    AgentState,
    ContextManager,
    GoalDriftDetector,
    GoalState,
    LongHorizonAgent,
    Observation,
    StepStatus,
)
from ama_data.synthesis import (
    AgenticDataSynthesizer,
    BugInjector,
    BugPattern,
    BugType,
    CodeTrajectory,
    CodeVerifier,
)
from llm.connector import (
    CachedContext,
    ContextCache,
    LLMHubWithCaching,
    MultiHeadLatentAttention,
)
from training.optimizers import (
    AttentionMonitor,
    MuonClipConfig,
    MuonClipOptimizer,
    QKClipper,
    TrainingStats,
)

__all__ = [
    # Optimizers
    "MuonClipOptimizer",
    "MuonClipConfig",
    "AttentionMonitor",
    "QKClipper",
    "TrainingStats",
    # Long Horizon Agent
    "LongHorizonAgent",
    "ActionType",
    "StepStatus",
    "Action",
    "Observation",
    "GoalState",
    "AgentState",
    "ContextManager",
    "GoalDriftDetector",
    # Data Synthesis
    "AgenticDataSynthesizer",
    "BugInjector",
    "CodeVerifier",
    "BugType",
    "BugPattern",
    "CodeTrajectory",
    # LLM Caching
    "ContextCache",
    "MultiHeadLatentAttention",
    "CachedContext",
    "LLMHubWithCaching",
]


def get_version():
    """Retorna la versión de la integración Kimi K2"""
    return "1.0.0"


def get_components():
    """Retorna lista de componentes disponibles"""
    return {
        "muonclip_optimizer": "Optimizador estable para entrenamiento de Reward Models",
        "long_horizon_agent": "Agente capaz de ejecutar tareas de 200-300 pasos",
        "agentic_synthesizer": "Generador de trayectorias sintéticas con RLVR",
        "context_caching": "Sistema de cacheo de contexto para reducir costos 90%",
        "mla_attention": "Multi-Head Latent Attention para contextos largos (256K tokens)",
    }


if __name__ == "__main__":
    print("=" * 60)
    print("AMA-Intent - Integración Kimi K2")
    print("=" * 60)
    print(f"Versión: {get_version()}")
    print("\nComponentes disponibles:")
    for name, desc in get_components().items():
        print(f"  • {name}: {desc}")
    print("=" * 60)
