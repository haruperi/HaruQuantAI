import {expect,test,type Page} from '@playwright/test';
import type {RemoteBasketRecord} from '../../workspaces/data_manager/plugins/Catalogs/StockGroups/stockGroupApiClient';
const initial:RemoteBasketRecord={id:'1',name:'[Tech]',description:'Technology',system:false,items:[{symbol:'OLD',date_from:'1950-01-01',date_to:'2000-01-01'}]};
async function launch(page:Page){
  const state={groups:[structuredClone(initial)],writes:[] as Array<{path:string;body:any}>,failRead:false,failSave:false,failMembers:false,failDelete:false,jobStatus:'RUNNING',gate:null as Promise<void>|null};
  await page.addInitScript(()=>{
    localStorage.setItem('sqx-stock-groups-v1',JSON.stringify({version:1,groups:[{id:'local',name:'[Browser only]',description:'',system:false,members:[]}],generated:[],job:null}));
    const original=window.fetch.bind(window);
    window.fetch=((input:RequestInfo|URL,init?:RequestInit)=>String(input).includes('/api/v1/events?')?Promise.resolve(new Response(new ReadableStream<Uint8Array>({start(){}}),{headers:{'Content-Type':'text/event-stream'}})):original(input,init)) as typeof fetch;
  });
  await page.route('**/api/v1/**',async route=>{
    const path=new URL(route.request().url()).pathname,method=route.request().method();let data:unknown=[];
    if(path.endsWith('/auth/login'))data={token:'basket-test',expires_at:'2099-01-01T00:00:00Z'};
    else if(path.endsWith('/settings'))data={revision:1,values:{}};
    else if(path.endsWith('/status'))data={cpu_count:4};
    else if(path==='/api/v1/home')data={recent_projects:[]};
    else if(path.endsWith('/data/workspace'))data={tabs:['data','symbols','sessions','brokers','custom-data','chart','home','stock-groups','log'].map((id,index)=>({id,title:id,core:index<5})),active_tab:'data',layout:{core_group:'catalogs',chart_position:'right'}};
    else if(path.includes('/workspace/tabs/'))data={active_tab:path.split('/').at(-1),selection:null,preview:{state:'unavailable',reason:'Select a saved dataset.',rows:[],limit:500}};
    else if(path==='/api/v1/data/baskets'&&method==='GET'){
      if(state.failRead){await route.fulfill({status:503,json:{status:'error',error:{code:'OFFLINE',message:'Stock group storage unavailable'}}});return;}
      data=state.groups;
    }else if(path==='/api/v1/data/baskets'&&method==='POST'){
      const body=route.request().postDataJSON();state.writes.push({path,body});await state.gate;
      if(state.failSave){await route.fulfill({status:503,json:{status:'error',error:{code:'FAILED',message:'Group not saved'}}});return;}
      const existing=state.groups.find(row=>row.id===body.id);
      const saved={...(existing??{id:String(state.groups.length+1),system:false,items:[]}),...body};
      state.groups=existing?state.groups.map(row=>row.id===saved.id?saved:row):[...state.groups,saved];data=saved;
    }else if(path==='/api/v1/data/baskets/edit'&&method==='POST'){
      const body=route.request().postDataJSON();state.writes.push({path,body});state.groups=state.groups.map(group=>body.ids.includes(group.id)?{...group,...body.updates}:group);data=state.groups.filter(group=>body.ids.includes(group.id));
    }else if(path==='/api/v1/data/baskets/save'&&method==='POST'){
      const body=route.request().postDataJSON();state.writes.push({path,body});const groups=state.groups.filter(group=>body.ids.includes(group.id));data={count:groups.length,content:JSON.stringify(groups.map(group=>({name:group.name,description:group.description,system:group.system,stocks:group.items.map(item=>({ticker:item.symbol,date_from:item.date_from??0,date_to:item.date_to??-1}))})))};
    }else if(path==='/api/v1/data/baskets/load'&&method==='POST'){
      const body=route.request().postDataJSON();state.writes.push({path,body});let groups:any[];
      try{groups=JSON.parse(body.content);if(!Array.isArray(groups))throw new Error();}catch{await route.fulfill({status:422,json:{status:'error',error:{code:'validation',message:'Invalid baskets JSON'}}});return;}
      if(state.failMembers||groups.some(group=>state.groups.some(saved=>saved.name===group.name))){await route.fulfill({status:409,json:{status:'error',error:{code:'conflict',message:'Groups not loaded; existing names or invalid memberships'}}});return;}
      state.groups.push(...groups.map((group,index)=>({id:String(state.groups.length+index+1),name:group.name,description:group.description??'',system:group.system??false,items:(group.stocks??[]).map((item:any)=>({symbol:item.ticker,date_from:item.date_from||null,date_to:item.date_to===-1?null:item.date_to??null}))})));data={loaded_count:groups.length};
    }else if(path==='/api/v1/data/baskets/update-data'&&method==='POST'){
      const body=route.request().postDataJSON();state.writes.push({path,body});state.jobStatus='RUNNING';data={job_id:'job-1',kind:'baskets.update_data',status:'RUNNING',progress:10};
    }else if(path.includes('/data/basket-jobs/')){
      if(method==='POST'){const action=path.split('/').at(-1);state.writes.push({path,body:{}});state.jobStatus=action==='pause'?'PAUSED':action==='stop'?'CANCELLED':'RUNNING';}
      if(state.jobStatus==='COMPLETED')state.groups=state.groups.map(group=>({...group,stocks_count:group.items.length,active_count:group.items.length,symbols_count:group.items.length,downloaded_count:group.items.length,ready:true}));
      data={job_id:'job-1',kind:'baskets.update_data',status:state.jobStatus,progress:state.jobStatus==='COMPLETED'?100:20,result:{updated_count:state.jobStatus==='COMPLETED'?1:0}};
    }else if(/\/baskets\/\d+\/stocks$/.test(path)&&method==='GET'){
      data=state.groups.find(group=>group.id===path.split('/').at(-2));
    }else if(/\/baskets\/\d+\/(import-stocks|export-stocks)$/.test(path)){
      const body=route.request().postDataJSON();state.writes.push({path,body});const group=state.groups.find(row=>row.id===path.split('/').at(-2))!;
      if(path.endsWith('export-stocks'))data={count:group.items.length,content:group.items.map(item=>`${item.symbol};${item.date_from??''};${item.date_to??''}`).join('\n')};
      else {group.items=body.content.split('\n').filter(Boolean).map((line:string)=>({symbol:line.split(';')[0],date_from:null,date_to:null}));data=group;}
    }else if(path==='/api/v1/data/baskets/delete'&&method==='POST'){
      const body=route.request().postDataJSON();state.writes.push({path,body});await state.gate;
      if(state.failDelete){await route.fulfill({status:503,json:{status:'error',error:{code:'FAILED',message:'Groups not removed'}}});return;}
      state.groups=state.groups.filter(group=>!body.ids.includes(group.id));data={deleted_ids:body.ids,deleted_count:body.ids.length};
    }else if(/\/baskets\/\d+\/stocks$/.test(path)&&method==='PUT'){
      const body=route.request().postDataJSON();state.writes.push({path,body});
      if(state.failMembers){await route.fulfill({status:503,json:{status:'error',error:{code:'FAILED',message:'Members not saved'}}});return;}
      const group=state.groups.find(row=>row.id===path.split('/').at(-2))!;
      group.items=body.symbols.map((line:string)=>{const [symbol,start,end]=line.split(';');return {symbol,date_from:start||null,date_to:end||null};});data=group;
    }
    await route.fulfill({json:{status:'success',data}});
  });
  await page.goto('/');
  const login=page.getByRole('dialog',{name:'Connect to HaruQuantAI host'});
  await login.getByLabel('Host password').fill('fixture-password');await login.getByRole('button',{name:'Connect',exact:true}).click();await expect(login).toHaveCount(0);
  await page.getByRole('button',{name:'Data Manager',exact:true}).click();await page.getByRole('button',{name:'Stock groups',exact:true}).click();
  await expect(table(page)).toContainText('[Tech]');return state;
}
const actions=(page:Page)=>page.getByLabel('Stock group operations',{exact:true});
const table=(page:Page)=>page.getByRole('table',{name:'Stock groups',exact:true});

