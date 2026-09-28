import { useState, type ChangeEvent } from 'react';
import { Button, Field, Modal, Select, TextInput } from '../../../components/ui';
import { actionsClient, downloadBlob } from './actionsClient';
import './actions.css';

export interface Mt5ExportTarget {
  id: string;
  symbol: string;
  from?: string;
  to?: string;
  timeframe?: string;
}

export function Mt5ExportDialog({
  target,
  onClose,
  onComplete,
}: {
  target: Mt5ExportTarget;
  onClose: () => void;
  onComplete: (message: string) => void;
}) {
  const [timeframe, setTimeframe] = useState<string>(
    target.timeframe?.toUpperCase().includes('TICK') ? 'TICK' : 'M1'
  );
  const [spreadMode, setSpreadMode] = useState<'real' | 'fixed'>('real');
  const [spreadPoints, setSpreadPoints] = useState<number>(10);
  const [timezone, setTimezone] = useState<string>('Original');
  const [dateFrom, setDateFrom] = useState<string>(target.from || '');
  const [dateTo, setDateTo] = useState<string>(target.to || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  async function handleExport(): Promise<void> {
    setLoading(true);
    setError('');
    try {
      const res = await actionsClient.exportToMt5({
        symbol: target.symbol,
        timeframe,
        spread_mode: spreadMode,
        spread_points: spreadPoints,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        target_timezone: timezone !== 'Original' ? timezone : undefined,
      });
      if (res.content) {
        downloadBlob(`${res.symbol}_mt5_${res.timeframe.toLowerCase()}.txt`, res.content, 'text/tab-separated-values');
      }
      onComplete(`Exported ${res.records} MT5 ${res.kind} record(s) for ${res.symbol}.`);
      onClose();
    } catch (exc: any) {
      setError(exc?.message || 'Failed to export MT5 data');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="data-export-flow">
      <Modal
        title={`Export to MetaTrader 5 (${target.symbol})`}
        width={560}
        onClose={onClose}
        footer={
          <>
            <Button onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button className="primary" onClick={handleExport} disabled={loading}>
              {loading ? 'Exporting…' : 'Export MT5'}
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
          <legend>MT5 Export Configuration</legend>
          <div className="export-grid">
            <Field label="Data Timeframe">
              <Select value={timeframe} onChange={setTimeframe}>
                <option value="M1">M1 (1-Minute Bars)</option>
                <option value="TICK">TICK (Real Tick Data)</option>
              </Select>
            </Field>
            <Field label="Spread Mode">
              <Select value={spreadMode} onChange={(v: string) => setSpreadMode(v as 'real' | 'fixed')}>
                <option value="real">Real Spreads (from Bid/Ask)</option>
                <option value="fixed">Fixed Spread (Specified points)</option>
              </Select>
            </Field>
            {spreadMode === 'fixed' && (
              <Field label="Fixed Spread Points">
                <TextInput
                  type="number"
                  min={0}
                  max={500}
                  value={String(spreadPoints)}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setSpreadPoints(Number(e.target.value) || 0)}
                />
              </Field>
            )}
            <Field label="Timezone Adjustment">
              <Select value={timezone} onChange={setTimezone}>
                <option value="Original">Original Timezone</option>
                <option value="+1h">UTC+1</option>
                <option value="+2h">UTC+2 (EET)</option>
                <option value="+3h">UTC+3 (MSK)</option>
              </Select>
            </Field>
          </div>
          <div className="export-date-grid">
            <Field label="Date From">
              <TextInput type="date" value={dateFrom} onChange={(e: ChangeEvent<HTMLInputElement>) => setDateFrom(e.target.value)} />
            </Field>
            <Field label="Date To">
              <TextInput type="date" value={dateTo} onChange={(e: ChangeEvent<HTMLInputElement>) => setDateTo(e.target.value)} />
            </Field>
          </div>
        </fieldset>
      </Modal>
    </div>
  );
}
