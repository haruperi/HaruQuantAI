import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => {
  const target = loadEnv(mode, '.', '').HARU_TEST_API_TARGET ?? 'http://127.0.0.1:8000';
  if (!/^http:\/\/(127\.0\.0\.1|localhost):[0-9]+$/.test(target)) throw new Error('API target must be a loopback HTTP server');
  return {
    plugins: [react(), tailwindcss()],
    server: { port: 3000, host: '127.0.0.1', proxy: { '/api': { target, changeOrigin: true } } },
    clearScreen: false,
  };
});
