// @ts-check
import { defineConfig, devices } from '@playwright/test';


/**
 * Playwright configuration for complaint-copilot-ai E2E tests.
 * Tests require BOTH the backend (port 8000) AND frontend (port 3000) to be running.
 *
 * Start them before running tests:
 *   cd backend && uvicorn app.main:app --reload &
 *   cd frontend && npm run dev &
 *
 * Then run: npx playwright test
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 120_000,           // individual test timeout — 2 min (SSE can be slow on first Groq call)
  expect: { timeout: 30_000 }, // assertion timeout — 30s to allow SSE streaming to settle
  fullyParallel: false,        // E2E tests share live backend state; run serially
  retries: 1,                  // one automatic retry on flake
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
