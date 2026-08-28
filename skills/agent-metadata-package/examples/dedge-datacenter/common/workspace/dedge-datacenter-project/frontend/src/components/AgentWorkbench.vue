<template>
  <div class="shell-container">
    <div class="shell">
      <header class="topbar" :class="{ collapsed: isHeaderCollapsed }">
        <div class="brand">
          <p class="eyebrow">dedge datacenter MVP</p>
          <h1 class="page-title">Agent 展示工作台</h1>
        </div>
        <div class="status-group">
          <span class="pill" :class="wsConnected ? 'ok' : 'warn'">
            {{ wsConnected ? 'WS 已连接' : 'WS 未连接' }}
          </span>
          <span class="pill client-pill">
            clientId: {{ clientId ?? '等待分配' }}
          </span>
          <div class="mode-switch" role="group" aria-label="工作模式切换">
            <button
              type="button"
              class="mode-option"
              :class="{ active: mode === 'test' }"
              @click="switchMode('test')"
            >
              测试模式
            </button>
            <button
              type="button"
              class="mode-option"
              :class="{ active: mode === 'production' }"
              @click="switchMode('production')"
            >
              生产模式
            </button>
          </div>
          <button class="refresh-button" type="button" @click="reloadAll()">手动刷新</button>
        </div>
      </header>

      <main class="layout" :class="{ 'ai-open': aiDrawer.isDrawerOpen.value }" >
        <aside
          class="sidebar"
          :class="{ collapsed: isSidebarCollapsed }"
          ref="sidebarEl"
          @scroll="onSidebarScroll"
        >
          <template v-if="!isSidebarCollapsed">
            <section v-if="mode === 'test'" class="card">
              <h2 class="card-title">Agent 最近指令</h2>
              <div class="hint-stack">
                <p class="muted">dashboardId: {{ currentView?.dashboardId ?? '未设置' }}</p>
                <p class="muted">catalogNodeId: {{ currentView?.catalogNodeId ?? '未设置' }}</p>
                <p class="hint-note">说明：currentView 仅表示 Agent 最近希望指定 WS client 跳转到哪里，不作为 iframe 当前展示真相源。</p>
              </div>
            </section>

            <section class="card tree-card">
              <h2 class="card-title">目录树</h2>
              <CatalogTree
                :nodes="catalogTree"
                :selected-node-id="selectedCatalogNodeId"
                :selected-dashboard-id="selectedDashboardId"
                @select-node="handleSelectNode"
                @select-dashboard="handleSelectDashboard"
              />
            </section>

            <section class="card detail-card">
              <div class="detail-header">
                <div class="detail-header-part1">
                  <h2 class="card-title">{{ currentDashboard?.title ?? '等待 dashboard' }}</h2>
                  <p class="muted">{{ currentDashboard?.description ?? '当前尚无 dashboard 描述' }}</p>
                </div>
              </div>

              <dl v-if="mode === 'test'" class="meta-grid">
                <div class="meta-item">
                  <dt>UID</dt>
                  <dd>{{ currentDashboard?.grafana?.dashboardUid ?? '未设置' }}</dd>
                </div>
                <div class="meta-item">
                  <dt>Dashboard URL</dt>
                  <dd class="break-all">{{ currentDashboard?.grafana?.dashboardUrl ?? '未设置' }}</dd>
                </div>
                <div class="meta-item">
                  <dt>Iframe</dt>
                  <dd class="break-all">{{ selectedIframeUrl ?? '未设置' }}</dd>
                </div>
                <div class="meta-item">
                  <dt>更新时间</dt>
                  <dd>{{ currentDashboard?.updatedAt ?? currentView?.updatedAt ?? '未设置' }}</dd>
                </div>
                <div class="meta-item full">
                  <dt>Tags</dt>
                  <dd>{{ currentDashboard?.tags?.join(' / ') ?? '未设置' }}</dd>
                </div>
              </dl>
            </section>

            <section v-if="mode === 'test'" class="card dashboard-card">
              <h2 class="card-title">Dashboard 列表</h2>
              <p v-if="dashboards.length === 0" class="muted">当前还没有 dashboard 条目。</p>
              <ul v-else class="dashboard-list">
                <li v-for="dashboard in dashboards" :key="dashboard.id">
                  <button
                    type="button"
                    class="dashboard-button"
                    :class="{ active: selectedDashboardId === dashboard.id }"
                    @click="selectDashboard(dashboard.id)"
                  >
                    <span class="dashboard-row">
                      <span class="dashboard-icon material-symbols-outlined" aria-hidden="true">insert_chart</span>
                      <span class="dashboard-title">{{ dashboard.title }}</span>
                    </span>
                    <span class="dashboard-id">{{ dashboard.id }}</span>
                  </button>
                </li>
              </ul>
            </section>
          </template>
        </aside>

        <div class="content-wrapper"">
          <button
            type="button"
            class="border-toggle border-toggle-top"
            :title="isHeaderCollapsed ? '展开 header' : '折叠 header'"
            @click="isHeaderCollapsed = !isHeaderCollapsed"
          >
            <span class="material-symbols-outlined">
              {{ isHeaderCollapsed ? 'expand_more' : 'expand_less' }}
            </span>
          </button>
          <button
            type="button"
            class="border-toggle border-toggle-left"
            :title="isSidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'"
            @click="isSidebarCollapsed = !isSidebarCollapsed"
          >
            <span class="material-symbols-outlined">
              {{ isSidebarCollapsed ? 'chevron_right' : 'chevron_left' }}
            </span>
          </button>

          <section class="content" ref="contentEl" @scroll="onContentScroll">
            <article class="card iframe-card">
              <div v-if="mode === 'test'" class="iframe-header">
              <div>
                <h2 class="card-title">Grafana iframe</h2>
                <p class="muted">前端只负责展示 catalog 选中的 iframe 页面，不承担编辑能力。</p>
              </div>
            </div>
            <iframe
              v-if="selectedIframeUrl"
              :key="`${selectedIframeUrl}-${iframeReloadKey}`"
              :src="selectedIframeUrl"
              class="grafana-frame"
              title="Grafana iframe"
            />
            <div v-else class="iframe-empty">
              <div class="empty-state">
                <p class="empty-title">等待数据源</p>
                <p class="empty-body">等待 Agent 通过 Grafana MCP 创建/修改 dashboard，并回写 currentView。</p>
              </div>
            </div>
          </article>
        </section>
        </div>

        <!-- 右侧工具栏 -->
        <RightSidebar
          v-show="!aiDrawer.isDrawerOpen.value"
          :top-buttons="sidebarButtons.topButtons.value"
          :bottom-buttons="sidebarButtons.bottomButtons.value"
          :show-status="false"
          @button-click="handleSidebarButtonClick"
        />
      </main>
    </div>
    <!-- AI Agent 抽屉组件 -->
    <AIAgentDrawer
      :is-open="aiDrawer.isDrawerOpen.value"
      :is-full-view="aiDrawer.isFullView.value"
      :title="'DEdge Agent'"
      :status="aiDrawer.status.value"
      :current-model="aiDrawer.currentModel.value"
      :current-agent="aiDrawer.currentAgent.value"
      :models="aiDrawer.models.value"
      :model-vendors="aiDrawer.modelVendors.value"
      :grouped-models="aiDrawer.groupedModels.value"
      :agents="aiDrawer.agents.value"
      :sessions="aiDrawer.sessions.value"
      :active-session-id="aiDrawer.activeSessionId.value"
      :current-messages="aiDrawer.currentMessages.value"
      :is-typing="aiDrawer.isTyping.value"
      :is-new-session="aiDrawer.isNewSession.value"
      :input-text="aiDrawer.inputText.value"
      :connection-status="aiDrawer.connectionStatus.value"
      :ws-connection-state="aiDrawer.wsConnectionState.value"
      :backend-server-url="aiDrawer.backendWsUrl.value"
      :is-server-connecting="aiDrawer.isServerConnecting.value"
      :recent-server-urls="aiDrawer.recentServerUrls.value"
      :red-dot-info="aiDrawer.redDotInfo.value"
      :session-unread-map="aiDrawer.sessionUnreadMap.value"
      :get-session-is-waiting="(sid) => aiDrawer.getSessionIsWaiting(sid)"
      :current-pending-files="aiDrawer.currentPendingFiles.value"
      @close="aiDrawer.close"
      @expand="aiDrawer.expandToFullView"
      @collapse="aiDrawer.collapseToDrawer"
      @send-message="aiDrawer.handleAiSendMessage"
      @sendcmd="aiDrawer.handleAiSendCmdMessage"
      @send-raw-message="aiDrawer.handleAiSendRawMessage"
      @stop-message="aiDrawer.handleAiStopMessage"
      @session-change="aiDrawer.handleSessionChange"
      @delete-session="aiDrawer.deleteSession"
      @model-change="aiDrawer.handleModelChange"
      @agent-change="aiDrawer.handleAgentChangeWithLookup"
      @create-new-session="aiDrawer.handleCreateNewSession"
      @attach="aiDrawer.handlers.attach"
      @voice="aiDrawer.handlers.voice"
      @add="aiDrawer.handlers.add"
      @input-change="aiDrawer.setInputText"
      @connect-server="aiDrawer.handleAiServerConnect"
      @file-select="aiDrawer.handleFileSelect"
      @file-remove="aiDrawer.handleFileRemove"
    />
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import CatalogTree from './CatalogTree.vue'
import RightSidebar from './dedge/RightSidebar.vue'
import { useSidebarButtons } from '../composables/useSidebarButtons.js'
import { AIAgentDrawer, useAIAgentDrawer } from 'dedge-ai-agent-frontend'

