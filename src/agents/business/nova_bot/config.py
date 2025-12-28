"""
Configuration for NovaBot (Noveum Docs Customer Support Bot).

Secrets are read from environment variables. Do NOT hardcode API keys.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


def _repo_root() -> Path:
    # src/agents/business/nova_bot/config.py -> repo root
    return Path(__file__).resolve().parents[4]


@dataclass
class NovaBotConfig:
    """Runtime configuration for NovaBot."""

    agent_name: str = "NovaBot"

    # Noveum tracing (LangChain integration)
    noveum_enabled: bool = True
    noveum_api_key: Optional[str] = None
    noveum_project: str = "novabot_v.1"
    noveum_environment: str = "dev-novabot"

    # LLM provider (answer generation) - supports OpenAI or Gemini
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    
    # Gemini (fallback if OpenAI not set)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"

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
        return cls(
            agent_name=os.getenv("NOVABOT_NAME", "NovaBot"),
            noveum_enabled=os.getenv("NOVEUM_ENABLED", "true").lower() == "true",
            noveum_api_key=os.getenv("NOVEUM_API_KEY"),
            noveum_project=os.getenv("NOVEUM_PROJECT", "novabot_v.1"),
            noveum_environment=os.getenv("NOVEUM_ENVIRONMENT", "dev-novabot"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            openai_embedding_model=os.getenv(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
            ),
            docs_json_path=os.getenv(
                "NOVABOT_DOCS_JSON_PATH",
                str(_repo_root() / "NoveumDocsData" / "processed" / "docs.json"),
            ),
            vectors_npy_path=os.getenv(
                "NOVABOT_VECTORS_PATH",
                str(_repo_root() / "NoveumDocsData" / "index" / "vectors.npy"),
            ),
            index_metadata_path=os.getenv(
                "NOVABOT_INDEX_METADATA_PATH",
                str(_repo_root() / "NoveumDocsData" / "index" / "metadata.json"),
            ),
            top_k=int(os.getenv("NOVABOT_TOP_K", "5")),
            temperature=float(os.getenv("NOVABOT_TEMPERATURE", "0.2")),
            max_output_tokens=int(os.getenv("NOVABOT_MAX_OUTPUT_TOKENS", "800")),
        )


