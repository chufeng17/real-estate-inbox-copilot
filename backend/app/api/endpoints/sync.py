from typing import Any
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.models import models
from app.agents.ingestion_agent import InboxIngestionAgent
from app.agents.classifier_agent import LeadClientClassifierAgent
from app.agents.task_agent import TaskAgendaAgent

router = APIRouter()

def run_ingestion_agent(user_id: int):
    print(f"Starting sync process for user {user_id}")
    
    # 1. Ingestion
    ingestion_agent = InboxIngestionAgent()
    ingestion_agent.run(user_id)
    
    # 2. Classification
    classifier_agent = LeadClientClassifierAgent()
    classifier_agent.run(user_id)
    
    # 3. Task Extraction
    task_agent = TaskAgendaAgent()
    task_agent.run(user_id)
    
    print(f"Sync process complete for user {user_id}")

@router.post("/emails")
def sync_emails(
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Trigger email ingestion from the sample dataset.
    """
    background_tasks.add_task(run_ingestion_agent, current_user.id)
    return {"message": "Email sync started in background"}
