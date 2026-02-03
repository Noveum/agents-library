"""
Configuration for NovaBot Simulator.

The simulator reuses NovaBotConfig for the underlying agent configuration
and adds simulator-specific settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Import NovaBotConfig to reuse its configuration
def _load_novabot_config():
    import importlib.util
    import sys
    from pathlib import Path

    config_path = Path(__file__).resolve().parent.parent / "nova_bot" / "config.py"
    spec = importlib.util.spec_from_file_location("novabot_config", config_path)
    if not spec or not spec.loader:
        raise ImportError(f"Unable to load NovaBot config from {config_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_novabot_config_mod = _load_novabot_config()
NovaBotConfig = _novabot_config_mod.NovaBotConfig


def _repo_root() -> Path:
    # src/agents/business/nova_bot_simulator/config.py -> repo root
    return Path(__file__).resolve().parents[4]


@dataclass
class SimulatorConfig:
    """Runtime configuration for NovaBot Simulator."""

    # Simulator-specific settings
    num_sessions: int = 100
    messages_per_session: int = 3
    adversarial_ratio: float = 0.2  # 20% adversarial questions
    output_file: str = str(_repo_root() / "nova_bot_simulator_results.json")
    parallel: bool = True
    metadata_json_path: str = str(_repo_root() / "NoveumDocsData" / "index" / "metadata.json")
    docs_json_path: str = str(_repo_root() / "NoveumDocsData" / "processed" / "docs.json")

    # Reuse NovaBotConfig for agent configuration
    # We'll create a NovaBotConfig instance from env vars
    @classmethod
    def from_env(cls) -> "SimulatorConfig":
        """Load configuration from local defaults."""
        return cls()

    def get_novabot_config(self) -> NovaBotConfig:
        """Get NovaBotConfig instance from environment variables."""
        return NovaBotConfig.from_env()

