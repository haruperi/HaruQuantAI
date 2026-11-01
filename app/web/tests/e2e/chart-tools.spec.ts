import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  const connection = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await page.addLocatorHandler(connection, async () => {
    await connection.getByRole('button', { name: 'Close', exact: true }).click();
  });
});
test('every drawing tool creates an editable persisted object with undo and redo', async ({
  page,
}) => {
  test.setTimeout(180000);
  await page.goto('/chart');
  const host = page.getByTestId('chart-canvas-host');
  await expect(host).toHaveAttribute('data-loading', 'false');
  const groups: { group: string; names: [string, number][] }[] = [
    { group: 'Measure', names: [['Measure', 2]] },
    {
      group: 'Trend',
      names: [
        ['Trend line', 2],
        ['Ray', 2],
        ['Segment', 2],
        ['Horizontal line', 1],
        ['Vertical line', 1],
        ['Horizontal ray', 1],
        ['Price line', 1],
        ['Arrow', 2],
        ['Info line', 2],
        ['Extended line', 2],
        ['Trend angle', 2],
        ['Crossline', 1],
        ['Parallel channel', 3],
        ['Regression trend', 2],
        ['Flat top/bottom', 3],
        ['Disjoint channel', 3],
        ['Pitchfork', 3],
        ['Schiff pitchfork', 3],
        ['Modified Schiff pitchfork', 3],
        ['Inside pitchfork', 3],
      ],
    },
    {
      group: 'Fibonacci',
      names: [
        ['Fib retracement', 2],
        ['Trend-based fib extension', 3],
        ['Fib time zone', 2],
        ['Gann fan', 2],
        ['Fib channel', 3],
        ['Fib speed resistance fan', 2],
        ['Trend-based fib time', 3],
        ['Fib circles', 2],
        ['Fib spiral', 2],
        ['Fib speed resistance arcs', 2],
        ['Fib wedge', 3],
        ['Pitchfan', 3],
        ['Gann box', 2],
        ['Gann square fixed', 2],
        ['Gann square', 2],
      ],
    },
    {
      group: 'Shapes',
      names: [
        ['Rectangle', 2],
        ['Ellipse', 2],
        ['Triangle', 3],
        ['Polygon', 0],
        ['Circle', 2],
      ],
    },
    {
      group: 'Annotate',
      names: [
        ['Text', 1],
        ['Anchored note', 1],
        ['Emoji / sticker', 1],
        ['Brush', -1],
      ],
    },
  ];
  let count = 0;
  const box = (await page.getByTestId('chart-input').boundingBox())!;
  for (const group of groups)
    for (const [name, anchors] of group.names) {
      if (group.group === 'Measure')
        await page.getByRole('button', { name: 'Measure', exact: true }).click();
      else {
        await page.getByRole('button', { name: group.group + ' tools', exact: true }).click();
        await page
          .getByRole('menuitem')
          .filter({ has: page.getByText(name, { exact: true }) })
          .click();
      }
      const x = box.x + 340 + (count % 4) * 30,
        y = box.y + 230 + (count % 3) * 35;
      if (anchors === 2 || anchors === -1) {
        await page.mouse.move(x, y);
        await page.mouse.down();
        await page.mouse.move(x + 130, y + 70, { steps: 5 });
        await page.mouse.up();
      } else {
        await page.mouse.click(x, y);
        if (anchors === 3 || anchors === 0) {
          await page.mouse.click(x + 110, y + 75);
          await page.mouse.click(x + 160, y - 25);
        }
        if (anchors === 0) await page.keyboard.press('Enter');
      }
      count++;
      await expect(host).toHaveAttribute('data-drawings', String(count));
      const dialog = page.getByRole('dialog');
      if (await dialog.isVisible())
        await page.getByRole('button', { name: 'Close dialog', exact: true }).click();
    }
  await page.getByRole('button', { name: 'Undo', exact: true }).click();
  await expect(host).toHaveAttribute('data-drawings', String(count - 1));
  await page.getByRole('button', { name: 'Redo', exact: true }).click();
  await expect(host).toHaveAttribute('data-drawings', String(count));
  await expect(page.getByText('Saved locally', { exact: true })).toBeVisible();
  await page.reload();
  await expect(host).toHaveAttribute('data-drawings', String(count));
  await page.getByRole('button', { name: 'Delete all drawings', exact: true }).click();
  await page.getByRole('button', { name: 'Delete drawings', exact: true }).click();
  await expect(host).toHaveAttribute('data-drawings', '0');
});

