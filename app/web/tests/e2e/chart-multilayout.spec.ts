import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  const connection = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await page.addLocatorHandler(connection, async () => {
    await connection.getByRole('button', { name: 'Close', exact: true }).click();
  });
});

test('switches between single, split, grid, and eight-chart presets and saves layout', async ({ page }) => {
  test.setTimeout(120000);
  await page.goto('/chart');
  const panes = page.getByTestId('chart-pane');
  const picker = page.getByRole('button', { name: 'Select layout', exact: true });
  await expect(panes).toHaveCount(1);

  const changeLayout = async (label: string) => {
    await picker.click();
    const dialog = page.getByRole('dialog', { name: 'Select layout', exact: true });
    await dialog.getByRole('button', { name: label, exact: true }).click();
    await expect(dialog).toBeHidden();
  };

  await changeLayout('2 charts · 2h');
  await expect(panes).toHaveCount(2);
  await expect(page.locator('.cq-chart-board')).toHaveAttribute('data-layout', '2h');
  await changeLayout('4 charts · 4');
  await expect(panes).toHaveCount(4);
  await changeLayout('8 charts · 8');
  await expect(panes).toHaveCount(8);
  await expect.poll(() => page.evaluate(() =>
    JSON.parse(localStorage.getItem('haruquantai.chart.layout.v1') || '{}').id
  )).toBe('8');
  await page.reload();
  await expect(panes).toHaveCount(8);
  await changeLayout('Single chart');
  await expect(panes).toHaveCount(1);
});

test('toolbar edits active pane only until interval sync is enabled, then persists independently', async ({ page }) => {
  test.setTimeout(120000);
  await page.goto('/chart');
  const picker = page.getByRole('button', { name: 'Select layout', exact: true });
  await picker.click();
  await page.getByRole('dialog', { name: 'Select layout', exact: true })
    .getByRole('button', { name: '2 charts · 2h' }).click();
  const panes = page.getByTestId('chart-pane');
  await expect(panes).toHaveCount(2);
  await expect(panes.nth(0).getByTestId('chart-canvas-host')).toHaveAttribute('data-loading', 'false');
  await expect(panes.nth(1).getByTestId('chart-canvas-host')).toHaveAttribute('data-loading', 'false');

  await panes.nth(1).getByTestId('chart-input').click({ position: { x: 30, y: 65 } });
  await expect(panes.nth(1)).toHaveClass(/cq-chart-cell-active/);
  await page.getByRole('combobox', { name: 'Interval', exact: true }).selectOption('1h');
  await expect.poll(() => page.evaluate(() => {
    const state = JSON.parse(localStorage.getItem('haruquantai.chart.v1.pane.1') || '{}').state;
    return state?.chart?.interval;
  })).toBe('1h');
  await panes.nth(0).getByTestId('chart-input').click({ position: { x: 30, y: 65 } });
  await expect(page.getByRole('combobox', { name: 'Interval', exact: true })).toHaveValue('3m');
  await panes.nth(1).getByTestId('chart-input').click({ position: { x: 30, y: 65 } });
  await expect(page.getByRole('combobox', { name: 'Interval', exact: true })).toHaveValue('1h');

  await picker.click();
  const menu = page.getByRole('dialog', { name: 'Select layout', exact: true });
  await menu.getByRole('switch', { name: 'Sync Interval' }).click();
  await expect(menu.getByRole('switch', { name: 'Sync Interval' })).toHaveAttribute('aria-checked', 'true');
  await picker.click();
  await expect.poll(() => page.evaluate(() => {
    const state = JSON.parse(localStorage.getItem('haruquantai.chart.v1') || '{}').state;
    return state?.chart?.interval;
  })).toBe('1h');

  await page.getByRole('combobox', { name: 'Interval', exact: true }).selectOption('15m');
  await expect.poll(() => page.evaluate(() => {
    const first = JSON.parse(localStorage.getItem('haruquantai.chart.v1') || '{}').state;
    const second = JSON.parse(localStorage.getItem('haruquantai.chart.v1.pane.1') || '{}').state;
    return [first?.chart?.interval, second?.chart?.interval];
  })).toEqual(['15m', '15m']);

  await page.reload();
  await expect(panes).toHaveCount(2);
  await expect(panes.nth(1)).toHaveClass(/cq-chart-cell-active/);
  await expect(page.getByRole('combobox', { name: 'Interval', exact: true })).toHaveValue('15m');
  await picker.click();
  await expect(page.getByRole('switch', { name: 'Sync Interval' })).toHaveAttribute('aria-checked', 'true');
});

