from app.api.routes import auth, health, settings
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
