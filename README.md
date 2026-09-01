# agent_metadata — 智能体元数据包规范与编制技能

`agent_metadata` 是一套框架无关的智能体元数据包规范，以及一个供智能体加载使用的编制技能。本仓库本身不是元数据包，而是规范来源和编制工具的来源。

## 本仓库包含什么

```text
agent_metadata/
├── README.md          # 人类入口（本文件）
├── CHANGELOG.md       # 规约规则变更日志
├── LICENSE            # MIT（本项目）
├── docs/              # 规范文档（四篇）
├── skills/            # 编制技能：agent-metadata-package
│   └── agent-metadata-package/
└── dist/              # 测试沙箱（不发布）
```

- `docs/` 是规范文档，定义元数据包应包含什么资产、如何自举、如何验证。包内资产的目录布局、字段和命名规则见 [包结构与元数据](docs/01-package-and-metadata.md)。
- `skills/agent-metadata-package/` 是编制技能。智能体加载该技能后，遵循其指令完成元数据包的创建、维护、审查和发布准备。
- `dist/` 是测试沙箱，不属于规范内容，正式发布前必须排空。

## 两种工作流

### 1. 制作一个智能体元数据包

在你的智能体（如 Hermes）中加载本项目的 `agent-metadata-package` 技能，并要求智能体遵循该技能。技能会指导智能体：

- 建立包结构和根清单 `package-metadata.json`；
- 定义能力域（`SOUL.md`、`USER.md`、`AGENTS.md` + `capability-metadata.json`）；
- 组织共享技能、MCP 声明、环境契约和工作区资产；
- 编写 Adapter（仅在确有已知宿主经验时）；
- 补足 `BOOTSTRAP.md`；
- 执行发布前静态检查。

编制技能只负责包的编制，不执行解包、自举或部署；这些由产出的包根目录 `BOOTSTRAP.md` 规定，由目标宿主现场执行。技能的完整内容见 [skills/agent-metadata-package/SKILL.md](skills/agent-metadata-package/SKILL.md)。

### 2. 使用一个已有的智能体元数据包

获得元数据包后（解压归档或克隆仓库），在你的智能体中要求它阅读该包——先读根 `package-metadata.json` 和 `BOOTSTRAP.md`，再按自举规约完成能力部署和原生验证。

自举流程、适配知识和安全边界见 [自举、适配与安全](docs/02-bootstrap-and-security.md)。验收门槛见 [发布与验证](docs/03-release-and-verification.md)。

## 文档

| 文档 | 适合在什么时候读 |
| --- | --- |
| [体系概览](docs/00-overview.md) | 第一次接触本规范，需要理解目标、边界和适用范围。 |
| [包结构与元数据](docs/01-package-and-metadata.md) | 需要创建包、维护目录或编写根 `package-metadata.json` 与能力域 `capability-metadata.json`。 |
| [自举、适配与安全](docs/02-bootstrap-and-security.md) | 需要把资产部署到 Hermes、OpenCode 等宿主，或处理 Secret 与工作区资产。 |
| [发布与验证](docs/03-release-and-verification.md) | 需要打包发布，或验收一次自举是否真正成功。 |

## 规范性措辞

本 README 与 `docs/` 下的全部规范文本均采用下表的措辞强度；未使用下表措辞的描述性文字不单独增加合规义务。

| 措辞 | 含义与处理要求 |
| --- | --- |
| **必须** | 强制要求；不满足即不合规，相关静态校验、发布或自举不得通过。 |
| **不得** | 绝对禁止；不得以降级、便利或实现差异绕过。 |
| **应** | 默认要求；无法满足时，应在交付或验证报告中说明原因、影响与降级。 |
| **不应** | 强烈不推荐；采用时应有明确的上下文理由。 |
| **可** | 允许的实现选择；不影响合规。 |
| **建议** | 最佳实践；不影响包或自举的合规性。 |
| **示例** | 仅用于说明，不构成默认要求或必然实现。 |

安全禁令、协议结构和验收门槛使用"必须 / 不得"；Adapter 内容、验证记录和部署后检查使用"应"；归档格式、目录组织、CI 与宿主命令使用"建议 / 示例"。对于由当前宿主、项目状态和用户授权决定的部署处置，自举智能体可自行判断，但应如实报告结果。

## 状态

当前规范版本为 `0.2.2`（协议版本 `0.2`）。协议版本与包内容版本分开维护，规则见 [发布与验证](docs/03-release-and-verification.md)。版本间的规则变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 贡献

欢迎通过 Issue 或 Pull Request 参与改进。提交前请确认：

1. 规范文档（`docs/`）与编制技能（`skills/agent-metadata-package/`）内容一致。
2. `dist/` 已清空，只保留 `.gitignore` 和 `README.md`。
3. 规约规则变更已在根 `CHANGELOG.md` 和技能目录 `CHANGELOG.md` 同步追加记录（两份内容必须一致）。

## 许可证

本项目采用 MIT 许可证，见 [LICENSE](LICENSE)。

智能体元数据包是独立产物；其许可证由包的编制者自行定义，不受本项目许可证约束。
