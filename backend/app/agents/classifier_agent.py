from app.tools import classifier_tools
from app.models import models
from app.core.database import SessionLocal
from app.core.config import settings
from app.core.adk import session_service, memory_service, Message
import google.generativeai as genai
from google.adk import Agent
from google.adk.runners import Runner
import json
import time
import asyncio
# Import the new ADK-compliant agent class
from agents.RealEstateCopilot.memory_recorder import ContactMemoryRecorder

APP_NAME = "RealEstateCopilot"

class LeadClientClassifierAgent:
    def __init__(self):
        self.model_name = settings.MODEL_NAME
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(self.model_name)
        self.batch_size = 5
        
        # Use the new ADK-compliant agent class
        self.memory_agent = ContactMemoryRecorder()

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
                
                self._process_batch(batch, contact_data_map, agent_user_id)
                
                # Rate limit handling between batches
                if i + self.batch_size < total_contacts:
                    time.sleep(5) 

        finally:
            db.close()

    def _process_batch(self, batch, contact_data_map, agent_user_id):
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

            # Update DB with classifications
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
            
            # After DB update, create ADK memory sessions for each contact
            print("Creating contact memory sessions...")
            # Pass contact IDs instead of objects to avoid session issues
            contact_ids = [c.id for c in batch]
            asyncio.run(self._create_contact_memories(contact_ids, agent_user_id))

        except Exception as e:
            print(f"Error processing batch: {e}")
    
    async def _create_contact_memories(self, contact_ids, agent_user_id):
        """
        Create ADK memory sessions for each contact with their narrative.
        """
        db = SessionLocal()
        try:
            for contact_id in contact_ids:
                # Load contact from DB
                contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
                if not contact:
                    continue
                
                # Build contact narrative
                narrative = f"""Contact Profile Update:
Name: {contact.name or 'Unknown'}
Email: {contact.email}
Pipeline Stage: {contact.pipeline_stage if contact.pipeline_stage else 'NEW_LEAD'}
Profile Summary: {contact.profile_summary or 'No summary yet'}
Preferences: {json.dumps(contact.preferences) if contact.preferences else 'None recorded'}
Last Updated: {contact.updated_at}

This is a comprehensive profile of the contact based on their email communication history.
"""
                
                # Session ID based on contact email
                session_id = f"contact-{contact.email}"
                
                # Create session if it doesn't exist
                try:
                    # Try to get session first
                    existing_session = await session_service.get_session(app_name=APP_NAME, user_id=str(agent_user_id), session_id=session_id)
                    if not existing_session:
                        raise Exception("Session not found")
                except Exception:
                    print(f"Creating new memory session for {contact.email}")
                    # Create session explicitly
                    await session_service.create_session(app_name=APP_NAME, user_id=str(agent_user_id), session_id=session_id)
                    
                    # Verify creation
                    created_session = await session_service.get_session(app_name=APP_NAME, user_id=str(agent_user_id), session_id=session_id)
                    if not created_session:
                        print(f"CRITICAL ERROR: Failed to create session {session_id}")
                    else:
                        print(f"Session {session_id} created successfully")

                # DEBUG: Check if session exists (Direct access for debugging)
                print(f"DEBUG: Checking session existence for {session_id}")
                print(f"DEBUG: APP_NAME={APP_NAME}, user_id={agent_user_id}")
                print(f"DEBUG: session_service ID: {id(session_service)}")
                if APP_NAME in session_service.sessions:
                    if str(agent_user_id) in session_service.sessions[APP_NAME]:
                        sessions = session_service.sessions[APP_NAME][str(agent_user_id)]
                        print(f"DEBUG: Sessions for user: {list(sessions.keys())}")
                        if session_id in sessions:
                            print("DEBUG: Session FOUND in service!")
                        else:
                            print("DEBUG: Session NOT FOUND in service!")
                    else:
                        print(f"DEBUG: User {agent_user_id} NOT FOUND in app {APP_NAME}")
                else:
                    print(f"DEBUG: App {APP_NAME} NOT FOUND in service")

                # Create runner for this contact
                runner = Runner(
                    agent=self.memory_agent,
                    app_name=APP_NAME,
                    session_service=session_service,
                    memory_service=memory_service
                )
                
                # Run agent to store memory
                # We send the narrative as a user message
                print(f"Storing memory for contact: {contact.email}")
                for _ in runner.run(
                    user_id=str(agent_user_id),
                    session_id=session_id,
                    new_message=Message("user", narrative)
                ):
                    pass # Just consume the stream to ensure processing
                    
            print("Contact memory sessions created successfully.")
        except Exception as e:
            print(f"Error creating contact memories: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
