import { useState } from 'react';
import { Menu, RefreshCw } from 'lucide-react';
import { ResultsToolbar, SqrDropdown, SegmentedButtons } from '../ResultsChrome';
import { SqdCheckbox } from '../../settings/SettingsControls';
import {
  benchmarkNormalizations,
  equityChartDefaults,
  type Direction,
  type EquityChartFilter,
  type SampleType,
} from '../resultsFixtures';

/** Equity chart tab: X Axis, Benchmark, refresh, Subcharts settings, empty state. */
export function EquityChartTab() {
  const [direction, setDirection] = useState<Direction>('both');
  const [sampleType, setSampleType] = useState<SampleType>('full');
  const [filter, setFilter] = useState<EquityChartFilter>(equityChartDefaults);
  const [benchOpen, setBenchOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const set = <K extends keyof EquityChartFilter>(key: K, value: EquityChartFilter[K]) =>
    setFilter(f => ({ ...f, [key]: value }));
  const xAxisIsTime = filter.xaxis === 'time';
  return (
    <div className="sqr-tab">
      <div className="sqr-toolbar-row">
        <ResultsToolbar
          direction={direction}
          sampleType={sampleType}
          onDirectionChange={setDirection}
          onSampleTypeChange={setSampleType}
        >
          <label>X Axis</label>
          <SegmentedButtons
            ariaLabel="X Axis"
            options={[
              { value: 'trade' as const, label: 'Trade' },
              { value: 'time' as const, label: 'Time' },
            ]}
            value={filter.xaxis}
            onChange={v => set('xaxis', v)}
          />
          <div className="sqr-benchmark-dd">
            <button
              type="button"
              className={`sqd-btn sqr-benchmark-btn${benchOpen ? ' open' : ''}`}
              onClick={() => setBenchOpen(v => !v)}
            >
              Benchmark: {filter.benchmarkOn ? 'On' : 'Off'}
            </button>
            <SqrDropdown open={benchOpen} onClose={() => setBenchOpen(false)} className="sqr-benchmark-menu">
              <table className="sqr-benchmark-table">
                <tbody>
                  <tr>
                    <td>
                      <label>Benchmark</label>
                    </td>
                    <td>
                      <input
                        type="text"
                        className="sqd-input sqr-text-input"
                        aria-label="Benchmark symbol"
                        value={filter.benchmarkSymbol}
                        onChange={e => set('benchmarkSymbol', e.target.value)}
                        style={{ width: 200 }}
                      />
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
                        <select
                          aria-label="Normalization"
                          value={filter.benchmarkNormalization}
                          onChange={e => set('benchmarkNormalization', e.target.value)}
                        >
                          {benchmarkNormalizations.map(n => (
                            <option key={n.value} value={n.value}>{n.label}</option>
                          ))}
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
                <a role="button" tabIndex={0} onClick={() => setBenchOpen(false)} onKeyDown={e => e.key === 'Enter' && setBenchOpen(false)}>
                  Learn more
                </a>
              </div>
            </SqrDropdown>
          </div>
          <button type="button" className="sqd-btn sqr-icon-btn" title="Refresh chart" aria-label="Refresh chart">
            <RefreshCw size={12} />
          </button>
          <div className="sqr-settings-dd">
            <button
              type="button"
              className={`sqd-btn sqr-icon-btn${settingsOpen ? ' open' : ''}`}
              title="Settings"
              aria-label="Chart settings"
              onClick={() => setSettingsOpen(v => !v)}
            >
              <Menu size={12} />
            </button>
            <SqrDropdown open={settingsOpen} onClose={() => setSettingsOpen(false)} className="sqr-settings-menu">
              <div className="sqr-settings-cols">
                <div className="sqr-settings-col">
                  <h4>Subcharts</h4>
                  <table>
                    <tbody>
                      <tr>
                        <td><label>Drawdown</label></td>
                        <td>
                          <SegmentedButtons
                            ariaLabel="Drawdown"
                            options={[
                              { value: 10, label: 'Money' },
                              { value: 20, label: 'Pct' },
                              { value: 30, label: 'Pips' },
                              { value: 40, label: 'Open $' },
                              { value: 50, label: 'Open %' },
                              { value: 0, label: 'Off' },
                            ]}
                            value={filter.drawdown}
                            onChange={v => set('drawdown', v)}
                          />
                        </td>
                      </tr>
                      <tr>
                        <td><label>Volume</label></td>
                        <td>
                          <SegmentedButtons
                            ariaLabel="Volume"
                            options={[
                              { value: '5', label: 'Auto' },
                              { value: '2', label: 'Size' },
                              { value: '1', label: 'Money' },
                              { value: '0', label: 'Off' },
                            ]}
                            value={filter.volume}
                            onChange={v => set('volume', v)}
                          />
                        </td>
                      </tr>
                      <tr>
                        <td><label>Daily chart</label></td>
                        <td>
                          {xAxisIsTime ? (
                            <SqdCheckbox checked={filter.dailychart} onChange={v => set('dailychart', v)}>
                              <span className="sqr-visually-hidden">Daily chart</span>
                            </SqdCheckbox>
                          ) : (
                            <span className="sqr-equity-hlp">(only for X-Axis = Time)</span>
                          )}
                        </td>
                      </tr>
                      <tr>
                        <td><label>Volatility (ATR)</label></td>
                        <td>
                          {xAxisIsTime ? (
                            <SqdCheckbox checked={filter.volatility} onChange={v => set('volatility', v)}>
                              <span className="sqr-visually-hidden">Volatility (ATR)</span>
                            </SqdCheckbox>
                          ) : (
                            <span className="sqr-equity-hlp">(only for X-Axis = Time)</span>
                          )}
                        </td>
                      </tr>
                      <tr>
                        <td><label>Line</label></td>
                        <td>
                          <SqdCheckbox checked={filter.trendline} onChange={v => set('trendline', v)}>
                            <span className="sqr-visually-hidden">Line</span>
                          </SqdCheckbox>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div className="sqr-settings-col">
                  <h4>Markers</h4>
                  <table>
                    <tbody>
                      <tr>
                        <td><label>Equity</label></td>
                        <td>
                          <SegmentedButtons
                            ariaLabel="Equity markers"
                            options={[
                              { value: 'daily', label: 'Daily' },
                              { value: 'maemfe', label: 'MAE/MFE' },
                              { value: 'off', label: 'Off' },
                            ]}
                            value={filter.equity}
                            onChange={v => set('equity', v)}
                          />
                        </td>
                      </tr>
                      <tr>
                        <td><label>Stagnation</label></td>
                        <td>
                          <SegmentedButtons
                            ariaLabel="Stagnation"
                            options={[
                              { value: 'full' as const, label: 'Full' },
                              { value: 'in' as const, label: 'IS' },
                              { value: 'out' as const, label: 'OOS' },
                              { value: 0, label: 'Off' },
                            ]}
                            value={filter.stagnation}
                            onChange={v => set('stagnation', v)}
                          />
                        </td>
                      </tr>
                      <tr>
                        <td><label>Stagnation V2</label></td>
                        <td>
                          <SegmentedButtons
                            ariaLabel="Stagnation V2"
                            options={[
                              { value: 'full' as const, label: 'Full' },
                              { value: 'in' as const, label: 'IS' },
                              { value: 'out' as const, label: 'OOS' },
                              { value: 0, label: 'Off' },
                            ]}
                            value={filter.stagnationV2}
                            onChange={v => set('stagnationV2', v)}
                          />
                        </td>
                      </tr>
                      <tr>
                        <td><label>Points</label></td>
                        <td>
                          <SegmentedButtons
                            ariaLabel="Points"
                            options={[
                              { value: 'all', label: 'All' },
                              { value: 'grow', label: 'Grow' },
                              { value: 'off', label: 'Off' },
                            ]}
                            value={filter.points}
                            onChange={v => set('points', v)}
                          />
                        </td>
                      </tr>
                      <tr>
                        <td><label>Crosshair</label></td>
                        <td>
                          <SqdCheckbox checked={filter.crosshair} onChange={v => set('crosshair', v)}>
                            <span className="sqr-visually-hidden">Crosshair</span>
                          </SqdCheckbox>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </SqrDropdown>
          </div>
        </ResultsToolbar>
      </div>
      <div className="sqr-content sqr-equity-content">
        <label className="sqr-info-label">No strategy selected.</label>
      </div>
    </div>
  );
}