type CatalogNode = {
  id?: string
  title?: string
  type?: 'directory' | 'dashboard-ref'
  dashboardId?: string | null
  children?: CatalogNode[]
}

type DashboardEntry = {
  id: string
  title?: string
  description?: string
  grafana?: {
    dashboardUid?: string
    dashboardUrl?: string
    dashboardShareUrl?: string | null
    iframeUrl?: string | null
  }
  tags?: string[]
  updatedAt?: string | null
}

type CurrentView = {
  catalogNodeId: string | null
  dashboardId: string | null
  iframeUrl: string | null
  updatedAt: string | null
} | null

type RefreshMessage = {
  type: 'frontend-refresh'
  reason: string
  dashboardId: string | null
  catalogNodeId: string | null
  targetClientId: string
  sentAt: string
}

type SessionMessage = {
  type: 'frontend-session'
  clientId: string
}

const api = axios.create({
  baseURL: '/api',
})

type WorkbenchMode = 'test' | 'production'
const mode = ref<WorkbenchMode>('production')

const isSidebarCollapsed = ref(false)
const isHeaderCollapsed = ref(false)

const catalogTree = ref<CatalogNode[]>([])
const dashboards = ref<DashboardEntry[]>([])
const currentView = ref<CurrentView>(null)
const selectedDashboardId = ref<string | null>(null)
const selectedCatalogNodeId = ref<string | null>(null)
const dashboardDetailMap = ref<Record<string, DashboardEntry>>({})
const lastRefreshReason = ref<string | null>(null)
const wsConnected = ref(false)
const clientId = ref<string | null>(null)
// 已发送出去的 clientId，用于检测 clientId 是否被刷新
let sentClientId: string | null = null

