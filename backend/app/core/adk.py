from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService

# Initialize shared services
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

class Message:
    def __init__(self, role, text):
        self.role = role
        self.parts = [{"text": text}]
