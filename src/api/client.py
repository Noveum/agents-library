"""
Python Client Library for AI Agents Library API.

This module provides a convenient Python interface for interacting
with the AI Agents Library API, making it easy to invoke agents
from other Python applications.
"""

import asyncio
import aiohttp
import requests
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import json


@dataclass
class AgentResponse:
    """Response from an agent invocation."""
    agent_id: str
    response: str
    metadata: Dict[str, Any]
    processing_time: float
    timestamp: str
    success: bool
    error: Optional[str] = None


@dataclass
class AgentInfo:
    """Information about an available agent."""
    agent_id: str
    name: str
    category: str
    subcategory: str
    description: str
    version: str
    author: str
    tags: List[str]
    endpoints: List[str]
    enabled: bool


class AgentsAPIClient:
    """
    Synchronous client for the AI Agents Library API.
    
    This client provides methods to list agents, get agent information,
    and invoke agents using the REST API.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the agents API server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AgentsAPIClient/1.0.0'
        })
    
    def list_agents(self, category: Optional[str] = None, enabled_only: bool = True) -> List[AgentInfo]:
        """
        List all available agents.
        
        Args:
            category: Filter by category (optional)
            enabled_only: Only return enabled agents
            
        Returns:
            List of agent information objects
        """
        params = {}
        if category:
            params['category'] = category
        if not enabled_only:
            params['enabled_only'] = 'false'
        
        response = self.session.get(
            f"{self.base_url}/agents",
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        agents_data = response.json()
        return [AgentInfo(**agent) for agent in agents_data]
    
    def get_agent_info(self, agent_id: str) -> AgentInfo:
        """
        Get detailed information about a specific agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent information object
        """
        response = self.session.get(
            f"{self.base_url}/agents/{agent_id}",
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return AgentInfo(**response.json())
    
    def chat(
        self, 
        agent_id: str, 
        message: str, 
        user_id: str = "api_user",
        config_overrides: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Chat with an agent.
        
        Args:
            agent_id: ID of the agent to chat with
            message: Message to send to the agent
            user_id: User identifier
            config_overrides: Configuration overrides for the agent
            metadata: Additional metadata to include
            
        Returns:
            Agent response object
        """
        return self._invoke_agent(agent_id, "chat", message, user_id, config_overrides, metadata)
    
    def process(
        self, 
        agent_id: str, 
        message: str, 
        user_id: str = "api_user",
        config_overrides: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process a message with an agent.
        
        Args:
            agent_id: ID of the agent to use
            message: Message to process
            user_id: User identifier
            config_overrides: Configuration overrides for the agent
            metadata: Additional metadata to include
            
        Returns:
            Agent response object
        """
        return self._invoke_agent(agent_id, "process", message, user_id, config_overrides, metadata)
    
    def support_request(
        self, 
        agent_id: str, 
        message: str, 
        user_id: str = "api_user",
        config_overrides: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Submit a support request to a support agent.
        
        Args:
            agent_id: ID of the support agent
            message: Support request message
            user_id: Customer identifier
            config_overrides: Configuration overrides for the agent
            metadata: Additional metadata to include
            
        Returns:
            Agent response object with support ticket information
        """
        return self._invoke_agent(agent_id, "support", message, user_id, config_overrides, metadata)
    
    def _invoke_agent(
        self,
        agent_id: str,
        method: str,
        message: str,
        user_id: str,
        config_overrides: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]]
    ) -> AgentResponse:
        """Internal method to invoke an agent."""
        payload = {
            "message": message,
            "user_id": user_id,
            "config_overrides": config_overrides or {},
            "metadata": metadata or {}
        }
        
        response = self.session.post(
            f"{self.base_url}/agents/{agent_id}/{method}",
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return AgentResponse(**response.json())
    
    def health_check(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform health check on the API or a specific agent.
        
        Args:
            agent_id: ID of specific agent to check (optional)
            
        Returns:
            Health check results
        """
        if agent_id:
            url = f"{self.base_url}/health/{agent_id}"
        else:
            url = f"{self.base_url}/health"
        
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        return response.json()
    
    def get_categories(self) -> List[str]:
        """
        Get all available agent categories.
        
        Returns:
            List of category names
        """
        response = self.session.get(
            f"{self.base_url}/categories",
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get API statistics.
        
        Returns:
            Statistics about the agent registry
        """
        response = self.session.get(
            f"{self.base_url}/stats",
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def reload_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Reload an agent module (useful for development).
        
        Args:
            agent_id: ID of the agent to reload
            
        Returns:
            Reload operation result
        """
        response = self.session.post(
            f"{self.base_url}/agents/{agent_id}/reload",
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class AsyncAgentsAPIClient:
    """
    Asynchronous client for the AI Agents Library API.
    
    This client provides async methods for high-performance applications
    that need to make many concurrent requests to the agents API.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        """
        Initialize the async API client.
        
        Args:
            base_url: Base URL of the agents API server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'AsyncAgentsAPIClient/1.0.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def list_agents(self, category: Optional[str] = None, enabled_only: bool = True) -> List[AgentInfo]:
        """
        List all available agents (async).
        
        Args:
            category: Filter by category (optional)
            enabled_only: Only return enabled agents
            
        Returns:
            List of agent information objects
        """
        params = {}
        if category:
            params['category'] = category
        if not enabled_only:
            params['enabled_only'] = 'false'
        
        async with self.session.get(f"{self.base_url}/agents", params=params) as response:
            response.raise_for_status()
            agents_data = await response.json()
            return [AgentInfo(**agent) for agent in agents_data]
    
    async def get_agent_info(self, agent_id: str) -> AgentInfo:
        """
        Get detailed information about a specific agent (async).
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent information object
        """
        async with self.session.get(f"{self.base_url}/agents/{agent_id}") as response:
            response.raise_for_status()
            return AgentInfo(**await response.json())
    
    async def chat(
        self, 
        agent_id: str, 
        message: str, 
        user_id: str = "api_user",
        config_overrides: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Chat with an agent (async).
        
        Args:
            agent_id: ID of the agent to chat with
            message: Message to send to the agent
            user_id: User identifier
            config_overrides: Configuration overrides for the agent
            metadata: Additional metadata to include
            
        Returns:
            Agent response object
        """
        return await self._invoke_agent(agent_id, "chat", message, user_id, config_overrides, metadata)
    
    async def process(
        self, 
        agent_id: str, 
        message: str, 
        user_id: str = "api_user",
        config_overrides: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process a message with an agent (async).
        
        Args:
            agent_id: ID of the agent to use
            message: Message to process
            user_id: User identifier
            config_overrides: Configuration overrides for the agent
            metadata: Additional metadata to include
            
        Returns:
            Agent response object
        """
        return await self._invoke_agent(agent_id, "process", message, user_id, config_overrides, metadata)
    
    async def support_request(
        self, 
        agent_id: str, 
        message: str, 
        user_id: str = "api_user",
        config_overrides: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Submit a support request to a support agent (async).
        
        Args:
            agent_id: ID of the support agent
            message: Support request message
            user_id: Customer identifier
            config_overrides: Configuration overrides for the agent
            metadata: Additional metadata to include
            
        Returns:
            Agent response object with support ticket information
        """
        return await self._invoke_agent(agent_id, "support", message, user_id, config_overrides, metadata)
    
    async def _invoke_agent(
        self,
        agent_id: str,
        method: str,
        message: str,
        user_id: str,
        config_overrides: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]]
    ) -> AgentResponse:
        """Internal method to invoke an agent (async)."""
        payload = {
            "message": message,
            "user_id": user_id,
            "config_overrides": config_overrides or {},
            "metadata": metadata or {}
        }
        
        async with self.session.post(
            f"{self.base_url}/agents/{agent_id}/{method}",
            json=payload
        ) as response:
            response.raise_for_status()
            return AgentResponse(**await response.json())
    
    async def health_check(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform health check on the API or a specific agent (async).
        
        Args:
            agent_id: ID of specific agent to check (optional)
            
        Returns:
            Health check results
        """
        if agent_id:
            url = f"{self.base_url}/health/{agent_id}"
        else:
            url = f"{self.base_url}/health"
        
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_categories(self) -> List[str]:
        """
        Get all available agent categories (async).
        
        Returns:
            List of category names
        """
        async with self.session.get(f"{self.base_url}/categories") as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get API statistics (async).
        
        Returns:
            Statistics about the agent registry
        """
        async with self.session.get(f"{self.base_url}/stats") as response:
            response.raise_for_status()
            return await response.json()


# Convenience functions for quick usage
def chat_with_agent(
    agent_id: str, 
    message: str, 
    user_id: str = "api_user",
    base_url: str = "http://localhost:8000"
) -> str:
    """
    Quick function to chat with an agent and get the response text.
    
    Args:
        agent_id: ID of the agent to chat with
        message: Message to send
        user_id: User identifier
        base_url: API server URL
        
    Returns:
        Agent's response text
    """
    with AgentsAPIClient(base_url) as client:
        response = client.chat(agent_id, message, user_id)
        return response.response


async def async_chat_with_agent(
    agent_id: str, 
    message: str, 
    user_id: str = "api_user",
    base_url: str = "http://localhost:8000"
) -> str:
    """
    Quick async function to chat with an agent and get the response text.
    
    Args:
        agent_id: ID of the agent to chat with
        message: Message to send
        user_id: User identifier
        base_url: API server URL
        
    Returns:
        Agent's response text
    """
    async with AsyncAgentsAPIClient(base_url) as client:
        response = await client.chat(agent_id, message, user_id)
        return response.response


# Example usage
if __name__ == "__main__":
    # Synchronous example
    print("🔍 Testing synchronous client...")
    
    with AgentsAPIClient() as client:
        # List available agents
        agents = client.list_agents()
        print(f"Found {len(agents)} agents")
        
        if agents:
            # Chat with the first agent
            agent = agents[0]
            print(f"Chatting with {agent.name}...")
            
            response = client.chat(
                agent.agent_id, 
                "Hello, how are you?", 
                "test_user"
            )
            
            print(f"Response: {response.response}")
            print(f"Processing time: {response.processing_time:.2f}s")
    
    # Asynchronous example
    async def async_example():
        print("\n🚀 Testing asynchronous client...")
        
        async with AsyncAgentsAPIClient() as client:
            # List available agents
            agents = await client.list_agents()
            print(f"Found {len(agents)} agents")
            
            if agents:
                # Chat with multiple agents concurrently
                tasks = []
                for agent in agents[:2]:  # Test with first 2 agents
                    task = client.chat(
                        agent.agent_id,
                        f"Hello from async client! What can you do?",
                        "async_test_user"
                    )
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, response in enumerate(responses):
                    if isinstance(response, Exception):
                        print(f"Agent {i}: Error - {response}")
                    else:
                        print(f"Agent {i}: {response.response[:100]}...")
    
    # Run async example
    asyncio.run(async_example())

