import { ResultsChart } from '../ProjectWorkbench/results/ResultsCharts';
import type { ResultDocument } from '../ProjectWorkbench/results/resultsModel';
import { useProfileChart } from './ProfileChartCtrl';

export function ProfileChartTab({ result }: {
    result: ResultDocument | null;
}) {
    const { path, setPath, loading, setLoading } = useProfileChart();
    return (<div className="sqr-tab">
      {result?.chartData && <div className="sqr-toolbar"><select aria-label="Profile chart" value={path} onChange={e => { setPath(e.target.value); setLoading(true); }}>{['EURUSD / H1 / Volume profile', 'GBPUSD / H1 / TPO profile'].map(p => <option key={p}>{p}</option>)}</select></div>}
      <div className="sqr-content sqr-profile-content">{loading && <p role="status">Loading chart...</p>}{result?.chartData ? <ResultsChart values={path.startsWith("EUR") ? [20, 30, 60, 80, 120, 90, 45, 25] : [14, 40, 55, 110, 75, 40, 30, 10]} title={path} bars/> : <p>No profile charts are stored for this strategy. Run a backtest with Volume Profile or TPO Profile indicator (Store chart data enabled) to generate charts.</p>}</div>
    </div>);
}
