"""
Audio Service - MiniMax Integration
====================================

Servicio para síntesis de voz, clonación y diseño de voces usando MiniMax.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


class AudioService:
    """
    Servicio de audio que utiliza MiniMax para síntesis de voz.

    Este servicio proporciona capacidades de text-to-speech, clonación de voz
    y diseño de voces personalizadas para el sistema AMA-Intent.
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Inicializa el servicio de audio.

        Args:
            output_dir: Directorio donde se guardarán los archivos de audio generados.
                       Por defecto: ./ama_data/audio/
        """
        if output_dir is None:
            output_dir = str(Path(__file__).parent.parent / "ama_data" / "audio")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = "Spanish_Narrator",
        emotion: str = "neutral",
        speed: float = 1.0,
        output_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convierte texto a voz usando MiniMax.

        Args:
            text: El texto a convertir en voz
            voice_id: ID de la voz a usar (ej: "Spanish_Narrator")
            emotion: Emoción de la voz ("happy", "sad", "angry", "neutral", etc.)
            speed: Velocidad de la voz (0.5 a 2.0)
            output_filename: Nombre del archivo de salida (opcional)

        Returns:
            Dict con información sobre el archivo generado
        """
        # Preparar argumentos
        args = {
            "text": text,
            "voice_id": voice_id,
            "output_dir": str(self.output_dir),
        }

        # Ejecutar comando MCP
        try:
            result = subprocess.run(
                [
                    "manus-mcp-cli",
                    "tool",
                    "call",
                    "text_to_audio",
                    "--server",
                    "minimax",
                    "--input",
                    json.dumps(args),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parsear resultado
            output = result.stdout.strip()

            return {
                "success": True,
                "output": output,
                "output_dir": str(self.output_dir),
                "text": text,
                "voice_id": voice_id or "default",
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": str(e),
                "stderr": e.stderr,
            }

    def list_available_voices(self, voice_type: str = "all") -> Dict[str, Any]:
        """
        Lista las voces disponibles en MiniMax.

        Args:
            voice_type: Tipo de voces ("all", "system", "voice_cloning")

        Returns:
            Dict con la lista de voces disponibles
        """
        args = {"voice_type": voice_type}

        try:
            result = subprocess.run(
                [
                    "manus-mcp-cli",
                    "tool",
                    "call",
                    "list_voices",
                    "--server",
                    "minimax",
                    "--input",
                    json.dumps(args),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            return {
                "success": True,
                "voices": result.stdout.strip(),
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": str(e),
                "stderr": e.stderr,
            }

    def design_voice(
        self, prompt: str, preview_text: str, voice_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Diseña una voz personalizada basada en una descripción.

        Args:
            prompt: Descripción de la voz deseada
            preview_text: Texto para previsualizar la voz
            voice_id: ID base de voz (opcional)

        Returns:
            Dict con información sobre la voz diseñada
        """
        args = {
            "prompt": prompt,
            "preview_text": preview_text,
            "output_directory": str(self.output_dir),
        }

        if voice_id:
            args["voice_id"] = voice_id

        try:
            result = subprocess.run(
                [
                    "manus-mcp-cli",
                    "tool",
                    "call",
                    "voice_design",
                    "--server",
                    "minimax",
                    "--input",
                    json.dumps(args),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            return {
                "success": True,
                "output": result.stdout.strip(),
                "prompt": prompt,
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": str(e),
                "stderr": e.stderr,
            }

    def generate_notification_sound(
        self, notification_type: str, message: str
    ) -> Dict[str, Any]:
        """
        Genera un sonido de notificación personalizado.

        Args:
            notification_type: Tipo de notificación ("info", "warning", "error", "success")
            message: Mensaje de la notificación

        Returns:
            Dict con información sobre el audio generado
        """
        # Mapeo de emociones según tipo de notificación
        emotion_map = {
            "info": "neutral",
            "warning": "surprised",
            "error": "angry",
            "success": "happy",
        }

        emotion = emotion_map.get(notification_type, "neutral")

        return self.text_to_speech(
            text=message,
            emotion=emotion,
            speed=1.1,  # Ligeramente más rápido para notificaciones
        )


# Ejemplo de uso
if __name__ == "__main__":
    audio_service = AudioService()

    # Test 1: Síntesis de voz simple
    print("Test 1: Síntesis de voz básica")
    result = audio_service.text_to_speech(
        text="Bienvenido al sistema AMA-Intent. El análisis de código ha finalizado correctamente.",
        emotion="happy",
    )
    print(f"Resultado: {result}")

    # Test 2: Listar voces disponibles
    print("\nTest 2: Listar voces disponibles")
    voices = audio_service.list_available_voices()
    print(f"Voces: {voices}")

    # Test 3: Notificación de éxito
    print("\nTest 3: Notificación de éxito")
    notification = audio_service.generate_notification_sound(
        notification_type="success", message="Tarea completada con éxito"
    )
    print(f"Notificación: {notification}")
