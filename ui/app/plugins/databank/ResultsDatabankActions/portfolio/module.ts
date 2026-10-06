import { label as merge, deferAction as deferMerge } from './merge/module';
import { label as split, deferAction as deferSplit } from './split/module';
import { label as mergeWF, deferAction as deferMergeWF } from './mergeWF/module';
import { MOVE_TO_PC_LABEL, requestMoveToPC } from './moveToPC/module';
import { MOVE_TO_PM_LABEL, requestMoveToPM } from './moveToPM/module';

/** Preserve existing menu order and deferred-only portfolio actions. */
export const PORTFOLIO_MENU = [merge, split, mergeWF, MOVE_TO_PC_LABEL, MOVE_TO_PM_LABEL];

export function dispatchPortfolioAction(item: string | undefined, deferred: (label: string) => void): void {
  if (item === merge) return deferMerge(deferred);
  if (item === split) return deferSplit(deferred);
  if (item === mergeWF) return deferMergeWF(deferred);
  if (item === MOVE_TO_PC_LABEL) return requestMoveToPC(deferred);
  if (item === MOVE_TO_PM_LABEL) return requestMoveToPM(deferred);
  deferred(`Portfolio: ${item}`);
}
