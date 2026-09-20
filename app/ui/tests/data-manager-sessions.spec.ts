import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';

async function launch(page:Page){await page.goto('/');await page.getByRole('button',{name:'Data Manager',exact:true}).click();await page.getByRole('button',{name:'Sessions',exact:true}).click();}
function sessionRow(page:Page,name:string){return page.getByRole('table',{name:'Sessions',exact:true}).getByRole('row').filter({has:page.getByRole('checkbox',{name:`Select session ${name}`,exact:true})});}

test('add, edit, clone, delete, and reload sessions',async({page})=>{
  await launch(page);const actions=page.getByLabel('Session operations');
  await actions.getByRole('button',{name:'Add Session',exact:true}).click();
  let dialog=page.getByRole('dialog',{name:'Add session template',exact:true});
  await dialog.getByLabel('Session name',{exact:true}).fill('TestSession');
  await dialog.getByRole('button',{name:'Add',exact:true}).click();
  let element=page.getByRole('dialog',{name:'Add session',exact:true});
  await element.getByRole('checkbox',{name:'Session End Means EOD'}).check();
  await element.getByRole('button',{name:'Save',exact:true}).click();
  await dialog.getByRole('button',{name:'Add Mon-Fri',exact:true}).click();
  await expect(dialog.getByRole('table',{name:'Session elements'}).getByRole('row')).toHaveCount(6);
  await page.screenshot({path:'test-results/sessions-add-dark.png'});
  await dialog.getByRole('button',{name:'Save',exact:true}).click();
  let row=sessionRow(page,'TestSession');await expect(row).toBeVisible();
  await row.dblclick();dialog=page.getByRole('dialog',{name:'Edit session template',exact:true});
  await expect(dialog.getByLabel('Session name',{exact:true})).toBeDisabled();
  await dialog.getByRole('table',{name:'Session elements'}).getByRole('row').nth(1).dblclick();
  element=page.getByRole('dialog',{name:'Edit session',exact:true});await element.getByLabel('Start time',{exact:true}).fill('01:00');await element.getByRole('button',{name:'Save',exact:true}).click();
  await dialog.getByRole('button',{name:'Save',exact:true}).click();
  row=sessionRow(page,'TestSession');await row.getByRole('checkbox').check();await actions.getByRole('button',{name:'Clone Session',exact:true}).click();
  dialog=page.getByRole('dialog',{name:"Clone session 'TestSession'",exact:true});await expect(dialog.getByLabel('New session name')).toHaveValue('TestSessionClone');await dialog.getByRole('button',{name:'Save',exact:true}).click();
  await expect(sessionRow(page,'TestSessionClone')).toBeVisible();await sessionRow(page,'TestSessionClone').getByRole('button',{name:'Delete session TestSessionClone'}).click();
  dialog=page.getByRole('dialog',{name:'Removing sessions',exact:true});await expect(dialog).toContainText('selected sessions (1)');await dialog.getByRole('button',{name:'Yes',exact:true}).click();
  await expect(sessionRow(page,'TestSessionClone')).toHaveCount(0);await page.reload();await page.getByRole('button',{name:'Sessions',exact:true}).click();await expect(sessionRow(page,'TestSession')).toBeVisible();
});

test('selection, JSON save/load conflicts, filters, and referenced deletion',async({page})=>{
  await launch(page);const actions=page.getByLabel('Session operations');
  await actions.getByRole('button',{name:'Clone Session',exact:true}).click();await expect(page.getByLabel('Data Manager progress')).toContainText('select some session');
  const row=sessionRow(page,'Forex 24/5');await row.getByRole('checkbox').check();await selectLightSkin(page);const downloadPromise=page.waitForEvent('download');await actions.getByRole('button',{name:'Save',exact:true}).click();
  let dialog=page.getByRole('dialog',{name:'Save sessions',exact:true});await page.screenshot({path:'test-results/sessions-save-light.png'});await dialog.getByRole('button',{name:'Download JSON',exact:true}).click();expect((await downloadPromise).suggestedFilename()).toBe('Sessions.json');
  await actions.getByRole('button',{name:'Load',exact:true}).click();dialog=page.getByRole('dialog',{name:'Load sessions',exact:true});const json=JSON.stringify({version:1,kind:'sessions',sessions:[{name:'Forex 24/5',broker:'-1',brokerName:'Default',elements:[{dayFrom:'Mon',dayTo:'Mon',timeFrom:'08:00',timeTo:'09:00',eod:true}]}]});
  await dialog.getByLabel('Sessions JSON file').setInputFiles({name:'Sessions.json',mimeType:'application/json',buffer:Buffer.from(json)});await dialog.getByRole('button',{name:'Validate and load',exact:true}).click();dialog=page.getByRole('dialog',{name:'Overwrite confirm',exact:true});await expect(dialog).toContainText("Session 'Forex 24/5' already exists");await dialog.getByRole('button',{name:'Overwrite',exact:true}).click();
  await page.getByLabel('Filter sessions').fill('Forex');await expect(sessionRow(page,'Forex 24/5')).toBeVisible();await page.getByLabel('Filter sessions').fill('');
  await row.getByRole('button',{name:'Delete session Forex 24/5'}).click();dialog=page.getByRole('dialog',{name:'Removing sessions',exact:true});await dialog.getByRole('button',{name:'Yes',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('used by an instrument');
});

test('corrupt persisted sessions fail closed',async({page})=>{await page.goto('/');await page.evaluate(()=>localStorage.setItem('haru-data-sessions-v1','{bad'));await page.reload();await page.getByRole('button',{name:'Data Manager',exact:true}).click();await page.getByRole('button',{name:'Sessions',exact:true}).click();await page.getByLabel('Session operations').getByRole('button',{name:'Add Session',exact:true}).click();await expect(page.getByRole('dialog',{name:'Add session template'}).getByRole('alert')).toContainText('could not be read');});
