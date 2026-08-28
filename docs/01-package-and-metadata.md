# 包结构与元数据

本页定义 `agent_metadata` 的目录布局、根与能力域子 `metadata.json`，以及资产的注册方式。它回答两个问题：包里应放什么，智能体如何找到它。

## 目录布局

```text
agent_metadata/
├── metadata.json                 # 根清单
├── README.md                      # 人类入口
├── BOOTSTRAP.md                   # 面向自举智能体的规约
├── LICENSE                       # 可选：发布或分发时应提供
├── schema/
│   └── metadata.schema.json       # 必需：根清单的 JSON Schema
├── common/
│   ├── skills/<skill-id>/         # 完整技能目录
│   │   ├── SKILL.md
│   │   ├── references/
│   │   ├── scripts/
│   │   └── assets/
│   ├── mcp/<mcp-id>.json          # MCP 逻辑需求
│   ├── environment/
│   │   ├── environment.json       # 变量契约
│   │   └── .env.example
│   ├── workspace/<asset-name>/    # 一个资产一个目录；目录内容复制到工作区根目录
│   └── references/                # 只读参考资料
├── capabilities/<capability-id>/
│   ├── metadata.json              # 能力域子清单
│   ├── SOUL.md
│   ├── USER.md
│   └── AGENTS.md
├── adapters/<agent-id>/
│   ├── README.md
│   └── examples/
├── helpers/                       # 可选辅助工具，不登记
├── evaluations/                   # 验证用例，不登记
└── dist/                          # 测试沙箱，正式发布时排空
```

最小合法包必须包含根 `metadata.json`、`README.md`、`BOOTSTRAP.md`、`schema/metadata.schema.json`，以及至少一个含四个文件的能力域目录。`LICENSE`、`common/`、`adapters/`、`helpers/`、`evaluations/` 和 `dist/` 可选；发布或分发包时应提供 `LICENSE`。

## 根 metadata.json

根清单描述包的全貌：包身份、能力域、共享资产、可参考的 Adapter 和发布排除规则。

```json
{
  "schemaVersion": "0.1",
  "package": {
    "id": "dedge-agent-metadata",
    "version": "0.1.0",
    "name": "Dedge Agent Metadata",
    "description": "dedge 组织智能体元数据包"
  },
  "capabilities": [
    { "id": "datacenter-agent", "path": "capabilities/datacenter-agent" }
  ],
  "skills": [
    { "id": "datacenter-agent-runtime", "path": "common/skills/datacenter-agent-runtime" }
  ],
  "mcp": [
    { "id": "grafana", "path": "common/mcp/grafana.json" }
  ],
  "environment": {
    "contract": "common/environment/environment.json",
    "example": "common/environment/.env.example"
  },
  "workspaceAssets": [
    { "id": "tsdb-memory", "path": "common/workspace/tsdb-memory" }
  ],
  "adapters": [
    { "id": "hermes", "path": "adapters/hermes", "status": "verified" }
  ],
  "bootstrap": "BOOTSTRAP.md",
  "distribution": {
    "exclude": ["dist/**", "**/.env", "**/sessions/**", "**/logs/**", "**/state.db*"]
  }
}
```

| 字段 | 要求 | 含义 |
|---|---|---|
| `schemaVersion` | 必填，字符串 | 元数据协议版本；当前为 `"0.1"`。 |
| `package` | 必填，对象 | 包的 `id`、内容版本，以及可选名称和说明。`id` 用小写连字符；`version` 用语义化版本。 |
| `capabilities` | 必填，至少一项 | 能力域 ID 与相对目录。 |
| `skills` / `mcp` | 可选，数组 | 共享资产 ID 与相对路径。技能以完整目录、MCP 以声明文件为单位。 |
| `workspaceAssets` | 可选，数组 | 工作区资产 ID 与相对路径；资产目录名必须等于资产 ID，部署时复制其目录内容到工作区根目录。 |
| `environment` | 可选，对象 | 环境契约与 `.env.example` 的路径。 |
| `adapters` | 可选，数组 | 适配知识的 ID、目录和状态。 |
| `bootstrap` | 必填，字符串 | 自举规约路径，固定为 `BOOTSTRAP.md`。 |
| `distribution.exclude` | 可选，字符串数组 | 发布时排除的 glob。 |

Adapter 状态可为：`verified`（已在真实版本验证）、`experimental`（有资料但验证不足）、`research_required`（仅占位，需现场研究）和 `unsupported`（已知不支持）。

## 能力域与子 metadata.json

能力域说明“这个专家是谁、遵守什么规则、需要哪些资产”，不拥有技能或工作区资产。它包含：

