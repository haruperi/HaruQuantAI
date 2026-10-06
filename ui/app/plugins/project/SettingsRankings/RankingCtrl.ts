import { useState } from 'react';
import { rankingDefaults, type RankingState } from '../ProjectWorkbench/settings/sharedSettingsFixtures';
import { useFitnessFunctionController, type FitnessFunctionController } from './FitnessFunction/FitnessFunctionCtrl';

export interface RankingController {
  state: RankingState;
  patch: (part: Partial<RankingState>) => void;
  stop: RankingState['stopConditionType'];
  fitness: FitnessFunctionController;
}

/** Retained two unconditional state hooks, in their original order. */
export function useRankingController(): RankingController {
  const fitness = useFitnessFunctionController();
  const [state, setState] = useState<RankingState>(rankingDefaults);
  const patch = (part: Partial<RankingState>) => setState(current => ({ ...current, ...part }));
  const stop = state.stopConditionType;

  return { state, patch, stop, fitness };
}
