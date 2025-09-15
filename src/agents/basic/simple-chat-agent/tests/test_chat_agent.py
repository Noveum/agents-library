"""
Tests for Simple Chat Agent.
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '..', 'shared-components'))

from main import SimpleChatAgent
from config import ChatAgentConfig, LLMConfig, MemoryConfig, NoveumConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return ChatAgentConfig(
        agent_name="TestBot",
        llm_config=LLMConfig(
            provider="mock",
            model="test-model",
            api_key="test-key"
        ),
        memory_config=MemoryConfig(
            type="buffer",
            max_messages=5,
            max_tokens=1000
        ),
        noveum_config=NoveumConfig(
            enabled=False  # Disable tracing for tests
        )
    )


@pytest.fixture
async def chat_agent(mock_config):
    """Create a chat agent instance for testing."""
    agent = SimpleChatAgent(mock_config)
    return agent


class TestChatAgentConfig:
    """Test configuration management."""
    
    def test_config_from_env(self):
        """Test configuration loading from environment variables."""
        with patch.dict(os.environ, {
            'AGENT_NAME': 'TestAgent',
            'LLM_PROVIDER': 'openai',
            'LLM_MODEL': 'gpt-4',
            'OPENAI_API_KEY': 'test-key',
            'MEMORY_MAX_MESSAGES': '10'
        }):
            config = ChatAgentConfig.from_env()
            
            assert config.agent_name == 'TestAgent'
            assert config.llm_config.provider == 'openai'
            assert config.llm_config.model == 'gpt-4'
            assert config.llm_config.api_key == 'test-key'
            assert config.memory_config.max_messages == 10
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = ChatAgentConfig(
            llm_config=LLMConfig(api_key="test-key")
        )
        assert config.validate() == True
        
        # Invalid config (no API key)
        config = ChatAgentConfig(
            llm_config=LLMConfig(api_key=None)
        )
        assert config.validate() == False


class TestSimpleChatAgent:
    """Test SimpleChatAgent functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, mock_config):
        """Test agent initialization."""
        agent = SimpleChatAgent(mock_config)
        
        assert agent.agent_name == "TestBot"
        assert agent.config == mock_config
        assert agent.llm_client is not None
        assert agent.memory is not None
    
    @pytest.mark.asyncio
    async def test_chat_basic(self, chat_agent):
        """Test basic chat functionality."""
        response = await chat_agent.chat("Hello", "test_user")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "Mock response" in response
    
    @pytest.mark.asyncio
    async def test_chat_with_memory(self, chat_agent):
        """Test chat with memory persistence."""
        # First message
        response1 = await chat_agent.chat("My name is Alice", "test_user")
        assert isinstance(response1, str)
        
        # Second message should have context
        response2 = await chat_agent.chat("What's my name?", "test_user")
        assert isinstance(response2, str)
        
        # Check that memory has messages
        conversation = await chat_agent.memory.get_conversation("test_user")
        assert len(conversation) >= 2  # At least user message and response
    
    @pytest.mark.asyncio
    async def test_reset_conversation(self, chat_agent):
        """Test conversation reset functionality."""
        # Add some messages
        await chat_agent.chat("Hello", "test_user")
        await chat_agent.chat("How are you?", "test_user")
        
        # Check messages exist
        conversation = await chat_agent.memory.get_conversation("test_user")
        assert len(conversation) > 0
        
        # Reset conversation
        await chat_agent.reset_conversation("test_user")
        
        # Check messages are cleared
        conversation = await chat_agent.memory.get_conversation("test_user")
        assert len(conversation) == 0
    
    @pytest.mark.asyncio
    async def test_multiple_users(self, chat_agent):
        """Test multiple user isolation."""
        # Chat with user 1
        await chat_agent.chat("I'm user 1", "user1")
        
        # Chat with user 2
        await chat_agent.chat("I'm user 2", "user2")
        
        # Check conversations are separate
        conv1 = await chat_agent.memory.get_conversation("user1")
        conv2 = await chat_agent.memory.get_conversation("user2")
        
        assert len(conv1) >= 1
        assert len(conv2) >= 1
        
        # Check content is different
        user1_content = [msg["content"] for msg in conv1]
        user2_content = [msg["content"] for msg in conv2]
        
        assert "I'm user 1" in str(user1_content)
        assert "I'm user 2" in str(user2_content)
    
    def test_get_stats(self, chat_agent):
        """Test agent statistics."""
        stats = chat_agent.get_stats()
        
        assert isinstance(stats, dict)
        assert "agent_name" in stats
        assert "llm_provider" in stats
        assert "llm_model" in stats
        assert "memory_type" in stats
        assert "tracing_enabled" in stats
        
        assert stats["agent_name"] == "TestBot"
        assert stats["llm_provider"] == "mock"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_config):
        """Test error handling in chat processing."""
        # Create agent with invalid LLM config to trigger errors
        mock_config.llm_config.provider = "invalid_provider"
        
        with pytest.raises(ValueError):
            agent = SimpleChatAgent(mock_config)


