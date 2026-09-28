/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect } from 'react';
import { CloneTimezoneDialog } from './CloneTimezoneDialog';
import { ViewAnalyzeDialog } from './ViewAnalyzeDialog';
import { useDataTools, toolsActive } from './dataToolsStore';
import { selectCloneTargets, selectReviewTarget, type ToolTarget } from './dataTools';

export { selectCloneTargets, selectReviewTarget, toolsActive };
export type { ToolTarget };

export const pluginId = 'tools';
export const pluginName = 'Tools';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useDataTools();
  useEffect(() => {
    const active = toolsActive(state.job?.state);
    onSync('tools', {
      definitions: state.definitions,
      job: state.job,
      storageError: state.storageError,
      active,
    });
  }, [state, onSync]);
  return null;
}

export function Dialogs({ cloneTargets, reviewTarget, toolRows, otherDataActive, onClose, onStarted, onReviewClose, onCloneClose }: any) {
  if (cloneTargets) {
    const existingNames = (toolRows ?? []).map((row: any) => row.symbol);
    return createElement(CloneTimezoneDialog, { targets: cloneTargets, existingNames, externalActive: otherDataActive, onClose: onCloneClose || onClose, onStarted: () => onStarted('tools', 'Clone to timezone started (simulation)') });
  }
  if (reviewTarget) {
    const state = useDataTools.getState();
    return createElement(ViewAnalyzeDialog, { target: reviewTarget, externalActive: otherDataActive || toolsActive(state.job?.state), onClose: onReviewClose || onClose });
  }
  return null;
}

export function advance() {
  useDataTools.getState().advance();
}

export function action(act: 'pause' | 'resume' | 'stop') {
  useDataTools.getState().action(act);
}
