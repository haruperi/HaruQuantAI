import { bestStrategies, resultRankTitle, type SampleType } from './fixtures';
/**
 * SQX-style results column of the Builder Progress tab (donor evidence
 * retained target UI; current donor equivalence unverified). Up to three best-strategy cards; the donor shows only
 * the first card at default zoom (implemented via CSS, siblings hidden).
 * The Sample selector is shared across cards and clicking a card opens the
 * Results tab. Chart and overview values are demo fixture truth.
 */
const SAMPLES: {
    id: SampleType;
    label: string;
}[] = [
    { id: 'full', label: 'Full' },
    { id: 'in', label: 'IS' },
    { id: 'out', label: 'OOS' },
];
function EquityCurve({ points }: {
    points: number[];
}) {
    const w = 300;
    const h = 90;
    const min = Math.min(...points);
    const max = Math.max(...points);
    const range = Math.max(max - min, 0.01);
    const coords = points
        .map((v, i) => `${(i / (points.length - 1)) * (w - 8) + 4},${h - 6 - ((v - min) / range) * (h - 12)}`)
        .join(' ');
    return (<svg className="sqd-equity-svg" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" role="img" aria-label="Equity chart">
      <polyline points={coords} fill="none" stroke="#4290d8" strokeWidth={1.6}/>
    </svg>);
}
export function ResultsColumn({ strategyNames, sampleType, onSampleSelect, onOpenResults, }: {
    strategyNames?: string[];
    sampleType: SampleType;
    onSampleSelect: (sample: SampleType) => void;
    onOpenResults: (rank?: number) => void;
}) {
    return (<div className="sqd-results-wrap">
      {bestStrategies.map((strategy, ranking) => (<div className="sqd-result-card" key={strategy.name} role="button" tabIndex={0} onKeyDown={e => { if (e.key === 'Enter')
            onOpenResults(ranking); }} title="Open in Results" onClick={() => onOpenResults(ranking)}>
          <div className="sqd-result-title">{resultRankTitle(ranking, strategyNames?.[ranking] ?? strategy.name)}</div>
          <div className="sqd-result-body">
            <div className="sqd-sample-toolbar">
              <label>Sample</label>
              <div className="sqd-btn-group">
                {SAMPLES.map(sample => (<button key={sample.id} type="button" className={sampleType === sample.id ? 'active' : ''} onClick={e => {
                    e.stopPropagation();
                    onSampleSelect(sample.id);
                }}>
                    {sample.label}
                  </button>))}
              </div>
            </div>
            <div className="sqd-result-overview">
              {strategy.overview.map(row => (<div className="sqd-overview-row" key={row.label}>
                  <span>{row.label}</span>
                  <span>{row.value}</span>
                </div>))}
            </div>
            <div className="sqd-result-equity">
              <EquityCurve points={strategy.equity}/>
            </div>
          </div>
        </div>))}
    </div>);
}
