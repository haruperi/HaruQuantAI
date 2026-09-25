import { useState } from 'react';
import {
  AdditionalConfigPopup,
  GearLink,
  SqdCheckbox,
  SqdFieldset,
  SqdRadio,
  SqdSelect,
  SqdSpinner,
} from './SettingsControls';
import {
  additionalConfigRowIds,
  additionalConfigRowNames,
  describeAdditionalConfig,
  whatToBuildDefaults,
  type AdditionalConfigRowId,
  type WhatToBuildState,
} from './settingsFixtures';

/**
 * The "What to build" settings tab (donor evidence SQX144-EV-000039):
 * the Strategy type radio set with its conditional sub-controls, and the
 * six "Additional build config" rows with gear popups and live description
 * strings. Fixture state only.
 */

export function WhatToBuildTab() {
  const [state, setState] = useState<WhatToBuildState>(whatToBuildDefaults);
  const [popup, setPopup] = useState<AdditionalConfigRowId | null>(null);

  const patch = (part: Partial<WhatToBuildState>) => setState(current => ({ ...current, ...part }));
  const st = state.strategyType;

  return (
    <div id="buildTypeContent" className="sqd-tab-content">
      <SqdFieldset legend="Strategy type">
        <div className="sqd-radio-row">
          <SqdRadio name="StrategyTypeRadio" value="simple" checked={st === 'simple'} onChange={() => patch({ strategyType: 'simple' })}>
            Simple strategy [default]
          </SqdRadio>
          <p className="sqd-radio-help">Simple strategy running on one symbol and timeframe</p>
        </div>

        <div className="sqd-radio-row">
          <SqdRadio name="StrategyTypeRadio" value="multiTf" checked={st === 'multiTf'} onChange={() => patch({ strategyType: 'multiTf' })}>
            Multi-TF or multi-symbol strategy
          </SqdRadio>
          <div className="sqd-multitf-text">
            Strategy looking at main chart and
            <SqdSpinner
              ariaLabel="Additional charts"
              value={state.additionalCharts}
              min={1}
              max={9}
              onChange={additionalCharts => patch({ additionalCharts })}
              disabled={st !== 'multiTf'}
            />
            additional charts. These can be just another timeframes of original chart or totally different symbols/TFs.
            <br />
            It trades only on the main chart.
          </div>
        </div>

        <div className="sqd-radio-row">
          <SqdRadio name="StrategyTypeRadio" value="template" checked={st === 'template'} onChange={() => patch({ strategyType: 'template' })}>
            Strategy from template
          </SqdRadio>
          <div className="sqd-multitf-text">
            <p className="sqd-radio-help" style={{ marginTop: 4 }}>Strategy created from the template</p>
            <span className={`sqd-template-file${st === 'template' ? '' : ' hidden'}`}>{state.templateFile}</span>
            <button type="button" className={`sqd-link-button${st === 'template' ? '' : ' hidden'}`}>Browse</button>
            <button type="button" className={`sqd-link-button${st === 'template' ? '' : ' hidden'}`} title="Reload selected template">
              &#8635; Reload
            </button>
          </div>
        </div>

        <div className="sqd-radio-row">
          <SqdRadio name="StrategyTypeRadio" value="improve" checked={st === 'improve'} onChange={() => patch({ strategyType: 'improve' })}>
            Improve existing strategy
          </SqdRadio>
          <p className="sqd-radio-help">Improve some parts of existing strategy / strategies</p>
          {st === 'improve' && (
            <div className="sqd-improve-options">
              <div className="sqd-radio-row">
                <SqdRadio name="ImproveStrategyRadio" value="strategy" checked={state.improveType === 'strategy'} onChange={() => patch({ improveType: 'strategy' })}>
                  Select strategy file
                </SqdRadio>
                <span className={`sqd-template-file${state.improveType === 'strategy' ? '' : ' hidden'}`}>Strategy 0.1.7.sq4</span>
                <button type="button" className={`sqd-link-button${state.improveType === 'strategy' ? '' : ' hidden'}`}>Browse</button>
              </div>
              <div className="sqd-radio-row">
                <SqdRadio name="ImproveStrategyRadio" value="databank" checked={state.improveType === 'databank'} onChange={() => patch({ improveType: 'databank' })}>
                  Improve all strategies in databank
                </SqdRadio>
                <SqdSelect
                  ariaLabel="Improve databank"
                  value="Initial population"
                  onChange={() => undefined}
                  options={[{ value: 'Initial population', label: 'Initial population' }, { value: 'Results', label: 'Results' }]}
                  width={170}
                />
              </div>
            </div>
          )}
        </div>
      </SqdFieldset>

      <SqdFieldset legend="Additional build config" className="sqd-acp">
        <div className="sqd-acp-wrapper">
          {additionalConfigRowIds.map(row => (
            <div className="sqd-acp-row" key={row}>
              <div className="sqd-acp-title">
                <label className="sqd-label">{additionalConfigRowNames[row]}</label>
                <GearLink title={additionalConfigRowNames[row]} onClick={() => setPopup(row)} />
              </div>
              <div className="sqd-acp-desc">
                <label className="sqd-label">{describeAdditionalConfig(state, row)}</label>
              </div>
            </div>
          ))}
        </div>
      </SqdFieldset>

      {popup !== null && (
        <AdditionalConfigPopup
          setting={additionalConfigRowNames[popup]}
          onHelp={() => window.open('https://strategyquant.com/doc/strategyquant/what-to-build/', '_blank', 'noopener')}
          onClose={() => setPopup(null)}
          onSave={() => setPopup(null)}
        >
          {popup === 'tradingDirections' && <TradingDirectionsEditor state={state} patch={patch} />}
          {popup === 'strategyStyle' && <StrategyStyleEditor state={state} patch={patch} />}
          {popup === 'buildMode' && <BuildModeEditor state={state} patch={patch} />}
          {popup === 'conditions' && <ConditionsEditor state={state} patch={patch} />}
          {popup === 'stopLoss' && <StopLossEditor state={state} patch={patch} />}
          {popup === 'profitTarget' && <ProfitTargetEditor state={state} patch={patch} />}
        </AdditionalConfigPopup>
      )}
    </div>
  );
}

