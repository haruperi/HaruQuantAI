/** Confirmed host transport for stock baskets and dated memberships. */
import {createDomainClient, type DomainClient } from '../../../../host/transport';
import { validateGroup, type StockGroupDefinition, type StockMembership } from './stockGroups';

export interface RemoteBasketRecord {
  stocks_count?:number; active_count?:number; symbols_count?:number; downloaded_count?:number; ready?:boolean; date_from?:string; date_to?:string;
  id: string; name: string; description: string; system: boolean;
  items: Array<{symbol: string; date_from: string|null; date_to: string|null; date_from_ms?:number; date_to_ms?:number}>;
}
let client: DomainClient = createDomainClient('/data');
export function setStockGroupApiClient(value: DomainClient): void { client = value; }
function id(value: string): string {
  if (typeof value !== 'string' || !/^[1-9]\d*$/.test(value) || !Number.isSafeInteger(Number(value))) throw new Error('Choose a saved stock group.');
  return value;
}
export function toStockGroupDefinition(record: RemoteBasketRecord): StockGroupDefinition {
  if (!record || id(record.id) !== record.id || typeof record.name !== 'string' || typeof record.description !== 'string' ||
    typeof record.system !== 'boolean' || !Array.isArray(record.items) || record.items.some(item => !item || typeof item.symbol !== 'string' ||
      !(item.date_from === null || typeof item.date_from === 'string') || !(item.date_to === null || typeof item.date_to === 'string'))) throw new Error('Invalid host stock group.');
  const group: StockGroupDefinition = {id:record.id,name:record.name,description:record.description,system:record.system,
    members:record.items.map(item=>({ticker:item.symbol,from:item.date_from??undefined,to:item.date_to??undefined,...(item.date_from_ms !== undefined?{fromMs:item.date_from_ms}:{}),...(item.date_to_ms !== undefined?{toMs:item.date_to_ms}:{})})),
    ...(record.stocks_count !== undefined?{statistics:{total:record.stocks_count,active:record.active_count??0,numberOfSymbols:record.symbols_count??0,downloaded:record.downloaded_count??0,ready:record.ready??false,from:record.date_from??'',to:record.date_to??''}}:{})};
  validateGroup(group);return group;
}
export async function fetchStockGroups(): Promise<StockGroupDefinition[]> {
  const rows = await client.get<RemoteBasketRecord[]>('/baskets');
  if (!Array.isArray(rows)) throw new Error('Invalid host stock group catalog.');
  const groups=rows.map(toStockGroupDefinition);
  if(new Set(groups.map(row=>row.id)).size!==groups.length || new Set(groups.map(row=>row.name.toLowerCase())).size!==groups.length) throw new Error('Duplicate stock group identities.');
  return groups;
}
export async function saveStockGroup(group: StockGroupDefinition): Promise<StockGroupDefinition> {
  validateGroup({...group,id:group.id||'new'});
  const saved=toStockGroupDefinition(await client.post<RemoteBasketRecord>('/baskets',{
    ...(group.id ? {id:id(group.id)}:{}),name:group.name,description:group.description,
  }));
  if(saved.name!==group.name || (group.id && saved.id!==group.id)) throw new Error('The host did not confirm this group.');
  return saved;
}
export async function saveStockGroupMembers(groupId: string, members: StockMembership[]): Promise<StockGroupDefinition> {
  const symbols=members.map(member=>`${member.ticker};${member.fromMs??member.from??''};${member.toMs??member.to??''}`);
  const saved=toStockGroupDefinition(await client.put<RemoteBasketRecord>(`/baskets/${id(groupId)}/stocks`,{symbols}));
  if(saved.id!==groupId) throw new Error('The host returned a different stock group.');
  return saved;
}