class TestMemorySystem:
    """Test memory system functionality."""
    
    @pytest.mark.asyncio
    async def test_memory_limits(self, chat_agent):
        """Test memory limits and trimming."""
        user_id = "test_user"
        
        # Add more messages than the limit (5)
        for i in range(10):
            await chat_agent.chat(f"Message {i}", user_id)
        
        # Check that memory is trimmed
        conversation = await chat_agent.memory.get_conversation(user_id)
        
        # Should not exceed max_messages * 2 (user + assistant messages)
        assert len(conversation) <= chat_agent.config.memory_config.max_messages * 2
    
    @pytest.mark.asyncio
    async def test_memory_persistence(self, tmp_path):
        """Test memory file persistence."""
        # Create config with file persistence
        config = ChatAgentConfig(
            llm_config=LLMConfig(provider="mock", api_key="test"),
            memory_config=MemoryConfig(
                type="buffer",
                persist_to_file=True,
                file_path=str(tmp_path / "test_memory.json")
            ),
            noveum_config=NoveumConfig(enabled=False)
        )
        
        agent = SimpleChatAgent(config)
        
        # Add a message
        await agent.chat("Test message", "test_user")
        
        # Check that file was created
        assert os.path.exists(config.memory_config.file_path)


class TestConfigurationFiles:
    """Test configuration file handling."""
    
    def test_yaml_config_loading(self, tmp_path):
        """Test loading configuration from YAML file."""
        # Create a test YAML config
        config_content = """
agent_name: "YAML Test Agent"
llm:
  provider: openai
  model: gpt-4
  temperature: 0.8
memory:
  type: buffer
  max_messages: 15
noveum:
  enabled: false
"""
        
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(config_content)
        
        # Load config
        config = ChatAgentConfig.from_file(str(config_file))
        
        assert config.agent_name == "YAML Test Agent"
        assert config.llm_config.provider == "openai"
        assert config.llm_config.model == "gpt-4"
        assert config.llm_config.temperature == 0.8
        assert config.memory_config.max_messages == 15
        assert config.noveum_config.enabled == False


# Integration tests
class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, chat_agent):
        """Test a complete conversation flow."""
        user_id = "integration_test_user"
        
        # Simulate a conversation
        messages = [
            "Hello, I'm looking for help with Python programming",
            "Can you explain what a list is?",
            "How do I add items to a list?",
            "Thank you for the help!"
        ]
        
        responses = []
        for message in messages:
            response = await chat_agent.chat(message, user_id)
            responses.append(response)
            assert isinstance(response, str)
            assert len(response) > 0
        
        # Check conversation history
        conversation = await chat_agent.memory.get_conversation(user_id)
        assert len(conversation) >= len(messages)  # At least one message per exchange
        
        # Check that all user messages are in history
        conversation_text = str(conversation)
        for message in messages:
            assert message in conversation_text or any(word in conversation_text for word in message.split())


if __name__ == "__main__":
    pytest.main([__file__])