test('drawing body move, endpoint resize, style, lock and delete are undoable', async ({
  page,
}) => {
  await page.goto('/chart');
  const host = page.getByTestId('chart-canvas-host');
  await expect(host).toHaveAttribute('data-loading', 'false');
  const box = (await page.getByTestId('chart-input').boundingBox())!;
  await page.getByRole('button', { name: 'Trend tools', exact: true }).click();
  await page.getByRole('menuitem', { name: /^Trend line/ }).click();
  const a = { x: box.x + 350, y: box.y + 240 },
    b = { x: box.x + 550, y: box.y + 340 };
  await page.mouse.move(a.x, a.y);
  await page.mouse.down();
  await page.mouse.move(b.x, b.y, { steps: 5 });
  await page.mouse.up();
  await expect(host).toHaveAttribute('data-drawings', '1');
  const read = () =>
    page.evaluate(() => {
      const root = JSON.parse(localStorage.getItem('haruquantai.chart.v1')!).state;
      return root.drawings[root.chart.symbol + ':' + root.chart.interval][0] as {
        points: { time: number; price: number }[];
        text: string;
        locked: boolean;
      };
    });
  await expect(page.getByText('Saved locally', { exact: true })).toBeVisible();
  const before = await read();
  await page.mouse.move((a.x + b.x) / 2, (a.y + b.y) / 2);
  await page.mouse.down();
  await page.mouse.move((a.x + b.x) / 2 + 40, (a.y + b.y) / 2 + 20, { steps: 5 });
  await page.mouse.up();
  await expect.poll(async () => (await read()).points[0].time).not.toBe(before.points[0].time);
  await page.getByRole('button', { name: 'Undo', exact: true }).click();
  await expect.poll(async () => (await read()).points[0].time).toBe(before.points[0].time);
  await page.mouse.move(a.x, a.y);
  await page.mouse.down();
  await page.mouse.move(a.x - 30, a.y - 40, { steps: 5 });
  await page.mouse.up();
  await expect.poll(async () => (await read()).points[0].price).not.toBe(before.points[0].price);
  await page.getByRole('button', { name: 'Favorites', exact: true }).click();
  await page.getByRole('button', { name: 'Trend line', exact: true }).last().click();
  await page.getByLabel('Drawing text', { exact: true }).fill('Support study');
  await page.getByLabel('Locked', { exact: true }).check();
  await page.getByRole('button', { name: 'Close dialog', exact: true }).click();
  await expect(
    page.getByRole('button', { name: 'Delete selected drawing', exact: true }),
  ).toBeDisabled();
  await expect.poll(async () => (await read()).text).toBe('Support study');
});

test('drawing menu hover closes on leave and permits menu selection', async ({ page }) => {
  await page.goto('/chart');
  const host = page.getByTestId('chart-canvas-host');
  await expect(host).toHaveAttribute('data-loading', 'false');
  const connection = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  if (await connection.isVisible())
    await connection.getByRole('button', { name: 'Close', exact: true }).click();

  for (const group of ['Trend', 'Fibonacci', 'Shapes', 'Annotate']) {
    const trigger = page.getByRole('button', { name: group + ' tools', exact: true });
    const caret = trigger.locator('.cq-caret');
    const menu = page.getByRole('menu', { name: group + ' tools', exact: true });
    await caret.hover();
    await expect(menu).toBeVisible();
    await page.getByRole('button', { name: 'Cursor mode', exact: true }).hover();
    await expect(menu).toBeHidden();

    await caret.hover();
    await expect(menu).toBeVisible();
    await menu.hover();
    // Remain inside beyond the closing delay to verify crossing the gap is safe.
    await page.waitForTimeout(250);
    await expect(menu).toBeVisible();
    await menu.getByRole('menuitem').first().click();
    await expect(menu).toBeHidden();
  }
});

