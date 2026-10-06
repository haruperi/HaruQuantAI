import { expect, test, type Page } from '@playwright/test';

async function expand(page: Page, route = '/builder') {
  await page.goto(route);
  await page.getByRole('button', { name: 'Expand databanks', exact: true }).click();
  return page.locator('.sqn-databanks');
}

test('pane collapse, drag, maximize and restore across project mounts', async ({ page }, info) => {
  const pane = await expand(page);
  await expect(page.locator('.sq-splitter')).toHaveClass('sq-splitter active');
  await expect(pane.getByRole('tablist', { name: 'Databanks' })).toBeVisible();
  const resizer = await pane.getByRole('separator', { name: 'Resize databanks pane' }).boundingBox();
  expect(resizer).not.toBeNull();
  await page.mouse.move(resizer!.x + resizer!.width / 2, resizer!.y + resizer!.height / 2);
  await page.mouse.down();
  await page.mouse.move(resizer!.x + resizer!.width / 2, resizer!.y - 80, { steps: 5 });
  await page.mouse.up();
  await expect(page.locator('.sq-splitter-top')).toHaveAttribute('style', /flex-basis/);
  await pane.getByRole('button', { name: 'Maximize databanks' }).click();
  await expect(page.locator('.sq-splitter')).toHaveClass('sq-splitter active maximised');
  await expect(page.locator('.sq-splitter-top')).toBeHidden();
  await page.screenshot({ path: info.outputPath('databanks-maximized.png') });
  await pane.getByRole('button', { name: 'Restore workspace' }).click();
  await pane.getByRole('button', { name: 'Collapse databanks' }).click();
  await expect(pane.locator('.sqn-databanks-header')).toContainText('DATABANKS 3');
  await expect(pane.locator('.sqn-databanks-header')).toContainText('STRATEGIES: 70');
  await pane.getByRole('button', { name: 'Expand databanks' }).click();
  await expect(page.locator('.sq-splitter-top')).not.toHaveAttribute('style', /flex-basis/);
  for (const route of ['/retester', '/optimizer']) {
    const mounted = await expand(page, route);
    await expect(mounted.getByRole('tablist', { name: 'Databanks' })).toBeVisible();
    await mounted.getByRole('button', { name: 'Collapse databanks' }).click();
  }
});

test('fixture selection, rename, delete confirmation and deferred save', async ({ page }) => {
  const pane = await expand(page);
  await pane.getByRole('checkbox', { name: /^Select Strategy / }).first().check();
  await pane.getByRole('button', { name: 'Rename', exact: true }).click();
  let dialog = page.getByRole('dialog');
  await dialog.getByRole('textbox').fill('Reviewed strategy');
  await dialog.getByRole('button', { name: 'Rename', exact: true }).click();
  await expect(pane.getByRole('checkbox', { name: 'Select Reviewed strategy', exact: true })).toBeChecked();
  await pane.getByRole('button', { name: 'Save', exact: true }).click();
  await pane.getByRole('menuitem', { name: 'HTML report', exact: true }).click();
  dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await pane.getByRole('button', { name: 'Delete', exact: true }).click();
  dialog = page.getByRole('dialog');
  await dialog.getByRole('button', { name: 'No', exact: true }).click();
  await expect(pane.getByRole('checkbox', { name: 'Select Reviewed strategy', exact: true })).toBeVisible();
  await pane.getByRole('button', { name: 'Delete', exact: true }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Yes', exact: true }).click();
  await expect(pane.getByRole('checkbox', { name: 'Select Reviewed strategy', exact: true })).toHaveCount(0);
});

test('bank tabs, views, manage dialog and narrow presentation', async ({ page }, info) => {
  const pane = await expand(page);
  await pane.getByRole('tab', { name: 'Last generation', exact: true }).click();
  await expect(pane.locator('.sqx-records-count')).toContainText('18');
  const view = pane.getByRole('combobox', { name: 'Databank view' });
  const options = await view.locator('option').allTextContents();
  expect(options.length).toBeGreaterThan(1);
  await view.selectOption({ label: options[1] });
  await expect(view).toHaveValue(options[1]);
  await pane.getByRole('button', { name: 'Manage databank views' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.setViewportSize({ width: 1000, height: 760 });
  await page.screenshot({ path: info.outputPath('databanks-narrow.png') });
  await expect(pane.getByRole('button', { name: 'Collapse databanks' })).toBeVisible();
});