test('sync options can be changed without collapsing the chart menu', async ({ page }) => {
  await page.goto('/chart');
  await page.getByRole('button', { name: 'Select layout', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Select layout', exact: true });
  await expect(dialog.getByRole('switch')).toHaveCount(5);
  for (const [name, value] of [
    ['Symbol', 'true'], ['Interval', 'true'], ['Crosshair', 'false'],
    ['Time', 'true'], ['Date range', 'true'],
  ]) {
    await dialog.getByRole('switch', { name: 'Sync ' + name }).click();
    await expect(dialog.getByRole('switch', { name: 'Sync ' + name })).toHaveAttribute('aria-checked', value);
  }
  await expect(dialog).toBeVisible();
});

test('chart splitters resize the grid and double-click restores equal tracks', async ({ page }) => {
  await page.goto('/chart');
  await page.getByRole('button', { name: 'Select layout', exact: true }).click();
  await page.getByRole('dialog', { name: 'Select layout' })
    .getByRole('button', { name: '2 charts · 2h' }).click();
  const handle = page.getByRole('separator', { name: 'Resize charts columns:1:0' });
  await expect(handle).toBeVisible();
  const bounds = (await handle.boundingBox())!;
  const from = { x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height / 2 };
  await page.mouse.move(from.x, from.y);
  await page.mouse.down();
  await page.mouse.move(from.x + 75, from.y, { steps: 8 });
  await page.mouse.up();
  await expect.poll(async () => page.evaluate(() => {
    const saved = JSON.parse(localStorage.getItem('haruquantai.chart.layout.v1') || '{}');
    return saved.sizes?.['2h']?.columns?.[0] ?? 0;
  })).toBeGreaterThan(50);
  await handle.dblclick();
  await expect.poll(async () => page.evaluate(() => {
    const saved = JSON.parse(localStorage.getItem('haruquantai.chart.layout.v1') || '{}');
    return saved.sizes?.['2h'];
  })).toBeUndefined();
});

test('crosshair and time window synchronization propagate to other chart canvases', async ({ page }) => {
  test.setTimeout(120000);
  await page.goto('/chart');
  const picker = page.getByRole('button', { name: 'Select layout', exact: true });
  await picker.click();
  await page.getByRole('dialog', { name: 'Select layout' })
    .getByRole('button', { name: '2 charts · 2h' }).click();
  const panes = page.getByTestId('chart-pane');
  await expect(panes.nth(0).getByTestId('chart-canvas-host')).toHaveAttribute('data-loading', 'false');
  const secondHost = panes.nth(1).getByTestId('chart-canvas-host');
  await expect(secondHost).toHaveAttribute('data-loading', 'false');

  const input = panes.nth(0).getByTestId('chart-input');
  const bounds = (await input.boundingBox())!;
  await page.mouse.move(bounds.x + Math.min(140, bounds.width - 80), bounds.y + 90);
  await expect.poll(() => secondHost.getAttribute('data-linked-crosshair-time')).toMatch(/^\d+$/);
  await picker.click();
  const menu = page.getByRole('dialog', { name: 'Select layout' });
  await menu.getByRole('switch', { name: 'Sync Crosshair' }).click();
  await expect(secondHost).toHaveAttribute('data-linked-crosshair-time', '');
  await menu.getByRole('switch', { name: 'Sync Time', exact: true }).click();
  await picker.click();
  await expect.poll(() => secondHost.getAttribute('data-synced-time-window')).not.toBeNull();
  const before = await secondHost.getAttribute('data-synced-time-window');
  await input.hover({ position: { x: Math.min(160, bounds.width - 90), y: 105 } });
  await page.mouse.wheel(0, -260);
  await expect.poll(() => secondHost.getAttribute('data-synced-time-window')).not.toBe(before);
});
