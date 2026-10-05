import { ResultsChart } from '../ResultsCharts';
import { type ResultDocument, visibleTrades } from '../resultsModel';
import { useEffect, useState } from 'react';
import { ResultsToolbar, SegmentedButtons } from '../ResultsChrome';
import { SqdCheckbox } from '../../settings/SettingsControls';
import type { Direction, SampleType } from '../resultsFixtures';
/** SP overview tab: stats + traded stocks tree-map header (no shared toolbar). */
export function SpOverviewTab({ result }: {
    result: ResultDocument | null;
}) {
    const [showAll, setShowAll] = useState(false);
    return (<div className="sqr-tab">
      <div className="sqr-content sqr-sp-content">
        <div className="sqr-metric-cards">{result?.metrics.slice(0, 4).map(([k, v]) => <div key={k}><strong>{v}</strong><span>{k}</span></div>)}</div>
        <div className="sqr-sp-treemap-title">
          <div className="title">
            TRADED STOCKS OVERVIEW ({showAll ? 'ALL' : 'TOP 100 BY VOLUME'})
          </div>
          <SqdCheckbox checked={showAll} onChange={setShowAll}>Show all</SqdCheckbox>
        </div>
        {result && <ResultsChart values={showAll ? [25, 18, 12, 8, 7, 6, 5, 4] : [25, 18, 12, 8]} title="Traded stocks / fixture volume" bars/>}
      </div>
    </div>);
}
/** Trade analysis tab: shared toolbar + Period by segmented + empty panels area. */
export function TradeAnalysisTab({ result }: {
    result: ResultDocument | null;
}) {
    const [direction, setDirection] = useState<Direction>('both');
    const [sampleType, setSampleType] = useState<SampleType>('full');
    const [dataKey, setDataKey] = useState("Main backtest");
    const [period, setPeriod] = useState(1);
    return (<div className="sqr-tab">
      <div className="sqr-toolbar-row">
        <ResultsToolbar dataKey={dataKey} dataItems={result?.markets} onDataChange={setDataKey} direction={direction} sampleType={sampleType} onDirectionChange={setDirection} onSampleTypeChange={setSampleType} extendedSample>
          <label>Period by</label>
          <SegmentedButtons ariaLabel="Period by" options={[
            { value: 1, label: 'Open Time' },
            { value: 2, label: 'Close Time' },
        ]} value={period} onChange={setPeriod}/>
        </ResultsToolbar>
      </div>
      <div className="sqr-content sqr-ta-content">{result && <><ResultsChart values={visibleTrades(result, direction, sampleType, dataKey).map(t => t.profit)} title={period === 1 ? "Profit by open time" : "Profit by close time"} bars/><table className="sqr-data-table"><thead><tr><th>Year (full result)</th><th>Profit</th><th>Trades</th><th>Drawdown</th></tr></thead><tbody><tr><td>2025</td><td>2,700.00</td><td>23</td><td>180.00</td></tr></tbody></table><div className="sqr-analysis-grid">{["Hour of day", "Day of week", "Month"].map(t => <ResultsChart key={t} title={t} values={period === 1 ? [12, 7, 14, 8, 20, 9] : [8, 12, 6, 18, 9, 17]} bars/>)}</div></>}</div>
    </div>);
}
/** Profile chart tab: empty until a result provides chart paths (no toolbar). */
export function ProfileChartTab({ result }: {
    result: ResultDocument | null;
}) {
    const [path, setPath] = useState('EURUSD / H1 / Volume profile');
    const [loading, setLoading] = useState(false);
    useEffect(() => { if (!loading)
        return; const timer = window.setTimeout(() => setLoading(false), 250); return () => window.clearTimeout(timer); }, [loading]);
    return (<div className="sqr-tab">
      {result?.chartData && <div className="sqr-toolbar"><select aria-label="Profile chart" value={path} onChange={e => { setPath(e.target.value); setLoading(true); }}>{['EURUSD / H1 / Volume profile', 'GBPUSD / H1 / TPO profile'].map(p => <option key={p}>{p}</option>)}</select></div>}
      <div className="sqr-content sqr-profile-content">{loading && <p role="status">Loading chart...</p>}{result?.chartData ? <ResultsChart values={path.startsWith("EUR") ? [20, 30, 60, 80, 120, 90, 45, 25] : [14, 40, 55, 110, 75, 40, 30, 10]} title={path} bars/> : <p>No profile charts are stored for this strategy. Run a backtest with Volume Profile or TPO Profile indicator (Store chart data enabled) to generate charts.</p>}</div>
    </div>);
}
/** Strategy config tab: empty-state label. */
export function StrategyConfigTab({ result }: {
    result: ResultDocument | null;
}) {
    return (<div className="sqr-tab">
      <div className="sqr-content sqr-config-content">
        <label className="sqr-info-label">{result ? `${result.name} — Local configuration preview` : "No strategy selected."}</label>{result && <pre>{JSON.stringify({ engine: "MetaTrader4", symbol: "EURUSD", timeframe: "H1", moneyManagement: "Fixed size 0.1 lots", entry: "Moving average crossover", stopLoss: "40 pips", profitTarget: "80 pips" }, null, 2)}</pre>}
      </div>
    </div>);
}
/** Custom analysis tab (user ResultsPlugins; demo fixture panel). */
export function CustomAnalysisTab({ name, result }: {
    name: string;
    result: ResultDocument | null;
}) {
    return (<div className="sqr-tab sqr-custom-tab">
      <div className="sqr-content sqr-custom-content">
        <div className="sqr-custom-box">
          <h3>{name}</h3>
          <p>
            Local mock analysis for the selected strategy.
          </p>
          {result ? <ResultsChart values={result.equity} title={`${name} / local mock analysis`} benchmark/> : <p>Select a strategy in the databank to load its results here.</p>}
        </div>
      </div>
    </div>);
}
