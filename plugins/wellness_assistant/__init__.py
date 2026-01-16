"""
Wellness Assistant Plugin - Enhanced with Audio
================================================

Plugin mejorado de asistente de bienestar con capacidades de audio
para guías de meditación, ejercicios y recordatorios.
"""

import sys
import time
from pathlib import Path

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from minimax_integration import AudioService


class WellnessAssistantPlugin:
    """
    Plugin de Asistente de Bienestar mejorado con capacidades de audio.

    Proporciona recordatorios, guías de ejercicios y meditación con
    instrucciones de voz para mejorar el bienestar del usuario.
    """

    def __init__(self):
        """Inicializa el plugin de bienestar."""
        self.name = "Wellness Assistant"
        self.version = "2.0.0"
        self.description = "Asistente de bienestar con guías de audio para pausas, ejercicios y meditación"
        self.author = "AMA-Intent Team"

        # Inicializar servicio de audio
        self.audio_service = AudioService(
            output_dir=str(root_dir / "ama_data" / "wellness" / "audio")
        )

        # Configuración
        self.break_interval = 3600  # 1 hora por defecto
        self.last_break = time.time()
        self.audio_enabled = True

    def get_info(self):
        """Retorna información sobre el plugin."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "capabilities": [
                "break_reminders",
                "exercise_guides",
                "meditation_sessions",
                "posture_checks",
                "eye_rest_exercises",
            ],
        }

    def guided_break(self, duration_minutes=5):
        """
        Inicia una pausa guiada con instrucciones de audio.

        Args:
            duration_minutes: Duración de la pausa en minutos

        Returns:
            Dict con resultado de la operación
        """
        script = f"""
        Es hora de tomar un descanso de {duration_minutes} minutos.
        
        Primero, levántate de tu silla y estira tus brazos hacia arriba.
        Mantén la posición durante 5 segundos.
        
        Ahora, gira tu cuello suavemente hacia la izquierda y hacia la derecha.
        Repite tres veces.
        
        Estira tus hombros moviendo los brazos en círculos.
        Cinco repeticiones hacia adelante, y cinco hacia atrás.
        
        Finalmente, camina un poco y bebe agua.
        
        Tu descanso ha terminado. Regresa renovado a tu trabajo.
        """

        if self.audio_enabled:
            result = self.audio_service.text_to_speech(
                text=script.strip(),
                emotion="neutral",
                speed=0.9,  # Más lento para instrucciones
            )
            return {
                "success": True,
                "type": "guided_break",
                "duration": duration_minutes,
                "audio": result,
            }
        else:
            return {
                "success": True,
                "type": "guided_break",
                "duration": duration_minutes,
                "script": script.strip(),
            }

    def meditation_session(self, session_type="breathing"):
        """
        Inicia una sesión de meditación guiada.

        Args:
            session_type: Tipo de sesión ("breathing", "body_scan", "mindfulness")

        Returns:
            Dict con resultado de la operación
        """
        scripts = {
            "breathing": """
                Bienvenido a esta sesión de respiración consciente.
                
                Siéntate cómodamente con la espalda recta.
                Cierra los ojos suavemente.
                
                Inhala profundamente por la nariz contando hasta cuatro.
                Uno, dos, tres, cuatro.
                
                Retén el aire contando hasta cuatro.
                Uno, dos, tres, cuatro.
                
                Exhala lentamente por la boca contando hasta seis.
                Uno, dos, tres, cuatro, cinco, seis.
                
                Repite este ciclo tres veces más a tu propio ritmo.
                
                Cuando termines, abre los ojos lentamente.
                Sesión completada.
            """,
            "body_scan": """
                Bienvenido a esta sesión de escaneo corporal.
                
                Siéntate o recuéstate cómodamente.
                Cierra los ojos.
                
                Lleva tu atención a tus pies. Nota cualquier sensación.
                Relaja tus pies completamente.
                
                Ahora, mueve tu atención a tus piernas. Libera cualquier tensión.
                
                Continúa hacia tu abdomen. Respira profundamente.
                Siente cómo se expande y contrae.
                
                Lleva tu atención a tu pecho y hombros.
                Deja caer los hombros, libera la tensión.
                
                Finalmente, relaja tu cuello, tu mandíbula y tu rostro.
                
                Toma tres respiraciones profundas.
                Abre los ojos lentamente cuando estés listo.
            """,
            "mindfulness": """
                Bienvenido a esta práctica de atención plena.
                
                Encuentra una posición cómoda.
                Respira naturalmente.
                
                Observa tus pensamientos sin juzgarlos.
                Como nubes que pasan en el cielo.
                
                Si tu mente divaga, simplemente nota que ha divagado.
                Y vuelve suavemente a tu respiración.
                
                No hay forma correcta o incorrecta de hacer esto.
                Solo estar presente en este momento.
                
                Continúa durante unos minutos más.
                
                Cuando estés listo, abre los ojos.
                Gracias por practicar.
            """,
        }

        script = scripts.get(session_type, scripts["breathing"])

        if self.audio_enabled:
            result = self.audio_service.text_to_speech(
                text=script.strip(),
                emotion="neutral",
                speed=0.8,  # Muy lento para meditación
            )
            return {
                "success": True,
                "type": "meditation",
                "session_type": session_type,
                "audio": result,
            }
        else:
            return {
                "success": True,
                "type": "meditation",
                "session_type": session_type,
                "script": script.strip(),
            }

    def posture_check_reminder(self):
        """
        Emite un recordatorio de revisión de postura.

        Returns:
            Dict con resultado de la operación
        """
        script = """
        Momento de revisar tu postura.
        
        Siéntate con la espalda recta.
        Los pies apoyados en el suelo.
        Los hombros relajados, no elevados.
        La pantalla a la altura de los ojos.
        
        Mantén esta postura correcta.
        """

        if self.audio_enabled:
            result = self.audio_service.text_to_speech(
                text=script.strip(), emotion="neutral", speed=1.0
            )
            return {"success": True, "type": "posture_check", "audio": result}
        else:
            return {"success": True, "type": "posture_check", "script": script.strip()}

    def eye_rest_exercise(self):
        """
        Guía un ejercicio de descanso visual.

        Returns:
            Dict con resultado de la operación
        """
        script = """
        Ejercicio de descanso visual.
        
        Mira hacia un punto lejano, al menos a 6 metros de distancia.
        Mantén la mirada durante 20 segundos.
        
        Ahora, parpadea rápidamente 10 veces.
        
        Cierra los ojos durante 10 segundos.
        
        Abre los ojos lentamente.
        Ejercicio completado. Tus ojos están descansados.
        """

        if self.audio_enabled:
            result = self.audio_service.text_to_speech(
                text=script.strip(), emotion="neutral", speed=0.9
            )
            return {"success": True, "type": "eye_rest", "audio": result}
        else:
            return {"success": True, "type": "eye_rest", "script": script.strip()}

    def stretching_routine(self):
        """
        Guía una rutina de estiramientos.

        Returns:
            Dict con resultado de la operación
        """
        script = """
        Rutina de estiramientos de escritorio.
        
        Ejercicio uno: Estiramiento de cuello.
        Inclina tu cabeza hacia la derecha, mantén 10 segundos.
        Ahora hacia la izquierda, mantén 10 segundos.
        
        Ejercicio dos: Estiramiento de hombros.
        Lleva tu brazo derecho cruzando el pecho.
        Con el brazo izquierdo, presiona suavemente.
        Mantén 15 segundos. Repite con el otro brazo.
        
        Ejercicio tres: Estiramiento de espalda.
        Entrelaza tus dedos y estira los brazos hacia adelante.
        Redondea tu espalda. Mantén 15 segundos.
        
        Ejercicio cuatro: Estiramiento de muñecas.
        Extiende tu brazo derecho con la palma hacia arriba.
        Con la otra mano, tira suavemente de los dedos hacia abajo.
        Mantén 10 segundos. Repite con la otra mano.
        
        Rutina completada. Excelente trabajo.
        """

        if self.audio_enabled:
            result = self.audio_service.text_to_speech(
                text=script.strip(), emotion="happy", speed=0.9
            )
            return {"success": True, "type": "stretching", "audio": result}
        else:
            return {"success": True, "type": "stretching", "script": script.strip()}

    def hydration_reminder(self):
        """
        Emite un recordatorio de hidratación.

        Returns:
            Dict con resultado de la operación
        """
        script = "Recuerda mantenerte hidratado. Es un buen momento para beber agua. Tu cuerpo te lo agradecerá."

        if self.audio_enabled:
            result = self.audio_service.text_to_speech(
                text=script, emotion="happy", speed=1.0
            )
            return {"success": True, "type": "hydration", "audio": result}
        else:
            return {"success": True, "type": "hydration", "script": script}

    def enable_audio(self):
        """Habilita las guías de audio."""
        self.audio_enabled = True
        return {"success": True, "message": "Audio guides enabled"}

    def disable_audio(self):
        """Deshabilita las guías de audio."""
        self.audio_enabled = False
        return {"success": True, "message": "Audio guides disabled"}

    def get_status(self):
        """Retorna el estado actual del plugin."""
        return {
            "audio_enabled": self.audio_enabled,
            "break_interval": self.break_interval,
            "time_since_last_break": time.time() - self.last_break,
        }


# Función de registro del plugin
def register_plugin():
    """
    Función de registro del plugin.

    Returns:
        Instancia del plugin
    """
    return WellnessAssistantPlugin()


# Ejemplo de uso
if __name__ == "__main__":
    plugin = WellnessAssistantPlugin()

    print(f"Plugin: {plugin.get_info()}")

    # Test 1: Pausa guiada
    print("\nTest 1: Guided break")
    result = plugin.guided_break(duration_minutes=5)
    print(f"Resultado: {result}")

    # Test 2: Sesión de meditación
    print("\nTest 2: Meditation session")
    meditation = plugin.meditation_session(session_type="breathing")
    print(f"Meditación: {meditation}")

    # Test 3: Recordatorio de postura
    print("\nTest 3: Posture check")
    posture = plugin.posture_check_reminder()
    print(f"Postura: {posture}")
