import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production';
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src"),
      },
    },
    server: {
      // Development proxy - automatically routes /api calls to backend
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, '/api'),
        },
        '/health': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
        },
        '/docs': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
        }
      },
      port: 3000,
      host: true,
    },
    build: {
      // Production build configuration
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
          },
        },
      },
      // Ensure proper module resolution
      commonjsOptions: {
        include: [/node_modules/],
      },
    },
    define: {
      // Build-time configuration - no .env needed
      __API_BASE__: JSON.stringify(
        isProduction 
          ? '' // Empty string means same domain in production
          : 'http://127.0.0.1:8000' // Development backend URL
      ),
      __IS_PRODUCTION__: JSON.stringify(isProduction),
      __APP_VERSION__: JSON.stringify('2.0.0'),
    },
  }
})
