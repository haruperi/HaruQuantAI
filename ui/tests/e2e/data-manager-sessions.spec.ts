import { expect, test, type Page } from '@playwright/test';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

function profile(id: string, name: string) {
  return { id, name, broker_id: 0, description: 'Configured calendar', timezone: 'America/New_York', is_default: true,
    windows: [{ day_from: 'Mon', day_to: 'Mon', start_time: '09:00:15', end_time: '12:00:45', eod: false, session_type: 'Regular' },
      { day_from: 'Mon', day_to: 'Mon', start_time: '13:00:00', end_time: '16:00:00', eod: true, session_type: 'Regular' }],
    holidays: [{ date_str: '2028-02-29', description: 'Configured holiday' }] };
}
async function launch(page: Page) {
  const night = profile('2','Night');
  night.windows = [{ day_from: 'Sun', day_to: 'Mon', start_time: '23:50:15', end_time: '00:10:45', eod: true, session_type: 'Extended' }];
  let rows: Record<string,any>[] = [profile('1','Day'), night];
  const state = { failRead: false, failWrite: false, slow: false, failDeletes: new Set<string>(), writes: [] as { path: string; body: any }[] };
  const errors: string[] = []; page.on('pageerror',error=>errors.push(error.message)); page.on('close',()=>expect(errors).toEqual([]));
  await page.addInitScript(()=>{
    localStorage.setItem('haru-data-sessions-v1',JSON.stringify({sessions:[{name:'CACHED_FAKE'}]}));
    const original=window.fetch.bind(window);
    window.fetch=((input:RequestInfo|URL,init?:RequestInit)=>String(input).includes('/api/v1/events?')?Promise.resolve(new Response(new ReadableStream<Uint8Array>({start(){}}),{headers:{'Content-Type':'text/event-stream'}})):original(input,init)) as typeof fetch;
  });
  await page.route('**/api/v1/**',async route=>{
    const path=new URL(route.request().url()).pathname, method=route.request().method();
    let data:unknown=[];
    if(path.endsWith('/auth/login'))data={token:'session-test',expires_at:'2099-01-01T00:00:00Z'};
    else if(path.endsWith('/settings'))data={revision:1,values:{}};
    else if(path.endsWith('/status'))data={cpu_count:4};
    else if(path==='/api/v1/home')data={recent_projects:[]};
    else if(path.endsWith('/data/workspace'))data={tabs:['data','instruments','sessions','brokers','custom-data','chart','home','stock-groups','log'].map((id,index)=>({id,title:id,core:index<5})),active_tab:'data',layout:{core_group:'catalogs',chart_position:'right'}};
    else if(path.includes('/workspace/tabs/'))data={active_tab:path.split('/').at(-1),selection:null,preview:{state:'unavailable',reason:'Select a saved dataset.',rows:[],limit:500}};
    else if(path==='/api/v1/data/sessions'&&method==='GET'){
      if(state.failRead){await route.fulfill({status:503,json:{status:'error',error:{code:'UNAVAILABLE',message:'Session catalog unavailable'}}});return;}
      data=rows;
    }else if(path.startsWith('/api/v1/data/sessions')&&method!=='GET'){
      const body=method==='DELETE'?{}:route.request().postDataJSON();
      state.writes.push({path,body});
      if(state.slow)await new Promise(resolve=>setTimeout(resolve,600));
      const id=path.split('/')[5];
      if(state.failWrite||method==='DELETE'&&state.failDeletes.has(id)){await route.fulfill({status:503,json:{status:'error',error:{code:'WRITE_FAILED',message:'Session was not saved'}}});return;}
      if(method==='DELETE'){rows=rows.filter(row=>row.id!==id);data={id,deleted:true};}
      else if(path.endsWith('/elements')){
        const row=rows.find(row=>row.id===id)!;
        if(body.action==='add')row.windows.push(body.window);
        else if(body.action==='update')row.windows[body.index]=body.window;
        else row.windows.splice(body.index,1);
        data=row;
      }else if(path.endsWith('/clone')){
        const source=rows.find(row=>row.id===body.session_id)!;
        const days=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
        const windows=source.windows.map((window:any)=>{
          const result={...window};
          for(const [dayKey,timeKey]of[['day_from','start_time'],['day_to','end_time']]){
            const [h,m,s=0]=window[timeKey].split(':').map(Number);
            const seconds=((days.indexOf(window[dayKey])*86400+h*3600+m*60+s+body.timezone_offset*60)%604800+604800)%604800;
            result[dayKey]=days[Math.floor(seconds/86400)];
            const clock=seconds%86400;
            result[timeKey]=String(Math.floor(clock/3600)).padStart(2,'0')+':'+String(Math.floor(clock%3600/60)).padStart(2,'0')+(window[timeKey].split(':').length===3?':'+String(clock%60).padStart(2,'0'):'');
          }return result;
        });
        const created={...structuredClone(source),id:String(Math.max(0,...rows.map(row=>Number(row.id)))+1),name:body.new_name,is_default:false,windows};rows.push(created);data=created;
      }else{
        if(body.id){rows=rows.map(row=>row.id===body.id?{...row,...body}:row);data=rows.find(row=>row.id===body.id);}
        else{const created={...body,id:String(Math.max(0,...rows.map(row=>Number(row.id)))+1)};rows.push(created);data=created;}
      }
    }
    await route.fulfill({json:{status:'success',data}});
  });
  await page.goto('/');
  const login=page.getByRole('dialog',{name:'Connect to HaruQuantAI host'});
  await login.getByLabel('Host password').fill('fixture-password');await login.getByRole('button',{name:'Connect',exact:true}).click();await expect(login).toHaveCount(0);
  await page.getByRole('button',{name:'Data Manager',exact:true}).click();
  await page.getByRole('navigation',{name:'Data Manager workspace navigation'}).getByRole('button',{name:'Sessions',exact:true}).click();
  await expect(page.getByRole('table',{name:'Sessions',exact:true})).toContainText('Day');
  return {state,rows:()=>rows};
}
const table=(page:Page)=>page.getByRole('table',{name:'Sessions',exact:true});
const actions=(page:Page)=>page.getByLabel('Session operations',{exact:true});

