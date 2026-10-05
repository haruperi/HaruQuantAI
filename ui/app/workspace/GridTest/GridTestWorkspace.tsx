import { useMemo, useState } from 'react';
import { Select } from '../../components/ui';

export interface GridTestRow { row: number; instrument: string; session: string; bid: number; ask: number; spread: number; tick: number; status: 'Live' | 'Delayed' | 'Closed'; }

export const GRID_TEST_COLUMNS = ['Row', 'Instrument', 'Session', 'Bid', 'Ask', 'Spread', 'Tick #', 'Status'] as const;

const INSTRUMENTS = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'NQ100', 'ES500'] as const;
const SESSIONS = ['London', 'New York', 'Tokyo', 'Sydney'] as const;
const STATUSES: GridTestRow['status'][] = ['Live', 'Delayed', 'Closed'];
const ROW_COUNT_OPTIONS = [10, 100, 500, 1000] as const;

export const GRID_TEST_MAX_ROWS = 1000;
export const GRID_TEST_DEFAULT_SEED = 42;

// Deterministic linear congruential step: an identical seed always rebuilds the identical row set.
const nextRandom = (state: number): number => (1103515245 * state + 12345) % 2147483648;

export function buildGridTestRows(count: number, seed: number = GRID_TEST_DEFAULT_SEED): GridTestRow[] {
  const safeCount = Math.max(0, Math.min(Math.floor(count), GRID_TEST_MAX_ROWS));
  let state = Math.abs(Math.floor(seed)) % 2147483648 || GRID_TEST_DEFAULT_SEED;
  const rows: GridTestRow[] = [];
  for (let index = 0; index < safeCount; index += 1) {
    state = nextRandom(state);
    const bid = 1 + (state % 100000) / 100000;
    state = nextRandom(state);
    const ask = bid + 0.0002 + (state % 50) / 100000;
    state = nextRandom(state);
    const tick = 1000 + index * 7 + (state % 13);
    state = nextRandom(state);
    const status = STATUSES[(index + state) % 3];
    rows.push({ row: index + 1, instrument: INSTRUMENTS[index % INSTRUMENTS.length], session: SESSIONS[index % SESSIONS.length], bid, ask, spread: ask - bid, tick, status });
  }
  return rows;
}

export function GridTestWorkspace() {
  const [count, setCount] = useState<number>(100);
  const rows = useMemo(() => buildGridTestRows(count), [count]);
  return <section className="header-app grid-test" aria-labelledby="grid-test-title">
    <header className="header-app-title"><div><h1 id="grid-test-title">Grid test</h1><span>Development scaffold — deterministic mock data, no backend connected</span></div></header>
    <div className="debug-toolbar">
      <label>Rows<Select value={String(count)} onChange={value => setCount(Number(value))}>{ROW_COUNT_OPTIONS.map(option => <option key={option} value={String(option)}>{option}</option>)}</Select></label>
      <span className="grid-records">Records: {rows.length}</span>
    </div>
    <div className="plain-table-wrap"><table className="plain-table"><thead><tr>{GRID_TEST_COLUMNS.map(column => <th key={column}>{column}</th>)}</tr></thead><tbody>{rows.map(row => <tr key={row.row}><td>{row.row}</td><td>{row.instrument}</td><td>{row.session}</td><td>{row.bid.toFixed(5)}</td><td>{row.ask.toFixed(5)}</td><td>{row.spread.toFixed(5)}</td><td>{row.tick}</td><td>{row.status}</td></tr>)}</tbody></table></div>
  </section>;
}
