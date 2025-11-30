from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import models
from app.services.gmail_service import GmailService
from app.services.vector_store import VectorStore
from app.core.database import SessionLocal
from datetime import datetime, timezone

# Helper to get DB session
def get_db_session():
    return SessionLocal()

def load_email_dataset_tool() -> List[Dict[str, Any]]:
    """
    Loads the email dataset from the configured JSON file.
    """
    service = GmailService()
    return service.list_messages()

def upsert_contact_tool(contact_data: Dict[str, Any], agent_user_id: int) -> int:
    """
    Ensures a contact exists for the given email and agent.
    Returns the contact ID.
    """
    db = get_db_session()
    try:
        email = contact_data.get("email")
        name = contact_data.get("name")
        
        # Simple logic: check if contact exists for this agent by email
        contact = db.query(models.Contact).filter(
            models.Contact.email == email,
            models.Contact.agent_id == agent_user_id
        ).first()
        
        if not contact:
            contact = models.Contact(
                email=email,
                name=name,
                agent_id=agent_user_id,
                pipeline_stage=models.PipelineStage.NEW_LEAD
            )
            db.add(contact)
            db.commit()
            db.refresh(contact)
        
        return contact.id
    finally:
        db.close()

def upsert_thread_tool(thread_data: Dict[str, Any], contact_id: int, agent_user_id: int) -> int:
    """
    Creates or updates an email thread.
    Returns the thread ID (DB PK).
    """
    db = get_db_session()
    try:
        thread_id_str = thread_data.get("thread_id")
        subject = thread_data.get("subject")
        last_message_at_str = thread_data.get("last_message_at")
        
        # Parse date if string
        if isinstance(last_message_at_str, str):
            last_message_at = datetime.fromisoformat(last_message_at_str.replace("Z", "+00:00"))
        else:
            last_message_at = last_message_at_str

        # Ensure last_message_at is timezone-aware (assume UTC if naive)
        if last_message_at.tzinfo is None:
            last_message_at = last_message_at.replace(tzinfo=timezone.utc)

        thread = db.query(models.EmailThread).filter(
            models.EmailThread.thread_id == thread_id_str
        ).first()
        
        if not thread:
            thread = models.EmailThread(
                thread_id=thread_id_str,
                contact_id=contact_id,
                agent_id=agent_user_id,
                subject=subject,
                last_message_at=last_message_at
            )
            db.add(thread)
        else:
            # Update last message time if newer
            current_thread_time = thread.last_message_at
            # Ensure current_thread_time is timezone-aware
            if current_thread_time and current_thread_time.tzinfo is None:
                current_thread_time = current_thread_time.replace(tzinfo=timezone.utc)

            if current_thread_time is None or last_message_at > current_thread_time:
                thread.last_message_at = last_message_at
                thread.subject = subject # Update subject in case it changed
            
        db.commit()
        db.refresh(thread)
        return thread.id
    finally:
        db.close()

def upsert_message_tool(message_data: Dict[str, Any], thread_pk: int) -> int:
    """
    Creates an email message record.
    Returns the message ID (DB PK).
    """
    db = get_db_session()
    try:
        message_id_str = message_data.get("message_id")
        
        message = db.query(models.EmailMessage).filter(
            models.EmailMessage.message_id == message_id_str
        ).first()
        
        if not message:
            sent_at_str = message_data.get("sent_at")
            if isinstance(sent_at_str, str):
                sent_at = datetime.fromisoformat(sent_at_str.replace("Z", "+00:00"))
            else:
                sent_at = sent_at_str
            
            # Ensure sent_at is timezone-aware
            if sent_at.tzinfo is None:
                sent_at = sent_at.replace(tzinfo=timezone.utc)

            message = models.EmailMessage(
                thread_id=thread_pk,
                message_id=message_id_str,
                from_email=message_data.get("from"),
                to_emails=message_data.get("to"),
                cc_emails=message_data.get("cc"),
                direction=message_data.get("direction"),
                subject=message_data.get("subject"),
                body_text=message_data.get("body_text"),
                labels=message_data.get("labels"),
                sent_at=sent_at
            )
            db.add(message)
            db.commit()
            db.refresh(message)
        
        return message.id
    finally:
        db.close()

def vector_store_upsert_tool(entity_type: str, entity_id: int, text: str, metadata: Dict[str, Any] = None):
    """
    Upserts an embedding for the given text.
    """
    db = get_db_session()
    try:
        store = VectorStore(db)
        store.upsert_embedding(entity_type, entity_id, text, metadata)
    finally:
        db.close()
