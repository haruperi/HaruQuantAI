/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect } from 'react';
import { SQDataAddDialog } from './SQDataAddDialog';
import { useSQData, sqActive } from './sqDataStore';
import { providerLabel, timezones, validateName } from './sqData';

export { providerLabel, timezones, validateName };
export const pluginId = 'sq';
export const pluginName = 'SQ Data';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useSQData();
  useEffect(() => {
    const active = sqActive(state.job?.state);
    onSync('sq', {
      definitions: state.definitions,
      job: state.job,
      storageError: state.storageError,
      active,
    });
  }, [state, onSync]);
  return null;
}

export function Dialogs({ dialog, contextDocument, onClose, onStarted }: any) {
  if (dialog?.id === 'sq-equity-find' || dialog?.id === 'sq-futures-find') {
    return createElement(SQDataAddDialog, { provider: dialog.id === 'sq-equity-find' ? 'equity' : 'futures', contextDocument, onClose, onStarted: () => onStarted('sq') });
  }
  return null;
}

export function advance() {
  useSQData.getState().advance();
}

export function action(act: 'pause' | 'resume' | 'stop') {
  useSQData.getState().action(act);
}
