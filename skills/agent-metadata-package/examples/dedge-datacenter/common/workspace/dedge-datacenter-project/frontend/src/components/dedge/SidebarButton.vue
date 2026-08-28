<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: {
    type: String,
    required: true,
  },
  tooltip: {
    type: String,
    default: '',
  },
  active: {
    type: Boolean,
    default: false,
  },
  filled: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  badge: {
    type: Object,
    default: () => ({ show: false, count: 0 }),
  },
})

const emit = defineEmits(['click'])

const iconStyle = computed(() =>
  props.filled ? "font-variation-settings: 'FILL' 1;" : '',
)

const handleClick = (event) => {
  if (!props.disabled) {
    emit('click', event)
  }
}
</script>

<template>
  <button
    class="sidebar-btn"
    :class="{ active: active, disabled: disabled }"
    :disabled="disabled"
    @click="handleClick"
  >
    <span
      class="material-symbols-outlined sidebar-btn-icon"
      :style="iconStyle"
    >
      {{ icon }}
    </span>
    <span
      v-if="badge.show"
      class="sidebar-btn-badge"
      :class="{ 'has-count': badge.count > 0 }"
    >
      {{ badge.count > 0 ? (badge.count > 99 ? '99+' : badge.count) : '' }}
    </span>
    <!-- <div
      v-if="tooltip"
      class="sidebar-btn-tooltip"
    >
      &nbsp;
      {{ tooltip }}
    </div> -->
  </button>
</template>

<style scoped>
.sidebar-btn {
  position: relative;
  padding: 12px;
  border-radius: 12px;
  border: 0;
  cursor: pointer;
  background: transparent;
  color: #94a3b8;
  transition: all 400ms cubic-bezier(0.3, 0, 0, 1);
  line-height: 0;
}
.sidebar-btn:active {
  transform: scale(0.95);
}
.sidebar-btn:hover:not(.disabled) {
  color: #0f172a;
  background: rgba(226, 232, 240, 0.5);
}
.sidebar-btn.active {
  background: #fff;
  color: #2563eb;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}
.sidebar-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sidebar-btn-icon {
  font-size: 24px;
  vertical-align: middle;
}

.sidebar-btn-badge {
  position: absolute;
  top: -2px;
  left: -2px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ef4444;
  color: #fff;
  border-radius: 9999px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  z-index: 10;
  min-width: 10px;
  height: 10px;
}
.sidebar-btn-badge.has-count {
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}

.sidebar-btn-tooltip {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%) translateX(100%);
  margin-left: 16px;
  padding: 4px 8px;
  background: #0f172a;
  color: #fff;
  font-size: 10px;
  border-radius: 4px;
  opacity: 0;
  pointer-events: none;
  white-space: nowrap;
  z-index: 50;
  transition: opacity 150ms ease;
}
.sidebar-btn:hover .sidebar-btn-tooltip {
  opacity: 1;
}
</style>
