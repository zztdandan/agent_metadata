# 自举、适配与安全

本页说明智能体如何把一个元数据包落到当前宿主，并列出不得越过的安全边界。

## 自举流程

### 1. 先理解包

读取根 `README.md`、`metadata.json` 和 `BOOTSTRAP.md`，列出能力域、技能、MCP、环境变量、工作区资产和可用 Adapter。不得在完成理解前复制文件，也不得假定 Adapter 文档永远与包内容或当前版本一致。

### 2. 识别当前宿主

确认 Agent 实现和版本，以及它使用全局 profile 还是项目本地工作区。检查它是否支持多 Agent、技能发现、MCP、SOUL/USER/AGENTS 分文件和环境文件。Adapter 是经验，不是权威；最终依据是当前宿主的文档、配置和实际运行结果。

### 3. 与用户确定范围

向用户确认：选哪些能力域、部署到哪里、能否修改既有 Agent 配置、需要哪些外部系统权限，以及哪些配置仍缺失。未经确认不得覆盖既有配置、自动选择能力域或修改系统级设置。

### 4. 收集配置

根据 `environment.json` 收集必填项，并保存到当前环境认可的安全位置。Secret 不回显、不写入日志、不进入 Git，也不应默认写进 `.bashrc`。如果使用网页收集工具，应先说明监听地址、写入位置和退出时机。

### 5. 实施映射

- 将 SOUL、USER 和 AGENTS 按语义映射为宿主支持的身份表达。`AGENTS.md` 本身只提供能力长期生效的目录、资产和运行约束；其宿主落点由 `BOOTSTRAP.md` 与 Adapter 在部署时决定，不得把自举说明写回该 canonical 文件。
- 复制或链接完整技能目录到宿主的发现路径。
- 将 MCP 逻辑声明转换为宿主配置。直接继承的环境变量写作 `${VARIABLE_NAME}`；需要在模板中由部署流程填入的参数写作 `{{VARIABLE_NAME}}`。
- 对每个选定的工作区资产，将 `common/workspace/<asset-name>/` 下的**内容**复制到目标工作区根目录；不得额外创建 `<asset-name>/` 嵌套目录。目标中同路径内容已存在时先比较，并由自举智能体结合当前宿主、项目状态和用户授权处理。
- 应用结构化合并修改配置，不得简单文本追加。

### 6. 证明它真的可用

完成后必须验证：身份和边界已生效、技能能被宿主实际发现或加载、MCP 已连接、必填变量已设置但未泄漏值、工作区资产在实际使用位置且可读取，启动方式可复现。文件存在不等于自举成功。

## 宿主适配知识

Adapter 目录只记录已知经验，应包含已验证版本、能力域映射、技能发现路径、MCP 与环境变量配置、工作区位置、验证方法和已知限制。



对 Hermes 可用 `HERMES_HOME=<target> hermes chat -q "..."` 做身份、技能和 MCP 冒烟测试。对 OpenCode，可使用 `opencode debug config` 与 `opencode debug skill --print-logs` 查看配置和技能发现状态。命令只是示例，仍应以当前版本可用的命令为准。

## 环境变量与 Secret

环境契约位于 `common/environment/environment.json`。每项包含变量名、类型、是否必填、用途、消费者以及可选的示例、默认值和校验规则。

```json
{
  "variables": [
    {
      "name": "GRAFANA_URL",
      "kind": "url",
      "required": true,
      "description": "Grafana 服务地址",
      "example": "http://127.0.0.1:3000",
      "consumers": ["mcp.grafana"]
    },
    {
      "name": "GRAFANA_SERVICE_ACCOUNT_TOKEN",
      "kind": "secret",
      "required": true,
      "description": "Grafana Service Account Token",
      "consumers": ["mcp.grafana"]
    }
  ]
}
```

支持的 `kind` 为 `secret`、`url`、`path`、`string`、`integer`、`boolean` 和 `choice`。`secret` 仅可做非空检查，且不得提供默认值或真实示例。

`.env.example` 仅作为变量名模板。Secret 用 `***` 占位；普通配置可以给示例值。真实值应放在包外的安全位置，例如权限为 `0600` 且被 Git 忽略的项目 `.env`、系统凭证管理器或宿主的凭证存储。

