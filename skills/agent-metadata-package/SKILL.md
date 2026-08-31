---
name: agent-metadata-package
description: 当用户要创建、维护、审查或发布框架无关的智能体元数据包时使用。该技能将身份能力域、可迁移技能、MCP 逻辑需求、环境契约、工作区资产和宿主 Adapter 组织为 canonical 包；遇到新建或修改 package-metadata.json、capabilities、common/skills、common/mcp、workspace assets、Adapter 或发布检查时都应使用。
---

# 智能体元数据包编制

本技能服务于**包编制者**：将组织智能体资产整理为可迁移、可审计的 canonical 元数据包。它不执行解包、自举或部署；这些由包根目录的 `BOOTSTRAP.md` 规定并由目标宿主现场执行。

## 成功标准

交付的包应满足：

1. 根清单、能力域子清单和环境契约的引用闭合。
2. 每个能力域都有 `SOUL.md`、`USER.md`、`AGENTS.md` 和 `capability-metadata.json`。
3. 技能按完整目录提供；MCP 是框架无关的逻辑声明；工作区资产按目录提供。
4. 包内没有 Secret、真实 Token、密码、用户绝对路径或运行状态。
5. `BOOTSTRAP.md` 说明自举目标、安全边界与验收要求，但不绑定固定安装器。
6. 发布前通过静态检查，`dist/` 不含测试产物。

## 先判断任务边界

先区分 canonical 资产和宿主派生产物：

- **进入包**：能力域身份与规程、完整技能目录、MCP 逻辑需求、环境变量契约、可迁移的工作区种子资产、Adapter 适配知识与宿主专用实现、可重复的验证用例。
- **不进入包**：宿主最终配置、真实凭证、会话/日志/缓存/数据库状态、用户绝对路径、一次性评估产出、构建产物和运行状态。

若用户要将包部署到 Hermes、OpenCode 或其他宿主，停止在编制完成状态；请其读取包根 `BOOTSTRAP.md`，并以目标宿主的当前文档和实际行为完成自举。

## 编制流程

### 1. 建立或读取包地图

1. 读取包的 `README.md`、根 `package-metadata.json`、`BOOTSTRAP.md`，以及已有能力域和共享资产。
2. 先列出能力域、共享技能、MCP、环境变量、工作区资产和 Adapter 的 ID；再开始编辑。
3. 新包以 `assets/package-skeleton/` 为基础。字段和目录细节见 `references/package-structure-and-manifest.md`。

### 2. 定义能力域

每个 `capabilities/<capability-id>/` 必须包含：

```text
capability-metadata.json
SOUL.md
USER.md
AGENTS.md
```

- `SOUL.md` 仅描述身份、使命、取舍和硬边界，避免写成操作手册。
- `USER.md` 描述协作偏好和交互约定。
- `AGENTS.md` 描述可直接复制的能力工作目录约束：项目事实、目录边界、读写范围与运行限制；不要将任务的逐步流程、自举步骤或宿主部署路径写进该文件。
- 子清单只引用根清单中登记的共享资产，不复制资产定义。

使用 `assets/capability/` 创建最小结构；组合规则见 `references/capability-and-asset-model.md`。

### 3. 组织共享资产

- 技能位于 `common/skills/<skill-id>/`，必须有带 frontmatter 的 `SKILL.md`。复制或安装时以整个目录为单位，不能只取入口文件。
- MCP 位于 `common/mcp/<mcp-id>.json`，只描述传输、命令、参数、变量引用和可选工具范围；不放任一宿主原始配置。
- 环境契约位于 `common/environment/environment.json`，`.env.example` 只提供无密模板。
- 工作区资产位于 `common/workspace/<asset-id>/`。资产目录下的内容将来复制到工作区根目录；不能假定资产目录名会成为目标目录层级。
- `common/references/` 是只读资料，不需要根清单登记。

环境、MCP 和安全边界见 `references/environment-mcp-and-security.md`。

### 4. 写 Adapter（仅在确有已知宿主经验时）

Adapter 放在 `adapters/<agent-id>/`，是为了让元数据包在该宿主上集成而需要的全部宿主专用内容。它可以携带说明、脱敏配置示例、集成实现源码、构建配置和辅助脚本——只要该内容仅为该宿主的集成服务。例如：OpenCode 若采用插件模式，Adapter 说明如何基于公共资产制作插件；Hermes 可能需要示例的 config 裁剪能力、技能裁剪能力以及 `.env.example`。

Adapter 至少应说明：验证版本/状态、能力域映射、技能发现、MCP 映射、环境变量加载、建议工作区位置、原生验证方法和已知限制。其中的实现源码、构建配置和辅助脚本不自动执行；它们是参考或可选实现，不是安装脚本。

Adapter 未经真实验证时，根清单状态应为 `experimental` 或 `research_required`，不能写成 `verified`。详细边界见 `references/adapters-and-host-boundaries.md`。

### 5. 补足自举规约

根 `BOOTSTRAP.md` 应让自举智能体能独立完成：理解包、识别当前宿主、与用户确认范围、收集安全配置、映射资产、进行宿主原生发现验证。它规定结果与安全边界，不固定工具或命令。

不要把自举步骤复制到本技能中，也不要把本技能当作部署时依赖。

### 6. 静态检查与发布准备

发布前逐项检查：

1. 根 `package-metadata.json` 能通过 `schema/package-metadata.schema.json`，每个 `capability-metadata.json` 能通过 `schema/capability-metadata.schema.json`。
2. 子清单引用的 skill、MCP、workspace asset 和环境变量均有根级或环境契约定义。
3. ID 唯一，包内相对路径不含绝对路径或 `..`，技能依赖闭合。
4. `.env`、Secret、真实服务地址、用户绝对路径、会话和运行状态不在包内。
5. `dist/` 为空，或只保留 `.gitignore` 和 `README.md`。
6. 归档内容遵循 `distribution.exclude`。

完整检查清单与报告模板见 `references/release-and-static-validation.md`。

## 补充规约的读取顺序

- 需要目录、字段、命名和引用规则：读 `references/package-structure-and-manifest.md`。
- 需要判断 capability、skill、MCP、workspace asset 的归属和组合：读 `references/capability-and-asset-model.md`。
- 需要环境变量、`${...}`、`{{...}}`、Secret 或 MCP：读 `references/environment-mcp-and-security.md`。
- 需要 Hermes/OpenCode 或其他宿主适配知识（含 Adapter 内部 helpers 和实现源码）：读 `references/adapters-and-host-boundaries.md`。
- 需要发布、校验、验收报告：读 `references/release-and-static-validation.md`。

## 示例

- `examples/llm-wiki-vault/`：一个 capability、三个技能和一个工作区资产；不含 MCP。
- `examples/dedge-datacenter/`：多个 capability、技能组、MCP、环境契约、多个工作区资产和 Hermes Adapter。

示例是可阅读的完整包，不是生产配置。优先从与任务复杂度相同的示例开始，再使用 `assets/` 的最小模板创建或补齐局部资产。
