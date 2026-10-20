import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  use: { actionTimeout: 10000, baseURL: 'http://127.0.0.1:4173', viewport: { width: 1440, height: 900 }, channel: 'chrome' },
  webServer: { env: { HARU_TEST_API_TARGET: 'http://127.0.0.1:4180' }, command: 'npm run dev -- --config vite.config.ts --host 127.0.0.1 --port 4173', url: 'http://127.0.0.1:4173', reuseExistingServer: false, timeout: 120000 },
});