验证时仅可报告状态，例如 `GRAFANA_SERVICE_ACCOUNT_TOKEN — 已设置`。不得打印部分脱敏值，也不得展开完整配置。

## 工作区资产

工作区资产是项目运行需要的文件或目录，不通过技能发现或 MCP 连接加载，例如 memory、catalog、模板和配置种子。根清单只登记资产目录：`common/workspace/<asset-name>/` 的 `<asset-name>` 就是资产 ID，表示需要这一份资产。部署时将该目录下的**内容**复制到目标工作区根目录；资产目录本身不是目标目录名。

默认策略是 `copy`：逐项比较资产目录内容与工作区根目录中的对应相对路径；目标不存在时复制，内容相同则跳过，内容不同时由自举智能体结合当前宿主、项目状态和用户授权处理。复制后会被项目持续修改的资产属于项目，后续升级不得覆盖，卸载也不得删除。

资产里可有模板、占位符和 schema，不得有真实 Secret、密码、API Key 或用户机器绝对路径。建议的目标路径由 Adapter 给出，不得硬编码在跨宿主的元数据里。

## 可选 helpers

`helpers/` 中的脚本是可选辅助工具，不登记在 `metadata.json`，也不决定包是否合法。智能体应主动扫描该目录，检查脚本是否适合当前系统、宿主、字段集合和写入目标，再决定使用、改造或绕过。

例如 `configuration-web` 可给不熟悉配置文件的用户提供本地表单。它必须只监听 `127.0.0.1`，不得把 Secret 放进 URL 或日志，不得默认修改 `.bashrc`，写入文件后必须设为 `0600`，并应在提交后退出。

## 禁止事项

自举过程中不得：

1. 输出、记录或提交 Secret。
2. 未经确认覆盖用户配置或可变工作区资产。
3. 删除用户已有的 memory、会话或运行状态。
4. 把 `dist/` 测试目录当作正式部署目标。
5. 虚构宿主能力，或只凭文件存在宣称成功。
6. 修改全局 shell 配置，除非用户明确同意。
7. 拆散技能目录，或静默执行业务脚本。

打包排除、静态检查和最终验收见[发布与验证](03-release-and-verification.md)。

## 环境、工作区、Adapter 与交付补充

`environment.json` 的每个变量有如下字段：


| 字段            | 类型 / 是否必填          | 规则                                                                            |
| ------------- | ------------------ | ----------------------------------------------------------------------------- |
| `name`        | `string`，必填        | 大写下划线变量名。                                                                     |
| `kind`        | `string`，必填        | `secret`、`url`、`path`、`string`、`integer`、`boolean` 或 `choice`。                |
| `required`    | `boolean`，必填       | 是否必须提供。                                                                       |
| `description` | `string`，必填        | 面向人的用途说明。                                                                     |
| `example`     | `string`，可选        | `secret` 不得有真实示例。                                                             |
| `default`     | 任意类型，可选            | `secret` 不得有默认值。                                                              |
| `consumers`   | `array<string>`，可选 | 消费者格式为 `<type>.<id>`，如 `provider.deepseek`、`mcp.grafana`、`workspace.backend`。 |
| `validation`  | `object`，可选        | 可使用 `minLength`、`maxLength`、`pattern`、`min`、`max`、`enum`。                     |


收集建议：`secret` 使用不回显输入并只做非空检查；`url` 检查 URL 格式；`path` 可检查路径存在；`string` 在必填时检查非空；`integer` 检查整数；`boolean` 只接收 `true` / `false`；`choice` 必须落在给定枚举内。

完整示例：

