# 模式切换需求实现设计文档

## 1. 需求概述

在前端工作台 [AgentWorkbench.vue](file:///d:/dongxin/dedge-datacenter/frontend/src/components/AgentWorkbench.vue) 中增加"测试模式 / 生产模式"切换能力。

- **测试模式**：保持当前所有 UI 与交互不变。
- **生产模式**：对页面做以下精简：
  1. `Agent 最近指令` 卡片：隐藏。
  2. `detail-card` 区域：仅保留 `detail-header` 内容，隐藏下方的 `meta-grid` 详情元数据。
  3. `iframe-card` 区域：仅保留 `iframe` 本身；隐藏 `iframe-header`，且当没有 iframe URL 时不显示 `iframe-empty` 占位。

## 2. 实现方案

### 2.1 状态设计

在 `AgentWorkbench.vue` 的 `<script setup>` 中新增响应式状态：

```ts
type WorkbenchMode = 'test' | 'production'
const mode = ref<WorkbenchMode>('test')
```

默认值为 `'test'`，与现有效果保持一致。

### 2.2 模式切换控件

在顶部状态栏 [`.status-group`](file:///d:/dongxin/dedge-datacenter/frontend/src/components/AgentWorkbench.vue#L8-L16) 最右侧增加分段按钮（segmented control），提供两个选项：

- `测试模式`
- `生产模式`

点击后更新 `mode` 状态。使用现有的按钮与 pill 风格，保持设计系统一致性。

### 2.3 各区域条件渲染

#### 2.3.1 Agent 最近指令卡片

在 [sidebar 第一个 card](file:///d:/dongxin/dedge-datacenter/frontend/src/components/AgentWorkbench.vue#L21-L28) 上增加 `v-if="mode === 'test'"`：

```vue
<section v-if="mode === 'test'" class="card">
  <h2 class="card-title">Agent 最近指令</h2>
  ...
</section>
```

#### 2.3.2 detail-card 区域

在 `detail-card` 内的 [meta-grid](file:///d:/dongxin/dedge-datacenter/frontend/src/components/AgentWorkbench.vue#L81-L102) 上增加 `v-if="mode === 'test'"`，保留 `detail-header` 始终可见：

```vue
<article class="card detail-card">
  <div class="detail-header">...</div>
  <dl v-if="mode === 'test'" class="meta-grid">...</dl>
</article>
```

#### 2.3.3 iframe-card 区域

在 `iframe-card` 内：

- `iframe-header` 增加 `v-if="mode === 'test'"`。
- `iframe-empty` 占位改为 `v-else-if="mode === 'test'"`，确保生产模式下无 iframe URL 时不显示任何内容。

```vue
<article class="card iframe-card">
  <div v-if="mode === 'test'" class="iframe-header">...</div>
  <iframe v-if="selectedIframeUrl" ... />
  <div v-else-if="mode === 'test'" class="iframe-empty">...</div>
</article>
```

### 2.4 样式调整

新增 `.mode-switch` 相关样式，复用现有 `.pill`、按钮圆角与主色渐变风格，确保与顶部状态栏其他元素视觉统一。无需新增全局变量。

## 3. 涉及文件

- [frontend/src/components/AgentWorkbench.vue](file:///d:/dongxin/dedge-datacenter/frontend/src/components/AgentWorkbench.vue)

## 4. 函数与职责划分

本需求以 UI 状态切换为主，逻辑简单，不引入新的工具函数或服务函数。

- **副作用/状态**：`mode` 响应式 ref，记录当前模式。
- **视图逻辑**：模板中使用 `v-if` / `v-else-if` 根据 `mode` 控制各区域渲染。
- **交互**：顶部模式切换按钮更新 `mode` 状态。

## 5. 验收标准

- [ ] 页面默认显示测试模式，所有现有内容与交互保持不变。
- [ ] 切换到生产模式后：
  - [ ] 左侧 `Agent 最近指令` 卡片隐藏。
  - [ ] `detail-card` 仅显示标题、描述与最近事件，隐藏 UID、URL、Tags 等元数据。
  - [ ] `iframe-card` 仅显示 iframe；header 与 empty 占位均不显示。
- [ ] 切换回测试模式后，所有隐藏内容恢复显示。