// 滚动阴影检测（通过 CSS 变量控制 opacity，开销极小）
const sidebarEl = ref<HTMLElement | null>(null)
const contentEl = ref<HTMLElement | null>(null)

function updateShadowVars(el: HTMLElement) {
  const overflow = el.scrollHeight > el.clientHeight + 1
  el.style.setProperty('--shadow-top', overflow && el.scrollTop > 2 ? '1' : '0')
  el.style.setProperty('--shadow-bottom', overflow && el.scrollTop + el.clientHeight < el.scrollHeight - 2 ? '1' : '0')
}

function onSidebarScroll() { updateShadowVars(sidebarEl.value!) }
function onContentScroll() { updateShadowVars(contentEl.value!) }

function switchMode(nextMode: WorkbenchMode) {
  mode.value = nextMode
  nextTick(() => {
    updateShadowVars(sidebarEl.value!)
    updateShadowVars(contentEl.value!)
  })
}

// ==================== AI Agent Drawer ====================
const aiDrawer = useAIAgentDrawer({
  getGlobalData: () => ({
    userId: 'datacenter',
  }),
  onAgentChange: (agent: unknown) => {
    console.log('切换智能体/功能:', agent)
  },
  beforeSend: ({ data, session }) => {
    if (!clientId.value) return data
    const result = {
      ...data,
    }
    // 第一条消息，或 clientId 被刷新后（sentClientId 为空）时，在消息末尾追加 clientId 标识
    if (data.messages.length === 1 || !sentClientId) {
      const content = (result.content || '') + '\nWS 客户端标识 clientId为' + clientId.value
      ;result.content = content
      ;data.messages[data.messages.length - 1].content = content
      sentClientId = clientId.value
    }
    return result
  },
})

