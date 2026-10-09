import { useState } from 'react';
import { Button, Field, Modal } from '../../../../components/ui';
import { parseBrokersJson, type BrokerProfile } from './brokerProfiles';
import { importBrokersXml } from './brokerApiClient';
import { useDataManagerStore } from '../../Common/dataManagerStore';
import './brokerProfiles.css';

export function BrokerTransferDialog({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: (message: string) => void;
}) {
  const store = useDataManagerStore();
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState<Omit<BrokerProfile, 'id'>[]>([]);
  const [conflicts, setConflicts] = useState<string[]>([]);
  const [index, setIndex] = useState(0);
  const [overwrite, setOverwrite] = useState<string[]>([]);
  const [skipped, setSkipped] = useState<string[]>([]);
  const [error, setError] = useState('');

  async function commit(items = pending, overwrites = overwrite, skips = skipped) {
    try {
      const count = await store.importBrokers(
        items.filter(row => !skips.includes(row.name)),
        overwrites
      );
      onSaved(`Brokers (${count}) loaded.`);
      onClose();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Cannot load brokers.');
    }
  }

  function decide(action: 'skip' | 'overwrite' | 'overwrite-all') {
    const name = conflicts[index];
    const nextSkipped = action === 'skip' ? [...skipped, name] : skipped;
    const nextOverwrite =
      action === 'skip'
        ? overwrite
        : action === 'overwrite-all'
        ? [...overwrite, ...conflicts.slice(index)]
        : [...overwrite, name];
    if (action === 'overwrite-all' || index === conflicts.length - 1)
      void commit(pending, nextOverwrite, nextSkipped);
    else {
      setSkipped(nextSkipped);
      setOverwrite(nextOverwrite);
      setIndex(value => value + 1);
    }
  }

  async function load() {
    try {
      if (!file) throw new Error('Select a Brokers JSON or XML file.');
      if (file.size > 5_000_000) throw new Error('Cannot load brokers: file too large.');
      const text = await file.text();
      let items: Omit<BrokerProfile, 'id'>[];

      if (file.name.toLowerCase().endsWith('.xml') || text.trim().startsWith('<')) {
        const imported = await importBrokersXml(text);
        if (!imported.length) throw new Error('No Brokers found in XML file.');
        await store.syncBrokers();
        onSaved(`Brokers (${imported.length}) loaded from XML.`);
        onClose();
        return;
      } else {
        items = parseBrokersJson(text);
      }

      const duplicates = items
        .map(
          item =>
            store.brokers.find(row => row.name.toLowerCase() === item.name.toLowerCase())?.name
        )
        .filter((v): v is string => Boolean(v));
      setPending(items);
      setConflicts(duplicates);
      setIndex(0);
      setOverwrite([]);
      setSkipped([]);
      if (!duplicates.length) void commit(items, [], []);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Cannot load brokers.');
    }
  }

  if (conflicts.length)
    return (
      <div className="broker-flow">
        <Modal
          title="Overwrite confirm"
          width={590}
          onClose={onClose}
          footer={
            <>
              <Button onClick={onClose}>Cancel</Button>
              <Button onClick={() => decide('skip')}>Skip</Button>
              <Button onClick={() => decide('overwrite')}>Overwrite</Button>
              <Button className="primary" onClick={() => decide('overwrite-all')}>
                Overwrite all
              </Button>
            </>
          }
        >
          <p>
            Broker '{conflicts[index]}' already exists, do you want to overwrite it with the
            imported one?
          </p>
          <small>
            Conflict {index + 1} of {conflicts.length}
          </small>
        </Modal>
      </div>
    );

  return (
    <div className="broker-flow">
      <Modal
        title="Load brokers"
        width={560}
        onClose={onClose}
        footer={
          <>
            <Button onClick={onClose}>Close</Button>
            <Button className="primary" onClick={() => void load()}>
              Validate and load
            </Button>
          </>
        }
      >
        {error && (
          <p className="broker-error" role="alert">
            {error}
          </p>
        )}
        <Field label="Brokers file (JSON or XML)">
          <input
            aria-label="Brokers file"
            className="file-input compact"
            type="file"
            accept=".json,.xml,application/json,text/xml,application/xml"
            onChange={event => {
              setFile(event.target.files?.[0] ?? null);
              setError('');
            }}
          />
        </Field>
        <p className="broker-note">
          The complete file is validated before any broker profile is updated.
        </p>
      </Modal>
    </div>
  );
}
