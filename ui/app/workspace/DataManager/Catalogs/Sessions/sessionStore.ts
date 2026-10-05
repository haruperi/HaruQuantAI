import { catalogPort } from '../../Common/catalogClient';
import { normalizeLegacyBranding } from '../../../../host/branding';
import { create } from 'zustand';
import { effectiveSessions, validateSession, type SessionDefinition } from './sessions';

interface SessionState { sessions:SessionDefinition[]; overrides:Record<string,SessionDefinition>; removed:string[]; storageError:string; refresh:()=>Promise<void>; importLegacy:()=>Promise<void>;
  add:(item:SessionDefinition,brokers:string[])=>Promise<void>; edit:(original:string,item:SessionDefinition,brokers:string[])=>Promise<void>;
  clone:(item:SessionDefinition,brokers:string[])=>Promise<void>; remove:(names:string[],referenced:string[])=>Promise<void>;
  importSessions:(items:SessionDefinition[],overwrite:string[])=>Promise<void>;
  importForBroker:(items:SessionDefinition[],overwrite:string[])=>Promise<void>;
}
const key='haru-data-sessions-v1';
export const useSessions=create<SessionState>((set,get)=>{
  let initial:Pick<SessionState,'sessions'|'overrides'|'removed'|'storageError'>={sessions:[],overrides:{},removed:[],storageError:''};
  try { const raw=localStorage.getItem(key); if(raw){ const value=normalizeLegacyBranding(JSON.parse(raw)); if(value.version!==1||!Array.isArray(value.sessions)||!value.overrides||typeof value.overrides!=='object'||!Array.isArray(value.removed)||value.sessions.length>10000||Object.keys(value.overrides).length>10000||value.removed.length>10000) throw new Error('invalid');
    const names:string[]=[]; for(const item of value.sessions as SessionDefinition[]){validateSession(item,names,[item.broker],false);names.push(item.name);} for(const [name,item] of Object.entries(value.overrides) as [string,SessionDefinition][]){if(name!==item.name)throw new Error('invalid');validateSession(item,[],[item.broker],false);} if(value.removed.some((name:unknown)=>typeof name!=='string'))throw new Error('invalid'); initial={sessions:value.sessions,overrides:value.overrides,removed:value.removed,storageError:''}; }}
  catch { initial.storageError='Saved sessions could not be read. Existing browser storage has been preserved.'; }
  initial = { sessions: [], overrides: {}, removed: [], storageError: '' };
  const port = catalogPort<any>('sessions');
  async function refresh(): Promise<void> { try { set({ ...await port.read(), storageError: '' }); } catch (cause) { set({ storageError: cause instanceof Error ? cause.message : 'Catalog unavailable.' }); } }
  async function importLegacy(): Promise<void> { const raw = localStorage.getItem('haru-data-sessions-v1'); if (!raw) throw new Error('No saved browser catalog.'); const saved = normalizeLegacyBranding(JSON.parse(raw)); await persist(saved); }
  async function persist(patch: any): Promise<void> { const next = { ...get(), ...patch }; const state = await port.write({ sessions: next.sessions, overrides: next.overrides, removed: next.removed }); set({ ...state, storageError: '' }); }
  return {...initial, refresh, importLegacy,
    add: async (item,brokers) =>{validateSession(item,effectiveSessions(get().sessions,get().overrides,get().removed).map(row=>row.name),brokers);await persist({sessions:[...get().sessions,structuredClone(item)]});},
    edit: async (original,item,brokers) =>{if(item.name!==original)throw new Error('Session identity cannot be changed while editing.');const all=effectiveSessions(get().sessions,get().overrides,get().removed);validateSession(item,all.filter(row=>row.name!==original).map(row=>row.name),brokers,false);const index=get().sessions.findIndex(row=>row.name===original);if(index>=0){const sessions=[...get().sessions];sessions[index]=structuredClone(item);await persist({sessions});}else if(Boolean(get().overrides[original]))await persist({overrides:{...get().overrides,[original]:structuredClone(item)}});else throw new Error('Session no longer exists.');},
    clone: async (item,brokers) =>{validateSession(item,effectiveSessions(get().sessions,get().overrides,get().removed).map(row=>row.name),brokers);await persist({sessions:[...get().sessions,structuredClone(item)]});},
    remove: async (names,referenced) =>{if(!names.length)throw new Error('No session selected');const blocked=names.find(name=>referenced.includes(name));if(blocked)throw new Error(`Session '${blocked}' is used by an instrument and cannot be removed.`);const selected=new Set(names);await persist({sessions:get().sessions.filter(row=>!selected.has(row.name)),overrides:Object.fromEntries(Object.entries(get().overrides).filter(([name])=>!selected.has(name))),removed:[...new Set([...get().removed,...names.filter(name=>Boolean(get().overrides[name]))])]});},
    importSessions: async (items,overwrite) =>{const current=effectiveSessions(get().sessions,get().overrides,get().removed);const replace=new Set(overwrite);const sessions=[...get().sessions];const overrides={...get().overrides};for(const item of items){const found=current.find(row=>row.name.toLowerCase()===item.name.toLowerCase());if(found){if(!replace.has(found.name))continue;const value={...item,name:found.name,broker:found.broker,brokerName:found.brokerName};const index=sessions.findIndex(row=>row.name===found.name);if(index>=0)sessions[index]=value;else overrides[found.name]=value;}else sessions.push(item);}await persist({sessions,overrides});},
    importForBroker: async (items,overwrite) =>{const current=effectiveSessions(get().sessions,get().overrides,get().removed);const replace=new Set(overwrite);const sessions=[...get().sessions];const overrides={...get().overrides};for(const item of items){const found=current.find(row=>row.name.toLowerCase()===item.name.toLowerCase());if(found){if(!replace.has(found.name))continue;const value={...structuredClone(item),name:found.name};const index=sessions.findIndex(row=>row.name===found.name);if(index>=0)sessions[index]=value;else overrides[found.name]=value;}else sessions.push(structuredClone(item));}await persist({sessions,overrides});},
  };
});
