// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Complaint Copilot AI — E2E Journey', () => {
  test('Full user journey: load app -> extract complaint text -> verify extracted fields -> ask chat question', async ({ page }) => {
    // 1. Load application
    await page.goto('http://localhost:3000');
    await expect(page).toHaveTitle(/Complaint Copilot/i);

    // 2. Locate paste textarea and paste complaint text
    const sampleText = `
Complaint Source: Retail Pharmacy — MedStore Plus
Customer Name: MedStore Plus, Bengaluru
Product Name: Atorvastatin 40mg Tablets
Product Strength: 40mg
Batch/Lot Number: ATR-2024-E2E
Manufacturing Date: 2024-01-15
Expiry Date: 2026-01-14
Quantity Affected: 48 blister packs
Complaint Type: Packaging Defect
Complaint Date: 2024-06-15
Detailed Description: Customer reported multiple blister packs with broken seal integrity. No hospitalization occurred. Symptoms were mild and resolved after discontinuing product use.
    `.trim();

    const textarea = page.locator('textarea.paste-textarea');
    await expect(textarea).toBeVisible();
    await textarea.fill(sampleText);

    // 3. Click Extract button
    const extractBtn = page.locator('button.btn-extract');
    await expect(extractBtn).toBeEnabled();
    await extractBtn.click();

    // 4. Wait for extraction stream to finish (extract button turns back to idle or progress disappears/completes)
    // Wait up to 30s for LLM pipeline to stream through SSE
    await page.waitForSelector('.field-value:not(.empty)', { timeout: 35000 });

    // 5. Verify key extracted fields rendered in UI
    const productNameField = page.locator('.field-value', { hasText: 'Atorvastatin' });
    await expect(productNameField).toBeVisible({ timeout: 10000 });

    // 6. Verify Severity Badge
    const severityBadge = page.locator('.severity-badge, .risk-score-pill, .summary-text');
    await expect(severityBadge.first()).toBeVisible({ timeout: 10000 });

    // 7. Verify Executive Summary or CAPA is displayed
    const aiCopilotSection = page.locator('.copilot-panel, .risk-panel, .summary-section');
    await expect(aiCopilotSection.first()).toBeVisible();

    // 8. Interact with Grounded Chat
    const chatInput = page.locator('input[placeholder*="Ask a question"], input[placeholder*="chat"]');
    if (await chatInput.isVisible()) {
      await chatInput.fill('What is the batch number of this product?');
      const sendBtn = page.locator('button', { hasText: /Send/i });
      await sendBtn.click();

      // Assert AI response appears in chat
      const chatResponse = page.locator('.chat-message.assistant, .message.assistant, .chat-bubble');
      await expect(chatResponse.first()).toBeVisible({ timeout: 15000 });
      const text = await chatResponse.first().innerText();
      expect(text.length).toBeGreaterThan(5);
    }
  });
});
