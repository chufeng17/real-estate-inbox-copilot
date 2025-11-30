import sys
import os

# Try to import requested classes
try:
    from google.adk import Agent
    import inspect
    print("Found Agent")
    print(f"Agent signature: {inspect.signature(Agent)}")
except ImportError as e:
    print(f"Failed to import Agent: {e}")

try:
    from google.adk.memory import InMemoryMemoryService
    print("Found InMemoryMemoryService")
except ImportError as e:
    print(f"Failed to import InMemoryMemoryService: {e}")

try:
    from google.adk import Agent
    print("Found Agent")
except ImportError as e:
    print(f"Failed to import Agent: {e}")

# Check google.generativeai types
try:
    import google.generativeai.types as gtypes
    print(f"GenAI Types: {dir(gtypes)}")
    if hasattr(gtypes, 'Content'):
        print(f"GenAI Content: {dir(gtypes.Content)}")
except Exception as e:
    print(f"Error importing genai types: {e}")