// ==================== 右侧工具栏 ====================
const sidebarButtons = useSidebarButtons()

const handleSidebarButtonClick = (buttonId: string) => {
  // if (buttonId === 'agent') {
    aiDrawer.toggle()
  // }
  sidebarButtons.setActiveButton(buttonId)
}

let socket: WebSocket | null = null
let resizeObserver: ResizeObserver | null = null

const currentDashboard = computed(() => {
  const dashboardId = selectedDashboardId.value
  return dashboardId ? dashboardDetailMap.value[dashboardId] ?? null : null
})

const selectedIframeUrl = computed(() => {
  return currentDashboard.value?.grafana?.iframeUrl ?? currentView.value?.iframeUrl ?? null
})

const iframeReloadKey = ref(0)

async function reloadAll(options?: { applyAgentHint?: boolean }) {
  const [treeResponse, dashboardsResponse, currentViewResponse] = await Promise.all([
    api.get<CatalogNode[]>('/catalog/tree'),
    api.get<DashboardEntry[]>('/dashboards'),
    api.get<CurrentView>('/current-view'),
  ])

  catalogTree.value = treeResponse.data
  dashboards.value = dashboardsResponse.data
  currentView.value = currentViewResponse.data
  dashboardDetailMap.value = Object.fromEntries(
    dashboardsResponse.data.map((dashboard) => [dashboard.id, dashboard]),
  )

  iframeReloadKey.value++

  if (options?.applyAgentHint && currentView.value) {
    await applyAgentHint(currentView.value)
    return
  }

  const dashboardId = selectedDashboardId.value
  if (dashboardId && !dashboardDetailMap.value[dashboardId]) {
    await loadDashboardDetail(dashboardId)
  }
}

async function loadDashboardDetail(dashboardId: string) {
  const response = await api.get<DashboardEntry>(`/dashboards/${dashboardId}`)
  dashboardDetailMap.value = {
    ...dashboardDetailMap.value,
    [dashboardId]: response.data,
  }
}

async function selectDashboard(dashboardId: string) {
  selectedDashboardId.value = dashboardId
  const matchedNode = findNodeByDashboardId(catalogTree.value, dashboardId)
  selectedCatalogNodeId.value = matchedNode?.id ?? selectedCatalogNodeId.value
  await loadDashboardDetail(dashboardId)
}

function findFirstDashboardId(node: CatalogNode): string | null {
  if (node.dashboardId) {
    return node.dashboardId
  }
  for (const child of node.children ?? []) {
    const dashboardId = findFirstDashboardId(child)
    if (dashboardId) {
      return dashboardId
    }
  }
  return null
}

function findNodeById(nodes: CatalogNode[], nodeId: string): CatalogNode | null {
  for (const node of nodes) {
    if (node.id === nodeId) {
      return node
    }
    const matchedChild = findNodeById(node.children ?? [], nodeId)
    if (matchedChild) {
      return matchedChild
    }
  }
  return null
}

