import { expect, test } from '@playwright/test';

import { selectLightSkin } from './shellTestUtils';

test.beforeEach(async ({ page }) => { await page.goto('/'); });

test('sidebar collapses to a persistent icon rail and expands again', async ({ page }) => {
  const shell = page.locator('.app-shell');
  const navigation = page.getByRole('complementary', { name: 'Applications' });
  const topbar = page.locator('.topbar');
  const brandName = page.locator('.brand strong');
  const builder = navigation.getByRole('button', { name: 'Builder', exact: true });
  const collapse = page.getByRole('button', { name: 'Collapse navigation', exact: true });

  await expect(navigation).toHaveCSS('width', '190px');
  await expect(topbar.locator(':scope > .nav-toggle')).toBeVisible();
  await expect(navigation.locator('.nav-toggle')).toHaveCount(0);
  await expect(page.getByText('Applications', { exact: true })).toHaveCount(0);
  await expect(navigation.getByRole('button', { name: 'Improver', exact: true })).toHaveCount(0);
  await expect(navigation.getByRole('button', { name: 'Retester', exact: true })).toBeVisible();
  await expect(navigation.getByRole('button', { name: 'Optimizer', exact: true })).toBeVisible();
  await expect(brandName).toHaveText('HaruQuantAI');
  await expect(brandName).toBeVisible();
  await expect(collapse.locator('.lucide-list-indent-decrease')).toBeVisible();
  await expect(builder.locator('span')).toBeVisible();
  await expect(navigation.getByText('Research', { exact: true })).toBeVisible();

  await collapse.click();
  await expect(shell).toHaveClass(/nav-collapsed/);
  await expect(navigation).toHaveCSS('width', '49px');
  await expect(brandName).toBeHidden();
  await expect(page.getByRole('button', { name: 'Expand navigation', exact: true }).locator('.lucide-list-indent-increase')).toBeVisible();
  await expect(builder.locator('svg')).toBeVisible();
  await expect(builder.locator('span')).toBeHidden();
  await expect(navigation.getByText('Research', { exact: true })).toBeHidden();

  await navigation.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await expect(navigation.getByRole('button', { name: 'Data Manager', exact: true })).toHaveClass(/active/);
  await expect(page.locator('.dm-title')).toHaveText('Data Manager');

  await page.reload();
  await expect(shell).toHaveClass(/nav-collapsed/);
  await expect(navigation).toHaveCSS('width', '49px');
  await page.getByRole('button', { name: 'Expand navigation', exact: true }).click();
  await expect(shell).not.toHaveClass(/nav-collapsed/);
  await expect(navigation).toHaveCSS('width', '190px');
  await expect(brandName).toBeVisible();
  await expect(page.getByRole('button', { name: 'Collapse navigation', exact: true })).toBeVisible();
  await expect(navigation.getByRole('button', { name: 'Data Manager', exact: true }).locator('span')).toBeVisible();
});

test('legacy Improver workspace opens Builder with improve-existing behavior retained', async ({ page }) => {
  await page.evaluate(() => localStorage.setItem('sqx-recreation-v1', JSON.stringify({
    state: { module: 'improver' },
    version: 1,
  })));
  await page.reload();

  const navigation = page.getByRole('complementary', { name: 'Applications' });
  await expect(navigation.getByRole('button', { name: 'Improver', exact: true })).toHaveCount(0);
  await expect(navigation.getByRole('button', { name: 'Builder', exact: true })).toHaveClass(/active/);
  await expect(page.locator('.project-header h1')).toHaveText('Builder');

  await page.getByRole('button', { name: 'Full settings', exact: true }).click();
  await page.getByLabel('Build mode').selectOption('Improve existing');
  await expect(page.getByRole('checkbox', { name: 'Seed from input databank', exact: true })).toBeChecked();
});

test('collapsed navigation remains usable with the light skin', async ({ page }) => {
  await page.setViewportSize({ width: 520, height: 700 });
  await selectLightSkin(page);
  const navigation = page.getByRole('complementary', { name: 'Applications' });
  await page.getByRole('button', { name: 'Collapse navigation', exact: true }).click();
  await expect(navigation).toHaveCSS('width', '49px');
  await expect(navigation.getByRole('button', { name: 'Home', exact: true }).locator('svg')).toBeVisible();
  await expect(navigation).toHaveCSS('background-color', 'rgb(226, 231, 235)');
});
