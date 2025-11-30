from app.agents.chat_agent import CoachChatAgent

agent = CoachChatAgent()
print(f"Number of tools: {len(agent.agent.tools)}")
for i, tool in enumerate(agent.agent.tools):
    print(f"Tool {i}: {type(tool).__name__}")
    if hasattr(tool, '__name__'):
        print(f"  Function name: {tool.__name__}")
