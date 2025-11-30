from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models import models
from app.schemas import schemas
from app.agents.chat_agent import CoachChatAgent

router = APIRouter()

@router.post("/", response_model=schemas.ChatResponse)
def chat(
    request: schemas.ChatRequest,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Chat with the Coach Agent.
    """
    import asyncio
    agent = CoachChatAgent()
    response = asyncio.run(agent.run(current_user.id, request.message, request.session_id))
    return response
