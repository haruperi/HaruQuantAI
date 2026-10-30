import { ResultsChart } from '../ResultsCharts';
import type { ResultDocument } from '../resultsModel';
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