function findNodeByDashboardId(nodes: CatalogNode[], dashboardId: string): CatalogNode | null {
  for (const node of nodes) {
    if (node.dashboardId === dashboardId) {
      return node
    }
    const matchedChild = findNodeByDashboardId(node.children ?? [], dashboardId)
    if (matchedChild) {
      return matchedChild
    }
  }
  return null
}

async function applyAgentHint(view: NonNullable<CurrentView>) {
  selectedCatalogNodeId.value = view.catalogNodeId

  if (view.catalogNodeId) {
    const hintedNode = findNodeById(catalogTree.value, view.catalogNodeId)
    const dashboardId = hintedNode ? findFirstDashboardId(hintedNode) : null
    if (dashboardId) {
      await selectDashboard(dashboardId)
      return
    }
  }

  if (view.dashboardId) {
    await selectDashboard(view.dashboardId)
  }
}

function handleSelectNode(node: CatalogNode) {
  selectedCatalogNodeId.value = node.id ?? null
}

function handleSelectDashboard(dashboardId: string) {
  void selectDashboard(dashboardId)
}
function simpleUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0; // 0-15 的随机整数
    const v = c === 'x' ? r : (r & 0x3 | 0x8); // v4 规范要求固定版本位
    return v.toString(16);
  });
}
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const requestedClientId = clientId.value ?? simpleUUID()
  socket = new WebSocket(`${protocol}//${window.location.host}/ws/frontend?clientId=${encodeURIComponent(requestedClientId)}`)

  socket.addEventListener('open', () => {
    wsConnected.value = true
  })

  socket.addEventListener('message', async (event) => {
    const message = JSON.parse(event.data) as RefreshMessage | SessionMessage
    if (message.type === 'frontend-session') {
      clientId.value = message.clientId
      // clientId 被刷新，清空已发送的标识以便下次发送时重新追加
      sentClientId = null
      return
    }
    lastRefreshReason.value = `${message.reason} @ ${message.sentAt}`
    await reloadAll()

    if (message.catalogNodeId || message.dashboardId) {
      await applyAgentHint({
        catalogNodeId: message.catalogNodeId,
        dashboardId: message.dashboardId,
        iframeUrl: null,
        updatedAt: message.sentAt,
      })
    }
  })

  socket.addEventListener('close', () => {
    wsConnected.value = false
    socket = null
    window.setTimeout(connectWebSocket, 1000)
  })
}

onMounted(async () => {
  await reloadAll({ applyAgentHint: true })
  connectWebSocket()
  updateShadowVars(sidebarEl.value!)
  updateShadowVars(contentEl.value!)
  // 内容变化时自动更新阴影（数据加载、切换等场景）
  resizeObserver = new ResizeObserver(() => {
    updateShadowVars(sidebarEl.value!)
    updateShadowVars(contentEl.value!)
  })
  resizeObserver.observe(sidebarEl.value!)
  resizeObserver.observe(contentEl.value!)
})

onBeforeUnmount(() => {
  socket?.close()
  resizeObserver?.disconnect()
})
</script>

<style scoped>
:global(body) {
  --surface: #f8f9fa;
  --surface-bright: #ffffff;
  --surface-container-low: #f3f4f5;
  --surface-container-lowest: #ffffff;
  --surface-container-high: #eceeef;
  --on-surface: #191c1d;
  --on-surface-variant: #44474e;
  --outline-variant: #c4c7c5;
  --primary: #0045db;
  --primary-container: #285eff;
  --on-primary: #ffffff;
  --on-primary-container: #ffffff;
  --tertiary: #9d3000;
  --tertiary-fixed: #ffdbd0;
  --shadow-color: rgba(25, 28, 29, 0.06);
  --ambient-shadow: 0px 3px 10px var(--shadow-color);

  margin: 0;
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--surface);
  color: var(--on-surface);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

:global(*) {
  box-sizing: border-box;
}

button {
  font: inherit;
}

h1,
h2,
p,
dl,
dd,
dt,
ul,
li {
  margin: 0;
  padding: 0;
}

