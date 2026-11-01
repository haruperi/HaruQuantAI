import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  const connection = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await page.addLocatorHandler(connection, async () => {
    await connection.getByRole('button', { name: 'Close', exact: true }).click();
  });
});

test('chart settings has the seven TradingView-style sections and disables unsupported feed options', async ({ page }) => {
  await page.goto('/chart');
  await page.getByRole('button', { name: 'Chart settings' }).click();
  const modal = page.getByRole('dialog', { name: 'Chart settings' });
  const nav = modal.getByRole('navigation', { name: 'Chart settings sections' });
  await expect(nav.getByRole('button')).toHaveText([
    'Symbol', 'Status line', 'Scales and lines', 'Canvas', 'Trading', 'Alerts', 'Events',
  ]);
  await expect(modal.getByRole('region', { name: 'Symbol settings' })).toBeVisible();
  await expect(modal.getByLabel('Body up color')).toHaveValue('#089981');
  await expect(modal.getByLabel('Borders down color')).toHaveValue('#f23645');
  await expect(modal.getByLabel('Adjust data for dividends')).toBeDisabled();
  await nav.getByRole('button', { name: 'Events' }).click();
  await expect(modal.getByLabel('Earnings')).toBeDisabled();
  await expect(modal.getByLabel('Dividends')).toBeDisabled();
  await expect(modal.getByLabel('Splits')).toBeDisabled();
  await modal.getByRole('button', { name: 'Cancel' }).click();
  await expect(modal).toHaveCount(0);
});

test('settings are transactional and persist after applying; cancel keeps prior chart appearance', async ({ page }) => {
  await page.goto('/chart');
  const open = () => page.getByRole('button', { name: 'Chart settings' }).click();
  const dialog = page.getByRole('dialog', { name: 'Chart settings' });
  const nav = dialog.getByRole('navigation', { name: 'Chart settings sections' });
  await open();
  await nav.getByRole('button', { name: 'Trading' }).click();
  await dialog.getByLabel('Buy and Sell buttons').uncheck();
  await dialog.getByRole('button', { name: 'Cancel' }).click();
  await expect(page.getByRole('button', { name: /SELL/i }).first()).toBeVisible();

  await open();
  await dialog.getByLabel('Body up color').fill('#11aa88');
  await nav.getByRole('button', { name: 'Trading' }).click();
  await dialog.getByLabel('Buy and Sell buttons').uncheck();
  await nav.getByRole('button', { name: 'Canvas' }).click();
  await dialog.getByLabel('Grid lines', { exact: true }).uncheck();
  await dialog.getByRole('button', { name: 'Ok', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await expect(page.locator('.cq-quotes')).toHaveCount(0);
  await expect.poll(async () => page.evaluate(() => {
    const value = localStorage.getItem('haruquantai.chart.v1');
    if (!value) return null;
    const chart = JSON.parse(value).state.chart;
    return [chart.candleUpColor, chart.showBuySellButtons, chart.showGrid];
  })).toEqual(['#11aa88', false, false]);

  await page.reload();
  await open();
  await expect(dialog.getByLabel('Body up color')).toHaveValue('#11aa88');
  await nav.getByRole('button', { name: 'Trading' }).click();
  await expect(dialog.getByLabel('Buy and Sell buttons')).not.toBeChecked();
  await nav.getByRole('button', { name: 'Canvas' }).click();
  await expect(dialog.getByLabel('Grid lines', { exact: true })).not.toBeChecked();
});

test('templates apply only on Ok and can be saved and restored', async ({ page }) => {
  await page.goto('/chart');
  await page.getByRole('button', { name: 'Chart settings' }).click();
  const modal = page.getByRole('dialog', { name: 'Chart settings' });
  const nav = modal.getByRole('navigation', { name: 'Chart settings sections' });
  await nav.getByRole('button', { name: 'Canvas' }).click();
  await modal.getByLabel('Chart theme').selectOption('light');

  page.once('dialog', (dialog) => dialog.accept('My light settings'));
  await modal.locator('summary').filter({ hasText: 'Template' }).click();
  await modal.getByRole('button', { name: 'Save as template…' }).click();
  await expect.poll(async () => page.evaluate(() =>
    Object.keys(JSON.parse(localStorage.getItem('haruquantai.chart.settings.templates.v1') || '{}')),
  )).toContain('My light settings');
  // Saving a template must not commit the current draft to the chart.
  await modal.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('button', { name: 'Chart settings' }).click();
  await nav.getByRole('button', { name: 'Canvas' }).click();
  await expect(modal.getByLabel('Chart theme')).toHaveValue('dark');
  await modal.locator('summary').filter({ hasText: 'Template' }).click();
  await modal.getByRole('button', { name: 'My light settings' }).click();
  await expect(modal.getByLabel('Chart theme')).toHaveValue('light');
  await modal.getByRole('button', { name: 'Ok', exact: true }).click();
  await expect.poll(async () => page.evaluate(() =>
    JSON.parse(localStorage.getItem('haruquantai.chart.v1') || '{}')?.state?.chart?.theme,
  )).toBe('light');
});
