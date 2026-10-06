import { SqrDropdown } from '../../ProjectWorkbench/results/ResultsChrome';
import { benchmarkNormalizations, type EquityChartFilter } from '../../ProjectWorkbench/results/resultsFixtures';
import { useBenchmark } from './BenchmarkCtrl';

export interface BenchmarkProps { filter: EquityChartFilter; set: <K extends keyof EquityChartFilter>(key: K, value: EquityChartFilter[K]) => void }
export function Benchmark({ filter, set }: BenchmarkProps) {
  const { benchOpen, setBenchOpen } = useBenchmark();
  return (
          <div className="sqr-benchmark-dd">
            <button type="button" className={`sqd-btn sqr-benchmark-btn${benchOpen ? ' open' : ''}`} onClick={() => setBenchOpen(v => !v)}>
              Benchmark: {filter.benchmarkOn ? 'On' : 'Off'}
            </button>
            <SqrDropdown open={benchOpen} onClose={() => setBenchOpen(false)} className="sqr-benchmark-menu">
              <table className="sqr-benchmark-table">
                <tbody>
                  <tr>
                    <td>
                      <label><input type="checkbox" checked={filter.benchmarkOn} onChange={e => set("benchmarkOn", e.target.checked)}/> Benchmark</label>
                    </td>
                    <td>
                      <input type="text" className="sqd-input sqr-text-input" aria-label="Benchmark symbol" value={filter.benchmarkSymbol} onChange={e => set('benchmarkSymbol', e.target.value)} style={{ width: 200 }}/>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <label>Normalization</label>
                    </td>
                    <td>
                      <span className="sqd-select" style={{ width: 200 }}>
                        <span>
                          {benchmarkNormalizations.find(n => n.value === filter.benchmarkNormalization)
            ?.label ?? filter.benchmarkNormalization}
                        </span>
                        <select aria-label="Normalization" value={filter.benchmarkNormalization} onChange={e => set('benchmarkNormalization', e.target.value)}>
                          {benchmarkNormalizations.map(n => (<option key={n.value} value={n.value}>{n.label}</option>))}
                        </select>
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div className="sqr-benchmark-text">
                <span>
                  Normalization means that we&apos;ll recompute real performance of
                  benchmark asset as if it would have the same exposure / drawdown as
                  your strategy.
                </span>
                <br />
                <span>
                  This allows you to compare how would the benchmark look like with the
                  same risk or invested capital in time.
                </span>
                <br />
                <a role="button" tabIndex={0} href="https://strategyquant.com/doc/strategyquant/results-equity-chart/" target="_blank" rel="noreferrer">
                  Learn more
                </a>
              </div>
            </SqrDropdown>
          </div>
);
}
