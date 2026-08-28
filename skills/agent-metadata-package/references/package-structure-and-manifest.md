# 包结构、清单与命名规则

本参考定义 canonical 智能体元数据包的目录、根/子 `metadata.json` 与命名规则。根 `metadata.json` 是机器可读资产总表；能力域子清单只引用根级资产。

## 最小合法包

```text
<package-root>/
├── README.md
├── BOOTSTRAP.md
├── metadata.json
├── schema/metadata.schema.json
└── capabilities/<capability-id>/
    ├── metadata.json
    ├── SOUL.md
    ├── USER.md
    └── AGENTS.md
```

`common/`、`adapters/`、`helpers/`、`evaluations/` 和 `dist/` 按需添加。正式分发时应提供许可证。

## 完整布局

```text
<package-root>/
├── README.md
├── BOOTSTRAP.md
├── metadata.json
├── schema/metadata.schema.json
├── common/
│   ├── skills/<skill-id>/
│   ├── mcp/<mcp-id>.json
│   ├── environment/environment.json
│   ├── environment/.env.example
│   ├── workspace/<asset-id>/
│   └── references/
├── capabilities/<capability-id>/
├── adapters/<agent-id>/
├── helpers/
├── evaluations/
└── dist/
```

## 根 metadata.json

```json
{
  "schemaVersion": "0.1",
  "package": {
    "id": "example-agent-metadata",
    "version": "0.1.0",
    "name": "Example Agent Metadata",
    "description": "示例智能体元数据包"
  },
  "capabilities": [
    { "id": "example-agent", "path": "capabilities/example-agent" }
  ],
  "skills": [
    { "id": "example-skill", "path": "common/skills/example-skill" }
  ],
  "mcp": [
    { "id": "example-mcp", "path": "common/mcp/example-mcp.json" }
  ],
  "environment": {
    "contract": "common/environment/environment.json",
    "example": "common/environment/.env.example"
  },
  "workspaceAssets": [
    { "id": "example-memory", "path": "common/workspace/example-memory" }
  ],
  "adapters": [
    { "id": "hermes", "path": "adapters/hermes", "status": "experimental" }
  ],
  "bootstrap": "BOOTSTRAP.md",
  "distribution": {
    "exclude": ["dist/**", "**/.env", "**/sessions/**", "**/logs/**", "**/state.db*"]
  }
}
```

| 字段 | 要求 |
|---|---|
| `schemaVersion` | 必填；当前协议为 `"0.1"`。 |
| `package` | 必填；含小写连字符 `id` 和语义化 `version`。 |
| `capabilities` | 必填且至少一项；每项含 `id` 和相对 `path`。 |
| `skills`、`mcp`、`workspaceAssets` | 可选；每项在根级登记 ID 和相对路径。 |
| `environment` | 可选；有则同时指定 `contract` 与 `example`。 |
| `adapters` | 可选；每项含 `id`、目录 `path` 和状态。 |
| `bootstrap` | 必填，固定为 `BOOTSTRAP.md`。 |
| `distribution.exclude` | 可选；发布排除 glob。 |

Adapter 状态为 `verified`、`experimental`、`research_required` 或 `unsupported`。只有真实版本已验证时才能使用 `verified`。

## capability 子 metadata.json

```json
{
  "capabilityId": "example-agent",
  "skills": ["example-skill"],
  "mcp": ["example-mcp"],
  "workspaceAssets": ["example-memory"],
  "environment": ["EXAMPLE_SERVICE_URL"]
}
```

- `capabilityId` 必须等于根清单中该能力域 ID。
- `skills`、`mcp`、`workspaceAssets` 只写根清单已登记的 ID。
- `environment` 只写 `environment.json` 已声明的变量名。
- 引用缺失时，包不合规；不得用能力域私有副本绕过根登记。

## 文件与目录命名

- 资产 ID 使用小写连字符：`wiki-research`、`grafana`、`datasource-memory`。
- 能力域文件固定为 `SOUL.md`、`USER.md`、`AGENTS.md` 和 `metadata.json`。
- 技能入口固定为 `SKILL.md`，并带 `name`、`description` YAML frontmatter；`name` 必须等于根清单 skill ID。
- 路径必须相对包根，不得含绝对路径或 `..`。
- `helpers/`、`evaluations/`、Adapter 内部文件和技能内部文件清单不登记进 `metadata.json`。
