import {test,expect} from '@playwright/test';
import {resolve} from 'node:path';
const evidence=resolve(process.cwd(),'../../.agents/logs/2026-09-25T164633_portfolio-master-composer-ui-plan/verification');
test('Master settings, dialogs and summary use one local draft',async({page})=>{
 await page.goto('/portfolio?tab=settings');await expect(page.getByRole('tab',{name:'Automatic Portfolio Builder',exact:true})).toBeVisible();
 await expect(page.getByRole('tab',{name:'What to build',exact:true})).toHaveCount(0);
 await page.getByLabel('Minimum strategies',{exact:true}).fill('3');await page.getByLabel('Initial capital',{exact:true}).fill('25000');
 await page.getByRole('button',{name:'Genetic settings',exact:true}).click();await page.getByRole('dialog').getByLabel('Population size',{exact:true}).fill('200');await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Genetic settings',exact:true}).click();await expect(page.getByRole('dialog').getByLabel('Population size',{exact:true})).toHaveValue('200');await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Correlation settings',exact:true}).click();await page.getByLabel('Maximum correlation',{exact:true}).fill('0.3');await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Add condition',exact:true}).click();await page.getByLabel('Filter 1 value',{exact:true}).fill('100');
 await page.setViewportSize({width:1840,height:1000});await page.screenshot({path:resolve(evidence,'master-settings.png')});
 await page.getByRole('tab',{name:'Progress',exact:true}).click();await expect(page.locator('.pf-master-summary')).toContainText('3 – 8');await expect(page.locator('.pf-master-summary')).toContainText('25,000');await expect(page.locator('.pf-master-summary')).toContainText('0.3');
 await page.getByRole('button',{name:'Configure portfolio options',exact:true}).click();await expect(page.getByLabel('Minimum strategies',{exact:true})).toHaveValue('3');
});
test('Master mock lifecycle, guards, locking and result completion',async({page})=>{
 const writes:string[]=[];page.on('request',r=>{if(r.method()==='POST'&&/executions|portfolio/i.test(r.url()))writes.push(r.url());});
 await page.goto('/portfolio?tab=progress');await page.getByRole('checkbox',{name:'only selected',exact:true}).check();await expect(page.getByRole('button',{name:'Start',exact:true})).toBeDisabled();await page.getByRole('checkbox',{name:'only selected',exact:true}).uncheck();
 await page.getByRole('button',{name:'Start',exact:true}).click();await page.getByRole('button',{name:'Pause',exact:true}).click();await page.getByRole('tab',{name:'Full settings',exact:true}).click();await expect(page.getByText('Setting changes locked while the local preview is running.',{exact:true})).toBeVisible();
 await page.getByRole('tab',{name:'Progress',exact:true}).click();await page.getByRole('button',{name:'Resume',exact:true}).click();await page.getByRole('button',{name:'Stop',exact:true}).click();await page.getByRole('button',{name:'Start',exact:true}).click();
 await expect(page.locator('.sqd-task-desc')).toContainText('complete',{timeout:15000});await page.getByRole('button',{name:'Open Results',exact:true}).click();await expect(page.locator('.sqr-info-line')).toContainText('Portfolio 001');expect(writes).toEqual([]);
});
test('Master databank activation, query routing and layouts',async({page})=>{
 await page.goto('/portfolio?tab=progress');await page.setViewportSize({width:1567,height:958});await page.screenshot({path:resolve(evidence,'master-progress.png')});
 await page.getByRole('button',{name:'Expand databanks',exact:true}).click();await page.locator('.databanks-body').getByRole('button',{name:'Strategy Name',exact:true}).click();await page.locator('.databanks-body').getByText('Strategy 002',{exact:true}).dblclick();
 await expect(page.getByRole('tablist',{name:'Portfolio Master panels'}).getByRole('tab',{name:'Results',exact:true})).toHaveAttribute('aria-selected','true');await expect(page).toHaveURL(/tab=results/);await page.screenshot({path:resolve(evidence,'master-results-expanded.png')});
 await page.setViewportSize({width:900,height:760});await page.screenshot({path:resolve(evidence,'master-narrow.png')});
});
