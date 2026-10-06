import {test,expect} from './frontendStructureFixtures';
import {resolve} from 'node:path';
const evidence=resolve(process.cwd(),'../../.agents/logs/2026-09-25T151716_builder-results-ui-correction/verification');
test.beforeEach(async({page})=>{await page.goto('/builder');await page.getByRole('tab',{name:'Results',exact:true}).click();});
test('populated views, selection and screenshots',async({page})=>{
 await expect(page.locator('.sqr-info-line')).toContainText('Local mock');
 for(const name of ['Overview','SP overview','List of trades','Equity chart','Trade analysis','Profile chart','Strategy config','Source Code','Monte Carlo tests','Trades on chart','Portfolio correlation']){
  await page.getByRole('tab',{name,exact:true}).click();
  await expect(page.getByRole('tab',{name,exact:true})).toHaveAttribute('aria-selected','true');
  await page.locator('.sqr-results').screenshot({path:resolve(evidence,name.replaceAll(' ','-')+'.png')});
 }
 await page.setViewportSize({width:1000,height:760});
 await page.getByRole('tab',{name:'Overview',exact:true}).click();
 await page.locator('.sqr-results').screenshot({path:resolve(evidence,'narrow.png')});
 const boxes=await page.locator('.sqr-results').evaluate(e=>({width:e.clientWidth,scroll:e.scrollWidth}));expect(boxes.scroll).toBeLessThanOrEqual(boxes.width+1);
});
test('trade filtering, view CRUD, sorting and CSV download',async({page})=>{
 await page.getByRole('tab',{name:'List of trades',exact:true}).click();
 const view=page.locator('.sqr-panel-slot:not([hidden])');
 await expect(view.locator('tbody tr')).toHaveCount(23);
 await view.getByRole('button',{name:'Lng',exact:true}).click();await expect(view.locator('tbody tr')).toHaveCount(12);
 await view.getByRole('button',{name:'OOS',exact:true}).click();await expect(view.locator('tbody tr')).toHaveCount(4);
 await view.getByRole('button',{name:'Manage views',exact:true}).click();await page.getByLabel('View name').fill('Review');await page.getByRole('button',{name:'Save view',exact:true}).click();await page.getByRole('dialog').getByRole('button',{name:'Close',exact:true}).click();
 await expect(view.getByLabel('View',{exact:true})).toHaveValue('Review');
 const download=page.waitForEvent('download');await view.getByRole('button',{name:'Export',exact:true}).click();await page.getByRole('dialog').getByRole('button',{name:'Export',exact:true}).click();expect((await download).suggestedFilename()).toBe('trades.csv');
 await page.getByRole('tab',{name:'Overview',exact:true}).click();await page.getByRole('tab',{name:'List of trades',exact:true}).click();await expect(view.locator('tbody tr')).toHaveCount(4);
});
test('source preview download, refresh and custom analysis lifecycle',async({page})=>{
 await page.getByRole('tab',{name:'Source Code',exact:true}).click();await expect(page.getByLabel('Source code',{exact:true})).toContainText('Local mock preview');
 await page.getByLabel('Source code type').selectOption('XML');await expect(page.getByLabel('Source code',{exact:true})).toContainText('Format: XML');
 await page.getByRole('button',{name:'Refresh source code',exact:true}).click();await expect(page.getByLabel('Source code',{exact:true})).toContainText('Revision: 1');
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Save to file',exact:true}).click();expect((await download).suggestedFilename()).toBe('strategy-preview.txt');
 await page.getByRole('button',{name:'+ New analysis',exact:true}).click();await page.getByLabel('Name of custom plugin tab').fill('Review panel');await page.getByRole('button',{name:'Create',exact:true}).click();await expect(page.getByRole('tab',{name:/Review panel/})).toBeVisible();
 await page.getByRole('button',{name:'Review panel menu',exact:true}).click();await page.getByRole('button',{name:'Delete',exact:true}).click();await page.getByRole('dialog').getByRole('button',{name:'Delete',exact:true}).click();await expect(page.getByRole('tab',{name:/Review panel/})).toHaveCount(0);
});
test('equity controls, chart settings and Results stays below header',async({page})=>{
 await page.getByRole('tab',{name:'Equity chart',exact:true}).click();const slot=page.locator('.sqr-panel-slot:not([hidden])');
 await slot.getByRole('button',{name:'Time',exact:true}).click();await expect(slot.getByRole('img',{name:/Equity \/ Time/})).toBeVisible();
 await slot.getByRole('button',{name:'Chart settings',exact:true}).click();await slot.getByRole('group',{name:'Drawdown',exact:true}).getByRole('button',{name:'Off',exact:true}).click();await page.keyboard.press('Escape');await expect(slot.getByRole('img',{name:/Drawdown/})).toHaveCount(0);
 await page.getByRole('tab',{name:'Progress',exact:true}).click();await expect(page.locator('.sqd-dashboard')).toBeVisible();
});

