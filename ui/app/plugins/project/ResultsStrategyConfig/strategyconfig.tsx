import type { ResultDocument } from '../ProjectWorkbench/results/resultsModel';

/** Existing fixed local JSON configuration preview. */
export function StrategyConfigTab({ result }: {
    result: ResultDocument | null;
}) {
    return (<div className="sqr-tab">
      <div className="sqr-content sqr-config-content">
        <label className="sqr-info-label">{result ? `${result.name} — Local configuration preview` : "No strategy selected."}</label>{result && <pre>{JSON.stringify({ engine: "MetaTrader4", symbol: "EURUSD", timeframe: "H1", moneyManagement: "Fixed size 0.1 lots", entry: "Moving average crossover", stopLoss: "40 pips", profitTarget: "80 pips" }, null, 2)}</pre>}
      </div>
    </div>);
}
