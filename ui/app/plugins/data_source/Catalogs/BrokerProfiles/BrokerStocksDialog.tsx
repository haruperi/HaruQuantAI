import { useEffect, useRef, useState } from 'react';
import { Button, Modal } from '../../../../components/ui';
import { parseBrokerStocks, type BrokerProfile } from './brokerProfiles';
import { fetchBrokerStocks } from './brokerApiClient';
import { useDataManagerStore } from '../../Common/dataManagerStore';
import './brokerProfiles.css';

function download(content: string, filename: string) {
  const url = URL.createObjectURL(new Blob([content], { type: 'text/plain;charset=utf-8' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function BrokerStocksDialog({
  profile,
  onClose,
  onSaved,
}: {
  profile: BrokerProfile;
  onClose: () => void;
  onSaved: (message: string) => void;
}) {
  const [text, setText] = useState(() => profile.stocks.join('\n'));
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const store = useDataManagerStore();
  const submitting = useRef(false);
  function close() {if (!submitting.current) onClose();}

  useEffect(() => {
    let mounted = true;
    if (/^\d+$/.test(profile.id)) {
      setLoading(true);
      fetchBrokerStocks(profile.id)
        .then(stocks => {
          if (mounted) {
            setText(stocks.join('\n'));
          }
        })
        .catch(cause => {
          if (mounted) {
            setError(cause instanceof Error ? cause.message : 'Cannot load broker stocks.');
          }
        })
        .finally(() => {
          if (mounted) setLoading(false);
        });
    }
    return () => {
      mounted = false;
    };
  }, [profile.id]);

  async function load(file: File | undefined) {
    if (!file || submitting.current || loading || profile.system) return;
    submitting.current=true;setSaving(true);setError('');
    try {
      if (file.size > 2_000_000) throw new Error('Stock file is too large.');
      const parsed = parseBrokerStocks(await file.text());
      await store.saveBrokerStocks(profile.id, parsed);
      onSaved(`Stocks (${useDataManagerStore.getState().brokers.find(row=>row.id===profile.id)?.stocks.length??0}) were imported`);
      onClose();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Cannot import stocks.');
    } finally {submitting.current=false;setSaving(false);}
  }

  async function save() {
    if (submitting.current || loading || error) return;
    submitting.current=true;
    setSaving(true);
    if (profile.system) {
      setError("This broker can't be edited.");
      submitting.current=false;setSaving(false); return;
    }
    try {
      const parsed = parseBrokerStocks(text);
      await store.saveBrokerStocks(profile.id, parsed);
      onSaved('Stocks were saved.');
      onClose();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Cannot save stocks.');
    } finally { submitting.current=false;setSaving(false); }
  }

  return (
    <div className="broker-flow">
      <Modal
        title={`Edit stocks ${profile.name}`}
        width={700}
        onClose={close}
        footer={
          <>
            <Button disabled={saving} onClick={close}>Close</Button>
            <Button disabled={saving || loading || Boolean(error) || profile.system} className="primary" onClick={save}>
              Save
            </Button>
          </>
        }
      >
        {loading && <p role="status">Loading saved stocks…</p>}
        {error && (
          <p className="broker-error" role="alert">
            {error}
          </p>
        )}
        <div className="broker-stock-hint">
          <p>Use the textarea below to define the individual stocks for broker, separated by lines.</p>
          <div className="broker-stock-example-label">Example:</div>
          <pre className="broker-stock-example">
AAPL{'\n'}TSLA{'\n'}AMZN
          </pre>
        </div>
        <div className="broker-stock-actions">
          <label className="btn-stock-file">
            Import from file
            <input
              aria-label="Broker stocks file"
              hidden
              type="file"
              accept=".csv,text/csv,text/plain"
              disabled={profile.system || loading || saving}
              onChange={event => void load(event.target.files?.[0])}
            />
          </label>
          <button
            type="button"
            className="btn-stock-file"
            onClick={() => {
              const stocks = parseBrokerStocks(text);
              const cleanName = profile.name.replace(/[\[\]]/g, '').trim().replace(/[^a-zA-Z0-9_-]/g, '_');
              download(stocks.join('\n'), `${cleanName || 'Broker'}_stocks.csv`);
              onSaved('Stocks were exported');
            }}
          >
            Export to file
          </button>
        </div>
        <textarea
          className="broker-stocks"
          aria-label="Broker stocks"
          value={text}
          placeholder={loading ? 'Loading constituent stocks...' : ''}
          disabled={saving || loading || profile.system}
          onChange={event => {setText(event.target.value);setError('');}}
        />
      </Modal>
    </div>
  );
}
