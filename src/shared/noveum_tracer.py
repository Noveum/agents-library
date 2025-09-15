"""
Noveum tracing integration for AI agents.

This module provides seamless integration with Noveum.ai for tracing
and observability of AI agent interactions.
"""

import time
import uuid
import asyncio
from typing import Any, Dict, Optional, Callable, Awaitable
from datetime import datetime
from functools import wraps


class NoveumTracer:
    """
    Noveum tracing integration for AI agents.
    
    Provides automatic tracing of agent interactions, LLM calls,
    and performance metrics with graceful degradation if Noveum
    is not available.
    """
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.enabled and config.api_key is not None
        self._client = None
        
        if self.enabled:
            self._initialize_client()
        else:
            print("📊 Noveum tracing disabled (no API key or disabled in config)")
    
    def _initialize_client(self):
        """Initialize Noveum client if available."""
        try:
            # Try to import and initialize Noveum trace
            import noveum_trace
            
            self._client = noveum_trace.Client(
                api_key=self.config.api_key,
                project=self.config.project,
                environment=self.config.environment
            )
            
            print(f"📊 Noveum tracing initialized for project: {self.config.project}")
            
        except ImportError:
            print("⚠️  Noveum trace package not found. Install with: pip install noveum-trace")
            self.enabled = False
        except Exception as e:
            print(f"⚠️  Failed to initialize Noveum tracing: {e}")
            self.enabled = False
    
    async def trace_agent_interaction(
        self,
        agent_name: str,
        user_message: str,
        handler: Callable[[str, str], Awaitable[str]],
        user_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Trace an agent interaction with automatic performance monitoring.
        
        Args:
            agent_name: Name of the agent
            user_message: User's input message
            handler: Async function that processes the message
            user_id: User identifier
            metadata: Additional metadata to include in trace
            
        Returns:
            Agent's response
        """
        if not self.enabled:
            # If tracing is disabled, just call the handler directly
            return await handler(user_message, user_id)
        
        trace_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Start trace
            trace_data = {
                "trace_id": trace_id,
                "agent_name": agent_name,
                "user_id": user_id,
                "user_message": user_message,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            await self._start_trace(trace_data)
            
            # Execute the handler
            response = await handler(user_message, user_id)
            
            # End trace with success
            end_time = time.time()
            duration = end_time - start_time
            
            await self._end_trace(trace_id, {
                "response": response,
                "duration_seconds": duration,
                "status": "success",
                "response_length": len(response) if response else 0
            })
            
            return response
            
        except Exception as e:
            # End trace with error
            end_time = time.time()
            duration = end_time - start_time
            
            await self._end_trace(trace_id, {
                "error": str(e),
                "duration_seconds": duration,
                "status": "error"
            })
            
            # Re-raise the exception
            raise
    
    async def trace_llm_call(
        self,
        provider: str,
        model: str,
        messages: list,
        response: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Trace an LLM API call.
        
        Args:
            provider: LLM provider name (openai, anthropic, etc.)
            model: Model name
            messages: Input messages
            response: LLM response
            duration: Call duration in seconds
            metadata: Additional metadata
        """
        if not self.enabled:
            return
        
        try:
            trace_data = {
                "type": "llm_call",
                "provider": provider,
                "model": model,
                "input_messages": len(messages),
                "input_tokens": self._estimate_tokens(messages),
                "output_tokens": self._estimate_tokens([{"content": response}]),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            await self._log_event(trace_data)
            
        except Exception as e:
            print(f"⚠️  Failed to trace LLM call: {e}")
    
    async def trace_memory_operation(
        self,
        operation: str,
        user_id: str,
        details: Dict[str, Any]
    ):
        """
        Trace memory operations (add, retrieve, clear).
        
        Args:
            operation: Type of operation (add, get, clear)
            user_id: User identifier
            details: Operation details
        """
        if not self.enabled:
            return
        
        try:
            trace_data = {
                "type": "memory_operation",
                "operation": operation,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                **details
            }
            
            await self._log_event(trace_data)
            
        except Exception as e:
            print(f"⚠️  Failed to trace memory operation: {e}")
    
    async def trace_custom_event(
        self,
        event_type: str,
        data: Dict[str, Any]
    ):
        """
        Trace a custom event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if not self.enabled:
            return
        
        try:
            trace_data = {
                "type": event_type,
                "timestamp": datetime.now().isoformat(),
                **data
            }
            
            await self._log_event(trace_data)
            
        except Exception as e:
            print(f"⚠️  Failed to trace custom event: {e}")
    
    async def _start_trace(self, trace_data: Dict[str, Any]):
        """Start a new trace."""
        if self._client and hasattr(self._client, 'start_trace'):
            try:
                await self._client.start_trace(trace_data)
            except Exception as e:
                print(f"⚠️  Failed to start trace: {e}")
    
    async def _end_trace(self, trace_id: str, result_data: Dict[str, Any]):
        """End a trace with results."""
        if self._client and hasattr(self._client, 'end_trace'):
            try:
                await self._client.end_trace(trace_id, result_data)
            except Exception as e:
                print(f"⚠️  Failed to end trace: {e}")
    
    async def _log_event(self, event_data: Dict[str, Any]):
        """Log an event to Noveum."""
        if self._client and hasattr(self._client, 'log_event'):
            try:
                await self._client.log_event(event_data)
            except Exception as e:
                print(f"⚠️  Failed to log event: {e}")
    
    def _estimate_tokens(self, messages: list) -> int:
        """Estimate token count for messages (rough approximation)."""
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        # Rough approximation: 1 token ≈ 4 characters
        return total_chars // 4
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracer statistics."""
        return {
            "enabled": self.enabled,
            "project": self.config.project if self.enabled else None,
            "environment": self.config.environment if self.enabled else None,
            "sample_rate": self.config.sample_rate,
            "client_initialized": self._client is not None
        }


# Decorator functions for easy tracing
def trace_agent_method(agent_name: str = None):
    """Decorator to automatically trace agent methods."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Try to get tracer from self
            tracer = getattr(self, 'tracer', None)
            if not tracer or not tracer.enabled:
                return await func(self, *args, **kwargs)
            
            # Extract message from args/kwargs
            message = args[0] if args else kwargs.get('message', 'Unknown')
            user_id = kwargs.get('user_id', 'default')
            
            name = agent_name or getattr(self, 'agent_name', self.__class__.__name__)
            
            async def handler(msg, uid):
                return await func(self, msg, uid, **{k: v for k, v in kwargs.items() if k not in ['message', 'user_id']})
            
            return await tracer.trace_agent_interaction(
                agent_name=name,
                user_message=str(message),
                handler=handler,
                user_id=user_id
            )
        
        return wrapper
    return decorator


def trace_llm_method(provider: str = None, model: str = None):
    """Decorator to automatically trace LLM method calls."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(self, *args, **kwargs)
                duration = time.time() - start_time
                
                # Try to get tracer from self or parent
                tracer = getattr(self, 'tracer', None)
                if tracer and tracer.enabled:
                    await tracer.trace_llm_call(
                        provider=provider or getattr(self, 'provider', 'unknown'),
                        model=model or getattr(self, 'model', 'unknown'),
                        messages=args[0] if args else [],
                        response=str(result),
                        duration=duration
                    )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Try to trace the error
                tracer = getattr(self, 'tracer', None)
                if tracer and tracer.enabled:
                    await tracer.trace_custom_event('llm_error', {
                        'provider': provider or getattr(self, 'provider', 'unknown'),
                        'model': model or getattr(self, 'model', 'unknown'),
                        'error': str(e),
                        'duration': duration
                    })
                
                raise
        
        return wrapper
    return decorator


# Mock Noveum client for development/testing
class MockNoveumClient:
    """Mock Noveum client for development and testing."""
    
    def __init__(self, api_key: str, project: str, environment: str):
        self.api_key = api_key
        self.project = project
        self.environment = environment
        print(f"🧪 Mock Noveum client initialized for project: {project}")
    
    async def start_trace(self, trace_data: Dict[str, Any]):
        """Mock start trace."""
        print(f"📊 [MOCK] Starting trace: {trace_data.get('trace_id', 'unknown')}")
    
    async def end_trace(self, trace_id: str, result_data: Dict[str, Any]):
        """Mock end trace."""
        status = result_data.get('status', 'unknown')
        duration = result_data.get('duration_seconds', 0)
        print(f"📊 [MOCK] Ending trace {trace_id}: {status} ({duration:.2f}s)")
    
    async def log_event(self, event_data: Dict[str, Any]):
        """Mock log event."""
        event_type = event_data.get('type', 'unknown')
        print(f"📊 [MOCK] Logging event: {event_type}")


# Monkey patch for development
def use_mock_noveum():
    """Use mock Noveum client for development."""
    import sys
    
    class MockNoveumModule:
        Client = MockNoveumClient
    
    sys.modules['noveum_trace'] = MockNoveumModule()

