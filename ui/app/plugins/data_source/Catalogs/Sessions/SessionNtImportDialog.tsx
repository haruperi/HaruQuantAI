import { useEffect, useState } from 'react';
import { Button, Field, Modal, Select, TextInput } from '../../../../components/ui';
import { importNtRemote, listNtTemplates, type NtImportResult, type NtTemplateInfo } from './sessionApiClient';
import { useSessions } from './sessionStore';
import './sessions.css';

export function SessionNtImportDialog({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: (message: string) => void;
}) {
  const store = useSessions();
  const [folderPath, setFolderPath] = useState('');
  const [templateInfo, setTemplateInfo] = useState<NtTemplateInfo | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [policy, setPolicy] = useState<'overwrite' | 'skip'>('overwrite');
  const [scanning, setScanning] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<NtImportResult | null>(null);

  useEffect(() => {
    void scanFolder();
  }, []);

  async function scanFolder(customFolder?: string) {
    setScanning(true);
    setError('');
    try {
      const info = await listNtTemplates(customFolder || undefined);
      setTemplateInfo(info);
      if (!folderPath && info.folder) {
        setFolderPath(info.folder);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Failed to scan NinjaTrader folder.');
    } finally {
      setScanning(false);
    }
  }

  async function runImport() {
    setImporting(true);
    setError('');
    try {
      let res: NtImportResult;
      if (file) {
        const text = await file.text();
        res = await importNtRemote({
          xml_content: text,
          conflict_policy: policy,
        });
      } else if (folderPath) {
        res = await importNtRemote({
          folder_path: folderPath,
          conflict_policy: policy,
        });
      } else {
        throw new Error('Please select an XML file or enter a valid template folder path.');
      }
      setResult(res);
      await store.refreshFromServer();
      onSaved(res.success);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Import failed.');
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="sessions-flow">
      <Modal
        title="Import NinjaTrader 8 Trading Hours"
        width={580}
        onClose={onClose}
        footer={
          <>
            <Button onClick={onClose}>Close</Button>
            <Button
              className="primary"
              disabled={importing || scanning}
              onClick={() => void runImport()}
            >
              {importing ? 'Importing...' : 'Import sessions'}
            </Button>
          </>
        }
      >
        {error && (
          <p className="session-error" role="alert">
            {error}
          </p>
        )}

        {result ? (
          <div className="session-import-result">
            <p className="session-success-msg">
              <strong>{result.success}</strong>
            </p>
            {result.imported.length > 0 && (
              <p>
                Imported sessions: <em>{result.imported.join(', ')}</em>
              </p>
            )}
            {result.skipped.length > 0 && (
              <p>
                Skipped sessions: <em>{result.skipped.join(', ')}</em>
              </p>
            )}
            {result.failed.length > 0 && (
              <p className="session-error">
                Failed templates:{' '}
                {result.failed.map((f) => `${f.template} (${f.reason})`).join(', ')}
              </p>
            )}
          </div>
        ) : (
          <>
            <Field label="NinjaTrader 8 TradingHours template folder">
              <div className="session-folder-picker">
                <TextInput
                  value={folderPath}
                  placeholder="e.g. C:\Users\...\Documents\NinjaTrader 8\templates\TradingHours"
                  onChange={(e) => setFolderPath(e.target.value)}
                />
                <Button
                  onClick={() => void scanFolder(folderPath)}
                  disabled={scanning}
                >
                  {scanning ? 'Scanning...' : 'Scan'}
                </Button>
              </div>
            </Field>

            {templateInfo && (
              <p className="session-note">
                {templateInfo.exists
                  ? `Found ${templateInfo.count} XML template(s) in folder.`
                  : 'Folder does not exist on server. You can upload an individual XML file below.'}
              </p>
            )}

            <Field label="Or choose XML template file from disk">
              <input
                aria-label="Upload XML file"
                className="file-input compact"
                type="file"
                accept=".xml,text/xml"
                onChange={(e) => {
                  setFile(e.target.files?.[0] ?? null);
                  setError('');
                }}
              />
            </Field>

            <Field label="Conflict policy">
              <Select
                value={policy}
                onChange={(val) => setPolicy(val as 'overwrite' | 'skip')}
              >
                <option value="overwrite">Overwrite existing sessions</option>
                <option value="skip">Skip existing sessions</option>
              </Select>
            </Field>

            <p className="session-note">
              Note: NT8 holidays and partial holidays will not be imported as SQX has no equivalent.
            </p>
          </>
        )}
      </Modal>
    </div>
  );
}