export async function deleteStockGroups(values: string[]): Promise<string[]> {
  if (!Array.isArray(values) || !values.length || values.length > 1000) throw new Error('Select between 1 and 1000 stock groups.');
  const ids=[...new Set(values.map(id))];
  const result=await client.post<{deleted_ids:string[];deleted_count:number}>('/baskets/delete',{ids});
  if(!result || !Array.isArray(result.deleted_ids) || result.deleted_count!==ids.length ||
    result.deleted_ids.length!==ids.length || new Set(result.deleted_ids).size!==ids.length ||
    result.deleted_ids.some(value=>typeof value!=='string'||!ids.includes(value))) {
    throw new Error('The host did not confirm the selected stock group deletions. Refresh before retrying.');
  }
  return result.deleted_ids;
}

export async function fetchStockGroupMembers(groupId:string):Promise<StockGroupDefinition> {
  const saved=toStockGroupDefinition(await client.get<RemoteBasketRecord>(`/baskets/${id(groupId)}/stocks`));
  if(saved.id!==groupId)throw new Error('The host returned a different group.');return saved;
}
export async function importStockGroupMembers(groupId:string,content:string):Promise<StockGroupDefinition> {
  const saved=toStockGroupDefinition(await client.post<RemoteBasketRecord>(`/baskets/${id(groupId)}/import-stocks`,{content}));
  if(saved.id!==groupId)throw new Error('The host returned a different group.');return saved;
}
async function exportFile(path:string,body:unknown):Promise<string> {
  const result=await client.post<{content:string;count:number}>(path,body);
  if(typeof result?.content!=='string'||!Number.isSafeInteger(result.count)||result.count<0)throw new Error('Invalid stock group file response.');
  return result.content;
}
export const exportStockGroupMembers=(groupId:string)=>exportFile(`/baskets/${id(groupId)}/export-stocks`,{});
export const exportStockGroupCatalog=(ids:string[])=>exportFile('/baskets/save',{ids:ids.map(id)});
export async function loadStockGroupCatalog(content:string):Promise<number> {
  const result=await client.post<{loaded_count:number}>('/baskets/load',{content});
  if(!Number.isSafeInteger(result?.loaded_count)||result.loaded_count<0)throw new Error('Invalid groups import confirmation.');return result.loaded_count;
}
export interface BasketJob {job_id:string;kind:string;status:string;progress:number;error_message?:string;message?:string;result?:{updated_count?:number}}
function job(value:BasketJob):BasketJob {
  if(!value||typeof value.job_id!=='string'||!value.job_id||value.kind!=='baskets.update_data'||!['QUEUED','RUNNING','PAUSED','COMPLETED','FAILED','CANCELLED','INTERRUPTED'].includes(value.status)||!Number.isFinite(value.progress)||value.progress<0||value.progress>100)throw new Error('Invalid stock group job response.');
  return value;
}
export async function startStockGroupUpdate(ids:string[]):Promise<BasketJob> {return job(await client.post<BasketJob>('/baskets/update-data',{ids:ids.map(id)}));}
export async function fetchStockGroupJob(jobId:string):Promise<BasketJob> {const result=job(await client.get<BasketJob>(`/basket-jobs/${encodeURIComponent(jobId)}`));if(result.job_id!==jobId)throw new Error('Different job returned.');return result;}
export async function controlStockGroupJob(jobId:string,action:'pause'|'resume'|'stop'):Promise<BasketJob> {const result=job(await client.post<BasketJob>(`/basket-jobs/${encodeURIComponent(jobId)}/${action}`,{}));if(result.job_id!==jobId)throw new Error('Different job returned.');return result;}

export async function editStockGroupCatalog(ids:string[],updates:Record<string,unknown>):Promise<StockGroupDefinition[]> {
  const rows=await client.post<RemoteBasketRecord[]>('/baskets/edit',{ids:ids.map(id),updates});
  if(!Array.isArray(rows)||rows.length!==new Set(ids).size)throw new Error('Invalid group edit confirmation');
  const saved=rows.map(toStockGroupDefinition);if(new Set(saved.map(row=>row.id)).size!==new Set(ids).size||saved.some(row=>!ids.includes(row.id)))throw new Error('Different stock groups returned');return saved;
}
