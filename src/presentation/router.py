from fastapi import APIRouter

from src.presentation.api.v1.entities import router as entity_router
from src.presentation.api.v1.events import router as event_router
from src.presentation.api.v1.sessions import router as session_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(session_router)
api_router.include_router(entity_router)
api_router.include_router(event_router)
