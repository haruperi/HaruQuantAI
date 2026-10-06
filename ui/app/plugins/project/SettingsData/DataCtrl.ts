import { useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { oosRangePercents, type DataTabState, type OosRange } from '../ProjectWorkbench/settings/sharedSettingsFixtures';

/** Existing local data-form draft and presentation-only preset editor. */
export interface DataController {
  state: DataTabState;
  precision: string;
  setPrecision: Dispatch<SetStateAction<string>>;
  rangeError: string;
  graphShown: boolean;
  setGraphShown: Dispatch<SetStateAction<boolean>>;
  patch: (part: Partial<DataTabState>) => void;
  percents: number[];
  totalDays: number;
  applyPreset: (title: string) => void;
}

/** Preserve initialization, date validation, range rounding and draft lifetime. */
export function useDataController(initialState: DataTabState): DataController {
  const [state, setState] = useState<DataTabState>(()=>structuredClone(initialState));
  const [precision, setPrecision] = useState("1");
  const [rangeError, setRangeError] = useState("");
  const [graphShown, setGraphShown] = useState(false);
  const patch = (part: Partial<DataTabState>) => setState(current => ({ ...current, ...part }));
  const percents = oosRangePercents(state.oosRanges);
  const totalDays = Math.round((new Date(state.dateTo).getTime() - new Date(state.dateFrom).getTime()) / 86400000);

  // Local range-editor presentation only, not a backtest sampling algorithm.
  const applyPreset = (title: string) => {
    const from = Date.parse(state.dateFrom.replaceAll('.', '-'));
    const to = Date.parse(state.dateTo.replaceAll('.', '-'));
    if (!Number.isFinite(from) || !Number.isFinite(to) || to <= from) { setRangeError('Enter a valid date range before applying a preset.'); return; }
    const parts = title.split(',').map(p => { const [type, weight] = p.trim().split(':'); return {type: type as OosRange['type'], weight: weight ? Number(weight) : null}; });
    const specified = parts.reduce((total,p) => total+(p.weight??0),0);
    const missing = parts.filter(p=>p.weight===null).length;
    let cursor = 0;
    const format = (percent: number) => new Date(from + (to-from)*percent/100).toISOString().slice(0,10).replaceAll('-','.');
    patch({oosRanges: parts.map(p => { const start=cursor; cursor += p.weight ?? (100-specified)/missing; return {type:p.type,from:format(start),to:format(cursor)}; })});
    setRangeError(''); setGraphShown(true);
  };
  return {
    state, precision, setPrecision, rangeError, graphShown, setGraphShown,
    patch, percents, totalDays, applyPreset,
  };
}
