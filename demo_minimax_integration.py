#!/usr/bin/env python3
"""
Demo de Integración MiniMax en AMA-Intent
==========================================

Script de demostración que muestra las capacidades de la integración
de MiniMax en el sistema AMA-Intent.

Autor: AMA-Intent Team
Fecha: 2026-01-16
"""

import sys
from pathlib import Path

# Añadir al path
sys.path.insert(0, str(Path(__file__).parent))

from minimax_integration import AudioService, ImageService, NotificationService


def print_section(title):
    """Imprime un separador de sección."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70 + "\n")


def demo_audio_service():
    """Demuestra las capacidades del servicio de audio."""
    print_section("DEMO: Audio Service")

    audio_service = AudioService()

    # Demo 1: Síntesis de voz básica
    print("1. Síntesis de voz básica")
    print("   Generando audio de bienvenida...")
    result = audio_service.text_to_speech(
        text="Bienvenido al sistema AMA-Intent versión 2.0. Este es un sistema de inteligencia artificial biomimética.",
        emotion="happy",
        speed=1.0,
    )

    if result["success"]:
        print(f"   ✓ Audio generado exitosamente")
        print(f"   ✓ Directorio: {result['output_dir']}")
    else:
        print(f"   ✗ Error: {result.get('error')}")

    # Demo 2: Listar voces disponibles
    print("\n2. Listado de voces disponibles")
    print("   Consultando voces del sistema...")
    voices_result = audio_service.list_available_voices()

    if voices_result["success"]:
        print(f"   ✓ Voces obtenidas exitosamente")
        print(f"   ℹ Primeras líneas de la respuesta:")
        voice_lines = voices_result["voices"].split("\n")[:5]
        for line in voice_lines:
            if line.strip():
                print(f"     {line}")
    else:
        print(f"   ✗ Error: {voices_result.get('error')}")

    # Demo 3: Notificación de éxito
    print("\n3. Generación de notificación audible")
    print("   Generando notificación de tarea completada...")
    notification = audio_service.generate_notification_sound(
        notification_type="success", message="El análisis de código ha finalizado con éxito"
    )

    if notification["success"]:
        print(f"   ✓ Notificación generada exitosamente")
    else:
        print(f"   ✗ Error: {notification.get('error')}")


def demo_image_service():
    """Demuestra las capacidades del servicio de imágenes."""
    print_section("DEMO: Image Service")

    image_service = ImageService()

    # Demo 1: Diagrama de arquitectura
    print("1. Generación de diagrama de arquitectura")
    print("   Creando diagrama del sistema AMA-Intent...")

    components = [
        "Dashboard Web",
        "Core Cognitivo",
        "Knowledge Graph",
        "Sistema de Plugins",
        "Base de Datos SQLite",
    ]

    relationships = [
        {"from": "Dashboard Web", "to": "Core Cognitivo", "type": "uses"},
        {"from": "Core Cognitivo", "to": "Knowledge Graph", "type": "queries"},
        {"from": "Core Cognitivo", "to": "Sistema de Plugins", "type": "manages"},
        {"from": "Dashboard Web", "to": "Base de Datos SQLite", "type": "stores data in"},
    ]

    result = image_service.generate_architecture_diagram(components, relationships)

    if result["success"]:
        print(f"   ✓ Diagrama generado exitosamente")
        print(f"   ✓ Directorio: {result['output_dir']}")
        print(f"   ✓ Componentes: {len(components)}")
    else:
        print(f"   ✗ Error: {result.get('error')}")

    # Demo 2: Icono del sistema
    print("\n2. Generación de icono")
    print("   Creando icono del cerebro artificial...")

    icon_result = image_service.generate_icon(
        description="artificial brain with neural connections and circuits", style="modern"
    )

    if icon_result["success"]:
        print(f"   ✓ Icono generado exitosamente")
    else:
        print(f"   ✗ Error: {icon_result.get('error')}")

    # Demo 3: Logo del proyecto
    print("\n3. Generación de logo del proyecto")
    print("   Creando logo de AMA-Intent...")

    logo_result = image_service.generate_project_logo(
        project_name="AMA-Intent",
        project_description="biomimetic artificial intelligence system for complex task orchestration",
    )

    if logo_result["success"]:
        print(f"   ✓ Logo generado exitosamente (3 variantes)")
    else:
        print(f"   ✗ Error: {logo_result.get('error')}")


def demo_notification_service():
    """Demuestra las capacidades del servicio de notificaciones."""
    print_section("DEMO: Notification Service")

    notification_service = NotificationService()

    # Demo 1: Notificación de tarea completada
    print("1. Notificación de tarea completada")
    print("   Enviando notificación de análisis finalizado...")

    result = notification_service.notify_task_complete(
        task_name="Análisis de calidad de código", duration=42.5, with_audio=True
    )

    if result["audio"] and result["audio"]["success"]:
        print(f"   ✓ Notificación enviada con audio")
        print(f"   ℹ Tipo: {result['type']}")
        print(f"   ℹ Título: {result['title']}")
    else:
        print(f"   ⚠ Notificación enviada sin audio")

    # Demo 2: Notificación de análisis
    print("\n2. Notificación de análisis completado")
    print("   Enviando resumen de análisis...")

    analysis_result = notification_service.notify_analysis_complete(
        analysis_type="código Python",
        results_summary="Se encontraron 3 problemas menores y 2 recomendaciones de mejora",
        with_audio=True,
    )

    if analysis_result["audio"] and analysis_result["audio"]["success"]:
        print(f"   ✓ Notificación de análisis enviada")
    else:
        print(f"   ⚠ Notificación enviada sin audio")

    # Demo 3: Recordatorio de bienestar
    print("\n3. Recordatorio de bienestar")
    print("   Enviando recordatorio de pausa...")

    wellness_result = notification_service.notify_wellness_reminder(
        reminder_type="break",
        message="Has estado trabajando durante 60 minutos. Es momento de tomar un descanso de 5 minutos.",
        with_audio=True,
    )

    if wellness_result["audio"] and wellness_result["audio"]["success"]:
        print(f"   ✓ Recordatorio de bienestar enviado")
    else:
        print(f"   ⚠ Recordatorio enviado sin audio")


def demo_voice_assistant_plugin():
    """Demuestra las capacidades del plugin Voice Assistant."""
    print_section("DEMO: Voice Assistant Plugin")

    try:
        from plugins.voice_assistant import VoiceAssistantPlugin

        plugin = VoiceAssistantPlugin()

        # Info del plugin
        print("1. Información del plugin")
        info = plugin.get_info()
        print(f"   Nombre: {info['name']}")
        print(f"   Versión: {info['version']}")
        print(f"   Descripción: {info['description']}")
        print(f"   Capacidades: {', '.join(info['capabilities'])}")

        # Demo 2: Leer resultados de análisis
        print("\n2. Lectura de resultados de análisis")
        print("   Leyendo resultados en voz alta...")

        analysis_data = {
            "quality_score": 87,
            "issues_found": 2,
            "recommendations": [
                "Añadir documentación a funciones públicas",
                "Implementar tests unitarios para módulo X",
                "Refactorizar función compleja en módulo Y",
            ],
        }

        result = plugin.read_analysis_results(analysis_data)

        if result["success"]:
            print(f"   ✓ Análisis leído exitosamente")
        else:
            print(f"   ✗ Error: {result.get('error')}")

        # Demo 3: Leer lista de tareas
        print("\n3. Lectura de lista de tareas")
        print("   Leyendo tareas pendientes...")

        todos = [
            {"name": "Implementar feature de exportación"},
            {"name": "Revisar PR #42"},
            {"name": "Actualizar documentación"},
            {"name": "Corregir bug en módulo de autenticación"},
        ]

        todo_result = plugin.read_todo_list(todos)

        if todo_result["success"]:
            print(f"   ✓ Lista de tareas leída exitosamente")
        else:
            print(f"   ✗ Error: {todo_result.get('error')}")

    except ImportError as e:
        print(f"   ✗ No se pudo importar el plugin: {e}")


def demo_wellness_assistant_plugin():
    """Demuestra las capacidades del plugin Wellness Assistant mejorado."""
    print_section("DEMO: Wellness Assistant Plugin (Enhanced)")

    try:
        from plugins.wellness_assistant import WellnessAssistantPlugin

        plugin = WellnessAssistantPlugin()

        # Info del plugin
        print("1. Información del plugin")
        info = plugin.get_info()
        print(f"   Nombre: {info['name']}")
        print(f"   Versión: {info['version']}")
        print(f"   Descripción: {info['description']}")

        # Demo 2: Pausa guiada
        print("\n2. Pausa guiada con audio")
        print("   Iniciando pausa guiada de 5 minutos...")

        break_result = plugin.guided_break(duration_minutes=5)

        if break_result["success"]:
            print(f"   ✓ Pausa guiada iniciada")
            print(f"   ℹ Duración: {break_result['duration']} minutos")
        else:
            print(f"   ✗ Error al iniciar pausa")

        # Demo 3: Sesión de meditación
        print("\n3. Sesión de meditación guiada")
        print("   Iniciando sesión de respiración consciente...")

        meditation_result = plugin.meditation_session(session_type="breathing")

        if meditation_result["success"]:
            print(f"   ✓ Sesión de meditación iniciada")
            print(f"   ℹ Tipo: {meditation_result['session_type']}")
        else:
            print(f"   ✗ Error al iniciar meditación")

        # Demo 4: Rutina de estiramientos
        print("\n4. Rutina de estiramientos")
        print("   Iniciando rutina de estiramientos...")

        stretch_result = plugin.stretching_routine()

        if stretch_result["success"]:
            print(f"   ✓ Rutina de estiramientos iniciada")
        else:
            print(f"   ✗ Error al iniciar rutina")

    except ImportError as e:
        print(f"   ✗ No se pudo importar el plugin: {e}")


def main():
    """Función principal del demo."""
    print("\n" + "=" * 70)
    print(" DEMO: Integración MiniMax en AMA-Intent v2.0")
    print(" Demostrando capacidades de audio, imágenes y notificaciones")
    print("=" * 70)

    print("\nℹ NOTA: Este demo generará archivos de audio e imágenes.")
    print("ℹ Los archivos se guardarán en el directorio ama_data/")
    print("ℹ Algunos servicios pueden tardar unos segundos en responder.")

    try:
        # Ejecutar demos
        demo_audio_service()
        demo_image_service()
        demo_notification_service()
        demo_voice_assistant_plugin()
        demo_wellness_assistant_plugin()

        # Resumen final
        print_section("RESUMEN")
        print("✓ Demo completado exitosamente")
        print("\nCapacidades demostradas:")
        print("  • Síntesis de voz con control de emoción y velocidad")
        print("  • Generación de imágenes (diagramas, iconos, logos)")
        print("  • Sistema de notificaciones multimodales")
        print("  • Plugin de asistente de voz")
        print("  • Plugin de bienestar mejorado con guías de audio")
        print("\nArchivos generados en:")
        print("  • ama_data/audio/")
        print("  • ama_data/images/")
        print("  • ama_data/notifications/")
        print("  • ama_data/wellness/")

        print("\n" + "=" * 70)
        print(" Para más información, consulte docs/MINIMAX_INTEGRATION.md")
        print("=" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠ Demo interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Error durante el demo: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
