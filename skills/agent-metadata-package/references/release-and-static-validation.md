# 发布与静态校验

本参考只约束包编制阶段的静态检查和发布清理。自举后是否真的被宿主发现，由 `BOOTSTRAP.md` 要求的四层验收确认。

## 发布前清单

1. `README.md`、`BOOTSTRAP.md`、根 `package-metadata.json`、两份 Schema 及至少一个完整 capability 存在。
2. 根 `package-metadata.json` 通过 `schema/package-metadata.schema.json`，每个 `capability-metadata.json` 通过 `schema/capability-metadata.schema.json`。
3. 所有 capability 子清单的 `capabilityId`、skill、MCP、workspace asset ID 已在根清单登记。
4. 所有 capability 子清单环境变量、MCP `${...}` 和模板 `{{...}}` 已在 `environment.json` 声明。
5. ID 无重复；路径均在包根内，不含绝对路径或 `..`。
6. 每个根清单 skill 路径存在且有 `SKILL.md`；其 frontmatter `name` 与 skill ID 一致。
7. 工作区资产路径是目录，目录名与资产 ID 一致。
8. 不含 `.env`、真实 Secret、Token、密码、真实 API Key、非示例生产地址、用户绝对路径、会话、日志、缓存、`state.db*` 或宿主运行状态。
9. `dist/` 为空，或只保留 `.gitignore` 和 `README.md`。
10. 归档排除项至少覆盖 `dist/**`、`**/.env`、会话、日志和状态文件。
11. 若 `schemaVersion` 或规则约束自上一版本以来有变化，根 `CHANGELOG.md` 中有对应记录且已更新版本号。

## 建议的静态校验顺序

```text
JSON 格式 → JSON Schema → 根/子清单交叉引用 → 路径与 ID → 技能目录 →
变量引用 → Secret/运行态扫描 → dist 清理 → 归档内容检查
```

任一步失败时，停止发布并报告真实失败项；不得以推测替代检查结果。

## 四层验收报告模板

这是自举完成后应由执行者填写的脱敏报告格式，包编制者可把它作为验证用例的期望输出：

```text
=== 自举验证报告 ===

包: <package-id> v<package-version>
能力域: <selected-capability-ids>
目标: <host and scope>

包静态验证: 通过 / 失败
生成物验证: 通过 / 失败 / 未执行
安装状态验证: 通过 / 失败 / 未执行
宿主原生发现验证: 通过 / 失败 / 未执行

变量状态: 仅报告已设置/未设置，不展示值
降级与未完成项: <事实描述>
结论: 自举成功 / 仅生成物完成 / 失败
```

只有四层均通过时，才可写“自举成功”。文件复制完成、配置生成完成或 Agent 能启动，均不足以单独证明成功。

## 归档

建议格式为 `<package-id>-<package-version>.tar.gz` 或 `.zip`。归档应包含 canonical 根级文件、`common/`、`capabilities/`、实际提供的 `adapters/`（含其内部 helpers 和 implementation 等目录）、`evaluations/`（只含验证定义和最小夹具，不含一次性评估结果）、`schema/`，以及空的 `dist/` 说明文件；不得包含测试产物或未声明的运行时内容。
