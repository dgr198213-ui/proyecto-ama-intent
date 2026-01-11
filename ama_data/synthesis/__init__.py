"""
Synthesis Module - AMA-Intent
Generación sintética de trayectorias para entrenamiento de Reward Models
RLVR: Reinforcement Learning with Verifiable Rewards
"""

from .synthesizer import (
    AgenticDataSynthesizer,
    BugInjector,
    BugPattern,
    BugType,
    CodeTrajectory,
    CodeVerifier,
)

__all__ = [
    "AgenticDataSynthesizer",
    "BugInjector",
    "CodeVerifier",
    "BugType",
    "BugPattern",
    "CodeTrajectory",
]
