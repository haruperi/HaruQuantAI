import { expect, test } from '@playwright/test';

import { selectLightSkin } from './shellTestUtils';

test.beforeEach(async ({ page }) => { await page.goto('/'); });

test('collapsed icon rail expands as a hover flyout and collapses when the pointer leaves', async ({ page }) => {
  const navigation = page.getByRole('complementary', { name: 'Applications' });
  const flyout = navigation.locator('.nav-flyout');
  const brandButton = navigation.getByRole('button', { name: 'HaruQuantAI', exact: true });
  const builder = navigation.getByRole('button', { name: 'Builder', exact: true });

  await expect(page.locator('.topbar > .nav-toggle')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Collapse navigation', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Expand navigation', exact: true })).toHaveCount(0);
  await expect(navigation).toHaveCSS('width', '49px');
  await expect(flyout).toHaveCSS('width', '49px');
  await expect(brandButton.getByText('HaruQuantAI', { exact: true })).toBeHidden();
  await expect(brandButton).toHaveText('HaruQuantAI');
  await expect(navigation.getByRole('button', { name: 'Improver', exact: true })).toHaveCount(0);
  await expect(navigation.getByRole('button', { name: 'Retester', exact: true })).toBeVisible();
  await expect(navigation.getByRole('button', { name: 'Optimizer', exact: true })).toBeVisible();
  await expect(builder.locator('svg')).toBeVisible();
  await expect(builder.locator('span')).toBeHidden();
  await expect(navigation.getByText('Fundamentals', { exact: true })).toBeHidden();

  await navigation.hover();
  await expect(flyout).toHaveCSS('width', '190px');
  await expect(navigation).toHaveCSS('width', '49px');
  await expect(builder.locator('span')).toBeVisible();
  await expect(navigation.getByText('Fundamentals', { exact: true })).toBeVisible();
  await expect(brandButton.getByText('HaruQuantAI', { exact: true })).toBeVisible();

  await navigation.getByRole('button', { name: 'Retester', exact: true }).hover();
  await expect(flyout).toHaveCSS('width', '190px');

  await navigation.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await expect(navigation.getByRole('button', { name: 'Data Manager', exact: true })).toHaveClass(/active/);
  await expect(page.locator('.dm-title')).toHaveText('Data Manager');
  await expect(flyout).toHaveCSS('width', '49px');

  await page.locator('.app-main').hover();
  await expect(flyout).toHaveCSS('width', '49px');
  await expect(builder.locator('span')).toBeHidden();

  await page.reload();
  await expect(flyout).toHaveCSS('width', '49px');
  await expect(navigation.getByRole('button', { name: 'Data Manager', exact: true })).toHaveClass(/active/);
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
  await expect(navigation).toHaveCSS('width', '49px');
  await expect(navigation.getByRole('button', { name: 'HaruQuantAI', exact: true }).locator('svg')).toBeVisible();
  await expect(navigation).toHaveCSS('background-color', 'rgb(226, 231, 235)');
  await navigation.hover();
  await expect(navigation.locator('.nav-flyout')).toHaveCSS('width', '190px');
});
