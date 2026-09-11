import { defineConfig } from '@playwright/test';
import { existsSync } from 'node:fs';

const python = process.env.PYTHON ?? (existsSync('.venv/bin/python') ? '.venv/bin/python' : 'python3');
export default defineConfig({
  testDir: 'tests/frontend',
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:8010',
    reducedMotion: 'reduce',
    trace: 'retain-on-failure',
    ...(process.env.PLAYWRIGHT_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHANNEL } : {}),
  },
  webServer: {
    command: `${python} -m uvicorn app.app:app --host 127.0.0.1 --port 8010`,
    url: 'http://127.0.0.1:8010',
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
  },
});
