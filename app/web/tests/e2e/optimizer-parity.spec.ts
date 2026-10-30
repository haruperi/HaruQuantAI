import {test,expect} from './frontendStructureFixtures';
import {resolve} from 'node:path';
const evidence=resolve(process.cwd(),'../../.agents/logs/2026-09-25T160123_retester-optimizer-ui-plan/verification');
test('Optimizer modes, parameter presets, file selection and result contributions',async({page})=>{
 await page.goto('/optimizer?tab=settings');
 await expect(page.getByRole('tab',{name:'Cross checks (robustness)',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Automatic ranges',exact:true}).click();await page.getByLabel('Range percent',{exact:true}).fill('50');await page.getByRole('button',{name:'Cancel',exact:true}).click();
 await expect(page.getByLabel('FastPeriod min',{exact:true})).toHaveValue('8');
 await page.getByRole('button',{name:'Automatic ranges',exact:true}).click();await page.getByLabel('Range percent',{exact:true}).fill('50');await page.getByRole('button',{name:'Apply',exact:true}).click();await expect(page.getByLabel('FastPeriod min',{exact:true})).toHaveValue('6');
 await page.getByLabel('Sequential optimization',{exact:true}).check();await expect(page.getByLabel('% to pass',{exact:true})).toBeVisible();
 await page.getByRole('tab',{name:'Results',exact:true}).click();await page.getByRole('tab',{name:'Sequential Optimization Results',exact:true}).click();await page.getByRole('button',{name:'Apply optimized values into strategy',exact:true}).click();await expect(page.getByText(/Local preview value:/)).toBeVisible();
 await page.getByRole('tab',{name:'Full settings',exact:true}).click();await page.getByLabel('Walk - Forward optimization',{exact:true}).check();await page.getByLabel('Walk-Forward type',{exact:true}).selectOption('Anchored');
 await page.getByLabel('Walk - Forward matrix',{exact:true}).check();await expect(page.getByLabel('OOS start',{exact:true})).toBeVisible();
 await page.getByRole('tab',{name:'Results',exact:true}).click();await page.getByRole('tab',{name:'Walk-Forward matrix',exact:true}).click();await page.getByRole('button',{name:'5 runs 30 percent',exact:true}).click();await expect(page.getByText('Selected: 5 runs / 30% OOS · Mock score 88%',{exact:true})).toBeVisible();await page.screenshot({path:resolve(evidence,'optimizer-matrix.png')});
 await page.getByRole('tab',{name:'Full settings',exact:true}).click();await page.getByLabel('Strategy from file',{exact:true}).check();
 await expect(page.getByRole('alert').filter({hasText:'Choose a strategy file for the local preview.'})).toBeVisible();
 await page.getByLabel('Strategy file',{exact:true}).setInputFiles({name:'fixture.sqx',mimeType:'application/octet-stream',buffer:Buffer.from('mock')});
 await expect(page.getByText('fixture.sqx',{exact:true})).toBeVisible();
 await page.setViewportSize({width:1840,height:1000});await page.screenshot({path:resolve(evidence,'optimizer-settings.png')});
});
test('Optimizer invalid ranges, mock run, cancellation and shared settings isolation',async({page})=>{
 const posts:string[]=[];page.on('request',r=>{if(r.method()==='POST')posts.push(r.url());});
 await page.goto('/optimizer?tab=settings');await page.getByLabel('FastPeriod step',{exact:true}).fill('0');
 await page.getByRole('tab',{name:'Progress',exact:true}).click();await expect(page.getByRole('button',{name:'Start',exact:true})).toBeDisabled();
 await page.getByRole('tab',{name:'Full settings',exact:true}).click();await page.getByLabel('FastPeriod step',{exact:true}).fill('2');
 await page.getByRole('tab',{name:'Notes',exact:true}).click();await expect(page.getByRole('textbox',{name:'Notes',exact:true})).toHaveText('');
 await page.getByRole('tab',{name:'Progress',exact:true}).click();await page.getByRole('button',{name:'Start',exact:true}).click();await page.getByRole('button',{name:'Pause',exact:true}).click();await page.getByRole('button',{name:'Resume',exact:true}).click();await page.getByRole('button',{name:'Stop',exact:true}).click();
 await expect(page.locator('.sqd-task-desc')).toContainText('idle');expect(posts.filter(url=>/executions|retest|optimiz|backtest/i.test(url))).toEqual([]);
 await page.setViewportSize({width:1567,height:958});await page.screenshot({path:resolve(evidence,'optimizer-progress.png')});
 await page.evaluate(()=>document.documentElement.dataset.theme='light');await page.screenshot({path:resolve(evidence,'optimizer-light.png')});
 await page.evaluate(()=>document.body.style.zoom='0.8');await page.screenshot({path:resolve(evidence,'optimizer-zoom.png')});
});

test('workspace notes are isolated and Optimizer databank activation opens Results',async({page})=>{
 await page.goto('/retester?tab=settings');await page.getByRole('tab',{name:'Notes',exact:true}).click();await page.getByRole('textbox',{name:'Notes',exact:true}).fill('Retester private note');
 await page.getByRole('complementary',{name:'Applications'}).getByRole('button',{name:'Optimizer',exact:true}).click();await expect(page.getByRole('tablist',{name:'Optimizer panels'})).toBeVisible();await expect(page).toHaveURL(/optimizer/);
 await page.getByRole('tab',{name:'Full settings',exact:true}).click();await page.getByRole('tab',{name:'Notes',exact:true}).click();await expect(page.getByRole('textbox',{name:'Notes',exact:true})).toHaveText('');
 await page.getByRole('button',{name:'Expand databanks',exact:true}).click();await page.locator('.databanks-body').getByRole('button',{name:'Strategy Name',exact:true}).click();await page.locator('.databanks-body').getByText('Strategy 002',{exact:true}).dblclick();
 await expect(page.getByRole('tablist',{name:'Optimizer panels'}).getByRole('tab',{name:'Results',exact:true})).toHaveAttribute('aria-selected','true');
 await expect(page).toHaveURL(/tab=results/);await expect(page.locator('.sqr-info-line')).toContainText('Strategy 002');
});
