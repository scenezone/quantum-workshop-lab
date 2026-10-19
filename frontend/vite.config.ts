import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: { '/api': { target: env.API_PROXY_TARGET || 'http://127.0.0.1:8000', changeOrigin: true } },
    },
    preview: {
      proxy: { '/api': { target: env.API_PROXY_TARGET || 'http://127.0.0.1:8000', changeOrigin: true } },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (/node_modules[/\\](react|react-dom|scheduler)[/\\]/.test(id)) return 'react';
            if (/node_modules[/\\](lodash|lodash-es)[/\\]/.test(id)) return 'utilities';
            if (/node_modules[/\\](recharts|d3-|victory-vendor)/.test(id)) return 'charts';
            if (/node_modules[/\\](katex|remark-|rehype-|micromark|mdast|hast)/.test(id)) return 'markdown';
          },
        },
      },
    },
  };
});
