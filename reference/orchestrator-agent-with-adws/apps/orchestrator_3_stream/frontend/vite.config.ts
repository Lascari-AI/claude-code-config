import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  // Load env file from parent directory (orchestrator_3_stream/)
  const env = loadEnv(mode, '../', '')

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      host: env.FRONTEND_HOST || '127.0.0.1',
      port: parseInt(env.FRONTEND_PORT || '5175'),
      middlewareMode: false
    },
    publicDir: 'public'
  }
})
