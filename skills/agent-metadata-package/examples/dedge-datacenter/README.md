# Dedge Datacenter 元数据包示例

本示例以 `/home/base/repo/dedge/dedge-datacenter-harness__root/dedge-datacenter` 的真实项目与 project-local Hermes home 为编制来源。它演示多个 capability、完整技能组、Grafana MCP、环境契约、完整项目工作区资产和 Hermes Adapter 的组合。

## 真实来源映射

| 源项目资产 | 本示例 canonical 位置 | 处理 |
|---|---|---|
| `.hermes/skills/` | `common/skills/` | 完整复制 5 个 Skill 及其 references。 |
| `.hermes/SOUL.md` | `capabilities/datacenter-dashboard-agent/SOUL.md` | 真实 dashboard Agent 身份与边界。 |
| `.hermes/config.yaml` | `adapters/hermes/examples/config.yaml.example` | 删除内联凭证后保留工具裁剪、模型/Provider、MCP 和白名单结构。 |
| `.hermes/README.md` | `adapters/hermes/references/project-local-home.md` | 保留 project-local home、自举和运行态边界说明。 |
| `.hermes/.env.example` | `adapters/hermes/examples/.env.example` | 无密变量模板。 |
| `backend/ frontend/ runtime/ catalog/ README* .gitignore` | `common/workspace/dedge-datacenter-project/` | 完整项目工作区资产；现场 memory 中的真实认证信息改为变量/参数模板。 |

## 能力域与资产关系

```text
datacenter-query-agent ─── datacenter-agent-runtime
                         ─── datacenter-agent-cloud-tss-query
                         ─── datacenter-agent-tdengine-longstmt
                         ─── grafana MCP
                         ─── dedge-datacenter-project

datacenter-dashboard-agent ─ datacenter-agent-runtime
                            ─ datacenter-agent-grafana-dashboard
                            ─ datacenter-agent-catalog-maintenance
                            ─ grafana MCP
                            ─ dedge-datacenter-project
```

`dedge-datacenter-project` 是一份完整工作区资产，因此项目自带的 `catalog/` 与 `runtime/agent-memory/` 不再被拆成独立、与真实项目脱节的演示资产。

## 安全说明

源项目 `.hermes/config.yaml` 及 `runtime/agent-memory/tsdb-memory.json` 含有真实凭证和现场运行地址。示例中不包含这些值：需要恢复环境时由 adapter 中的无密模板、环境契约和部署时的安全配置共同完成。
