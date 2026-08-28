# 环境契约、MCP 与安全边界

环境契约只声明变量，不保存真实值。MCP 文件描述逻辑需求，不保存 Hermes、OpenCode 等宿主的最终配置。

## environment.json

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

每项必须有 `name`、`kind`、`required`、`description`。可选字段是 `example`、`default`、`consumers`、`validation`。

支持的 `kind`：`secret`、`url`、`path`、`string`、`integer`、`boolean`、`choice`。

- `secret` 不得有默认值或真实示例；验证只能检查是否设置。
- `choice` 应使用 `validation.enum` 约束。
- `consumers` 使用 `<type>.<id>`，如 `mcp.grafana`、`workspace.backend`。

`.env.example` 仅提供变量名和安全占位符：

```dotenv
GRAFANA_URL=http://127.0.0.1:3000
GRAFANA_SERVICE_ACCOUNT_TOKEN=***
```

真实值只可保存在包外、受访问控制且被 Git 忽略的位置。验证报告只输出“已设置/未设置”，不得输出完整值或部分脱敏值。

## 两类引用

| 写法 | 含义 | 解析时机 |
|---|---|---|
| `${VARIABLE_NAME}` | 当前运行环境必须提供的变量 | 由支持环境展开的宿主字段在运行时解析。 |
| `{{PARAMETER_NAME}}` | 部署/自举时必须填入模板的参数格 | 自举智能体收集后写入目标配置。 |

二者都必须在环境契约中声明。`{{...}}` 不得嵌套，不能留在最终可运行的宿主配置中；`${...}` 仅能出现在明确支持环境变量展开的字段。不得根据字段名猜测选择哪种写法。

## MCP 逻辑声明

```json
{
  "id": "grafana",
  "transport": "stdio",
  "command": "mcp-grafana",
  "args": [],
  "environment": {
    "GRAFANA_URL": "${GRAFANA_URL}",
    "GRAFANA_SERVICE_ACCOUNT_TOKEN": "${GRAFANA_SERVICE_ACCOUNT_TOKEN}"
  },
  "tools": {
    "include": ["search_dashboards", "get_dashboard_by_uid", "update_dashboard"]
  }
}
```

- `command` 表示期望执行的命令；不是固定安装命令。
- `environment` 只能引用环境契约中已声明变量。
- `tools.include` 仅在编制人明确要限制工具范围时声明；未声明时不得擅自缩小工具范围。
- MCP 不含真实 Secret、用户路径、运行状态、宿主专有配置或未来版本承诺。

## 不可违反的安全边界

不得：

1. 将 Secret、Token、密码、真实 API Key 或用户绝对路径写进包、示例、Git 或日志。
2. 将 `.env`、会话、日志、缓存、state 数据库或 `dist/` 测试产物作为发布资产。
3. 将宿主最终配置当作跨宿主 canonical 资产。
4. 将工作区中已持续变化的现场 memory 当作可随升级静默覆盖的模板。
5. 因为示例或 Adapter 存在就宣称目标宿主已经可用。
