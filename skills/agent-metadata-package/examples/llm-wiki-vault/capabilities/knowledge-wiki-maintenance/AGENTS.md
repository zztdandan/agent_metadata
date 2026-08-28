# 工作目录约束与 Vault 契约

## 语言与角色

- 无论输入语言，均以**简体中文**思考、回复并编写知识库；必要的技术术语可保留原文。
- 将碎片化资料编译为结构化、高度互联、可追溯的 Obsidian LLM Wiki，服务 AI 辅助学习和研究。

## 目录权限与架构

- `raw/` 是不可变事实层，存放原始素材、网页剪藏和转录。绝对只读：禁止修改或删除其中的文件文本。
- `assets/` 是媒体资产层。笔记中用 Obsidian 标准语法 `![[文件名称.png]]` 引用。
- `wiki/` 是编译输出层。只在此处创建、更新、提炼知识和显式处理矛盾。
- `raw/09-archive/` 是已处理资料归档区；摄入技能应忽略它。

## Wiki 核心契约

1. **索引**：每新增 wiki 页面，必须同步更新 `wiki/index.md`。条目格式为 `[[页面名称]] — 一句话描述`；Entities/Concepts 使用 TitleCase，Sources/Syntheses 使用 kebab-case。
2. **日志**：`wiki/log.md` 仅可追加。每次 ingest、query、lint 修复或 sync 后，按 `## [YYYY-MM-DD] <动作> | <操作简述>` 写入事实日志。
3. **分类**：`wiki/concepts/` 存概念、框架和方法论；`wiki/entities/` 存人物、公司、工具和产品；`wiki/sources/` 存 raw 材料摘要；`wiki/syntheses/` 存复杂问题综合。
4. **关联**：每个 wiki 页面必须有 `## 关联连接`，以 `[[页面名称]]` 链接到实际相关页面；不能产生孤岛页面。
5. **冲突**：新旧知识冲突时，不得静默覆盖。暂停摄入并请求用户决定；需要共存时写入 `## 知识冲突`，保留两种说法和比较。

## 页面格式

所有生成的 wiki 页面必须有：

```yaml
---
title: "页面标题"
type: concept | entity | source | synthesis
tags: [知识标签]
sources: [关联的 raw 文件相对路径]
last_updated: YYYY-MM-DD
---
```

## 长期维护约束

- 新增/更新后检查 frontmatter、索引登记、双链和日志。
- `wiki/log.md` 只允许追加；lint 的修复必须先得到用户确认。
- 不把编辑器状态、宿主会话、缓存或用户私有资料写入知识库资产。
