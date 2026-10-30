import {expect,test,type Page} from '@playwright/test';

async function launch(page:Page) {
  const entry={id:'a',timestamp:'2026-10-26T10:00:00Z',task_id:'basket-job',message:'Updated AAPL',level:'info',progress:25};
  const state={entries:[entry],failClear:false,failRead:false,clears:0};
  await page.addInitScript(()=>{
    const original=window.fetch.bind(window);
    window.fetch=((input:RequestInfo|URL,init?:RequestInit)=>String(input).includes('/api/v1/events?')?Promise.resolve(new Response(new ReadableStream<Uint8Array>({start(){}}),{headers:{'Content-Type':'text/event-stream'}})):original(input,init)) as typeof fetch;
  });
  await page.route('**/api/v1/**',async route=>{
    const path=new URL(route.request().url()).pathname;let data:unknown=[];
    if(path.endsWith('/auth/login'))data={token:'log-test',expires_at:'2099-01-01T00:00:00Z'};
    else if(path.endsWith('/settings'))data={revision:1,values:{}};
    else if(path.endsWith('/status'))data={cpu_count:4};
    else if(path==='/api/v1/home')data={recent_projects:[]};
    else if(path.endsWith('/data/workspace'))data={tabs:['data','symbols','sessions','brokers','custom-data','chart','home','stock-groups','log'].map((id,index)=>({id,title:id,core:index<5})),active_tab:'data',layout:{core_group:'catalogs',chart_position:'right'}};
    else if(path.includes('/workspace/tabs/'))data={active_tab:path.split('/').at(-1),selection:null,preview:{state:'unavailable',reason:'Select data',rows:[],limit:500}};
    else if(path==='/api/v1/data/logs'){
      if(state.failRead){await route.fulfill({status:503,json:{status:'error',error:{code:'unavailable',message:'Log service unavailable'}}});return;}
      data={entries:state.entries,total:state.entries.length,limit:1000,offset:0};
    }else if(path==='/api/v1/data/logs/active')data=[entry];
    else if(path==='/api/v1/data/logs/clear'){
      if(state.failClear){await route.fulfill({status:503,json:{status:'error',error:{code:'unavailable',message:'History not cleared'}}});return;}
      state.clears++;data={cleared_count:state.entries.length};state.entries=[];
    }
    await route.fulfill({json:{status:'success',success:true,data}});
  });
  await page.goto('/');
  const login=page.getByRole('dialog',{name:'Connect to HaruQuantAI host'});
  await login.getByLabel('Host password').fill('fixture-password');
  await login.getByRole('button',{name:'Connect',exact:true}).click();
  await expect(login).toHaveCount(0);
  await page.getByRole('button',{name:'Data Manager',exact:true}).click();
  await page.getByRole('button',{name:'Log',exact:true}).click();
  await expect(page.getByRole('log',{name:'Data Manager log'})).toContainText('Updated AAPL');
  return state;
}

test('shows backend history and active tasks; clear preserves running task',async({page})=>{
  const state=await launch(page);
  await expect(page.getByLabel('Active log tasks')).toContainText('basket-job: 25%');
  await page.getByTestId('dm-data-log-clear-log-btn').click();
  await expect(page.getByRole('log',{name:'Data Manager log'})).toBeEmpty();
  expect(state.clears).toBe(1);
  await expect(page.getByLabel('Active log tasks')).toContainText('basket-job: 25%');
  state.entries.push({id:'b',timestamp:'2026-10-26T10:01:00Z',task_id:'basket-job',message:'Updated MSFT',level:'info',progress:50});
  await expect(page.getByRole('log',{name:'Data Manager log'})).toContainText('Updated MSFT');
});

test('failed clear retains history and reports the backend error',async({page})=>{
  const state=await launch(page);state.failClear=true;
  await page.getByTestId('dm-data-log-clear-log-btn').click();
  await expect(page.getByRole('alert')).toContainText('History not cleared');
  await expect(page.getByRole('log',{name:'Data Manager log'})).toContainText('Updated AAPL');
  expect(state.clears).toBe(0);
});
