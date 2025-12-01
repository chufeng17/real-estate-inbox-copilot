from google.adk import Agent
from app.core.config import settings

class ContactMemoryRecorder(Agent):
    def __init__(self):
        super().__init__(
            model=settings.MODEL_NAME,
            name="ContactMemoryRecorder",
            instruction="You are recording contact narratives for future reference."
        )
