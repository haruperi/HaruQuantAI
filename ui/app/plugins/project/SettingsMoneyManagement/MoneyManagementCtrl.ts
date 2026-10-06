import { useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { moneyManagementDefaults, type MmMethod } from '../ProjectWorkbench/settings/sharedSettingsFixtures';

/** Existing local capital/method draft; no position sizing or persistence. */
export interface MoneyManagementController {
  initialCapital: number;
  setInitialCapital: Dispatch<SetStateAction<number>>;
  methods: MmMethod[];
  setMethods: Dispatch<SetStateAction<MmMethod[]>>;
  patch: (key: string, part: Partial<MmMethod>) => void;
}

export function useMoneyManagementController(): MoneyManagementController {
  const [initialCapital, setInitialCapital] = useState(moneyManagementDefaults.initialCapital);
  const [methods, setMethods] = useState<MmMethod[]>(moneyManagementDefaults.methods);

  const patch = (key: string, part: Partial<MmMethod>) =>
    setMethods(current => current.map(m => (m.key === key ? { ...m, ...part } : m)));

  return { initialCapital, setInitialCapital, methods, setMethods, patch };
}
