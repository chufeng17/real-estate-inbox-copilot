from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"

class PipelineStage(str, enum.Enum):
    NEW_LEAD = "NEW_LEAD"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    SHOWING_SCHEDULED = "SHOWING_SCHEDULED"
    ACTIVE_SEARCH = "ACTIVE_SEARCH"
    OFFER_MADE = "OFFER_MADE"
    UNDER_CONTRACT = "UNDER_CONTRACT"
    CLOSED = "CLOSED"
    LOST = "LOST"
    NURTURE = "NURTURE"

class TaskType(str, enum.Enum):
    FOLLOW_UP = "FOLLOW_UP"
    SEND_DOCUMENTS = "SEND_DOCUMENTS"
    SCHEDULE_SHOWING = "SCHEDULE_SHOWING"
    PREPARE_COMPARABLES = "PREPARE_COMPARABLES"
    SUBMIT_OFFER = "SUBMIT_OFFER"
    REVIEW_OFFER = "REVIEW_OFFER"
    CONTRACT_TASK = "CONTRACT_TASK"
    ANSWER_CLIENT_QUESTION = "ANSWER_CLIENT_QUESTION"
    REQUEST_INFORMATION = "REQUEST_INFORMATION"
    GENERAL_TODO = "GENERAL_TODO"

class TaskPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class TaskStatus(str, enum.Enum):
    OPEN = "OPEN"
    WAITING_ON_CLIENT = "WAITING_ON_CLIENT"
    DONE = "DONE"
    CANCELED = "CANCELED"

class EmailDirection(str, enum.Enum):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default=UserRole.AGENT) # Stored as string for simplicity
    name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contacts = relationship("Contact", back_populates="agent")
    tasks = relationship("Task", back_populates="agent")
    email_threads = relationship("EmailThread", back_populates="agent")

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=True)
    email = Column(String, index=True) # Unique per agent logic handled in code
    phone = Column(String, nullable=True)
    pipeline_stage = Column(String, default=PipelineStage.NEW_LEAD)
    profile_summary = Column(Text, nullable=True)
    preferences = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("User", back_populates="contacts")
    tasks = relationship("Task", back_populates="contact")
    email_threads = relationship("EmailThread", back_populates="contact")

class EmailThread(Base):
    __tablename__ = "email_threads"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True) # From dataset
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    agent_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String)
    last_message_at = Column(DateTime(timezone=True))

    contact = relationship("Contact", back_populates="email_threads")
    agent = relationship("User", back_populates="email_threads")
    messages = relationship("EmailMessage", back_populates="thread")
    tasks = relationship("Task", back_populates="source_thread")

class EmailMessage(Base):
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("email_threads.id"))
    message_id = Column(String, unique=True, index=True) # From dataset
    from_email = Column(String)
    to_emails = Column(JSON)
    cc_emails = Column(JSON)
    direction = Column(String) # INCOMING, OUTGOING
    subject = Column(String)
    body_text = Column(Text)
    labels = Column(JSON)
    sent_at = Column(DateTime(timezone=True))

    thread = relationship("EmailThread", back_populates="messages")
    tasks = relationship("Task", back_populates="source_message")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    task_type = Column(String) # TaskType enum
    title = Column(String)
    detailed_description = Column(Text, nullable=True)
    priority = Column(String, default=TaskPriority.MEDIUM)
    status = Column(String, default=TaskStatus.OPEN)
    due_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    source_thread_id = Column(Integer, ForeignKey("email_threads.id"), nullable=True)
    source_message_id = Column(Integer, ForeignKey("email_messages.id"), nullable=True)

    agent = relationship("User", back_populates="tasks")
    contact = relationship("Contact", back_populates="tasks")
    source_thread = relationship("EmailThread", back_populates="tasks")
    source_message = relationship("EmailMessage", back_populates="tasks")

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String) # email_message, contact, etc.
    entity_id = Column(Integer)
    embedding = Column(JSON) # Storing as JSON list of floats for simplicity in SQLite
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
