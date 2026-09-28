import { useState } from 'react';
import { Modal } from '../../../components/ui';
import { actionsClient, type DeleteResult } from './actionsClient';
import './actions.css';

export function getDeleteConfirmMessage(symbols: string[]): string {
  if (symbols.length === 0) {
    return 'No symbols selected.';
  }
  if (symbols.length === 1) {
    return `Do you want to remove symbol '${symbols[0]}' or only clear its data ?`;
  }
  return `Do you want to remove selected symbols (${symbols.length}) or only clear their data ?`;
}

export function formatDeleteCompletion(
  result: DeleteResult,
  mode: 'remove' | 'clear',
): string {
  if (result?.success !== true) {
    throw new Error('Dataset deletion did not succeed.');
  }
  const count = result.deletedCount ?? result.affected;
  if (typeof count !== 'number' || !Number.isInteger(count) || count < 0) {
    throw new Error('Invalid dataset deletion response.');
  }
  const deleted = result.deleted ?? [];
  if (!Array.isArray(deleted) || deleted.some(symbol => typeof symbol !== 'string')) {
    throw new Error('Invalid dataset deletion response.');
  }
  const verb = mode === 'remove' ? 'Deleted' : 'Cleared data for';
  const symbols = deleted.length ? `: ${deleted.join(', ')}` : '';
  return `${verb} ${count} dataset(s)${symbols}.`;
}

export function MassDeleteDialog({
  selectedSymbols,
  onClose,
  onComplete,
}: {
  selectedSymbols: string[];
  onClose: () => void;
  onComplete: (message: string) => void;
}) {
  const [loading, setLoading] = useState<boolean>(false);
  const [targetMode, setTargetMode] = useState<'remove' | 'clear' | null>(null);
  const [error, setError] = useState<string>('');

  async function handleDelete(mode: 'remove' | 'clear'): Promise<void> {
    if (!selectedSymbols.length) return;
    setLoading(true);
    setTargetMode(mode);
    setError('');
    try {
      const res = await actionsClient.deleteDatasets({
        symbols: selectedSymbols,
        mode,
      });
      onComplete(formatDeleteCompletion(res, mode));
      onClose();
    } catch (exc: any) {
      setError(exc?.message || 'Failed to delete dataset(s)');
    } finally {
      setLoading(false);
      setTargetMode(null);
    }
  }

  const message = getDeleteConfirmMessage(selectedSymbols);

  return (
    <div className="delete-dialog-flow">
      <Modal
        title="Delete data"
        width={530}
        onClose={onClose}
        footer={
          <div className="delete-dialog-actions">
            <button
              type="button"
              className="delete-dialog-close-link"
              onClick={onClose}
              disabled={loading}
            >
              Close
            </button>
            <button
              type="button"
              className="delete-dialog-btn"
              onClick={() => handleDelete('clear')}
              disabled={loading || !selectedSymbols.length}
            >
              {loading && targetMode === 'clear' ? 'Clearing…' : 'Clear data'}
            </button>
            <button
              type="button"
              className="delete-dialog-btn"
              onClick={() => handleDelete('remove')}
              disabled={loading || !selectedSymbols.length}
            >
              {loading && targetMode === 'remove' ? 'Deleting…' : 'Delete'}
            </button>
          </div>
        }
      >
        {error && (
          <p role="alert" className="actions-error" style={{ marginBottom: 12 }}>
            {error}
          </p>
        )}
        <p className="delete-dialog-message">{message}</p>
      </Modal>
    </div>
  );
}
