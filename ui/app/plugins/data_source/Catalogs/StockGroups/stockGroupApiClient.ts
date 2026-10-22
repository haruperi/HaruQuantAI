/** Confirmed host transport for stock baskets and dated memberships. */
import { createDomainClient, type DomainClient } from '../../../../host/transport';
import { validateGroup, type StockGroupDefinition, type StockMembership } from './stockGroups';

export interface RemoteBasketRecord {
  id: string; name: string; description: string; system: boolean;
  items: Array<{symbol: string; date_from: string|null; date_to: string|null}>;
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
    members:record.items.map(item=>({ticker:item.symbol,from:item.date_from??undefined,to:item.date_to??undefined}))};
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
  const symbols=members.map(member=>`${member.ticker};${member.from??''};${member.to??''}`);
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