test('creates confirmed groups, persists dated members and explicitly clears them',async({page})=>{
  const state=await launch(page);
  await expect(table(page)).not.toContainText('Browser only');
  await actions(page).getByRole('button',{name:'Add new',exact:true}).click();
  let dialog=page.getByRole('dialog',{name:'Add stocks group',exact:true});
  await dialog.getByLabel('Group name *').fill('Technology');await dialog.getByLabel('Description',{exact:true}).fill('Leaders');
  await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog).toHaveCount(0);
  await expect(table(page)).toContainText('Technology');expect(state.writes[0].body).toEqual({name:'Technology',description:'Leaders'});
  await actions(page).getByRole('button',{name:'Edit stocks',exact:true}).click();
  dialog=page.getByRole('dialog',{name:'Edit stocks Technology',exact:true});
  await dialog.getByRole('textbox',{name:'Stocks',exact:true}).fill('AAPL\nOLD;01.01.1950;01.01.2000\nOLD;01.01.2001\nUNTIL;;01.01.2020');
  await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog).toHaveCount(0);
  expect(state.groups[1].items).toHaveLength(4);expect(state.groups[1].items[1].date_from).toBe('1950-01-01');
  await page.reload();await page.getByRole('button',{name:'Stock groups',exact:true}).click();
  await page.getByRole('checkbox',{name:'Select stock group Technology',exact:true}).check();
  await actions(page).getByRole('button',{name:'Edit stocks',exact:true}).click();
  dialog=page.getByRole('dialog',{name:'Edit stocks Technology',exact:true});
  await expect(dialog.getByRole('textbox',{name:'Stocks',exact:true})).toContainText('OLD;01.01.1950;01.01.2000');
  await dialog.getByRole('textbox',{name:'Stocks',exact:true}).fill('');await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog).toHaveCount(0);
  expect(state.groups[1].items).toEqual([]);
  await expect(actions(page).getByRole('button',{name:'Mass delete',exact:true})).toBeEnabled();
  await expect(actions(page).getByRole('button',{name:'Update data in group (automatic)',exact:true})).toBeEnabled();
});

