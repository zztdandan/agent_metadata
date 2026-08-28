from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "backend" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dedge_datacenter_api.main import create_app


def _write_frontend_dist(frontend_dist: Path) -> None:
    frontend_dist.mkdir(parents=True, exist_ok=True)
    (frontend_dist / "index.html").write_text(
        "<html><body>dedge datacenter mvp</body></html>",
        encoding="utf-8",
    )


def _write_catalog(catalog_path: Path) -> None:
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        json.dumps(
            {
                "schemaVersion": "1.0.0",
                "project": "dedge-datacenter",
                "environment": "default",
                "createdAt": None,
                "updatedAt": None,
                "currentView": None,
                "tree": [],
                "dashboards": [],
            }
        ),
        encoding="utf-8",
    )


def _build_app(frontend_dist: Path, catalog_path: Path):
    return create_app(
        frontend_dist_dir=frontend_dist,
        catalog_path=catalog_path,
        agent_memory_path=str(PROJECT_ROOT / "runtime" / "agent-memory" / "tsdb-memory.json"),
        grafana_base_url="http://grafana.test",
    )


def test_catalog_and_current_view_endpoints_return_seed_data(tmp_path: Path) -> None:
    frontend_dist = tmp_path / "frontend-dist"
    catalog_path = tmp_path / "catalog" / "dashboard-catalog.json"
    _write_frontend_dist(frontend_dist)
    _write_catalog(catalog_path)

    app = _build_app(frontend_dist, catalog_path)
    client = TestClient(app)

    catalog_response = client.get("/api/catalog")
    tree_response = client.get("/api/catalog/tree")
    current_view_response = client.get("/api/current-view")
    dashboards_response = client.get("/api/dashboards")

    assert catalog_response.status_code == 200
    assert catalog_response.json()["project"] == "dedge-datacenter"
    assert tree_response.json() == []
    assert current_view_response.json() is None
    assert dashboards_response.json() == []


def test_post_current_view_updates_backend_truth_source(tmp_path: Path) -> None:
    frontend_dist = tmp_path / "frontend-dist"
    catalog_path = tmp_path / "catalog" / "dashboard-catalog.json"
    _write_frontend_dist(frontend_dist)
    _write_catalog(catalog_path)

    app = _build_app(frontend_dist, catalog_path)
    client = TestClient(app)

    response = client.post(
        "/api/current-view",
        json={
            "catalogNodeId": "node-001",
            "dashboardId": "dash-001",
            "iframeUrl": "{agentmemory.grafana.url}/d-solo/uid-001",
            "updatedAt": "2026-07-09T00:00:00Z",
        },
    )

    assert response.status_code == 200
    assert response.json()["dashboardId"] == "dash-001"
    assert response.json()["iframeUrl"] == "http://localhost:3000/d-solo/uid-001"
    stored_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert stored_catalog["currentView"]["catalogNodeId"] == "node-001"
    assert stored_catalog["currentView"]["iframeUrl"] == "{agentmemory.grafana.url}/d-solo/uid-001"


def test_notify_endpoint_sends_refresh_only_to_target_ws_client(tmp_path: Path) -> None:
    frontend_dist = tmp_path / "frontend-dist"
    catalog_path = tmp_path / "catalog" / "dashboard-catalog.json"
    _write_frontend_dist(frontend_dist)
    _write_catalog(catalog_path)

    app = _build_app(frontend_dist, catalog_path)
    client = TestClient(app)

    with client.websocket_connect("/ws/frontend?clientId=client-a") as websocket_a:
        with client.websocket_connect("/ws/frontend?clientId=client-b") as websocket_b:
            session_a = websocket_a.receive_json()
            session_b = websocket_b.receive_json()
            assert session_a == {"type": "frontend-session", "clientId": "client-a"}
            assert session_b == {"type": "frontend-session", "clientId": "client-b"}

            response = client.post(
                "/api/notify/frontend-refresh",
                json={
                    "reason": "dashboard-created",
                    "dashboardId": "dash-001",
                    "catalogNodeId": "node-001",
                    "targetClientId": "client-b",
                },
            )

            assert response.status_code == 202
            assert response.json()["delivered"] == 1
            assert response.json()["targetClientId"] == "client-b"

            message = websocket_b.receive_json()
            assert message["type"] == "frontend-refresh"
            assert message["reason"] == "dashboard-created"
            assert message["dashboardId"] == "dash-001"
            assert message["catalogNodeId"] == "node-001"
            assert message["targetClientId"] == "client-b"

            websocket_a.send_text("ping")
            websocket_b.send_text("ping")


def test_catalog_service_persists_dashboard_and_current_view(tmp_path: Path) -> None:
    frontend_dist = tmp_path / "frontend-dist"
    catalog_path = tmp_path / "catalog" / "dashboard-catalog.json"
    _write_frontend_dist(frontend_dist)
    _write_catalog(catalog_path)

    app = _build_app(frontend_dist, catalog_path)
    service = app.state.catalog_service

    dashboard = {
        "id": "dash-001",
        "title": "电压监控",
        "status": "active",
        "directoryPath": ["电池", "电压"],
        "grafana": {
            "dashboardUid": "uid-001",
            "dashboardUrl": "{agentmemory.grafana.url}/d/uid-001",
            "iframeUrl": "{agentmemory.grafana.url}/d-solo/uid-001",
            "folder": "dedge-datacenter",
            "panelTypes": ["stat"],
        },
        "questions": {
            "original": ["看下电压"],
            "normalized": "电压监控",
            "similar": [],
        },
        "scope": {
            "products": [],
            "devices": [],
            "groups": [],
            "tags": [],
            "timeRange": "last_24h",
        },
        "modelContext": {
            "cloudCommand": "dedge cloud tm tree",
            "exploredAt": None,
            "summary": "",
            "matchedProperties": [],
        },
        "tssContext": {
            "storagePattern": "one-thing-one-table-with-tags",
            "tables": [],
            "querySummary": "",
            "lastQueryPlan": {},
        },
        "visualization": {
            "intent": "status",
            "recommendedPanel": "stat",
            "layoutSummary": "",
        },
        "usage": {
            "createdBy": "agent",
            "createdAt": None,
            "updatedAt": None,
            "lastUsedAt": None,
            "useCount": 1,
        },
        "feedback": {
            "userAccepted": False,
            "notes": [],
            "modificationHistory": [],
        },
        "tags": ["voltage"],
        "reusePolicy": {
            "preferReuseForSimilarQuestions": True,
            "doNotReuseReasons": [],
        },
    }

    service.upsert_dashboard(dashboard)
    service.set_current_view(
        {
            "catalogNodeId": "node-001",
            "dashboardId": "dash-001",
            "iframeUrl": "{agentmemory.grafana.url}/d-solo/uid-001",
            "updatedAt": "2026-07-08T00:00:00Z",
        }
    )

    stored_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    assert stored_catalog["dashboards"][0]["id"] == "dash-001"
    assert stored_catalog["dashboards"][0]["grafana"]["dashboardUrl"] == "{agentmemory.grafana.url}/d/uid-001"
    assert stored_catalog["currentView"]["dashboardId"] == "dash-001"
    assert stored_catalog["currentView"]["iframeUrl"] == "{agentmemory.grafana.url}/d-solo/uid-001"
    assert service.get_dashboard("dash-001")["grafana"]["dashboardUrl"] == "http://localhost:3000/d/uid-001"
    assert service.get_dashboard("dash-001")["title"] == "电压监控"
