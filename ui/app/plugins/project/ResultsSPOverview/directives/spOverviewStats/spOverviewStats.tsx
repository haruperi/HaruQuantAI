import type { ResultDocument } from '../../../ProjectWorkbench/results/resultsModel';

/** The existing four mock metric cards; no stockpicker summary calculation. */
export function SPOverviewStats({ result }: { result: ResultDocument | null }) {
    return <div className="sqr-metric-cards">{result?.metrics.slice(0, 4).map(([k, v]) => <div key={k}><strong>{v}</strong><span>{k}</span></div>)}</div>;
}
