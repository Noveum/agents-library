"""
Unified LLM Client for multiple providers.

This module provides a unified interface for different LLM providers
including OpenAI, Anthropic, Azure OpenAI, and others.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def stream_generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", api_base: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self._client = None
    
    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base
                )
            except ImportError:
                raise ImportError("OpenAI package not installed. Install with: pip install openai")
        return self._client
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using OpenAI API."""
        client = self._get_client()
        
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1000),
                timeout=kwargs.get('timeout', 30)
            )
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def stream_generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI API."""
        client = self._get_client()
        
        try:
            stream = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1000),
                stream=True,
                timeout=kwargs.get('timeout', 30)
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise Exception(f"OpenAI streaming error: {str(e)}")


class AnthropicProvider(LLMProvider):
    """Anthropic provider implementation."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Get or create Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
        return self._client
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple:
        """Convert messages to Anthropic format."""
        system_message = ""
        conversation_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation_messages.append(msg)
        
        return system_message, conversation_messages
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using Anthropic API."""
        client = self._get_client()
        system_message, conversation_messages = self._convert_messages(messages)
        
        try:
            response = await client.messages.create(
                model=self.model,
                system=system_message,
                messages=conversation_messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1000),
                timeout=kwargs.get('timeout', 30)
            )
            return response.content[0].text
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    async def stream_generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming response using Anthropic API."""
        client = self._get_client()
        system_message, conversation_messages = self._convert_messages(messages)
        
        try:
            async with client.messages.stream(
                model=self.model,
                system=system_message,
                messages=conversation_messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1000),
                timeout=kwargs.get('timeout', 30)
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            raise Exception(f"Anthropic streaming error: {str(e)}")


class MockProvider(LLMProvider):
    """Mock provider for testing and development."""
    
    def __init__(self, model: str = "mock-model"):
        self.model = model
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate mock response."""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        last_message = messages[-1]["content"] if messages else "Hello"
        return f"Mock response to: {last_message[:50]}..."
    
    async def stream_generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Generate mock streaming response."""
        response = await self.generate(messages, **kwargs)
        
        # Simulate streaming by yielding chunks
        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)


class LLMClient:
    """
    Unified client for multiple LLM providers.
    
    This class provides a consistent interface for different LLM providers
    and handles provider-specific configuration and error handling.
    """
    
    def __init__(self, config):
        """Initialize LLM client with configuration."""
        self.config = config
        self.provider = self._create_provider()
    
    def _create_provider(self) -> LLMProvider:
        """Create the appropriate provider based on configuration."""
        provider_type = self.config.provider.lower()
        
        if provider_type == "openai":
            if not self.config.api_key:
                raise ValueError("OpenAI API key is required")
            return OpenAIProvider(
                api_key=self.config.api_key,
                model=self.config.model,
                api_base=self.config.api_base
            )
        
        elif provider_type == "anthropic":
            if not self.config.api_key:
                raise ValueError("Anthropic API key is required")
            return AnthropicProvider(
                api_key=self.config.api_key,
                model=self.config.model
            )
        
        elif provider_type == "mock":
            return MockProvider(model=self.config.model)
        
        else:
            raise ValueError(f"Unsupported provider: {provider_type}")
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated response text
        """
        # Merge config defaults with kwargs
        params = {
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens,
            'timeout': self.config.timeout,
            **kwargs
        }
        
        try:
            return await self.provider.generate(messages, **params)
        except Exception as e:
            # Add provider context to error
            raise Exception(f"LLM generation failed ({self.config.provider}): {str(e)}")
    
    async def stream_generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Yields:
            Chunks of generated text
        """
        # Merge config defaults with kwargs
        params = {
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens,
            'timeout': self.config.timeout,
            **kwargs
        }
        
        try:
            async for chunk in self.provider.stream_generate(messages, **params):
                yield chunk
        except Exception as e:
            # Add provider context to error
            raise Exception(f"LLM streaming failed ({self.config.provider}): {str(e)}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the LLM client."""
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "timeout": self.config.timeout,
            "api_base": self.config.api_base
        }

