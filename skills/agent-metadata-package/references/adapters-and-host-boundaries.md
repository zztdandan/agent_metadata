# Adapter 与宿主边界

Adapter 保存“已知宿主如何适配 canonical 资产”的脱敏知识。它帮助自举智能体减少现场摸索，但不替代 `BOOTSTRAP.md`、当前宿主文档或真实运行验证。

## 目录

```text
adapters/<agent-id>/
├── README.md
└── examples/
    └── <sanitized-config>.example
```

根清单登记 Adapter：

```json
{
  "id": "hermes",
  "path": "adapters/hermes",
  "status": "experimental"
}
```

## Adapter README 最小内容

1. 已验证的宿主版本、验证日期和状态。
2. capability 如何映射为该宿主的身份/Agent 表达。
3. skill 的发现目录与 frontmatter 要求。
4. MCP 声明如何转写到宿主配置，是否支持工具白名单。
5. 环境变量由何处加载，是否支持 `${...}` 展开。
6. 工作区资产的建议位置和冲突处理边界。
7. 宿主原生发现验证的方法。
8. 已知限制、不兼容情形与需要现场确认的项目。

Adapter 可带脱敏配置片段，但不能包含真实值、用户绝对路径、会话/运行状态、全局安装脚本或“保证未来版本可用”的表述。

## Hermes 示例边界

Hermes 的实际配置格式、profile 布局和发现逻辑取决于当前安装版本。Adapter 可说明经过验证的映射方向，例如：

- 将能力域语义映射到 Hermes 支持的身份/项目指令表达；
- 将完整 skill 目录放到当前 profile 或 project-local `HERMES_HOME` 的技能发现路径；
- 将 MCP 逻辑声明转换到当前 Hermes 的 MCP 配置段，并通过环境变量引用 Secret；
- 用 Hermes 的当前原生命令验证身份、技能发现、MCP 可用性和工作区资产可读性。

不要在 canonical 包里硬编码特定用户的 `HERMES_HOME`、`~/.hermes` 路径或 `config.yaml` 完整文件。应将已验证的片段放在 `examples/`，并明确变量、版本和需现场确认项。

## 状态使用

- `verified`：在明确的真实宿主版本执行过验证，并保留版本与验证方法。
- `experimental`：有实现或资料依据，但尚未完成当前版本的真实验证。
- `research_required`：仅知道需要适配，尚未掌握可靠加载方式。
- `unsupported`：已确认当前宿主不支持该需求。

宿主升级后未重新验证，原 `verified` Adapter 应降为 `experimental`。Adapter 与 `BOOTSTRAP.md` 冲突时，后者的安全边界优先。
