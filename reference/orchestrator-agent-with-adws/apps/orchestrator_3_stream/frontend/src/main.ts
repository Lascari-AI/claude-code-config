import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './styles/global.css'
// Syntax highlighting theme for code blocks
import 'highlight.js/styles/github-dark.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.mount('#app')