test('creates a profile with lunch intervals and holidays after confirmation, then reloads',async({page})=>{
  const {state}=await launch(page);
  await expect(table(page)).not.toContainText('CACHED_FAKE');await expect(table(page)).not.toContainText('Forex 24/5');
  await actions(page).getByRole('button',{name:'Add Session',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Add session template',exact:true});
  await dialog.getByLabel('Session name',{exact:true}).fill('NewSchedule');
  await dialog.getByLabel('Timezone',{exact:true}).fill('Asia/Kolkata');
  for(const [from,to]of[['09:00:15','12:00:45'],['13:00:00','16:00:00']]){
    await dialog.getByRole('button',{name:'Add interval',exact:true}).click();
    const element=page.getByRole('dialog',{name:'Add session',exact:true});
    await element.getByLabel('Start time',{exact:true}).fill(from);await element.getByLabel('End time',{exact:true}).fill(to);
    await element.getByRole('button',{name:'Save',exact:true}).click();await expect(element).toHaveCount(0);
  }
  await dialog.getByRole('button',{name:'Add holiday',exact:true}).click();
  await dialog.getByLabel('Holiday date 1',{exact:true}).fill('2028-02-29');
  await dialog.getByLabel('Holiday description 1',{exact:true}).fill('Configured closure');
  state.slow=true;
  await dialog.getByRole('button',{name:'Save',exact:true}).click();
  await expect(dialog.getByRole('button',{name:'Saving…',exact:true})).toBeDisabled();
  await expect(table(page)).not.toContainText('NewSchedule');
  await expect(dialog).toHaveCount(0);await expect(table(page)).toContainText('NewSchedule');
  expect(state.writes.at(-1)?.body).toMatchObject({timezone:'Asia/Kolkata',holidays:[{date_str:'2028-02-29',description:'Configured closure'}]});
  await page.reload();await page.getByRole('button',{name:'Data Manager',exact:true}).click();
  await page.getByRole('navigation',{name:'Data Manager workspace navigation'}).getByRole('button',{name:'Sessions',exact:true}).click();
  await expect(table(page)).toContainText('NewSchedule');await expect(table(page)).toContainText('09:00:15');
});

test('edits existing intervals immediately and preserves unsaved profile fields until Save',async({page})=>{
  const {state,rows}=await launch(page);
  await table(page).getByRole('row').filter({has:page.getByLabel('Select session Day',{exact:true})}).dblclick();
  const dialog=page.getByRole('dialog',{name:'Edit session template',exact:true});
  await dialog.getByLabel('Description',{exact:true}).fill('Updated profile');
  await dialog.getByRole('table',{name:'Session elements'}).getByRole('row').nth(1).dblclick();
  const element=page.getByRole('dialog',{name:'Edit session',exact:true});
  await element.getByLabel('Start time',{exact:true}).fill('10:00:30');
  await element.getByRole('button',{name:'Save',exact:true}).click();await expect(element).toHaveCount(0);
  expect(rows()[0].windows[0].start_time).toBe('10:00:30');expect(rows()[0].description).toBe('Configured calendar');
  await expect(dialog.getByLabel('Description',{exact:true})).toHaveValue('Updated profile');
  await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog).toHaveCount(0);
  expect(rows()[0]).toMatchObject({timezone:'America/New_York',description:'Updated profile',holidays:[{date_str:'2028-02-29',description:'Configured holiday'}]});
  expect(state.writes.some(row=>row.path.endsWith('/elements'))).toBe(true);
  await page.screenshot({path:join(tmpdir(),'haru-sessions-authoritative.png'),fullPage:true});
});

test('clones through week rollover in minutes without moving holidays or source',async({page})=>{
  const {state,rows}=await launch(page);
  await table(page).getByLabel('Select session Night',{exact:true}).check();
  await actions(page).getByRole('button',{name:'Clone Session',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Clone session',exact:true});
  await dialog.getByLabel('New session name',{exact:true}).fill('Shifted');
  await dialog.getByLabel('Shift schedule (minutes)',{exact:true}).fill('30');
  await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog).toHaveCount(0);
  expect(state.writes.at(-1)?.body).toEqual({session_id:'2',new_name:'Shifted',timezone_offset:30});
  expect(rows().at(-1)?.windows[0]).toMatchObject({day_from:'Mon',day_to:'Mon',start_time:'00:20:15',end_time:'00:40:45'});
  expect(rows()[1].windows[0].day_from).toBe('Sun');expect(rows().at(-1)?.holidays).toEqual(rows()[1].holidays);
});

test('cancelled drafts and failed saves produce no local success',async({page})=>{
  const {state}=await launch(page);
  await actions(page).getByRole('button',{name:'Add Session',exact:true}).click();
  let dialog=page.getByRole('dialog',{name:'Add session template',exact:true});
  await dialog.getByLabel('Session name',{exact:true}).fill('Discarded');
  await dialog.getByRole('button',{name:'Close',exact:true}).last().click();
  await page.getByRole('dialog',{name:'Changes not saved',exact:true}).getByRole('button',{name:'Yes',exact:true}).click();
  expect(state.writes).toHaveLength(0);
  state.failWrite=true;
  await table(page).getByRole('row').filter({has:page.getByLabel('Select session Day',{exact:true})}).dblclick();
  dialog=page.getByRole('dialog',{name:'Edit session template',exact:true});
  await dialog.getByLabel('Description',{exact:true}).fill('Not saved');
  await dialog.getByRole('button',{name:'Save',exact:true}).click();
  await expect(dialog.getByRole('alert')).toContainText('not saved');await expect(table(page)).not.toContainText('Not saved');
  await dialog.getByRole('button',{name:'Close',exact:true}).last().click();
  await page.getByRole('dialog',{name:'Changes not saved',exact:true}).getByRole('button',{name:'Yes',exact:true}).click();
  await table(page).getByRole('row').filter({has:page.getByLabel('Select session Day',{exact:true})}).dblclick();
  dialog=page.getByRole('dialog',{name:'Edit session template',exact:true});
  await dialog.getByRole('table',{name:'Session elements'}).getByRole('row').nth(1).dblclick();
  const element=page.getByRole('dialog',{name:'Edit session',exact:true});
  await element.getByLabel('Start time',{exact:true}).fill('10:00:30');
  await element.getByRole('button',{name:'Save',exact:true}).click();
  await expect(element.getByRole('alert')).toContainText('not saved');
  await expect(table(page)).toContainText('09:00:15');
});

test('multi-delete reports partial failure and removes only confirmed IDs',async({page})=>{
  const {state}=await launch(page);state.failDeletes.add('2');
  await table(page).getByLabel('Select all visible sessions').check();
  await actions(page).getByRole('button',{name:'Mass Delete',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Removing sessions',exact:true});
  await dialog.getByRole('button',{name:'Yes',exact:true}).click();
  await expect(dialog.getByRole('alert')).toContainText('1 deleted; 1 could not be deleted');
  await expect(table(page)).not.toContainText('Day');await expect(table(page)).toContainText('Night');
  state.failDeletes.clear();await dialog.getByRole('button',{name:'Yes',exact:true}).click();await expect(dialog).toHaveCount(0);
  await expect(table(page)).toContainText('No matching sessions.');
});

test('failed refresh is visible and successful empty catalog clears saved rows',async({page})=>{
  const {state,rows}=await launch(page);state.failRead=true;
  await page.getByRole('button',{name:'Refresh sessions',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Showing the last server snapshot.');
  rows().splice(0);state.failRead=false;
  await page.getByRole('button',{name:'Refresh sessions',exact:true}).click();
  await expect(table(page)).toContainText('No matching sessions.');
});


test('loading and initial read failure are distinct from an empty catalog',async({page})=>{
  await launch(page);
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/v1/data/sessions',async route=>{
    await gate;
    await route.fulfill({status:503,json:{status:'error',error:{code:'UNAVAILABLE',message:'Session catalog unavailable'}}});
  });
  await page.reload();await page.getByRole('button',{name:'Data Manager',exact:true}).click();
  await page.getByRole('navigation',{name:'Data Manager workspace navigation'}).getByRole('button',{name:'Sessions',exact:true}).click();
  try {
    await expect(table(page)).toContainText('Loading session profiles');
    await expect(table(page)).not.toContainText('No matching sessions.');
  } finally { release(); }
  await expect(table(page)).toContainText('Session profiles could not be loaded.');
  await expect(table(page)).not.toContainText('No matching sessions.');
  await expect(page.getByRole('alert')).toContainText('Session catalog unavailable');
});

test('catalog shows saved values in the requested column order and keeps compatibility notes in the edit form',async({page})=>{
  const {state,rows}=await launch(page);
  rows()[0].normalization_warnings=['Legacy numeric weekdays use 0=Monday through 6=Sunday.','EOD was not stored; the historical default False is used.'];
  await page.getByRole('button',{name:'Refresh sessions',exact:true}).click();
  await expect(table(page).getByRole('columnheader')).toHaveText(['','Session Name','Description','Timezone','Intervals','Holidays','']);
  await expect(table(page).getByRole('columnheader',{name:'Broker profile',exact:true})).toHaveCount(0);
  await expect(table(page).getByRole('note')).toHaveCount(0);
  const savedRow=table(page).getByRole('row').filter({has:page.getByLabel('Select session Day',{exact:true})});
  await expect(savedRow.getByRole('cell').nth(1)).toHaveText('Day');
  await expect(savedRow.getByRole('cell').nth(2)).toHaveText('Configured calendar');
  rows()[1].description='';rows()[1].windows=[];rows()[1].holidays=[];
  await page.getByRole('button',{name:'Refresh sessions',exact:true}).click();
  const emptyRow=table(page).getByRole('row').filter({has:page.getByLabel('Select session Night',{exact:true})});
  for(const index of [2,4,5])await expect(emptyRow.getByRole('cell').nth(index)).toBeEmpty();
  await table(page).getByRole('row').filter({has:page.getByLabel('Select session Day',{exact:true})}).dblclick();
  const dialog=page.getByRole('dialog',{name:'Edit session template',exact:true});
  await expect(dialog.getByRole('note',{name:'Stored session compatibility'})).toContainText('0=Monday through 6=Sunday');
  await expect(dialog).toContainText('Reading leaves the stored profile unchanged.');
  expect(state.writes).toHaveLength(0);
  await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog).toHaveCount(0);
  expect(state.writes.at(-1)?.body).not.toHaveProperty('normalization_warnings');
  expect(state.writes.at(-1)?.body).not.toHaveProperty('normalizationWarnings');
  expect(state.writes.at(-1)?.body.windows[0]).toMatchObject({day_from:'Mon',start_time:'09:00:15',eod:false});
  await page.screenshot({path:join(tmpdir(),'haru-sessions-simple-catalog.png'),fullPage:true});
});
