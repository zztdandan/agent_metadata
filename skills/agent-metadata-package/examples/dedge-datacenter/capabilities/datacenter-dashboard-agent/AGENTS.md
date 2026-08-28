# 工作目录约束

## 项目范围

- 项目根是 `dedge-datacenter/`，包含 `backend/`（FastAPI API、catalog/currentView、WS/notify、静态托管）、`frontend/`（Vue AgentWorkbench）、`catalog/`（看板目录与 schema）和 `runtime/agent-memory/`（外接业务记忆）。
- 此能力域只处理问数、Grafana 看板复用/修改、catalog/currentView 写回与 notify 刷新链路；不是通用编码身份。
- Grafana 看板管理归属 Agent；前端只是目录切换器与 iframe 外壳，后端只承担 catalog/currentView 持久化、静态托管、notify 与 WS 广播。

## 长期资产与读写边界

- `catalog/dashboard-catalog.json` 与 `catalog/dashboard-catalog.schema.json` 是看板目录的项目资产；写入前必须满足 schema/结构要求。
- `runtime/agent-memory/tsdb-memory.json` 是系统地址、认证定位、数据源/时序库事实的项目外接记忆；不得将等价业务事实存入宿主私有 memory。
- 在外接 memory 之外，配置或文档如需表示运行事实，使用 `{agentmemory.grafana.url}`、`{agentmemory.grafana.publicDashboardBaseUrl}`、`{agentmemory.backend.notifyFrontendRefreshUrl}`、`{agentmemory.tss.dockerReachableUrl}` 等项目约定占位，而不写死现场地址或认证。
- 运行时生成的会话、日志、缓存、私有 memory、state 数据库与 `.env` 不属于项目资产，也不得提交或覆盖。

## 项目持续性约束

- 每个看板的新建、修改、复用或归档决定都必须使 catalog 与 `currentView` 保持一致。
- catalog 写回后，必须经由后端 notify → WebSocket 广播 → 前端 axios 重新拉取实现同步；浏览器刷新不能替代该链路。
- 与数据源、物模型、TSS 或 Grafana 相关的当前事实以实时命令/API/工具结果优先；若与旧文档冲突，应报告差异。
- 运行时优先读取项目携带资产与捆绑技能；外层 Harness 文档仅在当前环境实际存在时作为补充来源。
