import json
from app.tools import ingestion_tools
from app.models import models
from app.core.database import SessionLocal
from app.core.config import settings

class InboxIngestionAgent:
    def __init__(self):
        pass

    def load_emails_from_json(self):
        """Load emails from JSON file (for Kaggle offline mode)."""
        dataset_path = settings.DATASET_PATH
        print(f"Loading emails from: {dataset_path}")
        
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        return data.get("emails", [])

    def run(self, agent_user_id: int):
        """
        Orchestrates the ingestion process.
        Uses ingestion_tools which now leverage Google Gemini for embeddings.
        """
        print(f"Starting ingestion for agent {agent_user_id}")
        
        # 1. Load emails
        # emails = ingestion_tools.load_email_dataset_tool() # Original line
        emails = self.load_emails_from_json() # Using the new method
        print(f"Loaded {len(emails)} emails")
        
        # Get the agent user email to filter/match
        db = SessionLocal()
        try:
            agent_user = db.query(models.User).filter(models.User.id == agent_user_id).first()
            if not agent_user:
                print("Agent user not found")
                return
            agent_email_address = agent_user.email
        finally:
            db.close()

        for email_data in emails:
            # Only process if this email belongs to the current agent
            if email_data.get("agent_email") != agent_email_address:
                continue

            # 2. Upsert Contact
            contact_email = email_data.get("contact_email")
            # Heuristic: Name is usually not in the email object directly in this simple schema, 
            # but we can try to extract or just use email as name for now.
            # In a real system, we'd parse "Name <email>" format.
            contact_name = contact_email.split("@")[0].replace(".", " ").title()
            
            contact_id = ingestion_tools.upsert_contact_tool(
                {"email": contact_email, "name": contact_name}, 
                agent_user_id
            )
            
            # 3. Upsert Thread
            thread_data = {
                "thread_id": email_data.get("thread_id"),
                "subject": email_data.get("subject"),
                "last_message_at": email_data.get("sent_at") # This logic is simplified; usually we check max
            }
            thread_pk = ingestion_tools.upsert_thread_tool(thread_data, contact_id, agent_user_id)
            
            # 4. Upsert Message
            message_pk = ingestion_tools.upsert_message_tool(email_data, thread_pk)
            
            # 5. Vector Store Upsert
            # Embed the body text
            ingestion_tools.vector_store_upsert_tool(
                entity_type="email_message",
                entity_id=message_pk,
                text=email_data.get("body_text"),
                metadata={"subject": email_data.get("subject"), "contact_id": contact_id}
            )
            
        print("Ingestion complete")
