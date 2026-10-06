import { test, expect } from './frontendStructureFixtures';

test('Select remains functional while childless Tools entries stay inactive', async ({ page }, info) => {
  await page.goto('/builder');
  await page.getByRole('button', { name: 'Expand databanks', exact: true }).click();
  const pane = page.locator('.sqn-databanks');
  await pane.getByRole('button', { name: 'Tools', exact: true }).click();
  await pane.getByRole('menuitem', { name: 'Select', exact: true }).hover();
  await pane.getByRole('menuitem', { name: 'Passed', exact: true }).click();
  const passed = await pane.getByRole('checkbox', { name: /^Select Strategy / }).evaluateAll(nodes => nodes.filter(node => (node as HTMLInputElement).checked).map(node => node.getAttribute('aria-label')));
  expect(passed.length).toBeGreaterThan(0);
  await pane.getByRole('button', { name: 'Tools', exact: true }).click();
  await pane.getByRole('menuitem', { name: 'Set note', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(pane.getByRole('menu', { name: 'Tools menu', exact: true })).toBeVisible();
  await page.screenshot({ path: info.outputPath('selection-inactive-note.png') });
  await pane.getByRole('menuitem', { name: 'Select', exact: true }).hover();
  await pane.getByRole('menuitem', { name: 'Failed', exact: true }).click();
  const failed = await pane.getByRole('checkbox', { name: /^Select Strategy / }).evaluateAll(nodes => nodes.filter(node => (node as HTMLInputElement).checked).map(node => node.getAttribute('aria-label')));
  expect(failed.length).toBeGreaterThan(0);
  expect(failed.filter(name => passed.includes(name))).toEqual([]);
});
