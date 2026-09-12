<p align="center">
  <img src="assets/icon.png" alt="AGENT_METADATA" width="128">
</p>

![Spec](https://img.shields.io/badge/spec-v0.2.2-blue.svg)
![Protocol](https://img.shields.io/badge/schema-0.2-informational.svg)
![Kind](https://img.shields.io/badge/kind-agent--metadata--package-purple.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

# AGENT_METADATA

## 元数据能解决什么问题？

好的 Agent harness 一直在变。这没什么可抱怨的——变得快本来就是好事。

今天最强的框架，明天可能被另一个取代。团队里同一个人，上午还在 Hermes 里干活，下午就换到了 OpenCode 或别的宿主。换工具本身不是问题，问题是**你经营过的那些东西都得重来一遍**：专家身份提示写在宿主的私有配置里，技能挂在宿主的发现路径下，MCP 连接、环境变量、项目初始化文件散落在宿主的目录结构中。换一次宿主，重排一次；换到第三次，就没人说得清哪一份才是准的了。

办公智能体这边，撞墙更早。像 WorkBuddy 这类平台把上手体验做得很好——好到你愿意在里面认真调教专家、编排流程、积累知识资产。代价是这些能力长在平台的私有格式上，导不出来。等你哪天想迁到一个更强、更开放的 harness，只能从零重配。

`agent_metadata` **首先是一个搬家专家。**

它给出的是一套智能体无关的打包模式：把你家里的软装（身份、技能、工具需求、工作区种子文件）按标准装箱搬运；到了新家，再根据新家的布局重新布置一遍。这个“重新布置一遍”，我们叫它**自举（bootstrap）**。搬家不要求两家户型一样——新宿主自己读包、自己识别自己的能力、自己决定每样东西放哪里，最后自己验证可用性。

`agent_metadata` 还是一个标准化包：数据是可以复制的。**你可以把自己的智能体划分多个能力域，以运行时无关的形式分享给别人**。别人拿到的是能力本身，不是某个框架的配置文件；它落在谁的宿主上，就按谁的宿主布置。比如你按照 workbuddy制作的一套工作流，分享给一个 hermes的用户他也能用。



### 为什么不用skill分享能力

一个人真正的工作流可能要配合 MCP skill，部分 cli依赖，甚至固定的工作区文件结构才能最终定义，skill能分享的工作流都是非常浅层的。比如 llm-wiki这个能力，实际有 init、ingest、query、review 四个技能，以及一套标准的初始化文档结构作为起步，才能构建完整的知识库闭环。

## 正式介绍

`agent_metadata` 是一套框架无关的**元数据包规范**，加上一个供智能体加载使用的**编制技能**。本仓库本身不是元数据包，而是规范来源和编制工具的来源。

包内资产是**来源（canonical）**，在 Hermes、OpenCode 或其他宿主中生成的 profile、agent、preset 和配置都是**派生产物**。派生产物随时可以从包里重建。

一个标准的 `agent_metadata` 包里会有这些：


| 资产          | 内容                                                                    |
| ----------- | --------------------------------------------------------------------- |
| **能力域**     | 专家身份、边界、协作方式，以及可直接复制到目标工作目录的持续性约束                                     |
| **技能**      | 按需加载的能力目录，含入口、参考资料、脚本和资源                                              |
| **MCP 声明**  | 需要接入什么工具、用什么命令和变量，不含宿主专有配置，不包含任何secret                                |
| **环境契约**    | 部署时需要的变量和凭证说明，不含真实值，在自举时自行询问与加入                                       |
| **工作区资产**   | 需要落到项目里的模板、目录或运行种子                                                    |
| **Adapter** | 针对某些专用的适配知识、脱敏示例与集成实现，如opencode 的加载方式可能为 plugin hook，dsh可能针对本能力有独立的界面 |
| **验证用例**    | 可重复的迁移验收契约，确认自举结果真的能被宿主使用                                             |


- **适合**：团队有多个专家角色、会更换 Agent 框架
- 希望把已有能力作为可交接资产保存。

## 开始使用

两件事，分开看：**打包**（做出一个元数据包）和**自举**（把包部署到目标智能体）。打包归本仓库的编制技能；自举归包自己——在目标宿主现场执行。

### 一、如何打包

打包在**你的智能体**里做：把本仓库的 `agent-metadata-package` 技能加载进去，然后让它照这个技能来。

```text
skills/agent-metadata-package/
├── SKILL.md          # 技能入口
├── references/       # 结构与字段细则
├── assets/           # 包骨架与能力域骨架
└── examples/         # dedge-datacenter、llm-wiki-vault 两个完整示例
```

技能会带着智能体走完这几步：

1. 建立包结构和根清单 `package-metadata.json`；
2. 定义能力域（`SOUL.md`、`USER.md`、`AGENTS.md` + `capability-metadata.json`）；
3. 组织共享技能、MCP 声明、环境契约和工作区资产；
4. 编写 Adapter（仅在确有已知宿主经验时）；
5. 补足 `BOOTSTRAP.md`；
6. 执行发布前静态检查。

注意分工：编制技能只管**编制**，不碰解包、自举和部署——那些写在产出的包根目录 `BOOTSTRAP.md` 里，由目标宿主现场执行。完整指令见 [skills/agent-metadata-package/SKILL.md](skills/agent-metadata-package/SKILL.md)，字段与目录细节见 [包结构与元数据](docs/01-package-and-metadata.md)。

### 二、如何自举

拿到一个元数据包之后，交给**目标智能体**就行。两种做法等价：

**方式 A —— 把压缩包丢给它。** 包归档（`.zip` / `.tar.gz`）直接拖给目标智能体，或在对话里标记这个压缩包，让它解压、读包根。

**方式 B —— 只给它 `BOOTSTRAP.md`。** 把包根 `BOOTSTRAP.md` 交给目标智能体，它同样会回到包根开始自举。

不管走哪条，路径都是同一条：

```text
读取 README、package-metadata.json 和 BOOTSTRAP.md
    ↓
识别当前宿主及其实际能力
    ↓
选择能力域，确认目标工作区和修改范围
    ↓
按需收集配置，将资产映射到宿主
    ↓
检查技能、MCP、环境和工作区资产是否真的生效
```

往后的事，由目标宿主自己完成：如果能分开加载 `SOUL` / `USER` / `AGENTS`，就分别落位；如果只能合并，就按语义合并。Adapter 文档能帮你少摸索一会儿，但**它不是事实来源**——撞上版本差异，以当前宿主的官方文档、配置格式和实际运行结果为准。

做完必须**验证**，而且验的是“能用”，不是“有文件”：身份和边界生效了，技能真的被宿主发现或加载了，MCP 连上了，必填变量设置了且没泄漏值，工作区资产躺在实际使用位置并且读得到。

**文件存在，不等于自举成功。**

自举流程、适配知识和安全边界见 [自举、适配与安全](docs/02-bootstrap-and-security.md)；验收门槛见 [发布与验证](docs/03-release-and-verification.md)。

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

- `docs/` 定义元数据包应包含什么资产、如何自举、如何验证。
- `skills/agent-metadata-package/` 是编制技能，智能体加载后按它完成包的创建、维护、审查和发布准备。
- `dist/` 是测试沙箱，不属于规范内容，正式发布前必须排空。

## 如何阅读本项目


| 文档                                                                                 | 适合在什么时候读                                                                 |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| [体系概览](docs/00-overview.md)                                                        | 第一次接触本规范，需要理解目标、边界和适用范围。                                                 |
| [包结构与元数据](docs/01-package-and-metadata.md)                                         | 需要创建包、维护目录，或编写根 `package-metadata.json` 与能力域 `capability-metadata.json`。 |
| [自举、适配与安全](docs/02-bootstrap-and-security.md)                                      | 需要把资产部署到 Hermes、OpenCode 等宿主，或处理 Secret 与工作区资产。                          |
| [发布与验证](docs/03-release-and-verification.md)                                       | 需要打包发布，或验收一次自举是否真正成功。                                                    |
| [skills/agent-metadata-package/SKILL.md](skills/agent-metadata-package/SKILL.md)   | 需要知道智能体在做包时会执行哪些步骤。                                                      |
| [skills/agent-metadata-package/examples/](skills/agent-metadata-package/examples/) | 想直接看一个真实的包长什么样。                                                          |


按角色的最短路径：

- **只想搞清这套规范在解决什么** → [体系概览](docs/00-overview.md)。
- **要动手做包** → 把技能加载进你的智能体，再对照 [包结构与元数据](docs/01-package-and-metadata.md)。
- **要把包落到某个宿主上** → 让目标智能体读包根 `BOOTSTRAP.md`，遇到差异再查 [自举、适配与安全](docs/02-bootstrap-and-security.md)。
- **要发布或验收** → [发布与验证](docs/03-release-and-verification.md)。

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


安全禁令、协议结构和验收门槛使用“必须 / 不得”；Adapter 内容、验证记录和部署后检查使用“应”；归档格式、目录组织、CI 与宿主命令使用“建议 / 示例”。对于由当前宿主、项目状态和用户授权决定的部署处置，自举智能体可自行判断，但应如实报告结果。

## 状态

当前规范版本为 `0.2.2`（协议版本 `0.2`）。协议版本与包内容版本分开维护，规则见 [发布与验证](docs/03-release-and-verification.md)。版本间的规则变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 贡献

欢迎用 Issue 或 Pull Request 一起把它改得更好。提交前请确认：

1. 规范文档（`docs/`）与编制技能（`skills/agent-metadata-package/`）内容一致。
2. `dist/` 已清空，只保留 `.gitignore` 和 `README.md`。
3. 规约规则变更已在根 `CHANGELOG.md` 和技能目录 `CHANGELOG.md` 同步追加记录（两份内容必须一致）。

## 许可证

本项目采用 MIT 许可证，见 [LICENSE](LICENSE)。

智能体元数据包是独立产物；其许可证由包的编制者自行定义，不受本项目许可证约束。