import { ResultsChart } from '../../../ProjectWorkbench/results/ResultsCharts';

/** The existing synthetic progress series; no engine chart feed or selectors. */
export function EngineChartPanel({ step }: { step: number }) {
  return <ResultsChart values={[0,2,3,2,5,4,6,8,7,10].slice(0,Math.max(1,step))} title="Task progress / local preview"/>;
}
