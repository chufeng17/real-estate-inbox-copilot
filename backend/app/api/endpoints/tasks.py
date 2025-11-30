from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.models import models
from app.schemas import schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.Task])
def read_tasks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    contact_id: Optional[int] = None,
    overdue: Optional[bool] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve tasks with filtering.
    """
    query = db.query(models.Task).filter(models.Task.agent_id == current_user.id)
    
    if status:
        query = query.filter(models.Task.status == status)
    if priority:
        query = query.filter(models.Task.priority == priority)
    if contact_id:
        query = query.filter(models.Task.contact_id == contact_id)
    
    tasks = query.offset(skip).limit(limit).all()
    
    # Compute overdue flag dynamically for response
    now = datetime.utcnow()
    for task in tasks:
        if task.due_date and task.status != models.TaskStatus.DONE and task.due_date < now:
            task.overdue = True
        else:
            task.overdue = False
            
    if overdue is not None:
        tasks = [t for t in tasks if t.overdue == overdue]

    return tasks

@router.get("/{task_id}", response_model=schemas.Task)
def read_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get task by ID.
    """
    task = (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.agent_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    now = datetime.utcnow()
    if task.due_date and task.status != models.TaskStatus.DONE and task.due_date < now:
        task.overdue = True
    else:
        task.overdue = False
        
    return task

@router.patch("/{task_id}", response_model=schemas.Task)
def update_task(
    task_id: int,
    task_in: schemas.TaskUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update task status, due date, etc.
    """
    task = (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.agent_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_in.dict(exclude_unset=True)
    
    # Handle completion
    if "status" in update_data and update_data["status"] == models.TaskStatus.DONE and task.status != models.TaskStatus.DONE:
        task.completed_at = datetime.utcnow()
    elif "status" in update_data and update_data["status"] != models.TaskStatus.DONE:
        task.completed_at = None
        
    for field, value in update_data.items():
        if field != "notes": # Notes not in DB yet
             setattr(task, field, value)
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    now = datetime.utcnow()
    if task.due_date and task.status != models.TaskStatus.DONE and task.due_date < now:
        task.overdue = True
    else:
        task.overdue = False
        
    return task
