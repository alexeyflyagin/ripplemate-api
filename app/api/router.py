from fastapi import APIRouter

from app.api.routes import auth, category, health, settings, workspace

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(workspace.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(
    category.router, prefix="/workspaces/{workspace_id}/categories", tags=["categories"]
)