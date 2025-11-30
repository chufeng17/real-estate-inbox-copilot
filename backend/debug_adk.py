import sys
import os
from google.adk import Agent

def inspect_adk():
    print("Inspecting google.adk.Agent...")
    try:
        agent = Agent(model="gemini-2.0-flash-exp", instruction="test", name="test_agent")
        print(f"Agent type: {type(agent)}")
        print(f"Agent dir: {dir(agent)}")
    except Exception as e:
        print(f"Error initializing agent: {e}")

if __name__ == "__main__":
    inspect_adk()
