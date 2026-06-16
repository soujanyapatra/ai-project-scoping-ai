from fastapi import APIRouter

from app.api.v1.routes import scope
from app.api.v1.routes import estimate
from app.api.v1.routes import requirements

api_router = APIRouter()

api_router.include_router(
    scope.router,
    tags=["scope"]
)

api_router.include_router(
    estimate.router,
    tags=["estimate"]
)

api_router.include_router(
    requirements.router,
    tags=["requirements"]
)