import { normalizeSymbolContract } from '../../workspaces/data_manager/plugins/Common/symbolContract';
import {expect,test,type Page} from '@playwright/test';
import type {RemoteBrokerRecord} from '../../workspaces/data_manager/plugins/Catalogs/BrokerProfiles/brokerApiClient';

const initial:RemoteBrokerRecord={id:'1',name:'Demo',description:'Saved profile',timezone:'UTC',postfix:'_d',stockpicker_use:true,mt_use:true,is_system:false,stocks:['OLD'],customized_stocks:1,total_symbols:0,total_sessions:0,spread_model:{model:'inherit'},commission_model:{model:'inherit'}};
async function launch(page:Page){
  const state={profiles:[structuredClone(initial)],symbols:[] as any[],sessions:[] as any[],writes:[] as any[],failRead:false,failSave:false,failDelete:false,deleteGate:null as Promise<void>|null,partial:false};
  await page.addInitScript(()=>{
    const original=window.fetch.bind(window);
    window.fetch=((input:RequestInfo|URL,init?:RequestInit)=>String(input).includes('/api/v1/events?')?Promise.resolve(new Response(new ReadableStream<Uint8Array>({start(){}}),{headers:{'Content-Type':'text/event-stream'}})):original(input,init)) as typeof fetch;
  });
  await page.route('**/api/v1/**',async route=>{
    const path=new URL(route.request().url()).pathname,method=route.request().method();
    let data:unknown=[];
    if(path.endsWith('/auth/login'))data={token:'session-test',expires_at:'2099-01-01T00:00:00Z'};
    else if(path.endsWith('/settings'))data={revision:1,values:{}};
    else if(path.endsWith('/status'))data={cpu_count:4};
    else if(path==='/api/v1/home')data={recent_projects:[]};
    else if(path.endsWith('/data/workspace'))data={tabs:['data','symbols','sessions','brokers','custom-data','chart','home','stock-groups','log'].map((id,index)=>({id,title:id,core:index<5})),active_tab:'data',layout:{core_group:'catalogs',chart_position:'right'}};
    else if(path.includes('/workspace/tabs/'))data={active_tab:path.split('/').at(-1),selection:null,preview:{state:'unavailable',reason:'Select a saved dataset.',rows:[],limit:500}};
    else if(path==='/api/v1/data/symbols')data=state.symbols;
    else if(path==='/api/v1/data/sessions')data=state.sessions;
    else if(path==='/api/v1/data/brokers'&&method==='GET'){
      if(state.failRead){await route.fulfill({status:503,json:{status:'error',error:{code:'OFFLINE',message:'Broker storage unavailable'}}});return;}
      data=state.profiles;
    }else if(path==='/api/v1/data/brokers'&&method==='POST'){
      const body=normalizeSymbolContract(route.request().postDataJSON());state.writes.push({path,body});
      if(state.failSave){await route.fulfill({status:503,json:{status:'error',error:{code:'FAILED',message:'Broker not saved'}}});return;}
      const existing=state.profiles.find(row=>row.id===body.id);
      const saved={...(existing??{...initial,id:String(state.profiles.length+1),stocks:[],customized_stocks:0}),...body};
      if(existing)state.profiles=state.profiles.map(row=>row.id===saved.id?saved:row);else state.profiles.push(saved);
      data=saved;
    }else if(path==='/api/v1/data/brokers/edit'&&method==='POST'){
      const body=route.request().postDataJSON();state.writes.push({path,body});
      state.profiles=state.profiles.map(row=>body.ids.includes(row.id)?{...row,...body.updates}:row);
      data=state.profiles.filter(row=>body.ids.includes(row.id));
    }else if(path==='/api/v1/data/brokers/load'&&method==='POST'){
      const body=route.request().postDataJSON();state.writes.push({path,body});
      let records:any[];
      try{records=JSON.parse(body.content);if(!Array.isArray(records))throw new Error();}
      catch{await route.fulfill({status:422,json:{status:'error',error:{code:'validation',message:'Invalid brokers JSON'}}});return;}
      if(records.some(item=>state.profiles.some(row=>row.name===item.name))){await route.fulfill({status:409,json:{status:'error',error:{code:'conflict',message:'Broker already exists'}}});return;}
      state.profiles.push(...records.map((item,index)=>({...structuredClone(initial),...item,id:String(state.profiles.length+index+1),timezone:item.server_timezone??'UTC',stocks:[],customized_stocks:0})));
      data={loaded_count:records.length};
    }else if(path==='/api/v1/data/brokers/save'&&method==='POST'){
      const body=route.request().postDataJSON();state.writes.push({path,body});
      data={count:state.profiles.length,content:JSON.stringify(state.profiles.map(row=>({name:row.name,server_timezone:row.timezone})))};
    }else if(path==='/api/v1/data/brokers/delete'&&method==='POST'){
      const body=normalizeSymbolContract(route.request().postDataJSON());state.writes.push({path,body});
      await state.deleteGate;
      if(state.failDelete){await route.fulfill({status:422,json:{status:'error',error:{code:'IN_USE',message:'Broker is used by saved datasets.'}}});return;}
      state.profiles=state.profiles.filter(row=>!body.ids.includes(row.id));
      data={deleted_ids:body.ids,deleted_count:body.ids.length};
    }else if(/\/brokers\/\d+\/stocks$/.test(path)){
      const profile=state.profiles.find(row=>row.id===path.split('/').at(-2))!;
      if(method==='PUT'){
        const body=normalizeSymbolContract(route.request().postDataJSON());state.writes.push({path,body});
        profile.stocks=[...new Set<string>(body.stocks.map((s:string)=>s.trim()))];profile.customized_stocks=profile.stocks.length;
      }
      data={broker_id:profile.id,stocks:profile.stocks,count:profile.stocks.length};
    }else if(path.includes('/import-symbols')||path.includes('/import-sessions')){
      const body=normalizeSymbolContract(route.request().postDataJSON());state.writes.push({path,body});
      const kind=body.kind as 'symbols'|'sessions',field=kind==='symbols'?'symbol':'name';
      const brokerId=path.split('/').at(-2)!;
      const selected=body[kind].filter((row:any)=>body.options.selected_names.includes(row[field]));
      const failed=state.partial?selected.splice(1).map((row:any)=>({name:row[field]+body.options.postfix,reason:'Record validation failed.'})):[];
      const records=selected.map((source:any)=>{
        const saved={...source,id:String(state[kind].length+1),[field]:source[field]+body.options.postfix,broker_id:Number(brokerId)};
        if(kind==='symbols')Object.assign(saved,{contract_size:100000,pip_size:.0001,margin_rate:.05,decimals:5,tick_value_in_money:10,min_volume:.01,max_volume:100,lot_step:.01,swap_long:0,swap_short:0,swap_3day_day:3});
        state[kind].push(saved);return saved;
      });
      const profile=state.profiles.find(row=>row.id===brokerId);
      if(profile){profile.total_symbols=state.symbols.length;profile.total_sessions=state.sessions.length;}
      data={broker_id:brokerId,imported_count:records.length,created_count:records.length,updated_count:0,records,failed,unattempted:[]};
    }
    await route.fulfill({json:{status:'success',data}});
  });
  await page.goto('/');
  const login=page.getByRole('dialog',{name:'Connect to HaruQuantAI host'});
  await login.getByLabel('Host password').fill('fixture-password');await login.getByRole('button',{name:'Connect',exact:true}).click();await expect(login).toHaveCount(0);
  await page.getByRole('button',{name:'Data Manager',exact:true}).click();
  await page.getByRole('button',{name:'Broker profiles',exact:true}).click();
  await expect(page.getByRole('table',{name:'Broker profiles',exact:true})).toContainText('Demo');
  return state;
}
const actions=(page:Page)=>page.getByLabel('Broker profile operations',{exact:true});
const table=(page:Page)=>page.getByRole('table',{name:'Broker profiles',exact:true});
test('saves broker fields, reloads confirmed profiles and replaces stocks with empty',async({page})=>{
  const state=await launch(page);
  await actions(page).getByRole('button',{name:'Add new',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Add Broker profile',exact:true});
  await dialog.getByLabel('Broker profile name').fill('New');await dialog.getByLabel('Broker enabled').uncheck();
  await dialog.getByLabel('Clock policy JSON').fill('{"offset":120}');await dialog.getByLabel('Clock policy revision').fill('2');
  await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog).toHaveCount(0);await expect(table(page)).toContainText('New');
  expect(state.writes[0].body).toMatchObject({enabled:false,clock_policy:{offset:120},clock_policy_revision:2});
  await page.reload();await page.getByRole('button',{name:'Broker profiles',exact:true}).click();await expect(table(page)).toContainText('New');
  await page.getByRole('checkbox',{name:'Select broker Demo',exact:true}).check();await actions(page).getByRole('button',{name:'Edit stocks',exact:true}).click();
  const stocks=page.getByRole('dialog',{name:'Edit stocks Demo',exact:true});await expect(stocks.getByRole('textbox',{name:'Broker stocks',exact:true})).toHaveValue('OLD');
  await stocks.getByRole('textbox',{name:'Broker stocks',exact:true}).fill('');await stocks.getByRole('button',{name:'Save',exact:true}).click();await expect(stocks).toHaveCount(0);expect(state.profiles[0].stocks).toEqual([]);
  await expect(actions(page).getByRole('button',{name:'Mass delete',exact:true})).toBeEnabled();
  await expect(actions(page).getByRole('button',{name:'Update data for broker (automatic)',exact:true})).toHaveCount(0);
  await expect(actions(page).getByRole('button',{name:'Refresh',exact:true})).toHaveCount(0);
});

test('edits multiple selected brokers atomically through one request',async({page})=>{
  const state=await launch(page);
  state.profiles.push({...structuredClone(initial),id:'2',name:'Second'});
  await page.reload();await page.getByRole('button',{name:'Broker profiles',exact:true}).click();
  await expect(table(page)).toContainText('Second');
  await page.getByLabel('Select all broker profiles',{exact:true}).check();
  await actions(page).getByRole('button',{name:'Edit selected',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Edit selected brokers',exact:true});
  await dialog.getByLabel('Broker field',{exact:true}).selectOption('postfix');
  await dialog.getByLabel('Broker field value',{exact:true}).fill('_bulk');
  await dialog.getByRole('button',{name:'Save',exact:true}).click();
  await expect(dialog).toHaveCount(0);
  expect(state.profiles.every(row=>row.postfix==='_bulk')).toBe(true);
  expect(state.writes).toHaveLength(1);
});

test('rejects invalid JSON and duplicate names without overwriting brokers',async({page})=>{
  const state=await launch(page);
  await actions(page).getByRole('button',{name:'Load',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Load brokers',exact:true});
  await dialog.getByLabel('Brokers file',{exact:true}).setInputFiles({name:'Invalid.json',mimeType:'application/json',buffer:Buffer.from('{bad')});
  await dialog.getByRole('button',{name:'Validate and load',exact:true}).click();
  await expect(dialog.getByRole('alert')).toContainText('Invalid brokers JSON');
  await dialog.getByLabel('Brokers file',{exact:true}).setInputFiles({name:'Duplicate.json',mimeType:'application/json',buffer:Buffer.from('[{"name":"Demo"}]')});
  await dialog.getByRole('button',{name:'Validate and load',exact:true}).click();
  await expect(dialog.getByRole('alert')).toContainText('already exists');
  expect(state.profiles).toHaveLength(1);
  expect(state.profiles[0].description).toBe('Saved profile');
});

test('shows backend save and listing failures without local success',async({page})=>{
  const state=await launch(page);state.failSave=true;
  await actions(page).getByRole('button',{name:'Add new',exact:true}).click();const dialog=page.getByRole('dialog',{name:'Add Broker profile',exact:true});await dialog.getByLabel('Broker profile name').fill('Unsaved');await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('Broker not saved');await expect(table(page)).not.toContainText('Unsaved');
  await dialog.getByLabel('Close',{exact:true}).click();state.failRead=true;await page.reload();await page.getByRole('button',{name:'Broker profiles',exact:true}).click();await expect(page.getByRole('alert')).toContainText('Broker storage unavailable');await expect(table(page)).not.toContainText('Demo');await expect(table(page)).not.toContainText('No brokers are defined.');state.failRead=false;await page.getByRole('button',{name:'Retry broker profiles',exact:true}).click();await expect(table(page)).toContainText('Demo');
});
test('loads canonical broker JSON and downloads the authoritative catalog',async({page})=>{
  const state=await launch(page);
  await actions(page).getByRole('button',{name:'Load',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Load brokers',exact:true});
  const payload=[{name:'Imported',description:'From CLI',server_timezone:'UTC',enabled:false,clock_policy:{offset:60}}];
  await dialog.getByLabel('Brokers file',{exact:true}).setInputFiles({name:'Brokers.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(payload))});
  await dialog.getByRole('button',{name:'Validate and load',exact:true}).click();
  await expect(dialog).toHaveCount(0);await expect(table(page)).toContainText('Imported');
  const download=page.waitForEvent('download');
  await actions(page).getByRole('button',{name:'Save',exact:true}).click();
  expect((await download).suggestedFilename()).toBe('Brokers.json');
  expect(state.writes.at(-1).path).toBe('/api/v1/data/brokers/save');
});

test('lists existing system profiles with EETUS after a retry and reload',async({page})=>{
  const state=await launch(page);
  state.profiles.push({...structuredClone(initial),id:'2',name:'[[Darwinex]]',is_system:true,timezone:'EETUS',stocks:[],customized_stocks:0});
  await page.reload();await page.getByRole('button',{name:'Broker profiles',exact:true}).click();
  let row=table(page).getByRole('row').filter({has:page.getByRole('checkbox',{name:'Select broker [[Darwinex]]',exact:true})});
  await expect(row).toContainText('EETUS');await expect(table(page)).toContainText('Demo');
  await page.reload();await page.getByRole('button',{name:'Broker profiles',exact:true}).click();
  row=table(page).getByRole('row').filter({has:page.getByRole('checkbox',{name:'Select broker [[Darwinex]]',exact:true})});await expect(row).toContainText('EETUS');
});


test('mass delete requires selection and confirmation and retains rows on rejection',async({page})=>{
  const state=await launch(page);
  const remove=actions(page).getByRole('button',{name:'Mass delete',exact:true});
  await remove.click();await expect(page.getByRole('dialog',{name:'Remove broker',exact:true})).toHaveCount(0);
  expect(state.writes).toHaveLength(0);
  await page.getByRole('checkbox',{name:'Select broker Demo',exact:true}).check();
  await remove.click();let dialog=page.getByRole('dialog',{name:'Remove broker',exact:true});
  await dialog.getByRole('button',{name:'No',exact:true}).click();expect(state.writes).toHaveLength(0);
  state.failDelete=true;
  await remove.click();dialog=page.getByRole('dialog',{name:'Remove broker',exact:true});
  await dialog.getByRole('button',{name:'Yes',exact:true}).click();
  await expect(dialog.getByRole('alert')).toContainText('saved datasets');
  await expect(table(page)).toContainText('Demo');
  await expect(page.getByRole('checkbox',{name:'Select broker Demo',exact:true})).toBeChecked();
  state.failDelete=false;await dialog.getByRole('button',{name:'Yes',exact:true}).click();
  await expect(dialog).toHaveCount(0);await expect(table(page)).not.toContainText('Demo');
  expect(state.profiles).toEqual([]);
  await page.reload();await page.getByRole('button',{name:'Broker profiles',exact:true}).click();
  await expect(table(page)).not.toContainText('Demo');
});

test('edits database fields and deletes a system broker through the service',async({page})=>{
  const state=await launch(page);state.profiles[0].is_system=true;
  await page.reload();await page.getByRole('button',{name:'Broker profiles',exact:true}).click();
  await page.getByRole('checkbox',{name:'Select broker Demo',exact:true}).check();
  await actions(page).getByRole('button',{name:'Edit selected',exact:true}).click();
  const editor=page.getByRole('dialog',{name:'Edit Broker profile',exact:true});
  await expect(editor.getByLabel('Broker ID',{exact:true})).toHaveValue('1');
  await expect(editor.getByLabel('System broker profile',{exact:true})).toBeChecked();
  await editor.getByLabel('Broker description',{exact:true}).fill('Updated system profile');
  await editor.getByRole('button',{name:'Save',exact:true}).click();
  await expect(editor).toHaveCount(0);
  expect(state.profiles[0].description).toBe('Updated system profile');
  expect(state.writes[0].body).toMatchObject({id:'1',is_system:true,description:'Updated system profile'});
  await actions(page).getByRole('button',{name:'Mass delete',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Remove broker',exact:true});
  await dialog.getByRole('button',{name:'Yes',exact:true}).click();
  await expect(dialog).toHaveCount(0);expect(state.profiles).toEqual([]);
});


test('mass delete sends one batch and keeps confirmation locked while pending',async({page})=>{
  const state=await launch(page);
  state.profiles.push({...structuredClone(initial),id:'2',name:'Second'});
  await page.reload();await page.getByRole('button',{name:'Broker profiles',exact:true}).click();
  await page.getByRole('checkbox',{name:'Select all broker profiles',exact:true}).check();
  await actions(page).getByRole('button',{name:'Mass delete',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Remove brokers',exact:true});
  let release!:()=>void;state.deleteGate=new Promise<void>(resolve=>{release=resolve;});
  await dialog.getByRole('button',{name:'Yes',exact:true}).click();
  await expect(dialog.getByRole('button',{name:'Yes',exact:true})).toBeDisabled();
  await expect(dialog.getByRole('button',{name:'No',exact:true})).toBeDisabled();
  await page.keyboard.press('Escape');await expect(dialog).toBeVisible();
  expect(state.writes).toHaveLength(1);expect(state.writes[0].body).toEqual({ids:['1','2']});
  release();await expect(dialog).toHaveCount(0);await expect(table(page)).not.toContainText('Demo');
  await expect(table(page)).not.toContainText('Second');expect(state.profiles).toEqual([]);
});
