import { useEffect, useState } from 'react';
import { useProjectBinding } from '../projectController';
import type { Dispatch, SetStateAction } from 'react';
import { oosRangePercents, type DataTabState, type OosRange } from '../../../common/project/settings/sharedSettingsFixtures';

/** Existing local data-form draft and presentation-only preset editor. */
export interface DataController {
  bound: boolean; source: string; setSource: (source: string) => void;
  splitTime: string; setSplitTime: (value: string) => void;
  model: Record<string, unknown>; setModel: (key: string, value: number) => void;
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
  const binding = useProjectBinding();
  const execution = (binding?.state.draft.execution ?? {}) as Record<string, unknown>;
  const dataset = (execution.dataset ?? {}) as Record<string, unknown>;
  const model = (execution.model ?? {}) as Record<string, unknown>;
  const date = (epoch: unknown) => typeof epoch === 'number' ? new Date(epoch * 1000).toISOString().slice(0, 19) : '';
  const boundState: DataTabState = { engine: 'Core OHLC', symbol: String(dataset.symbol ?? ''), timeframe: String(dataset.timeframe ?? 'M1'),
    dateFrom: date(dataset.start), dateTo: date(dataset.end), oosRanges: [] };
  const [state, setState] = useState<DataTabState>(()=>structuredClone(initialState));
  const [precision, setPrecision] = useState("1");
  const [rangeError, setRangeError] = useState("");
  const [graphShown, setGraphShown] = useState(false);
  useEffect(() => { if (binding) setState(boundState); }, [binding?.state.project?.manifest.project_id, binding?.state.taskId]);
  const patch = (part: Partial<DataTabState>) => {
    setState(current => ({ ...current, ...part }));
    if (!binding) return;
    const next = { ...dataset };
    if (part.symbol !== undefined) { next.symbol = part.symbol; next.revision = null; }
    if (part.timeframe !== undefined) { next.timeframe = part.timeframe; next.revision = null; }
    let error = '';
    for (const [field, value] of [['start', part.dateFrom], ['end', part.dateTo]] as const) {
      if (value !== undefined) {
        const parsed = value ? Date.parse(value.includes('Z') ? value : value + 'Z') : null;
        if (parsed !== null && !Number.isFinite(parsed)) error = 'Enter valid UTC dataset dates.';
        else next[field] = parsed === null ? null : parsed / 1000;
      }
    }
    binding.controller.validate('data', error);
    binding.controller.patchExecution({ dataset: next });
  };
  const percents = oosRangePercents(state.oosRanges);
  const days = (Date.parse(state.dateTo) - Date.parse(state.dateFrom)) / 86400000;
  const totalDays = Number.isFinite(days) ? Math.round(days) : 0;

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
  const setSplitTime = (value: string) => {
    const parsed = value ? Date.parse(value.includes('Z') ? value : value + 'Z') : null;
    binding?.controller.validate('sample', parsed !== null && !Number.isFinite(parsed) ? 'Enter a valid UTC sample boundary.' : '');
    if (parsed === null || Number.isFinite(parsed)) binding?.controller.patchExecution({ split_time: parsed === null ? null : parsed / 1000 });
  };
  return {
    bound: !!binding, source: String(dataset.source ?? ''),
    setSource: source => binding?.controller.patchExecution({ dataset: { ...dataset, source, revision: null } }),
    splitTime: date(execution.split_time), setSplitTime,
    model, setModel: (key, value) => binding?.controller.patchExecution({ model: { ...model, [key]: value } }),
    state: binding && state.engine !== 'Core OHLC' ? boundState : state, precision, setPrecision, rangeError, graphShown, setGraphShown,
    patch, percents, totalDays, applyPreset,
  };
}
