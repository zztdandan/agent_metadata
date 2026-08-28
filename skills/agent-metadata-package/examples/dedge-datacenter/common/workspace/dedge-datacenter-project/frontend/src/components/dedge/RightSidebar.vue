<script setup>
import SidebarButton from './SidebarButton.vue'
import StatusIndicator from './StatusIndicator.vue'

const props = defineProps({
  /** 是否显示状态指示器 */
  showStatus: {
    type: Boolean,
    default: true,
  },
  /** 状态指示器颜色 */
  statusColor: {
    type: String,
    default: 'emerald',
    validator: (value) => ['emerald', 'amber', 'red', 'blue'].includes(value),
  },
  /** 顶部按钮列表 */
  topButtons: {
    type: Array,
    default: () => [],
  },
  /** 底部按钮列表 */
  bottomButtons: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['buttonClick'])

const handleButtonClick = (buttonId) => {
  emit('buttonClick', buttonId)
}
</script>

<template>
  <aside class="right-sidebar">
    <!-- 顶部按钮区域 -->
    <div class="sidebar-top-buttons">
      <SidebarButton
        v-for="button in topButtons"
        :key="button.id"
        :icon="button.icon"
        :tooltip="button.tooltip"
        :active="button.active"
        :filled="button.filled"
        :badge="button.badge"
        @click="handleButtonClick(button.id)"
      />
    </div>

    <!-- 底部按钮区域 -->
    <div class="sidebar-bottom-buttons">
      <SidebarButton
        v-for="button in bottomButtons"
        :key="button.id"
        :icon="button.icon"
        :tooltip="button.tooltip"
        :active="button.active"
        :badge="button.badge"
        @click="handleButtonClick(button.id)"
      />

      <!-- 状态指示器 -->
      <StatusIndicator
        v-if="showStatus"
        :color="statusColor"
        pulse
      />
    </div>
  </aside>
</template>

<style scoped>
.right-sidebar {
  box-sizing: border-box;
  height: 100%;
  width: 64px;
  z-index: 40;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 0;
  border-radius: 8px;
  /* tailwind shadow-lg + ring-2 */
  box-shadow:
    0 10px 15px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -4px rgba(0, 0, 0, 0.1),
    0 0 0 2px rgba(0, 69, 219, 0.1); /* ring-primary/10 */
}

.sidebar-top-buttons {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}
.sidebar-top-buttons > * + * {
  margin-top: 32px;
}

.sidebar-bottom-buttons {
  margin-top: auto;
  padding-bottom: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.sidebar-bottom-buttons > * + * {
  margin-top: 24px;
}
</style>
