"""
Script de prueba para la integración de MiniMax con el Dashboard v2.1
Valida la generación de analíticas y reportes multimodales.
"""

import asyncio
import os
import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_dashboard.database import DatabaseManager, User, Project, DebugSession
from personal_dashboard.analytics import AnalyticsManager

async def test_integration():
    print("🧪 Iniciando pruebas de integración Dashboard v2.1 + MiniMax...")
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    # 1. Obtener o crear usuario de prueba
    user = session.query(User).filter_by(username="admin").first()
    if not user:
        print("❌ Usuario admin no encontrado. Ejecuta scripts/migrate_and_upgrade.py primero.")
        return

    # 2. Crear datos de prueba si no existen
    if session.query(Project).filter_by(user_id=user.id).count() == 0:
        project = Project(user_id=user.id, name="Test Project", description="Project for testing MiniMax")
        session.add(project)
        
    if session.query(DebugSession).filter_by(user_id=user.id).count() == 0:
        debug = DebugSession(
            user_id=user.id, 
            error_type="ImportError", 
            error_message="No module named 'minimax'",
            solution_provided="Install minimax-sdk",
            time_saved_minutes=30
        )
        session.add(debug)
    
    session.commit()
    print("✅ Datos de prueba preparados.")

    # 3. Probar AnalyticsManager
    analytics = AnalyticsManager(session)
    
    print("📊 Generando métricas de productividad...")
    metrics = analytics.get_productivity_metrics(user.id)
    print(f"Métricas: {metrics}")

    print("🎙️ Generando resumen de voz con MiniMax...")
    try:
        audio_path = analytics.generate_voice_summary(user.id)
        print(f"✅ Audio generado en: {audio_path}")
    except Exception as e:
        print(f"❌ Error en AudioService: {e}")

    print("🖼️ Generando reporte visual con MiniMax...")
    try:
        image_path = await analytics.generate_visual_report(user.id)
        print(f"✅ Imagen generada en: {image_path}")
    except Exception as e:
        print(f"❌ Error en ImageService: {e}")

    session.close()
    print("\n✨ Pruebas de integración completadas.")

if __name__ == "__main__":
    asyncio.run(test_integration())
