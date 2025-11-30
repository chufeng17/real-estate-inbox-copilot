from app.tools import task_tools
from app.models import models
from app.core.database import SessionLocal
from app.core.config import settings
import google.generativeai as genai
import os
import json
import time
from datetime import datetime, timedelta, timezone

class TaskAgendaAgent:
    def __init__(self):
        self.model_name = settings.MODEL_NAME
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(self.model_name)
        self.batch_size = 5

    def run(self, agent_user_id: int):
        """
        Analyzes threads to create tasks in batches.
        """
        print(f"Running task agent for agent {agent_user_id}")
        db = SessionLocal()
        try:
            threads = db.query(models.EmailThread).filter(models.EmailThread.agent_id == agent_user_id).all()
            
            threads_with_emails = []
            thread_data_map = {} # ID -> (thread_obj, context_str, last_email_id)

            for thread in threads:
                emails = task_tools.list_emails_for_thread_tool(thread.id)
                if not emails:
                    continue
                
                emails.sort(key=lambda x: x["sent_at"])
                email_texts = []
                for e in emails:
                    direction = "Agent to Client" if e["direction"] == "OUTGOING" else "Client to Agent"
                    email_texts.append(f"[{direction}] Subject: {e['subject']}\nBody: {e['body_text']}")
                
                context = "\n\n".join(email_texts)
                threads_with_emails.append(thread)
                thread_data_map[thread.id] = {
                    "context": context,
                    "last_email_id": emails[-1]["id"],
                    "contact_id": thread.contact_id
                }

            # Process in batches
            total_threads = len(threads_with_emails)
            print(f"Found {total_threads} threads to analyze.")

            for i in range(0, total_threads, self.batch_size):
                batch = threads_with_emails[i : i + self.batch_size]
                print(f"Processing batch {i//self.batch_size + 1} ({len(batch)} threads)...")
                
                self._process_batch(batch, thread_data_map, agent_user_id)
                
                if i + self.batch_size < total_threads:
                    time.sleep(5)

        finally:
            db.close()

    def _process_batch(self, batch, thread_data_map, agent_user_id):
        batch_input = []
        for thread in batch:
            batch_input.append({
                "thread_id": thread.id,
                "email_thread": thread_data_map[thread.id]["context"]
            })

        instruction = f"""
        You are a real estate assistant. Analyze the following email threads to identify actionable tasks.
        For EACH thread, return a task object if a task exists, or null if no task.

        Task Types:
        - SCHEDULE_SHOWING
        - REVIEW_OFFER
        - ANSWER_CLIENT_QUESTION
        - FOLLOW_UP

        Input Data:
        {json.dumps(batch_input, indent=2)}

        Output strictly a JSON LIST of objects:
        [
            {{
                "thread_id": 123,
                "task_type": "TYPE",
                "title": "Title",
                "description": "Desc",
                "priority": "HIGH/MEDIUM/LOW",
                "due_in_days": 1
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

            db = SessionLocal()
            try:
                tasks_created = 0
                for result in results:
                    thread_id = result.get("thread_id")
                    if not thread_id: continue
                    
                    task_type_str = result.get("task_type")
                    if not task_type_str: continue
                    
                    try:
                        task_type = models.TaskType[task_type_str]
                    except KeyError:
                        print(f"Unknown task type: {task_type_str}")
                        continue
                    
                    title = result.get("title", "Untitled Task")
                    description = result.get("description", "")
                    priority_str = result.get("priority", "MEDIUM")
                    due_in_days = result.get("due_in_days", 7)
                    
                    try:
                        priority = models.TaskPriority[priority_str]
                    except KeyError:
                        priority = models.TaskPriority.MEDIUM
                    
                    due_date = datetime.now(timezone.utc) + timedelta(days=due_in_days)
                    
                    thread = db.query(models.EmailThread).filter(models.EmailThread.id == thread_id).first()
                    contact_id = thread.contact_id if thread else None
                    
                    # Check existing
                    # The original code checked for existing tasks based on source_message_id.
                    # The new instruction removes source_message_id from task_data and doesn't explicitly
                    # include an existing check. Assuming the intent is to create a new task if LLM suggests one.
                    
                    # Create the task
                    task_data = {
                        "contact_id": contact_id,
                        "task_type": task_type,
                        "title": title,
                        "detailed_description": description,
                        "priority": priority,
                        "status": models.TaskStatus.OPEN,
                        "due_date": due_date,
                        "source_thread_id": thread_id
                    }
                    
                    task_id = task_tools.upsert_task_tool(task_data, agent_user_id)
                    tasks_created += 1
                    print(f"  Created task: {title} (ID: {task_id}, Priority: {priority_str}, Due: {due_in_days} days)")
                    
                print(f"Created {tasks_created} task(s) from batch")
            finally:
                db.close()

        except Exception as e:
            print(f"Error processing batch: {e}")
