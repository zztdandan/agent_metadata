# 能力域与资产组合模型

能力域回答“专家是谁、遵守什么边界、需要哪些资产”；共享资产由根清单拥有。能力域不是资产私有目录，也不等同于宿主中的 Agent 实体。

## capability 四件套

```text
capabilities/<capability-id>/
├── metadata.json
├── SOUL.md
├── USER.md
└── AGENTS.md
```

- `SOUL.md`：身份、使命、价值取舍和硬边界。应简短，不能替代技能手册。
- `USER.md`：用户画像、协作偏好和交互约定。
- `AGENTS.md`：可直接复制的能力工作目录约束，记录长期生效的项目事实、目录、资产、读写与运行限制。它不承载按任务执行的逐步流程，也不写自举或宿主落点；任务流程属于技能，部署位置属于 `BOOTSTRAP.md` 与 Adapter。
- `metadata.json`：引用共享资产。

若目标宿主不能分开加载这些文件，自举时按“身份与边界 → 工作目录约束 → 用户协作”合并，并保留来源章节；不得直接首尾拼接。`AGENTS.md` 不写宿主映射或任务工作流；该映射属于 `BOOTSTRAP.md` 与 Adapter。

## 资产归属

| 资产 | canonical 位置 | 根清单登记 | 组合方式 |
|---|---|---:|---|
| 技能 | `common/skills/<skill-id>/` | 是 | capability 子清单引用 ID。 |
| MCP 逻辑声明 | `common/mcp/<mcp-id>.json` | 是 | capability 子清单引用 ID。 |
| 环境契约 | `common/environment/` | 是（整体） | capability 子清单引用变量名。 |
| 工作区资产 | `common/workspace/<asset-id>/` | 是 | capability 子清单引用资产 ID。 |
| 通用参考 | `common/references/` | 否 | 只读，不部署。 |
| Adapter | `adapters/<agent-id>/` | 是 | 宿主适配参考与宿主专用实现；含 README、examples、helpers、implementation 等内部目录。 |
| evaluations、dist | 各自目录 | 否 | 分别用于可重复验证用例和测试沙箱。 |

## 多对多组合

同一个 skill、MCP 或 workspace asset 可以被任意多个 capability 引用，但在根清单只登记一次。能力域可以没有技能或 MCP；不要为了目录对称创建无意义资产。

```text
capability A ─┬─ skill 1
              ├─ skill 2
              ├─ mcp 1
              └─ asset 1

capability B ─┬─ skill 2
              ├─ skill 3
              ├─ mcp 2
              └─ asset 1
```

子清单表达选择关系；不要将 `common/` 的资产复制到每一个 capability 下。

## 技能目录

```text
common/skills/<skill-id>/
├── SKILL.md
├── references/     # 可选
├── scripts/        # 可选
└── assets/         # 可选
```

技能是完整目录资产。脚本和附属资料随技能携带，但安装计划只能列明来源与路径，不能因打包或自举而静默运行脚本。

## 工作区资产

一个资产一个目录：

```text
common/workspace/dashboard-catalog/
└── catalog/
    ├── dashboard-catalog.json
    └── dashboard-catalog.schema.json
```

登记 `dashboard-catalog` 表示选择整份资产。未来部署时把资产目录**内容**按相对路径落到工作区根目录，因此上述文件会成为 `<workspace>/catalog/...`，而不是 `<workspace>/dashboard-catalog/catalog/...`。

资产适合保存模板、schema、初始 memory、catalog 或其他项目种子文件。资产不得带真实凭证、密码、Token、用户绝对路径或运行状态；复制后持续变化的现场资产由项目管理，升级或卸载不得静默覆盖或删除。
