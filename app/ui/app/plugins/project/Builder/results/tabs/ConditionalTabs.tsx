import { useState } from 'react';
import { ResultsChart, TradesChart } from '../ResultsCharts';
import type { ResultDocument } from '../resultsModel';
export function ConditionalTabs({ id, result }: {
    id: string;
    result: ResultDocument;
}) {
    const [period, setPeriod] = useState('Day');
    const [method, setMethod] = useState('Randomize trades order');
    if(id==='correlation'&&!result.portfolio)return <div className="sqr-tab"><div className="sqr-content">Strategy is not a portfolio.</div></div>;
    return <div className="sqr-tab"><div className="sqr-toolbar">{id === 'monteCarloTests' && <label>Test choice <select value={method} onChange={e => setMethod(e.target.value)}>{['Randomize trades order', 'Randomly skip trades'].map(v => <option key={v}>{v}</option>)}</select></label>}{id === 'correlation' && <label>Correlation by <select value={period} onChange={e => setPeriod(e.target.value)}>{['Hour', 'Day', 'Week', 'Month'].map(p => <option key={p}>{p}</option>)}</select></label>}</div><div className="sqr-content">
 {id === 'correlation' ? <><h3>Portfolio correlation / {period}</h3><table className="sqr-data-table"><thead><tr><th>Market</th><th>EURUSD</th><th>GBPUSD</th></tr></thead><tbody><tr><th>EURUSD</th><td>1.00</td><td>{period === 'Day' ? '0.42' : '0.36'}</td></tr><tr><th>GBPUSD</th><td>{period === 'Day' ? '0.42' : '0.36'}</td><td>1.00</td></tr></tbody></table></> : id === 'stockpicker' ? <table className="sqr-data-table"><thead><tr><th>Date</th><th>Symbol</th><th>Score</th><th>Action</th></tr></thead><tbody>{['AAPL', 'MSFT', 'NVDA'].map((s, i) => <tr key={s}><td>2025.06.03</td><td>{s}</td><td>{90 - i * 10}</td><td>Selected</td></tr>)}</tbody></table> : id === 'tradesOnChart' ? <TradesChart /> : <ResultsChart values={id === 'monteCarloTests' ? (method === 'Randomize trades order' ? [10000, 10200, 10100, 10500, 10800, 10600, 11100, 11800] : [10000, 10100, 10300, 10200, 10600, 10900, 10800, 11600]) : result.equity} title={id === 'monteCarloTests' ? 'Monte Carlo simulations / mock confidence preview' : 'Trades on chart / stored mock data'} benchmark/>}
 {id === 'monteCarloTests' && <table className="sqr-data-table"><thead><tr><th>Confidence level</th><th>Net profit</th><th>Drawdown</th></tr></thead><tbody>{[['Original', '2,700', '180'], ['80%', '2,100', '720'], ['90%', '1,900', '850'], ['95%', '1,650', '980']].map(row => <tr key={row[0]}>{row.map((v, i) => <td key={i}>{v}</td>)}</tr>)}</tbody></table>}
 <p className="sqd-gen-help">Precomputed local UI fixture. No analysis is executed.</p></div></div>;
}
