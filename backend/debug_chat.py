import sys
import os
from app.agents.chat_agent import CoachChatAgent
from app.schemas.schemas import ChatRequest

print("Import successful")

try:
    agent = CoachChatAgent()
    print("Agent initialized")
    # We need to manually call runner.run here because agent.run is wrapping it but we want to debug the generator if agent.run fails
    # But wait, agent.run is what we want to test.
    # Let's update agent.run first to use new_message and return a generator or handle it.
    
    # For now, let's just try to call the agent.run and see if it works with the fix I'm about to apply to the agent file.
    # But I haven't applied the fix to the agent file yet.
    
    from app.core.adk import session_service
    import asyncio

    class Message:
        def __init__(self, role, text):
            self.role = role
            self.parts = [{"text": text}]

    print("Creating session...")
    # We need to run async code to create session
    async def setup_session():
        await session_service.create_session(app_name="RealEstateCopilot", user_id="1", session_id="test_session")
    
    asyncio.run(setup_session())

    print("Calling runner directly...")
    msg = Message("user", "Hello")
    for event in agent.runner.run(user_id="1", session_id="test_session", new_message=msg):
        print(f"Event: {event}")
        print(f"Event Type: {type(event)}")
        if hasattr(event, 'text'):
            print(f"Text: {event.text}")
        if hasattr(event, 'output'):
            print(f"Output: {event.output}")
            if hasattr(event.output, 'text'):
                print(f"Output Text: {event.output.text}")
except Exception as e:
    print(f"Error: {e}")
