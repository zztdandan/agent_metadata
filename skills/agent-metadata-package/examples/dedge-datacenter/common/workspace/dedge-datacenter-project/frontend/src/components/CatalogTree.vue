<template>
  <div class="catalog-tree">
    <p v-if="nodes.length === 0" class="tree-empty">当前 catalog 树为空，待 Agent 首次写入。</p>
    <ul v-else class="tree-root">
      <CatalogTreeItem
        v-for="node in nodes"
        :key="node.id ?? node.title"
        :node="node"
        :selected-node-id="selectedNodeId"
        :selected-dashboard-id="selectedDashboardId"
        @select-node="emit('selectNode', $event)"
        @select-dashboard="emit('selectDashboard', $event)"
      />
    </ul>
  </div>
</template>

<script setup lang="ts">
import CatalogTreeItem from './CatalogTreeItem.vue'

export type CatalogNode = {
  id?: string
  title?: string
  type?: 'directory' | 'dashboard-ref'
  dashboardId?: string | null
  children?: CatalogNode[]
}

defineProps<{
  nodes: CatalogNode[]
  selectedNodeId?: string | null
  selectedDashboardId?: string | null
}>()

const emit = defineEmits<{
  selectNode: [node: CatalogNode]
  selectDashboard: [dashboardId: string]
}>()
</script>

<style scoped>
.catalog-tree {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tree-root {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tree-empty {
  margin: 8px 0 0 0;
  color: var(--on-surface-variant);
  font-size: 13px;
  line-height: 1.5;
}
</style>
