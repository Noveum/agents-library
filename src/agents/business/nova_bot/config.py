"""
Configuration for NovaBot (Noveum Docs Customer Support Bot).

All settings are defined here (hardcoded).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


def _repo_root() -> Path:
    # src/agents/business/nova_bot/config.py -> repo root
    return Path(__file__).resolve().parents[4]


@dataclass
class NovaBotConfig:
    """Runtime configuration for NovaBot."""

    agent_name: str = "NovaBot"

    # Noveum tracing (LangChain integration)
    noveum_enabled: bool = True
    noveum_api_key: str = "*****-xC"
    noveum_project: str = "NovaBot-demo"
    noveum_environment: str = "dev-Novabot"
    noveum_endpoint: str = ""

    # LLM provider (answer generation) - supports OpenAI or Gemini
    openai_api_key: str = "sk-***"
    openai_model: str = "gpt-4o-mini"
    
    # Gemini (fallback if OpenAI not set)
    gemini_api_key: str = "******-"
    gemini_model: str = "gemini-2.5-flash"

    # OpenAI embeddings (for RAG retrieval)
    openai_embedding_model: str = "text-embedding-3-small"

    # RAG data paths
    docs_json_path: str = str(_repo_root() / "NoveumDocsData" / "processed" / "docs.json")
    vectors_npy_path: str = str(_repo_root() / "NoveumDocsData" / "index" / "vectors.npy")
    index_metadata_path: str = str(_repo_root() / "NoveumDocsData" / "index" / "metadata.json")

    # Behavior
    top_k: int = 5
    temperature: float = 0.2
    max_output_tokens: int = 800

    rag_keywords: List[str] = field(
        default_factory=lambda: [
            "noveum",
            "trace",
            "traces",
            "span",
            "spans",
            "attribute",
            "attributes",
            "event",
            "events",
            "sdk",
            "python sdk",
            "noveum-trace",
            "dashboard",
            "evaluation",
            "eval",
            "scoring",
            "observability",
            "autofix",
            "api key",
        ]
    )

    @classmethod
    def from_env(cls) -> "NovaBotConfig":
        return cls()


