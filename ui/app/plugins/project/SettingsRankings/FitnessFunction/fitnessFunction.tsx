import { SqdFieldset, SqdSelect } from '../../ProjectWorkbench/settings/SettingsControls';
import { fitnessMethods } from '../../ProjectWorkbench/settings/sharedSettingsFixtures';
import type { RankingController } from '../RankingCtrl';

type FitnessFunctionProps = Pick<RankingController, 'state' | 'patch' | 'fitness'>;

/** Hook-free fitness view; shared method state remains in the mounted parent. */
export function FitnessFunction({ state, patch, fitness }: FitnessFunctionProps) {
  const { method, setMethod, selectCriterion, removeCriterion, addCriterion } = fitness;
  return (
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
                onChange={key => selectCriterion(state, patch, index, key)}
                options={fitnessMethods.slice(1).map(m => ({ value: m.value, label: m.label }))}
                width={200}
              />
              <button
                type="button"
                className="sqd-cc-link"
                aria-label="Remove criterion"
                onClick={() => removeCriterion(state, patch, index)}
              >
                &times;
              </button>
            </div>
          ))}
          <button
            type="button"
            className="sqd-link-button"
            onClick={() => addCriterion(state, patch)}
          >
            + Add criterion
          </button>
        </div>
      </SqdFieldset>
  );
}
