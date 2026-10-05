/** Owner-local prototype state. Shared published resources are accessed through the host. */
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { ownerViewStorage, mergeViewState, previewResources, connectPreviewDocument } from '../../../host/resourceClient';
import { useAppStore as useShellStore } from '../../../host/store';
import type { PortfolioMember } from './presentation';
interface LocalState { portfolio: PortfolioMember[]; reset: () => void; }

const portfolioMembers: PortfolioMember[] = JSON.parse("[{\"strategyId\":\"str-59\",\"weight\":15,\"enabled\":true,\"sector\":\"FX Majors\"},{\"strategyId\":\"str-60\",\"weight\":15,\"enabled\":true,\"sector\":\"Metals\"},{\"strategyId\":\"str-61\",\"weight\":15,\"enabled\":true,\"sector\":\"Indices\"},{\"strategyId\":\"str-62\",\"weight\":15,\"enabled\":true,\"sector\":\"FX Majors\"},{\"strategyId\":\"str-63\",\"weight\":10,\"enabled\":true,\"sector\":\"Metals\"},{\"strategyId\":\"str-64\",\"weight\":10,\"enabled\":true,\"sector\":\"Indices\"},{\"strategyId\":\"str-65\",\"weight\":10,\"enabled\":true,\"sector\":\"FX Majors\"},{\"strategyId\":\"str-66\",\"weight\":10,\"enabled\":true,\"sector\":\"Metals\"}]");
const useLocalState = create<LocalState>()(persist((set) => ({portfolio: portfolioMembers, reset: () => set({portfolio: portfolioMembers})}), {name: 'plugin.retester.project_workbench.view.v1', version: 1, storage:createJSONStorage(() => { if (typeof localStorage === 'undefined') throw new Error('Local view storage unavailable'); return ownerViewStorage; }), merge:mergeViewState}));

type CombinedState = ReturnType<typeof useShellStore.getState> & LocalState;
function useCombinedState<T = CombinedState>(selector: (state: CombinedState) => T = state => state as unknown as T): T {
 const shell=useShellStore(); const local=useLocalState(); return selector({...shell,...local});
}
export const useAppStore=Object.assign(useCombinedState, {getState: (): CombinedState => ({...useShellStore.getState(),...useLocalState.getState()}), setState: useLocalState.setState, subscribe: useLocalState.subscribe, persist:useLocalState.persist});
