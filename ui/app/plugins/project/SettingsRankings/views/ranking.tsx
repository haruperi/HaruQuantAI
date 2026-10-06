import { useRankingController } from '../RankingCtrl';
import { FitnessFunction } from '../FitnessFunction/fitnessFunction';
import { SqdFieldset, SqdHelpLink, SqdRadio, SqdSpinner } from '../../ProjectWorkbench/settings/SettingsControls';

/** "Ranking" tab (donor evidence SQX144-EV-000043). */
export function RankingTab({task='Build'}:{task?:'Build'|'Retest'|'Optimize'}={}) {
  const { state, patch, stop, fitness } = useRankingController();

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

      <FitnessFunction state={state} patch={patch} fitness={fitness} />

      <SqdFieldset legend={<span>Custom analysis <SqdHelpLink url="https://strategyquant.com/doc/strategyquant/custom-analysis" /></span>}>
        <p className="sqd-gen-help">Custom analysis on ranking results (demo — donor surface).</p>
      </SqdFieldset>
    </div>
  );
}
