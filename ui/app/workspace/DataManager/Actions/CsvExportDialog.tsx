import { useState, type ChangeEvent } from 'react';
import { Button, Checkbox, Field, Modal, Select, TextInput } from '../../../components/ui';
import { actionsClient, downloadBlob } from './actionsClient';
import './actions.css';

export interface CsvExportTarget {
  id: string;
  symbol: string;
  from?: string;
  to?: string;
  timeframe?: string;
}

export function CsvExportDialog({
  targets,
  onClose,
  onComplete,
}: {
  targets: CsvExportTarget[];
  onClose: () => void;
  onComplete: (message: string) => void;
}) {
  const target = targets[0];
  const [timeframe, setTimeframe] = useState<string>(target?.timeframe || 'M1');
  const [dateFrom, setDateFrom] = useState<string>(target?.from || '');
  const [dateTo, setDateTo] = useState<string>(target?.to || '');
  const [timezone, setTimezone] = useState<string>('Original');
  const [includeHeader, setIncludeHeader] = useState<boolean>(true);
  const [header, setHeader] = useState<string>(target?.timeframe === 'TICK' ? '<DATE>,<TIME>,<BID>,<ASK>,<VOL>' : '<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  async function handleExport(): Promise<void> {
    if (!target) return;
    setLoading(true);
    setError('');
    try {
      let totalRecords = 0;
      for (const t of targets) {
        const res = await actionsClient.exportToCsv({
          dataset_id: t.id,
          symbol: t.symbol,
          timeframe,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
          target_timezone: timezone !== 'Original' ? timezone : undefined,
          header,
          include_header: includeHeader,
        });
        totalRecords += res.records;
        if (res.content) {
          downloadBlob(`${res.symbol}_${res.timeframe}.csv`, res.content, 'text/csv');
        }
      }
      onComplete(`Exported ${totalRecords} bar(s) for ${targets.length} dataset(s) to CSV.`);
      onClose();
    } catch (exc: any) {
      setError(exc?.message || 'Failed to export CSV');
    } finally {
      setLoading(false);
    }
  }

  const selectedTitle = targets.length === 1 ? targets[0].symbol : `${targets.length} datasets`;

  return (
    <div className="data-export-flow">
      <Modal
        title={`Export to CSV (${selectedTitle})`}
        width={560}
        onClose={onClose}
        footer={
          <>
            <Button onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button className="primary" onClick={handleExport} disabled={loading || !targets.length}>
              {loading ? 'Exporting…' : 'Export CSV'}
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
          <legend>Export Parameters</legend>
          <div className="export-grid">
            <Field label="Target Timeframe">
              <Select value={timeframe} onChange={setTimeframe}>
                {target?.timeframe === 'TICK' && <option value="TICK">TICK (Stored)</option>}
                <option value="M1">M1 (1 Minute)</option>
                <option value="M5">M5 (5 Minutes)</option>
                <option value="M15">M15 (15 Minutes)</option>
                <option value="M30">M30 (30 Minutes)</option>
                <option value="H1">H1 (1 Hour)</option>
                <option value="H4">H4 (4 Hours)</option>
                <option value="D1">D1 (Daily)</option>
              </Select>
            </Field>
            <Field label="Timezone Adjustment">
              <Select value={timezone} onChange={setTimezone}>
                <option value="Original">Original Timezone</option>
                <option value="+1h">UTC+1</option>
                <option value="+2h">UTC+2 (EET)</option>
                <option value="+3h">UTC+3 (MSK)</option>
                <option value="-4h">UTC-4 (EDT)</option>
                <option value="-5h">UTC-5 (EST)</option>
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
          <Checkbox label="Include Header Row" checked={includeHeader} onChange={setIncludeHeader} />
          {includeHeader && (
            <Field label="Header Format Template">
              <TextInput value={header} onChange={(e: ChangeEvent<HTMLInputElement>) => setHeader(e.target.value)} />
            </Field>
          )}
        </fieldset>
      </Modal>
    </div>
  );
}
