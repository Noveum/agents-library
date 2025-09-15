"""
Shared configuration classes for AI agents.

This module provides base configuration classes that can be used
across different agent implementations.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    provider: str = "openai"  # openai, anthropic, azure, etc.
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30


@dataclass
class MemoryConfig:
    """Configuration for conversation memory."""
    type: str = "buffer"  # buffer, summary, vector
    max_messages: int = 20
    max_tokens: int = 4000
    persist_to_file: bool = False
    file_path: Optional[str] = None


@dataclass
class NoveumConfig:
    """Configuration for Noveum tracing."""
    enabled: bool = True
    api_key: Optional[str] = None
    project: str = "ai-agent"
    environment: str = "development"
    sample_rate: float = 1.0


@dataclass
class ChatAgentConfig:
    """Main configuration for basic chat agents."""
    agent_name: str = "ChatBot"
    system_prompt: Optional[str] = None
    max_response_tokens: int = 1000
    temperature: float = 0.7
    
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    memory_config: MemoryConfig = field(default_factory=MemoryConfig)
    noveum_config: NoveumConfig = field(default_factory=NoveumConfig)
    
    @classmethod
    def from_env(cls) -> 'ChatAgentConfig':
        """Create configuration from environment variables."""
        
        # LLM Configuration
        llm_config = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            api_key=os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
            api_base=os.getenv("OPENAI_API_BASE"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30"))
        )
        
        # Memory Configuration
        memory_config = MemoryConfig(
            type=os.getenv("MEMORY_TYPE", "buffer"),
            max_messages=int(os.getenv("MEMORY_MAX_MESSAGES", "20")),
            max_tokens=int(os.getenv("MEMORY_MAX_TOKENS", "4000")),
            persist_to_file=os.getenv("MEMORY_PERSIST", "false").lower() == "true",
            file_path=os.getenv("MEMORY_FILE_PATH")
        )
        
        # Noveum Configuration
        noveum_config = NoveumConfig(
            enabled=os.getenv("NOVEUM_ENABLED", "true").lower() == "true",
            api_key=os.getenv("NOVEUM_API_KEY"),
            project=os.getenv("NOVEUM_PROJECT", "simple-chat-agent"),
            environment=os.getenv("NOVEUM_ENVIRONMENT", "development"),
            sample_rate=float(os.getenv("NOVEUM_SAMPLE_RATE", "1.0"))
        )
        
        return cls(
            agent_name=os.getenv("AGENT_NAME", "ChatBot"),
            system_prompt=os.getenv("SYSTEM_PROMPT"),
            max_response_tokens=int(os.getenv("MAX_RESPONSE_TOKENS", "1000")),
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
            llm_config=llm_config,
            memory_config=memory_config,
            noveum_config=noveum_config
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> 'ChatAgentConfig':
        """Create configuration from YAML file."""
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Parse LLM config
        llm_data = data.get('llm', {})
        llm_config = LLMConfig(
            provider=llm_data.get('provider', 'openai'),
            model=llm_data.get('model', 'gpt-3.5-turbo'),
            api_key=llm_data.get('api_key') or os.getenv('OPENAI_API_KEY'),
            api_base=llm_data.get('api_base'),
            temperature=llm_data.get('temperature', 0.7),
            max_tokens=llm_data.get('max_tokens', 2000),
            timeout=llm_data.get('timeout', 30)
        )
        
        # Parse memory config
        memory_data = data.get('memory', {})
        memory_config = MemoryConfig(
            type=memory_data.get('type', 'buffer'),
            max_messages=memory_data.get('max_messages', 20),
            max_tokens=memory_data.get('max_tokens', 4000),
            persist_to_file=memory_data.get('persist_to_file', False),
            file_path=memory_data.get('file_path')
        )
        
        # Parse Noveum config
        noveum_data = data.get('noveum', {})
        noveum_config = NoveumConfig(
            enabled=noveum_data.get('enabled', True),
            api_key=noveum_data.get('api_key') or os.getenv('NOVEUM_API_KEY'),
            project=noveum_data.get('project', 'simple-chat-agent'),
            environment=noveum_data.get('environment', 'development'),
            sample_rate=noveum_data.get('sample_rate', 1.0)
        )
        
        return cls(
            agent_name=data.get('agent_name', 'ChatBot'),
            system_prompt=data.get('system_prompt'),
            max_response_tokens=data.get('max_response_tokens', 1000),
            temperature=data.get('temperature', 0.7),
            llm_config=llm_config,
            memory_config=memory_config,
            noveum_config=noveum_config
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'agent_name': self.agent_name,
            'system_prompt': self.system_prompt,
            'max_response_tokens': self.max_response_tokens,
            'temperature': self.temperature,
            'llm': {
                'provider': self.llm_config.provider,
                'model': self.llm_config.model,
                'api_key': '***' if self.llm_config.api_key else None,
                'api_base': self.llm_config.api_base,
                'temperature': self.llm_config.temperature,
                'max_tokens': self.llm_config.max_tokens,
                'timeout': self.llm_config.timeout
            },
            'memory': {
                'type': self.memory_config.type,
                'max_messages': self.memory_config.max_messages,
                'max_tokens': self.memory_config.max_tokens,
                'persist_to_file': self.memory_config.persist_to_file,
                'file_path': self.memory_config.file_path
            },
            'noveum': {
                'enabled': self.noveum_config.enabled,
                'api_key': '***' if self.noveum_config.api_key else None,
                'project': self.noveum_config.project,
                'environment': self.noveum_config.environment,
                'sample_rate': self.noveum_config.sample_rate
            }
        }
    
    def save_to_file(self, file_path: str):
        """Save configuration to YAML file."""
        with open(file_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
    
    def validate(self) -> bool:
        """Validate configuration and return True if valid."""
        errors = []
        
        # Validate LLM config
        if not self.llm_config.api_key:
            errors.append("LLM API key is required")
        
        if self.llm_config.temperature < 0 or self.llm_config.temperature > 2:
            errors.append("LLM temperature must be between 0 and 2")
        
        if self.llm_config.max_tokens < 1:
            errors.append("LLM max_tokens must be positive")
        
        # Validate memory config
        if self.memory_config.max_messages < 1:
            errors.append("Memory max_messages must be positive")
        
        if self.memory_config.max_tokens < 1:
            errors.append("Memory max_tokens must be positive")
        
        # Validate Noveum config
        if self.noveum_config.enabled and not self.noveum_config.api_key:
            print("⚠️  Noveum tracing enabled but no API key provided")
        
        if self.noveum_config.sample_rate < 0 or self.noveum_config.sample_rate > 1:
            errors.append("Noveum sample_rate must be between 0 and 1")
        
        if errors:
            print("❌ Configuration validation errors:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        return True

