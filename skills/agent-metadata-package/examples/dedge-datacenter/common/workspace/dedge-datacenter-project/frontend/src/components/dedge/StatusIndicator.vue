<script setup>
const props = defineProps({
  /** 状态颜色 */
  color: {
    type: String,
    default: 'emerald',
    validator: (value) => ['emerald', 'amber', 'red', 'blue'].includes(value),
  },
  /** 是否显示脉动动画 */
  pulse: {
    type: Boolean,
    default: true,
  },
  /** 尺寸 */
  size: {
    type: String,
    default: 'sm',
    validator: (value) => ['sm', 'md', 'lg'].includes(value),
  },
})

const colorClasses = {
  emerald: 'bg-emerald-500',
  amber: 'bg-amber-500',
  red: 'bg-red-500',
  blue: 'bg-blue-500',
}

const sizeClasses = {
  sm: 'w-2 h-2',
  md: 'w-3 h-3',
  lg: 'w-4 h-4',
}
</script>

<template>
  <div
    :class="[
      'rounded-full',
      colorClasses[color],
      sizeClasses[size],
      pulse && 'animate-pulse',
    ]"
  />
</template>
