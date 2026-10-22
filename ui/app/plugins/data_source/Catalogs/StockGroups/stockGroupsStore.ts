import { create } from 'zustand';
import { normalizeGroupName, validateGroup, type StockGroupDefinition, type StockGroupDataset, type StockGroupUpdateJob, type StockMembership } from './stockGroups';
import { deleteStockGroups, fetchStockGroups, saveStockGroup, saveStockGroupMembers } from './stockGroupApiClient';

interface Store {
  groups: StockGroupDefinition[];
  loading: boolean; storageError: string;
  generated: StockGroupDataset[]; job: StockGroupUpdateJob|null;
  syncRemote: () => Promise<void>;
  saveGroup: (name:string,description:string,source?:StockGroupDefinition) => Promise<StockGroupDefinition>;
  replaceMembers: (id:string,members:StockMembership[]) => Promise<void>;
  applyImported: (items:StockGroupDefinition[],decisions:Record<string,'skip'|'overwrite'>) => Promise<number>;
  remove: (ids:string[]) => Promise<void>;
  start: (ids:string[],existing:string[],active:boolean) => never;
  action: (action:'pause'|'resume'|'stop') => never;
}
export const stockGroupJobActive=(state?:string)=>state==='running'||state==='paused';
let request=0;
const unavailable=():never=>{throw new Error('Automatic stock group data updates are unavailable.');};
export const useStockGroups=create<Store>((set,get)=>{
  const confirmed=(saved:StockGroupDefinition)=>{
    ++request;
    set(current=>({loading:false,storageError:'',groups:current.groups.some(row=>row.id===saved.id)
      ? current.groups.map(row=>row.id===saved.id?saved:row):[...current.groups,saved]}));
  };
  return {
    groups:[],loading:false,storageError:'',generated:[],job:null,
    syncRemote:async()=>{
      const active=++request;set({loading:true,storageError:''});
      try {const groups=await fetchStockGroups();if(active===request)set({groups});}
      catch(cause){if(active===request)set({storageError:cause instanceof Error?cause.message:'Unable to load stock groups.'});}
      finally{if(active===request)set({loading:false});}
    },
    saveGroup:async(name,description,source)=>{
      if(source?.system)throw new Error('System stock groups cannot be edited.');
      const draft:StockGroupDefinition={id:source?.id??'',name:normalizeGroupName(name),description:description.trim(),system:false,members:source?.members??[]};
      validateGroup({...draft,id:draft.id||'new'},get().groups);
      const saved=await saveStockGroup(draft);confirmed(saved);return saved;
    },
    replaceMembers:async(id,members)=>{
      const source=get().groups.find(row=>row.id===id);
      if(!source||source.system)throw new Error('Choose an editable stock group.');
      validateGroup({...source,members},get().groups);
      confirmed(await saveStockGroupMembers(id,members));
    },
    applyImported:async(items,decisions)=>{
      let count=0;
      try {
        for(const item of items){
          const previous=get().groups.find(row=>row.name.toLowerCase()===item.name.toLowerCase());
          if(previous && decisions[item.name]!=='overwrite')continue;
          const saved=await get().saveGroup(item.name,item.description,previous);
          await get().replaceMembers(saved.id,item.members);count++;
        }
      } catch(cause){throw new Error(`${count} groups fully loaded. Earlier confirmed changes remain saved; ${cause instanceof Error?cause.message:'group load failed.'}`);}
      return count;
    },
    remove:async ids=>{
      const selected=ids.map(id=>get().groups.find(group=>group.id===id));
      if(selected.some(group=>!group||group.system))throw new Error('Choose saved custom stock groups.');
      const deleted=await deleteStockGroups(ids);
      ++request;
      set(current=>({loading:false,storageError:'',groups:current.groups.filter(group=>!deleted.includes(group.id))}));
    },
    start:unavailable,action:unavailable,
  };
});
