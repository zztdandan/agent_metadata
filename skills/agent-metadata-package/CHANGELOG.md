# 规约变更日志

本文件记录 agent_metadata **规约规则**的版本变更，不是 Git commit history。每次 `schemaVersion` 或规则约束发生变化时，必须在此追加一条记录，说明改了什么、旧包需要怎么改。

用户从旧版本迁移到新版本时，应对照本文件逐项检查。

---

## schemaVersion `0.2`（规范版本 0.2.1）

发布日期：2026-08-31

本次升级不改变 `schemaVersion`（仍为 `"0.2"`），属于 0.2 协议下的内容修订（PATCH）。

### 新增规则

1. **新增规约变更日志机制**：项目根和 skill 目录各维护一份 `CHANGELOG.md`，内容必须一致。每次 `schemaVersion` 升级、字段增删、目录结构变化或规则约束变化时，必须在 `CHANGELOG.md` 追加记录，包含变更编号、变更类型（破坏性/语义澄清/文档修正）、变更描述和迁移动作。
   - 迁移动作：无（新机制，旧包不受影响）。

2. **SKILL.md 新增"版本与变更"段**：声明当前规约版本，并指引用户阅读 `CHANGELOG.md` 进行版本迁移。
   - 迁移动作：无（skill 内容更新，不影响元数据包结构）。

3. **发布前检查新增第 11 条**：若 `schemaVersion` 或规则约束自上一版本以来有变化，`CHANGELOG.md` 中有对应记录且已更新版本号。
   - 迁移动作：无（发布流程更新，不影响元数据包结构）。

### 文档修正

4. **修正版本不一致**：`docs/00-overview.md` 中版本从 `0.1.0` 修正为 `0.2.1`（与 README.md 一致，此前该文件一直停留在 0.1.0）。
   - 迁移动作：无（文档修正）。

---

## schemaVersion `0.2`（规范版本 0.2.0）

发布日期：2026-08-31（对应 git commit `cf146e5`，commit message: "release: publish metadata specification v0.2.0"）

本次升级的核心是：将根清单和子清单从同名的 `metadata.json` 区分为 `package-metadata.json` 和 `capability-metadata.json`，并引入 `$schema`/`kind` 自描述字段，使每个清单文件可独立校验。

### 破坏性变更（不兼容，旧包必须迁移）

1. **根清单文件重命名**：`metadata.json` → `package-metadata.json`；Schema 文件同步重命名为 `package-metadata.schema.json`。
   - 迁移动作：重命名根清单文件和 Schema 文件；更新所有文档和脚本中的引用。

2. **能力域子清单文件重命名**：`capabilities/<id>/metadata.json` → `capabilities/<id>/capability-metadata.json`。
   - 迁移动作：重命名每个能力域的子清单文件。

3. **新增 Schema 文件**：新增 `schema/capability-metadata.schema.json`，用于独立校验能力域子清单。
   - 迁移动作：将新 Schema 文件加入 `schema/` 目录。

4. **新增必填字段 `$schema` 和 `kind`**：
   - 根清单：`"kind": "agent-metadata-package"`，`"$schema"` 指向 `schema/package-metadata.schema.json`。
   - 子清单：`"kind": "agent-capability"`，`"$schema"` 指向对应 Schema。
   - 迁移动作：在根清单和每个子清单中补填这两个字段。

5. **`schemaVersion` 值升级**：`"0.1"` → `"0.2"`。
   - 迁移动作：修改根清单和所有子清单中的 `schemaVersion`。

6. **Schema 校验要求变化**：发布前检查从"根 `metadata.json` 能通过 Schema 校验"扩展为"根清单和每个能力域子清单分别通过对应 Schema 校验"。
   - 迁移动作：更新发布前检查流程，增加子清单 Schema 校验。

### 文档跟随更新

