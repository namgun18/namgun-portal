export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',

  app: {
    head: {
      htmlAttrs: { lang: 'ko' },
      title: 'namgun.or.kr Portal',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      ],
    },
  },

  modules: [
    '@nuxtjs/tailwindcss',
    '@nuxtjs/color-mode',
  ],

  colorMode: {
    classSuffix: '',
  },

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    public: {
      demoMode: process.env.NUXT_PUBLIC_DEMO_MODE === 'true',
    },
  },

  // SSR: 데모 모드는 SPA (하이드레이션 미스매치 방지, SEO 불필요)
  ssr: process.env.NUXT_PUBLIC_DEMO_MODE !== 'true',

  // /api/**, /oauth/** → FastAPI 백엔드 프록시
  nitro: {
    devProxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/oauth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  routeRules: process.env.NUXT_PUBLIC_DEMO_MODE === 'true' ? {} : {
    '/api/**': { proxy: 'http://backend:8000/api/**' },
  },
})