test('locks pending creation and retains forms and previous members on errors',async({page})=>{
  const state=await launch(page);state.failSave=true;
  let release!:()=>void;state.gate=new Promise<void>(resolve=>{release=resolve;});
  await actions(page).getByRole('button',{name:'Add new',exact:true}).click();
  let dialog=page.getByRole('dialog',{name:'Add stocks group',exact:true});await dialog.getByLabel('Group name *').fill('Failed');
  await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog.getByRole('button',{name:'Save',exact:true})).toBeDisabled();
  await page.keyboard.press('Escape');await expect(dialog).toBeVisible();release();
  await expect(dialog.getByRole('alert')).toContainText('Group not saved');await expect(table(page)).not.toContainText('[Failed]');
  await dialog.getByRole('button',{name:'Close',exact:true}).last().click();
  await page.getByRole('checkbox',{name:'Select stock group [Tech]',exact:true}).check();await actions(page).getByRole('button',{name:'Edit stocks',exact:true}).click();
  dialog=page.getByRole('dialog',{name:'Edit stocks [Tech]',exact:true});state.failMembers=true;
  await dialog.getByRole('textbox',{name:'Stocks',exact:true}).fill('NEW');await dialog.getByRole('button',{name:'Save',exact:true}).click();
  await expect(dialog.getByRole('alert')).toContainText('Members not saved');expect(state.groups[0].items[0].symbol).toBe('OLD');
  await dialog.getByRole('textbox',{name:'Stocks',exact:true}).fill('BAD;31.02.2020');const writes=state.writes.length;
  await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('Invalid membership date');expect(state.writes).toHaveLength(writes);
});

