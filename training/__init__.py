"""
Training Module - AMA-Intent
Módulos para entrenamiento de modelos de recompensa y optimización
"""

from .optimizers.muonclip import (AttentionMonitor, MuonClipConfig,
                                  MuonClipOptimizer, QKClipper, TrainingStats)

__all__ = [
    "MuonClipOptimizer",
    "MuonClipConfig",
    "AttentionMonitor",
    "QKClipper",
    "TrainingStats",
]
