import { useState } from 'react';
import { Button, Modal } from '../../../components/ui';
import { actionsClient } from './actionsClient';
import './actions.css';

export function LoadDefinitionsDialog({
  onClose,
  onComplete,
}: {
  onClose: () => void;
  onComplete: (message: string) => void;
}) {
  const [fileContent, setFileContent] = useState<string>('');
  const [fileName, setFileName] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setError('');
    const reader = new FileReader();
    reader.onload = e => {
      const text = e.target?.result as string;
      setFileContent(text);
    };
    reader.onerror = () => {
      setError('Failed to read file from disk');
    };
    reader.readAsText(file);
  }

  async function handleLoad(): Promise<void> {
    if (!fileContent) {
      setError('Please select a JSON backup file to load');
      return;
    }
    setLoading(true);
    setError('');
    try {
      let parsed: any;
      try {
        parsed = JSON.parse(fileContent);
      } catch {
        throw new Error('Selected file is not valid JSON');
      }

      const definitions = parsed.datasets || parsed.definitions || [];
      const instruments = parsed.instruments || [];

      const res = await actionsClient.loadDefinitions({
        definitions,
        instruments,
      });

      onComplete(`Restored ${res.loadedDatasets} dataset(s) and ${res.loadedInstruments} instrument(s) from ${fileName}.`);
      onClose();
    } catch (exc: any) {
      setError(exc?.message || 'Failed to restore definitions');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="actions-flow">
      <Modal
        title="Load Dataset Definitions"
        width={500}
        onClose={onClose}
        footer={
          <>
            <Button onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button className="primary" onClick={handleLoad} disabled={loading || !fileContent}>
              {loading ? 'Restoring…' : 'Restore'}
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
          <legend>Select Backup File</legend>
          <p style={{ fontSize: 12, color: 'var(--muted)', margin: '0 0 8px 0' }}>
            Choose a JSON definition file to restore symbols, instruments, and configurations.
          </p>
          <input
            type="file"
            accept=".json,application/json"
            onChange={handleFileChange}
            disabled={loading}
            style={{ width: '100%', padding: '6px' }}
          />
          {fileName && (
            <p style={{ fontSize: 12, margin: '8px 0 0 0' }}>
              Selected: <strong>{fileName}</strong>
            </p>
          )}
        </fieldset>
      </Modal>
    </div>
  );
}
