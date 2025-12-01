from typing import Dict, Any, List
from app.tools import chat_tools
from app.models import models
from app.core.config import settings
from app.core.database import SessionLocal
import google.generativeai as genai
import json

APP_NAME = "RealEstateCopilot"

from typing import Dict, Any, List, Optional
from app.tools import chat_tools
from app.models import models
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.adk import session_service, memory_service, Message
from google.adk import Agent, Runner
import logging

APP_NAME = "RealEstateCopilot"
logger = logging.getLogger(__name__)

class CoachChatAgent:
    def __init__(self):
        self.model_name = settings.MODEL_NAME

    async def run(self, agent_user_id: int, message: str, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Processes a user message using ADK Agent and Runner.
        """
        print(f"Chat Agent received: {message} (User: {agent_user_id})")
        
        try:
            # 1. Define tools with agent_user_id injection
            def search_contacts(query: str):
                """Searches contacts by name or email."""
                return chat_tools.search_contacts_tool(query, agent_user_id)

            def search_tasks(query: str):
                """Searches tasks by title."""
                return chat_tools.search_tasks_tool(query, agent_user_id)
            
            def get_contact_profile(contact_id: int):
                """Gets detailed profile for a specific contact ID."""
                return chat_tools.get_contact_profile_tool(contact_id)
            
            def search_emails(query: str):
                """Semantic search over email history."""
                return chat_tools.vector_search_emails_tool(query, agent_user_id)
            
            def count_contacts():
                """Counts total contacts."""
                db = SessionLocal()
                try:
                    return db.query(models.Contact).filter(models.Contact.agent_id == agent_user_id).count()
                finally:
                    db.close()

            def count_tasks():
                """Counts total tasks."""
                db = SessionLocal()
                try:
                    return db.query(models.Task).filter(models.Task.agent_id == agent_user_id).count()
                finally:
                    db.close()

            # 2. Create ADK Agent with injected tools
            # Import the ADK-compliant agent class
            from agents.RealEstateCopilot.chat_assistant import ChatAssistant
            
            agent = ChatAssistant(tools=[search_contacts, search_tasks, get_contact_profile, search_emails, count_contacts, count_tasks])

            # 3. Create Session (if needed)
            # Ensure session exists for this user/chat
            # Use a unique session ID for the chat if provided, or generate one
            # The frontend passes 'session_id', we should use it.
            # We prefix it to avoid collision with other session types
            full_session_id = f"chat-{session_id}"
            
            print(f"DEBUG: ChatAgent session_id={session_id}, full_session_id={full_session_id}")
            
            try:
                # Check/Create session
                existing = await session_service.get_session(app_name=APP_NAME, user_id=str(agent_user_id), session_id=full_session_id)
                if not existing:
                    raise Exception("Session not found")
                print(f"DEBUG: Session exists")
            except Exception as e:
                print(f"DEBUG: Creating session: {e}")
                await session_service.create_session(app_name=APP_NAME, user_id=str(agent_user_id), session_id=full_session_id)
                # Verify creation
                created = await session_service.get_session(app_name=APP_NAME, user_id=str(agent_user_id), session_id=full_session_id)
                if not created:
                    print(f"CRITICAL: Failed to create session {full_session_id}")
                else:
                    print(f"DEBUG: Session created successfully")

            # 4. Run Runner
            runner = Runner(
                agent=agent,
                app_name=APP_NAME,
                session_service=session_service,
                memory_service=memory_service
            )
            
            response_text = ""
            
            
            for event in runner.run(
                user_id=str(agent_user_id),
                session_id=full_session_id,
                new_message=Message("user", message)
            ):
                # Extract text from event
                if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
                elif hasattr(event, 'text') and event.text:
                    response_text = event.text
                elif hasattr(event, 'output') and hasattr(event.output, 'text'):
                    response_text = event.output.text
            
            if not response_text:
                response_text = "I processed your request but didn't have a text response."

            return {
                "reply": response_text,
                "structured": None
            }
                
        except Exception as e:
            print(f"Error in chat agent: {e}")
            import traceback
            traceback.print_exc()
            return {
                "reply": "I encountered an error while processing your request.",
                "structured": None
            }
