# Hermes Adapter（Dedge Datacenter project-local home）

本 Adapter 基于 `dedge-datacenter/.hermes/` 的真实部署态编制。该源项目使用**扁平 project-local `HERMES_HOME`**：`config.yaml`、`SOUL.md` 和 `skills/` 直接在 `.hermes/` 根目录，不使用嵌套 profile。

## 包内映射

- 源 `.hermes/skills/` 已完整复制为 `common/skills/`：包括 5 个 Skill 的 `SKILL.md` 和两个技能所带的全部 `references/`。
- 源 `.hermes/SOUL.md` 已原样放入 `capabilities/datacenter-dashboard-agent/SOUL.md`，作为看板能力域的真实身份和边界。
- 源 `.hermes/README.md` 已保留为 `references/project-local-home.md`，供自举时理解该 project-local home 的目录边界、运行态排除和外接 memory 约定。
- `examples/config.yaml.example` 来自真实 `config.yaml`，但已移除源文件内联 `api_key`。provider/MCP Secret 必须通过 `key_env` 或 `${VARIABLE}` 从包外安全位置提供。
- `examples/.env.example` 是原项目的无密变量模板。

## 配置保留与脱敏原则

已保留真实配置中与能力恢复有关的非密结构：默认模型/provider 声明、`platform_toolsets.cli`、被禁用的 toolsets、Agent `max_turns`、compression/auxiliary 选择、Grafana MCP 命令、环境引用以及工具白名单。

不得将源 `.hermes/.env`、内联 API Key、认证文件、session、logs、cache、memory、state 数据库或其他运行态内容放入包或 Adapter 示例。

## 动态部署

Adapter 不规定 `AGENTS.md` 的固定宿主路径。根据目标智能体性质部署：

- Hermes：将能力域 `AGENTS.md` 映射到项目工作目录或当前版本实际读取的项目指令入口；将完整技能目录放入该 `HERMES_HOME` 的发现路径。
- Codex：将能力域 `AGENTS.md` 放入实际项目工作目录的 Codex 指令入口。
- OpenClaw：将能力域 `AGENTS.md` 放入对应 Agent 文件夹。

当宿主不支持独立 SOUL/USER/AGENTS 文件时，按身份与边界、宿主/工作区初始化约束、用户协作约定的语义顺序合并并标明来源，不得机械拼接。

## 验证

应使用目标版本 Hermes 的原生命令验证身份、技能发现、Grafana MCP、工具白名单、已设置变量状态与工作区资产可读性。仅有配置文件或能启动 Hermes 都不足以证明适配成功。
