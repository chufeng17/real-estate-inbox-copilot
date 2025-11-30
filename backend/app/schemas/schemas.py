from typing import List, Optional, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.models import UserRole, PipelineStage, TaskType, TaskPriority, TaskStatus, EmailDirection

# Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None

# User
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    role: UserRole = UserRole.AGENT

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Contact
class ContactBase(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    pipeline_stage: PipelineStage = PipelineStage.NEW_LEAD
    profile_summary: Optional[str] = None
    preferences: Optional[Any] = None
    notes: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(ContactBase):
    pass

class Contact(ContactBase):
    id: int
    agent_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Task
class TaskBase(BaseModel):
    task_type: TaskType
    title: str
    detailed_description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.OPEN
    due_date: Optional[datetime] = None
    source_thread_id: Optional[int] = None
    source_message_id: Optional[int] = None

class TaskCreate(TaskBase):
    contact_id: Optional[int] = None

class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    priority: Optional[TaskPriority] = None
    notes: Optional[str] = None # Not in DB yet, but useful for API

class Task(TaskBase):
    id: int
    agent_id: int
    contact_id: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    overdue: bool = False # Computed field

    class Config:
        from_attributes = True

# Email
class EmailMessageBase(BaseModel):
    message_id: str
    from_email: str
    to_emails: Optional[List[str]] = []
    cc_emails: Optional[List[str]] = []
    direction: EmailDirection
    subject: str
    body_text: str
    labels: Optional[List[str]] = []
    sent_at: datetime

class EmailMessage(EmailMessageBase):
    id: int
    thread_id: int

    class Config:
        from_attributes = True

class EmailThreadBase(BaseModel):
    thread_id: str
    subject: str
    last_message_at: datetime

class EmailThread(EmailThreadBase):
    id: int
    contact_id: Optional[int] = None
    agent_id: int
    messages: List[EmailMessage] = []

    class Config:
        from_attributes = True

# Chat
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    reply: str
    structured: Optional[Any] = None
