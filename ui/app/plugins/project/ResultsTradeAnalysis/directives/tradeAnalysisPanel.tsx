import { ResultsChart } from '../../ProjectWorkbench/results/ResultsCharts';

/** Existing repeated synthetic time-category panel. */
export function TradeAnalysisPanel({ title, period }: { title: string; period: number }) {
  return <ResultsChart title={title} values={period === 1 ? [12, 7, 14, 8, 20, 9] : [8, 12, 6, 18, 9, 17]} bars/>;
}