.shell {
  height: 100vh;
  padding: 32px;
  background: var(--surface);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.shell-container {
  height: 100%;
  display: flex;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  overflow: hidden;
  max-height: 200px;
  opacity: 1;
  margin-bottom: 32px;
  transition: max-height 200ms ease, opacity 200ms ease, margin-bottom 200ms ease;
}

.brand {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--primary);
  font-size: 12px;
  font-weight: 600;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--on-surface);
}

.status-group {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
}

.pill.ok {
  background: rgba(0, 69, 219, 0.08);
  color: var(--primary);
}

.pill.warn {
  background: var(--tertiary-fixed);
  color: var(--tertiary);
}

.client-pill {
  background: var(--surface-container-low);
  color: var(--on-surface-variant);
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.refresh-button {
  border: 0;
  border-radius: 999px;
  padding: 10px 18px;
  font-size: 13px;
  font-weight: 600;
  color: var(--on-primary);
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-container) 100%);
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(0, 69, 219, 0.18);
  transition: transform 120ms ease, box-shadow 120ms ease;
}

.refresh-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(0, 69, 219, 0.24);
}

.refresh-button:active {
  transform: translateY(0);
}

.topbar.collapsed {
  max-height: 0;
  opacity: 0;
  margin-bottom: 0;
  pointer-events: none;
}

.mode-switch {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: var(--surface-container-low);
  padding: 4px;
  gap: 4px;
}

.mode-option {
  border: 0;
  border-radius: 999px;
  padding: 7px 14px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  color: var(--on-surface-variant);
  background: transparent;
  cursor: pointer;
  transition: background 140ms ease, color 140ms ease;
}

.mode-option:hover {
  color: var(--on-surface);
}

.mode-option.active {
  color: var(--on-primary);
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-container) 100%);
  box-shadow: 0 2px 8px rgba(0, 69, 219, 0.18);
}

.layout {
  flex: 1;
  min-height: 0;
  display: flex;
}

