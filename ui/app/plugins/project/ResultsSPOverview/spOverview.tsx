import { ResultsChart } from '../ProjectWorkbench/results/ResultsCharts';
import type { ResultDocument } from '../ProjectWorkbench/results/resultsModel';
import { SqdCheckbox } from '../ProjectWorkbench/settings/SettingsControls';
import { useSPOverview } from './SPOverviewCtrl';
import { SPOverviewStats } from './directives/spOverviewStats/spOverviewStats';

export function SpOverviewTab({ result }: {
    result: ResultDocument | null;
}) {
    const { showAll, setShowAll } = useSPOverview();
    return (<div className="sqr-tab">
      <div className="sqr-content sqr-sp-content">
        <SPOverviewStats result={result}/>
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
