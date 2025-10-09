import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  server: {
    port: 3007,
    proxy: {
      '/api/auth': {
        target: 'https://auth.jkusa.org',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/api\/auth/, ''),
      },
    },
  },
  css: {
    postcss: {
      plugins: [tailwindcss, autoprefixer],
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false, // Disable sourcemaps in production for smaller builds
    minify: 'esbuild', // Use esbuild for faster minification
  },
})