"""
Agent Registry System for Dynamic Agent Discovery and Loading.

This module provides a centralized registry for all available agents,
allowing the FastAPI application to dynamically discover, load, and
invoke agents based on their configuration.
"""

import os
import sys
import json
import importlib.util
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    agent_id: str
    name: str
    category: str
    subcategory: str
    description: str
    version: str
    author: str
    tags: List[str]
    
    # Technical details
    module_path: str
    class_name: str
    config_class: str
    
    # API details
    endpoints: List[str]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    
    # Requirements
    dependencies: List[str]
    min_python_version: str
    
    # Status
    enabled: bool = True
    health_status: str = "unknown"
    last_health_check: Optional[str] = None


class AgentRegistry:
    """
    Central registry for managing and discovering AI agents.
    
    This class automatically discovers agents in the repository structure,
    loads their metadata, and provides methods to instantiate and invoke them.
    """
    
    def __init__(self, base_path: str = None):
        """Initialize the agent registry."""
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.agents: Dict[str, AgentInfo] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self.agent_instances: Dict[str, Any] = {}
        
        # Discover and register all agents
        self._discover_agents()
    
    def _discover_agents(self):
        """Discover all agents in the repository structure."""
        print("🔍 Discovering agents in repository...")
        
        # Define agent directory patterns for src/agents structure
        agent_patterns = [
            "agents/basic/*/",
            "agents/business/*/",
            "agents/technical/*/",
            "agents/creative/*/",
            "agents/specialized/*/"
        ]
        
        for pattern in agent_patterns:
            agent_dirs = list(self.base_path.glob(pattern))
            for agent_dir in agent_dirs:
                if self._is_valid_agent_directory(agent_dir):
                    try:
                        agent_info = self._load_agent_metadata(agent_dir)
                        if agent_info:
                            self.agents[agent_info.agent_id] = agent_info
                            print(f"✅ Registered agent: {agent_info.agent_id}")
                    except Exception as e:
                        print(f"⚠️  Failed to register agent in {agent_dir}: {e}")
        
        print(f"📋 Total agents registered: {len(self.agents)}")
    
    def _is_valid_agent_directory(self, agent_dir: Path) -> bool:
        """Check if a directory contains a valid agent."""
        required_files = ["main.py", "config.py", "requirements.txt"]
        return all((agent_dir / file).exists() for file in required_files)
    
    def _load_agent_metadata(self, agent_dir: Path) -> Optional[AgentInfo]:
        """Load agent metadata from directory."""
        try:
            # Try to load metadata from agent_info.yaml first
            metadata_file = agent_dir / "agent_info.yaml"
            if metadata_file.exists():
                return self._load_metadata_from_file(metadata_file, agent_dir)
            
            # Otherwise, infer metadata from directory structure and files
            return self._infer_agent_metadata(agent_dir)
            
        except Exception as e:
            print(f"❌ Error loading metadata for {agent_dir}: {e}")
            return None
    
    def _load_metadata_from_file(self, metadata_file: Path, agent_dir: Path) -> AgentInfo:
        """Load agent metadata from YAML file."""
        with open(metadata_file, 'r') as f:
            data = yaml.safe_load(f)
        
        return AgentInfo(
            agent_id=data['agent_id'],
            name=data['name'],
            category=data['category'],
            subcategory=data.get('subcategory', ''),
            description=data['description'],
            version=data.get('version', '1.0.0'),
            author=data.get('author', 'Unknown'),
            tags=data.get('tags', []),
            module_path=str(agent_dir / "main.py"),
            class_name=data.get('class_name', 'Agent'),
            config_class=data.get('config_class', 'AgentConfig'),
            endpoints=data.get('endpoints', ['chat', 'process']),
            input_schema=data.get('input_schema', {}),
            output_schema=data.get('output_schema', {}),
            dependencies=self._load_dependencies(agent_dir),
            min_python_version=data.get('min_python_version', '3.8'),
            enabled=data.get('enabled', True)
        )
    
    def _infer_agent_metadata(self, agent_dir: Path) -> AgentInfo:
        """Infer agent metadata from directory structure and files."""
        # Parse directory path to get category and subcategory
        parts = agent_dir.relative_to(self.base_path).parts
        
        if len(parts) >= 2:
            category = parts[0].replace('-agents', '')
            if len(parts) >= 3:
                subcategory = parts[1]
                agent_name = parts[2]
            else:
                subcategory = ''
                agent_name = parts[1]
        else:
            category = 'unknown'
            subcategory = ''
            agent_name = parts[0] if parts else 'unknown'
        
        # Generate agent ID
        agent_id = f"{category}.{subcategory}.{agent_name}" if subcategory else f"{category}.{agent_name}"
        agent_id = agent_id.replace('-', '_')
        
        # Try to extract description from README
        description = self._extract_description_from_readme(agent_dir)
        
        # Infer class names based on common patterns
        class_name = self._infer_class_name(agent_dir)
        config_class = self._infer_config_class(agent_dir)
        
        return AgentInfo(
            agent_id=agent_id,
            name=agent_name.replace('-', ' ').title(),
            category=category,
            subcategory=subcategory,
            description=description,
            version="1.0.0",
            author="Noveum",
            tags=[category, subcategory] if subcategory else [category],
            module_path=str(agent_dir / "main.py"),
            class_name=class_name,
            config_class=config_class,
            endpoints=['chat', 'process'],
            input_schema={
                "message": {"type": "string", "description": "Input message"},
                "user_id": {"type": "string", "description": "User identifier", "default": "default"},
                "config": {"type": "object", "description": "Agent configuration overrides", "default": {}}
            },
            output_schema={
                "response": {"type": "string", "description": "Agent response"},
                "metadata": {"type": "object", "description": "Response metadata"}
            },
            dependencies=self._load_dependencies(agent_dir),
            min_python_version="3.8",
            enabled=True
        )
    
    def _extract_description_from_readme(self, agent_dir: Path) -> str:
        """Extract description from README file."""
        readme_file = agent_dir / "README.md"
        if readme_file.exists():
            try:
                with open(readme_file, 'r') as f:
                    content = f.read()
                
                # Look for the first paragraph after the title
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('#') and not line.startswith('```'):
                        return line.strip()
                
                return "AI Agent Template"
            except Exception:
                pass
        
        return "AI Agent Template"
    
    def _infer_class_name(self, agent_dir: Path) -> str:
        """Infer the main agent class name from the main.py file."""
        main_file = agent_dir / "main.py"
        if main_file.exists():
            try:
                with open(main_file, 'r') as f:
                    content = f.read()
                
                # Look for class definitions that likely represent the main agent
                import re
                class_matches = re.findall(r'class\s+(\w+Agent)\s*\(', content)
                if class_matches:
                    return class_matches[0]
                
                # Fallback to any class that contains "Agent"
                class_matches = re.findall(r'class\s+(\w*Agent\w*)\s*\(', content)
                if class_matches:
                    return class_matches[0]
                
            except Exception:
                pass
        
        return "Agent"
    
    def _infer_config_class(self, agent_dir: Path) -> str:
        """Infer the configuration class name from the config.py file."""
        config_file = agent_dir / "config.py"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                
                # Look for config class definitions
                import re
                class_matches = re.findall(r'class\s+(\w+Config)\s*\(', content)
                if class_matches:
                    return class_matches[0]
                
            except Exception:
                pass
        
        return "AgentConfig"
    
    def _load_dependencies(self, agent_dir: Path) -> List[str]:
        """Load dependencies from requirements.txt."""
        req_file = agent_dir / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    lines = f.readlines()
                
                dependencies = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        dependencies.append(line)
                
                return dependencies
            except Exception:
                pass
        
        return []
    
    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """Get information about a specific agent."""
        return self.agents.get(agent_id)
    
    def list_agents(self, category: str = None, enabled_only: bool = True) -> List[AgentInfo]:
        """List all registered agents, optionally filtered by category."""
        agents = list(self.agents.values())
        
        if category:
            agents = [agent for agent in agents if agent.category == category]
        
        if enabled_only:
            agents = [agent for agent in agents if agent.enabled]
        
        return agents
    
    def get_categories(self) -> List[str]:
        """Get all available agent categories."""
        return list(set(agent.category for agent in self.agents.values()))
    
    def load_agent_module(self, agent_id: str) -> Optional[Any]:
        """Dynamically load an agent module."""
        if agent_id in self.loaded_modules:
            return self.loaded_modules[agent_id]
        
        agent_info = self.get_agent_info(agent_id)
        if not agent_info:
            return None
        
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(
                f"agent_{agent_id}", 
                agent_info.module_path
            )
            module = importlib.util.module_from_spec(spec)
            
            # Add the agent directory to sys.path temporarily
            agent_dir = Path(agent_info.module_path).parent
            if str(agent_dir) not in sys.path:
                sys.path.insert(0, str(agent_dir))
            
            spec.loader.exec_module(module)
            
            self.loaded_modules[agent_id] = module
            return module
            
        except Exception as e:
            print(f"❌ Failed to load agent module {agent_id}: {e}")
            return None
    
    def create_agent_instance(self, agent_id: str, config_overrides: Dict[str, Any] = None) -> Optional[Any]:
        """Create an instance of the specified agent."""
        if agent_id in self.agent_instances:
            return self.agent_instances[agent_id]
        
        module = self.load_agent_module(agent_id)
        if not module:
            return None
        
        agent_info = self.get_agent_info(agent_id)
        if not agent_info:
            return None
        
        try:
            # Get the agent class
            agent_class = getattr(module, agent_info.class_name)
            config_class = getattr(module, agent_info.config_class)
            
            # Create configuration
            if config_overrides:
                # Apply configuration overrides
                config = config_class.from_env()
                for key, value in config_overrides.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            else:
                config = config_class.from_env()
            
            # Create agent instance
            agent_instance = agent_class(config)
            
            self.agent_instances[agent_id] = agent_instance
            return agent_instance
            
        except Exception as e:
            print(f"❌ Failed to create agent instance {agent_id}: {e}")
            return None
    
    def health_check_agent(self, agent_id: str) -> Dict[str, Any]:
        """Perform health check on an agent."""
        agent_info = self.get_agent_info(agent_id)
        if not agent_info:
            return {"status": "error", "message": "Agent not found"}
        
        try:
            # Try to create an instance
            agent = self.create_agent_instance(agent_id)
            if not agent:
                return {"status": "error", "message": "Failed to create agent instance"}
            
            # Check if agent has required methods
            required_methods = ['chat', 'process'] if hasattr(agent, 'chat') else ['handle_support_request']
            
            for method in required_methods:
                if not hasattr(agent, method):
                    return {"status": "error", "message": f"Missing required method: {method}"}
            
            # Update health status
            agent_info.health_status = "healthy"
            agent_info.last_health_check = str(Path(__file__).stat().st_mtime)
            
            return {"status": "healthy", "message": "Agent is operational"}
            
        except Exception as e:
            agent_info.health_status = "unhealthy"
            return {"status": "error", "message": str(e)}
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the agent registry."""
        total_agents = len(self.agents)
        enabled_agents = len([a for a in self.agents.values() if a.enabled])
        categories = self.get_categories()
        
        category_counts = {}
        for category in categories:
            category_counts[category] = len([a for a in self.agents.values() if a.category == category])
        
        return {
            "total_agents": total_agents,
            "enabled_agents": enabled_agents,
            "loaded_modules": len(self.loaded_modules),
            "active_instances": len(self.agent_instances),
            "categories": categories,
            "category_counts": category_counts
        }
    
    def export_registry(self) -> Dict[str, Any]:
        """Export the complete registry as a dictionary."""
        return {
            "agents": {agent_id: asdict(info) for agent_id, info in self.agents.items()},
            "stats": self.get_registry_stats()
        }


# Global registry instance
_registry = None

def get_registry() -> AgentRegistry:
    """Get the global agent registry instance."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry

