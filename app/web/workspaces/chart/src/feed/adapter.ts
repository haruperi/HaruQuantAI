import type { Bar, Interval } from '../types';
export interface MarketDataAdapter {
  history(symbol: string, start: number, end: number, signal?: AbortSignal): Promise<Bar[]>;
  subscribe(symbol: string, interval: Interval, callback: (bar: Readonly<Bar>) => void): () => void;
}
