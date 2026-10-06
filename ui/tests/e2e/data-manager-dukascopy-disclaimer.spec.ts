import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.route('**/*', (route) =>
    ['127.0.0.1', 'localhost'].includes(new URL(route.request().url()).hostname)
      ? route.continue()
      : route.abort(),
  );
  await page.route('**/api/v1/**', (route) => route.abort());
  await page.goto('/datamanager');
});

test('standalone disclaimer keeps content, Escape and launcher focus across themes', async ({
  page,
}) => {
  const launcher = page.getByRole('button', { name: 'Dukascopy data', exact: true });
  for (const theme of ['dark', 'light']) {
    if (theme === 'light')
      await page.evaluate(async () => {
        const modulePath = '/app/host/store.ts';
        const { useAppStore } = await import(modulePath);
        useAppStore.getState().updateSettings({ theme: 'light' });
      });
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
    await launcher.click();
    await page.getByRole('menuitem', { name: 'Dukascopy Data Disclaimer', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: 'Dukascopy data disclaimer', exact: true });
    await expect(dialog).toContainText('AS IS');
    await expect(dialog.getByRole('button', { name: 'Close', exact: true }).first()).toBeFocused();
    await page.screenshot({ path: `test-results/dukascopy-disclaimer-${theme}.png` });
    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
    await expect(launcher).toBeFocused();
  }
});

test('instrument mapping Back preserves add draft and selection', async ({ page }) => {
  await page.evaluate(() =>
    localStorage.setItem(
      'sqx-data-manager-v1',
      JSON.stringify({
        version: 1,
        definitions: [],
        brokers: [
          {
            id: 'pilot',
            name: 'Pilot broker',
            postfix: '_P',
            timezone: 'UTC',
            mtUse: true,
            instruments: [],
          },
        ],
      }),
    ),
  );
  await page.reload();
  await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Add new Dukascopy symbol', exact: true }).click();
  const add = page.getByRole('dialog', { name: 'Add Dukascopy data', exact: true });
  await add.getByLabel('Filter available symbols').fill('AUDUSD');
  await add.getByRole('checkbox', { name: 'Select symbol AUDUSD', exact: true }).check();
  await add.getByLabel('Broker profile *', { exact: true }).selectOption('pilot');
  await add.getByRole('switch').check();
  await add.getByRole('button', { name: 'Save', exact: true }).click();
  const mapping = page.getByRole('dialog', {
    name: 'Add Dukascopy data - identify instruments',
    exact: true,
  });
  await expect(mapping.getByLabel('Instrument for AUDUSD')).toBeVisible();
  await page.screenshot({ path: 'test-results/dukascopy-mapping-pilot.png' });
  await mapping.getByRole('button', { name: '< Back', exact: true }).click();
  await expect(add.getByLabel('Filter available symbols')).toHaveValue('AUDUSD');
  await expect(
    add.getByRole('checkbox', { name: 'Select symbol AUDUSD', exact: true }),
  ).toBeChecked();
  await expect(add.getByLabel('Data postfix')).toHaveValue('_P');
  await add.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(mapping.getByLabel('Instrument for AUDUSD')).toBeVisible();
});
