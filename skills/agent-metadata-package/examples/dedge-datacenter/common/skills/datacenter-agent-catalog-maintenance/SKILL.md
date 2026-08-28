---
name: datacenter-agent-catalog-maintenance
description: Maintain dedge dashboard assets, tree references, currentView, and post-write notify discipline.
---

# dedge catalog maintenance

Use this skill before creating dashboards and after every dashboard change.

## Rules

1. Catalog is the first lookup surface for dashboard requests.
2. The catalog file path is `dedge-datacenter/catalog/dashboard-catalog.json`.
3. Treat `dashboards` as asset metadata and `tree` as navigation/reference structure. Do not reverse-bind one dashboard asset to only one tree path.
4. A tree node may reference a dashboard asset through `dashboardId`; future reuse across multiple tree nodes is allowed.
5. Keep dashboard assets minimal. For MVP, preserve only what helps locate, understand, and render the asset:
   - `id`
   - `title`
   - `description`
   - `grafana.dashboardUid`
   - `grafana.dashboardUrl`
   - optional `grafana.dashboardShareUrl` for debugging/manual review
   - `grafana.iframeUrl`
   - `tags`
   - `updatedAt`
6. Keep `currentView` synchronized with the dashboard/iframe the thin frontend should currently display.
7. `currentView.catalogNodeId` should point at the actual tree node id that the frontend should highlight.
8. Prefer `POST /api/current-view` to persist currentView when the backend is running, so the backend remains the truth owner for display state.
9. Validate JSON structure before writing.
10. For Grafana-backed dashboards, `iframeUrl` must be the public dashboard render link. `dashboardShareUrl` may be retained for debugging, but login-gated `d-solo` links must not be used as iframe truth.
11. Catalog write-back is not finished until the backend notify endpoint `POST {agentmemory.backend.notifyFrontendRefreshUrl}` has been called so frontend WS consumers can re-fetch by axios.
12. The notify payload must include `targetClientId`; it should also include `reason`, and when available `dashboardId` plus `catalogNodeId`.
13. Use business/use-case tags only. Avoid dialogue-process tags that do not help humans or agents filter dashboard assets by business meaning.
14. **Cross-verify catalog claims against live Grafana state.** The catalog is not the source of truth — Grafana is. Dashboards evolve in Grafana independently (panel count, titles, time ranges, tags change), and the catalog goes stale silently. When reusing or inspecting a dashboard, always call `get_dashboard_summary(uid)` first. Compare: title, panel count, panel titles, tags, time range. If the catalog disagrees with Grafana, Grafana wins — update the catalog immediately.
15. **Tree structure must reflect dashboard scope, not historical naming.** A dashboard covering CUR, TEMP, VOL, SOC, SOH, FAN, MAX_HIS, and CHARGE must not be filed under a narrow tree node like "验收 > 电池 > VOL". Restructure the tree so the node name describes what the dashboard actually contains ("全量复用(多Panel)" or similar). Stale narrow nodes that misrepresent dashboard scope must be removed.
16. **Tree grouping must come from Grafana folder structure, never invented.** Grafana organizes dashboards into folders (queryable via `GET /api/folders` and visible as `folderTitle`/`folderId` on each dashboard in `GET /api/search`). The catalog tree must mirror Grafana's actual folder hierarchy. If all dashboards are in the Grafana root folder (folderId=0, no folderTitle), the catalog tree must be flat — do NOT invent directory groupings like "电池监控"/"系统监控" based on dashboard content or tags. Only create catalog directory nodes that correspond 1:1 to real Grafana folders.
17. **Dashboard tags must be copied verbatim from Grafana.** The `tags` field in each catalog dashboard asset must exactly match the `tags` array returned by Grafana's dashboard API (`GET /api/dashboards/uid/<uid>` → `dashboard.tags`). Do not add inferred/semantic tags (e.g. "battery", "temperature", "system", "monitoring") that do not exist in Grafana. If Grafana returns `tags: []`, the catalog must record `tags: []`.
18. **All URLs in the catalog must use `{agentmemory.*}` placeholders, never hardcoded IPs.** This is mandated by the SOUL hard-prohibition and is enforced by the backend's placeholder resolver (`service.py` → `_resolve_placeholders`). The catalog file on disk stores `{agentmemory.grafana.url}/d/<uid>/<slug>` and `{agentmemory.grafana.publicDashboardBaseUrl}/<accessToken>`; the backend resolves these to real URLs at API-read time. Hardcoding `http://172.16.8.149:3000/...` directly in the catalog file violates the SOUL boundary and couples the catalog to a specific deployment IP. Verify with `grep -c '172\.16' dashboard-catalog.json` → must be 0.
19. **Dashboard asset fields must stay minimal per rule 5.** Do not add fields like `publicDashboardAccessToken` to the `grafana` object — the access token is already embedded in the `iframeUrl` placeholder path. The backend Pydantic model (`CatalogModel` in `backend/src/.../catalog/models.py`) uses `extra="forbid"` on `CurrentViewModel` but `dashboards`/`tree` are `list[dict]`, so extra fields won't be rejected — discipline must come from the agent.
20. **Validate catalog against backend Pydantic model before writing.** Run: `cd backend && .venv/bin/python -c "import json,sys; sys.path.insert(0,'src'); from dedge_datacenter_api.catalog.models import CatalogModel; CatalogModel(**json.load(open('../catalog/dashboard-catalog.json')))"` — must print PASS with no exception.
21. **Backend source code is the authority for catalog schema.** When in doubt about the correct catalog format, read `backend/src/dedge_datacenter_api/catalog/models.py` (Pydantic models) and `backend/tests/test_catalog_api.py` (real usage examples including placeholder format) before writing.
22. **写入 dashboard-catalog.json 时必须参考 dashboard-catalog.schema.json 的格式要求。** 在写入 catalog 之前，先读取 `dedge-datacenter/catalog/dashboard-catalog.schema.json`，确保字段名、类型、必填项、枚举值等与 schema 定义一致。

