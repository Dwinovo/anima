from fastapi import APIRouter

from src.presentation.api.v1.agents import router as agent_router
from src.presentation.api.v1.events import router as event_router
from src.presentation.api.v1.sessions import router as session_router
from src.presentation.api.v1.social_actions import router as social_action_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(session_router)
api_router.include_router(agent_router)
api_router.include_router(event_router)
api_router.include_router(social_action_router)