.sidebar,
.content {
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.sidebar::-webkit-scrollbar,
.content::-webkit-scrollbar {
  display: none;
}

/* 顶部阴影：position: sticky 固定在视口顶部，z-index 高于内容 */
.sidebar::before,
.content::before {
  content: '';
  display: block;
  position: sticky;
  top: 0;
  height: 0;
  z-index: 2;
  pointer-events: none;
  box-shadow: 0px 0px 20px 4px rgba(25, 28, 29, 0.4);
  opacity: var(--shadow-top, 0);
  transition: opacity 200ms ease;
}

/* 底部阴影 */
.sidebar::after,
.content::after {
  content: '';
  display: block;
  position: sticky;
  bottom: 0;
  height: 0;
  z-index: 2;
  pointer-events: none;
  box-shadow: 0px 0px 20px 4px rgba(25, 28, 29, 0.4);
  opacity: var(--shadow-bottom, 0);
  transition: opacity 200ms ease;
}

.sidebar {
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
  margin-right: 32px;
  transition: flex-basis 200ms ease, margin-right 200ms ease, opacity 200ms ease;
}

.sidebar.collapsed {
  flex-basis: 0;
  margin-right: 0;
  opacity: 0;
  pointer-events: none;
  overflow: hidden;
}

.content-wrapper {
  flex: 1;
  min-width: 0;
  position: relative;
  margin-right: 32px;
}

.content-wrapper .border-toggle {
  opacity: 0;
  pointer-events: none;
  transition: opacity 180ms ease, background 140ms ease, color 140ms ease, box-shadow 140ms ease;
}

.content-wrapper:hover .border-toggle {
  opacity: 1;
  pointer-events: auto;
}

.content {
  height: 100%;
  width: 100%;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  display: flex;
  flex-direction: column;
}

.layout.ai-open .content-wrapper {
  margin-right: 0;
}

.border-toggle {
  position: absolute;
  height: 18px;
  min-width: 30px;
  border-radius: 999px;
  border: 0;
  padding: 0 10px;
  background: var(--surface-container-high);
  color: var(--on-surface-variant);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.border-toggle:hover {
  background: var(--primary);
  color: var(--on-primary);
}

.border-toggle .material-symbols-outlined {
  font-size: 14px;
  line-height: 1;
}

.border-toggle-top {
  top: 0;
  left: 50%;
  transform: translate(-50%, -50%);
}

.border-toggle-left {
  left: 0;
  top: 50%;
  transform: translate(-50%, -50%) rotate(90deg);
}

.border-toggle-left .material-symbols-outlined {
  transform: rotate(-90deg);
}

.card {
  border-radius: 12px;
  background: var(--surface-container-lowest);
  box-shadow: var(--ambient-shadow);
  padding: 24px;
  transition: background 160ms ease, box-shadow 160ms ease;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.3;
  color: var(--on-surface);
  margin-bottom: 16px;
}

.muted {
  color: var(--on-surface-variant);
  font-size: 13px;
  line-height: 1.5;
}

.small {
  font-size: 12px;
}

.hint-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hint-note {
  color: var(--on-surface-variant);
  font-size: 12px;
  line-height: 1.5;
  margin-top: 4px;
}

.tree-card,
.dashboard-card {
  padding: 20px;
  background: var(--surface-container-low);
}

.dashboard-card {
  margin-top: 24px;
}

.sidebar .detail-card {
  margin-top: 24px;
  padding: 20px;
  background: var(--surface-container-low);
}

.sidebar .detail-card .meta-grid {
  grid-template-columns: 1fr;
}

.dashboard-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dashboard-button {
  width: 100%;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--on-surface);
  cursor: pointer;
  text-align: left;
  transition:
    background 140ms ease,
    color 140ms ease,
    box-shadow 140ms ease;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 9px 12px;
}

.dashboard-button:hover {
  background: rgba(0, 69, 219, 0.06);
}

.dashboard-button.active {
  background: var(--primary);
  color: var(--on-primary);
  box-shadow: 0 4px 12px rgba(0, 69, 219, 0.22);
}

.dashboard-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dashboard-icon {
  flex: 0 0 auto;
  font-size: 18px;
  line-height: 1;
  color: var(--on-surface-variant);
}

.dashboard-button:hover .dashboard-icon {
  color: var(--primary);
}

.dashboard-button.active .dashboard-icon {
  color: var(--on-primary);
}

.dashboard-title {
  font-size: 13px;
  font-weight: 600;
  color: inherit;
}

.dashboard-id {
  font-size: 11px;
  padding-left: 26px;
  color: var(--on-surface-variant);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.dashboard-button.active .dashboard-id {
  color: rgba(255, 255, 255, 0.8);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.detail-header-part1 {
  width: 100%;
  word-break: break-all;
}

.detail-header .card-title {
  margin-bottom: 6px;
}

.iframe-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-item.full {
  grid-column: 1 / -1;
}

.meta-item dt {
  color: var(--on-surface-variant);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.meta-item dd {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--on-surface);
}

.break-all {
  word-break: break-all;
}

.iframe-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.iframe-header .card-title {
  margin-bottom: 4px;
}

.grafana-frame {
  width: 100%;
  flex: 1;
  min-height: 480px;
  border: 0;
  border-radius: 12px;
  background: var(--surface-container-low);
  display: block;
}

.iframe-empty {
  flex: 1;
  min-height: 320px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: var(--surface-container-low);
  text-align: center;
  padding: 32px;
}

.empty-state {
  max-width: 420px;
}

.empty-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--on-surface);
  margin-bottom: 8px;
}

.empty-body {
  font-size: 14px;
  color: var(--on-surface-variant);
  line-height: 1.5;
}

@media (max-width: 1080px) {
  .shell {
    padding: 20px;
  }

  .layout {
    flex-direction: column;
  }

  .sidebar,
  .content-wrapper {
    margin-right: 0;
  }

  .sidebar {
    flex-basis: auto;
    width: 100%;
    margin-bottom: 20px;
  }

  .sidebar.collapsed {
    flex-basis: 0;
    margin-bottom: 0;
  }

  .content-wrapper {
    margin-bottom: 20px;
  }

  .topbar,
  .detail-header,
  .iframe-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .meta-grid {
    grid-template-columns: 1fr;
  }

  .status-group {
    width: 100%;
  }
}
</style>