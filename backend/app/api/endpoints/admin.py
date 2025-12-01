from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models import models
from app.core.database import SessionLocal
from app.services.vector_store import VectorStore

router = APIRouter()

@router.post("/reset-demo")
def reset_demo(
    current_admin: models.User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """
    Reset the application to a clean state for demo/testing.
    
    Deletes all email-derived data:
    - Contacts
    - Email threads
    - Email messages
    - Tasks
    - Embeddings (vector store)
    
    Preserves:
    - User accounts
    
    **Admin access required.**
    """
    db = SessionLocal()
    try:
        # Count before deletion for reporting
        contacts_count = db.query(models.Contact).count()
        threads_count = db.query(models.EmailThread).count()
        messages_count = db.query(models.EmailMessage).count()
        tasks_count = db.query(models.Task).count()
        
        # Delete email-derived data
        # Order matters due to foreign keys
        db.query(models.Task).delete()
        db.query(models.EmailMessage).delete()
        db.query(models.EmailThread).delete()
        db.query(models.Contact).delete()
        
        # Clear vector store (pass the existing db session)
        embeddings_count = db.query(models.Embedding).count()
        db.query(models.Embedding).delete()
        
        db.commit()
        
        # Clear ADK Memory (in-memory, so we'll note it in the response)
        # Note: InMemoryMemoryService doesn't have a clear method, but
        # since it's in-memory, it will reset on server restart
        memory_note = "ADK Memory will be cleared on server restart (in-memory store)"
        
        return {
            "success": True,
            "message": "Demo reset completed successfully",
            "deleted": {
                "contacts": contacts_count,
                "email_threads": threads_count,
                "email_messages": messages_count,
                "tasks": tasks_count,
                "embeddings": embeddings_count
            },
            "preserved": {
                "users": db.query(models.User).count()
            },
            "note": memory_note
        }
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
