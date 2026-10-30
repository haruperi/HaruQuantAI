import { test, expect } from './frontendStructureFixtures';

const routes = ['/', '/aiassistant', '/datamanager', '/chart', '/business', '/builder', '/algowizard', '/codeeditor', '/neuralnet', '/retester', '/optimizer', '/mtanalyzer', '/projects', '/portfolio', '/composer', '/trading', '/debugconsole', '/gridcontrol', '/gridtest'];

for (const theme of ['dark', 'light'] as const) {
  for (const route of routes) {
    test(`migration preserves ${theme} ${route}`, async ({ page }) => {
      await page.addInitScript(() => {
        let seed = 42;
        Math.random = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
      });
      await page.clock.install({ time: new Date('2026-10-30T08:00:00Z') });
      await page.goto(route);
      await page.clock.runFor(2000);
      const dialog = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
      await dialog.getByLabel('Host password').fill('test-password');
      await dialog.getByRole('button', { name: 'Connect', exact: true }).click();
      await page.clock.runFor(1000);
      await expect(dialog).toHaveCount(0);
      await page.evaluate(nextTheme => {
        document.documentElement.dataset.theme = nextTheme;
      }, theme);
      await expect(page.locator('.app-shell')).toBeVisible();
      await expect(page).toHaveURL(new RegExp(`${route === '/' ? '/$' : route + '(?:\\?|$)'}`));
      const image = await page.screenshot({ animations: 'disabled', caret: 'hide' });
      // Baselines are captured from ui/ before source migration and moved with this suite.
      expect(image).toMatchSnapshot(`${theme}-${route.slice(1) || 'home'}.png`, {
        // Old-root replay showed ~0.2% canvas/timing noise on these two live charts.
        maxDiffPixelRatio: route === '/chart' || route === '/mtanalyzer' ? 0.003 : 0.001,
      });
    });
  }
}

test.use({ viewport: { width: 1440, height: 900 } });

test('migration retains saved Builder data and deep-link navigation', async ({ page }) => {
  await page.addInitScript(() => {
    if (!localStorage.getItem('sqx-recreation-v1')) {
      localStorage.setItem('sqx-recreation-v1', JSON.stringify({
        version: 1, state: { module: 'builder', tab: 'settings', builder: { population: 250 } },
      }));
    }
  });
  await page.goto('/builder?tab=settings');
  await expect(page.locator('.app-shell')).toBeVisible();
  const readSaved = () => page.evaluate(() => JSON.parse(localStorage.getItem('sqx-recreation-v1')!));
  expect((await readSaved()).state.builder.population).toBe(250);
  await page.reload();
  expect((await readSaved()).state.builder.population).toBe(250);
  await expect(page).toHaveURL(/\/builder\?tab=settings/);
  await page.goto('/home');
  await expect(page.getByRole('main', { name: 'Home workspace' })).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(/\/builder\?tab=settings/);
  expect((await readSaved()).version).toBe(1);
});

for (const width of [1280, 1920]) {
  test(`migration retains shell geometry at width ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: width === 1280 ? 720 : 1080 });
    await page.goto('/builder');
    await expect(page.locator('.app-shell')).toBeVisible();
    const dialog = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
    await dialog.getByLabel('Host password').fill('test-password');
    await dialog.getByRole('button', { name: 'Connect', exact: true }).click();
    await expect(dialog).toHaveCount(0);
    await page.getByRole('tab', { name: 'Full settings', exact: true }).click();
    await expect(page.getByRole('tablist', { name: 'Settings tabs' })).toBeVisible();
    await expect(page.locator('.statusbar')).toBeVisible();
    const geometry = await page.locator('.app-shell').boundingBox();
    expect(geometry?.width).toBe(width);
    await page.getByRole('tab', { name: 'Results', exact: true }).click();
    await expect(page.locator('.app-shell')).toBeVisible();
  });
}
