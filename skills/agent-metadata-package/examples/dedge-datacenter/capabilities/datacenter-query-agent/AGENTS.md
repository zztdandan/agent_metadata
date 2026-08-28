# 工作目录约束

## 项目事实与范围

- 工作目录中的 `dedge-datacenter/` 是数据中心 MVP：`backend/` 提供 API、catalog/currentView、WS/notify 和静态页面；`frontend/` 是 Vue AgentWorkbench；`catalog/` 是看板资产；`runtime/agent-memory/` 是外接业务事实。
- 当前能力域处理数据查询、状态、趋势和排名；不承担无关的应用开发或仓库级重构。

## 持久化与安全边界

- `runtime/agent-memory/tsdb-memory.json` 是系统地址、认证定位和 datasource/时序库认知的项目事实入口。长期业务事实应保存在该项目资产或 catalog，而不保存在宿主私有 memory。
- 除外接 memory 外，禁止在项目指令、技能或配置中写死 Cloud、Grafana、backend、frontend、TSS 的现场地址与认证定位；使用项目的 `{agentmemory.*}` 约定或环境变量引用。
- `.env`、会话、日志、缓存、宿主私有 memory、状态数据库均不是项目资产。

## 当前运行假设与事实优先级

- 当前 MVP 可以以一个主时序数据源上下文开始，但这只是可演进假设；数据源到物模型的真实路由必须由实时结果确认。
- 权威顺序：实时命令/API/工具结果 → 项目捆绑技能与配置 → 项目 catalog/外接 memory → 当前环境实际存在的外层设计文档。
- 完整技能目录是此能力域的任务知识来源；项目目录中不保存任务步骤的重复副本。
