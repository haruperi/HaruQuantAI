import { test, expect } from './frontendStructureFixtures';
import { resolve } from 'node:path';
const evidence = resolve(process.cwd(), '../../.agents/logs/2026-09-25T145329_builder-settings-visual-correction/verification');
const titles = ['What to build', 'Genetic options', 'Data', 'Trading options', 'Building blocks', 'ATM', 'Money management', 'Cross checks (robustness)', 'Ranking', 'Notes'];
test.beforeEach(async ({ page }) => {
  await page.goto('/builder');
  await page.getByRole('tab', { name: 'Full settings', exact: true }).click();
});
test('header and settings geometry, cards, all tabs and screenshots', async ({ page }) => {
  await page.setViewportSize({width:1887,height:1031});
  const header = page.locator('.sqd-dashboard-header');
  const strip = page.getByRole('tablist', {name:'Settings tabs'});
  await expect(strip.getByRole('tab')).toHaveText(titles);
  await expect(page.locator('.sqd-project-name')).toHaveText('Builder');
  const geometry = await page.locator('.builder-workspace').evaluate(el => {
    const rect = (s:string) => {const r=el.querySelector(s)!.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom};};
    return {header:rect('.sqd-dashboard-header'),title:rect('.sqd-advanced-title'),tabs:rect('.sqd-stabs-header'),card:rect('#buildTypeContent .sqd-fieldset'),host:getComputedStyle(el.querySelector('.sqd-fullsettings')!).position};
  });
  expect(geometry.host).toBe('relative');
  expect(geometry.title.y).toBeGreaterThanOrEqual(geometry.header.bottom);
  expect(geometry.tabs.y).toBeGreaterThan(geometry.title.bottom);
  expect(geometry.card.width).toBeLessThanOrEqual(1001);
  expect(geometry.card.width).toBeGreaterThan(800);
  await expect(page.locator('.sqd-settings-nextbtns')).toBeHidden();
  await page.locator('.builder-workspace').screenshot({path:resolve(evidence,'what-to-build.png')});
  for(const title of titles.slice(1)) {
    await strip.getByRole('tab',{name:title,exact:true}).click();
    await expect(strip.getByRole('tab',{name:title,exact:true})).toHaveAttribute('aria-selected','true');
    await expect(page.locator('.sqd-settings-body-inner > div:visible')).toHaveCount(1);
    await page.locator('.builder-workspace').screenshot({path:resolve(evidence,title.toLowerCase().replace(/[^a-z]+/g,'-')+'.png')});
  }
  await page.setViewportSize({width:1567,height:958});
  await strip.getByRole('tab',{name:'What to build',exact:true}).click();
  await page.locator('.builder-workspace').screenshot({path:resolve(evidence,'user-viewport.png')});
  await expect(header).toBeVisible();
});
test('conditional tabs and local edits survive navigation', async ({page}) => {
  await page.getByRole('radio',{name:'Improve existing strategy',exact:true}).check();
  await page.getByRole('tab',{name:'Parts to improve',exact:true}).click();
  await page.getByRole('tab',{name:'What to build',exact:true}).click();
  await expect(page.getByRole('radio',{name:'Improve existing strategy',exact:true})).toBeChecked();
  await page.getByRole('radio',{name:'Multi-TF or multi-symbol strategy',exact:true}).check();
  await expect(page.getByRole('tab',{name:'Parts to improve',exact:true})).toHaveCount(0);
  await page.getByLabel('Additional charts',{exact:true}).fill('4');
  await page.getByRole('tab',{name:'Data',exact:true}).click();
  await page.getByRole('tab',{name:'What to build',exact:true}).click();
  await expect(page.getByLabel('Additional charts',{exact:true})).toHaveValue('4');
  await page.getByRole('tab',{name:'Genetic options',exact:true}).click();
  await page.getByLabel('Max generations',{exact:true}).fill('120');
  await page.getByRole('tab',{name:'Data',exact:true}).click();
  await page.getByRole('tab',{name:'Genetic options',exact:true}).click();
  await expect(page.getByLabel('Max generations',{exact:true})).toHaveValue('120');
});
test('six gear dialogs, local edit/reset and Help link', async ({page}) => {
  for (const name of ['Trading directions','Strategy style','Build mode','# of Conditions, Periods','Stop Loss','Profit Target']) {
    await page.getByRole('button',{name:'Configure '+name,exact:true}).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.getByRole('dialog').screenshot({path:resolve(evidence,'dialog-'+name.toLowerCase().replace(/[^a-z]+/g,'-')+'.png')});
    await page.getByRole('dialog').getByRole('button',{name:'Save',exact:true}).click();
  }
  await page.getByRole('button',{name:'Configure Trading directions',exact:true}).click();
  await page.getByRole('radio',{name:'Long only',exact:true}).check();
  await page.getByRole('dialog').getByRole('button',{name:'Save',exact:true}).click();
  await expect(page.locator('.sqd-acp-desc').first()).toHaveText('Long only');
  await page.getByRole('button',{name:'Configure Trading directions',exact:true}).click();
  await page.getByRole('button',{name:'Reset to default',exact:true}).click();
  await page.getByRole('dialog').press('Escape');
  await expect(page.locator('.sqd-acp-desc').first()).toContainText('Both (Long & Short)');
  await expect(page.getByRole('tab',{name:'Full settings',exact:true})).toHaveAttribute('aria-selected','true');
  const popup = page.waitForEvent('popup');
  await page.locator('.sqd-settings-body-header').getByRole('button',{name:'Help',exact:true}).click();
  const help = await popup;
  await expect(help).toHaveURL(/strategyquant.com\/doc\/strategyquant\/what-to-build/);
  await help.close();
});
test('adjacent panels and keyboard activation remain usable', async({page}) => {
  await page.getByRole('tab',{name:'Results',exact:true}).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('tab',{name:'Results',exact:true})).toHaveAttribute('aria-selected','true');
  await page.getByRole('tab',{name:'Progress',exact:true}).click();
  await expect(page.locator('.sqd-dashboard')).toBeVisible();
  await page.getByRole('tab',{name:'Full settings',exact:true}).click();
  await expect(page.locator('.sqd-advanced-title')).toBeVisible();
});

