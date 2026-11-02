import { useEffect, useRef, useState } from 'react';
import { Button, Modal, TextInput } from '../../../../common/components/ui';
import { createDomainClient } from '../../../../shell/transport';
import { today, validDate } from '../Dukascopy/dukascopyDownload';
import { ProviderConnectionsDialog, type ProviderConnection } from './ProviderConnectionsDialog';
import { useHistoricalSources, type SourceRecord } from './historicalSourceStore';
import './historicalDownload.css';

const names: Record<string, string> = { yahoo: 'Yahoo', darwinex: 'Darwinex', binance: 'Binance spot', binance_coinm: 'Binance Coin-M', binance_usdtm: 'Binance USDT-M', bitfinex: 'Bitfinex', coinbase: 'Coinbase', poloniex: 'Poloniex', sq_equity: 'SQ Equity', sq_futures: 'SQ Futures', dukascopy: 'Dukascopy', mt5: 'MT5' };
interface Props { provider: string; targets: SourceRecord[]; onClose: () => void; onStarted: () => void }
function savedDate(value?: string): string | undefined {
  const date = value?.slice(0, 10);
  return date && validDate(date) ? date : undefined;
}
function monthsAgo(months: number): string {
  const date = new Date(`${today()}T12:00:00Z`);
  const day = date.getUTCDate();
  date.setUTCDate(1); date.setUTCMonth(date.getUTCMonth() - months);
  const end = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0)).getUTCDate();
  date.setUTCDate(Math.min(day, end));
  return date.toISOString().slice(0, 10);
}
export function HistoricalDownloadDialog({ provider, targets, onClose, onStarted }: Props) {
  const [from, setFrom] = useState(() => monthsAgo(6));
  const [to, setTo] = useState(today);
  const [preset, setPreset] = useState('sixMonths');
  const [overwrite, setOverwrite] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [connectionId, setConnectionId] = useState('');
  const [connections, setConnections] = useState<ProviderConnection[]>([]);
  const [connectionError, setConnectionError] = useState('');
  const [connectionVersion, setConnectionVersion] = useState(0);
  const [manage, setManage] = useState(false);
  const submitting = useRef(false);
  const sources = [...new Set(targets.map(row => row.source))];
  const mixed = sources.length > 1;
  const sourceName = mixed ? 'historical' : names[provider] ?? provider;
  const title = `Download ${sourceName} data for ${targets.length === 1 ? targets[0].symbol : 'multiple datasets'}`;
  const lastDates = targets.map(row => savedDate(row.to));
  const sinceLast = lastDates.every((date): date is string => Boolean(date)) ? [...lastDates].sort()[0] : undefined;
  const close = () => {
    if (submitting.current) return;
    onClose();
    window.setTimeout(() => document.querySelector<HTMLButtonElement>(`[data-control-id="${mixed ? 'update-selected' : provider.startsWith('binance') || ['bitfinex', 'coinbase', 'poloniex'].includes(provider) ? 'crypto' : provider.replace('_', '-')}"]`)?.focus(), 0);
  };
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    setConnectionError('');
    createDomainClient('', { signal: controller.signal }).get<ProviderConnection[]>('/connections')
      .then(value => { if (active) setConnections(value); })
      .catch(() => { if (active) setConnectionError('Saved connections could not be loaded. Provider defaults remain available.'); })
      .finally(() => window.clearTimeout(timeout));
    return () => { active = false; window.clearTimeout(timeout); controller.abort(); };
  }, [connectionVersion]);
  function choose(key: string, months?: number) {
    setPreset(key); setError(''); setTo(today());
    if (key === 'sinceLast' && sinceLast) setFrom(sinceLast);
    else if (months) setFrom(monthsAgo(months));
  }
  async function start() {
    if (submitting.current) return;
    setError('');
    if (!targets.length || !validDate(from) || !validDate(to) || from > to || to > today()) {
      setError('Choose a valid date range with From on or before To, ending no later than today.'); return;
    }
    submitting.current = true; setBusy(true);
    try {
      await useHistoricalSources.getState().start(targets, from, to, overwrite, connectionId || undefined);
      onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start the download.'); }
    finally { submitting.current = false; setBusy(false); }
  }
  const presetButton = (key: string, label: string, months?: number) => <Button aria-pressed={preset === key} className={preset === key ? 'primary' : ''} disabled={busy || key === 'sinceLast' && !sinceLast || key === 'allTime'} title={key === 'allTime' ? 'The provider does not supply a verified earliest available date.' : key === 'sinceLast' && !sinceLast ? 'Every selected dataset must have a recorded last date.' : undefined} onClick={() => choose(key, months)}>{label}</Button>;
  if (manage) return <ProviderConnectionsDialog provider={provider} onClose={() => setManage(false)} onSaved={id => { setConnectionId(id); setConnectionVersion(value => value + 1); }}/>;
  return <div className="historical-download-flow" aria-busy={busy} onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),summary,a[href]'));
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}><Modal title={title} width={800} onClose={close} footer={<><Button disabled={busy} onClick={close}>Close</Button><Button className="primary" disabled={busy || !targets.length} onClick={() => void start()}>{busy ? 'Starting…' : 'Start download'}</Button></>}>
    {error && <p role="alert" className="historical-download-error">{error}</p>}
    {targets.length > 1 && <details><summary>{targets.length} selected datasets</summary><ul>{targets.map(row => <li key={row.id}>{row.symbol} ({names[row.source] ?? row.source}, {row.timeframe})</li>)}</ul></details>}
    <fieldset disabled={busy}><legend>Choose data range to download</legend>
      <div className="historical-date-row"><label>From<TextInput aria-label="From" type="date" max={today()} value={from} onChange={event => { setFrom(event.target.value); setPreset('custom'); }}/></label>{presetButton('sinceLast', 'Since last date')}{presetButton('sixMonths', 'Last 6 months', 6)}{presetButton('year', 'Last year', 12)}</div>
      <div className="historical-date-row"><label>To<TextInput aria-label="To" type="date" max={today()} value={to} onChange={event => { setTo(event.target.value); setPreset('custom'); }}/></label>{presetButton('fiveYears', 'Last 5 years', 60)}{presetButton('tenYears', 'Last 10 years', 120)}{presetButton('allTime', 'All time')}</div>
      <p className="historical-download-note">All time is unavailable because the provider does not supply a verified earliest available date.</p>
      {targets.length > 1 && sinceLast && <p className="historical-download-note">Since last date starts at the earliest recorded last date among the selected datasets.</p>}
    </fieldset>
    <fieldset disabled={busy}><legend>Redownload options</legend><div className="historical-redownload"><label><input type="radio" name="historical-overwrite" checked={!overwrite} onChange={() => setOverwrite(false)}/>Add only missing data</label><label><input type="radio" name="historical-overwrite" checked={overwrite} onChange={() => setOverwrite(true)}/>Overwrite existing data</label></div></fieldset>
    {targets.some(row => row.source === 'yahoo' && row.timeframe !== 'D1') && <p className="historical-download-note">Yahoo limits intraday history. Select recent dates; use daily bars for older history.</p>}
    {targets.some(row => row.source.startsWith('sq_')) && <p className="historical-download-note">The configured SQ adapter supplies daily data. Available dates depend on its configured CDN.</p>}
    <details className="historical-download-connection"><summary>Provider connection</summary>{connectionError && <p role="alert">{connectionError} <Button onClick={() => setConnectionVersion(value => value + 1)}>Retry connections</Button></p>}{mixed ? <p>Each source uses its provider default connection.</p> : <><label>Saved provider connection<select disabled={busy} value={connectionId} onChange={event => setConnectionId(event.target.value)}><option value="">Provider default</option>{connections.filter(row => row.provider === provider).map(row => <option key={row.connection_id} value={row.connection_id}>{row.name}</option>)}</select></label><Button disabled={busy} onClick={() => setManage(true)}>Manage connections</Button></>}</details>
  </Modal></div>;
}
