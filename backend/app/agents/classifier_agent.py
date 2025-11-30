from app.tools import classifier_tools
from app.models import models
from app.core.database import SessionLocal
from app.core.config import settings
import google.generativeai as genai
import os
import json
import time

class LeadClientClassifierAgent:
    def __init__(self):
        self.model_name = settings.MODEL_NAME
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(self.model_name)
        self.batch_size = 5

    def run(self, agent_user_id: int):
        """
        Iterates through contacts and updates their profiles/stages in batches.
        """
        print(f"Running classifier for agent {agent_user_id}")
        db = SessionLocal()
        try:
            contacts = db.query(models.Contact).filter(models.Contact.agent_id == agent_user_id).all()
            
            # Filter contacts that have emails
            contacts_with_emails = []
            contact_data_map = {} # Map ID to (contact_obj, context_str)

            for contact in contacts:
                emails = classifier_tools.get_contact_emails_tool(contact.id)
                if not emails:
                    continue
                
                # Prepare Context
                email_texts = []
                for e in emails:
                    direction = "Agent to Client" if e["direction"] == "OUTGOING" else "Client to Agent"
                    email_texts.append(f"[{direction}] Subject: {e['subject']}\nBody: {e['body_text']}")
                
                context = "\n\n".join(email_texts)
                contacts_with_emails.append(contact)
                contact_data_map[contact.id] = context

            # Process in batches
            total_contacts = len(contacts_with_emails)
            print(f"Found {total_contacts} contacts with emails to classify.")

            for i in range(0, total_contacts, self.batch_size):
                batch = contacts_with_emails[i : i + self.batch_size]
                print(f"Processing batch {i//self.batch_size + 1} ({len(batch)} contacts)...")
                
                self._process_batch(batch, contact_data_map)
                
                # Rate limit handling between batches
                if i + self.batch_size < total_contacts:
                    time.sleep(5) 

        finally:
            db.close()

    def _process_batch(self, batch, contact_data_map):
        # Construct Batch Prompt
        batch_input = []
        for contact in batch:
            batch_input.append({
                "contact_id": contact.id,
                "contact_name": contact.name or contact.email,
                "email_history": contact_data_map[contact.id]
            })
        
        instruction = f"""
        You are a real estate assistant. Analyze the email history for the following list of contacts.
        For EACH contact, determine their pipeline stage, summary, and preferences.

        Pipeline Stages:
        - NEW_LEAD
        - CONTACTED
        - QUALIFIED
        - SHOWING_SCHEDULED
        - ACTIVE_SEARCH
        - OFFER_MADE
        - UNDER_CONTRACT
        - CLOSED
        - LOST
        - NURTURE

        Input Data:
        {json.dumps(batch_input, indent=2)}

        Output strictly a JSON LIST of objects, where each object corresponds to a contact:
        [
            {{
                "contact_id": 123,
                "stage": "ONE_OF_THE_STAGES",
                "summary": "Brief summary...",
                "preferences": {{ ... }}
            }},
            ...
        ]
        """

        try:
            response = self.model.generate_content(instruction)
            response_text = response.text.replace("```json", "").replace("```", "").strip()
            results = json.loads(response_text)
            
            if not isinstance(results, list):
                print("Error: LLM did not return a list.")
                return

            for result in results:
                contact_id = result.get("contact_id")
                if not contact_id: 
                    continue
                
                stage_str = result.get("stage", "NEW_LEAD")
                new_stage = getattr(models.PipelineStage, stage_str, models.PipelineStage.NEW_LEAD)
                summary = result.get("summary", "")
                preferences = result.get("preferences", {})
                
                classifier_tools.update_contact_pipeline_stage_tool(contact_id, new_stage)
                classifier_tools.update_contact_profile_tool(contact_id, summary, preferences)
                print(f"Updated contact {contact_id} to {new_stage}")

        except Exception as e:
            print(f"Error processing batch: {e}")
