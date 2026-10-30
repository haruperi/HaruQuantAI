import { expect, test } from '@playwright/test';

import { selectLightSkin } from './shellTestUtils';

test.beforeEach(async ({ page }) => { await page.goto('/'); });

test('AI Assistant sits immediately above Fundamentals and supports direct links and reload', async ({ page }) => {
  const navigation = page.getByRole('complementary', { name: 'Applications' });
  const assistant = navigation.getByRole('button', { name: 'AI Assistant', exact: true });
  const labels = await navigation.getByRole('button').evaluateAll(buttons => buttons.map(button => button.getAttribute('aria-label')));
  expect(labels.slice(0, 3)).toEqual(['HaruQuantAI', 'AI Assistant', 'Data Manager']);
  await expect(assistant.locator('svg')).toBeVisible();
  await expect(assistant.locator('span')).toBeHidden();
  await navigation.hover();
  await expect(assistant.locator('span')).toBeVisible();
  const heading = navigation.getByText('Fundamentals', { exact: true });
  await expect(heading).toBeVisible();
  expect(await assistant.evaluate(button => button.parentElement?.nextElementSibling?.querySelector('.nav-group')?.textContent)).toBe('Fundamentals');
  await assistant.click();
  await expect(page).toHaveURL(/\/aiassistant(?:\?|$)/);
  await expect(assistant).toHaveClass(/active/);
  await expect(page.getByRole('region', { name: 'AI Assistant workspace' })).toBeVisible();
  await expect(navigation.locator('.nav-flyout')).toHaveCSS('width', '49px');
  await page.reload();
  await expect(assistant).toHaveClass(/active/);
  await page.goto('/');
  await page.goto('/aiassistant');
  await expect(assistant).toHaveClass(/active/);
  await expect(page.getByRole('heading', { name: 'What would you like to do?' })).toBeVisible();
});

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

test('Chart follows Data Manager and supports navigation, reload and direct links', async ({ page }) => {
  const navigation = page.getByRole('complementary', { name: 'Applications' });
  const chart = navigation.getByRole('button', { name: 'Chart', exact: true });
  const labels = await navigation.getByRole('button').evaluateAll(buttons =>
    buttons.map(button => button.getAttribute('aria-label')));
  const dataManagerIndex = labels.indexOf('Data Manager');
  expect(dataManagerIndex).toBeGreaterThanOrEqual(0);
  expect(labels.slice(dataManagerIndex, dataManagerIndex + 3)).toEqual(['Data Manager', 'Chart', 'Business']);
  await expect(chart.locator('svg')).toBeVisible();
  await expect(chart.locator('span')).toBeHidden();
  await navigation.hover();
  await expect(chart.locator('span')).toBeVisible();
  await chart.click();
  await expect(page).toHaveURL(/\/chart(?:\?|$)/);
  await expect(chart).toHaveClass(/active/);
  await expect(page.getByRole('region', { name: 'Chart', exact: true })).toBeVisible();
  await expect(page.getByText('SIMULATED DATA', { exact: true })).toBeVisible();
  await expect(navigation.locator('.nav-flyout')).toHaveCSS('width', '49px');
  await page.reload();
  await expect(chart).toHaveClass(/active/);
  await expect(page.getByRole('region', { name: 'Chart', exact: true })).toBeVisible();
  await page.goto('/');
  await page.goto('/chart');
  await expect(chart).toHaveClass(/active/);
  await expect(page.getByRole('region', { name: 'Chart', exact: true })).toBeVisible();
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
  await navigation.getByRole('button', { name: 'Chart', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Chart', exact: true })).toBeVisible();
});
