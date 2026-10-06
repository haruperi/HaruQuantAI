import { ResultsChart } from '../../ProjectWorkbench/results/ResultsCharts';
import type { ResultDocument } from '../../ProjectWorkbench/results/resultsModel';
import { visibleTrades } from '../../ProjectWorkbench/results/resultsModel';
import { ResultsToolbar, SegmentedButtons } from '../../ProjectWorkbench/results/ResultsChrome';
import { useTradeAnalysis } from '../controllers/TradeAnalysisCtrl';
import { TradeAnalysisPanel } from '../directives/tradeAnalysisPanel';

export function TradeAnalysisTab({ result }: {
    result: ResultDocument | null;
}) {
    const { direction, setDirection, sampleType, setSampleType, dataKey, setDataKey, period, setPeriod } = useTradeAnalysis();
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
      <div className="sqr-content sqr-ta-content">{result && <><ResultsChart values={visibleTrades(result, direction, sampleType, dataKey).map(t => t.profit)} title={period === 1 ? "Profit by open time" : "Profit by close time"} bars/><table className="sqr-data-table"><thead><tr><th>Year (full result)</th><th>Profit</th><th>Trades</th><th>Drawdown</th></tr></thead><tbody><tr><td>2025</td><td>2,700.00</td><td>23</td><td>180.00</td></tr></tbody></table><div className="sqr-analysis-grid">{["Hour of day", "Day of week", "Month"].map(t => <TradeAnalysisPanel key={t} title={t} period={period}/>)}</div></>}</div>
    </div>);
}