test('data presets, genetic filters, ATM and cross-check local controls', async ({page}) => {
  await page.getByRole('tab',{name:'Data',exact:true}).click();
  await page.getByLabel('Test precision',{exact:true}).selectOption('3');
  await page.getByRole('button',{name:'Apply preset IST: 50, ISV: 20, OOS: 30',exact:true}).click();
  await expect(page.locator('.sqd-oos-range-row')).toHaveCount(3);
  await expect(page.locator('.sqd-oos-graph')).toBeVisible();
  await page.getByRole('tab',{name:'Genetic options',exact:true}).click();
  await page.getByRole('button',{name:'+ Add condition',exact:true}).click();
  await expect(page.getByLabel('Filter metric 2')).toBeVisible();
  await page.getByLabel('Filter value 2').fill('100');
  await page.getByRole('button',{name:'Remove filter 1',exact:true}).click();
  await expect(page.getByLabel('Filter value 1')).toHaveValue('100');
  await page.getByRole('tab',{name:'ATM',exact:true}).click();
  const count = await page.locator('.sqd-atm-row').count();
  await page.getByRole('button',{name:'Add new exit method',exact:true}).click();
  await page.getByRole('dialog').getByRole('button',{name:'Add',exact:true}).click();
  await expect(page.locator('.sqd-atm-row')).toHaveCount(count+1);
  await page.getByRole('tab',{name:'Cross checks (robustness)',exact:true}).click();
  await page.getByRole('button',{name:'Save cross checks',exact:true}).click();
  await page.getByRole('checkbox',{name:'Disable all cross checks',exact:true}).check();
  await page.getByRole('button',{name:'Load cross checks',exact:true}).click();
  await expect(page.getByRole('checkbox',{name:'Disable all cross checks',exact:true})).not.toBeChecked();
  await expect(page.locator('.cross-checks').getByRole('status')).toContainText('snapshot restored');
});
test('running lock prevents settings input and light theme remains legible', async ({page}) => {
  await page.getByRole('tab',{name:'Progress',exact:true}).click();
  await page.getByRole('button',{name:'Start',exact:true}).click();
  await page.getByRole('tab',{name:'Full settings',exact:true}).click();
  await expect(page.locator('.sqd-settings-body-inner')).toHaveClass(/disabled-panel/);
  await expect(page.locator('#buildTypeContent').locator('..')).toHaveAttribute('inert','');
  await page.getByRole('tab',{name:'Progress',exact:true}).click();
  await page.getByRole('button',{name:'Stop',exact:true}).click();
  await page.getByRole('tab',{name:'Full settings',exact:true}).click();
  await page.getByRole('radio',{name:'Multi-TF or multi-symbol strategy',exact:true}).check();
  await page.evaluate(()=>document.documentElement.dataset.theme='light');
  await expect(page.locator('#buildTypeContent .sqd-fieldset').first()).not.toHaveCSS('background-color','rgb(59, 59, 59)');
  await page.locator('.builder-workspace').screenshot({path:resolve(evidence,'light-theme.png')});
});
test('Ranking and Money management controls remain visible and editable', async ({page}) => {
  await page.getByRole('tab',{name:'Money management',exact:true}).click();
  await expect(page.getByLabel('Initial capital',{exact:true})).toHaveValue('10000');
  await page.getByLabel('FixedSize Size',{exact:true}).fill('0.5');
  await page.getByRole('tab',{name:'Ranking',exact:true}).click();
  await page.getByRole('radio',{name:/^Totally/}).check();
  await page.getByLabel('Passed strategies',{exact:true}).fill('250');
  await expect(page.getByLabel('Passed strategies',{exact:true})).toHaveCSS('opacity','1');
  await page.getByLabel('Fitness criterion',{exact:true}).selectOption('NetProfit');
  await page.getByRole('button',{name:'+ Add criterion',exact:true}).click();
  await expect(page.getByLabel('Fitness criterion',{exact:true})).toHaveCount(2);
  await page.getByRole('tab',{name:'Money management',exact:true}).click();
  await expect(page.getByLabel('FixedSize Size',{exact:true})).toHaveValue('0.5');
});
