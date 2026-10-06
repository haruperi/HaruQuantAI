import { ResultsChart } from '../ResultsCharts';
import { resultSnapshot, type ResultDocument } from '../resultsModel';
import { useState } from 'react';
import { ResultsToolbar } from '../ResultsChrome';
import { overviewTemplates, type Direction, type SampleType } from '../resultsFixtures';
/** Overview results tab: toolbar + Template select + empty overview area. */
export function OverviewTab({ result }: {
    result: ResultDocument | null;
}) {
    const [dataKey, setDataKey] = useState("Main backtest");
    const [direction, setDirection] = useState<Direction>('both');
    const [sampleType, setSampleType] = useState<SampleType>('full');
    const [template, setTemplate] = useState('SQDefault');
    const snapshot = resultSnapshot(direction, sampleType, dataKey);
    return (<div className="sqr-tab">
      <div className="sqr-toolbar-row">
        <ResultsToolbar dataKey={dataKey} dataItems={result?.markets} onDataChange={setDataKey} direction={direction} sampleType={sampleType} onDirectionChange={setDirection} onSampleTypeChange={setSampleType} extendedSample>
          <label>Template</label>
          <span className="sqd-select">
            <span>
              {overviewTemplates.find(t => t.value === template)?.label ?? template}
            </span>
            <select aria-label="Template" value={template} onChange={e => setTemplate(e.target.value)}>
              {overviewTemplates.map(t => (<option key={t.value} value={t.value}>{t.label}</option>))}
            </select>
          </span>
        </ResultsToolbar>
      </div>
      <div className="sqr-content sqr-overview-content">
        {result ? <div className="sqr-overview-report"><div className="sqr-report-summary"><div className="sqr-report-profit"><small>TOTAL PROFIT</small><strong>{snapshot.metrics[0][1]}</strong><p>Drawdown: {snapshot.metrics[4][1]}</p></div><div className="sqr-metric-cards">{snapshot.metrics.map(([label, value]) => <div key={label}><strong>{value}</strong><span>{label}</span></div>)}</div></div><h2>{result.name}</h2><p>{dataKey} · 2025.01.01 - 2025.12.31 · {direction} / {sampleType}</p><ResultsChart values={snapshot.equity} title="Equity by trade"/><h3>Monthly performance — full result</h3><table className="sqr-data-table"><thead><tr><th>Year</th>{['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map(m => <th key={m}>{m}</th>)}</tr></thead><tbody><tr><th>2025</th>{[80, 120, 620, 210, 80, 120, 620, 210, 80, 120, 620, -180].map((v, i) => <td key={i}>{v}</td>)}</tr></tbody></table><h3>Strategy performance</h3><table className="sqr-data-table"><tbody>{snapshot.metrics.map(([k, v]) => <tr key={k}><th>{k}</th><td>{v}</td><td>{sampleType === "full" ? "Full sample" : sampleType === "in" ? "In sample" : "Out of sample"}</td></tr>)}</tbody></table></div> : <h3 className="sqr-no-strategy">No strategy selected</h3>}
      </div>
    </div>);
}