type Patch = (part: Partial<WhatToBuildState>) => void;

function TradingDirectionsEditor({ state, patch }: { state: WhatToBuildState; patch: Patch }) {
  const d = state.tradingDirections;
  return (
    <div>
      <SqdRadio name="td-type" value="both" checked={d.type === 'both'} onChange={() => patch({ tradingDirections: { ...d, type: 'both' } })}>Both (Long &amp; Short)</SqdRadio>
      <SqdRadio name="td-type" value="long" checked={d.type === 'long'} onChange={() => patch({ tradingDirections: { ...d, type: 'long' } })}>Long only</SqdRadio>
      <SqdRadio name="td-type" value="short" checked={d.type === 'short'} onChange={() => patch({ tradingDirections: { ...d, type: 'short' } })}>Short only</SqdRadio>
      <div className="sqd-acp-sep" />
      <SqdCheckbox checked={d.entrySymmetry} onChange={entrySymmetry => patch({ tradingDirections: { ...d, entrySymmetry } })}>Entry symmetry (short rules mirror long)</SqdCheckbox>
      <SqdCheckbox checked={d.exitSymmetry} onChange={exitSymmetry => patch({ tradingDirections: { ...d, exitSymmetry } })}>Exit symmetry</SqdCheckbox>
    </div>
  );
}

function StrategyStyleEditor({ state, patch }: { state: WhatToBuildState; patch: Patch }) {
  const s = state.strategyStyle;
  return (
    <div>
      <SqdRadio name="ss-type" value="sq4" checked={s.type === 'sq4'} onChange={() => patch({ strategyStyle: { ...s, type: 'sq4' } })}>SQX Signals</SqdRadio>
      <SqdRadio name="ss-type" value="sq4Fuzzy" checked={s.type === 'sq4Fuzzy'} onChange={() => patch({ strategyStyle: { ...s, type: 'sq4Fuzzy' } })}>SQX Signals with Fuzzy Logic</SqdRadio>
      {s.type === 'sq4Fuzzy' && (
        <div className="sqd-inline-controls">
          <label className="sqd-label">True conditions:</label>
          <SqdSpinner ariaLabel="Min true percent" value={s.minTrue} min={0} max={100} onChange={minTrue => patch({ strategyStyle: { ...s, minTrue } })} />
          <span className="sqd-dash">-</span>
          <SqdSpinner ariaLabel="Max true percent" value={s.maxTrue} min={0} max={100} onChange={maxTrue => patch({ strategyStyle: { ...s, maxTrue } })} />
          <label className="sqd-label">%</label>
        </div>
      )}
      <SqdRadio name="ss-type" value="sq3" checked={s.type === 'sq3'} onChange={() => patch({ strategyStyle: { ...s, type: 'sq3' } })}>Old SQ3 architecture</SqdRadio>
    </div>
  );
}

function BuildModeEditor({ state, patch }: { state: WhatToBuildState; patch: Patch }) {
  const b = state.buildMode;
  return (
    <div>
      <SqdRadio name="bm-type" value="genetic-evolution" checked={b.generationType === 'genetic-evolution'} onChange={() => patch({ buildMode: { ...b, generationType: 'genetic-evolution' } })}>Genetic evolution</SqdRadio>
      <SqdRadio name="bm-type" value="random-generation" checked={b.generationType === 'random-generation'} onChange={() => patch({ buildMode: { ...b, generationType: 'random-generation' } })}>Random generation</SqdRadio>
      <div className="sqd-acp-sep" />
      <div className="sqd-labeled-spinner">
        <label className="sqd-label">Population size (per island)</label>
        <SqdSpinner ariaLabel="Population size" value={b.population} min={5} max={50000} step={10} onChange={population => patch({ buildMode: { ...b, population } })} />
      </div>
      <div className="sqd-labeled-spinner">
        <label className="sqd-label">Max generations</label>
        <SqdSpinner ariaLabel="Max generations" value={b.maxGenerations} min={1} max={100000} step={10} onChange={maxGenerations => patch({ buildMode: { ...b, maxGenerations } })} />
      </div>
      <div className="sqd-labeled-spinner">
        <label className="sqd-label">Islands</label>
        <SqdSpinner ariaLabel="Islands" value={b.islands} min={1} max={100} onChange={islands => patch({ buildMode: { ...b, islands } })} />
      </div>
      <SqdCheckbox checked={b.restartOnFinish} onChange={restartOnFinish => patch({ buildMode: { ...b, restartOnFinish } })}>Start again when finished (continuous repeating evolution)</SqdCheckbox>
    </div>
  );
}

