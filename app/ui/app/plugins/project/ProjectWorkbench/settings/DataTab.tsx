import { useState } from 'react';
import { SqdFieldset, SqdHelpLink, SqdSelect, SqdTextInput } from './SettingsControls';
import { dataTabDefaults, oosPresets, oosRangePercents, type DataTabState, type OosRange } from './sharedSettingsFixtures';

/**
 * "Data" tab (donor evidence SQX144-EV-000041): the main chart setup editor
 * plus the "Data range parts" fieldset with the five most-used presets and
 * the OOS range rows. Sub-editors (symbol picker cloud) are donor-style
 * fixture selects.
 */
export function DataTab({initialState=dataTabDefaults}: {initialState?:DataTabState} = {}) {
  const [state, setState] = useState<DataTabState>(()=>structuredClone(initialState));
  const [precision, setPrecision] = useState("1");
  const [rangeError, setRangeError] = useState("");
  const [graphShown, setGraphShown] = useState(false);
  const patch = (part: Partial<DataTabState>) => setState(current => ({ ...current, ...part }));
  const percents = oosRangePercents(state.oosRanges);
  const totalDays = Math.round((new Date(state.dateTo).getTime() - new Date(state.dateFrom).getTime()) / 86400000);

  // Local range-editor presentation only, not a backtest sampling algorithm.
  const applyPreset = (title: string) => {
    const from = Date.parse(state.dateFrom.replaceAll('.', '-'));
    const to = Date.parse(state.dateTo.replaceAll('.', '-'));
    if (!Number.isFinite(from) || !Number.isFinite(to) || to <= from) { setRangeError('Enter a valid date range before applying a preset.'); return; }
    const parts = title.split(',').map(p => { const [type, weight] = p.trim().split(':'); return {type: type as OosRange['type'], weight: weight ? Number(weight) : null}; });
    const specified = parts.reduce((total,p) => total+(p.weight??0),0);
    const missing = parts.filter(p=>p.weight===null).length;
    let cursor = 0;
    const format = (percent: number) => new Date(from + (to-from)*percent/100).toISOString().slice(0,10).replaceAll('-','.');
    patch({oosRanges: parts.map(p => { const start=cursor; cursor += p.weight ?? (100-specified)/missing; return {type:p.type,from:format(start),to:format(cursor)}; })});
    setRangeError(''); setGraphShown(true);
  };
  return (
    <span id="builderDataTab" className="sqd-tab-content">
      <SqdFieldset className="sqd-data-setup">
        <div className="sqd-setting-row">
          <label className="sqd-label fixed">Engine</label>
          <SqdSelect
            ariaLabel="Engine"
            value={state.engine}
            onChange={engine => patch({ engine })}
            options={['MetaTrader5 (hedging mode)', 'MetaTrader5 (netting mode)', 'MetaTrader4', 'Tick data (custom)'].map(v => ({ value: v, label: v }))}
            width={210}
          />
        </div>
        <div className="sqd-setting-row">
          <label className="sqd-label fixed">Symbol</label>
          <div className="sqd-setting-right">
            <SqdSelect ariaLabel="Symbol" value={state.symbol} onChange={symbol => patch({ symbol })} options={[{ value: state.symbol, label: state.symbol }]} width={170} />
            <SqdSelect
              ariaLabel="Timeframe"
              value={state.timeframe}
              onChange={timeframe => patch({ timeframe })}
              options={['M5', 'M15', 'M30', 'H1', 'H4', 'D1'].map(v => ({ value: v, label: v }))}
              width={100}
            />
          </div>
        </div>
        <div className="sqd-setting-row">
          <label className="sqd-label fixed">Date range</label>
          <div className="sqd-setting-right">
            <SqdTextInput ariaLabel="Date from" value={state.dateFrom} onChange={dateFrom => patch({ dateFrom })} width={110} />
            <span className="sqd-dash">-</span>
            <SqdTextInput ariaLabel="Date to" value={state.dateTo} onChange={dateTo => patch({ dateTo })} width={110} />
            <label className="sqd-label">({totalDays} days)</label>
          </div>
        </div>
        <div className="sqd-setting-row">
          <label className="sqd-label fixed">Test precision</label>
          <SqdSelect
            ariaLabel="Test precision"
            value={precision}
            onChange={setPrecision}
            options={[{ value: '1', label: 'Selected timeframe only' }, { value: '2', label: '1 minute data' }, { value: '3', label: 'Real ticks' }]}
            width={210}
          />
        </div>
      </SqdFieldset>

      <SqdFieldset legend="Data range parts">
        <SqdHelpLink url="https://strategyquant.com/article/training-validation-test-periods" />
        <div className="sqd-oos-presets">
          Most used configs:
          {oosPresets.map(preset => (
            <button key={preset.id} type="button" className={`sqd-oos-preset oos-${preset.id}`} title={preset.title} aria-label={`Apply preset ${preset.title}`} onClick={() => applyPreset(preset.title)} />
          ))}
        </div>
        {rangeError && <p role="alert">{rangeError}</p>}
        <div className="sqd-oos-body">
          {graphShown && (
            <div className="sqd-oos-graph" aria-label="Data range chart (demo)">
              {state.oosRanges.map((range, i) => (
                <span key={i} className={`sqd-oos-seg type-${range.type.toLowerCase()}`} style={{ flexGrow: percents[i] }} title={`${range.type} ${percents[i]}%`} />
              ))}
            </div>
          )}
          <button type="button" className="sqd-link-button" onClick={() => setGraphShown(!graphShown)}>
            {graphShown ? 'Hide chart' : 'Show chart'}
          </button>
        </div>
        <div className="sqd-oos-ranges">
          {state.oosRanges.map((range, i) => (
            <div className="sqd-oos-range-row" key={i}>
              <SqdSelect
                ariaLabel={`Range ${i + 1} type`}
                value={range.type}
                onChange={type => {
                  const oosRanges = [...state.oosRanges];
                  oosRanges[i] = { ...range, type: type as OosRange['type'] };
                  patch({ oosRanges });
                }}
                options={[{ value: 'IST', label: 'IST - in-sample training' }, { value: 'ISV', label: 'ISV - in-sample validation' }, { value: 'OOS', label: 'OOS - out of sample' }]}
                width={210}
              />
              <SqdTextInput
                ariaLabel={`Range ${i + 1} from`}
                value={range.from}
                onChange={from => {
                  const oosRanges = [...state.oosRanges];
                  oosRanges[i] = { ...range, from };
                  patch({ oosRanges });
                }}
                width={110}
              />
              <SqdTextInput
                ariaLabel={`Range ${i + 1} to`}
                value={range.to}
                onChange={to => {
                  const oosRanges = [...state.oosRanges];
                  oosRanges[i] = { ...range, to };
                  patch({ oosRanges });
                }}
                width={110}
              />
              <label className="sqd-oos-perc">({percents[i]}%)</label>
              <button
                type="button"
                className="sqd-oos-remove"
                aria-label={`Remove range ${i + 1}`}
                onClick={() => patch({ oosRanges: state.oosRanges.filter((_, index) => index !== i) })}
              >
                &times;
              </button>
            </div>
          ))}
          <div className="sqd-oos-add">
            <button type="button" className="sqd-link-button" onClick={() => patch({ oosRanges: [...state.oosRanges, { type: 'OOS', from: state.dateFrom, to: state.dateTo }] })}>
              + Add new part
            </button>
          </div>
        </div>
      </SqdFieldset>
    </span>
  );
}
