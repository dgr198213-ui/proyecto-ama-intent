"""
Router de Analíticas para AMA-Intent Dashboard
Expone endpoints para reportes visuales y de voz con MiniMax.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..analytics import AnalyticsManager
from ..auth import get_current_user_from_session
from ..database import get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/productivity")
async def get_productivity(request: Request, db: Session = Depends(get_db)):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    manager = AnalyticsManager(db)
    return manager.get_productivity_metrics(user.id)


@router.get("/report/visual")
async def get_visual_report(request: Request, db: Session = Depends(get_db)):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    manager = AnalyticsManager(db)
    image_path = await manager.generate_visual_report(user.id)

    return {
        "status": "success",
        "image_url": f"/static/images/{image_path.split('/')[-1]}",
    }


@router.get("/report/voice")
async def get_voice_report(request: Request, db: Session = Depends(get_db)):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    manager = AnalyticsManager(db)
    audio_path = manager.generate_voice_summary(user.id)

    return {
        "status": "success",
        "audio_url": f"/static/audio/{audio_path.split('/')[-1]}",
    }
