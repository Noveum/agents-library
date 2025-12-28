#!/usr/bin/env python3
"""
Simple Chat Agent Template

A basic conversational AI agent that can chat with users using various LLM providers.
This template includes Noveum tracing integration for observability.

Usage:
    python main.py                    # Interactive chat mode
    python main.py --message "Hello"  # Single message mode
    python main.py --api             # Run as API server
"""

import asyncio
import argparse
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime

def _load_local_config():
    import importlib.util
    import sys
    from pathlib import Path

    config_path = Path(__file__).resolve().with_name("config.py")
    spec = importlib.util.spec_from_file_location("simple_chat_local_config", config_path)
    if not spec or not spec.loader:
        raise ImportError(f"Unable to load SimpleChat config from {config_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_local_config = _load_local_config()
ChatAgentConfig = _local_config.ChatAgentConfig

from src.shared.llm_client import LLMClient
from src.shared.memory import ConversationMemory
from src.shared.noveum_tracer import NoveumTracer


class SimpleChatAgent:
    """
    A simple conversational AI agent with memory and tracing capabilities.
    
    Features:
    - Multi-provider LLM support (OpenAI, Anthropic, etc.)
    - Conversation memory management
    - Automatic Noveum tracing integration
    - Customizable personality and behavior
    - Production-ready error handling
    """
    
    def __init__(self, config: ChatAgentConfig):
        """Initialize the chat agent with configuration."""
        self.config = config
        self.llm_client = LLMClient(config.llm_config)
        self.memory = ConversationMemory(config.memory_config)
        self.tracer = NoveumTracer(config.noveum_config) if config.noveum_config.enabled else None
        
        # Agent personality and behavior
        self.system_prompt = config.system_prompt or self._default_system_prompt()
        self.agent_name = config.agent_name or "Assistant"
        
        print(f"🤖 {self.agent_name} initialized with {config.llm_config.provider} ({config.llm_config.model})")
        if self.tracer:
            print(f"📊 Noveum tracing enabled for project: {config.noveum_config.project}")
    
    def _default_system_prompt(self) -> str:
        """Default system prompt for the agent."""
        return """You are a helpful, friendly, and knowledgeable AI assistant. 
        
Your personality:
- Conversational and approachable
- Clear and concise in your responses
- Helpful and solution-oriented
- Honest about your limitations

Guidelines:
- Keep responses focused and relevant
- Ask clarifying questions when needed
- Provide examples when helpful
- Be encouraging and positive"""
    
    async def chat(self, message: str, user_id: str = "default") -> str:
        """
        Process a chat message and return a response.
        
        Args:
            message: User's message
            user_id: Unique identifier for the user (for memory isolation)
            
        Returns:
            Agent's response
        """
        if self.tracer:
            return await self.tracer.trace_agent_interaction(
                agent_name=self.agent_name,
                user_message=message,
                handler=self._process_message,
                user_id=user_id
            )
        else:
            return await self._process_message(message, user_id)

    async def process(self, message: str, user_id: str = "default") -> str:
        """
        Process endpoint-compatible alias.

        The API supports /process, and will fall back to chat() if missing,
        but we implement it explicitly so health checks are clean.
        """
        return await self.chat(message, user_id)
    
    async def _process_message(self, message: str, user_id: str) -> str:
        """Internal message processing with error handling."""
        try:
            # Add user message to memory
            await self.memory.add_message(user_id, "user", message)
            
            # Get conversation history
            conversation_history = await self.memory.get_conversation(user_id)
            
            # Prepare messages for LLM
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(conversation_history)
            
            # Generate response
            response = await self.llm_client.generate(
                messages=messages,
                max_tokens=self.config.max_response_tokens,
                temperature=self.config.temperature
            )
            
            # Add assistant response to memory
            await self.memory.add_message(user_id, "assistant", response)
            
            return response
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            print(f"❌ Error processing message: {e}")
            return error_msg
    
    async def reset_conversation(self, user_id: str = "default"):
        """Reset conversation history for a user."""
        await self.memory.clear_conversation(user_id)
        print(f"🔄 Conversation reset for user: {user_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "agent_name": self.agent_name,
            "llm_provider": self.config.llm_config.provider,
            "llm_model": self.config.llm_config.model,
            "memory_type": self.config.memory_config.type,
            "tracing_enabled": self.tracer is not None,
            "total_conversations": self.memory.get_conversation_count(),
            "uptime": datetime.now().isoformat()
        }


async def interactive_chat_mode(agent: SimpleChatAgent):
    """Run the agent in interactive chat mode."""
    print(f"\n💬 Starting interactive chat with {agent.agent_name}")
    print("Type 'quit', 'exit', or 'bye' to end the conversation")
    print("Type '/reset' to clear conversation history")
    print("Type '/stats' to see agent statistics")
    print("-" * 50)
    
    user_id = "interactive_user"
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
                
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print(f"\n👋 Goodbye! Thanks for chatting with {agent.agent_name}")
                break
            elif user_input == '/reset':
                await agent.reset_conversation(user_id)
                continue
            elif user_input == '/stats':
                stats = agent.get_stats()
                print(f"\n📊 Agent Statistics:")
                for key, value in stats.items():
                    print(f"   {key}: {value}")
                continue
            
            # Process message
            print(f"\n{agent.agent_name}: ", end="", flush=True)
            response = await agent.chat(user_input, user_id)
            print(response)
            
        except KeyboardInterrupt:
            print(f"\n\n👋 Goodbye! Thanks for chatting with {agent.agent_name}")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")


async def single_message_mode(agent: SimpleChatAgent, message: str):
    """Process a single message and return the response."""
    response = await agent.chat(message)
    print(f"{agent.agent_name}: {response}")


async def api_server_mode(agent: SimpleChatAgent):
    """Run the agent as a simple API server."""
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
        import uvicorn
        
        app = FastAPI(title=f"{agent.agent_name} API", version="1.0.0")
        
        class ChatRequest(BaseModel):
            message: str
            user_id: str = "default"
        
        class ChatResponse(BaseModel):
            response: str
            user_id: str
            timestamp: str
        
        @app.post("/chat", response_model=ChatResponse)
        async def chat_endpoint(request: ChatRequest):
            try:
                response = await agent.chat(request.message, request.user_id)
                return ChatResponse(
                    response=response,
                    user_id=request.user_id,
                    timestamp=datetime.now().isoformat()
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/stats")
        async def stats_endpoint():
            return agent.get_stats()
        
        @app.post("/reset/{user_id}")
        async def reset_endpoint(user_id: str):
            await agent.reset_conversation(user_id)
            return {"message": f"Conversation reset for user: {user_id}"}
        
        print(f"🚀 Starting API server for {agent.agent_name}")
        print("📖 API Documentation: http://localhost:8000/docs")
        
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except ImportError:
        print("❌ FastAPI not installed. Install with: pip install fastapi uvicorn")
        sys.exit(1)


def main():
    """Main entry point for the chat agent."""
    parser = argparse.ArgumentParser(description="Simple Chat Agent")
    parser.add_argument("--message", "-m", help="Single message to process")
    parser.add_argument("--api", action="store_true", help="Run as API server")
    parser.add_argument("--config", "-c", help="Path to config file", default="config.yaml")
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = ChatAgentConfig.from_file(args.config)
    except FileNotFoundError:
        print(f"⚠️  Config file not found: {args.config}")
        print("Using default configuration...")
        config = ChatAgentConfig.from_env()
    
    # Create and run agent
    async def run():
        agent = SimpleChatAgent(config)
        
        if args.api:
            await api_server_mode(agent)
        elif args.message:
            await single_message_mode(agent, args.message)
        else:
            await interactive_chat_mode(agent)
    
    # Run the agent
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n👋 Agent stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

