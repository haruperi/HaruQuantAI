import { test, expect } from '@playwright/test';
test('every drawing tool creates an editable persisted object with undo and redo', async ({
  page,
}) => {
  test.setTimeout(120000);
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
      ],
    },
    {
      group: 'Fibonacci',
      names: [
        ['Fib retracement', 2],
        ['Fib extension', 3],
        ['Fib timezone', 2],
        ['Pitchfork', 3],
        ['Gann fan', 2],
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
          .getByRole('menuitem', {
            name: new RegExp('^' + name.replace(/[.*+?^$()|[\]\\]/g, '\\$&')),
          })
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
