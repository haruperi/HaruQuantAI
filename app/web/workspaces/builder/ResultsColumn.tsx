import { useProjectBinding } from '../home/projectController';
import { ResultsChart } from '../../common/project/results/ResultsCharts';
import type { SampleType } from './fixtures';

export function ResultsColumn({ sampleType, onSampleSelect, onOpenResults }: {
  sampleType: SampleType; onSampleSelect: (sample: SampleType) => void; onOpenResults: (rank?: number) => void;
}) {
  const binding = useProjectBinding();
  return <div className="sqd-results-wrap">{binding?.state.results.length ? binding.state.results.slice(0, 3).map((result, rank) => {
    const execution = result.parameters.execution as { split_time?: number | null } | undefined;
    const boundary = execution?.split_time;
    const shownSample = boundary ? sampleType : 'full';
    const suffix = shownSample === 'full' ? '' : shownSample === 'in' ? '_is' : '_oos';
    const curve = result.equity_curve.filter(point => !boundary || shownSample === 'full' || (shownSample === 'in' ? point.timestamp <= boundary : point.timestamp > boundary));
    return <div className="sqd-result-card" key={result.result_id}>
      <button className="sqd-result-title" onClick={() => onOpenResults(rank)}>{result.strategy_name}</button>
      <div className="sqd-result-body"><div className="sqd-sample-toolbar">Sample <div className="sqd-btn-group">
        {(['full', 'in', 'out'] as const).map(sample => <button key={sample} disabled={sample !== 'full' && !boundary} className={shownSample === sample ? 'active' : ''} onClick={() => onSampleSelect(sample)}>{sample === 'full' ? 'Full' : sample === 'in' ? 'IS' : 'OOS'}</button>)}
      </div></div><div className="sqd-result-overview">{['net_profit', 'profit_factor', 'trades_count', 'drawdown'].map(metric => <div className="sqd-overview-row" key={metric}><span>{metric}</span><span>{String(result.metrics[metric + suffix] ?? 'Unavailable')}</span></div>)}</div>
      <ResultsChart title="Stored equity" values={curve.map(point => point.equity)} /></div>
    </div>;
  }) : <p>No stored backtest results.</p>}</div>;
}
