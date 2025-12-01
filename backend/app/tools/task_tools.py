from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models import models
from app.core.database import SessionLocal

def get_db_session():
    return SessionLocal()

def list_emails_for_thread_tool(thread_id: int) -> List[Dict[str, Any]]:
    """
    Fetches emails for a specific thread.
    """
    db = get_db_session()
    try:
        thread = db.query(models.EmailThread).filter(models.EmailThread.id == thread_id).first()
        if not thread:
            return []
        
        emails = []
        for msg in thread.messages:
            emails.append({
                "id": msg.id,
                "body_text": msg.body_text,
                "subject": msg.subject,
                "direction": msg.direction,
                "sent_at": msg.sent_at
            })
        return emails
    finally:
        db.close()

def upsert_task_tool(task_data: Dict[str, Any], agent_user_id: int) -> int:
    """
    Creates or updates a task.
    """
    db = get_db_session()
    try:
        # Check if task exists (e.g. by title + contact + type, or if ID provided)
        task_id = task_data.get("id")
        
        if task_id:
            task = db.query(models.Task).filter(models.Task.id == task_id).first()
        else:
            # Try to find existing task by title and contact to avoid duplicates
            # We use a loose match on title or exact match on type + contact if title is similar
            task = db.query(models.Task).filter(
                models.Task.contact_id == task_data.get("contact_id"),
                models.Task.title == task_data.get("title"),
                models.Task.task_type == task_data.get("task_type")
            ).first()
            
        if not task:
            task = models.Task(
                agent_id=agent_user_id,
                contact_id=task_data.get("contact_id"),
                task_type=task_data.get("task_type"),
                title=task_data.get("title"),
                detailed_description=task_data.get("detailed_description"),
                priority=task_data.get("priority", models.TaskPriority.MEDIUM),
                status=task_data.get("status", models.TaskStatus.OPEN),
                due_date=task_data.get("due_date"),
                source_thread_id=task_data.get("source_thread_id"),
                source_message_id=task_data.get("source_message_id")
            )
            db.add(task)
        else:
            # Update fields
            if "status" in task_data: task.status = task_data["status"]
            if "due_date" in task_data: task.due_date = task_data["due_date"]
            if "priority" in task_data: task.priority = task_data["priority"]
            if "detailed_description" in task_data: task.detailed_description = task_data["detailed_description"]
            
        db.commit()
        db.refresh(task)
        return task.id
    finally:
        db.close()

def compute_daily_agenda_tool(agent_user_id: int, target_date: date = None) -> List[Dict[str, Any]]:
    """
    Computes the agenda for the given date.
    """
    if target_date is None:
        target_date = date.today()
        
    db = get_db_session()
    try:
        # Fetch tasks due on or before today that are not done
        tasks = db.query(models.Task).filter(
            models.Task.agent_id == agent_user_id,
            models.Task.status != models.TaskStatus.DONE
        ).all()
        
        agenda = []
        for task in tasks:
            is_overdue = False
            if task.due_date:
                task_date = task.due_date.date()
                if task_date < target_date:
                    is_overdue = True
                
                if task_date <= target_date:
                    agenda.append({
                        "task": task,
                        "overdue": is_overdue
                    })
        
        # Sort by priority and due date
        # Priority map
        prio_map = {models.TaskPriority.HIGH: 0, models.TaskPriority.MEDIUM: 1, models.TaskPriority.LOW: 2}
        
        agenda.sort(key=lambda x: (prio_map.get(x["task"].priority, 1), x["task"].due_date or datetime.max))
        
        return agenda
    finally:
        db.close()
