# agent_metadata — 智能体元数据包规范

`agent_metadata` 是一套框架无关的组织智能体资产规范。它把身份、技能、外部工具需求、环境契约和工作区资产保留为可迁移的来源，让不同 Agent 宿主按自己的真实能力完成适配。

它不是安装器或运行时，也不规定某个框架的最终配置。详情从[体系概览](docs/00-overview.md)开始。

---

## 核心特性

- **框架无关**：资产是来源，不是某个宿主的配置产物。Hermes、OpenCode 或其他宿主都能按自身能力适配。
- **身份可迁移**：专家身份（SOUL）、用户协作约定（USER）和可直接复制的能力工作目录约束（AGENTS）分离存放；它们在目标宿主的部署位置由 `BOOTSTRAP.md` 决定，合并时也有明确顺序。
- **安全优先**：Secret 不入包、不入 Git、不入日志；环境契约只声明变量名和类型。
- **四层验收**：静态校验 → 生成物验证 → 安装状态验证 → 宿主原生发现验证，层层递进，不靠猜。
- **可扩展**：能力域、技能、MCP 声明和工作区资产均为多对多关系，按需组合。

## 目录结构

```text
agent_metadata/
├── README.md                       # 人类入口（本文件）
├── BOOTSTRAP.md                    # 面向自举智能体的结果规约
├── package-metadata.json                   # 根清单
├── schema/
│   └── package-metadata.schema.json        # 根清单的 JSON Schema
├── common/
│   ├── skills/<skill-id>/          # 完整技能目录
│   ├── mcp/<mcp-id>.json           # MCP 逻辑需求
│   ├── environment/                # 环境契约 + .env.example
│   ├── workspace/<asset-name>/     # 工作区资产
│   └── references/                 # 只读参考资料
├── capabilities/<capability-id>/   # 能力域：SOUL + USER + AGENTS + 子清单
├── adapters/<agent-id>/            # 宿主适配知识与宿主专用实现
├── evaluations/                    # 可重复验证用例（不登记）
└── dist/                           # 测试沙箱（不发布）
```

字段定义和命名规则见[包结构与元数据](docs/01-package-and-metadata.md)。

## 文档


| 文档                                            | 适合在什么时候读                                        |
| --------------------------------------------- | ----------------------------------------------- |
| [体系概览](docs/00-overview.md)                   | 第一次接触本规范，需要理解目标、边界和适用范围。                        |
| [包结构与元数据](docs/01-package-and-metadata.md)    | 需要创建包、维护目录或编写根 `package-metadata.json` 与能力域 `capability-metadata.json`。               |
| [自举、适配与安全](docs/02-bootstrap-and-security.md) | 需要把资产部署到 Hermes、OpenCode 等宿主，或处理 Secret 与工作区资产。 |
| [发布与验证](docs/03-release-and-verification.md)  | 需要打包发布，或验收一次自举是否真正成功。                           |


## 快速开始

### 前置条件

- 已安装 [Git](https://git-scm.com/)
- 目标 Agent 宿主（如 [Hermes](https://github.com/NousResearch/hermes-agent) 或 OpenCode）已就绪
- 需要的外部服务（如 Grafana）和对应 Secret 已准备

### 使用一个已有包

```bash
git clone https://github.com/zztdandan/agent_metadata.git
cd agent_metadata

# 1. 阅读根 package-metadata.json 和 BOOTSTRAP.md
cat package-metadata.json
cat BOOTSTRAP.md

# 2. 让你的 Agent 宿主自举（以 Hermes 为例）
HERMES_HOME=./dist/hermes-test hermes chat -q "读取 package-metadata.json，列出可用能力域"

# 3. 验证自举结果（四层验收见 docs/03-release-and-verification.md）
```

### 创建一个新包

1. 复制本仓库结构或从零搭建最小合法包：`package-metadata.json` + `README.md` + `BOOTSTRAP.md` + `schema/package-metadata.schema.json` + 至少一个能力域目录。
2. 在根 `package-metadata.json` 登记 `package`、`capabilities`、`bootstrap` 等必填字段。
3. 在 `capabilities/<id>/` 下编写 `SOUL.md`、`USER.md`、`AGENTS.md` 和`capability-metadata.json`。
4. 把共享技能、MCP 声明、环境契约和工作区资产放进 `common/` 并在根清单登记。
5. 运行发布前检查（见[发布与验证](docs/03-release-and-verification.md)）。

## 规范性措辞

本 README 与 `docs/` 下的全部规范文本均采用下表的措辞强度；未使用下表措辞的描述性文字不单独增加合规义务。


| 措辞     | 含义与处理要求                          |
| ------ | -------------------------------- |
| **必须** | 强制要求；不满足即不合规，相关静态校验、发布或自举不得通过。   |
| **不得** | 绝对禁止；不得以降级、便利或实现差异绕过。            |
| **应**  | 默认要求；无法满足时，应在交付或验证报告中说明原因、影响与降级。 |
| **不应** | 强烈不推荐；采用时应有明确的上下文理由。             |
| **可**  | 允许的实现选择；不影响合规。                   |
| **建议** | 最佳实践；不影响包或自举的合规性。                |
| **示例** | 仅用于说明，不构成默认要求或必然实现。              |


安全禁令、协议结构和验收门槛使用"必须 / 不得"；Adapter 内容、验证记录和部署后检查使用"应"；归档格式、目录组织、CI 与宿主命令使用"建议 / 示例"。对于由当前宿主、项目状态和用户授权决定的部署处置，自举智能体可自行判断，但应如实报告结果。

## 给自举智能体的最短路径

1. 阅读根 `package-metadata.json` 和 `BOOTSTRAP.md`，了解包内资产与安全边界。
2. 确认当前宿主的版本和能力；如有 Adapter，只把它当作参考。
3. 选择能力域，确认目标工作区、既有配置的修改范围和缺失权限。
4. 映射资产并进行宿主原生验证：身份、技能、MCP、环境变量和工作区资产都要实际可用。

不得通过"文件已经复制"来判断完成。验证要求见[发布与验证](docs/03-release-and-verification.md)。

## 给维护者的路径

1. 先定义能力域及其 `SOUL.md`、`USER.md`、`AGENTS.md`。
2. 将共享技能、MCP、环境契约和工作区资产放进 `common/`，在根清单登记。
3. 用能力域子清单引用需要的资产。
4. 写 Adapter 和验证用例，再在测试沙箱中验证。
5. 清空 `dist/`，运行发布前检查后再归档。

## 状态

当前规范版本为 `0.2.1`（协议版本 `0.2`）。协议版本与包内容版本分开维护，规则见[发布与验证](docs/03-release-and-verification.md)。版本间的规则变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 贡献

欢迎通过 Issue 或 Pull Request 参与改进。提交前请确认：

1. `dist/` 已清空，只保留 `.gitignore` 和 `README.md`。
2. 包内没有 `.env`、真实 API Key、密码、Token 或用户绝对路径。
3. `schema/package-metadata.schema.json` 存在，且根 `package-metadata.json` 能通过 Schema 校验。
4. 子清单的技能、MCP、工作区资产和环境变量引用都能在根清单或环境契约中找到。
5. 路径不含绝对路径或 `../`；ID 没有重复；技能依赖闭合。

## 许可证

本项目暂未附带 `LICENSE` 文件。发布或分发包时应提供许可证。