- `SOUL.md`：身份、使命、价值取舍和硬性边界；应保持简短，不应写成技能手册。
- `USER.md`：用户画像、协作偏好和交互约定。
- `AGENTS.md`：工作区规则、工程约束和运行规程。
- `metadata.json`：引用本能力域所需资产。

```json
{
  "capabilityId": "datacenter-agent",
  "skills": ["datacenter-agent-runtime", "datacenter-agent-grafana-dashboard"],
  "mcp": ["grafana"],
  "workspaceAssets": ["tsdb-memory"],
  "environment": ["DEEPSEEK_API_KEY", "GRAFANA_URL", "GRAFANA_SERVICE_ACCOUNT_TOKEN"]
}
```

子清单中的每个技能、MCP 和工作区资产 ID 都必须已在根清单登记；`environment` 中的变量必须已在 `environment.json` 声明。缺少引用时应停止自举并报告问题。

不同宿主可把能力域表达成独立 Agent、单一入口内的组合规则、preset 或项目指令文件。若宿主不能分开加载 SOUL、USER 和 AGENTS，应按语义合并：先放身份与边界，再放工作规程，最后放用户协作约定。不得把三份文件直接首尾拼接。

能力域与技能、MCP、工作区资产和环境变量都是多对多关系。一个能力域可以不引用技能，也可以与其他能力域共享同一份技能。

## 资产的放置与处理

| 资产 | 位置 | 登记方式 | 处理方式 |
|---|---|---|---|
| 技能 | `common/skills/<id>/` | 根 + 子清单 | 复制整个目录；不得只复制 `SKILL.md`。 |
| MCP 声明 | `common/mcp/<id>.json` | 根 + 子清单 | 转换成当前宿主的配置格式。 |
| 环境契约 | `common/environment/` | 根 + 子清单 | 引用变量名，不保存真实值。 |
| 工作区资产 | `common/workspace/<asset-name>/` | 根 + 子清单 | 目录名即资产 ID，登记该目录表示需要这份资产；将其**目录内容**复制到目标工作区根目录。目标中同路径内容已存在且不同则报告冲突。 |
| 通用参考 | `common/references/` | 不登记 | 只读，不部署。 |
| Adapter 知识 | `adapters/<id>/` | 根清单 | 只读；以实际宿主行为为准。 |
| helpers / evaluations / dist | 各自目录 | 不登记 | 分别用于可选辅助、验证和测试。 |

技能的 `SKILL.md` 应带有 `name` 和 `description` 的 YAML frontmatter；`name` 与根清单的技能 ID 保持一致。技能中的脚本属于技能私有内容。安装时可提示来源和路径，但不得静默执行业务脚本。

工作区资产只登记到文件夹级别，且 `common/workspace/<asset-name>/` 的目录名就是资产 ID（例如 `common/workspace/tsdb-memory/` 对应 `tsdb-memory`）。登记该目录表示选择整份资产；部署时复制其**内容**到目标工作区根目录，而不是将资产目录本身再嵌套一层复制过去。复制后持续变化的资产（例如现场 memory）归项目管理，升级和卸载均不得静默覆盖或删除。

MCP 文件保存逻辑需求，例如命令、环境变量映射和工具白名单，而不是 Hermes、OpenCode 等宿主的原始配置片段。真实 Secret、绝对路径、运行状态、技能内部文件列表和宿主专有配置均不得登记进 `metadata.json`。

## 文件与目录命名

- ID 用小写连字符：`datacenter-agent`、`iot-stream-processor`、`grafana`。
- 根和子清单都叫 `metadata.json`。
- 能力域文件固定为 `SOUL.md`、`USER.md`、`AGENTS.md`。
- 技能入口固定为 `SKILL.md`，人类入口固定为 `README.md`。

发布、敏感配置和宿主适配规则见[自举、适配与安全](02-bootstrap-and-security.md)。静态校验和发布验收见[发布与验证](03-release-and-verification.md)。


## 补充字段细节、MCP 与现有项目映射


| 位置                            | 用途                                                 |
| ----------------------------- | -------------------------------------------------- |
| `metadata.json`               | 机器可读根清单；自举智能体首先读取它，了解包身份、能力域、共享资产、Adapter 和发布排除规则。 |
| `README.md`                   | 给维护者和使用者看的入口、文档索引和阅读路径。                            |
| `BOOTSTRAP.md`                | 给自举智能体看的结果规约；规定必须达到的结果和安全边界，不固定工具或命令。              |
| `LICENSE`                     | 可选；发布或分发时说明资产的使用、修改和分发许可。                         |
| `schema/metadata.schema.json` | `metadata.json` 的 JSON Schema；最小合法包必需。             |
| `common/`                     | 多个能力域共享的框架无关资产。                                    |
| `capabilities/`               | 能力域目录；每个目录存身份文件和子清单。                               |
| `adapters/`                   | 已知宿主的适配知识与脱敏示例；不是安装模板。                             |
| `helpers/`                    | 可选辅助工具；不在 `metadata.json` 登记。                      |
| `evaluations/`                | 验证用例；不在 `metadata.json` 登记。                        |
| `dist/`                       | 自举测试沙箱；不属于 canonical 资产。                           |


