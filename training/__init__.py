"""
Training Module - AMA-Intent
Módulos para entrenamiento de modelos de recompensa y optimización
"""

from .optimizers.muonclip import (
    MuonClipOptimizer,
    MuonClipConfig,
    AttentionMonitor,
    QKClipper,
    TrainingStats
)

__all__ = [
    'MuonClipOptimizer',
    'MuonClipConfig',
    'AttentionMonitor',
    'QKClipper',
    'TrainingStats'
]
