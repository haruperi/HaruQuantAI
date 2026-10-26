import {expect,test,type Page} from '@playwright/test';

async function launch(page:Page){
  const state={status:'RUNNING',progress:15,failStart:false,failPoll:false,posts:[] as Array<{path:string;body:any}>,bars:1};
  await page.addInitScript(()=>{
    const original=window.fetch.bind(window);
    window.fetch=((input:RequestInfo|URL,init?:RequestInit)=>String(input).includes('/api/v1/events?')?Promise.resolve(new Response(new ReadableStream<Uint8Array>({start(){}}),{headers:{'Content-Type':'text/event-stream'}})):original(input,init)) as typeof fetch;
  });
  await page.route('**/api/v1/**',async route=>{
    const path=new URL(route.request().url()).pathname;let data:unknown=[];
    if(path.endsWith('/auth/login'))data={token:'download-test',expires_at:'2099-01-01T00:00:00Z'};
    else if(path.endsWith('/settings'))data={revision:1,values:{}};
    else if(path.endsWith('/status'))data={cpu_count:4};
    else if(path==='/api/v1/home')data={recent_projects:[]};
    else if(path.endsWith('/data/workspace'))data={tabs:['data','symbols','sessions','brokers','custom-data','chart','home','stock-groups','log'].map((id,index)=>({id,title:id,core:index<5})),active_tab:'data',layout:{core_group:'catalogs',chart_position:'right'}};
    else if(path.includes('/workspace/tabs/'))data={active_tab:path.split('/').at(-1),selection:null,preview:{state:'unavailable',reason:'Select data',rows:[],limit:500}};
    else if(path.endsWith('/home/datasets'))data=[{id:'dukascopy:EURUSD:M1',source:'dukascopy',symbol:'EURUSD',underlying:'EURUSD',timeframe:'M1',broker:'default',timezone:'UTC',date_from:'2025-01-01',date_to:'2025-01-01',bars:state.bars}];
    else if(path==='/api/v1/data/providers/download'){
      state.posts.push({path,body:route.request().postDataJSON()});
      if(state.failStart){await route.fulfill({status:503,json:{status:'error',error:{code:'unavailable',message:'Provider rejected download'}}});return;}
      data={job_id:'backend-job',status:state.status,progress:state.progress,message:'Downloading'};
    }else if(path.includes('/download-jobs/backend-job')){
      if(route.request().method()==='POST'){
        const action=path.split('/').at(-1);state.posts.push({path,body:{}});
        state.status=action==='pause'?'PAUSED':action==='resume'?'RUNNING':'CANCELLED';
      }
      if(state.failPoll){await route.fulfill({status:503,json:{status:'error',error:{code:'unavailable',message:'Backend offline'}}});return;}
      data={job_id:'backend-job',status:state.status,progress:state.progress,message:state.status,error_message:state.status==='FAILED'?'Provider failed':null};
    }
    await route.fulfill({json:{status:'success',success:true,data}});
  });
  await page.goto('/');const login=page.getByRole('dialog',{name:'Connect to HaruQuantAI host'});
  await login.getByLabel('Host password').fill('fixture-password');await login.getByRole('button',{name:'Connect',exact:true}).click();await expect(login).toHaveCount(0);
  await page.getByRole('button',{name:'Data Manager',exact:true}).click();
  return state;
}
async function open(page:Page){
  await page.getByRole('checkbox',{name:'Select EURUSD',exact:true}).check();
  await page.getByRole('button',{name:'Dukascopy data',exact:true}).click();
  await page.getByRole('menuitem',{name:'Download data for existing symbol',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:/Download Dukascopy data for/});
  await dialog.getByRole('radio',{name:/Standard download/}).check();
  return dialog;
}

test('forwards overwrite and mode and controls a backend job across reload',async({page})=>{
  const state=await launch(page);const dialog=await open(page);
  await dialog.getByRole('radio',{name:'Overwrite existing data',exact:true}).check();
  await dialog.getByRole('button',{name:'Start download',exact:true}).click();
  const progress=page.getByLabel('Data Manager progress');
  await expect(progress).toContainText('running 15%');
  expect(state.posts[0].body).toMatchObject({overwrite:true,download_type:'standard',targets:[{symbol:'EURUSD',timeframe:'M1'}]});
  await page.getByRole('button',{name:'Pause all',exact:true}).click();await expect(progress).toContainText('paused 15%');
  await page.reload();await expect(progress).toContainText('paused 15%');
  await page.getByRole('button',{name:'Resume all',exact:true}).click();await expect(progress).toContainText('running 15%');
  state.status='COMPLETED';state.progress=100;state.bars=10;
  await expect(progress).toContainText('completed 100%');
  expect(state.posts.some(post=>post.path.endsWith('/resume'))).toBe(true);
});

test('submission failure retains configuration and never starts a fake job',async({page})=>{
  const state=await launch(page);state.failStart=true;const dialog=await open(page);
  await dialog.getByRole('button',{name:'Start download',exact:true}).click();
  await expect(dialog.getByRole('alert')).toContainText('Provider rejected download');
  await expect(dialog).toBeVisible();await expect(page.getByLabel('Data Manager progress')).not.toContainText('completed');
});

test('backend failure and stop are reflected rather than timer completion',async({page})=>{
  const state=await launch(page);const dialog=await open(page);await dialog.getByRole('button',{name:'Start download',exact:true}).click();
  const progress=page.getByLabel('Data Manager progress');await expect(progress).toContainText('running 15%');
  state.status='FAILED';await expect(progress).toContainText('failed 15%: Provider failed');
  state.status='RUNNING';const again=await open(page);await again.getByRole('button',{name:'Start download',exact:true}).click();
  await expect(progress).toContainText('running 15%');
  await page.getByRole('button',{name:'Stop all',exact:true}).click();await expect(progress).toContainText('cancelled 15%');
  expect(state.posts.some(post=>post.path.endsWith('/stop'))).toBe(true);
});
