from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import models
from app.core.database import SessionLocal
from app.services.vector_store import VectorStore

def get_db_session():
    return SessionLocal()

def search_contacts_tool(query: str, agent_user_id: int) -> List[Dict[str, Any]]:
    """
    Searches contacts by name or email.
    """
    db = get_db_session()
    try:
        contacts = db.query(models.Contact).filter(
            models.Contact.agent_id == agent_user_id,
            (models.Contact.name.ilike(f"%{query}%")) | (models.Contact.email.ilike(f"%{query}%"))
        ).all()
        
        return [{"id": c.id, "name": c.name, "email": c.email, "stage": c.pipeline_stage} for c in contacts]
    finally:
        db.close()

def search_tasks_tool(query: str, agent_user_id: int) -> List[Dict[str, Any]]:
    """
    Searches tasks by title.
    """
    db = get_db_session()
    try:
        tasks = db.query(models.Task).filter(
            models.Task.agent_id == agent_user_id,
            models.Task.title.ilike(f"%{query}%")
        ).all()
        
        return [{"id": t.id, "title": t.title, "status": t.status, "due_date": t.due_date} for t in tasks]
    finally:
        db.close()

def get_contact_profile_tool(contact_id: int) -> Dict[str, Any]:
    """
    Gets full profile for a contact.
    """
    db = get_db_session()
    try:
        contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
        if not contact:
            return None
        return {
            "name": contact.name,
            "email": contact.email,
            "summary": contact.profile_summary,
            "preferences": contact.preferences,
            "stage": contact.pipeline_stage
        }
    finally:
        db.close()

def vector_search_emails_tool(query: str, agent_user_id: int) -> List[Dict[str, Any]]:
    """
    Semantic search over emails.
    """
    db = get_db_session()
    try:
        store = VectorStore(db)
        # Note: In a real app we'd filter by agent_user_id in the vector store query
        # Here we just search and filter results if needed, or assume vector store handles it
        results = store.search(query, entity_type="email_message")
        return results
    finally:
        db.close()
