import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icones.png'],
      manifest: {
        name: 'MTG Camera Translator',
        short_name: 'MTG Translator',
        description: 'Traduza cartas, descubra preços e verifique a legalidade (Magic: The Gathering)',
        theme_color: '#1e1e2f',
        background_color: '#1e1e2f',
        display: 'standalone',
        icons: [
          {
            src: '/icones.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
