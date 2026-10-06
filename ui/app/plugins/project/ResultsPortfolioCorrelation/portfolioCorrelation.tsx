import type { ResultDocument } from '../ProjectWorkbench/results/resultsModel';
import { CorrelationMatrix } from './tabs/correlationMatrix/correlationMatrix';

export function PortfolioCorrelationTab({ result, period, setPeriod }: { result: ResultDocument; period: string; setPeriod: (value: string) => void }) {
  if (!result.portfolio) return <div className="sqr-tab"><div className="sqr-content">Strategy is not a portfolio.</div></div>;
  return <div className="sqr-tab"><div className="sqr-toolbar"><label>Correlation by <select value={period} onChange={e => setPeriod(e.target.value)}>{['Hour', 'Day', 'Week', 'Month'].map(p => <option key={p}>{p}</option>)}</select></label></div><div className="sqr-content"><CorrelationMatrix period={period}/><p className="sqd-gen-help">Precomputed local UI fixture. No analysis is executed.</p></div></div>;
}
