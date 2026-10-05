/** Host shell preferences and route/view selections only. */
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import type { AppSettings, ModuleId, ProjectTab } from './types';
import { createInitialAppSettings, mergeAppSettings } from './globalSettings';
import { mergeViewState, ownerViewStorage } from './resourceClient';
import { navigation } from './contributions';
interface AppState { module: ModuleId;
tab: ProjectTab;
selectedStrategyId: string;
resultView: string;
selectedBankId: string;
selectedRows: string[];
settings: AppSettings;
notifications: string[];
setModule: (module: ModuleId) => void;
setTab: (tab: ProjectTab) => void;
selectStrategy: (id: string) => void;
setResultView: (view: string) => void;
setBank: (id: string) => void;
setRows: (ids: string[]) => void;
updateSettings: (patch: Partial<AppSettings>) => void;
notify: (message: string) => void; reset:()=>void; }
const initialSettings: AppSettings = createInitialAppSettings();
export const useAppStore = create<AppState>()(persist((set)=>({
module: 'builder',
tab: 'progress',
selectedStrategyId: 'str-1',
resultView: 'Overview',
selectedBankId: 'results',
selectedRows: [],
settings: initialSettings,
notifications: [],
setModule: module => set({ module, tab: (navigation.find(item=>item.id===module)?.defaultTab ?? 'settings') as ProjectTab }),
setTab: tab => set({ tab }),
selectStrategy: selectedStrategyId => set({ selectedStrategyId }),
setResultView: resultView => set({ resultView }),
setBank: selectedBankId => set({ selectedBankId, selectedRows: [] }),
setRows: selectedRows => set({ selectedRows }),
updateSettings: patch => set(s => ({ settings: { ...s.settings, ...patch } })),
notify: message => set(s => ({ notifications: [message, ...s.notifications].slice(0, 8) })), reset:()=>set({module: 'builder',
tab: 'progress',
selectedStrategyId: 'str-1',
resultView: 'Overview',
selectedBankId: 'results',
selectedRows: [],
settings: initialSettings,
notifications: []})
}),{name:'host.shell.view.v1',version:1,storage:createJSONStorage(() => { if(typeof localStorage === 'undefined') throw new Error('Local view storage unavailable'); return ownerViewStorage; }),partialize:s=>{
const {settings:_settings,...view}=s; return {...view,notifications:[]};
},merge:(saved,current)=>({...mergeViewState(saved,current),settings:mergeAppSettings()})}));