```json
{
  "variables": [
    {
      "name": "DEEPSEEK_API_KEY",
      "kind": "secret",
      "required": true,
      "description": "DeepSeek API Key",
      "consumers": ["provider.deepseek"]
    },
    {
      "name": "MONA_API_KEY",
      "kind": "secret",
      "required": true,
      "description": "Mona API Key",
      "consumers": ["provider.mona"]
    },
    {
      "name": "GRAFANA_URL",
      "kind": "url",
      "required": true,
      "description": "Grafana 服务地址",
      "example": "http://127.0.0.1:3000",
      "consumers": ["mcp.grafana"]
    },
    {
      "name": "GRAFANA_SERVICE_ACCOUNT_TOKEN",
      "kind": "secret",
      "required": true,
      "description": "Grafana Service Account Token",
      "consumers": ["mcp.grafana"]
    },
    {
      "name": "BACKEND_PORT",
      "kind": "integer",
      "required": false,
      "description": "后端服务端口",
      "default": 8000,
      "consumers": ["workspace.backend"]
    }
  ]
}
```

`.env.example` 可安全提交；它仅保留变量名、占位符和非 Secret 示例值：

```dotenv
# === Provider Keys ===
DEEPSEEK_API_KEY=***
MONA_API_KEY=***

# === Grafana MCP ===
GRAFANA_URL=
GRAFANA_SERVICE_ACCOUNT_TOKEN=***

# === Backend ===
BACKEND_PORT=8000
```

环境信息分三层保存：`environment.json` 声明变量、`.env.example` 提供无密模板、包外安全位置保存真实值。真实值可以放在权限为 `0600` 且被 Git 忽略的项目 `.env`、系统凭证管理器、宿主凭证存储或用户指定的安全位置。它们不能进入元数据包、Git、日志、Shell 历史或默认的 `.bashrc`。

MCP 的 `${...}` 环境变量引用、模板中的 `{{...}}` 参数格，以及能力域子清单的 `environment` 都必须对应已声明变量。验证只输出“已设置 / 未设置”，例如：

```text
✓ DEEPSEEK_API_KEY — 已设置
✓ GRAFANA_URL — 已设置
✗ GRAFANA_SERVICE_ACCOUNT_TOKEN — 未设置
```

不得输出值，即使是部分脱敏后的值。

## 已知的安全迁移点

dedge-datacenter 曾在 `.hermes/config.yaml` 出现明文 provider key（`api_key: <真实值>`）。迁移时应改为 `key_env: DEEPSEEK_API_KEY`，把真实值写入被忽略的 `.hermes/.env`，并在环境契约中将 `DEEPSEEK_API_KEY` 声明为 `secret`。已盘点变量还包括 `MONA_API_KEY`、`GRAFANA_URL`、`GRAFANA_SERVICE_ACCOUNT_TOKEN` 和 `MCP_GRAFANA_API_KEY`；它们分别服务 provider 或 Grafana MCP。

### 工作区资产

工作区资产位于 `common/workspace/<asset-name>/`；`<asset-name>` 就是根清单的资产 ID，表示“需要使用这一份资产”。每个资产目录的**内容**复制到目标工作区根目录，不把资产目录本身作为额外层级带入目标。示例：

```text
common/workspace/
├── tsdb-memory/                  # asset ID: tsdb-memory
│   └── runtime/agent-memory/
│       ├── tsdb-memory.json
│       └── README.md
├── catalog/                      # asset ID: catalog
│   └── catalog/
│       ├── dashboard-catalog.json
│       └── dashboard-catalog.schema.json
└── handler-template/             # asset ID: handler-template
    └── templates/
        └── example_handler.lua
```

对选定资产，将整个资产目录的内容按相对路径复制到工作区根目录。例如 `tsdb-memory/runtime/agent-memory/tsdb-memory.json` 落为 `<workspace>/runtime/agent-memory/tsdb-memory.json`，而不是 `<workspace>/tsdb-memory/...`。目标中对应路径不存在时复制，内容一致时跳过，内容不同时由自举智能体结合当前宿主、项目状态和用户授权处理。选定能力域不需要某资产，或 Adapter 明确说明宿主不需要它时，可不部署。

建议位置如下，最终路径仍由当前宿主和项目结构决定：


| 宿主                    | 建议位置                              |
| --------------------- | --------------------------------- |
| Hermes（project-local） | `<project>/runtime/agent-memory/` |
| Hermes（global）        | `~/.hermes/runtime/agent-memory/` |
| OpenCode              | `<project>/runtime/agent-memory/` |


