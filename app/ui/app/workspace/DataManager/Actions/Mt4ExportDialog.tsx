import { useState, type ChangeEvent } from 'react';
import { Button, Field, Modal, Select, TextInput } from '../../../components/ui';
import { actionsClient } from './actionsClient';
import './actions.css';

export interface Mt4ExportTarget {
  id: string;
  symbol: string;
  instrument?: string;
  from?: string;
  to?: string;
}

export function Mt4ExportDialog({
  target,
  onClose,
  onComplete,
}: {
  target: Mt4ExportTarget;
  onClose: () => void;
  onComplete: (message: string) => void;
}) {
  const [mt4Symbol, setMt4Symbol] = useState<string>(target.instrument || target.symbol.split('_')[0] || target.symbol);
  const [timeframe, setTimeframe] = useState<string>('All');
  const [exportMode, setExportMode] = useState<'All' | 'hst' | 'fxt'>('All');
  const [serverName, setServerName] = useState<string>('MetaQuotes-Demo');
  const [spread, setSpread] = useState<number>(20);
  const [digits, setDigits] = useState<number>(5);
  const [timezone, setTimezone] = useState<string>('Original');
  const [dateFrom, setDateFrom] = useState<string>(target.from || '');
  const [dateTo, setDateTo] = useState<string>(target.to || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  async function handleExport(): Promise<void> {
    setLoading(true);
    setError('');
    try {
      const res = await actionsClient.exportToMt4({
        symbol: target.symbol,
        mt4_symbol: mt4Symbol || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        timeframe,
        export_mode: exportMode,
        server_name: serverName,
        spread,
        digits,
        target_timezone: timezone !== 'Original' ? timezone : undefined,
      });
      onComplete(`Successfully generated ${res.files.length} MT4 file(s) for ${res.symbol}.`);
      onClose();
    } catch (exc: any) {
      setError(exc?.message || 'Failed to export MT4 files');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="data-export-flow">
      <Modal
        title={`Export to MetaTrader 4 (${target.symbol})`}
        width={560}
        onClose={onClose}
        footer={
          <>
            <Button onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button className="primary" onClick={handleExport} disabled={loading}>
              {loading ? 'Exporting…' : 'Export MT4'}
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
          <legend>MT4 Symbol & Server Properties</legend>
          <div className="export-grid">
            <Field label="MT4 Symbol Name">
              <TextInput value={mt4Symbol} onChange={(e: ChangeEvent<HTMLInputElement>) => setMt4Symbol(e.target.value)} />
            </Field>
            <Field label="Server Name (for FXT)">
              <TextInput value={serverName} onChange={(e: ChangeEvent<HTMLInputElement>) => setServerName(e.target.value)} />
            </Field>
            <Field label="Export Mode">
              <Select value={exportMode} onChange={(v: string) => setExportMode(v as 'All' | 'hst' | 'fxt')}>
                <option value="All">All (HST History &amp; FXT Strategy Tester)</option>
                <option value="hst">HST Bar Files Only</option>
                <option value="fxt">FXT Tick Model File Only</option>
              </Select>
            </Field>
            <Field label="Timeframe">
              <Select value={timeframe} onChange={setTimeframe}>
                <option value="All">All Timeframes (M1, M5, M15, M30, H1, H4, D1)</option>
                <option value="M1">M1 Only</option>
                <option value="M5">M5 Only</option>
                <option value="H1">H1 Only</option>
                <option value="D1">D1 Only</option>
              </Select>
            </Field>
            <Field label="Spread (Points)">
              <TextInput
                type="number"
                min={0}
                max={500}
                value={String(spread)}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setSpread(Number(e.target.value) || 0)}
              />
            </Field>
            <Field label="Price Decimal Digits">
              <TextInput
                type="number"
                min={0}
                max={8}
                value={String(digits)}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setDigits(Number(e.target.value) || 5)}
              />
            </Field>
          </div>
          <div className="export-grid">
            <Field label="Timezone Shift">
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
