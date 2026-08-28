from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class AppSettings(BaseModel):
    """Runtime settings for the MVP backend."""

    model_config = ConfigDict(frozen=True)

    frontend_dist_dir: Path
    catalog_path: Path
    agent_memory_path: Path
    grafana_base_url: str


def build_settings(
    frontend_dist_dir: Path | str | None = None,
    catalog_path: Path | str | None = None,
    agent_memory_path: Path | str | None = None,
    grafana_base_url: str | None = None,
) -> AppSettings:
    """Create settings with project-local default paths."""

    project_root = Path(__file__).resolve().parents[3]

    if frontend_dist_dir is None:
        frontend_dist_dir = project_root / "frontend" / "dist"
    else:
        frontend_dist_dir = Path(frontend_dist_dir)
    if catalog_path is None:
        catalog_path = project_root / "catalog" / "dashboard-catalog.json"
    else:
        catalog_path = Path(catalog_path)
    if agent_memory_path is None:
        configured_agent_memory_path = os.environ.get("DEDGE_AGENT_MEMORY_PATH") or os.environ.get("DEDGE_TSDB_MEMORY_PATH")
        if configured_agent_memory_path:
            agent_memory_path = Path(configured_agent_memory_path)
        else:
            agent_memory_path = project_root / "runtime" / "agent-memory" / "tsdb-memory.json"
    else:
        agent_memory_path = Path(agent_memory_path)
    if grafana_base_url is None:
        grafana_base_url = (
            os.environ.get("GRAFANA_URL") or _read_agent_memory_value(agent_memory_path, "grafana.url") or ""
        ).rstrip("/")
    if not grafana_base_url:
        raise ValueError(
            "grafana_base_url is required; set GRAFANA_URL or populate grafana.url in runtime/agent-memory/tsdb-memory.json"
        )

    return AppSettings(
        frontend_dist_dir=frontend_dist_dir,
        catalog_path=catalog_path,
        agent_memory_path=agent_memory_path,
        grafana_base_url=grafana_base_url,
    )


def _read_agent_memory_value(agent_memory_path: Path, dotted_path: str) -> str | None:
    """Read a simple dotted value from the external agent memory file."""

    if not agent_memory_path.exists():
        return None

    memory = json.loads(agent_memory_path.read_text(encoding="utf-8"))
    current: object = memory
    for segment in dotted_path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return None
        current = current[segment]
    return current if isinstance(current, str) else None
