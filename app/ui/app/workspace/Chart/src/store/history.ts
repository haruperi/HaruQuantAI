import type { DocumentState } from '../types';
import type { StateCreator, StoreApi } from 'zustand/vanilla';
import type { ChartState } from './chartStore';
type HistoryCreator = (
  set: StoreApi<ChartState>['setState'],
  get: StoreApi<ChartState>['getState'],
  api: StoreApi<ChartState>,
) => Omit<ChartState, 'history' | 'edit' | 'undo'>;

/** Only explicit document transactions enter time travel; live execution never does. */
export function withChartHistory(creator: HistoryCreator): StateCreator<ChartState> {
  return (set, get, api) => {
    const snapshot = (s: ChartState): DocumentState => ({
      chart: s.chart,
      drawings: s.drawings,
      indicators: s.indicators,
    });
    return {
      ...creator(set, get, api),
      history: { past: [], future: [] },
      edit: (change) => set((s) => ({ ...change, history: record(s.history, snapshot(s)) })),
      undo: (redo = false) => {
        const s = get(),
          result = travel(s.history, snapshot(s), redo);
        if (result) set({ ...result.document, history: result.history });
      },
    };
  };
}
export interface History {
  past: DocumentState[];
  future: DocumentState[];
}
export const historyLimit = 100;
export function record(history: History, before: DocumentState): History {
  return {
    past: [...history.past.slice(-(historyLimit - 1)), structuredClone(before)],
    future: [],
  };
}
export function travel(
  history: History,
  current: DocumentState,
  redo: boolean,
): { history: History; document: DocumentState } | null {
  const source = redo ? history.future : history.past;
  const document = source.at(-1);
  if (!document) return null;
  return {
    document: structuredClone(document),
    history: redo
      ? {
          past: [...history.past, structuredClone(current)].slice(-historyLimit),
          future: source.slice(0, -1),
        }
      : { past: source.slice(0, -1), future: [...history.future, structuredClone(current)] },
  };
}
