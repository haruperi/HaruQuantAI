import { test, expect } from '@playwright/test';
import path from 'node:path';
test.beforeEach(async ({ page }) => {
  await page.goto('/chart');
  await expect(page.getByTestId('chart-canvas-host')).toHaveAttribute('data-loading', 'false');
});
test('styles, symbol search, local theme, indicators, settings and reload', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await expect(page.getByRole('region', { name: 'Chart', exact: true })).toBeVisible();
  for (const style of [
    'Hollow Candles',
    'Bars',
    'Line',
    'Area',
    'Baseline',
    'Heikin Ashi',
    'Candles',
  ])
    await page.getByLabel('Chart style', { exact: true }).selectOption(style);
  await page.getByRole('button', { name: 'Indicators', exact: true }).click();
  await page.getByRole('button', { name: 'SMA Simple Moving Average + Add', exact: true }).click();
  await page
    .getByRole('button', { name: 'RSI Relative Strength Index + Add', exact: true })
    .click();
  await page.getByRole('button', { name: 'Close dialog', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Remove SMA', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Remove RSI', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Remove RSI', exact: true }).click();
  await page.getByRole('button', { name: 'Chart settings', exact: true }).click();
  await page.getByLabel('Chart theme', { exact: true }).selectOption('light');
  await page.getByLabel('History minimap', { exact: true }).check();
  await page.getByRole('button', { name: 'Close dialog', exact: true }).click();
  await expect(page.locator('[data-chart-theme]')).toHaveAttribute('data-chart-theme', 'light');
  await page.screenshot({
    path: path.resolve('../../.agents/logs/2026-09-25T180609_chart-platform/chart-light.png'),
  });
  await page.getByRole('button', { name: 'XAUUSD', exact: true }).click();
  await page.getByLabel('Search symbols', { exact: true }).fill('BTCUSDT');
  await page.getByLabel('Search symbols', { exact: true }).press('Enter');
  await expect(page.getByRole('button', { name: 'BTCUSDT', exact: true })).toBeVisible();
  await expect(page.getByTestId('chart-canvas-host')).toHaveAttribute('data-loading', 'false');
  await page.getByLabel('Layout title', { exact: true }).fill('Bitcoin study');
  await expect(page.getByText('Saved locally', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByLabel('Layout title', { exact: true })).toHaveValue('Bitcoin study');
  await expect(page.locator('[data-chart-theme]')).toHaveAttribute('data-chart-theme', 'light');
  expect(errors).toEqual([]);
});

test('all intervals, long ranges, fullscreen, touch and persisted settings work', async ({
  page,
}) => {
  test.setTimeout(120000);
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  for (const interval of [
    '1m',
    '3m',
    '5m',
    '15m',
    '30m',
    '1h',
    '2h',
    '4h',
    '8h',
    '1D',
    '1W',
    '1M',
  ]) {
    await page.getByLabel('Interval', { exact: true }).selectOption(interval);
    await expect(page.getByTestId('chart-canvas-host')).toHaveAttribute('data-loading', 'false');
    await expect(page.getByTestId('chart-canvas-host')).not.toHaveAttribute('data-bar-count', '0');
  }
  for (const range of ['1D', '5D', '1M', '3M', '6M', 'YTD', '1Y', '5Y', 'All']) {
    await page.getByRole('button', { name: range, exact: true }).click();
    await expect(page.getByTestId('chart-canvas-host')).toHaveAttribute('data-loading', 'false', {
      timeout: 40000,
    });
  }
  await expect(page.getByLabel('Interval', { exact: true })).toHaveValue('1D');
  expect(
    Number(await page.getByTestId('chart-canvas-host').getAttribute('data-bar-count')),
  ).toBeGreaterThan(1200);
  await page.getByRole('button', { name: 'Fullscreen', exact: true }).click();
  await expect.poll(() => page.evaluate(() => !!document.fullscreenElement)).toBe(true);
  await page.getByRole('button', { name: 'Fullscreen', exact: true }).click();
  await expect.poll(() => page.evaluate(() => !!document.fullscreenElement)).toBe(false);
  const before = Number(
    await page.getByTestId('chart-canvas-host').getAttribute('data-visible-bars'),
  );
  const touch = await page.context().newCDPSession(page),
    box = (await page.getByTestId('chart-input').boundingBox())!;
  const points = (distance: number) => [
    { x: box.x + box.width / 2 - distance, y: box.y + 300, id: 1 },
    { x: box.x + box.width / 2 + distance, y: box.y + 300, id: 2 },
  ];
  await touch.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: points(70) });
  await touch.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: points(140) });
  await touch.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await expect
    .poll(async () =>
      Number(await page.getByTestId('chart-canvas-host').getAttribute('data-visible-bars')),
    )
    .toBeLessThan(before);
  await touch.detach();
  expect(errors).toEqual([]);
});

test('paper orders, alerts, replay and canvas/chrome PNG', async ({ page }) => {
  await page.getByRole('button', { name: /BUY$/ }).click();
  await page.getByLabel('Order quantity', { exact: true }).fill('2');
  await page.getByRole('button', { name: 'Place simulated order', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Simulated positions' })).toContainText('open');
  await page.getByRole('button', { name: 'Close position', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Simulated positions' })).toContainText('closed');
  await page.getByRole('button', { name: 'Close positions panel', exact: true }).click();
  await page.getByRole('button', { name: 'Create alert', exact: true }).click();
  await page.getByRole('button', { name: 'Create simulated alert', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Alerts', exact: true })).toContainText('XAUUSD');
  await page.getByRole('button', { name: 'Close alerts', exact: true }).click();
  await page.getByRole('button', { name: 'Replay', exact: true }).click();
  const box = (await page.getByTestId('chart-input').boundingBox())!;
  await page.mouse.click(box.x + box.width * 0.5, box.y + box.height * 0.5);
  await expect(page.getByRole('button', { name: 'Play replay', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Next replay bar', exact: true }).click();
  await page.getByRole('button', { name: 'Exit replay', exact: true }).click();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Save chart image', exact: true }).click();
  await (
    await download
  ).saveAs(path.resolve('../../.agents/logs/2026-09-25T180609_chart-platform/chart-export.png'));
  await page.screenshot({
    path: path.resolve('../../.agents/logs/2026-09-25T180609_chart-platform/chart-dark.png'),
  });
});
test('pan, zoom, price/time menus, shortcuts and narrow layout', async ({ page }) => {
  const canvas = page.getByTestId('chart-input'),
    box = (await canvas.boundingBox())!;
  await page.mouse.move(box.x + 400, box.y + 300);
  await page.mouse.wheel(0, -300);
  await canvas.click({ position: { x: 400, y: 300 } });
  await page.keyboard.press('l');
  await page.keyboard.press('a');
  await page.keyboard.press('0');
  await canvas.click({ position: { x: box.width - 25, y: 300 }, button: 'right' });
  await page.getByRole('menuitem', { name: 'Percentage scale', exact: true }).click();
  await canvas.click({ position: { x: 400, y: box.height - 10 }, button: 'right' });
  await page.getByRole('menuitem', { name: 'Reset scale', exact: true }).click();
  await page.getByRole('button', { name: 'Keyboard shortcuts', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Keyboard shortcuts' })).toContainText(
    'Ctrl/Cmd+Z',
  );
  await page.keyboard.press('Escape');
  await page.setViewportSize({ width: 760, height: 650 });
  await page.screenshot({
    path: path.resolve('../../.agents/logs/2026-09-25T180609_chart-platform/chart-narrow.png'),
  });
  await expect(page.getByRole('button', { name: 'Trend tools', exact: true })).toBeVisible();
});
