import { expect, test, type Page } from '@playwright/test';

const legacyBranding = /StrategyQuant|\bSQX\b|\bSQ (?:Equity|Futures|default|DataManager|Data Manager|CDN|Data)\b/;

async function expectCurrentBranding(page: Page): Promise<void> {
  await expect(page.locator('body')).toContainText('HaruQuantAI');
  expect(await page.locator('body').innerText()).not.toMatch(legacyBranding);
}

test.beforeEach(async ({ page }) => { await page.goto('/'); });

test('shell, primary modules and settings dialogs expose HaruQuantAI branding', async ({ page }) => {
  await expect(page).toHaveTitle('HaruQuantAI — Frontend Research Workspace');
  await expect(page.getByRole('button', { name: 'HaruQuantAI', exact: true })).toHaveText('HaruQuantAI');
  await expect(page.getByRole('complementary', { name: 'Applications' })).not.toContainText('Research platform');
  await expect(page.locator('.topbar > .nav-toggle')).toHaveCount(0);
  await expect(page.getByText('Applications', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Improver', exact: true })).toHaveCount(0);
  await expectCurrentBranding(page);

  for (const moduleName of ['Data Manager', 'Business', 'Code Editor']) {
    await page.getByRole('button', { name: moduleName, exact: true }).click();
    await expectCurrentBranding(page);
  }

  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  expect(await page.getByRole('menu', { name: 'Application settings' }).innerText()).not.toMatch(legacyBranding);
  await page.getByRole('menuitem', { name: 'About', exact: true }).click();
  await expectCurrentBranding(page);
});

test('legacy browser data is normalized before it is shown', async ({ page }) => {
  await page.evaluate(() => localStorage.setItem('sqx-data-manager-v1', JSON.stringify({
    version: 2,
    definitions: [{ id: 'legacy:1', source: 'SQ Futures', symbol: 'LEGACY', underlying: 'LEGACY', instrument: 'LEGACY', timeframe: 'M1', broker: '-1', brokerName: 'SQ default', timezone: 'UTC', category: 'Futures', from: '', to: '', bars: 0 }],
    brokers: [],
    brokerJob: null,
  })));
  await page.reload();
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await expect(page.getByRole('cell', { name: 'Futures', exact: true }).first()).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Default', exact: true })).toBeVisible();
  await expectCurrentBranding(page);
});
