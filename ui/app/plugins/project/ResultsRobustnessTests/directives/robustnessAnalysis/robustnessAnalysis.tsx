import { ResultsChart } from '../../../ProjectWorkbench/results/ResultsCharts';

/** Existing method-dependent fixture curve and confidence table. */
export function RobustnessAnalysis({ method }: { method: string }) {
  return <><ResultsChart values={(method === 'Randomize trades order' ? [10000, 10200, 10100, 10500, 10800, 10600, 11100, 11800] : [10000, 10100, 10300, 10200, 10600, 10900, 10800, 11600])} title={'Monte Carlo simulations / mock confidence preview'} benchmark/><table className="sqr-data-table"><thead><tr><th>Confidence level</th><th>Net profit</th><th>Drawdown</th></tr></thead><tbody>{[['Original', '2,700', '180'], ['80%', '2,100', '720'], ['90%', '1,900', '850'], ['95%', '1,650', '980']].map(row => <tr key={row[0]}>{row.map((v, i) => <td key={i}>{v}</td>)}</tr>)}</tbody></table></>;
}