`common/` 下的 `skills/`、`mcp/`、`environment/`、`workspace/` 和 `references/` 分别保存技能、MCP 逻辑声明、环境契约、项目资产和只读资料。`references/` 不部署。

### 命名规则

- 能力域、技能和 MCP ID 使用小写连字符，例如 `datacenter-agent`、`iot-stream-processor`、`grafana`。
- 工作区资产按资产目录组织，目录名即资产 ID，例如 `tsdb-memory/`、`catalog/`；每个资产目录的内容落到目标工作区根目录。
- 固定文件名为 `metadata.json`、`SOUL.md`、`USER.md`、`AGENTS.md`、`SKILL.md`、`README.md` 和 `BOOTSTRAP.md`。

## 根与子清单的字段细节

### 根 metadata.json


| 字段                | 类型 / 是否必填               | 规则                                                                 |
| ----------------- | ----------------------- | ------------------------------------------------------------------ |
| `schemaVersion`   | `string`，必填             | 元数据协议版本；当前为 `"0.1"`，与资产版本独立。                                       |
| `package`         | `object`，必填             | `id`（必填，小写连字符）、`version`（必填，语义化版本）、`name` 和 `description`（可选）。     |
| `capabilities`    | `array<object>`，必填且至少一项 | 每项含必填的 `id` 和 `path`；根清单不展开能力域内部资产。                                |
| `skills`          | `array<object>`，可选      | 每项含必填的 `id` 和技能目录 `path`。                                          |
| `mcp`             | `array<object>`，可选      | 每项含必填的 `id` 和 MCP 声明文件 `path`。                                     |
| `environment`     | `object`，可选             | `contract` 与 `example` 都是必填路径，分别指向变量契约和 `.env.example`。            |
| `workspaceAssets` | `array<object>`，可选      | 每项含必填的 `id` 与目录 `path`；只能登记目录，不能登记单个文件。目录名必须等于 `id`，目录内容部署到工作区根目录。 |
| `adapters`        | `array<object>`，可选      | 每项含 `id`、`path` 和 `status`。                                        |
| `bootstrap`       | `string`，必填             | 固定为 `"BOOTSTRAP.md"`。                                              |
| `distribution`    | `object`，可选             | `exclude` 是必填的 `array<string>`，保存发布排除 glob。                        |


子清单中的 `capabilityId` 为必填字符串，且必须等于根清单中登记的能力域 ID。`skills`、`mcp`、`workspaceAssets` 和 `environment` 都是可选的字符串数组；前三者引用根清单 ID，最后一个引用 `environment.json` 中的变量名。

不得在清单中登记 helpers、Adapter 内具体配置片段、真实 Secret、用户绝对路径、宿主专有配置、运行状态或技能内部文件清单。技能以整个目录作为黑盒搬运单元。

### 参数与环境变量引用

包内配置统一使用两种显式引用，避免把“等着填写的参数”和“运行时读取的环境变量”混在一个对象里：


| 写法                   | 含义                | 何时解析                               |
| -------------------- | ----------------- | ---------------------------------- |
| `${VARIABLE_NAME}`   | 当前运行环境必须提供的环境变量。  | 由宿主、shell 或其环境加载机制在运行时解析。          |
| `{{PARAMETER_NAME}}` | 部署或自举时必须填入模板的参数格。 | 自举智能体收集后写入目标配置；Secret 不回显，也不写进公共包。 |


名称使用大写下划线。`{{...}}` 不得嵌套，变量名或参数名不得含空格。二者都必须在 `environment.json` 的 `variables` 中声明：`kind`、`required`、`description` 和 `consumers` 仍是事实来源。`{{...}}` 仅可出现在模板或工作区资产中，不得保留在最终可运行的宿主配置里；`${...}` 仅可用于明确支持环境变量展开的宿主字段。

同一个声明可同时定义两者：例如 `GRAFANA_URL` 作为运行时环境变量，`GRAFANA_API_KEY` 作为部署时录入的 Secret。最终使用哪种写法由 Adapter 和宿主能力决定，不得根据字段名猜测。

