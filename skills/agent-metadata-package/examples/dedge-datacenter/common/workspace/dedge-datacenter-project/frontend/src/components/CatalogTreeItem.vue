<template>
  <li class="tree-node">
    <button
      type="button"
      class="node-button"
      :class="{
        'is-directory': isDirectory,
        'is-leaf': !isDirectory,
        'is-active': isActive,
      }"
      :style="{ paddingLeft: `${12 + depth * 18 + (hasChildren ? 0 : 7)}px` }"
      @click="handleClick"
    >
      <span
        v-if="isDirectory && hasChildren"
        class="toggle-icon material-symbols-outlined"
        aria-hidden="true"
      >
        {{ expanded ? 'expand_more' : 'chevron_right' }}
      </span>
      <span class="node-icon material-symbols-outlined" aria-hidden="true">
        {{ isDirectory ? (expanded ? 'folder_open' : 'folder') : 'insert_chart' }}
      </span>
      <span class="node-label">{{ node.title ?? node.id ?? '未命名' }}</span>
    </button>
    <ul v-if="isDirectory && expanded && hasChildren" class="node-children">
      <CatalogTreeItem
        v-for="child in node.children"
        :key="child.id ?? child.title"
        :node="child"
        :depth="depth + 1"
        :selected-node-id="selectedNodeId"
        :selected-dashboard-id="selectedDashboardId"
        @select-node="emit('selectNode', $event)"
        @select-dashboard="emit('selectDashboard', $event)"
      />
    </ul>
  </li>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { CatalogNode } from './CatalogTree.vue'

const props = withDefaults(
  defineProps<{
    node: CatalogNode
    depth?: number
    selectedNodeId?: string | null
    selectedDashboardId?: string | null
  }>(),
  {
    depth: 0,
  },
)

const emit = defineEmits<{
  selectNode: [node: CatalogNode]
  selectDashboard: [dashboardId: string]
}>()

const isDirectory = computed(() => props.node.type === 'directory')
const hasChildren = computed(() => (props.node.children?.length ?? 0) > 0)

function containsNode(node: CatalogNode, targetId: string): boolean {
  if (node.id === targetId) return true
  for (const child of node.children ?? []) {
    if (containsNode(child, targetId)) return true
  }
  return false
}

const containsSelected = computed(() => {
  if (!props.selectedNodeId) return false
  return containsNode(props.node, props.selectedNodeId)
})

const expanded = ref(containsSelected.value)

watch(containsSelected, (selected) => {
  if (selected) expanded.value = true
})

const isActive = computed(() => {
  if (!isDirectory.value && props.node.dashboardId) {
    return props.selectedDashboardId === props.node.dashboardId
  }
  return props.selectedNodeId === props.node.id
})

function handleClick() {
  if (isDirectory.value) {
    if (hasChildren.value) {
      expanded.value = !expanded.value
    }
    if (props.node.dashboardId) {
      emit('selectNode', props.node)
      emit('selectDashboard', props.node.dashboardId)
    }
  } else {
    emit('selectNode', props.node)
    if (props.node.dashboardId) {
      emit('selectDashboard', props.node.dashboardId)
    }
  }
}
</script>

<style scoped>
.tree-node {
  list-style: none;
}

.node-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 0;
  border-radius: 8px;
  padding: 8px 10px;
  min-height: 36px;
  font: inherit;
  color: var(--on-surface);
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition:
    background 140ms ease,
    color 140ms ease,
    box-shadow 140ms ease;
}

.node-button:hover {
  background: rgba(0, 69, 219, 0.06);
  color: var(--on-surface);
}

.node-button.is-active {
  background: var(--primary);
  color: var(--on-primary);
  box-shadow: 0 4px 12px rgba(0, 69, 219, 0.22);
}

.node-button.is-active .node-label {
  font-weight: 600;
}

.toggle-icon {
  flex: 0 0 18px;
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--on-surface-variant);
  font-size: 18px;
}

.node-button:hover .toggle-icon {
  color: var(--primary);
}

.node-button.is-active .toggle-icon {
  color: var(--on-primary);
}

.node-icon {
  flex: 0 0 auto;
  font-size: 18px;
  line-height: 1;
  color: var(--on-surface-variant);
}

.node-button:hover .node-icon {
  color: var(--primary);
}

.node-button.is-active .node-icon {
  color: var(--on-primary);
}

.node-label {
  flex: 1 1 auto;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-children {
  margin: 2px 0 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>
