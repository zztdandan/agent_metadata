import { createApp } from 'vue'
import { createPinia } from 'pinia'

import 'dedge-ai-agent-frontend/materialsymbolsoutlinedIcon.css'
import 'dedge-ai-agent-frontend/style.css'
import 'dedge-ai-agent-frontend/font-Inter.css'

import App from './App.vue'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