test('cursor menu modes, effects, tooltip and eraser undo', async ({ page }, testInfo) => {
  test.setTimeout(60000);
  await page.goto('/chart');
  const host = page.getByTestId('chart-canvas-host');
  await expect(host).toHaveAttribute('data-loading', 'false');
  const connection = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  if (await connection.isVisible())
    await connection.getByRole('button', { name: 'Close', exact: true }).click();
  const cursor = page.getByRole('button', { name: 'Cursor mode', exact: true });
  const menu = page.getByRole('menu', { name: 'Cursor modes', exact: true });
  const select = async (name: string) => {
    await cursor.click();
    await menu.getByRole('menuitemradio', { name, exact: true }).click();
    await expect(menu).toBeHidden();
  };
  for (const [name, mode] of [
    ['Cross', 'crosshair'],
    ['Dot', 'dot'],
    ['Arrow', 'arrow'],
  ]) {
    await select(name);
    await expect(host).toHaveAttribute('data-cursor', mode);
  }
  await cursor.click();
  await menu.getByRole('button', { name: 'Favorite cursor Arrow', exact: true }).click();
  await expect(
    menu.getByRole('button', { name: 'Favorite cursor Arrow', exact: true }),
  ).toHaveAttribute('aria-pressed', 'true');
  await menu.getByRole('menuitemradio', { name: 'Cross', exact: true }).click();
  const box = (await page.getByTestId('chart-input').boundingBox())!;
  const x = box.x + 350,
    y = box.y + 240;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await expect(host).toHaveAttribute('data-values-tooltip', 'true');
  await page.mouse.up();
  await expect(host).toHaveAttribute('data-values-tooltip', 'false');
  await cursor.click();
  await menu.getByRole('switch', { name: 'Values tooltip on long press' }).click();
  await menu.getByRole('menuitemradio', { name: 'Cross', exact: true }).click();
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.waitForTimeout(600);
  await expect(host).toHaveAttribute('data-values-tooltip', 'false');
  await page.mouse.up();

  for (const name of ['Demonstration', 'Magic']) {
    await select(name);
    await page.mouse.move(x, y);
    await page.mouse.down();
    await page.mouse.move(x + 100, y + 60, { steps: 10 });
    await page.mouse.up();
    await expect
      .poll(async () => Number(await host.getAttribute('data-cursor-effects')))
      .toBeGreaterThan(0);
    await expect(host).toHaveAttribute('data-drawings', '0');
    await expect(host).toHaveAttribute('data-cursor-effects', '0');
  }
  await page.getByRole('button', { name: 'Trend tools', exact: true }).click();
  await page.getByRole('menuitem', { name: /^Trend line/ }).click();
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + 120, y + 80, { steps: 5 });
  await page.mouse.up();
  await expect(host).toHaveAttribute('data-drawings', '1');
  await select('Eraser');
  await page.getByRole('button', { name: 'Lock all drawings', exact: true }).click();
  await page.mouse.click(x + 60, y + 40);
  await expect(host).toHaveAttribute('data-drawings', '1');
  await page.getByRole('button', { name: 'Lock all drawings', exact: true }).click();
  await page.mouse.click(x + 60, y + 40);
  await expect(host).toHaveAttribute('data-drawings', '0');
  await page.getByRole('button', { name: 'Undo', exact: true }).click();
  await expect(host).toHaveAttribute('data-drawings', '1');
  await cursor.click();
  await page.getByRole('button', { name: 'Cursor mode', exact: true }).hover();
  await expect(menu).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('cursor-menu.png') });
  await page.getByRole('button', { name: 'Zoom in', exact: true }).hover();
  await expect(menu).toBeHidden();
});

