from __future__ import annotations

import json
import re
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from dedge_datacenter_api.catalog.models import CatalogModel, CurrentViewModel, default_catalog_payload

_AGENT_MEMORY_PATTERN = re.compile(r"\{agentmemory\.([^{}]+)\}")


class CatalogService:
    """File-backed catalog service for the MVP backend.

    The service is intentionally simple: one JSON file is the source of truth.
    Every write is validated by pydantic and persisted atomically.
    """

    def __init__(self, catalog_path: Path, agent_memory_path: Path) -> None:
        self.catalog_path = catalog_path
        self.agent_memory_path = agent_memory_path

    def ensure_catalog(self) -> dict[str, Any]:
        """Create the empty catalog on first use and return it."""

        if self.catalog_path.exists():
            return self.load_catalog()
        catalog = default_catalog_payload()
        self.save_catalog(catalog)
        return catalog

    def load_catalog(self) -> dict[str, Any]:
        """Load and validate the catalog from disk."""

        raw = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        return CatalogModel.model_validate(raw).model_dump()

    def save_catalog(self, catalog: dict[str, Any]) -> dict[str, Any]:
        """Validate then atomically write the catalog."""

        validated = CatalogModel.model_validate(catalog).model_dump()
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(
            "w",
            delete=False,
            dir=self.catalog_path.parent,
            encoding="utf-8",
        ) as tmp_file:
            json.dump(validated, tmp_file, ensure_ascii=False, indent=2)
            tmp_file.write("\n")
            tmp_path = Path(tmp_file.name)

        tmp_path.replace(self.catalog_path)
        return validated

    def get_catalog_view(self) -> dict[str, Any]:
        """Return a placeholder-resolved view for API consumers."""

        return self._resolve_placeholders(self.ensure_catalog())

    def list_dashboards(self) -> list[dict[str, Any]]:
        return self.get_catalog_view()["dashboards"]

    def get_dashboard(self, dashboard_id: str) -> dict[str, Any] | None:
        for dashboard in self.get_catalog_view()["dashboards"]:
            if dashboard.get("id") == dashboard_id:
                return dashboard
        return None

    def get_catalog_tree(self) -> list[dict[str, Any]]:
        return self.get_catalog_view()["tree"]

    def get_current_view(self) -> dict[str, Any] | None:
        return self.get_catalog_view()["currentView"]

    def upsert_dashboard(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Insert or replace a dashboard by id."""

        catalog = self.ensure_catalog()
        dashboards = catalog["dashboards"]
        dashboard_id = entry["id"]

        for idx, existing in enumerate(dashboards):
            if existing.get("id") == dashboard_id:
                dashboards[idx] = entry
                break
        else:
            dashboards.append(entry)

        saved = self.save_catalog(catalog)
        resolved_saved = self._resolve_placeholders(saved)
        return next(item for item in resolved_saved["dashboards"] if item.get("id") == dashboard_id)

    def set_current_view(self, current_view: dict[str, Any] | None) -> dict[str, Any] | None:
        """Replace the current thin-frontend display target."""

        catalog = self.ensure_catalog()
        if current_view is None:
            catalog["currentView"] = None
        else:
            catalog["currentView"] = CurrentViewModel.model_validate(current_view).model_dump()
        saved = self.save_catalog(catalog)
        return self._resolve_placeholders(saved["currentView"])

    def _load_agent_memory(self) -> dict[str, Any]:
        """Best-effort load of the external agent memory file."""

        if not self.agent_memory_path.exists():
            return {}
        return json.loads(self.agent_memory_path.read_text(encoding="utf-8"))

    def _resolve_placeholders(self, value: Any) -> Any:
        """Recursively resolve {agentmemory.*} placeholders for API reads only."""

        agent_memory = self._load_agent_memory()
        return _resolve_placeholder_value(value, agent_memory)


def _resolve_placeholder_value(value: Any, agent_memory: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {key: _resolve_placeholder_value(child, agent_memory) for key, child in value.items()}
    if isinstance(value, list):
        return [_resolve_placeholder_value(item, agent_memory) for item in value]
    if isinstance(value, str):
        return _AGENT_MEMORY_PATTERN.sub(lambda match: _lookup_placeholder(match.group(1), agent_memory), value)
    return value


def _lookup_placeholder(dotted_path: str, agent_memory: dict[str, Any]) -> str:
    current: Any = agent_memory
    for segment in dotted_path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return f"{{agentmemory.{dotted_path}}}"
        current = current[segment]
    return current if isinstance(current, str) else f"{{agentmemory.{dotted_path}}}"
