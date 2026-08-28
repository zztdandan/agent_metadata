from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "backend" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dedge_datacenter_api.main import create_app


def _build_app(frontend_dist: Path):
    return create_app(frontend_dist_dir=frontend_dist, grafana_base_url="http://grafana.test")


def test_health_endpoint_reports_ok(tmp_path: Path) -> None:
    frontend_dist = tmp_path / "frontend-dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<html><body>ok</body></html>", encoding="utf-8")

    app = _build_app(frontend_dist)
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_frontend_index_when_dist_exists(tmp_path: Path) -> None:
    frontend_dist = tmp_path / "frontend-dist"
    frontend_dist.mkdir()
    index_html = "<html><body>dedge datacenter mvp</body></html>"
    (frontend_dist / "index.html").write_text(index_html, encoding="utf-8")

    app = _build_app(frontend_dist)
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "dedge datacenter mvp" in response.text


def test_static_asset_path_serves_real_asset_file(tmp_path: Path) -> None:
    frontend_dist = tmp_path / "frontend-dist"
    assets_dir = frontend_dist / "assets"
    assets_dir.mkdir(parents=True)
    (frontend_dist / "index.html").write_text("<html><body>index</body></html>", encoding="utf-8")
    (assets_dir / "app.js").write_text("console.log('asset-ok')", encoding="utf-8")

    app = _build_app(frontend_dist)
    client = TestClient(app)

    response = client.get("/assets/app.js")

    assert response.status_code == 200
    assert "asset-ok" in response.text


def test_root_returns_service_unavailable_when_frontend_dist_missing(tmp_path: Path) -> None:
    frontend_dist = tmp_path / "missing-dist"

    app = _build_app(frontend_dist)
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "frontend dist not found; build frontend before starting the API server"
    }
