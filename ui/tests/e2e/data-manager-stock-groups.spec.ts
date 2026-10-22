import {expect,test,type Page} from '@playwright/test';
import type {RemoteBasketRecord} from '../../app/plugins/data_source/Catalogs/StockGroups/stockGroupApiClient';
const initial:RemoteBasketRecord={id:'1',name:'[Tech]',description:'Technology',system:false,items:[{symbol:'OLD',date_from:'1950-01-01',date_to:'2000-01-01'}]};
async function launch(page:Page){
  const state={groups:[structuredClone(initial)],writes:[] as Array<{path:string;body:any}>,failRead:false,failSave:false,failMembers:false,failDelete:false,gate:null as Promise<void>|null};
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
    else if(path.endsWith('/data/workspace'))data={tabs:['data','instruments','sessions','brokers','custom-data','chart','home','stock-groups','log'].map((id,index)=>({id,title:id,core:index<5})),active_tab:'data',layout:{core_group:'catalogs',chart_position:'right'}};
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
  await expect(table(page)).toContainText('[Technology]');expect(state.writes[0].body).toEqual({name:'[Technology]',description:'Leaders'});
  await actions(page).getByRole('button',{name:'Edit stocks',exact:true}).click();
  dialog=page.getByRole('dialog',{name:'Edit stocks [Technology]',exact:true});
  await dialog.getByRole('textbox',{name:'Stocks',exact:true}).fill('AAPL\nOLD;01.01.1950;01.01.2000\nOLD;01.01.2001\nUNTIL;;01.01.2020');
  await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog).toHaveCount(0);
  expect(state.groups[1].items).toHaveLength(4);expect(state.groups[1].items[1].date_from).toBe('1950-01-01');
  await page.reload();await page.getByRole('button',{name:'Stock groups',exact:true}).click();
  await page.getByRole('checkbox',{name:'Select stock group [Technology]',exact:true}).check();
  await actions(page).getByRole('button',{name:'Edit stocks',exact:true}).click();
  dialog=page.getByRole('dialog',{name:'Edit stocks [Technology]',exact:true});
  await expect(dialog.getByRole('textbox',{name:'Stocks',exact:true})).toContainText('OLD;01.01.1950;01.01.2000');
  await dialog.getByRole('textbox',{name:'Stocks',exact:true}).fill('');await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog).toHaveCount(0);
  expect(state.groups[1].items).toEqual([]);
  await expect(actions(page).getByRole('button',{name:'Mass delete',exact:true})).toBeEnabled();
  await expect(actions(page).getByRole('button',{name:'Update data in group (automatic)',exact:true})).toBeDisabled();
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

test('imports group files through confirmed saves and exposes partial membership failure',async({page})=>{
  const state=await launch(page);state.failMembers=true;
  await actions(page).getByRole('button',{name:'Load',exact:true}).click();const dialog=page.getByRole('dialog',{name:'Load groups',exact:true});
  const xml='<Groups><Group name="[Imported]"><Desc>Leaders</Desc><Stocks><Stock name="AAPL" from="1950-01-01"/></Stocks></Group></Groups>';
  await dialog.getByLabel('Groups file').setInputFiles({name:'Groups.xml',mimeType:'application/xml',buffer:Buffer.from(xml)});
  await dialog.getByRole('button',{name:'Load',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('0 groups fully loaded');
  expect(state.groups.find(row=>row.name==='[Imported]')?.items).toEqual([]);
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
