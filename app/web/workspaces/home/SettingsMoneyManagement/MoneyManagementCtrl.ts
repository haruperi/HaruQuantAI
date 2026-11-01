import { useState } from 'react';
import { useProjectBinding } from '../projectController';
import type { Dispatch, SetStateAction } from 'react';
import { moneyManagementDefaults, type MmMethod } from '../../../common/project/settings/sharedSettingsFixtures';

/** Existing local capital/method draft; no position sizing or persistence. */
export interface MoneyManagementController {
  bound: boolean; clearMethod: () => void;
  initialCapital: number;
  setInitialCapital: Dispatch<SetStateAction<number>>;
  methods: MmMethod[];
  setMethods: Dispatch<SetStateAction<MmMethod[]>>;
  patch: (key: string, part: Partial<MmMethod>) => void;
}

export function useMoneyManagementController(): MoneyManagementController {
  const binding = useProjectBinding();
  const [localCapital, setLocalCapital] = useState(moneyManagementDefaults.initialCapital);
  const [localMethods, setLocalMethods] = useState<MmMethod[]>(moneyManagementDefaults.methods);
  const execution = (binding?.state.draft.execution ?? {}) as Record<string, unknown>;
  const model = (execution.model ?? {}) as Record<string, unknown>;
  const sizing = execution.money_management as { method: string; size: number } | null | undefined;
  const initialCapital = binding ? Number(model.initial_capital ?? 100000) : localCapital;
  const methods = binding ? moneyManagementDefaults.methods.map(method => ({ ...method, use: sizing?.method === method.key,
    params: method.key === 'FixedSize' ? method.params.map(parameter => ({ ...parameter, value: String(sizing?.size ?? 0.1) })) : method.params })) : localMethods;
  const setInitialCapital: Dispatch<SetStateAction<number>> = value => {
    const next = typeof value === 'function' ? value(initialCapital) : value;
    if (!binding) { setLocalCapital(next); return; }
    binding.controller.validate('money', Number.isFinite(next) && next > 0 ? '' : 'Initial capital must be positive.');
    binding.controller.patchExecution({ model: { ...model, initial_capital: next } });
  };
  const setMethods: Dispatch<SetStateAction<MmMethod[]>> = value => {
    const next = typeof value === 'function' ? value(methods) : value;
    if (!binding) { setLocalMethods(next); return; }
    const selected = next.find(method => method.use);
    const size = Number(selected?.params.find(parameter => parameter.key === 'Size')?.value);
    const valid = selected?.key === 'FixedSize' && Number.isFinite(size) && size > 0;
    binding.controller.validate('sizing', valid ? '' : 'Only a positive fixed size is supported for this mode.');
    if (valid) binding.controller.patchExecution({ money_management: { method: 'FixedSize', size, decimals: 8 } });
  };
  const patch = (key: string, part: Partial<MmMethod>) => setMethods(methods.map(method => method.key === key ? { ...method, ...part } : method));
  return { bound: !!binding, clearMethod: () => binding?.controller.patchExecution({ money_management: null }),
    initialCapital, setInitialCapital, methods, setMethods, patch };
}
