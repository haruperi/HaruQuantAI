/** Backend job ownership; persisted IDs recover status, never simulated progress. */
import {create} from 'zustand';
import {ApiClientError, createDomainClient} from '../../../host/transport';
import {validateDownload, type DownloadRequest, type DownloadState, type DownloadJob} from './dukascopyDownload';

const key='sqx-data-download-v1';
const client=createDomainClient('/data');
interface HostJob {job_id:string;status:string;progress:number;message:string;error_message?:string|null}
interface Store extends DownloadState {
  storageError:string; starting:boolean;
  start:(request:DownloadRequest)=>Promise<void>;
  advance:()=>Promise<void>;
  action:(action:'pause'|'resume'|'stop')=>Promise<void>;
}
function fromHost(record:HostJob, request:DownloadRequest):DownloadJob {
  const states:Record<string,DownloadJob['state']>={QUEUED:'running',RUNNING:'running',PAUSED:'paused',COMPLETED:'completed',CANCELLED:'cancelled',FAILED:'failed',INTERRUPTED:'failed'};
  if (!record || typeof record.job_id!=='string' || !states[record.status] || !Number.isFinite(record.progress)) throw new Error('Invalid backend download job.');
  return {jobId:record.job_id,request,state:states[record.status],progress:record.progress,error:record.error_message??undefined};
}
export function createDownloadStore(refreshCatalog:()=>Promise<void>) {
  let job:DownloadJob|null=null,preferred:DownloadState['preferred']=null,storageError='';
  try {
    const raw=localStorage.getItem(key);
    if(raw){const saved=JSON.parse(raw);preferred=saved.preferred??null;if(saved.version===2 && typeof saved.job?.jobId==='string'){validateDownload(saved.job.request);if(!['running','paused','completed','cancelled','failed'].includes(saved.job.state))throw new Error('Invalid saved job');job=saved.job;}}
  }catch{storageError='Saved download job could not be read.';}
  return create<Store>((set,get)=>{
    let polling=false,revision=0;
    const persist=(next:Partial<Store>)=>{
      set(next);
      const state=get();
      try{localStorage.setItem(key,JSON.stringify({version:2,job:state.job,preferred:state.preferred}));}
      catch{set({storageError:'Download is controlled by the backend; its ID could not be saved locally.'});}
    };
    return {
      job,preferred,storageError,ranges:{},starting:false,
      start:async request=>{
        if(get().starting || ['running','paused'].includes(get().job?.state??''))throw new Error('Finish or stop the active backend download first.');
        validateDownload(request);
        set({starting:true});
        try{
          const record=await client.post<HostJob>('/providers/download',{provider:'dukascopy',targets:request.targets.map(target=>({symbol:target.symbol,timeframe:target.timeframe})),date_from:request.dateFrom,date_to:request.dateTo,overwrite:request.overwrite,download_type:request.downloadType});
          revision++;
          const accepted=fromHost(record,structuredClone(request));
          persist({job:accepted,preferred:request.downloadType,storageError:''});
          if(['completed','cancelled','failed'].includes(accepted.state))await refreshCatalog();
        }finally{set({starting:false});}
      },
      advance:async()=>{
        const current=get().job;
        if(polling || !current?.jobId || !['running','paused'].includes(current.state))return;
        polling=true;const generation=revision;
        try{
          const record=await client.get<HostJob>(`/download-jobs/${encodeURIComponent(current.jobId)}`);
          if(generation!==revision)return;
          const updated=fromHost(record,current.request);
          persist({job:updated,storageError:''});
          if(['completed','cancelled','failed'].includes(updated.state))await refreshCatalog();
        }catch(error){if(generation===revision){if(error instanceof ApiClientError && error.status===404)persist({job:{...current,state:'failed',error:'Backend job no longer exists.'}});else set({storageError:error instanceof Error?error.message:'Unable to read backend job status.'});}}
        finally{polling=false;}
      },
      action:async action=>{
        const current=get().job;if(!current?.jobId)return;
        revision++;
        try{
          const record=await client.post<HostJob>(`/download-jobs/${encodeURIComponent(current.jobId)}/${action}`,{});
          persist({job:fromHost(record,current.request),storageError:''});
          if(action==='stop')await refreshCatalog();
        }catch(error){set({storageError:error instanceof Error?error.message:'Download control failed.'});}
      },
    };
  });
}
