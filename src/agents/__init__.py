"""
AI Agents Package

Contains all agent implementations organized by category.
"""

from typing import Dict, List, Any

# Agent categories
AGENT_CATEGORIES = {
    "basic": "Simple foundational AI agents",
    "business": "Business domain specific agents", 
    "technical": "Technical and development agents",
    "creative": "Creative and content generation agents",
    "specialized": "Domain-specific specialized agents"
}

def get_available_categories() -> List[str]:
    """Get list of available agent categories."""
    return list(AGENT_CATEGORIES.keys())

def get_category_description(category: str) -> str:
    """Get description for a specific category."""
    return AGENT_CATEGORIES.get(category, "Unknown category")

