# 最小元数据包骨架

将本目录内容复制为一个新包的起点。随后：

1. 为真实包替换根 `metadata.json` 的 package 和 capability ID。
2. 在 `capabilities/` 中补齐真实能力域的身份与规程。
3. 按需增加 `common/`、`adapters/`、`evaluations/`。
4. 根据包中的真实引用扩充 Schema 或使用协议 Schema。
5. 写明 `BOOTSTRAP.md`；它是自举规约，不是本技能的执行脚本。

此骨架不携带 MCP、环境变量、技能或工作区资产。
