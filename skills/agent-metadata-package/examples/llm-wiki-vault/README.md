# Karpathy LLM Wiki Vault 元数据包

这是对 `/home/base/Downloads/karpathy-llm-wiki-vault-main` 的真实结构进行脱离宿主后的 canonical 编制示例。源仓库是一个基于 Karpathy LLM Wiki 理念的 Obsidian 知识库：将原始资料编译成高度互联的 `wiki/` 知识网络，供 AI 辅助学习和研究。

示例完整保留该 vault 的三条可迁移业务技能：


| Skill ID      | 源技能                      | 用途                                             |
| ------------- | ------------------------ | ---------------------------------------------- |
| `wiki-ingest` | `.claude/skills/ingest/` | 将未归档 `raw/` 材料编译到 `wiki/`，更新 index/log 后归档源文件。 |
| `wiki-query`  | `.claude/skills/query/`  | index-first 检索 wiki，使用双链引用回答。                  |
| `wiki-lint`   | `.claude/skills/lint/`   | 只读检查索引、双链、孤儿页面与知识冲突。                           |


它只有一个 capability `knowledge-wiki-maintenance`，没有 MCP、环境契约或 Adapter。原 vault 的 `.claude/` 是 Claude Code 的派生产物；这里将三项业务能力作为框架无关的完整 skill 目录保存于 `common/skills/`。

## 工作区资产

`common/workspace/llm-wiki-vault/` 是实际 vault 种子内容，包含：

```text
assets/                         # Obsidian 图片/媒体资产
raw/                            # 原始资料收件箱和归档区
├── 01-articles/
├── 02-papers/
├── 03-transcripts/
└── 09-archive/
wiki/                           # 已编译知识网络
├── index.md                    # 全局注册表
├── log.md                      # 追加式操作日志
├── concepts/
├── entities/
├── sources/
└── syntheses/
```

部署时复制该资产目录的**内容**到目标工作区根目录。`raw/` 是原始事实层：业务规约禁止修改其中的文件文本；`wiki/` 是可写的编译输出层。此示例的已归档原始材料、已编译 wiki 页面及媒体文件均来自上述真实 vault。

## 与源仓库的差异

- 本示例不复制 `.claude/skills/`：其三个业务 Skill 已映射到 `common/skills/`，由目标宿主按自身发现机制安装。
- 源 vault 的 `CLAUDE.md` 是 Claude Code 的宿主指令产物；其语言、目录权限、页面、索引、日志、双链和冲突规则已实质迁移到 `capabilities/knowledge-wiki-maintenance/AGENTS.md`，不作为工作区资产部署。
- 本示例不声明 Obsidian CLI、defuddle 或任何 MCP，因为该源 vault 未使用 MCP，且这些宿主/工具能力不是其核心业务资产。
- 不将用户本地的编辑器状态、插件配置、缓存或会话作为资产。

