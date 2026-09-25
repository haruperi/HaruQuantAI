import {test,expect} from '@playwright/test';
import {resolve} from 'node:path';
const evidence=resolve(process.cwd(),'../../.agents/logs/2026-09-25T160123_retester-optimizer-ui-plan/verification');
test('Retester lifecycle, locking, settings retention and local-only actions',async({page})=>{
 const requests:string[]=[];page.on('request',r=>{if(r.method()==='POST')requests.push(r.url());});
 await page.goto('/retester?tab=progress');
 await page.getByLabel('Retest only selected').check();
 await expect(page.getByRole('button',{name:'Start',exact:true})).toBeDisabled();
 await page.getByLabel('Retest only selected').uncheck();
 await page.getByRole('button',{name:'Start',exact:true}).click();
 await page.getByRole('button',{name:'Pause',exact:true}).click();
 await expect(page.getByRole('button',{name:'Resume',exact:true})).toBeEnabled();
 await page.getByRole('tab',{name:'Full settings',exact:true}).click();
 await expect(page.getByText('Setting changes locked while the local preview is running.')).toBeVisible();
 await page.getByRole('tab',{name:'Progress',exact:true}).click();
 await page.getByRole('button',{name:'Stop',exact:true}).click();
 await page.getByRole('tab',{name:'Full settings',exact:true}).click();
 await expect(page.getByRole('tab',{name:'Cross checks (robustness)',exact:true})).toBeVisible();
 await expect(page.getByRole('tab',{name:'What to retest',exact:true})).toHaveCount(0);
 await page.getByRole('tab',{name:'Notes',exact:true}).click();await page.getByRole('textbox',{name:'Notes',exact:true}).fill('Retest note');
 await page.getByRole('tab',{name:'Progress',exact:true}).click();await page.getByRole('tab',{name:'Full settings',exact:true}).click();
 await expect(page.getByRole('textbox',{name:'Notes',exact:true})).toHaveText('Retest note');
 await page.getByRole('tab',{name:'Progress',exact:true}).click();
 await page.getByRole('button',{name:'Start',exact:true}).click();await expect(page.locator('.sqd-task-desc')).toContainText('complete',{timeout:15000});
 expect(requests.filter(url=>/executions|retest|optimiz|backtest/i.test(url))).toEqual([]);
});
test('Retester databank activation and visual states',async({page})=>{
 await page.goto('/retester');await page.getByRole('button',{name:'Expand databanks',exact:true}).click();
 await page.locator('.databanks-body').getByRole('button',{name:'Strategy Name',exact:true}).click();
 await page.locator('.databanks-body').getByText('Strategy 002',{exact:true}).dblclick();
 await expect(page.locator('.sqr-info-line')).toContainText('Strategy 002');
 await page.getByRole('tab',{name:'Progress',exact:true}).click();
 for(const [width,height] of [[1567,958],[1840,1000],[900,760]]){
  await page.setViewportSize({width,height});await page.screenshot({path:resolve(evidence,`retester-progress-${width}.png`)});
 }
 await page.getByRole('tab',{name:'Full settings',exact:true}).click();await page.screenshot({path:resolve(evidence,'retester-settings.png')});
});

test('configuration detail, routing labels, log download and reset',async({page})=>{
 await page.goto('/retester?tab=progress');await page.getByLabel('Target databank',{exact:true}).selectOption('Results');await expect(page.getByText(/Overwrite preview:/)).toBeVisible();
 await page.getByRole('button',{name:'Configure cross checks',exact:true}).click();await expect(page.getByRole('tab',{name:'Cross checks (robustness)',exact:true})).toHaveAttribute('aria-selected','true');await page.getByRole('tab',{name:'Progress',exact:true}).click();
 await page.getByRole('button',{name:'Config',exact:true}).click();await expect(page.getByRole('dialog')).toContainText('Local Retester preview');await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Start',exact:true}).click();await page.getByRole('button',{name:'Stop',exact:true}).click();
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Save log',exact:true}).click();expect((await download).suggestedFilename()).toBe('retester-preview.log');
 await page.getByRole('button',{name:'Clear log',exact:true}).click();await expect(page.locator('.sqd-log-scroll')).toHaveText('');
 await page.setViewportSize({width:900,height:760});await page.screenshot({path:resolve(evidence,'retester-narrow-collapsed.png')});
});
