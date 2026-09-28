import { useState, type ChangeEvent } from 'react';
import { Button, Field, Modal, TextInput } from '../../../components/ui';
import { actionsClient, downloadBlob } from './actionsClient';
import './actions.css';

export function SaveDefinitionsDialog({
  selectedSymbols,
  onClose,
  onComplete,
}: {
  selectedSymbols: string[];
  onClose: () => void;
  onComplete: (message: string) => void;
}) {
  const [scope, setScope] = useState<'all' | 'selected'>('all');
  const [filename, setFilename] = useState<string>('Data.json');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  async function handleSave(): Promise<void> {
    setLoading(true);
    setError('');
    try {
      const symbolsToSave = scope === 'selected' && selectedSymbols.length ? selectedSymbols : undefined;
      const res = await actionsClient.saveDefinitions({ symbols: symbolsToSave });
      if (res.content) {
        downloadBlob(filename, res.content, 'application/json');
      }
      onComplete(`Saved ${res.datasetsCount} dataset(s) and ${res.instrumentsCount} instrument(s) to ${filename}.`);
      onClose();
    } catch (exc: any) {
      setError(exc?.message || 'Failed to save definitions');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="actions-flow">
      <Modal
        title="Save Dataset Definitions"
        width={500}
        onClose={onClose}
        footer={
          <>
            <Button onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button className="primary" onClick={handleSave} disabled={loading}>
              {loading ? 'Saving…' : 'Save JSON'}
            </Button>
          </>
        }
      >
        {error && (
          <p role="alert" className="actions-error">
            {error}
          </p>
        )}
        <fieldset>
          <legend>Export Scope</legend>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="radio"
                name="save-scope"
                checked={scope === 'all'}
                onChange={() => setScope('all')}
              />
              <span>Save all dataset definitions &amp; instruments</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="radio"
                name="save-scope"
                checked={scope === 'selected'}
                disabled={!selectedSymbols.length}
                onChange={() => setScope('selected')}
              />
              <span>Save only selected datasets ({selectedSymbols.length})</span>
            </label>
          </div>
          <Field label="File Name">
            <TextInput value={filename} onChange={(e: ChangeEvent<HTMLInputElement>) => setFilename(e.target.value)} />
          </Field>
        </fieldset>
      </Modal>
    </div>
  );
}
