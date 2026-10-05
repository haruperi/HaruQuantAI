/** Owner-local prototype state. Shared published resources are accessed through the host. */
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { ownerViewStorage, mergeViewState, previewResources, connectPreviewDocument } from '../../host/resourceClient';
import { useAppStore as useShellStore } from '../../host/store';
import type { RuleNode } from './documents';
interface LocalState { rules: RuleNode[];
updateRule: (id: string, patch: Partial<RuleNode>) => void; reset: () => void; }

const rules: RuleNode[] = JSON.parse("[{\"id\":\"r1\",\"depth\":0,\"kind\":\"event\",\"label\":\"On Bar Open\"},{\"id\":\"r2\",\"depth\":1,\"kind\":\"if\",\"label\":\"IF\"},{\"id\":\"r3\",\"depth\":2,\"kind\":\"condition\",\"label\":\"EMA(12) crosses above EMA(28)\"},{\"id\":\"r4\",\"depth\":2,\"kind\":\"condition\",\"label\":\"ATR(14) > 0.0012\"},{\"id\":\"r5\",\"depth\":1,\"kind\":\"then\",\"label\":\"THEN\"},{\"id\":\"r6\",\"depth\":2,\"kind\":\"action\",\"label\":\"Enter at Market (Long)\"},{\"id\":\"r7\",\"depth\":2,\"kind\":\"action\",\"label\":\"Set Stop Loss: 90 pips\"},{\"id\":\"r8\",\"depth\":2,\"kind\":\"action\",\"label\":\"Set Profit Target: 180 pips\"}]");
const useLocalState = create<LocalState>()(persist((set) => ({rules,
updateRule: (id, patch) => set(s => ({ rules: s.rules.map(r => r.id === id ? { ...r, ...patch } : r) })), reset: () => set({rules})}), {name: 'workspace.algo_wizard.view.v1', version: 1, storage:createJSONStorage(() => { if (typeof localStorage === 'undefined') throw new Error('Local view storage unavailable'); return ownerViewStorage; }), merge:mergeViewState}));

type CombinedState = ReturnType<typeof useShellStore.getState> & LocalState;
function useCombinedState<T = CombinedState>(selector: (state: CombinedState) => T = state => state as unknown as T): T {
 const shell=useShellStore(); const local=useLocalState(); return selector({...shell,...local});
}
export const useAppStore=Object.assign(useCombinedState, {getState: (): CombinedState => ({...useShellStore.getState(),...useLocalState.getState()}), setState: useLocalState.setState, subscribe: useLocalState.subscribe, persist:useLocalState.persist});
