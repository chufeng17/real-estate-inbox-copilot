from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models import models
from app.schemas import schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.EmailThread])
def read_threads(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve email threads for the current agent.
    """
    threads = (
        db.query(models.EmailThread)
        .filter(models.EmailThread.agent_id == current_user.id)
        .order_by(models.EmailThread.last_message_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return threads

@router.get("/{thread_id}", response_model=schemas.EmailThread)
def read_thread(
    thread_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get thread by ID with messages.
    """
    thread = (
        db.query(models.EmailThread)
        .filter(models.EmailThread.id == thread_id, models.EmailThread.agent_id == current_user.id)
        .first()
    )
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread
