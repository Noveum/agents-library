#!/usr/bin/env python3
"""
AI Agents Library - FastAPI Application

A unified API server for invoking AI agents via REST endpoints.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import importlib.util
import traceback
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from .agent_registry import get_registry, AgentRegistry, AgentInfo


# Pydantic models for API requests and responses
class AgentRequest(BaseModel):
    """Request model for agent invocation."""
    message: str = Field(..., description="Input message for the agent")
    user_id: str = Field(default="api_user", description="User identifier")
    config_overrides: Optional[Dict[str, Any]] = Field(default=None, description="Configuration overrides")


class AgentResponse(BaseModel):
    """Response model for agent invocation."""
    agent_id: str = Field(..., description="Agent identifier")
    response: str = Field(..., description="Agent response")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if any")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Check timestamp")
    version: str = Field(default="1.0.0", description="API version")
    agents_count: int = Field(..., description="Number of registered agents")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional health details")


class AgentListResponse(BaseModel):
    """Agent list response model."""
    agents: List[AgentInfo] = Field(..., description="List of available agents")
    total_count: int = Field(..., description="Total number of agents")
    categories: List[str] = Field(..., description="Available categories")


# Initialize FastAPI app
app = FastAPI(
    title="AI Agents Library API",
    description="Unified API for invoking AI agents via REST endpoints",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global registry instance
registry: Optional[AgentRegistry] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    global registry
    print("🚀 Starting AI Agents Library API")
    
    # Initialize agent registry
    registry = get_registry()
    print(f"📋 Discovered {len(registry.agents)} agents")
    
    # Perform initial health checks
    print("🔍 Performing initial health checks...")
    
    # Check Noveum tracing configuration
    noveum_enabled = os.getenv("NOVEUM_ENABLED", "true").lower() == "true"
    noveum_api_key = os.getenv("NOVEUM_API_KEY")
    
    if noveum_enabled and noveum_api_key:
        print("📊 Noveum tracing enabled")
    else:
        print("📊 Noveum tracing disabled (no API key or disabled in config)")
    
    # Health check all agents
    for agent_id in registry.agents:
        try:
            health_status = await registry.check_agent_health(agent_id)
            status_icon = "✅" if health_status["status"] == "healthy" else "❌"
            print(f"{status_icon} {agent_id}: {health_status['status']}")
        except Exception as e:
            print(f"❌ {agent_id}: error")


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Get API information and statistics."""
    return {
        "name": "AI Agents Library API",
        "version": "1.0.0",
        "description": "Unified API for invoking AI agents via REST endpoints",
        "agents_count": len(registry.agents) if registry else 0,
        "endpoints": {
            "agents": "/agents",
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/agents", response_model=AgentListResponse)
async def list_agents(category: Optional[str] = None):
    """List all available agents, optionally filtered by category."""
    if not registry:
        raise HTTPException(status_code=503, detail="Agent registry not initialized")
    
    agents = list(registry.agents.values())
    
    # Filter by category if specified
    if category:
        agents = [agent for agent in agents if agent.category == category]
    
    # Get unique categories
    categories = list(set(agent.category for agent in registry.agents.values()))
    
    return AgentListResponse(
        agents=agents,
        total_count=len(agents),
        categories=sorted(categories)
    )


@app.get("/agents/{agent_id}", response_model=AgentInfo)
async def get_agent_info(agent_id: str):
    """Get detailed information about a specific agent."""
    if not registry:
        raise HTTPException(status_code=503, detail="Agent registry not initialized")
    
    if agent_id not in registry.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    return registry.agents[agent_id]


@app.get("/categories")
async def list_categories():
    """List all available agent categories."""
    if not registry:
        raise HTTPException(status_code=503, detail="Agent registry not initialized")
    
    categories = {}
    for agent in registry.agents.values():
        if agent.category not in categories:
            categories[agent.category] = {
                "name": agent.category,
                "agents": [],
                "count": 0
            }
        categories[agent.category]["agents"].append(agent.agent_id)
        categories[agent.category]["count"] += 1
    
    return {
        "categories": list(categories.values()),
        "total_categories": len(categories)
    }


@app.post("/agents/{agent_id}/chat", response_model=AgentResponse)
async def chat_with_agent(agent_id: str, request: AgentRequest):
    """Chat with a specific agent."""
    start_time = time.time()
    
    if not registry:
        raise HTTPException(status_code=503, detail="Agent registry not initialized")
    
    if agent_id not in registry.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    try:
        # Get agent instance
        agent_instance = await registry.get_agent_instance(agent_id)
        
        # Check if agent supports chat endpoint
        agent_info = registry.agents[agent_id]
        if "chat" not in agent_info.endpoints:
            raise HTTPException(
                status_code=400, 
                detail=f"Agent '{agent_id}' does not support chat endpoint"
            )
        
        # Invoke agent
        response = await agent_instance.chat(request.message, request.user_id)
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
            agent_id=agent_id,
            response=response,
            metadata={
                "user_id": request.user_id,
                "agent_name": agent_info.name,
                "processing_time": processing_time
            },
            processing_time=processing_time,
            timestamp=datetime.utcnow().isoformat(),
            success=True
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Error invoking agent '{agent_id}': {str(e)}"
        
        return AgentResponse(
            agent_id=agent_id,
            response="",
            metadata={"error_details": str(e)},
            processing_time=processing_time,
            timestamp=datetime.utcnow().isoformat(),
            success=False,
            error=error_msg
        )


@app.post("/agents/{agent_id}/process", response_model=AgentResponse)
async def process_with_agent(agent_id: str, request: AgentRequest):
    """Process a message with a specific agent."""
    start_time = time.time()
    
    if not registry:
        raise HTTPException(status_code=503, detail="Agent registry not initialized")
    
    if agent_id not in registry.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    try:
        # Get agent instance
        agent_instance = await registry.get_agent_instance(agent_id)
        
        # Check if agent supports process endpoint
        agent_info = registry.agents[agent_id]
        if "process" not in agent_info.endpoints:
            raise HTTPException(
                status_code=400, 
                detail=f"Agent '{agent_id}' does not support process endpoint"
            )
        
        # Invoke agent
        if hasattr(agent_instance, 'process'):
            response = await agent_instance.process(request.message, request.user_id)
        else:
            # Fallback to chat if process method not available
            response = await agent_instance.chat(request.message, request.user_id)
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
            agent_id=agent_id,
            response=response,
            metadata={
                "user_id": request.user_id,
                "agent_name": agent_info.name,
                "processing_time": processing_time
            },
            processing_time=processing_time,
            timestamp=datetime.utcnow().isoformat(),
            success=True
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Error processing with agent '{agent_id}': {str(e)}"
        
        return AgentResponse(
            agent_id=agent_id,
            response="",
            metadata={"error_details": str(e)},
            processing_time=processing_time,
            timestamp=datetime.utcnow().isoformat(),
            success=False,
            error=error_msg
        )


@app.post("/agents/{agent_id}/support", response_model=AgentResponse)
async def support_request(agent_id: str, request: AgentRequest):
    """Submit a support request to a support agent."""
    start_time = time.time()
    
    if not registry:
        raise HTTPException(status_code=503, detail="Agent registry not initialized")
    
    if agent_id not in registry.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    try:
        # Get agent instance
        agent_instance = await registry.get_agent_instance(agent_id)
        
        # Check if agent supports support endpoint
        agent_info = registry.agents[agent_id]
        if "support" not in agent_info.endpoints:
            raise HTTPException(
                status_code=400, 
                detail=f"Agent '{agent_id}' does not support support endpoint"
            )
        
        # Invoke agent
        if hasattr(agent_instance, 'handle_support_request'):
            response = await agent_instance.handle_support_request(request.message, request.user_id)
        else:
            # Fallback to chat for support requests
            response = await agent_instance.chat(request.message, request.user_id)
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
            agent_id=agent_id,
            response=response,
            metadata={
                "user_id": request.user_id,
                "agent_name": agent_info.name,
                "request_type": "support",
                "processing_time": processing_time
            },
            processing_time=processing_time,
            timestamp=datetime.utcnow().isoformat(),
            success=True
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Error handling support request with agent '{agent_id}': {str(e)}"
        
        return AgentResponse(
            agent_id=agent_id,
            response="",
            metadata={"error_details": str(e)},
            processing_time=processing_time,
            timestamp=datetime.utcnow().isoformat(),
            success=False,
            error=error_msg
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Overall system health check."""
    if not registry:
        raise HTTPException(status_code=503, detail="Agent registry not initialized")
    
    # Check system health
    healthy_agents = 0
    total_agents = len(registry.agents)
    
    for agent_id in registry.agents:
        try:
            health_status = await registry.check_agent_health(agent_id)
            if health_status["status"] == "healthy":
                healthy_agents += 1
        except:
            pass
    
    overall_status = "healthy" if healthy_agents == total_agents else "degraded"
    if healthy_agents == 0:
        overall_status = "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        agents_count=total_agents,
        details={
            "healthy_agents": healthy_agents,
            "total_agents": total_agents,
            "health_percentage": (healthy_agents / total_agents * 100) if total_agents > 0 else 0
        }
    )


@app.get("/health/{agent_id}")
async def agent_health_check(agent_id: str):
    """Health check for a specific agent."""
    if not registry:
        raise HTTPException(status_code=503, detail="Agent registry not initialized")
    
    if agent_id not in registry.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    try:
        health_status = await registry.check_agent_health(agent_id)
        return health_status
    except Exception as e:
        return {
            "agent_id": agent_id,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.post("/agents/{agent_id}/reload")
async def reload_agent(agent_id: str):
    """Reload an agent module (development only)."""
    if not registry:
        raise HTTPException(status_code=503, detail="Agent registry not initialized")
    
    if agent_id not in registry.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    try:
        # Remove from loaded modules and instances
        if agent_id in registry.loaded_modules:
            del registry.loaded_modules[agent_id]
        if agent_id in registry.agent_instances:
            del registry.agent_instances[agent_id]
        
        # Force reload on next access
        return {
            "agent_id": agent_id,
            "status": "reloaded",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading agent: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get registry statistics."""
    if not registry:
        raise HTTPException(status_code=503, detail="Agent registry not initialized")
    
    # Calculate statistics
    categories = {}
    for agent in registry.agents.values():
        if agent.category not in categories:
            categories[agent.category] = 0
        categories[agent.category] += 1
    
    return {
        "total_agents": len(registry.agents),
        "categories": categories,
        "loaded_modules": len(registry.loaded_modules),
        "active_instances": len(registry.agent_instances),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/export")
async def export_registry():
    """Export complete registry information."""
    if not registry:
        raise HTTPException(status_code=503, detail="Agent registry not initialized")
    
    return {
        "agents": {agent_id: agent.dict() for agent_id, agent in registry.agents.items()},
        "export_timestamp": datetime.utcnow().isoformat(),
        "total_agents": len(registry.agents)
    }


def main():
    """Main entry point for the API server."""
    parser = argparse.ArgumentParser(description="AI Agents Library API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    print(f"🚀 Starting AI Agents Library API on {args.host}:{args.port}")
    print(f"📖 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🔍 Health Check: http://{args.host}:{args.port}/health")
    
    # Run the server
    uvicorn.run(
        "src.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level,
        access_log=True
    )


if __name__ == "__main__":
    main()

