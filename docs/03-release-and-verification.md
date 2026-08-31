# 发布与验证

本页定义发布前的清理要求和“自举成功”的验收标准。目标很简单：发布包不带敏感或运行时内容，部署结果不靠猜。

## dist/ 是测试沙箱

`dist/` 用于在不同宿主中试运行自举结果，例如 `dist/hermes-test/` 或 `dist/opencode-test/`。它不是包的 canonical 资产，不进入 Git，也不能进入正式归档。

`dist/.gitignore` 应忽略所有测试内容，仅保留自身和说明文件：

```gitignore
*
!.gitignore
!README.md
```

正式打包前，`dist/` 必须为空，或只包含 `.gitignore` 与 `README.md`。其中不能有环境文件、Secret、会话、日志或运行状态。

## 发布内容与排除规则

发布包应包含根级文件、`common/`、`capabilities/`，以及实际提供的 `adapters/`（含其内部 helpers 和 implementation 等目录）、`evaluations/`（只含验证定义和最小夹具，不含一次性评估结果）和 `schema/`。保留 `dist/.gitignore` 和 `dist/README.md`，但不带任何测试产物。

根清单可声明排除规则：

```json
{
  "distribution": {
    "exclude": [
      "dist/**",
      "**/.env",
      "**/sessions/**",
      "**/logs/**",
      "**/state.db*",
      "**/__pycache__/**",
      "**/node_modules/**",
      "**/.DS_Store"
    ]
  }
}
```

归档建议使用 `<package-id>-<package-version>.tar.gz` 或 `.zip`，例如 `dedge-agent-metadata-0.1.0.tar.gz`。

建议的根 `.gitignore` 至少排除 `.env`、`dist/` 下的测试内容、会话与日志、缓存、memory、锁文件，以及 `.DS_Store`、`__pycache__/`、`node_modules/`。CI 最好加入 Secret 扫描。

## 发布前检查

1. `dist/` 已清空。
2. 包内没有 `.env`、真实 API Key、密码、Token、非示例服务地址或用户绝对路径。
3. `schema/package-metadata.schema.json` 与 `schema/capability-metadata.schema.json` 均存在；根和每个能力域清单分别通过对应 Schema 校验。
4. capability ID、技能、MCP、工作区资产和环境变量引用均能在根清单或环境契约中找到。
5. 路径不含绝对路径或 `../`；ID 没有重复；技能依赖闭合。
6. 归档内容与 `distribution.exclude` 一致。

## 四层验收

### 1. 包静态验证

在自举前必须检查 JSON Schema、引用完整性、路径穿越、重复 ID、依赖闭环和 Secret 泄漏。任何一项失败都不得继续部署。

### 2. 生成物验证

检查生成的宿主配置是否符合该宿主格式，技能是否作为完整目录复制，MCP 是否已转换为宿主配置，环境变量是否仅以变量名引用，工作区资产是否在预期位置。

### 3. 安装状态验证

确认必填变量已经设置但不泄漏值，生成文件与安装计划一致，没有覆盖非受管文件，可变资产没有被覆盖，`dist/` 测试内容没有混进正式目标。

### 4. 宿主原生发现验证

让宿主实际读取和使用资产：确认它知道能力域身份、能发现或加载技能、能连上 MCP，并能读取工作区资产。这一层缺失时，仅可说“文件已生成”，不得说“自举成功”。

## 验证用例与报告

`evaluations/` 是可选的迁移验收契约。只有当某项能力存在可重复的安装后发现、加载、连接、运行或边界验证时才需要提供。它存放验证定义及其最小测试夹具，不存放一次性评估结果。评估执行结果应由部署方或 CI 在包外产生；如需随包提供结果，只能提供脱敏、可复核、明确标注版本和环境的参考报告。

可以按能力域发现、技能发现、MCP 连通性和工作区资产分目录存放用例。每个用例写清验证目标、前置条件、执行步骤、预期结果和脱敏要求。

报告应明确包版本、能力域、目标宿主、四层结果、未完成项和降级情况。环境变量只显示状态，例如：

```text
=== 自举验证报告 ===

包: dedge-agent-metadata v0.1.0
能力域: datacenter-agent
目标: Hermes（project-local）

包静态验证: 通过
生成物验证: 通过
安装状态验证: 通过
宿主原生发现验证: 通过

结论: 自举成功
```

失败时应列出实际失败项、能确认的原因和下一步检查点；不得用推测代替结果。报告里不得出现 Secret、Token、密码或完整敏感配置。

## 版本管理

`schemaVersion` 是协议版本，字段定义变化时才升级；`package.version` 是资产内容版本。二者独立演进。包内容通常使用语义化版本：结构性资产变更增加 MINOR，内容修订增加 PATCH；不兼容的协议调整需要升级 `schemaVersion`。


## Git、打包与术语补充

根 `.gitignore` 建议包含：

```gitignore
# 自举测试沙箱
dist/
!dist/.gitignore
!dist/README.md

# 环境变量
.env
**/.env

# 运行时副产物
sessions/
logs/
cache/
memory/
memories/
checkpoints/
backups/
home/
tmp/
plans/
state.db*
*.lock

# 系统文件
.DS_Store
__pycache__/
node_modules/
```

`distribution.exclude` 中每项的含义：`dist/**` 排除测试沙箱；`**/.env` 排除凭证；`**/sessions/**`、`**/logs/**`、`**/state.db*` 排除运行状态；`**/__pycache__/**`、`**/node_modules/**` 和 `**/.DS_Store` 排除构建依赖或系统文件。

发布归档应包含 `common/`、`capabilities/`、现有的 `adapters/`（含其内部 helpers 和 implementation 等目录）、`evaluations/`（只含验证定义和最小夹具）、`schema/` 和根级文件，以及 `dist/.gitignore`、`dist/README.md`；不含 `dist/` 产物、`.env`、运行状态或未明确要求的 Git 元数据。

## 术语速查

- **canonical 资产**：包内框架无关的真源资产。
- **Host 派生产物**：由包在某宿主中生成的配置、profile、agent 或 preset；可从 canonical 资产重建。
- **自举**：当前智能体读取包、适配宿主、生成配置并验证的过程；规范限定结果和安全边界，不限定工具。
- `**copy` / `merge` / `reference` / `generate`**：分别表示仅在目标缺失时复制、需要理解内容后合并、只读不复制、根据用户输入或环境生成。
- **工具自由**：元数据包不强制安装器、语言、模板系统或交互方式。
- **Secret 不入包**：敏感值只在包外安全位置保存，包内只放变量名或引用。
- **自举必验证**：必须验证宿主实际发现与加载，而非只检查文件。
- **dist 不发布**：`dist/` 仅用于试验，正式打包前必须排空。
