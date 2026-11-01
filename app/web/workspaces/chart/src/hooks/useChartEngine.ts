import { createContext, useContext, type MutableRefObject, type RefObject } from 'react';
import type { ChartStore } from '../store/chartStore';
import type { ChartEngine } from '../engine/ChartEngine';
export interface ChartServices {
  store: ChartStore;
  engine: MutableRefObject<ChartEngine | null>;
  root: RefObject<HTMLDivElement | null>;
  onCrosshairTime?: (time: number | null) => void;
  onViewport?: (range: readonly [number, number]) => void;
}
export const ChartContext = createContext<ChartServices | null>(null);
export function useChart() {
  const value = useContext(ChartContext);
  if (!value) throw new Error('Chart provider missing');
  return value;
}