## Pitfalls

- **Stale catalog metadata**: A dashboard that started as a single-stat VOL panel may have grown to 8 panels without the catalog being updated. Symptom: catalog says "1 stat panel, 24h range" but `get_dashboard_summary` returns 8 panels with a 5m range. Fix: query Grafana, update catalog title/description/tags/tree to match reality.
- **Misleading tree paths**: A tree node like "电池 > VOL" pointing at a dashboard that covers current, temperature, fan settings, and charge cycles is wrong. Restructure the tree so the node name reflects the dashboard's actual scope. Do not preserve stale narrow tree paths just because they used to be accurate.
- **Fabricated directory groupings**: Inventing catalog directory nodes (e.g. "电池监控", "系统监控") that have no corresponding Grafana folder creates data inconsistency. Grafana is the truth source for grouping. Always query `GET /api/folders` and check `folderTitle` on each dashboard via `GET /api/search` before building the tree. If Grafana has no folders (all root), the tree must be flat.
- **Invented tags**: Adding semantic tags to catalog dashboard assets that don't exist in Grafana (e.g. "battery", "system") pollutes tag-based filtering with false data. Tags must be copied verbatim from `GET /api/dashboards/uid/<uid>` → `dashboard.tags`.

## Thin frontend contract

The frontend only:
- switches directory entries
- shows current dashboard detail
- embeds iframe URLs
- re-fetches after WS signals

Do not design catalog writes around page-side editing features.

## Authority

1. Live catalog file shape and backend API behavior in the deployed project.
2. This bundled skill and the bundled runtime skill inside `dedge-datacenter/.hermes/`.
3. Project asset files inside `dedge-datacenter/`.
4. Harness-root docs only when they are present in the current environment.
