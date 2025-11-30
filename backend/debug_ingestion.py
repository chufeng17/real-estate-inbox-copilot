import sys
import os
import json

from app.agents.ingestion_agent import InboxIngestionAgent
from app.core.database import SessionLocal
from app.models import models

def debug_ingestion():
    db = SessionLocal()
    try:
        # Get the first user
        user = db.query(models.User).first()
        if not user:
            print("No user found! Please register a user first.")
            return

        print(f"Running ingestion for user: {user.email} (ID: {user.id})")
        
        # Check dataset agent email
        dataset_path = "../data/sample_emails.json"
        if os.path.exists(dataset_path):
            with open(dataset_path, "r") as f:
                data = json.load(f)
                if data["emails"]:
                    print(f"Dataset agent email: {data['emails'][0].get('agent_email')}")
        else:
            print(f"Dataset not found at {dataset_path}")
        
        agent = InboxIngestionAgent()
        agent.run(user.id)
        print("Ingestion finished.")
        
    except Exception as e:
        print(f"Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_ingestion()
