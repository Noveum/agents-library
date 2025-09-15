#!/usr/bin/env python3
"""
Basic Chat Example

Demonstrates how to use the AI Agents Library for simple chat interactions.
"""

import asyncio
import os
from src.api.client import AgentsAPIClient, AsyncAgentsAPIClient


def basic_sync_chat():
    """Example of synchronous chat with an agent."""
    print("🤖 Basic Sync Chat Example")
    print("=" * 40)
    
    # Initialize client
    with AgentsAPIClient("http://localhost:8000") as client:
        # List available agents
        agents = client.list_agents()
        print(f"📋 Available agents: {len(agents.agents)}")
        for agent in agents.agents:
            print(f"  - {agent.agent_id}: {agent.name}")
        
        # Chat with simple chat agent
        print("\n💬 Chatting with Simple Chat Agent:")
        response = client.chat(
            "basic.simple_chat_agent",
            "Hello! Can you tell me what you can do?",
            user_id="example_user"
        )
        print(f"Agent: {response.response}")
        
        # Follow-up question
        response = client.chat(
            "basic.simple_chat_agent",
            "What's the weather like today?",
            user_id="example_user"
        )
        print(f"Agent: {response.response}")


async def basic_async_chat():
    """Example of asynchronous chat with an agent."""
    print("\n🚀 Basic Async Chat Example")
    print("=" * 40)
    
    # Initialize async client
    async with AsyncAgentsAPIClient("http://localhost:8000") as client:
        # Get agent information
        agent_info = await client.get_agent_info("basic.simple_chat_agent")
        print(f"📝 Agent: {agent_info.name}")
        print(f"📝 Description: {agent_info.description}")
        
        # Multiple concurrent chats
        tasks = [
            client.chat("basic.simple_chat_agent", "What's 2+2?", user_id="user1"),
            client.chat("basic.simple_chat_agent", "Tell me a joke", user_id="user2"),
            client.chat("basic.simple_chat_agent", "What's the capital of France?", user_id="user3")
        ]
        
        responses = await asyncio.gather(*tasks)
        
        print("\n💬 Concurrent Chat Responses:")
        for i, response in enumerate(responses, 1):
            print(f"Response {i}: {response.response}")


def interactive_chat():
    """Interactive chat session with an agent."""
    print("\n🎯 Interactive Chat Session")
    print("=" * 40)
    print("Type 'quit' to exit")
    
    with AgentsAPIClient("http://localhost:8000") as client:
        user_id = "interactive_user"
        
        while True:
            try:
                message = input("\nYou: ").strip()
                if message.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not message:
                    continue
                
                response = client.chat(
                    "basic.simple_chat_agent",
                    message,
                    user_id=user_id
                )
                print(f"Agent: {response.response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Run all examples."""
    print("🤖 AI Agents Library - Basic Chat Examples")
    print("=" * 50)
    
    # Check if API server is running
    try:
        with AgentsAPIClient("http://localhost:8000") as client:
            health = client.get_health()
            print(f"✅ API Server Status: {health['status']}")
    except Exception as e:
        print(f"❌ API Server not available: {e}")
        print("💡 Start the server with: python -m src.api.main")
        return
    
    # Run examples
    basic_sync_chat()
    
    # Run async example
    asyncio.run(basic_async_chat())
    
    # Interactive chat (uncomment to enable)
    # interactive_chat()


if __name__ == "__main__":
    main()

