import { useState } from 'react';
import { SqdCheckbox, SqdFieldset, SqdSelect, SqdSlider, SqdSpinner } from './SettingsControls';
import { geneticOptionsDefaults, type GeneticOptionsState } from './settingsFixtures';

/** "Genetic options" tab (donor evidence retained target UI; current donor equivalence unverified). */
export function GeneticOptionsTab() {
  const [restartType, setRestartType] = useState('bestInIsland');
  const [conditions, setConditions] = useState([{ metric: 'Net profit', comparison: '>', value: '0' }]);
  const [state, setState] = useState<GeneticOptionsState>(geneticOptionsDefaults);
  const patch = (part: Partial<GeneticOptionsState>) => setState(current => ({ ...current, ...part }));

  return (
    <div id="genetic-options" className="sqd-tab-content">
      <div className="sqd-cols">
        <SqdFieldset legend="Genetic options">
          <div className="sqd-labeled-spinner">
            <label className="sqd-label">Max # of Generations</label>
            <SqdSpinner ariaLabel="Max generations" value={state.maxGenerations} min={1} max={100000} step={10} onChange={maxGenerations => patch({ maxGenerations })} />
          </div>
          <div className="sqd-labeled-spinner">
            <label className="sqd-label">Population Size (per island)</label>
            <SqdSpinner ariaLabel="Population size" value={state.populationSize} min={5} max={50000} step={10} onChange={populationSize => patch({ populationSize })} />
          </div>
          <div className="sqd-labeled-slider">
            <label className="sqd-label">Crossover Probability</label>
            <SqdSlider ariaLabel="Crossover probability" value={state.crossoverProbability} min={0} max={100} postfix="%" onChange={crossoverProbability => patch({ crossoverProbability })} />
          </div>
          <div className="sqd-labeled-slider">
            <label className="sqd-label">Mutation Probability</label>
            <SqdSlider ariaLabel="Mutation probability" value={state.mutationProbability} min={0} max={100} postfix="%" onChange={mutationProbability => patch({ mutationProbability })} />
          </div>
        </SqdFieldset>

        <SqdFieldset legend="Islands options">
          <div className="sqd-labeled-spinner">
            <label className="sqd-label">Islands (separate evolution)</label>
            <SqdSpinner ariaLabel="Islands" value={state.islands} min={1} max={100} onChange={islands => patch({ islands })} />
          </div>
          <div className="sqd-labeled-slider">
            <label className="sqd-label">Migrate every Xth generation, X =</label>
            <SqdSlider ariaLabel="Migration modulo" value={state.migrationModulo} min={3} max={100} onChange={migrationModulo => patch({ migrationModulo })} />
          </div>
          <div className="sqd-labeled-slider">
            <label className="sqd-label">Population migration rate</label>
            <SqdSlider ariaLabel="Migration rate" value={state.migrationRate} min={0} max={20} postfix="%" onChange={migrationRate => patch({ migrationRate })} />
          </div>
        </SqdFieldset>
      </div>

      <div className="sqd-cols">
        <SqdFieldset legend="Initial population generation">
          <label className="sqd-label">Initial population size required: {state.populationSize * state.islands}</label>
          <SqdCheckbox checked={state.useInitialPopulationDatabank} onChange={useInitialPopulationDatabank => patch({ useInitialPopulationDatabank })}>
            Use strategies from Initial population databank as evolution start
          </SqdCheckbox>
          <p className="sqd-gen-help">
            Note - initial strategies from databank are not filtered.<br />
            If not used or not enough, the rest will be generated.
          </p>
          <div className="sqd-labeled-slider">
            <label className="sqd-label">Generated decimation coefficient</label>
            <SqdSlider ariaLabel="Decimation coefficient" value={state.decimationCoef} min={1} max={10} onChange={decimationCoef => patch({ decimationCoef })} />
          </div>
          <p className="sqd-gen-help">
            Decimation means that there will be X-times more strategies (that pass filters) generated than required, and from these the best will be chosen.
          </p>
        </SqdFieldset>

        <SqdFieldset legend="Filter generated initial population">
          <p className="sqd-gen-help">Only strategies that fulfill the conditions below will be accepted</p>
          <div className="sqd-cond-grid-demo" aria-label="Initial population filter conditions (demo)">
            <div className="sqd-cond-grid-head"><span>Left side</span><span>Comparison</span><span>Right side</span></div>
            {conditions.map((c,i) => <div className="sqd-cond-grid-row" key={i}>
              <select aria-label={`Filter metric ${i+1}`} value={c.metric} onChange={e => setConditions(items => items.map((item,j) => i===j ? {...item, metric:e.target.value} : item))}>{['Net profit','Number of trades','Drawdown'].map(v=><option key={v}>{v}</option>)}</select>
              <select aria-label={`Filter comparison ${i+1}`} value={c.comparison} onChange={e => setConditions(items => items.map((item,j) => i===j ? {...item, comparison:e.target.value} : item))}>{['>','<','>=','<='].map(v=><option key={v}>{v}</option>)}</select>
              <input aria-label={`Filter value ${i+1}`} value={c.value} onChange={e => setConditions(items => items.map((item,j) => i===j ? {...item, value:e.target.value} : item))}/>
              <button type="button" aria-label={`Remove filter ${i+1}`} onClick={()=>setConditions(items=>items.filter((_,j)=>j!==i))}>&times;</button>
            </div>)}
            <button type="button" className="sqd-link-button sqd-cond-add" onClick={()=>setConditions(items=>[...items,{metric:"Net profit",comparison:">",value:"0"}])}>+ Add condition</button>
          </div>
        </SqdFieldset>
      </div>

      <div className="sqd-cols">
        <SqdFieldset legend={'"Fresh blood"'}>
          <SqdCheckbox checked={state.freshBloodReplaceSimilar} onChange={freshBloodReplaceSimilar => patch({ freshBloodReplaceSimilar })}>
            Detect same strategies in population and replace them with newly generated ones
          </SqdCheckbox>
          <div className="sqd-inline-controls">
            <SqdCheckbox checked={state.freshBloodWeakestPct > 0} onChange={checked => patch({ freshBloodWeakestPct: checked ? 10 : 0 })}>Replace</SqdCheckbox>
            <SqdSelect
              ariaLabel="Weakest percent"
              value={String(state.freshBloodWeakestPct)}
              onChange={v => patch({ freshBloodWeakestPct: Number(v) })}
              options={[5, 10, 15, 20, 25, 30].map(v => ({ value: String(v), label: String(v) }))}
              width={70}
            />
            <label className="sqd-label">%</label>
            <label className="sqd-label">of weakest strategies with newly generated every</label>
            <SqdSpinner ariaLabel="Weakest generations" value={state.freshBloodWeakestGenerations} min={1} max={500} onChange={freshBloodWeakestGenerations => patch({ freshBloodWeakestGenerations })} />
            <label className="sqd-label">generation(s)</label>
          </div>
          <SqdCheckbox checked={state.showLastGenerationDatabank} onChange={showLastGenerationDatabank => patch({ showLastGenerationDatabank })}>
            Show last generation databank - for island #1 only
          </SqdCheckbox>
        </SqdFieldset>

        <SqdFieldset legend="Evolution management">
          <SqdCheckbox checked={state.restartOnFinish} onChange={restartOnFinish => patch({ restartOnFinish })}>
            Start again when finished (continuous repeating evolution)
          </SqdCheckbox>
          <div className="sqd-inline-controls">
            <SqdCheckbox checked={state.restartOnStagnation} onChange={restartOnStagnation => patch({ restartOnStagnation })}>Restart evolution if fitness of</SqdCheckbox>
            <SqdSelect
              ariaLabel="Fitness restart type"
              value={restartType}
              onChange={setRestartType}
              options={[{ value: 'bestInIsland', label: 'best strategy in island' }, { value: 'average', label: 'average of population' }]}
              width={190}
            />
            <label className="sqd-label">stagnates for</label>
            <SqdSpinner ariaLabel="Stagnation generations" value={state.stagnationGenerations} min={3} max={500} onChange={stagnationGenerations => patch({ stagnationGenerations })} />
            <label className="sqd-label">generation(s)</label>
          </div>
        </SqdFieldset>
      </div>
    </div>
  );
}