test('line parity menu sections, favorites, shortcuts and channel editing', async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await page.goto('/chart');
  const host = page.getByTestId('chart-canvas-host');
  await expect(host).toHaveAttribute('data-loading', 'false');
  const trigger = page.getByRole('button', { name: 'Trend tools', exact: true });
  const menu = page.getByRole('menu', { name: 'Trend tools', exact: true });
  await trigger.click();
  await expect(menu.locator('.cq-line-heading')).toHaveText([
    'Lines',
    'Channels',
    'Pitchforks',
    'Additional tools',
  ]);
  await expect(menu.getByRole('menuitem')).toHaveCount(20);
  const favorite = menu.getByRole('button', { name: 'Favorite Parallel channel', exact: true });
  await favorite.click();
  await expect(favorite).toHaveAttribute('aria-pressed', 'true');
  await menu.getByRole('menuitem', { name: 'Parallel channel', exact: true }).click();
  await trigger.click();
  await expect(
    menu.getByRole('menuitem', { name: 'Parallel channel', exact: true }),
  ).toHaveAttribute('aria-current', 'true');
  await menu.getByRole('menuitem', { name: 'Parallel channel', exact: true }).click();
  const box = (await page.getByTestId('chart-input').boundingBox())!;
  const a = { x: box.x + 350, y: box.y + 230 };
  await page.mouse.click(a.x, a.y);
  await page.mouse.click(a.x + 150, a.y - 60);
  await page.mouse.click(a.x + 70, a.y + 90);
  await expect(host).toHaveAttribute('data-drawings', '1');
  const read = () =>
    page.evaluate(() => {
      const state = JSON.parse(localStorage.getItem('haruquantai.chart.v1')!).state;
      return (state.drawings[state.chart.symbol + ':' + state.chart.interval]?.[0]?.points ??
        []) as {
        time: number;
        price: number;
      }[];
    });
  await expect.poll(read).toHaveLength(3);
  const before = await read();
  await page.mouse.move(a.x, a.y);
  await page.mouse.down();
  await page.mouse.move(a.x - 30, a.y + 30, { steps: 5 });
  await page.mouse.up();
  await expect.poll(async () => (await read())[0].price).not.toBe(before[0].price);
  await page.getByRole('button', { name: 'Undo', exact: true }).click();
  await expect.poll(read).toEqual(before);
  await page.getByRole('button', { name: 'Lock all drawings', exact: true }).click();
  await page.mouse.move(a.x, a.y);
  await page.mouse.down();
  await page.mouse.move(a.x - 30, a.y + 30, { steps: 5 });
  await page.mouse.up();
  await expect.poll(read).toEqual(before);
  await page.getByRole('button', { name: 'Lock all drawings', exact: true }).click();
  await page.reload();
  await expect(host).toHaveAttribute('data-drawings', '1');
  await trigger.click();
  await expect(favorite).toHaveAttribute('aria-pressed', 'true');
  await page.screenshot({ path: testInfo.outputPath('line-tools-menu.png') });
  await menu
    .getByRole('menuitem', { name: 'Inside pitchfork', exact: true })
    .scrollIntoViewIfNeeded();
  await expect(menu.getByRole('menuitem', { name: 'Inside pitchfork', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Zoom in', exact: true }).hover();
  await expect(menu).toBeHidden();
  await page.keyboard.press('Alt+j');
  await expect(page.locator('.cq-hint')).toContainText('HorizontalRay');
  await page.keyboard.press('Escape');
  await page.keyboard.press('Alt+c');
  await expect(page.locator('.cq-hint')).toContainText('CrossLine');
  await page.keyboard.press('Escape');
});

test('Fibonacci parity menu, curve editing, favorites, locks and reload', async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await page.goto('/chart');
  const host = page.getByTestId('chart-canvas-host');
  await expect(host).toHaveAttribute('data-loading', 'false');
  const trigger = page.getByRole('button', { name: 'Fibonacci tools', exact: true });
  const menu = page.getByRole('menu', { name: 'Fibonacci tools', exact: true });
  await trigger.click();
  await expect(menu.locator('.cq-line-heading')).toHaveText(['Fibonacci', 'Gann']);
  await expect(menu.getByRole('menuitem')).toHaveCount(15);
  const favorite = menu.getByRole('button', { name: 'Favorite Fib spiral', exact: true });
  await favorite.click();
  await expect(favorite).toHaveAttribute('aria-pressed', 'true');
  await menu.getByRole('menuitem', { name: 'Fib circles', exact: true }).click();
  await trigger.click();
  await expect(menu.getByRole('menuitem', { name: 'Fib circles', exact: true })).toHaveAttribute(
    'aria-current',
    'true',
  );
  await menu.getByRole('menuitem', { name: 'Fib circles', exact: true }).click();
  const box = (await page.getByTestId('chart-input').boundingBox())!;
  const x = box.x + 350,
    y = box.y + 240;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + 120, y + 60, { steps: 5 });
  await page.mouse.up();
  await expect(host).toHaveAttribute('data-drawings', '1');
  const read = () =>
    page.evaluate(() => {
      const state = JSON.parse(localStorage.getItem('haruquantai.chart.v1')!).state;
      return (state.drawings[state.chart.symbol + ':' + state.chart.interval]?.[0]?.points ??
        []) as { time: number; price: number }[];
    });
  await expect.poll(read).toHaveLength(2);
  const before = await read();
  await page.mouse.move(x + 120, y + 60);
  await page.mouse.down();
  await page.mouse.move(x + 160, y + 80, { steps: 5 });
  await page.mouse.up();
  await expect.poll(async () => (await read())[1].price).not.toBe(before[1].price);
  await page.getByRole('button', { name: 'Undo', exact: true }).click();
  await expect.poll(read).toEqual(before);
  await page.getByRole('button', { name: 'Redo', exact: true }).click();
  await expect.poll(async () => (await read())[1].price).not.toBe(before[1].price);
  const after = await read();
  await page.getByRole('button', { name: 'Lock all drawings', exact: true }).click();
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + 30, y + 30, { steps: 5 });
  await page.mouse.up();
  await expect.poll(read).toEqual(after);
  await page.reload();
  await expect(host).toHaveAttribute('data-drawings', '1');
  await trigger.click();
  await expect(favorite).toHaveAttribute('aria-pressed', 'true');
  await page.screenshot({ path: testInfo.outputPath('fibonacci-menu.png') });
  await menu.getByRole('menuitem', { name: 'Gann fan', exact: true }).scrollIntoViewIfNeeded();
  await expect(menu.getByRole('menuitem', { name: 'Gann fan', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Zoom in', exact: true }).hover();
  await expect(menu).toBeHidden();
  await page.keyboard.press('Alt+f');
  await expect(page.locator('.cq-hint')).toContainText('FibRetracement');
  await page.keyboard.press('Escape');
});
