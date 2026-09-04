from fastapi import APIRouter, Depends

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
from app.core.api_key import verify_api_key

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", dependencies=[Depends(verify_api_key)])
api_router.include_router(
    verification.router,
    prefix="/validation",
    tags=["validation"],
    dependencies=[Depends(verify_api_key)],
)
api_router.include_router(
    account.router, prefix="/account", tags=["account"], dependencies=[Depends(verify_api_key)]
)
api_router.include_router(
    settings.router, prefix="/settings", tags=["settings"], dependencies=[Depends(verify_api_key)]
)
api_router.include_router(
    workspace.router,
    prefix="/workspaces",
    tags=["workspaces"],
    dependencies=[Depends(verify_api_key)],
)
api_router.include_router(
    category.router,
    prefix="/workspaces/{workspace_id}/categories",
    tags=["categories"],
    dependencies=[Depends(verify_api_key)],
)
api_router.include_router(
    card.router,
    prefix="/workspaces/{workspace_id}/cards",
    tags=["cards"],
    dependencies=[Depends(verify_api_key)],
)
