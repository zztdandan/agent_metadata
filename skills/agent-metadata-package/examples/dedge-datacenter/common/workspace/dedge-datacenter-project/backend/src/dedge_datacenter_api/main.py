from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, AsyncIterator
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict

from dedge_datacenter_api.catalog.service import CatalogService
from dedge_datacenter_api.config import AppSettings, build_settings

TTS_UPSTREAM_BASE = "https://zhenze-huhehaote.cmecloud.cn"
TTS_PROXY_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]


class FrontendRefreshRequest(BaseModel):
    """Payload used by the agent/backend refresh bridge."""

    model_config = ConfigDict(extra="forbid")

    reason: str
    dashboardId: str | None = None
    catalogNodeId: str | None = None
    targetClientId: str


class FrontendWsHub:
    """Very small in-memory WebSocket hub with targeted delivery."""

    def __init__(self) -> None:
        self._clients: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self._clients[client_id] = websocket

    def disconnect(self, client_id: str) -> None:
        self._clients.pop(client_id, None)

    async def send_to(self, client_id: str, payload: dict[str, Any]) -> int:
        websocket = self._clients.get(client_id)
        if websocket is None:
            return 0
        try:
            await websocket.send_json(payload)
            return 1
        except RuntimeError:
            self.disconnect(client_id)
            return 0


def create_app(
    frontend_dist_dir: str | None = None,
    catalog_path: str | None = None,
    agent_memory_path: str | None = None,
    grafana_base_url: str | None = None,
) -> FastAPI:
    """Build the MVP backend app.

    The first complete MVP slice hosts:
    - health and thin display APIs
    - file-backed catalog/currentView persistence
    - notify + websocket refresh bridge
    - static frontend serving
    - a minimal Grafana public-dashboard proxy for iframe embedding
    """

    settings = build_settings(
        frontend_dist_dir=frontend_dist_dir,
        catalog_path=catalog_path,
        agent_memory_path=agent_memory_path,
        grafana_base_url=grafana_base_url,
    )
    app = FastAPI(title="dedge datacenter api")
    app.state.settings = settings
    app.state.catalog_service = CatalogService(settings.catalog_path, settings.agent_memory_path)
    app.state.catalog_service.ensure_catalog()
    app.state.frontend_ws_hub = FrontendWsHub()

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/catalog")
    def get_catalog() -> dict[str, Any]:
        return app.state.catalog_service.get_catalog_view()

    @app.get("/api/catalog/tree")
    def get_catalog_tree() -> list[dict[str, Any]]:
        return app.state.catalog_service.get_catalog_tree()

    @app.get("/api/dashboards")
    def list_dashboards() -> list[dict[str, Any]]:
        return app.state.catalog_service.list_dashboards()

    @app.get("/api/dashboards/{dashboard_id}")
    def get_dashboard(dashboard_id: str) -> dict[str, Any]:
        dashboard = app.state.catalog_service.get_dashboard(dashboard_id)
        if dashboard is None:
            raise HTTPException(status_code=404, detail="dashboard not found")
        return dashboard

    @app.get("/api/current-view")
    def get_current_view() -> dict[str, Any] | None:
        return app.state.catalog_service.get_current_view()

    @app.post("/api/current-view")
    def update_current_view(current_view: dict[str, Any] | None) -> dict[str, Any] | None:
        return app.state.catalog_service.set_current_view(current_view)

    @app.post("/api/notify/frontend-refresh", status_code=202)
    async def notify_frontend_refresh(request: FrontendRefreshRequest) -> dict[str, Any]:
        payload = {
            "type": "frontend-refresh",
            "reason": request.reason,
            "dashboardId": request.dashboardId,
            "catalogNodeId": request.catalogNodeId,
            "targetClientId": request.targetClientId,
            "sentAt": datetime.now(UTC).isoformat(),
        }
        delivered = await app.state.frontend_ws_hub.send_to(request.targetClientId, payload)
        return {
            "accepted": True,
            "delivered": delivered,
            "targetClientId": request.targetClientId,
            "message": payload,
        }

    @app.websocket("/ws/frontend")
    async def frontend_ws(
        websocket: WebSocket,
        clientId: str | None = Query(default=None),
    ) -> None:
        client_id = clientId or str(uuid4())
        await app.state.frontend_ws_hub.connect(websocket, client_id)
        await websocket.send_json({"type": "frontend-session", "clientId": client_id})
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            app.state.frontend_ws_hub.disconnect(client_id)

    @app.api_route("/public-dashboards/{path:path}", methods=["GET", "HEAD"])
    async def proxy_grafana_public_dashboards(path: str, request: Request) -> Response:
        return await _proxy_grafana_response(settings, f"/public-dashboards/{path}", request)

    @app.api_route("/public/{path:path}", methods=["GET", "HEAD"])
    async def proxy_grafana_public_assets(path: str, request: Request) -> Response:
        return await _proxy_grafana_response(settings, f"/public/{path}", request)

    @app.api_route("/v1/audio/tts", methods=TTS_PROXY_METHODS)
    @app.api_route("/v1/audio/tts/{remainder:path}", methods=TTS_PROXY_METHODS)
    async def proxy_tts(request: Request) -> Response:
        return await _proxy_tts_response(request)

    @app.get("/{full_path:path}")
    def frontend_entry(full_path: str) -> FileResponse:
        # API routes are intentionally excluded from the SPA fallback surface.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="not found")
        return _serve_frontend_path(settings, full_path)

    return app


