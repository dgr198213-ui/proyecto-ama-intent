"""
Módulo de Analíticas con Integración MiniMax para AMA-Intent Dashboard
Proporciona métricas de productividad y generación de informes multimodales.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from minimax_integration import AudioService, ImageService
from .database import DebugSession, Project, SystemLog


class AnalyticsManager:
    """Gestor de analíticas e informes multimodales"""

    def __init__(self, db: Session):
        self.db = db
        self.audio = AudioService()
        self.image = ImageService()

    def get_productivity_metrics(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Calcula métricas de productividad para un usuario"""
        since_date = datetime.now() - timedelta(days=days)

        # Sesiones de debug
        debug_stats = (
            self.db.query(
                func.count(DebugSession.id).label("count"),
                func.sum(DebugSession.time_saved_minutes).label("total_time_saved"),
            )
            .filter(DebugSession.user_id == user_id, DebugSession.created_at >= since_date)
            .first()
        )

        # Proyectos activos
        active_projects = (
            self.db.query(Project)
            .filter(Project.user_id == user_id, Project.status == "active")
            .count()
        )

        # Errores frecuentes
        top_errors = (
            self.db.query(DebugSession.error_type, func.count(DebugSession.id).label("count"))
            .filter(DebugSession.user_id == user_id, DebugSession.created_at >= since_date)
            .group_by(DebugSession.error_type)
            .order_by(func.count(DebugSession.id).desc())
            .limit(3)
            .all()
        )

        return {
            "debug_count": debug_stats.count or 0,
            "time_saved_hours": round((debug_stats.total_time_saved or 0) / 60, 2),
            "active_projects": active_projects,
            "top_errors": [{"type": e[0], "count": e[1]} for e in top_errors],
            "period_days": days,
        }

    async def generate_visual_report(self, user_id: int) -> str:
        """Genera un gráfico de productividad usando MiniMax ImageService"""
        metrics = self.get_productivity_metrics(user_id)
        
        prompt = (
            f"A professional productivity dashboard chart showing: "
            f"{metrics['debug_count']} debug sessions completed, "
            f"{metrics['time_saved_hours']} hours saved, and "
            f"{metrics['active_projects']} active projects. "
            f"Style: modern, clean, data visualization, blue and white theme."
        )
        
        image_path = self.image.generate_image(
            prompt=prompt
        )
        return image_path

    def generate_voice_summary(self, user_id: int) -> str:
        """Genera un resumen de voz de la actividad usando MiniMax AudioService"""
        metrics = self.get_productivity_metrics(user_id)
        
        text = (
            f"Hola. Aquí tienes tu resumen de productividad de los últimos {metrics['period_days']} días. "
            f"Has completado {metrics['debug_count']} sesiones de resolución de errores, "
            f"lo que te ha ahorrado aproximadamente {metrics['time_saved_hours']} horas de trabajo. "
            f"Actualmente tienes {metrics['active_projects']} proyectos activos. "
            f"Sigue así, vas por muy buen camino."
        )
        
        audio_path = self.audio.text_to_speech(
            text=text,
            voice_id="Spanish_Narrator",
            emotion="happy"
        )
        return audio_path

    def log_event(self, level: str, message: str, module: str, user_id: Optional[int] = None):
        """Registra un evento en los logs del sistema"""
        log = SystemLog(
            level=level,
            message=message,
            module=module,
            user_id=user_id
        )
        self.db.add(log)
        self.db.commit()
