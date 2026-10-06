import { useState } from 'react';
import { tradingOptionsDefaults, type TradingOptionProperty } from '../ProjectWorkbench/settings/sharedSettingsFixtures';

/** Existing local trading-options draft; no engine or schema synchronization. */
export interface OptionsController {
  properties: TradingOptionProperty[];
  setProperty: (key: string, value: boolean | number | string) => void;
}

export function useOptionsController(): OptionsController {
  const [properties, setProperties] = useState<TradingOptionProperty[]>(tradingOptionsDefaults);

  const setProperty = (key: string, value: boolean | number | string) =>
    setProperties(current => current.map(p => (p.key === key ? { ...p, value } : p)));

  return { properties, setProperty };
}
