import { useState } from 'react';
import { useProjectBinding } from '../projectController';
import { tradingOptionsDefaults, type TradingOptionProperty } from '../../../common/project/settings/sharedSettingsFixtures';

/** Existing local trading-options draft; no engine or schema synchronization. */
export interface OptionsController {
  properties: TradingOptionProperty[];
  setProperty: (key: string, value: boolean | number | string) => void;
}

export function useOptionsController(): OptionsController {
  const binding = useProjectBinding();
  const [localProperties, setProperties] = useState<TradingOptionProperty[]>(tradingOptionsDefaults);

  const execution = (binding?.state.draft.execution ?? {}) as Record<string, unknown>;
  const model = (execution.model ?? {}) as Record<string, unknown>;
  const properties: TradingOptionProperty[] = binding ? [
    { key: 'commission_per_order', label: 'Commission per order', type: 'spinner', value: Number(model.commission_per_order ?? 0) },
    { key: 'slippage_points', label: 'Slippage points', type: 'spinner', value: Number(model.slippage_points ?? 0) },
    { key: 'same_bar_sl_tp_rule', label: 'Same-bar stop and target rule', type: 'select', value: String(model.same_bar_sl_tp_rule ?? 'WORST_CASE'), options: ['WORST_CASE', 'BEST_CASE'] },
  ] : localProperties;
  const setProperty = (key: string, value: boolean | number | string) => {
    if (!binding) { setProperties(current => current.map(property => property.key === key ? { ...property, value } : property)); return; }
    binding.controller.validate('options', typeof value === 'number' && (!Number.isFinite(value) || value < 0) ? 'Costs must be finite and nonnegative.' : '');
    binding.controller.patchExecution({ model: { ...model, [key]: value } });
  };
  return { properties, setProperty };
}
