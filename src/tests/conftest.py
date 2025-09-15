"""
Pytest configuration and shared fixtures for AI Agents Library tests.
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.main import app
from src.api.agent_registry import AgentRegistry


@pytest.fixture(scope="session")
def test_registry():
    """Create a test registry with proper agent discovery."""
    src_path = project_root / "src"
    registry = AgentRegistry(base_path=str(src_path))
    return registry


@pytest.fixture
def client(test_registry):
    """Create test client with properly initialized registry."""
    # Patch the global registry in the main module
    with patch('src.api.main.registry', test_registry):
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment with mock configuration."""
    test_env = {
        'LLM_PROVIDER': 'mock',
        'LLM_MODEL': 'test-model',
        'OPENAI_API_KEY': 'test-openai-key',
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'NOVEUM_ENABLED': 'false',
        'NOVEUM_API_KEY': 'test-noveum-key',
        'MEMORY_TYPE': 'buffer',
        'MEMORY_MAX_MESSAGES': '10',
        'MEMORY_PERSIST': 'false',
        'AGENT_NAME': 'Test Agent',
        'ENVIRONMENT': 'test'
    }
    
    with patch.dict(os.environ, test_env):
        yield


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return "This is a mock response from the test LLM."


@pytest.fixture
def sample_agent_request():
    """Sample agent request for testing."""
    return {
        "message": "Hello, this is a test message",
        "user_id": "test_user_123",
        "config_overrides": {
            "llm_config": {
                "provider": "mock",
                "temperature": 0.5
            }
        },
        "metadata": {
            "test_run": True,
            "source": "pytest"
        }
    }


@pytest.fixture
def sample_agent_response():
    """Sample agent response for testing."""
    return {
        "agent_id": "test.sample_agent",
        "response": "Hello! This is a test response.",
        "metadata": {
            "user_id": "test_user_123",
            "agent_name": "Test Agent",
            "processing_time": 0.123
        },
        "processing_time": 0.123,
        "timestamp": "2024-01-01T12:00:00Z",
        "success": True,
        "error": None
    }


@pytest.fixture
def sample_agent_info():
    """Sample agent info for testing."""
    return {
        "agent_id": "test.sample_agent",
        "name": "Sample Test Agent",
        "category": "test",
        "subcategory": "sample",
        "description": "A sample agent for testing purposes",
        "version": "1.0.0",
        "author": "Test Suite",
        "tags": ["test", "sample", "mock"],
        "module_path": "/test/path/main.py",
        "class_name": "SampleAgent",
        "config_class": "SampleAgentConfig",
        "endpoints": ["chat", "process"],
        "input_schema": {
            "message": {
                "type": "string",
                "description": "Input message"
            },
            "user_id": {
                "type": "string",
                "description": "User identifier",
                "default": "default"
            }
        },
        "output_schema": {
            "response": {
                "type": "string",
                "description": "Agent response"
            }
        },
        "dependencies": ["pytest", "mock"],
        "min_python_version": "3.8",
        "enabled": True,
        "health_status": "healthy",
        "last_health_check": "2024-01-01T12:00:00Z"
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file names
        if "test_api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        if "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        if "slow" in item.name.lower():
            item.add_marker(pytest.mark.slow)
        if not any(marker.name in ["integration", "slow", "api"] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)