test('loads host system groups, rejects edits and retries failed and empty catalogs',async({page})=>{
  const state=await launch(page);state.groups[0]={...state.groups[0],name:'[[Tech]]',system:true};
  await page.reload();await page.getByRole('button',{name:'Stock groups',exact:true}).click();
  await page.getByRole('checkbox',{name:'Select stock group [[Tech]]',exact:true}).check();await actions(page).getByRole('button',{name:'Edit stocks',exact:true}).click();
  await expect(page.getByRole('dialog',{name:'Edit stocks [[Tech]]',exact:true})).toHaveCount(0);expect(state.writes).toEqual([]);
  state.failRead=true;await page.reload();await page.getByRole('button',{name:'Stock groups',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Stock group storage unavailable');state.failRead=false;state.groups=[];
  await page.getByRole('button',{name:'Retry stock groups',exact:true}).click();await expect(table(page)).not.toContainText('Tech');
});

test('loads JSON groups atomically and saves the selected group through the service',async({page})=>{
  const state=await launch(page);state.failMembers=true;
  await actions(page).getByRole('button',{name:'Load',exact:true}).click();const dialog=page.getByRole('dialog',{name:'Load groups',exact:true});
  const groups=[{name:'Imported',description:'Leaders',stocks:[{ticker:'AAPL',date_from:'2020-01-01',date_to:-1}]}];
  await dialog.getByLabel('Groups file').setInputFiles({name:'Groups.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(groups))});
  await dialog.getByRole('button',{name:'Load',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('Groups not loaded');
  expect(state.groups).toHaveLength(1);state.failMembers=false;
  await dialog.getByRole('button',{name:'Load',exact:true}).click();await expect(dialog).toHaveCount(0);await expect(table(page)).toContainText('Imported');
  await page.getByRole('checkbox',{name:'Select stock group Imported',exact:true}).check();
  const downloading=page.waitForEvent('download');await actions(page).getByRole('button',{name:'Save',exact:true}).click();expect((await downloading).suggestedFilename()).toBe('Groups.json');
  expect(state.writes.at(-1)?.path).toBe('/api/v1/data/baskets/save');
});

test('mass delete requires selection and confirmation and retains selection on rejection',async({page})=>{
  const state=await launch(page);const remove=actions(page).getByRole('button',{name:'Mass delete',exact:true});
  await remove.click();await expect(page.getByRole('dialog',{name:'Remove group',exact:true})).toHaveCount(0);expect(state.writes).toEqual([]);
  await page.getByRole('checkbox',{name:'Select stock group [Tech]',exact:true}).check();await remove.click();
  let dialog=page.getByRole('dialog',{name:'Remove group',exact:true});
  await expect(dialog).toContainText('full membership history');await dialog.getByRole('button',{name:'No',exact:true}).click();expect(state.writes).toEqual([]);
  state.failDelete=true;await remove.click();dialog=page.getByRole('dialog',{name:'Remove group',exact:true});
  await dialog.getByRole('button',{name:'Yes',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('Groups not removed');
  await expect(table(page)).toContainText('[Tech]');await expect(page.getByRole('checkbox',{name:'Select stock group [Tech]',exact:true})).toBeChecked();
  state.failDelete=false;await dialog.getByRole('button',{name:'Yes',exact:true}).click();await expect(dialog).toHaveCount(0);await expect(table(page)).not.toContainText('[Tech]');expect(state.groups).toEqual([]);
  await page.reload();await page.getByRole('button',{name:'Stock groups',exact:true}).click();await expect(table(page)).not.toContainText('[Tech]');
});

test('mass delete rejects mixed system and custom selection without writes',async({page})=>{
  const state=await launch(page);state.groups.push({...structuredClone(initial),id:'2',name:'[[System]]',system:true});
  await page.reload();await page.getByRole('button',{name:'Stock groups',exact:true}).click();
  await page.getByRole('checkbox',{name:'Select all stock groups',exact:true}).check();await actions(page).getByRole('button',{name:'Mass delete',exact:true}).click();
  await expect(page.getByText('System stock groups cannot be deleted.',{exact:true})).toBeVisible();
  await expect(page.getByRole('dialog',{name:'Remove groups',exact:true})).toHaveCount(0);expect(state.writes).toEqual([]);
});

test('mass delete sends one confirmed batch and locks controls while pending',async({page})=>{
  const state=await launch(page);state.groups.push({...structuredClone(initial),id:'2',name:'[Second]'});
  await page.reload();await page.getByRole('button',{name:'Stock groups',exact:true}).click();
  await page.getByRole('checkbox',{name:'Select all stock groups',exact:true}).check();await actions(page).getByRole('button',{name:'Mass delete',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Remove groups',exact:true});let release!:()=>void;state.gate=new Promise<void>(resolve=>{release=resolve;});
  await dialog.getByRole('button',{name:'Yes',exact:true}).click();await expect(dialog.getByRole('button',{name:'Yes',exact:true})).toBeDisabled();await expect(dialog.getByRole('button',{name:'No',exact:true})).toBeDisabled();
  await page.keyboard.press('Escape');await expect(dialog).toBeVisible();expect(state.writes).toHaveLength(1);expect([...state.writes[0].body.ids].sort()).toEqual(['1','2']);
  release();await expect(dialog).toHaveCount(0);await expect(table(page)).not.toContainText('[Tech]');await expect(table(page)).not.toContainText('[Second]');expect(state.groups).toEqual([]);
});


test('edits metadata and imports and exports stocks through backend operations',async({page})=>{
  const state=await launch(page);
  await page.getByRole('checkbox',{name:'Select stock group [Tech]',exact:true}).check();await actions(page).getByRole('button',{name:'Edit selected',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Edit stocks group',exact:true})).toBeVisible();
  let dialog=page.getByRole('dialog',{name:'Edit stocks group',exact:true});await dialog.getByLabel('Description',{exact:true}).fill('Updated metadata');await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog).toHaveCount(0);expect(state.groups[0].description).toBe('Updated metadata');
  await actions(page).getByRole('button',{name:'Edit stocks',exact:true}).click();dialog=page.getByRole('dialog',{name:'Edit stocks [Tech]',exact:true});
  await dialog.getByLabel('Choose stocks CSV').setInputFiles({name:'stocks.csv',mimeType:'text/csv',buffer:Buffer.from('AAPL\nMSFT')});await expect(dialog).toHaveCount(0);
  expect(state.writes.at(-1)?.path).toBe('/api/v1/data/baskets/1/import-stocks');
  await actions(page).getByRole('button',{name:'Edit stocks',exact:true}).click();dialog=page.getByRole('dialog',{name:'Edit stocks [Tech]',exact:true});
  const downloading=page.waitForEvent('download');await dialog.getByRole('button',{name:'Export to file',exact:true}).click();expect((await downloading).suggestedFilename()).toBe('Tech_stocks.csv');
  expect(state.writes.at(-1)?.path).toBe('/api/v1/data/baskets/1/export-stocks');
});

test('starts, pauses, resumes and completes an authoritative backend update job',async({page})=>{
  const state=await launch(page);
  await page.getByRole('checkbox',{name:'Select stock group [Tech]',exact:true}).check();
  await actions(page).getByRole('button',{name:'Update data in group (automatic)',exact:true}).click();
  await expect(page.getByRole('button',{name:'Pause all',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'Pause all',exact:true}).click();await expect(page.getByRole('button',{name:'Resume all',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'Resume all',exact:true}).click();
  expect(state.writes.some(write=>write.path.endsWith('/job-1/resume'))).toBe(true);
  state.jobStatus='COMPLETED';
  await expect(page.getByLabel('Data Manager progress',{exact:true})).toContainText('completed');
  await expect(table(page).getByRole('row').filter({has:page.getByRole('checkbox',{name:'Select stock group [Tech]',exact:true})})).toContainText('Yes');
});
