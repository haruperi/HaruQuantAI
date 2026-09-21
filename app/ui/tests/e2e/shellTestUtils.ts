import type { Page } from '@playwright/test';

export async function selectLightSkin(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Skin', exact: true }).click();
  await page.getByRole('menu', { name: 'Skin' }).getByRole('menuitem', { name: 'Light skin', exact: true }).click();
}

export async function setFeatureProfileFixture(page: Page, profile: 'Full' | 'Starter'): Promise<void> {
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Skin', exact: true }).click();
  await page.getByRole('menu', { name: 'Skin' }).getByRole('menuitem', { name: 'Dark skin', exact: true }).click();
  await page.evaluate(nextProfile => {
    const key = 'sqx-recreation-v1';
    const raw = window.localStorage.getItem(key);
    if (!raw) throw new Error('Expected the persisted application fixture to exist.');
    const saved = JSON.parse(raw) as { state?: { settings?: Record<string, unknown> }; version?: number };
    if (saved.version !== 1 || !saved.state?.settings) throw new Error('Unexpected application fixture schema.');
    saved.state.settings.profile = nextProfile;
    window.localStorage.setItem(key, JSON.stringify(saved));
  }, profile);
  await page.reload();
  await page.waitForFunction(expected => document.documentElement.dataset.profile === expected, profile);
}