function ConditionsEditor({ state, patch }: { state: WhatToBuildState; patch: Patch }) {
  const c = state.conditions;
  return (
    <div>
      <div className="sqd-inline-controls">
        <label className="sqd-label">Number of conditions:</label>
        <SqdSpinner ariaLabel="Min conditions" value={c.minConditions} min={0} max={20} onChange={minConditions => patch({ conditions: { ...c, minConditions } })} />
        <span className="sqd-dash">-</span>
        <SqdSpinner ariaLabel="Max conditions" value={c.maxConditions} min={0} max={20} onChange={maxConditions => patch({ conditions: { ...c, maxConditions } })} />
      </div>
      <div className="sqd-labeled-spinner">
        <label className="sqd-label">Max lookback period</label>
        <SqdSpinner ariaLabel="Max lookback period" value={c.maxLookback} min={1} max={500} onChange={maxLookback => patch({ conditions: { ...c, maxLookback } })} />
      </div>
      <div className="sqd-inline-controls">
        <label className="sqd-label">Indicator periods:</label>
        <SqdSpinner ariaLabel="Min indicator period" value={c.minPeriod} min={1} max={500} onChange={minPeriod => patch({ conditions: { ...c, minPeriod } })} />
        <span className="sqd-dash">-</span>
        <SqdSpinner ariaLabel="Max indicator period" value={c.maxPeriod} min={1} max={500} onChange={maxPeriod => patch({ conditions: { ...c, maxPeriod } })} />
      </div>
    </div>
  );
}

function StopLossEditor({ state, patch }: { state: WhatToBuildState; patch: Patch }) {
  const s = state.stopLoss;
  return (
    <div>
      <SqdCheckbox checked={s.required} onChange={required => patch({ stopLoss: { ...s, required } })}>Required</SqdCheckbox>
      <div className="sqd-acp-sep" />
      <SqdCheckbox checked={s.fixedPips} onChange={fixedPips => patch({ stopLoss: { ...s, fixedPips } })}>Pips based</SqdCheckbox>
      {s.fixedPips && (
        <div className="sqd-inline-controls">
          <SqdSpinner ariaLabel="SL min pips" value={s.minPips} min={0} max={1000} onChange={minPips => patch({ stopLoss: { ...s, minPips } })} />
          <span className="sqd-dash">-</span>
          <SqdSpinner ariaLabel="SL max pips" value={s.maxPips} min={0} max={1000} onChange={maxPips => patch({ stopLoss: { ...s, maxPips } })} />
          <label className="sqd-label">pips</label>
        </div>
      )}
      <SqdCheckbox checked={s.percent} onChange={percent => patch({ stopLoss: { ...s, percent } })}>Percent based</SqdCheckbox>
      <SqdCheckbox checked={s.atr} onChange={atr => patch({ stopLoss: { ...s, atr } })}>ATR based</SqdCheckbox>
    </div>
  );
}

function ProfitTargetEditor({ state, patch }: { state: WhatToBuildState; patch: Patch }) {
  const p = state.profitTarget;
  return (
    <div>
      <SqdCheckbox checked={p.required} onChange={required => patch({ profitTarget: { ...p, required } })}>Required</SqdCheckbox>
      <SqdCheckbox checked={p.sameAsSl} onChange={sameAsSl => patch({ profitTarget: { ...p, sameAsSl } })}>Use the same ranges as Stop Loss</SqdCheckbox>
      <div className="sqd-acp-sep" />
      <SqdCheckbox checked={p.fixedPips} onChange={fixedPips => patch({ profitTarget: { ...p, fixedPips } })}>Pips based</SqdCheckbox>
      {p.fixedPips && !p.sameAsSl && (
        <div className="sqd-inline-controls">
          <SqdSpinner ariaLabel="PT min pips" value={p.minPips} min={0} max={1000} onChange={minPips => patch({ profitTarget: { ...p, minPips } })} />
          <span className="sqd-dash">-</span>
          <SqdSpinner ariaLabel="PT max pips" value={p.maxPips} min={0} max={1000} onChange={maxPips => patch({ profitTarget: { ...p, maxPips } })} />
          <label className="sqd-label">pips</label>
        </div>
      )}
    </div>
  );
}
