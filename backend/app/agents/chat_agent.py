from typing import Dict, Any, List
from app.tools import chat_tools
from app.models import models
from app.core.config import settings
from app.core.database import SessionLocal
import google.generativeai as genai
import json

class CoachChatAgent:
    def __init__(self):
        self.model_name = settings.MODEL_NAME
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)

    def _count_contacts(self, agent_user_id: int) -> str:
        """Count total contacts for the agent."""
        db = SessionLocal()
        try:
            count = db.query(models.Contact).filter(models.Contact.agent_id == agent_user_id).count()
            return f"You have {count} contact(s)."
        finally:
            db.close()

    def _search_contacts(self, query: str, agent_user_id: int) -> str:
        """Search contacts by name or email."""
        results = chat_tools.search_contacts_tool(query, agent_user_id)
        if not results:
            return "No contacts found."
        return "Contacts:\n" + "\n".join([f"- {r['name']} ({r['email']}) - Stage: {r['stage']}" for r in results])

    def _search_tasks(self, query: str, agent_user_id: int) -> str:
        """Search tasks by title."""
        results = chat_tools.search_tasks_tool(query, agent_user_id)
        if not results:
            return "No tasks found."
        return "Tasks:\n" + "\n".join([f"- {r['title']} - Status: {r['status']}, Due: {r['due_date']}" for r in results])
    
    def _count_tasks(self, agent_user_id: int) -> str:
        """Count total tasks for the agent."""
        db = SessionLocal()
        try:
            count = db.query(models.Task).filter(models.Task.agent_id == agent_user_id).count()
            return f"You have {count} task(s)."
        finally:
            db.close()

    def _get_contact_profile(self, contact_id: int) -> str:
        """Get detailed contact profile."""
        result = chat_tools.get_contact_profile_tool(contact_id)
        if not result:
            return "Contact not found."
        return f"Contact: {result['name']}\nEmail: {result['email']}\nStage: {result['stage']}\nSummary: {result['summary']}\nPreferences: {result['preferences']}"

    def _get_user_info(self, agent_user_id: int) -> str:
        """Get information about the logged-in user."""
        db = SessionLocal()
        try:
            user = db.query(models.User).filter(models.User.id == agent_user_id).first()
            if not user:
                return "User information not available."
            return f"Your name is {user.name} and your email is {user.email}."
        finally:
            db.close()

    async def run(self, agent_user_id: int, message: str, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Processes a user message.
        """
        print(f"Chat Agent received: {message} (User: {agent_user_id})")
        
        try:
            # Prepare context with available data
            contacts_count = db_count = 0
            tasks_count = 0
            user_info = ""
            
            db = SessionLocal()
            try:
                contacts_count = db.query(models.Contact).filter(models.Contact.agent_id == agent_user_id).count()
                tasks_count = db.query(models.Task).filter(models.Task.agent_id == agent_user_id).count()
                user = db.query(models.User).filter(models.User.id == agent_user_id).first()
                if user:
                    user_info = f"User: {user.name} ({user.email})"
            finally:
                db.close()

            # Build instruction with context
            instruction = f"""You are a helpful Real Estate Coach and Assistant.

Current Context:
- {user_info}
- Total Contacts: {contacts_count}
- Total Tasks: {tasks_count}

When the user asks questions:
- If they ask "how many contacts", say "You have {contacts_count} contact(s)."
- If they ask "how many tasks", say "You have {tasks_count} task(s)."
- If they ask "what's my name", use the user information above
- For specific contact/task searches, say you'd need to search the database
- Be conversational and helpful

User Question: {message}

Provide a helpful, direct answer based on the context above."""

            # Call the model
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(instruction)
            response_text = response.text.strip()
            
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
