import { TradesChart } from '../ProjectWorkbench/results/ResultsCharts';

/** Existing stored mock trade-chart view; controls remain shared support. */
export function ResultsChartTab() {
  return <div className="sqr-tab"><div className="sqr-toolbar"/><div className="sqr-content"><TradesChart/><p className="sqd-gen-help">Precomputed local UI fixture. No analysis is executed.</p></div></div>;
}
