from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import models
from app.core.database import SessionLocal

def get_db_session():
    return SessionLocal()

def get_contact_emails_tool(contact_id: int) -> List[Dict[str, Any]]:
    """
    Fetches all emails exchanged with a contact.
    """
    db = get_db_session()
    try:
        contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
        if not contact:
            return []
            
        emails = []
        # Iterate through threads to get messages
        for thread in contact.email_threads:
            for msg in thread.messages:
                emails.append({
                    "from": msg.from_email,
                    "to": msg.to_emails,
                    "subject": msg.subject,
                    "body_text": msg.body_text,
                    "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
                    "direction": msg.direction
                })
        return emails
    finally:
        db.close()

def update_contact_profile_tool(contact_id: int, summary: str, preferences: Dict[str, Any]):
    """
    Updates the contact's profile summary and preferences.
    """
    db = get_db_session()
    try:
        contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
        if contact:
            contact.profile_summary = summary
            contact.preferences = preferences
            db.add(contact)
            db.commit()
    finally:
        db.close()

def update_contact_pipeline_stage_tool(contact_id: int, stage: str):
    """
    Updates the contact's pipeline stage.
    """
    db = get_db_session()
    try:
        contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
        if contact:
            # Validate stage against enum
            if stage in models.PipelineStage.__members__:
                contact.pipeline_stage = stage
                db.add(contact)
                db.commit()
            else:
                print(f"Invalid stage: {stage}")
    finally:
        db.close()
