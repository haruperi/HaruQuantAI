import { useState } from 'react';
import { Button, Field, Modal, Select, TextInput } from '../../../../components/ui';
import {
  parseSessionsJson,
  parseSessionsXml,
  serializeSessionsJson,
  serializeSessionsXml,
  type SessionBroker,
  type SessionDefinition,
} from './sessions';
import { exportSqxXmlRemote, importSqxXmlRemote } from './sessionApiClient';
import { useSessions } from './sessionStore';
import './sessions.css';

function downloadFile(content: string, filename: string, mime: string) {
  const url = URL.createObjectURL(new Blob([content], { type: mime }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function SessionTransferDialog({
  mode,
  selected,
  all,
  brokers,
  onClose,
  onSaved,
}: {
  mode: 'save' | 'load';
  selected: SessionDefinition[];
  all: SessionDefinition[];
  brokers: SessionBroker[];
  onClose: () => void;
  onSaved: (message: string) => void;
}) {
  const store = useSessions();
  const [format, setFormat] = useState<'xml' | 'json'>('xml');
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState<SessionDefinition[]>([]);
  const [conflicts, setConflicts] = useState<string[]>([]);
  const [index, setIndex] = useState(0);
  const [skipped, setSkipped] = useState<string[]>([]);
  const [overwrite, setOverwrite] = useState<string[]>([]);
  const [error, setError] = useState('');

  function commit(items = pending, overwrites = overwrite, skips = skipped) {
    try {
      store.importSessions(
        items.filter((row) => !skips.includes(row.name)),
        overwrites,
      );
      onSaved(`Sessions (${items.length - skips.length}) loaded.`);
      onClose();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Cannot load sessions.');
    }
  }

  function decide(action: 'skip' | 'overwrite') {
    const name = conflicts[index];
    const nextSkipped = action === 'skip' ? [...skipped, name] : skipped;
    const nextOverwrite = action === 'overwrite' ? [...overwrite, name] : overwrite;
    if (index === conflicts.length - 1) {
      commit(pending, nextOverwrite, nextSkipped);
    } else {
      setSkipped(nextSkipped);
      setOverwrite(nextOverwrite);
      setIndex((value) => value + 1);
    }
  }

  async function primary() {
    try {
      setError('');
      if (mode === 'save') {
        if (!selected.length) {
          throw new Error('You have to select at least one session.');
        }
        if (format === 'xml') {
          let xmlContent = '';
          try {
            xmlContent = await exportSqxXmlRemote(selected.map((s) => s.name));
          } catch {
            xmlContent = serializeSessionsXml(selected);
          }
          downloadFile(xmlContent, 'Sessions.xml', 'application/xml');
        } else {
          downloadFile(serializeSessionsJson(selected), 'Sessions.json', 'application/json');
        }
        onSaved('Sessions saved.');
        onClose();
        return;
      }

      if (!file) throw new Error('Select a Sessions XML or JSON file.');
      if (file.size > 2_000_000) throw new Error('Session file is too large.');

      const text = await file.text();
      const isXml = file.name.toLowerCase().endsWith('.xml') || text.trim().startsWith('<');

      let items: SessionDefinition[] = [];
      if (isXml) {
        try {
          const remoteRes = await importSqxXmlRemote(text, 'overwrite');
          if (remoteRes.imported.length > 0) {
            items = remoteRes.imported;
          } else {
            items = parseSessionsXml(text);
          }
        } catch {
          items = parseSessionsXml(text);
        }
      } else {
        items = parseSessionsJson(text);
      }

      items = items.map((item) => {
        const exact = brokers.find((row) => row.id === item.broker || row.name === item.brokerName);
        if (exact) return { ...item, broker: exact.id, brokerName: exact.name };
        const broker = [...brokers]
          .filter((row) => row.postfix && item.name.endsWith(row.postfix))
          .sort((a, b) => b.postfix.length - a.postfix.length)[0];
        return broker
          ? { ...item, broker: broker.id, brokerName: broker.name }
          : { ...item, broker: '-1', brokerName: 'Default' };
      });

      const duplicate = items
        .map((item) => all.find((row) => row.name.toLowerCase() === item.name.toLowerCase())?.name)
        .filter((name): name is string => Boolean(name));

      setPending(items);
      setConflicts(duplicate);
      setIndex(0);
      setSkipped([]);
      setOverwrite([]);
      if (!duplicate.length) {
        commit(items, [], []);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Cannot load sessions.');
    }
  }

  if (mode === 'load' && conflicts.length) {
    return (
      <div className="sessions-flow">
        <Modal
          title="Overwrite confirm"
          width={560}
          onClose={onClose}
          footer={
            <>
              <Button onClick={onClose}>Cancel</Button>
              <Button onClick={() => decide('skip')}>Skip</Button>
              <Button className="primary" onClick={() => decide('overwrite')}>
                Overwrite
              </Button>
            </>
          }
        >
          <p>
            Session '{conflicts[index]}' already exists, do you want to overwrite it with the
            imported one?
          </p>
          <p className="session-note">
            Conflict {index + 1} of {conflicts.length}
          </p>
        </Modal>
      </div>
    );
  }

  return (
    <div className="sessions-flow">
      <Modal
        title={mode === 'save' ? 'Save sessions' : 'Load sessions'}
        width={540}
        onClose={onClose}
        footer={
          <>
            <Button onClick={onClose}>Close</Button>
            <Button className="primary" onClick={() => void primary()}>
              {mode === 'save' ? 'Download file' : 'Validate and load'}
            </Button>
          </>
        }
      >
        {(error || store.storageError) && (
          <p className="session-error" role="alert">
            {error || store.storageError}
          </p>
        )}
        {mode === 'save' ? (
          <>
            <p>
              Export <strong>{selected.length}</strong> selected session
              {selected.length === 1 ? '' : 's'}.
            </p>
            <Field label="File format">
              <Select value={format} onChange={(val) => setFormat(val as 'xml' | 'json')}>
                <option value="xml">StrategyQuant X XML (Sessions.xml)</option>
                <option value="json">JSON format (Sessions.json)</option>
              </Select>
            </Field>
            <Field label="File name">
              <TextInput value={format === 'xml' ? 'Sessions.xml' : 'Sessions.json'} readOnly />
            </Field>
          </>
        ) : (
          <>
            <Field label="Sessions XML or JSON file">
              <input
                aria-label="Sessions file"
                className="file-input compact"
                type="file"
                accept=".xml,.json,text/xml,application/json"
                onChange={(event) => {
                  setFile(event.target.files?.[0] ?? null);
                  setError('');
                }}
              />
            </Field>
            <p className="session-note">
              Supports both native StrategyQuant X Sessions.xml and Sessions.json files.
            </p>
          </>
        )}
      </Modal>
    </div>
  );
}