async def _proxy_grafana_response(settings: AppSettings, upstream_path: str, request: Request) -> Response:
    """Proxy Grafana public dashboard content through the backend.

    This strips frame-blocking headers so the thin frontend can embed the
    public dashboard path inside an iframe served from the backend origin.
    """

    upstream_url = f"{settings.grafana_base_url}{upstream_path}"
    if request.url.query:
        upstream_url = f"{upstream_url}?{request.url.query}"

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        upstream_response = await client.request(
            request.method,
            upstream_url,
            headers={k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length"}},
        )

    headers = {
        key: value
        for key, value in upstream_response.headers.items()
        if key.lower() not in {"content-length", "transfer-encoding", "connection", "x-frame-options"}
    }
    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=headers,
        media_type=upstream_response.headers.get("content-type"),
    )


async def _proxy_tts_response(request: Request) -> Response:
    """Proxy TTS requests to the upstream provider to bypass browser CORS limits.

    Forwards the original path, query string, method, body and headers to the
    upstream host and streams the response back to the client.
    """

    upstream_url = f"{TTS_UPSTREAM_BASE}{request.url.path}"
    if request.url.query:
        upstream_url = f"{upstream_url}?{request.url.query}"

    body = await request.body()
    forward_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }

    client = httpx.AsyncClient(follow_redirects=True, timeout=60.0)
    upstream_request = client.build_request(
        request.method,
        upstream_url,
        headers=forward_headers,
        content=body if body else None,
    )
    upstream_response = await client.send(upstream_request, stream=True)

    response_headers = {
        key: value
        for key, value in upstream_response.headers.items()
        if key.lower() not in {"content-length", "transfer-encoding", "connection"}
    }

    async def stream_upstream() -> AsyncIterator[bytes]:
        try:
            async for chunk in upstream_response.aiter_raw():
                yield chunk
        finally:
            await upstream_response.aclose()
            await client.aclose()

    return StreamingResponse(
        stream_upstream(),
        status_code=upstream_response.status_code,
        headers=response_headers,
        media_type=upstream_response.headers.get("content-type"),
    )


def _serve_frontend_path(settings: AppSettings, full_path: str) -> FileResponse:
    """Serve built frontend assets, falling back to index.html for SPA routes."""

    dist_dir = settings.frontend_dist_dir
    index_path = dist_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(
            status_code=503,
            detail="frontend dist not found; build frontend before starting the API server",
        )

    if full_path and full_path != "/":
        asset_path = (dist_dir / full_path).resolve()
        if asset_path.exists() and asset_path.is_file() and dist_dir.resolve() in asset_path.parents:
            return FileResponse(asset_path)

    return FileResponse(index_path)


app = create_app()
