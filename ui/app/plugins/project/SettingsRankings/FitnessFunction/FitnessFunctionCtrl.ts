import { useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { fitnessMethods, type RankingState } from '../../ProjectWorkbench/settings/sharedSettingsFixtures';

type PatchRanking = (part: Partial<RankingState>) => void;

export interface FitnessFunctionController {
  method: string;
  setMethod: Dispatch<SetStateAction<string>>;
  selectCriterion: (state: RankingState, patch: PatchRanking, index: number, key: string) => void;
  removeCriterion: (state: RankingState, patch: PatchRanking, index: number) => void;
  addCriterion: (state: RankingState, patch: PatchRanking) => void;
}

/** Parent invokes this hook unconditionally to retain method selection lifetime. */
export function useFitnessFunctionController(): FitnessFunctionController {
  const [method, setMethod] = useState("ComputeFromStrategyResult");
  const selectCriterion = (state: RankingState, patch: PatchRanking, index: number, key: string) => patch({fitnessCriteria:state.fitnessCriteria.map((c,i)=> i===index ? {key,label:fitnessMethods.find(m=>m.value===key)?.label ?? key} : c)});
  const removeCriterion = (state: RankingState, patch: PatchRanking, index: number) => patch({ fitnessCriteria: state.fitnessCriteria.filter((_, i) => i !== index) });
  const addCriterion = (state: RankingState, patch: PatchRanking) => patch({ fitnessCriteria: [...state.fitnessCriteria, { key: 'NetProfit', label: 'Net profit' }] });
  return { method, setMethod, selectCriterion, removeCriterion, addCriterion };
}
