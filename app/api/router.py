from fastapi import APIRouter

from app.api.routes import (
    account,
    auth,
    card,
    category,
    health,
    settings,
    verification,
    workspace,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(verification.router, prefix="/auth", tags=["auth"])
api_router.include_router(account.router, prefix="/account", tags=["account"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(workspace.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(
    category.router, prefix="/workspaces/{workspace_id}/categories", tags=["categories"]
)
api_router.include_router(card.router, prefix="/workspaces/{workspace_id}/cards", tags=["cards"])