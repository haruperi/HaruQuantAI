import { ResultsChart } from '../ProjectWorkbench/results/ResultsCharts';
import { type ResultDocument } from '../ProjectWorkbench/results/resultsModel';
import { useEquityChart } from './EquityChartCtrl';
import { Benchmark } from './benchmark/Benchmark';
import { Menu, RefreshCw } from 'lucide-react';
import { ResultsToolbar, SqrDropdown, SegmentedButtons } from '../ProjectWorkbench/results/ResultsChrome';
import { SqdCheckbox } from '../ProjectWorkbench/settings/SettingsControls';
/** Equity chart tab: X Axis, Benchmark, refresh, Subcharts settings, empty state. */
export function EquityChartTab({ result }: {
    result: ResultDocument | null;
}) {
    const { dataKey, setDataKey, direction, setDirection, sampleType, setSampleType, filter, set, settingsOpen, setSettingsOpen, revision, setRevision, snapshot, xAxisIsTime } = useEquityChart();
    return (<div className="sqr-tab">
      <div className="sqr-toolbar-row">
        <ResultsToolbar dataKey={dataKey} dataItems={result?.markets} onDataChange={setDataKey} direction={direction} sampleType={sampleType} onDirectionChange={setDirection} onSampleTypeChange={setSampleType}>
          <label>X Axis</label>
          <SegmentedButtons ariaLabel="X Axis" options={[
            { value: 'trade' as const, label: 'Trade' },
            { value: 'time' as const, label: 'Time' },
        ]} value={filter.xaxis} onChange={v => set('xaxis', v)}/>
          <Benchmark filter={filter} set={set}/>
          <button type="button" className="sqd-btn sqr-icon-btn" title="Refresh chart" aria-label="Refresh chart" onClick={() => setRevision(v => v + 1)}>
            <RefreshCw size={12}/>
          </button>
          <div className="sqr-settings-dd">
            <button type="button" className={`sqd-btn sqr-icon-btn${settingsOpen ? ' open' : ''}`} title="Settings" aria-label="Chart settings" onClick={() => setSettingsOpen(v => !v)}>
              <Menu size={12}/>
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
                          <SegmentedButtons ariaLabel="Drawdown" options={[
            { value: 10, label: 'Money' },
            { value: 20, label: 'Pct' },
            { value: 30, label: 'Pips' },
            { value: 40, label: 'Open $' },
            { value: 50, label: 'Open %' },
            { value: 0, label: 'Off' },
        ]} value={filter.drawdown} onChange={v => set('drawdown', v)}/>
                        </td>
                      </tr>
                      <tr>
                        <td><label>Volume</label></td>
                        <td>
                          <SegmentedButtons ariaLabel="Volume" options={[
            { value: '5', label: 'Auto' },
            { value: '2', label: 'Size' },
            { value: '1', label: 'Money' },
            { value: '0', label: 'Off' },
        ]} value={filter.volume} onChange={v => set('volume', v)}/>
                        </td>
                      </tr>
                      <tr>
                        <td><label>Daily chart</label></td>
                        <td>
                          {xAxisIsTime ? (<SqdCheckbox checked={filter.dailychart} onChange={v => set('dailychart', v)}>
                              <span className="sqr-visually-hidden">Daily chart</span>
                            </SqdCheckbox>) : (<span className="sqr-equity-hlp">(only for X-Axis = Time)</span>)}
                        </td>
                      </tr>
                      <tr>
                        <td><label>Volatility (ATR)</label></td>
                        <td>
                          {xAxisIsTime ? (<SqdCheckbox checked={filter.volatility} onChange={v => set('volatility', v)}>
                              <span className="sqr-visually-hidden">Volatility (ATR)</span>
                            </SqdCheckbox>) : (<span className="sqr-equity-hlp">(only for X-Axis = Time)</span>)}
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
                          <SegmentedButtons ariaLabel="Equity markers" options={[
            { value: 'daily', label: 'Daily' },
            { value: 'maemfe', label: 'MAE/MFE' },
            { value: 'off', label: 'Off' },
        ]} value={filter.equity} onChange={v => set('equity', v)}/>
                        </td>
                      </tr>
                      <tr>
                        <td><label>Stagnation</label></td>
                        <td>
                          <SegmentedButtons ariaLabel="Stagnation" options={[
            { value: 'full' as const, label: 'Full' },
            { value: 'in' as const, label: 'IS' },
            { value: 'out' as const, label: 'OOS' },
            { value: 0, label: 'Off' },
        ]} value={filter.stagnation} onChange={v => set('stagnation', v)}/>
                        </td>
                      </tr>
                      <tr>
                        <td><label>Stagnation V2</label></td>
                        <td>
                          <SegmentedButtons ariaLabel="Stagnation V2" options={[
            { value: 'full' as const, label: 'Full' },
            { value: 'in' as const, label: 'IS' },
            { value: 'out' as const, label: 'OOS' },
            { value: 0, label: 'Off' },
        ]} value={filter.stagnationV2} onChange={v => set('stagnationV2', v)}/>
                        </td>
                      </tr>
                      <tr>
                        <td><label>Points</label></td>
                        <td>
                          <SegmentedButtons ariaLabel="Points" options={[
            { value: 'all', label: 'All' },
            { value: 'grow', label: 'Grow' },
            { value: 'off', label: 'Off' },
        ]} value={filter.points} onChange={v => set('points', v)}/>
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
        {result ? <><span className="sqr-visually-hidden" role="status">Chart revision {revision}</span><ResultsChart key={revision} points={filter.points} crosshair={filter.crosshair} trendline={filter.trendline} markers={filter.equity} stagnation={filter.stagnation} stagnationV2={filter.stagnationV2} values={snapshot.equity} title={`Equity / ${filter.xaxis === 'time' ? 'Time' : 'Trade'} / ${dataKey}`} benchmark={filter.xaxis === 'time' && filter.benchmarkOn}/>{filter.drawdown > 0 && <ResultsChart values={snapshot.drawdown} title={`Drawdown / ${filter.drawdown === 20 ? "Percent" : filter.drawdown === 30 ? "Pips" : "Money"}`} bars/>}{filter.volume !== '0' && <ResultsChart values={[1, 2, 1, 3, 2, 1, 2, 3]} title={`Volume / ${filter.volume === '1' ? 'Money' : filter.volume === '2' ? 'Size' : 'Auto'}`} bars/>}{filter.dailychart && xAxisIsTime && <ResultsChart values={snapshot.equity} title="Daily equity"/>}{filter.volatility && xAxisIsTime && <ResultsChart values={[12, 18, 16, 20, 14, 17]} title="Volatility (ATR)"/>}</> : <label className="sqr-info-label">No strategy selected.</label>}
      </div>
    </div>);
}