test('profile paths and stored trade chart interactions',async({page})=>{
 await page.getByRole('tab',{name:'Profile chart',exact:true}).click();
 await page.getByLabel('Profile chart',{exact:true}).selectOption('GBPUSD / H1 / TPO profile');
 await expect(page.getByRole('img',{name:'GBPUSD / H1 / TPO profile',exact:true})).toBeVisible();
 await expect(page.getByText('Loading chart...', {exact:true})).toHaveCount(0);
 await page.getByRole('tab',{name:'Trades on chart',exact:true}).click();
 await page.getByRole('button',{name:'Next trade',exact:true}).click();
 await expect(page.getByText(/Selected bar: 2/)).toBeVisible();
 await page.getByRole('button',{name:'Zoom in',exact:true}).click();
 await expect(page.getByRole('img',{name:'Trades on chart',exact:true})).toHaveAttribute('viewBox','0 0 720 280');
 await page.getByRole('button',{name:'reset',exact:true}).click();
 await expect(page.getByRole('img',{name:'Trades on chart',exact:true})).toHaveAttribute('viewBox','0 0 900 280');
});

test('databank activation selects result and conditional views',async({page})=>{
 await page.getByRole('tab',{name:'Progress',exact:true}).click();
 await page.getByRole('button',{name:'Expand databanks',exact:true}).click();
 await page.locator('.databanks-body').getByRole('button',{name:'Strategy Name',exact:true}).click();
 await page.locator('.databanks-body').getByText('Strategy 002',{exact:true}).dblclick();
 await expect(page.getByRole('tablist',{name:'Builder panels'}).getByRole('tab',{name:'Results',exact:true})).toHaveAttribute('aria-selected','true');
 await expect(page.locator('.sqr-info-line')).toContainText('Strategy 002');
 await expect(page.getByRole('tab',{name:'Stockpicker log',exact:true})).toBeVisible();
 await page.locator('.databanks-body').getByText('Strategy 003',{exact:true}).dblclick();
 await expect(page.locator('.sqr-info-line')).toContainText('Strategy 003');
 await expect(page.getByRole('tab',{name:'Trades on chart',exact:true})).toHaveCount(0);
 await page.getByRole('tab',{name:'Profile chart',exact:true}).click();
 await expect(page.getByText(/No profile charts are stored/)).toBeVisible();
});
test('source clipboard and saved columns',async({page,context})=>{
 await context.grantPermissions(['clipboard-read','clipboard-write']);
 await page.getByRole('tab',{name:'Source Code',exact:true}).click();
 await page.getByRole('button',{name:'Copy to clipboard',exact:true}).click();
 await expect.poll(()=>page.evaluate(()=>navigator.clipboard.readText())).toContain('Local mock preview');
 await page.getByRole('tab',{name:'List of trades',exact:true}).click();
 await page.getByRole('button',{name:'Manage views',exact:true}).click();
 await page.getByRole('dialog').getByRole('checkbox',{name:'Close price',exact:true}).uncheck();
 await page.getByRole('button',{name:'Save changes',exact:true}).click();
 await page.keyboard.press('Escape');
 await expect(page.locator('.sqr-panel-slot:not([hidden])').getByRole('columnheader',{name:'Close price',exact:true})).toHaveCount(0);
});
