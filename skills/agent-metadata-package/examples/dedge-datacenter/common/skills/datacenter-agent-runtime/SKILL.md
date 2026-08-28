---
name: datacenter-agent-runtime
description: 运行 dedge datacenter MVP 主流程：优先查 catalog，规划 Cloud/TSS 查询，经 Grafana MCP 改板后回写 catalog/currentView，并通知后端定向刷新前端。
---

# dedge 编排运行时

当用户提出自然语言物联网数据问题、要求创建/修改/复用 Grafana 看板，或询问 dedge MVP 执行流程时，使用本技能。

本 profile 不是通用编码助手。除非是保持问数 / 改板闭环所必需的运行资产维护，否则不要接手应用功能开发、代码重构或一般性工程实现任务。

## 工作流

1. 在任何新看板动作之前，先读取/搜索 `dedge-datacenter/catalog/dashboard-catalog.json`。
2. **若 catalog 命中已有看板，先交叉验证：** 通过 Grafana MCP `get_dashboard_summary(uid)` 对比面板数、标题、标签、时间范围。Grafana 是最终真相源——catalog 可能因看板独立演进而过时。若不一致，以 Grafana 为准并立即修正 catalog（参考 `datacenter-agent-catalog-maintenance` 技能规则 14-15）。
3. 在规划 TSS 查询之前，先读取项目外接记忆文件 `dedge-datacenter/runtime/agent-memory/tsdb-memory.json`，获取稳定的数据源/运行时事实。
4. 先判断请求类型：复用已有看板、修改已有看板、新建看板、解释现有看板、维护 catalog。
5. 如果是新建或大改，先确认当前 Cloud 物模型事实，再规划 TSS。
6. 在内部补齐语义槽位：`intent`、`metric`、`entity`、`timeRange`、`aggregation`、`groupBy`、`sort`、`limit`、`threshold`、`compareWith`、`vizIntent`。
7. 如果关键槽位仍有歧义，只问一个简洁澄清问题。
8. 执行命令前，先给出 TSS 查询计划。
9. 执行后必须检查真实结果，再通过 Grafana MCP 创建/更新看板。
10. 每次看板改动后，先获取并核验 Grafana 公开分享信息：公开 `iframeUrl={agentmemory.grafana.publicDashboardBaseUrl}/<accessToken>`，以及可选调试入口 `dashboardShareUrl`。
11. 回写 catalog 时，遵守最小资产模型：
   - `dashboards` 记录资产
   - `tree` 记录导航结构与 `dashboardId` 引用
   - 不要把 dashboard 资产反向绑定唯一目录路径
   - 以 `description` 作为主要文字说明，而不是恢复 `questions/scope/modelContext/tssContext/feedback` 一类冗余字段
12. 更新 `currentView`；确保 `currentView.catalogNodeId` 与真实 tree 节点 id 一致。若后端 API 可用，优先使用 `POST /api/current-view` 持久化当前展示目标。
13. 在通知前端前，先从当前浏览器会话或操作员提供的信息中拿到目标页面的 WS 客户端标识 `clientId`。
14. 调用后端通知接口 `POST {agentmemory.backend.notifyFrontendRefreshUrl}`；如果 API 实际运行在其他端口，先以 agent memory 为准并探测真实端口。
15. 通知 payload 必须包含 `reason` 与 `targetClientId`；有条件时还应携带 `dashboardId` 与 `catalogNodeId`。
16. 始终把前端视为“薄壳”：只负责目录切换与 iframe 展示，不要假设页面具备编辑能力。
17. 验收时优先看文本/日志/JSON，但对本地 Grafana 页面最终必须做 browser/web/vision 级别核验：只有 iframe 中肉眼可见 Grafana 内容才算通过；仅仅存在 iframe 节点或返回 HTTP 200 不算通过。

## 外接记忆路径

不要把数据源/运行时事实写入 Hermes 私有 memory，应使用项目文件：

`dedge-datacenter/runtime/agent-memory/tsdb-memory.json`

当前 MVP 假设：
- 只有一个主时间序列数据源上下文
- 该数据源默认覆盖当前全部物模型

## 权威来源

1. 当前部署项目中的实时命令/API/工具输出。
2. `dedge-datacenter/.hermes/` 下本技能及同级 bundled skills。
3. `dedge-datacenter/` 内项目资产文件，例如 catalog 与外接记忆。
4. 仅当当前环境确实存在时，才把 harness 根目录 docs 作为补充参考。
