/**
 * E2E: Full User Journey — complaint-copilot-ai
 *
 * What this test verifies (the only layer that can catch frontend/backend API contract mismatches):
 *   1. App loads and renders the upload interface
 *   2. User uploads sample_pharma_complaint.pdf via the file input
 *   3. SSE streaming fires and progress bar appears
 *   4. Extraction completes and the form renders real extracted values
 *   5. Batch number ATR-2024-B0421 is visible in the "Batch / Lot Number" field
 *   6. Severity badge reads "Critical"
 *   7. User types a question in the chat input and sends it
 *   8. A non-empty AI response appears in the chat message list
 *
 * Prerequisites (must be running before executing this test):
 *   cd backend && uvicorn app.main:app --reload --port 8000
 *   cd frontend && npm run dev   (proxies /api → port 8000)
 *
 * Run: npx playwright test e2e/complaint_journey.spec.js
 *
 * @jest-environment playwright
 */
import { test, expect } from '@playwright/test';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/** Path to the sample PDF used throughout the suite */
const SAMPLE_PDF = resolve(
  __dirname,
  '../../backend/sample_pharma_complaint.pdf'
);

/** After extraction, streaming may take up to 90s on a cold Groq call */
const EXTRACTION_TIMEOUT_MS = 90_000;

/** Chat responses may need up to 30s on a slow Groq call */
const CHAT_RESPONSE_TIMEOUT_MS = 30_000;

test.describe('Full user journey', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Confirm the AI Copilot upload area is visible before each test
    await expect(page.locator('.copilot-upload-section')).toBeVisible();
  });

  /**
   * Core happy-path journey:
   * upload PDF → wait for SSE streaming → assert batch + severity → chat Q&A
   */
  test('upload PDF, extract fields, assert batch + severity, send chat message', async ({ page }) => {
    // ── Step 1: Attach the PDF via the hidden file input ─────────────────────
    // The dropzone click triggers #file-input; we set files directly on it
    const fileInput = page.locator('#file-input');
    await fileInput.setInputFiles(SAMPLE_PDF);

    // The "Selected:" label should appear after file selection
    await expect(page.locator('.file-selected')).toBeVisible({ timeout: 5_000 });
    await expect(page.locator('.file-selected')).toContainText('sample_pharma_complaint.pdf');

    // ── Step 2: Click Extract ────────────────────────────────────────────────
    const extractBtn = page.locator('.btn-extract');
    await expect(extractBtn).toBeEnabled();
    await extractBtn.click();

    // ── Step 3: SSE progress bar should appear ───────────────────────────────
    // The progress bar renders while isExtracting = true
    await expect(page.locator('.progress-container')).toBeVisible({ timeout: 10_000 });

    // ── Step 4: Wait for extraction to complete ──────────────────────────────
    // When done, the AI summary bubble appears and the progress bar disappears.
    // We wait on the summary bubble as the signal extraction is fully complete.
    await expect(page.locator('.chat-bubble')).toBeVisible({
      timeout: EXTRACTION_TIMEOUT_MS,
    });

    // Progress bar should be gone once SSE stream finishes
    await expect(page.locator('.progress-container')).not.toBeVisible({ timeout: 5_000 });

    // ── Step 5: Assert batch number is visible in the form ───────────────────
    // The "Batch / Lot Number" SkeletonField renders value in a .field-value div
    // that follows the label "Batch / Lot Number"
    const batchField = page.locator('.field-row', {
      has: page.locator('.field-label', { hasText: 'Batch / Lot Number' }),
    });
    await expect(batchField).toBeVisible();
    await expect(batchField.locator('.field-value')).toContainText('ATR-2024-B0421', {
      timeout: 5_000,
    });

    // ── Step 6: Assert severity badge reads "Critical" ───────────────────────
    // SeverityBadge renders a <span> inside the "Initial Severity" field-row
    const severityField = page.locator('.field-row', {
      has: page.locator('.field-label', { hasText: 'Initial Severity' }),
    });
    await expect(severityField.locator('span')).toContainText('Critical', {
      timeout: 5_000,
    });

    // ── Step 7: Type a question in the chat input and send it ────────────────
    const chatInput = page.locator('input[placeholder*="Ask a question"]');
    await expect(chatInput).toBeEnabled({ timeout: 5_000 });
    await chatInput.fill('What is the batch number for this complaint?');
    await chatInput.press('Enter');

    // ── Step 8: A non-empty AI response appears in the chat message list ─────
    // ChatMessageList renders user messages with className "msg-user"
    // and AI responses with className "msg-ai".
    // Wait for at least one AI message to appear after our question.
    const aiMessage = page.locator('.msg-ai').last();
    await expect(aiMessage).toBeVisible({ timeout: CHAT_RESPONSE_TIMEOUT_MS });

    // The AI message should be non-trivially long (not empty / loading placeholder)
    const aiText = await aiMessage.textContent();
    expect(aiText?.trim().length).toBeGreaterThan(20);

    // Optional: the batch number should appear in the AI response since that's
    // exactly what was asked — this would catch a context-injection failure
    expect(aiText).toContain('ATR-2024-B0421');
  });

  /**
   * Smoke test: App loads without JS errors and renders critical UI structure.
   * This is a lightweight version that runs even when Groq is unavailable.
   */
  test('app loads and renders upload interface correctly', async ({ page }) => {
    // Three main panels should be present
    await expect(page.locator('.copilot-panel')).toBeVisible();
    await expect(page.locator('.copilot-upload-section')).toBeVisible();

    // Upload file input exists
    await expect(page.locator('#file-input')).toBeAttached();

    // Text paste area exists
    await expect(
      page.locator('textarea[placeholder*="Paste customer email"]')
    ).toBeVisible();

    // Extract button is present and initially disabled (no file or text selected)
    const extractBtn = page.locator('.btn-extract');
    await expect(extractBtn).toBeVisible();
    await expect(extractBtn).toBeDisabled();

    // The idle hint "Ready for document intake" should be shown
    await expect(page.locator('.idle-hint')).toBeVisible();

    // No unexpected console errors on load
    const errors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    // Give the page a moment to settle
    await page.waitForTimeout(1_000);
    // Filter out known non-critical Vite/React warnings
    const criticalErrors = errors.filter(
      (e) => !e.includes('Warning:') && !e.includes('[vite]')
    );
    expect(criticalErrors).toHaveLength(0);
  });

  /**
   * Regression: uploading an unsupported file type (e.g. .jpg) 
   * must show a user-visible error, not crash the app.
   */
  test('uploading unsupported file type shows error and does not crash', async ({ page }) => {
    // Create a fake JPG file buffer in the browser context
    const fakeJpg = {
      name: 'test_image.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10]), // JFIF magic bytes
    };

    const fileInput = page.locator('#file-input');
    await fileInput.setInputFiles(fakeJpg);

    // File gets selected (the dropzone shows it)
    await expect(page.locator('.file-selected')).toBeVisible({ timeout: 3_000 });

    // Click Extract
    await page.locator('.btn-extract').click();

    // An error message must appear — the backend returns 422 for unsupported types
    await expect(page.locator('.error-msg')).toBeVisible({ timeout: 15_000 });

    // The app should still be responsive — the extract button should re-enable
    await expect(page.locator('.btn-extract')).toBeEnabled({ timeout: 5_000 });
  });
});