### MCP 声明

MCP 文件描述逻辑需求，不保存宿主原始配置。环境变量直接写成 `${VARIABLE_NAME}`，不再使用“声明来源 + 重复变量名”的对象包装：

```json
{
  "id": "grafana",
  "transport": "stdio",
  "command": "mcp-grafana",
  "args": [],
  "environment": {
    "GRAFANA_URL": "${GRAFANA_URL}",
    "GRAFANA_SERVICE_ACCOUNT_TOKEN": "${GRAFANA_SERVICE_ACCOUNT_TOKEN}"
  }
}
```

`command` 是期望执行的命令；`environment` 只能引用环境契约中的变量；`tools` 是可选字段。仅当元数据包编制人明确希望限制工具使用范围时，才声明 `tools.include` 白名单，例如：

```json
{
  "tools": {
    "include": ["search_dashboards", "get_dashboard_by_uid", "update_dashboard"]
  }
}
```

未声明 `tools` 时，自举智能体不得擅自缩小工具范围。Hermes 将它转换为 `config.yaml` 的 `mcp_servers`，OpenCode 转为其 MCP 配置。不支持 MCP 的宿主必须记录降级，而不是假装已接入。

### 技能、依赖与可执行内容

一个技能目录必须包含 `SKILL.md`，并可带 `references/`、`scripts/`、`assets/`。`SKILL.md` 使用如下 frontmatter：

```yaml
---
name: <skill-id>
description: <一句话描述，用于触发判断>
---
```

`name` 与根清单登记的技能 ID 一致。技能可以在正文声明依赖，例如涉及 dedge CLI 的 flags 或 JSON I/O 时依赖 `dedge-cli-common`，发现 `<prefix>_schema_selector`、`<prefix>_schema`、`<prefix>_content` 字段族时依赖 `dedge-schema-content`。自举时应一并安装依赖。

技能可能带 Python、Go 等可执行内容。安装计划应列出其来源和路径；不得静默执行这些业务脚本，也不要把它们提升为宿主全局工具。

## 能力域的组合与映射

能力域不是“角色实体”，而是身份、边界和资产引用的轻量单元。这样宿主可以把它表达为独立 Agent、总入口中的一部分、preset 或项目指令文件，而不改变资产所有权。

当宿主不支持分开的 SOUL、USER 和 AGENTS 时，应按下列顺序合并并标明来源，不得直接拼接：

```markdown
# <能力域名称>

## 身份与边界
（来自 SOUL.md）

## 工作规程
（来自 AGENTS.md）

## 用户协作
（来自 USER.md）
```

一个包可以只部署一个能力域，也可以把多个能力域分别部署为多个 Agent 或组合为一个 Agent。组合时保留每个能力域的身份和边界；重复的技能、MCP 和工作区资产各安装或配置一次。

能力域与技能、MCP、工作区资产、环境变量均为多对多关系。能力域可以不引用任何技能；技能也可以被多个能力域共享。

### 现有项目资产映射


| 原项目资产                                                   | 目标位置或处理                                                |
| ------------------------------------------------------- | ------------------------------------------------------ |
| `src/builtin/agents/dedge-cloud-thingmodel.md`          | `capabilities/dedge-cloud-thingmodel/SOUL.md`，保留身份和边界。 |
| `src/builtin/skills/dedge-cloud-thingmodel/`            | `common/skills/dedge-cloud-thingmodel/`。               |
| `src/builtin/skills/dedge-cloud-te/reference/ontology/` | `common/skills/dedge-cloud-te/references/ontology/`。   |
| `.hermes/SOUL.md`                                       | `capabilities/datacenter-agent/SOUL.md`。               |
| `.hermes/config.yaml` 内 MCP 声明                          | `common/mcp/grafana.json`。                             |
| `.hermes/config.yaml` 的 provider / `key_env`            | `common/environment/environment.json`。                 |
| `runtime/agent-memory/tsdb-memory.json`                 | `common/workspace/tsdb-memory/runtime/agent-memory/`。                       |
| `opencode.json` 插件配置                                    | 不进入包；属于 Adapter 适配知识。                                  |
| `src/plugin-factory.ts` 插件代码                            | 不进入包；属于派生产物。                                           |


已盘点的能力域包括 `datacenter-agent`、`iot-stream`、`dedge-cloud-thingmodel`、`dedge-cloud-te` 与 `dedge-cloud-component`。其中 `iot-stream` 的 SOUL 来源为 `src/builtin/agents/iot-stream.md`；其余云侧能力域对应 `src/builtin/agents/` 下同名 Agent 文件。
