import { useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { atmDefaults, type AtmMethod } from '../ProjectWorkbench/settings/sharedSettingsFixtures';

/** Existing fixture-backed method draft and Add-dialog state. */
export interface AdvancedTMController {
  adding: boolean;
  setAdding: Dispatch<SetStateAction<boolean>>;
  selected: string;
  setSelected: Dispatch<SetStateAction<string>>;
  methods: AtmMethod[];
  patchMethod: (key: string, part: Partial<AtmMethod>) => void;
  patchParam: (key: string, paramKey: string, value: number) => void;
  addExit: () => void;
}

export function useAdvancedTMController(): AdvancedTMController {
  const [adding, setAdding] = useState(false);
  const [selected, setSelected] = useState(atmDefaults[0].key);
  const [methods, setMethods] = useState<AtmMethod[]>(atmDefaults);

  const patchMethod = (key: string, part: Partial<AtmMethod>) =>
    setMethods(current => current.map(m => (m.key === key ? { ...m, ...part } : m)));

  const patchParam = (key: string, paramKey: string, value: number) =>
    setMethods(current =>
      current.map(m => (m.key === key ? { ...m, params: m.params.map(p => (p.key === paramKey ? { ...p, value } : p)) } : m)),
    );

  const addExit = () => {const method=atmDefaults.find(m=>m.key===selected)!;setMethods(items=>[...items,{...structuredClone(method),key:`local-${Date.now()}`,use:true}]);setAdding(false);};
  return { adding, setAdding, selected, setSelected, methods, patchMethod, patchParam, addExit };
}
