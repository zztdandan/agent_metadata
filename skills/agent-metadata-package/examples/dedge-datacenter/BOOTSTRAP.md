# 自举规约

自举智能体必须先读取根清单、选定能力域、环境契约和 `adapters/hermes/README.md`。确认目标宿主、工作区、用户授权范围与必填变量后才可生成或修改宿主产物。

1. 完整复制每个选定 skill 目录；不得只复制 `SKILL.md`。
2. 将完整的 `dedge-datacenter-project` 工作区资产内容复制到目标工作区根目录。它包含 `backend/`、`frontend/`、`catalog/`、`runtime/`、README 与项目 `.gitignore`；目标已有不同内容时，必须报告冲突，不得静默覆盖。
3. 将 `grafana.json` 转换为当前宿主支持的 MCP 配置，并仅使用环境变量引用 Secret。
4. `runtime/agent-memory/tsdb-memory.json` 在包内是无密 schema/占位模板；真实系统地址、认证定位和数据源信息应在包外的项目安全配置中维护。
5. 根据目标智能体性质，将 capability 的 `AGENTS.md` 部署或映射到实际加载的 Agent 说明文件或项目初始化文档；任务流程由完整 skill 目录提供。
6. 运行四层验收：包静态验证、生成物验证、安装状态验证和宿主原生发现验证。

不得从源项目复制 `.hermes/.env`、真实 `config.yaml` 凭证、会话/日志/缓存，或包含真实地址与认证信息的现场 memory。仅在四层均通过时报告自举成功。