资产可含示例、模板、schema，以及统一约定的两类引用：运行时环境变量写作 `${GRAFANA_URL}`，部署时要填入的参数格写作 `{{GRAFANA_API_KEY}}`。`{agentmemory.grafana.url}` 是既有项目约定，不属于元数据协议；迁移时应保留并在 Adapter 中说明其解析方。资产不得带真实地址、API Key、密码或用户绝对路径。

`tsdb-memory.json` 是特殊例子：它可能同时记录系统地址、认证定位和时序库认知。包内只保留结构与占位符；复制到项目后再由用户或智能体填写现场信息。历史映射还包括 `catalog/dashboard-catalog.json` 和 `catalog/dashboard-catalog.schema.json`，两者共同组成 `catalog` 资产。

### Adapter 与 helpers 的维护规则

每份 Adapter README 应写明：已验证版本和状态、已知不兼容场景、能力域映射、技能发现机制和 frontmatter 要求、MCP 配置与工具白名单能力、环境变量加载、工作区位置、验证命令、已知限制，以及 `examples/` 下的脱敏参考配置。

- `verified` 需要真实版本验证记录；Agent 升级后未复验，应降为 `experimental`。
- `research_required` 仅可说明需要研究的装载机制、配置入口、技能路径和 MCP 支持，不得写未经验证的具体步骤，也不得被当作已可用方案展示。
- Adapter 与 `BOOTSTRAP.md` 冲突时，后者的安全边界优先。
- Adapter 不应包含编译脚本、固定安装命令序列、真实凭证、机器绝对路径或未来版本承诺。

`helpers/configuration-web/` 是面向不熟悉配置文件用户的表单参考实现，目录由 `README.md`、`app.py`、`templates/` 和 `static/` 组成。运行前检查操作系统、宿主变量加载机制、写入目标、字段集合和写入权限。它不是唯一配置方式，也不保证无需修改就适配所有环境。

该 helper 应仅监听 `127.0.0.1`，使用密码输入框，不把 Secret 放入 URL 或日志，不默认写 `.bashrc`，写入目标由自举智能体指定并设为 `0600`，提交后允许自动退出。未来可增加 `validate-references.py`、`scan-secrets.py` 或 `inspect-package.py`；它们同样可选，不能替代智能体的判断。

### 交付、升级与验证细节

交付报告应包含：最终工作区位置、选定能力域、已安装技能、已配置 MCP、新增或修改的文件、尚缺事项、敏感信息保存位置（不含值）、启动方法、验证结果、能力降级和后续重新自举或迁移方式。

重复自举时，应先检查目标是否有旧产物。已有且被用户修改的工作区资产不得覆盖；技能和身份文件应先检查用户修改，再由自举智能体结合当前宿主、项目状态和用户授权决定处置；配置应使用结构化合并；不得删除 memory、会话或运行状态。

验证用例建议放在如下位置：

```text
evaluations/
├── README.md
├── capability-discovery/
│   ├── identity-check.md
│   └── boundary-check.md
├── skill-discovery/
│   ├── skill-list.md
│   └── skill-load.md
└── mcp-connectivity/
    ├── grafana-connect.md
    └── tool-whitelist.md
```

每个用例写验证目标、前置条件、执行步骤、预期结果和脱敏要求。用例类型可为 `capability-discovery`、`skill-discovery`、`mcp-connectivity` 和 `workspace-asset`。

可参考以下宿主命令：

```bash
# Hermes
HERMES_HOME=<target> hermes chat -q "列出你当前可用的 skills"
HERMES_HOME=<target> hermes chat -q "检查 grafana MCP 是否可用，只返回一句话结论"
HERMES_HOME=<target> hermes chat -q "你的身份是什么？只返回一句话"
HERMES_HOME=<target> hermes chat -q "读取 tsdb-memory 文件并报告当前默认数据源"

# OpenCode
opencode debug config
opencode debug skill --print-logs
opencode debug config | grep agent
```

Pi 和 DeepSeek Harness 在锁定版本前不提供验证命令。

不接受以下成功结论：仅检查文件存在；配置写入后 Agent 无法启动；Agent 启动但技能未发现；技能已发现但 MCP 未连接；环境变量未设置却跳过验证；输出泄漏 Secret；未做第四层宿主原生发现；或发生降级却未报告。