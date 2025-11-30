import sys
import os
import json
from datetime import datetime

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.agents.ingestion_agent import InboxIngestionAgent
from app.agents.classifier_agent import LeadClientClassifierAgent
from app.agents.task_agent import TaskAgendaAgent
from app.core.database import SessionLocal
from app.models import models

def debug_full_pipeline():
    print("=== Starting Full Pipeline Debug ===")
    db = SessionLocal()
    try:
        # 1. Check User
        user = db.query(models.User).first()
        if not user:
            print("ERROR: No user found. Please register a user first.")
            return
        
        print(f"User found: {user.email} (ID: {user.id})")
        
        # 2. Run Ingestion
        print("\n--- Running Ingestion Agent ---")
        ingestion_agent = InboxIngestionAgent()
        ingestion_agent.run(user.id)
        
        # Verify Ingestion
        thread_count = db.query(models.EmailThread).filter(models.EmailThread.agent_id == user.id).count()
        message_count = db.query(models.EmailMessage).join(models.EmailThread).filter(models.EmailThread.agent_id == user.id).count()
        print(f"Ingestion Result: {thread_count} threads, {message_count} messages.")
        
        if thread_count == 0:
            print("WARNING: No threads ingested. Aborting pipeline.")
            return

        # 3. Run Classifier
        print("\n--- Running Classifier Agent ---")
        classifier_agent = LeadClientClassifierAgent()
        classifier_agent.run(user.id)
        
        # Verify Classification
        contacts = db.query(models.Contact).filter(models.Contact.agent_id == user.id).all()
        print(f"Contacts processed: {len(contacts)}")
        for c in contacts:
            print(f"  - {c.name} ({c.email}): {c.pipeline_stage}")
            
        # 4. Run Task Agent
        print("\n--- Running Task Agent ---")
        task_agent = TaskAgendaAgent()
        task_agent.run(user.id)
        
        # Verify Tasks
        tasks = db.query(models.Task).filter(models.Task.agent_id == user.id).all()
        print(f"Tasks created: {len(tasks)}")
        for t in tasks:
            print(f"  - [{t.status}] {t.title} (Type: {t.task_type})")

        print("\n=== Pipeline Complete ===")

    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_full_pipeline()
