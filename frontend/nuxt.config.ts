// https://nuxt.com/docs/api/configuration/nuxt-config
const apiBase = process.env.NUXT_PUBLIC_API_BASE || ''
const apiProxyTarget = apiBase.endsWith('/api') ? apiBase : `${apiBase.replace(/\/$/, '')}/api`
const devApiTarget = apiBase ? apiProxyTarget : 'http://localhost:8765/api'

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  // Modules
  modules: ['@pinia/nuxt'],

  // TypeScript
  typescript: {
    strict: true,
  },

  // Runtime config (env variables)
  runtimeConfig: {
    // Server-only
    dashscopeApiKey: '',
    // Public (exposed to client)
    public: {
      apiBase,
      appName: '儿童思维树',
    },
  },

  // Dev server
  devServer: {
    port: 3000,
  },

  // App config
  app: {
    head: {
      title: '儿童思维树 - Thinking Tree',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Interactive thinking tree for children' },
      ],
      htmlAttrs: {
        lang: 'zh-CN',
      },
    },
  },

  // Server-side CORS for development
  nitro: {
    devProxy: {
      '/api': {
        target: devApiTarget,
        changeOrigin: true,
      },
    },
    routeRules: {
      '/api/**': {
        cors: true,
      },
    },
  },
})
