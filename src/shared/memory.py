"""
Memory management for AI agents.

This module provides different types of memory systems for maintaining
conversation history and context across interactions.
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod


class MemorySystem(ABC):
    """Abstract base class for memory systems."""
    
    @abstractmethod
    async def add_message(self, user_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to memory."""
        pass
    
    @abstractmethod
    async def get_conversation(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a user."""
        pass
    
    @abstractmethod
    async def clear_conversation(self, user_id: str):
        """Clear conversation history for a user."""
        pass
    
    @abstractmethod
    def get_conversation_count(self) -> int:
        """Get total number of conversations."""
        pass


class BufferMemory(MemorySystem):
    """
    Simple buffer memory that keeps recent messages in memory.
    
    Features:
    - Configurable message limit
    - Token-based truncation
    - Optional file persistence
    """
    
    def __init__(self, config):
        self.config = config
        self.conversations: Dict[str, List[Dict]] = {}
        
        # Load from file if persistence is enabled
        if config.persist_to_file and config.file_path:
            self._load_from_file()
    
    async def add_message(self, user_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the conversation buffer."""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversations[user_id].append(message)
        
        # Trim conversation if it exceeds limits
        await self._trim_conversation(user_id)
        
        # Persist to file if enabled
        if self.config.persist_to_file:
            self._save_to_file()
    
    async def get_conversation(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history formatted for LLM."""
        if user_id not in self.conversations:
            return []
        
        # Return only role and content for LLM
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.conversations[user_id]
        ]
    
    async def clear_conversation(self, user_id: str):
        """Clear conversation history for a user."""
        if user_id in self.conversations:
            del self.conversations[user_id]
            
        if self.config.persist_to_file:
            self._save_to_file()
    
    def get_conversation_count(self) -> int:
        """Get total number of active conversations."""
        return len(self.conversations)
    
    async def _trim_conversation(self, user_id: str):
        """Trim conversation to stay within limits."""
        if user_id not in self.conversations:
            return
        
        messages = self.conversations[user_id]
        
        # Trim by message count
        if len(messages) > self.config.max_messages:
            # Keep the most recent messages
            self.conversations[user_id] = messages[-self.config.max_messages:]
            messages = self.conversations[user_id]
        
        # Trim by token count (approximate)
        if self.config.max_tokens > 0:
            total_tokens = sum(len(msg["content"].split()) for msg in messages)
            
            while total_tokens > self.config.max_tokens and len(messages) > 1:
                # Remove oldest message (but keep at least one)
                removed = messages.pop(0)
                total_tokens -= len(removed["content"].split())
    
    def _save_to_file(self):
        """Save conversations to file."""
        if not self.config.file_path:
            return
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config.file_path), exist_ok=True)
            
            with open(self.config.file_path, 'w') as f:
                json.dump(self.conversations, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save memory to file: {e}")
    
    def _load_from_file(self):
        """Load conversations from file."""
        if not self.config.file_path or not os.path.exists(self.config.file_path):
            return
        
        try:
            with open(self.config.file_path, 'r') as f:
                self.conversations = json.load(f)
        except Exception as e:
            print(f"⚠️  Failed to load memory from file: {e}")
            self.conversations = {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        total_messages = sum(len(conv) for conv in self.conversations.values())
        
        return {
            "type": "buffer",
            "total_conversations": len(self.conversations),
            "total_messages": total_messages,
            "max_messages": self.config.max_messages,
            "max_tokens": self.config.max_tokens,
            "persistence_enabled": self.config.persist_to_file,
            "file_path": self.config.file_path
        }


class SummaryMemory(MemorySystem):
    """
    Memory system that maintains conversation summaries.
    
    This is a placeholder implementation for future development.
    """
    
    def __init__(self, config):
        self.config = config
        self.summaries: Dict[str, str] = {}
        self.recent_messages: Dict[str, List[Dict]] = {}
    
    async def add_message(self, user_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message and update summary if needed."""
        # This is a placeholder - would implement summarization logic
        if user_id not in self.recent_messages:
            self.recent_messages[user_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.recent_messages[user_id].append(message)
        
        # Placeholder: would trigger summarization when buffer is full
        if len(self.recent_messages[user_id]) > 10:
            await self._create_summary(user_id)
    
    async def get_conversation(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation with summary context."""
        messages = []
        
        # Add summary as context if available
        if user_id in self.summaries:
            messages.append({
                "role": "system",
                "content": f"Previous conversation summary: {self.summaries[user_id]}"
            })
        
        # Add recent messages
        if user_id in self.recent_messages:
            messages.extend([
                {"role": msg["role"], "content": msg["content"]}
                for msg in self.recent_messages[user_id]
            ])
        
        return messages
    
    async def clear_conversation(self, user_id: str):
        """Clear conversation and summary."""
        if user_id in self.summaries:
            del self.summaries[user_id]
        if user_id in self.recent_messages:
            del self.recent_messages[user_id]
    
    def get_conversation_count(self) -> int:
        """Get total number of conversations."""
        return len(self.recent_messages)
    
    async def _create_summary(self, user_id: str):
        """Create summary of conversation (placeholder)."""
        # This would use an LLM to create a summary
        messages = self.recent_messages.get(user_id, [])
        if messages:
            # Placeholder summary
            self.summaries[user_id] = f"Conversation with {len(messages)} messages"
            # Clear old messages after summarizing
            self.recent_messages[user_id] = messages[-3:]  # Keep last 3


class ConversationMemory:
    """
    Factory class for creating different types of memory systems.
    
    This provides a unified interface for different memory implementations.
    """
    
    def __init__(self, config):
        self.config = config
        self.memory_system = self._create_memory_system()
    
    def _create_memory_system(self) -> MemorySystem:
        """Create the appropriate memory system based on configuration."""
        memory_type = self.config.type.lower()
        
        if memory_type == "buffer":
            return BufferMemory(self.config)
        elif memory_type == "summary":
            return SummaryMemory(self.config)
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")
    
    async def add_message(self, user_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to memory."""
        await self.memory_system.add_message(user_id, role, content, metadata)
    
    async def get_conversation(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history."""
        return await self.memory_system.get_conversation(user_id)
    
    async def clear_conversation(self, user_id: str):
        """Clear conversation history."""
        await self.memory_system.clear_conversation(user_id)
    
    def get_conversation_count(self) -> int:
        """Get total number of conversations."""
        return self.memory_system.get_conversation_count()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if hasattr(self.memory_system, 'get_stats'):
            return self.memory_system.get_stats()
        else:
            return {
                "type": self.config.type,
                "conversations": self.get_conversation_count()
            }