7. docs/01、docs/02、docs/03、README.md 和 SKILL.md 中的文件名引用（`metadata.json` → `package-metadata.json`/`capability-metadata.json`、`metadata.schema.json` → `package-metadata.schema.json`）跟随变更。这些是文档措辞更新，不是独立规则变更。

---

## schemaVersion `0.1`（规范版本 0.1.0）— 初始版本及内部修订

发布日期：2026-08-28（对应 git commit `84f7f14`，commit message: "docs: agent_metadata 规范文档体系初始版本"）

初始版本定义了 canonical 智能体元数据包的基本结构。`schemaVersion: "0.1"`。根清单和子清单都叫 `metadata.json`，Schema 文件叫 `metadata.schema.json`。

初始版本包含：根清单 `metadata.json` + 能力域子清单 `metadata.json`、能力域四文件（`SOUL.md`、`USER.md`、`AGENTS.md`、`metadata.json`）、共享资产（skills、mcp、environment、workspace、references）、顶层目录（`helpers/`、`evaluations/`、`dist/`）、四层验收、Adapter 定义为"已知经验记录"。

### 0.1.0 内部修订（不涉及 schemaVersion 变更，以下变更发生在 0.1 生命周期内）

以下变更发生在 commit `6115cf0`（2026-08-28，"docs: clarify canonical AGENTS asset semantics"）和 commit `cddebb2`（2026-08-28，"修改部分措辞，尤其 adapter方面定义"）中，属于 0.1 协议下的措辞和语义澄清，不改变 `schemaVersion`：

- **AGENTS.md 语义收窄**（commit `6115cf0`）：从"工作区规则、工程约束和运行规程"收窄为"可迁移的能力说明/工作目录指令资产"，明确它只描述能力本身（项目事实、目录边界、读写范围与运行约束），不是任务逐步流程，不是自举步骤。自举时将它复制到哪个宿主文件或目录，是 `BOOTSTRAP.md` 和 Adapter 的职责。
- **Adapter 语义扩展**（commit `cddebb2`）：从"脱敏的适配知识"扩展为"为了让元数据包在特定宿主上集成而需要的全部宿主专用内容"，可携带适配说明、脱敏配置示例、集成实现源码、构建配置和辅助脚本。Adapter 内部可含 `helpers/` 和 `implementation/` 子目录。
- **`helpers/` 降级**（commit `cddebb2`）：从包级顶层目录降级为 Adapter 内部目录。如果某个辅助工具对多个宿主通用，应提升为 `common/` 下的共享资产或技能。
- **evaluations 细化**（commit `cddebb2`）：从"验证用例"细化为"可重复验证用例"——只存验证定义和最小测试夹具，不存一次性评估结果。
- **删除"首批验证来源"段**（commit `cddebb2`）：docs/00-overview.md 中移除对 dedge-agent-lua、dedge-datacenter、dedge-cloud-agents 三个验证样本的提及。
- **新增编制技能**（commit `e618435`，2026-08-28）：`skills/agent-metadata-package/` 目录及其 assets、examples、references，作为编制辅助工具。

由于以上变更不改变 `schemaVersion`，使用 0.1 协议的包不需要迁移。但如果包内 `AGENTS.md` 写了任务流程或自举步骤，应按澄清后的语义修订内容。

---

## 维护规则

- **何时记录**：每次 `schemaVersion` 升级、字段增删、目录结构变化或规则约束变化时。
- **记录内容**：变更编号、变更类型（破坏性/语义澄清/文档修正）、变更描述、迁移动作。
- **版本号规则**：`schemaVersion` 是协议版本，字段定义变化时才升级；`package.version` 是资产内容版本。结构性资产变更增加 MINOR，内容修订增加 PATCH；不兼容的协议调整升级 `schemaVersion`。
- **同步要求**：CHANGELOG 更新后，`SKILL.md` 的"版本与变更"段和 `docs/03-release-and-verification.md` 的版本管理段应同步引用当前版本。
- **本文件只记录规约规则的变更**，不记录 Git commit、包内容修订或资产增减。
