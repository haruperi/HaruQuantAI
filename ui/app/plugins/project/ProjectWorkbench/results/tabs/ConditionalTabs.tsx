import { ResultsChart } from '../ResultsCharts';
import type { ResultDocument } from '../resultsModel';
import { ResultsChartTab } from '../../../ResultsChart/module';
import { StockpickerTab } from '../../../ResultsStockpicker/module';
import { PortfolioCorrelationTab, usePortfolioCorrelation } from '../../../ResultsPortfolioCorrelation/module';
import { RobustnessTestsTab, useRobustnessTestsResults } from '../../../ResultsRobustnessTests/module';

/** Preserve unconditional state lifetime while delegating existing branch views. */
export function ConditionalTabs({ id, result }: { id: string; result: ResultDocument }) {
  const { period, setPeriod } = usePortfolioCorrelation();
  const { method, setMethod } = useRobustnessTestsResults();
  if (id === 'correlation') return <PortfolioCorrelationTab result={result} period={period} setPeriod={setPeriod}/>;
  if (id === 'monteCarloTests') return <RobustnessTestsTab method={method} setMethod={setMethod}/>;
  if (id === 'stockpicker') return <StockpickerTab/>;
  if (id === 'tradesOnChart') return <ResultsChartTab/>;
  return <div className="sqr-tab"><div className="sqr-toolbar"/><div className="sqr-content"><ResultsChart values={result.equity} title="Trades on chart / stored mock data" benchmark/><p className="sqd-gen-help">Precomputed local UI fixture. No analysis is executed.</p></div></div>;
}
