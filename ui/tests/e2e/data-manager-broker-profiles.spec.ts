import {expect,test,type Page} from '@playwright/test';
import {newInstrument} from '../../app/plugins/data_source/FileImport/fileSymbols';
import type {RemoteBrokerRecord} from '../../app/plugins/data_source/Catalogs/BrokerProfiles/brokerApiClient';

const initial:RemoteBrokerRecord={id:'1',name:'Demo',description:'Saved profile',timezone:'UTC',postfix:'_d',stockpicker_use:true,mt_use:true,is_system:false,stocks:['OLD'],customized_stocks:1,total_instruments:0,total_sessions:0,spread_model:{model:'inherit'},commission_model:{model:'inherit'}};
async function launch(page:Page){
  const state={profiles:[structuredClone(initial)],instruments:[] as any[],sessions:[] as any[],writes:[] as any[],failRead:false,failSave:false,failDelete:false,deleteGate:null as Promise<void>|null,partial:false};
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
    else if(path.endsWith('/data/workspace'))data={tabs:['data','instruments','sessions','brokers','custom-data','chart','home','stock-groups','log'].map((id,index)=>({id,title:id,core:index<5})),active_tab:'data',layout:{core_group:'catalogs',chart_position:'right'}};
    else if(path.includes('/workspace/tabs/'))data={active_tab:path.split('/').at(-1),selection:null,preview:{state:'unavailable',reason:'Select a saved dataset.',rows:[],limit:500}};
    else if(path==='/api/v1/data/instruments')data=state.instruments;
    else if(path==='/api/v1/data/sessions')data=state.sessions;
    else if(path==='/api/v1/data/brokers'&&method==='GET'){
      if(state.failRead){await route.fulfill({status:503,json:{status:'error',error:{code:'OFFLINE',message:'Broker storage unavailable'}}});return;}
      data=state.profiles;
    }else if(path==='/api/v1/data/brokers'&&method==='POST'){
      const body=route.request().postDataJSON();state.writes.push({path,body});
      if(state.failSave){await route.fulfill({status:503,json:{status:'error',error:{code:'FAILED',message:'Broker not saved'}}});return;}
      const existing=state.profiles.find(row=>row.id===body.id);
      const saved={...(existing??{...initial,id:String(state.profiles.length+1),stocks:[],customized_stocks:0}),...body};
      if(existing)state.profiles=state.profiles.map(row=>row.id===saved.id?saved:row);else state.profiles.push(saved);
      data=saved;
    }else if(path==='/api/v1/data/brokers/delete'&&method==='POST'){
      const body=route.request().postDataJSON();state.writes.push({path,body});
      await state.deleteGate;
      if(state.failDelete){await route.fulfill({status:422,json:{status:'error',error:{code:'IN_USE',message:'Broker is used by saved datasets.'}}});return;}
      state.profiles=state.profiles.filter(row=>!body.ids.includes(row.id));
      data={deleted_ids:body.ids,deleted_count:body.ids.length};
    }else if(/\/brokers\/\d+\/stocks$/.test(path)){
      const profile=state.profiles.find(row=>row.id===path.split('/').at(-2))!;
      if(method==='PUT'){
        const body=route.request().postDataJSON();state.writes.push({path,body});
        profile.stocks=[...new Set<string>(body.stocks.map((s:string)=>s.trim()))];profile.customized_stocks=profile.stocks.length;
      }
      data={broker_id:profile.id,stocks:profile.stocks,count:profile.stocks.length};
    }else if(path.includes('/import-instruments')||path.includes('/import-sessions')){
      const body=route.request().postDataJSON();state.writes.push({path,body});
      const kind=body.kind as 'instruments'|'sessions',field=kind==='instruments'?'symbol':'name';
      const brokerId=path.split('/').at(-2)!;
      const selected=body[kind].filter((row:any)=>body.options.selected_names.includes(row[field]));
      const failed=state.partial?selected.splice(1).map((row:any)=>({name:row[field]+body.options.postfix,reason:'Record validation failed.'})):[];
      const records=selected.map((source:any)=>{
        const saved={...source,id:String(state[kind].length+1),[field]:source[field]+body.options.postfix,broker_id:Number(brokerId)};
        if(kind==='instruments')Object.assign(saved,{contract_size:100000,pip_size:.0001,margin_rate:.05,decimals:5,tick_value_in_money:10,min_volume:.01,max_volume:100,lot_step:.01,swap_long:0,swap_short:0,swap_3day_day:3});
        state[kind].push(saved);return saved;
      });
      const profile=state.profiles.find(row=>row.id===brokerId);
      if(profile){profile.total_instruments=state.instruments.length;profile.total_sessions=state.sessions.length;}
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
async function browse(page:Page,kind:'instrument'|'session',records:unknown[]){
  await actions(page).getByRole('button',{name:`Import broker ${kind==='instrument'?'instruments':'sessions'} from JSON`,exact:true}).click();
  const dialog=page.getByRole('dialog',{name:kind==='instrument'?'Instruments import from JSON':'Session import from JSON',exact:true});
  const plural=kind==='instrument'?'instruments':'sessions';
  await dialog.getByLabel(`${kind} JSON file`).setInputFiles({name:'Catalog.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({version:1,kind:plural,[plural]:records,...(kind==='instrument'?{brokers:[]}:{} )}))});
  await dialog.getByLabel('Import broker profile').selectOption('1');
  return dialog;
}

test('saves configured costs, reloads confirmed profiles and replaces stocks with empty',async({page})=>{
  const state=await launch(page);
  await actions(page).getByRole('button',{name:'Add new',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Add Broker profile',exact:true});
  await dialog.getByLabel('Broker profile name').fill('New');await dialog.getByLabel('Broker spread model').selectOption('fixed');
  await dialog.getByLabel('Broker spread value').fill('0');await dialog.getByLabel('Broker commission model').selectOption('Per trade');await dialog.getByLabel('Broker commission value').fill('3.5');
  await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog).toHaveCount(0);await expect(table(page)).toContainText('New');
  expect(state.writes[0].body.spread_model).toEqual({model:'fixed',value:0});expect(state.writes[0].body.commission_model.value).toBe(3.5);
  await page.reload();await page.getByRole('button',{name:'Broker profiles',exact:true}).click();await expect(table(page)).toContainText('New');
  await page.getByRole('checkbox',{name:'Select broker Demo',exact:true}).check();await actions(page).getByRole('button',{name:'Edit stocks',exact:true}).click();
  const stocks=page.getByRole('dialog',{name:'Edit stocks Demo',exact:true});await expect(stocks.getByRole('textbox',{name:'Broker stocks',exact:true})).toHaveValue('OLD');
  await stocks.getByRole('textbox',{name:'Broker stocks',exact:true}).fill('');await stocks.getByRole('button',{name:'Save',exact:true}).click();await expect(stocks).toHaveCount(0);expect(state.profiles[0].stocks).toEqual([]);
  await expect(actions(page).getByRole('button',{name:'Mass delete',exact:true})).toBeEnabled();
  await expect(actions(page).getByRole('button',{name:'Update data for broker (automatic)',exact:true})).toBeDisabled();
});

test('imports only selected instruments and sessions and refreshes saved counts',async({page})=>{
  const state=await launch(page);
  let dialog=await browse(page,'instrument',[{...newInstrument(),symbol:'ONE',name:'First'},{...newInstrument(),symbol:'TWO',name:'Second'}]);
  await dialog.getByLabel('Select ONE',{exact:true}).check();await dialog.getByLabel('Use broker cost defaults').check();await dialog.getByRole('button',{name:'Start Import',exact:true}).click();await expect(dialog).toHaveCount(0);
  expect(state.instruments.map(row=>row.symbol)).toEqual(['ONE_d']);expect(state.writes[0].body.options.use_profile_costs).toBe(true);
  dialog=await browse(page,'session',[{name:'Week',broker:'-1',brokerName:'Default',elements:[{dayFrom:'Mon',timeFrom:'09:00',dayTo:'Mon',timeTo:'16:00',eod:true}],holidays:[{date_str:'2026-12-25',description:'Holiday'}]}]);
  await dialog.getByLabel('Select Week',{exact:true}).check();await dialog.getByRole('button',{name:'Start Import',exact:true}).click();await expect(dialog).toHaveCount(0);
  expect(state.sessions[0].name).toBe('Week_d');expect(state.sessions[0].holidays).toHaveLength(1);
  const row=table(page).getByRole('row').filter({has:page.getByRole('checkbox',{name:'Select broker Demo',exact:true})});await expect(row).toContainText('Demo');expect(state.profiles[0].total_sessions).toBe(1);
});

test('keeps partial import results visible and clears stale previews for invalid files',async({page})=>{
  const state=await launch(page);state.partial=true;
  const dialog=await browse(page,'instrument',[{...newInstrument(),symbol:'GOOD',name:'Good'},{...newInstrument(),symbol:'BAD',name:'Bad'}]);
  await dialog.getByLabel('Select all import records').check();await dialog.getByRole('button',{name:'Start Import',exact:true}).click();
  await expect(dialog.getByRole('status')).toContainText('1 saved; 1 failed');await expect(dialog.getByLabel('Select GOOD',{exact:true})).not.toBeChecked();await expect(dialog.getByLabel('Select BAD',{exact:true})).toBeChecked();
  await dialog.getByLabel('instrument JSON file').setInputFiles({name:'Invalid.json',mimeType:'application/json',buffer:Buffer.from('{bad')});
  await expect(dialog.getByLabel('Select GOOD',{exact:true})).toHaveCount(0);await expect(dialog.getByRole('button',{name:'Start Import',exact:true})).toBeDisabled();await expect(dialog.getByRole('alert')).toBeVisible();
});

test('shows backend save and listing failures without local success',async({page})=>{
  const state=await launch(page);state.failSave=true;
  await actions(page).getByRole('button',{name:'Add new',exact:true}).click();const dialog=page.getByRole('dialog',{name:'Add Broker profile',exact:true});await dialog.getByLabel('Broker profile name').fill('Unsaved');await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('Broker not saved');await expect(table(page)).not.toContainText('Unsaved');
  await dialog.getByLabel('Close',{exact:true}).click();state.failRead=true;await page.reload();await page.getByRole('button',{name:'Broker profiles',exact:true}).click();await expect(page.getByRole('alert')).toContainText('Broker storage unavailable');await expect(table(page)).not.toContainText('Demo');await expect(table(page)).not.toContainText('No brokers are defined.');state.failRead=false;await page.getByRole('button',{name:'Retry broker profiles',exact:true}).click();await expect(table(page)).toContainText('Demo');
});
test('loads broker JSON with cost defaults and explicitly overwrites a profile',async({page})=>{
  const state=await launch(page);
  await actions(page).getByRole('button',{name:'Load',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Load brokers',exact:true});
  const payload={version:1,kind:'brokers',brokers:[{name:'Demo',desc:'Imported defaults',postfix:'_new',timezone:'UTC',mtUse:true,stockPickerUse:true,stocks:[],spreadModel:{model:'fixed',value:0},commissionModel:{model:'Per trade',value:3.5,unit:'share',min:0,minUnit:'money',max:0,maxUnit:'money'}}]};
  await dialog.getByLabel('Brokers file',{exact:true}).setInputFiles({name:'Brokers.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(payload))});
  await dialog.getByRole('button',{name:'Validate and load',exact:true}).click();
  const confirm=page.getByRole('dialog',{name:'Overwrite confirm',exact:true});await expect(confirm).toContainText('Demo');await confirm.getByRole('button',{name:'Overwrite',exact:true}).click();await expect(confirm).toHaveCount(0);
  expect(state.profiles[0].spread_model).toEqual({model:'fixed',value:0});expect(state.profiles[0].stocks).toEqual([]);
  const brokerRow=table(page).getByRole('row').filter({has:page.getByRole('checkbox',{name:'Select broker Demo',exact:true})});await expect(brokerRow).toContainText('Imported defaults');await brokerRow.dblclick();
  const editor=page.getByRole('dialog',{name:'Edit Broker profile',exact:true});await expect(editor.getByLabel('Broker commission model')).toHaveValue('Per trade');await expect(editor.getByLabel('Broker commission value')).toHaveValue('3.5');
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

test('mass delete rejects protected selections without issuing writes',async({page})=>{
  const state=await launch(page);state.profiles[0].is_system=true;
  await page.reload();await page.getByRole('button',{name:'Broker profiles',exact:true}).click();
  await page.getByRole('checkbox',{name:'Select broker Demo',exact:true}).check();
  await actions(page).getByRole('button',{name:'Mass delete',exact:true}).click();
  await expect(page.getByRole('dialog',{name:'Remove broker',exact:true})).toHaveCount(0);
  await expect(page.getByText('System broker profiles cannot be deleted.',{exact:true})).toBeVisible();
  expect(state.writes).toHaveLength(0);
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
