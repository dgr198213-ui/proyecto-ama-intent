"""
MiniMax Integration Module for AMA-Intent
==========================================

Este módulo proporciona integración con los servicios de MiniMax para:
- Síntesis de voz (Text-to-Speech)
- Generación de imágenes
- Generación de videos
- Generación de música
- Clonación y diseño de voces

Autor: AMA-Intent Team
Fecha: 2026-01-16
Versión: 1.0.0
"""

from .audio_service import AudioService
from .image_service import ImageService
from .notification_service import NotificationService

__all__ = ["AudioService", "ImageService", "NotificationService"]
__version__ = "1.0.0"
