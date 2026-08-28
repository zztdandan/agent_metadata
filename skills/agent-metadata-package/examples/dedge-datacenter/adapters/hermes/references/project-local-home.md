# dedge project-local Hermes home

这个目录本身就是 dedge-datacenter 项目的唯一部署态 `HERMES_HOME`。

也就是说，当你执行：

```bash
cd /home/base/repo/dedge/dedge-datacenter-harness/dedge-datacenter
HERMES_HOME=/home/base/repo/dedge/dedge-datacenter-harness/dedge-datacenter/.hermes \
  hermes chat
```

Hermes 会直接把这里当作当前唯一工作 home，而不是再去读取 `profiles/<name>/`。

## 目录边界

当前项目内 `.hermes/` 采用“单 home、无额外 profiles 嵌套”的结构：

```text
.hermes/
├── .env.example
├── .gitignore
├── README.md
├── config.yaml
├── SOUL.md
└── skills/
    ├── datacenter-agent-runtime/
    ├── datacenter-agent-catalog-maintenance/
    ├── datacenter-agent-cloud-tss-query/
    └── datacenter-agent-grafana-dashboard/
```

说明：
- `config.yaml`、`SOUL.md`、`skills/` 都直接放在 `.hermes/` 根目录。
- 不再保留 `profiles/dedge-orchestrator/` 这种二级 profile 结构，避免 HERMES_HOME 与 profile 嵌套来源冲突。
- 这套项目内 Agent 的运行身份统一声明为 `datacenter-agent`；不再要求通过 `-p dedge-orchestrator` 才生效。

## 职责裁剪

当前这套 project-local Hermes home 已按 MVP 运行面裁剪为：

- **只处理问数、看板复用/修改、catalog/currentView 写回、notify 刷新链路**
- **不是通用编码 profile**，不承担应用功能开发、代码重构、仓库级工程任务
- 保留的核心 toolset 仅覆盖：terminal、file、code_execution、browser、skills、todo、clarify、mcp-grafana
- Grafana MCP 仅保留与 dashboard 查询/读取/更新直接相关的工具白名单
- `skills/` 目录仅保留 4 个项目专用技能；其他 bundled skills 视为运行态冗余资产，应删除或忽略

## 外部 agent 记忆与占位约定

项目业务长期记忆不存放在 Hermes 私有 memory 中，而放在项目文件：

`/home/base/repo/dedge/dedge-datacenter-harness/dedge-datacenter/runtime/agent-memory/tsdb-memory.json`

该文件现在同时承载：
- Agent 运行会依赖的系统地址
- 登录权限/认证定位信息
- datasource / 时序库认知

除该文件外，其他 `.hermes/` 资产中如果需要表达这些信息，统一使用 `{agentmemory.*}` 占位：
- `{agentmemory.grafana.url}`
- `{agentmemory.backend.notifyFrontendRefreshUrl}`
- `{agentmemory.tss.dockerReachableUrl}`

禁止在其他 `.hermes/` 文件里继续写死这些地址或登录定位信息。

## 环境变量

项目本地真实运行时使用：
- `.hermes/.env`（本地存在，不可提交）

`.env.example` 只保留变量名模板。

当前本地开发时，Grafana / provider 相关环境变量应直接从个人 `~/.hermes/.env` 拷贝到这里，确保项目内运行自洽。

## 运行态与版本化

可提交内容：
- `.gitignore`
- `.env.example`
- `README.md`
- `config.yaml`
- `SOUL.md`
- `skills/` 下 4 个项目专用 skills

不得提交内容：
- `.env`
- sessions / logs / cache / memory / memories / checkpoints / backups / home / tmp / plans
- `state.db*`
- `active_profile`
- Hermes 自动生成的其他副产物

## 外接业务 memory

当前外接记忆文件除保存 datasource / 时序库认知外，也作为 `datacenter-agent` 的系统地址与认证定位总表，供 Agent 在 TSS 规划、Grafana 落板与 notify 刷新前读取。
