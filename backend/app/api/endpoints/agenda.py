from typing import Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.api import deps
from app.models import models
from app.schemas import schemas

router = APIRouter()

@router.get("/today", response_model=List[schemas.Task])
def read_today_agenda(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve tasks for today's agenda.
    Includes:
    1. Overdue tasks (due_date < now AND status != DONE)
    2. Tasks due today (due_date is today)
    """
    now = datetime.utcnow()
    # Start of today (00:00:00) - naive approximation for now, ideally should handle timezones
    # But for this MVP, we'll just check if due_date is <= end of today
    
    # Actually, a common definition of "Agenda" is everything overdue + everything due in the next 24 hours or just "today".
    # Let's stick to: Overdue OR Due Today.
    
    # For "Due Today", we usually mean due_date is between today 00:00 and today 23:59.
    # However, since we are using UTC now, let's just say anything due before tomorrow's start.
    
    tomorrow = now + timedelta(days=1)
    tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    
    tasks = (
        db.query(models.Task)
        .filter(
            models.Task.agent_id == current_user.id,
            models.Task.status != models.TaskStatus.DONE,
            models.Task.due_date != None,
            models.Task.due_date < tomorrow_start
        )
        .order_by(models.Task.due_date.asc())
        .all()
    )
    
    # Compute overdue flag
    for task in tasks:
        if task.due_date and task.due_date < now:
            task.overdue = True
        else:
            task.overdue = False
            
    return tasks
