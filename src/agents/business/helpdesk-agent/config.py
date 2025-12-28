"""
Configuration management for the Customer Support Agent.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from src.shared.config import LLMConfig, MemoryConfig, NoveumConfig


@dataclass
class SupportAgentConfig:
    """Configuration for the customer support agent."""
    agent_name: str = "Support Agent"
    company_name: str = "TechCorp"
    max_response_tokens: int = 1500
    temperature: float = 0.3  # Lower temperature for more consistent support responses
    
    # Support-specific settings
    escalation_keywords: List[str] = field(default_factory=lambda: [
        "manager", "supervisor", "escalate", "complaint", "legal", "lawsuit",
        "cancel", "refund", "angry", "frustrated", "unacceptable"
    ])
    
    # Knowledge base settings
    knowledge_base_path: Optional[str] = None
    auto_suggest_articles: bool = True
    
    # Ticket settings
    default_priority: str = "medium"
    auto_categorize: bool = True
    
    # Response settings
    include_ticket_id: bool = True
    include_escalation_notice: bool = True
    max_conversation_context: int = 10
    
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    memory_config: MemoryConfig = field(default_factory=MemoryConfig)
    noveum_config: NoveumConfig = field(default_factory=NoveumConfig)
    
    @classmethod
    def from_env(cls) -> 'SupportAgentConfig':
        """Create configuration from environment variables."""
        
        # LLM Configuration
        llm_config = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            api_key=os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
            api_base=os.getenv("OPENAI_API_BASE"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30"))
        )
        
        # Memory Configuration
        memory_config = MemoryConfig(
            type=os.getenv("MEMORY_TYPE", "buffer"),
            max_messages=int(os.getenv("MEMORY_MAX_MESSAGES", "50")),  # More history for support
            max_tokens=int(os.getenv("MEMORY_MAX_TOKENS", "8000")),    # Larger context for support
            persist_to_file=os.getenv("MEMORY_PERSIST", "true").lower() == "true",
            file_path=os.getenv("MEMORY_FILE_PATH", "./support_conversations.json")
        )
        
        # Noveum Configuration
        noveum_config = NoveumConfig(
            enabled=os.getenv("NOVEUM_ENABLED", "true").lower() == "true",
            api_key=os.getenv("NOVEUM_API_KEY"),
            project=os.getenv("NOVEUM_PROJECT", "customer-support-agent"),
            environment=os.getenv("NOVEUM_ENVIRONMENT", "development"),
            sample_rate=float(os.getenv("NOVEUM_SAMPLE_RATE", "1.0"))
        )
        
        # Parse escalation keywords from environment
        escalation_keywords_str = os.getenv("ESCALATION_KEYWORDS", "")
        escalation_keywords = [kw.strip() for kw in escalation_keywords_str.split(",") if kw.strip()] if escalation_keywords_str else [
            "manager", "supervisor", "escalate", "complaint", "legal", "lawsuit",
            "cancel", "refund", "angry", "frustrated", "unacceptable"
        ]
        
        return cls(
            agent_name=os.getenv("AGENT_NAME", "Support Agent"),
            company_name=os.getenv("COMPANY_NAME", "TechCorp"),
            max_response_tokens=int(os.getenv("MAX_RESPONSE_TOKENS", "1500")),
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.3")),
            escalation_keywords=escalation_keywords,
            knowledge_base_path=os.getenv("KNOWLEDGE_BASE_PATH"),
            auto_suggest_articles=os.getenv("AUTO_SUGGEST_ARTICLES", "true").lower() == "true",
            default_priority=os.getenv("DEFAULT_PRIORITY", "medium"),
            auto_categorize=os.getenv("AUTO_CATEGORIZE", "true").lower() == "true",
            include_ticket_id=os.getenv("INCLUDE_TICKET_ID", "true").lower() == "true",
            include_escalation_notice=os.getenv("INCLUDE_ESCALATION_NOTICE", "true").lower() == "true",
            max_conversation_context=int(os.getenv("MAX_CONVERSATION_CONTEXT", "10")),
            llm_config=llm_config,
            memory_config=memory_config,
            noveum_config=noveum_config
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> 'SupportAgentConfig':
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
            temperature=llm_data.get('temperature', 0.3),
            max_tokens=llm_data.get('max_tokens', 2000),
            timeout=llm_data.get('timeout', 30)
        )
        
        # Parse memory config
        memory_data = data.get('memory', {})
        memory_config = MemoryConfig(
            type=memory_data.get('type', 'buffer'),
            max_messages=memory_data.get('max_messages', 50),
            max_tokens=memory_data.get('max_tokens', 8000),
            persist_to_file=memory_data.get('persist_to_file', True),
            file_path=memory_data.get('file_path', './support_conversations.json')
        )
        
        # Parse Noveum config
        noveum_data = data.get('noveum', {})
        noveum_config = NoveumConfig(
            enabled=noveum_data.get('enabled', True),
            api_key=noveum_data.get('api_key') or os.getenv('NOVEUM_API_KEY'),
            project=noveum_data.get('project', 'customer-support-agent'),
            environment=noveum_data.get('environment', 'development'),
            sample_rate=noveum_data.get('sample_rate', 1.0)
        )
        
        # Parse support-specific config
        support_data = data.get('support', {})
        
        return cls(
            agent_name=data.get('agent_name', 'Support Agent'),
            company_name=data.get('company_name', 'TechCorp'),
            max_response_tokens=data.get('max_response_tokens', 1500),
            temperature=data.get('temperature', 0.3),
            escalation_keywords=support_data.get('escalation_keywords', [
                "manager", "supervisor", "escalate", "complaint", "legal", "lawsuit",
                "cancel", "refund", "angry", "frustrated", "unacceptable"
            ]),
            knowledge_base_path=support_data.get('knowledge_base_path'),
            auto_suggest_articles=support_data.get('auto_suggest_articles', True),
            default_priority=support_data.get('default_priority', 'medium'),
            auto_categorize=support_data.get('auto_categorize', True),
            include_ticket_id=support_data.get('include_ticket_id', True),
            include_escalation_notice=support_data.get('include_escalation_notice', True),
            max_conversation_context=support_data.get('max_conversation_context', 10),
            llm_config=llm_config,
            memory_config=memory_config,
            noveum_config=noveum_config
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'agent_name': self.agent_name,
            'company_name': self.company_name,
            'max_response_tokens': self.max_response_tokens,
            'temperature': self.temperature,
            'support': {
                'escalation_keywords': self.escalation_keywords,
                'knowledge_base_path': self.knowledge_base_path,
                'auto_suggest_articles': self.auto_suggest_articles,
                'default_priority': self.default_priority,
                'auto_categorize': self.auto_categorize,
                'include_ticket_id': self.include_ticket_id,
                'include_escalation_notice': self.include_escalation_notice,
                'max_conversation_context': self.max_conversation_context
            },
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
        
        # Validate basic settings
        if not self.agent_name:
            errors.append("Agent name is required")
        
        if not self.company_name:
            errors.append("Company name is required")
        
        if self.max_response_tokens < 1:
            errors.append("Max response tokens must be positive")
        
        if self.temperature < 0 or self.temperature > 2:
            errors.append("Temperature must be between 0 and 2")
        
        # Validate LLM config
        if not self.llm_config.api_key:
            errors.append("LLM API key is required")
        
        # Validate escalation keywords
        if not self.escalation_keywords:
            print("⚠️  No escalation keywords configured - escalation detection disabled")
        
        # Validate knowledge base path if provided
        if self.knowledge_base_path and not os.path.exists(self.knowledge_base_path):
            print(f"⚠️  Knowledge base path does not exist: {self.knowledge_base_path}")
        
        # Validate Noveum config
        if self.noveum_config.enabled and not self.noveum_config.api_key:
            print("⚠️  Noveum tracing enabled but no API key provided")
        
        if errors:
            print("❌ Configuration validation errors:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        return True

