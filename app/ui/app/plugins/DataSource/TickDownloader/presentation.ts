/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect } from 'react';
import { TickDownloaderImportDialog } from './TickDownloaderImportDialog';
import { useTickDownloader } from './tickDownloaderStore';

export const pluginId = 'td';
export const pluginName = 'TickDownloader';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useTickDownloader();
  useEffect(() => {
    const active = state.job?.state === 'running' || state.job?.state === 'paused';
    onSync('td', {
      definitions: state.definitions,
      job: state.job,
      storageError: state.storageError,
      active,
    });
  }, [state, onSync]);
  return null;
}

export function Dialogs({ dialog, onClose, onStarted }: any) {
  if (dialog?.id === 'tickdownloader-import') {
    return createElement(TickDownloaderImportDialog, { onClose, onStarted: () => onStarted('td', 'TickDownloader import started (simulation)') });
  }
  return null;
}

export function advance() {
  useTickDownloader.getState().advance();
}

export function action(act: 'pause' | 'resume' | 'stop') {
  useTickDownloader.getState().action(act);
}
