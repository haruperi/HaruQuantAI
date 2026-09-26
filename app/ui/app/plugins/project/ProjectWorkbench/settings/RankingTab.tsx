import { useState } from 'react';
import { SqdFieldset, SqdHelpLink, SqdRadio, SqdSelect, SqdSpinner } from './SettingsControls';
import { fitnessMethods, rankingDefaults, type RankingState } from './sharedSettingsFixtures';

/** "Ranking" tab (donor evidence SQX144-EV-000043). */
export function RankingTab({task='Build'}:{task?:'Build'|'Retest'|'Optimize'}={}) {
  const [method, setMethod] = useState("ComputeFromStrategyResult");
  const [state, setState] = useState<RankingState>(rankingDefaults);
  const patch = (part: Partial<RankingState>) => setState(current => ({ ...current, ...part }));
  const stop = state.stopConditionType;

  return (
    <div id="ranking-settings" className="sqd-tab-content">
      <SqdFieldset legend="Maximum top strategies to store">
        <div className="sqd-labeled-spinner">
          <label className="sqd-label">{task==='Optimize'?'Maximum optimizations to store in databank':'Maximum strategies to store in databank'}</label>
          <SqdSpinner ariaLabel="Maximum strategies" value={state.maxStrategies} min={0} max={1000000} onChange={maxStrategies => patch({ maxStrategies })} />
        </div>
      </SqdFieldset>

      {task==='Build'&&<SqdFieldset legend="Stop generation when">
        <div className="sqd-radio-row">
          <SqdRadio name="StopGenerationRadio" value="never" checked={stop === 'never'} onChange={() => patch({ stopConditionType: 'never' })}>Never</SqdRadio>
        </div>
        <div className="sqd-radio-row">
          <SqdRadio name="StopGenerationRadio" value="passedCount" checked={stop === 'passedCount'} onChange={() => patch({ stopConditionType: 'passedCount' })}>
            Totally
            <SqdSpinner ariaLabel="Passed strategies" value={state.passedStrategies} min={1} max={1000000} disabled={stop !== 'passedCount'} onChange={passedStrategies => patch({ passedStrategies })} />
            strategies (that passed filters) were generated
          </SqdRadio>
        </div>
        <div className="sqd-radio-row">
          <SqdRadio name="StopGenerationRadio" value="databankFull" checked={stop === 'databankFull'} onChange={() => patch({ stopConditionType: 'databankFull' })}>
            Databank is full (reached maximum capacity)
          </SqdRadio>
        </div>
        <div className="sqd-radio-row">
          <SqdRadio name="StopGenerationRadio" value="timeLimit" checked={stop === 'timeLimit'} onChange={() => patch({ stopConditionType: 'timeLimit' })}>
            After
            <SqdSpinner ariaLabel="Days" value={state.days} min={0} disabled={stop !== 'timeLimit'} onChange={days => patch({ days })} />
            days
            <SqdSpinner ariaLabel="Hours" value={state.hours} min={0} max={23} disabled={stop !== 'timeLimit'} onChange={hours => patch({ hours })} />
            hours
            <SqdSpinner ariaLabel="Minutes" value={state.minutes} min={0} max={59} disabled={stop !== 'timeLimit'} onChange={minutes => patch({ minutes })} />
            minutes
          </SqdRadio>
        </div>
      </SqdFieldset>}

      <SqdFieldset legend="Fitness function">
        <div className="sqd-fitness-table" role="table" aria-label="Fitness criteria">
          <div className="sqd-fitness-head" role="row">
            <span role="columnheader">Method</span>
            <span role="columnheader">Criteria</span>
            <span role="columnheader" />
          </div>
          {state.fitnessCriteria.map((criterion, index) => (
            <div className="sqd-fitness-row" role="row" key={index}>
              <SqdSelect
                ariaLabel="Fitness method"
                value={method}
                onChange={setMethod}
                options={fitnessMethods.filter(m => m.value !== 'ReturnDDRatio').map(m => ({ value: m.value, label: m.label }))}
                width={230}
              />
              <SqdSelect
                ariaLabel="Fitness criterion"
                value={criterion.key}
                onChange={key => patch({fitnessCriteria:state.fitnessCriteria.map((c,i)=> i===index ? {key,label:fitnessMethods.find(m=>m.value===key)?.label ?? key} : c)})}
                options={fitnessMethods.slice(1).map(m => ({ value: m.value, label: m.label }))}
                width={200}
              />
              <button
                type="button"
                className="sqd-cc-link"
                aria-label="Remove criterion"
                onClick={() => patch({ fitnessCriteria: state.fitnessCriteria.filter((_, i) => i !== index) })}
              >
                &times;
              </button>
            </div>
          ))}
          <button
            type="button"
            className="sqd-link-button"
            onClick={() => patch({ fitnessCriteria: [...state.fitnessCriteria, { key: 'NetProfit', label: 'Net profit' }] })}
          >
            + Add criterion
          </button>
        </div>
      </SqdFieldset>

      <SqdFieldset legend={<span>Custom analysis <SqdHelpLink url="https://strategyquant.com/doc/strategyquant/custom-analysis" /></span>}>
        <p className="sqd-gen-help">Custom analysis on ranking results (demo — donor surface).</p>
      </SqdFieldset>
    </div>
  );
}
