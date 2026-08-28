import { ref, computed } from 'vue'

/**
 * 侧边栏按钮配置和交互逻辑
 * @returns {Object} 按钮配置和状态管理
 */
export function useSidebarButtons() {
  // 当前激活的按钮ID
  const activeButtonId = ref('agent')

  // 顶部按钮配置
  const topButtons = computed(() => [
    {
      id: 'agent',
      icon: 'smart_toy',
      tooltip: 'Agent',
      active: activeButtonId.value === 'agent',
      filled: true,
      handler: () => {
        setActiveButton('agent')
        console.log('Agent button clicked')
      },
    },
    {
      id: 'history',
      icon: 'history',
      tooltip: 'History',
      active: activeButtonId.value === 'history',
      handler: () => {
        setActiveButton('history')
        console.log('History button clicked')
      },
    },
    {
      id: 'chat_bubble',
      icon: 'chat_bubble',
      tooltip: 'Notifications',
      active: activeButtonId.value === 'chat_bubble',
      handler: () => {
        setActiveButton('chat_bubble')
        console.log('Notifications button clicked')
      },
    },
  ])

  // 底部按钮配置
  const bottomButtons = computed(() => [
    {
      id: 'help',
      icon: 'help',
      tooltip: 'Help',
      active: activeButtonId.value === 'help',
      handler: () => {
        setActiveButton('help')
        console.log('Help button clicked')
      },
    },
  ])

  // 设置激活按钮
  const setActiveButton = (id) => {
    activeButtonId.value = id
  }

  return {
    topButtons,
    bottomButtons,
    activeButtonId,
    setActiveButton,
  }
}
