from __future__ import annotations

from copy import deepcopy
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CurrentViewModel(BaseModel):
    """Thin frontend display target stored by the backend."""

    model_config = ConfigDict(extra="forbid")

    catalogNodeId: str | None = None
    dashboardId: str | None = None
    iframeUrl: str | None = None
    updatedAt: str | None = None


class CatalogModel(BaseModel):
    """Minimal MVP catalog shape used by the first backend slice."""

    model_config = ConfigDict(extra="forbid")

    schemaVersion: str = "1.0.0"
    project: str = "dedge-datacenter"
    environment: str = "default"
    createdAt: str | None = None
    updatedAt: str | None = None
    currentView: CurrentViewModel | None = None
    tree: list[dict[str, Any]] = Field(default_factory=list)
    dashboards: list[dict[str, Any]] = Field(default_factory=list)
    # Keep these extension slots explicit so the backend remains compatible
    # with the current catalog payload instead of rejecting the file.
    preferences: dict[str, Any] = Field(default_factory=dict)
    lessons: list[Any] = Field(default_factory=list)


def default_catalog_payload() -> dict[str, Any]:
    """Return a fresh empty catalog payload."""

    return deepcopy(CatalogModel().model_dump())
