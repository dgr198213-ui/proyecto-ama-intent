"""
Voice Assistant Plugin for AMA-Intent
======================================

Plugin que proporciona capacidades de asistente de voz al dashboard,
permitiendo interacción por voz y respuestas audibles.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar minimax_integration
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from minimax_integration import AudioService, NotificationService


class VoiceAssistantPlugin:
    """
    Plugin de Asistente de Voz para AMA-Intent.

    Proporciona capacidades de text-to-speech y notificaciones audibles
    para mejorar la accesibilidad y la experiencia de usuario.
    """

    def __init__(self):
        """Inicializa el plugin de asistente de voz."""
        self.name = "Voice Assistant"
        self.version = "1.0.0"
        self.description = "Asistente de voz con capacidades de síntesis de voz y notificaciones audibles"
        self.author = "AMA-Intent Team"

        # Inicializar servicios
        self.audio_service = AudioService()
        self.notification_service = NotificationService()

        # Estado del asistente
        self.enabled = True
        self.current_voice = None
        self.volume = 1.0

    def get_info(self):
        """Retorna información sobre el plugin."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "enabled": self.enabled,
            "capabilities": [
                "text_to_speech",
                "voice_notifications",
                "voice_selection",
                "audio_feedback",
            ],
        }

    def speak(self, text, emotion="neutral", speed=1.0):
        """
        Convierte texto a voz y lo reproduce.

        Args:
            text: Texto a convertir en voz
            emotion: Emoción de la voz
            speed: Velocidad de reproducción

        Returns:
            Dict con resultado de la operación
        """
        if not self.enabled:
            return {"success": False, "error": "Voice assistant is disabled"}

        return self.audio_service.text_to_speech(
            text=text,
            voice_id=self.current_voice,
            emotion=emotion,
            speed=speed,
        )

    def list_voices(self):
        """
        Lista las voces disponibles.

        Returns:
            Dict con lista de voces
        """
        return self.audio_service.list_available_voices()

    def set_voice(self, voice_id):
        """
        Establece la voz actual del asistente.

        Args:
            voice_id: ID de la voz a usar

        Returns:
            Dict con resultado de la operación
        """
        self.current_voice = voice_id
        return {
            "success": True,
            "voice_id": voice_id,
            "message": f"Voice set to {voice_id}",
        }

    def notify(self, notification_type, title, message, with_audio=True):
        """
        Envía una notificación con audio opcional.

        Args:
            notification_type: Tipo de notificación
            title: Título
            message: Mensaje
            with_audio: Si incluir audio

        Returns:
            Dict con resultado de la notificación
        """
        if not self.enabled:
            with_audio = False

        return self.notification_service.send_notification(
            notification_type=notification_type,
            title=title,
            message=message,
            with_audio=with_audio,
        )

    def read_analysis_results(self, analysis_data):
        """
        Lee en voz alta los resultados de un análisis.

        Args:
            analysis_data: Datos del análisis a leer

        Returns:
            Dict con resultado de la operación
        """
        # Construir texto descriptivo del análisis
        text = "Resultados del análisis. "

        if isinstance(analysis_data, dict):
            if "quality_score" in analysis_data:
                text += (
                    f"Puntuación de calidad: {analysis_data['quality_score']} de 100. "
                )

            if "issues_found" in analysis_data:
                issues = analysis_data["issues_found"]
                text += f"Se encontraron {issues} problemas. "

            if "recommendations" in analysis_data:
                recs = analysis_data["recommendations"]
                if isinstance(recs, list) and recs:
                    text += "Recomendaciones principales: "
                    text += ". ".join(recs[:3])  # Primeras 3 recomendaciones

        return self.speak(text, emotion="neutral", speed=1.0)

    def read_todo_list(self, todos):
        """
        Lee en voz alta una lista de tareas pendientes.

        Args:
            todos: Lista de tareas pendientes

        Returns:
            Dict con resultado de la operación
        """
        if not todos:
            text = "No tienes tareas pendientes."
        else:
            text = f"Tienes {len(todos)} tareas pendientes. "
            for i, todo in enumerate(todos[:5], 1):  # Primeras 5 tareas
                if isinstance(todo, dict):
                    task_name = todo.get("name", todo.get("title", "Tarea sin nombre"))
                else:
                    task_name = str(todo)
                text += f"Tarea {i}: {task_name}. "

            if len(todos) > 5:
                text += f"Y {len(todos) - 5} tareas más."

        return self.speak(text, emotion="neutral", speed=1.0)

    def wellness_reminder(self, reminder_type="break"):
        """
        Emite un recordatorio de bienestar.

        Args:
            reminder_type: Tipo de recordatorio

        Returns:
            Dict con resultado de la operación
        """
        messages = {
            "break": "Es hora de tomar un descanso. Levántate, estira tu cuerpo y descansa tu vista durante 5 minutos.",
            "hydration": "Recuerda mantenerte hidratado. Es un buen momento para beber agua.",
            "posture": "Revisa tu postura. Mantén la espalda recta y los hombros relajados.",
            "eyes": "Descansa tu vista. Mira hacia un punto lejano durante 20 segundos para relajar tus ojos.",
        }

        message = messages.get(reminder_type, "Es momento de cuidar tu bienestar.")

        return self.notification_service.notify_wellness_reminder(
            reminder_type=reminder_type, message=message, with_audio=True
        )

    def enable(self):
        """Habilita el asistente de voz."""
        self.enabled = True
        return {"success": True, "message": "Voice assistant enabled"}

    def disable(self):
        """Deshabilita el asistente de voz."""
        self.enabled = False
        return {"success": True, "message": "Voice assistant disabled"}

    def get_status(self):
        """Retorna el estado actual del asistente."""
        return {
            "enabled": self.enabled,
            "current_voice": self.current_voice or "default",
            "volume": self.volume,
        }


# Función de registro del plugin (requerida por el sistema de plugins)
def register_plugin():
    """
    Función de registro del plugin.

    Returns:
        Instancia del plugin
    """
    return VoiceAssistantPlugin()


# Ejemplo de uso
if __name__ == "__main__":
    plugin = VoiceAssistantPlugin()

    print(f"Plugin: {plugin.get_info()}")

    # Test 1: Hablar
    print("\nTest 1: Speak")
    result = plugin.speak(
        "Hola, soy tu asistente de voz de AMA Intent", emotion="happy"
    )
    print(f"Resultado: {result}")

    # Test 2: Listar voces
    print("\nTest 2: List voices")
    voices = plugin.list_voices()
    print(f"Voces: {voices}")

    # Test 3: Leer resultados de análisis
    print("\nTest 3: Read analysis results")
    analysis = {
        "quality_score": 85,
        "issues_found": 3,
        "recommendations": [
            "Mejorar documentación",
            "Añadir tests unitarios",
            "Refactorizar función compleja",
        ],
    }
    analysis_result = plugin.read_analysis_results(analysis)
    print(f"Análisis: {analysis_result}")
