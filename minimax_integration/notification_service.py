"""
Notification Service - MiniMax Integration
===========================================

Sistema de notificaciones multimodales que combina texto, voz e imágenes.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from .audio_service import AudioService
from .image_service import ImageService


class NotificationService:
    """
    Servicio de notificaciones multimodales para AMA-Intent.

    Combina texto, voz e imágenes para crear notificaciones ricas
    y efectivas que mejoran la experiencia del usuario.
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Inicializa el servicio de notificaciones.

        Args:
            output_dir: Directorio base para archivos generados
        """
        if output_dir is None:
            output_dir = str(
                Path(__file__).parent.parent / "ama_data" / "notifications"
            )

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar servicios
        self.audio_service = AudioService(
            output_dir=str(self.output_dir / "audio")
        )
        self.image_service = ImageService(
            output_dir=str(self.output_dir / "images")
        )

        # Configuración de voces por tipo de notificación
        self.voice_config = {
            "info": {"emotion": "neutral", "speed": 1.0},
            "success": {"emotion": "happy", "speed": 1.1},
            "warning": {"emotion": "surprised", "speed": 1.0},
            "error": {"emotion": "sad", "speed": 0.9},
            "critical": {"emotion": "angry", "speed": 0.8},
        }

    def send_notification(
        self,
        notification_type: str,
        title: str,
        message: str,
        with_audio: bool = True,
        with_icon: bool = False,
    ) -> Dict[str, Any]:
        """
        Envía una notificación multimodal.

        Args:
            notification_type: Tipo de notificación ("info", "success", "warning", "error", "critical")
            title: Título de la notificación
            message: Mensaje de la notificación
            with_audio: Si se debe generar audio
            with_icon: Si se debe generar un icono visual

        Returns:
            Dict con información sobre la notificación enviada
        """
        result = {
            "type": notification_type,
            "title": title,
            "message": message,
            "timestamp": None,  # Aquí se añadiría timestamp real
            "audio": None,
            "icon": None,
        }

        # Generar audio si está habilitado
        if with_audio:
            voice_config = self.voice_config.get(
                notification_type, {"emotion": "neutral", "speed": 1.0}
            )

            audio_text = f"{title}. {message}"
            audio_result = self.audio_service.text_to_speech(
                text=audio_text,
                emotion=voice_config["emotion"],
                speed=voice_config["speed"],
            )

            result["audio"] = audio_result

        # Generar icono si está habilitado
        if with_icon:
            icon_descriptions = {
                "info": "information icon, blue circle with 'i' letter",
                "success": "success icon, green checkmark in circle",
                "warning": "warning icon, yellow triangle with exclamation mark",
                "error": "error icon, red X in circle",
                "critical": "critical alert icon, red octagon with exclamation mark",
            }

            icon_desc = icon_descriptions.get(
                notification_type, "notification bell icon"
            )
            icon_result = self.image_service.generate_icon(
                description=icon_desc, style="flat"
            )

            result["icon"] = icon_result

        return result

    def notify_task_complete(
        self, task_name: str, duration: float, with_audio: bool = True
    ) -> Dict[str, Any]:
        """
        Notifica la finalización de una tarea.

        Args:
            task_name: Nombre de la tarea completada
            duration: Duración de la tarea en segundos
            with_audio: Si se debe generar audio

        Returns:
            Dict con información sobre la notificación
        """
        message = f"La tarea '{task_name}' se ha completado en {duration:.1f} segundos."

        return self.send_notification(
            notification_type="success",
            title="Tarea Completada",
            message=message,
            with_audio=with_audio,
            with_icon=False,
        )

    def notify_error(
        self, error_type: str, error_message: str, with_audio: bool = True
    ) -> Dict[str, Any]:
        """
        Notifica un error en el sistema.

        Args:
            error_type: Tipo de error
            error_message: Mensaje de error
            with_audio: Si se debe generar audio

        Returns:
            Dict con información sobre la notificación
        """
        message = f"Error de tipo {error_type}: {error_message}"

        return self.send_notification(
            notification_type="error",
            title="Error del Sistema",
            message=message,
            with_audio=with_audio,
            with_icon=False,
        )

    def notify_analysis_complete(
        self, analysis_type: str, results_summary: str, with_audio: bool = True
    ) -> Dict[str, Any]:
        """
        Notifica la finalización de un análisis.

        Args:
            analysis_type: Tipo de análisis realizado
            results_summary: Resumen de resultados
            with_audio: Si se debe generar audio

        Returns:
            Dict con información sobre la notificación
        """
        message = f"Análisis de {analysis_type} completado. {results_summary}"

        return self.send_notification(
            notification_type="info",
            title="Análisis Completado",
            message=message,
            with_audio=with_audio,
            with_icon=False,
        )

    def notify_wellness_reminder(
        self, reminder_type: str, message: str, with_audio: bool = True
    ) -> Dict[str, Any]:
        """
        Notifica un recordatorio de bienestar.

        Args:
            reminder_type: Tipo de recordatorio ("break", "exercise", "hydration")
            message: Mensaje del recordatorio
            with_audio: Si se debe generar audio

        Returns:
            Dict con información sobre la notificación
        """
        return self.send_notification(
            notification_type="info",
            title="Recordatorio de Bienestar",
            message=message,
            with_audio=with_audio,
            with_icon=False,
        )


# Ejemplo de uso
if __name__ == "__main__":
    notification_service = NotificationService()

    # Test 1: Notificación de tarea completada
    print("Test 1: Notificación de tarea completada")
    result = notification_service.notify_task_complete(
        task_name="Análisis de código", duration=45.3, with_audio=True
    )
    print(f"Resultado: {result}")

    # Test 2: Notificación de error
    print("\nTest 2: Notificación de error")
    error_result = notification_service.notify_error(
        error_type="ImportError",
        error_message="No se pudo importar el módulo requerido",
        with_audio=True,
    )
    print(f"Error: {error_result}")

    # Test 3: Recordatorio de bienestar
    print("\nTest 3: Recordatorio de bienestar")
    wellness_result = notification_service.notify_wellness_reminder(
        reminder_type="break",
        message="Es hora de tomar un descanso de 5 minutos. Estira tus brazos y descansa tu vista.",
        with_audio=True,
    )
    print(f"Bienestar: {wellness_result}")
