from app.tools import task_tools
from app.models import models
from app.core.database import SessionLocal
from app.core.config import settings
from app.core.adk import session_service, memory_service, Message
import google.generativeai as genai
from google.adk import Agent
from google.adk.runners import Runner
from google.adk.tools import load_memory
import os
import json
import time
from datetime import datetime, timedelta, timezone
# Import the new ADK-compliant agent class
from agents.RealEstateCopilot.task_agenda import TaskAgendaAgent as ADKTaskAgendaAgent

APP_NAME = "RealEstateCopilot"

class TaskAgendaAgent:
    def __init__(self):
        self.model_name = settings.MODEL_NAME
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # Use the new ADK-compliant agent class
        self.agent = ADKTaskAgendaAgent()

    def run(self, agent_user_id: int):
        """
        Runs task analysis for all contacts with email threads.
        Now processes one contact at a time to enable memory retrieval.
        """
        print(f"Running task agent for agent {agent_user_id}")
        db = SessionLocal()
        try:
            # Get all threads for this agent
            threads = db.query(models.EmailThread).join(models.Contact).filter(
                models.Contact.agent_id == agent_user_id
            ).all()
            
            # Group threads by contact
            contact_threads_map = {}
            for thread in threads:
                contact_id = thread.contact_id
                if contact_id not in contact_threads_map:
                    contact_threads_map[contact_id] = []
                contact_threads_map[contact_id].append(thread)
            
            total_contacts = len(contact_threads_map)
            print(f"Found {total_contacts} contacts with email threads to analyze.")
            
            # Process each contact individually (enables memory retrieval)
            for idx, (contact_id, contact_threads) in enumerate(contact_threads_map.items(), 1):
                contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
                if not contact:
                    continue
                
                print(f"Processing contact {idx}/{total_contacts}: {contact.email}...")
                
                self._process_contact(contact, contact_threads, agent_user_id, db)
                
                # Rate limit between contacts
                if idx < total_contacts:
                    time.sleep(5)
        
        finally:
            db.close()

    def _process_contact(self, contact, threads, agent_user_id, db):
        """
        Process a single contact's threads with memory-aware analysis.
        """
        try:
            # Build email history for this contact
            thread_data = []
            for thread in threads:
                messages = db.query(models.EmailMessage).filter(
                    models.EmailMessage.thread_id == thread.id
                ).order_by(models.EmailMessage.sent_at).all()
                
                thread_info = {
                    "thread_id": thread.id,
                    "subject": thread.subject,
                    "emails": []
                }
                
                for msg in messages:
                    thread_info["emails"].append({
                        "from": msg.from_email or "Unknown",
                        "direction": msg.direction if msg.direction else "UNKNOWN",
                        "subject": msg.subject,
                        "body": msg.body_text[:500] if msg.body_text else "",  # Truncate for brevity
                        "sent_at": str(msg.sent_at)
                    })
                
                thread_data.append(thread_info)
            
            # Build prompt with contact identifier
            contact_context = f"""Contact Information:
Name: {contact.name or 'Unknown'}
Email: {contact.email}

IMPORTANT: Before analyzing, use load_memory tool to search for any existing memories about "{contact.email}" or "{contact.name or contact.email}".
The memories may provide valuable context about this contact's journey, preferences, and history.

Email Thread History:
{json.dumps(thread_data, indent=2)}"""

            # Fetch existing tasks for this contact
            existing_tasks = db.query(models.Task).filter(
                models.Task.contact_id == contact.id,
                models.Task.status != models.TaskStatus.CANCELED
            ).all()
            
            if existing_tasks:
                tasks_json = json.dumps([{
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "description": t.detailed_description
                } for t in existing_tasks], indent=2)
                contact_context += f"\n\nExisting Tasks (Update status to DONE if completed):\n{tasks_json}\n"

            contact_context += "\nBased on ALL available information (email history + any retrieved memories + existing tasks), determine the complete current task list for this contact."
            
            # Create runner for this analysis
            runner = Runner(
                agent=self.agent,
                app_name=APP_NAME,
                session_service=session_service,
                memory_service=memory_service
            )
            
            # Run analysis (agent can call load_memory)
            session_id = f"task-analysis-{contact.id}-{int(time.time())}"
            
            # Create the session explicitly (async service called from sync context)
            try:
                import asyncio
                async def create_session():
                    await session_service.create_session(app_name=APP_NAME, user_id=str(agent_user_id), session_id=session_id)
                
                asyncio.run(create_session())
            except Exception as e:
                print(f"    Error creating session {session_id}: {e}")
                return

            response_text = ""
            
            print(f"    Running ADK agent for contact {contact.email}...")
            event_count = 0
            
            for event in runner.run(
                user_id=str(agent_user_id),
                session_id=session_id,
                new_message=Message("user", contact_context)
            ):
                event_count += 1
                print(f"    Event {event_count}: {type(event).__name__}")
                # Debug event structure
                try:
                    print(f"    Event vars: {vars(event)}")
                except:
                    print(f"    Event dir: {dir(event)}")
                
                # Extract text from event
                if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
                elif hasattr(event, 'text') and event.text:
                    response_text = event.text
                elif hasattr(event, 'output') and hasattr(event.output, 'text'):
                    response_text = event.output.text
                
                if response_text:
                    print(f"    Got text response: {response_text[:100]}...")
                    print(f"    Got output.text response: {response_text[:100]}...")
            
            print(f"    Total events: {event_count}")
            print(f"    Final response length: {len(response_text)} characters")
            
            if not response_text:
                print(f"  No response from agent for contact {contact.email}")
                return
            
            # Parse tasks from response
            print(f"    Parsing tasks from response...")
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            print(f"    Cleaned response: {response_text[:200]}...")
            
            try:
                tasks = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"  JSON decode error for contact {contact.email}: {e}")
                print(f"  Response was: {response_text}")
                return
            
            if not isinstance(tasks, list):
                print(f"  Invalid response format for contact {contact.email}")
                return
            
            # Delete existing tasks for this contact
            db.query(models.Task).filter(models.Task.contact_id == contact.id).delete()
            
            # Create new tasks
            tasks_created = 0
            for task_data in tasks:
                task_type_str = task_data.get("task_type")
                if not task_type_str:
                    continue
                
                try:
                    task_type = models.TaskType[task_type_str]
                except KeyError:
                    print(f"  Unknown task type: {task_type_str}")
                    continue
                
                priority_str = task_data.get("priority", "MEDIUM")
                try:
                    priority = models.TaskPriority[priority_str]
                except KeyError:
                    priority = models.TaskPriority.MEDIUM
                
                due_in_days = task_data.get("due_in_days", 7)
                due_date = datetime.now(timezone.utc) + timedelta(days=due_in_days)
                
                task = models.Task(
                    agent_id=agent_user_id,
                    contact_id=contact.id,
                    task_type=task_type,
                    title=task_data.get("title", "Untitled Task"),
                    detailed_description=task_data.get("description", ""),
                    priority=priority,
                    status=models.TaskStatus.OPEN,
                    due_date=due_date,
                    source_thread_id=threads[0].id if threads else None
                )
                db.add(task)
                tasks_created += 1
                print(f"    Created task: {task.title} (Priority: {priority_str}, Due: {due_in_days} days)")
            
            db.commit()
            print(f"  Created {tasks_created} task(s) for {contact.email}")
        
        except Exception as e:
            print(f"  Error processing contact {contact.email}: {e}")
            import traceback
            traceback.print_exc()
