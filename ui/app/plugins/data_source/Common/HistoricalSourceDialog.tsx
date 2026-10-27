import { ProviderConnectionsDialog, type ProviderConnection } from './ProviderConnectionsDialog';
import { createDomainClient } from '../../../host/transport';
import { DarwinexConsent } from '../Darwinex/disclaimer/darwinexDisclaimerPopup';
import { EquityDataUsageConditions } from '../SQData/Equity/add/dataUsageConditionsPopup';
import { FuturesDataUsageConditions } from '../SQData/Futures/add/dataUsageConditionsPopup';
import { useEffect, useState } from 'react';
import { Button, TextInput } from '../../../components/ui';
import { sourceClient, refreshSourceCatalog, useHistoricalSources, type SourceRecord } from './historicalSourceStore';

const providers: Record<string, string> = { darwinex: 'Darwinex', binance: 'Binance spot', binance_coinm: 'Binance Coin-M', binance_usdtm: 'Binance USDT-M', bitfinex: 'Bitfinex', coinbase: 'Coinbase', poloniex: 'Poloniex', yahoo: 'Yahoo', sq_equity: 'SQ Equity', sq_futures: 'SQ Futures', mt5: 'MT5' };
interface Props { provider: string; targets: SourceRecord[]; onClose: () => void; onStarted: () => void }
export function HistoricalSourceDialog({ provider: initial, targets, onClose, onStarted }: Props) {
  const [connectionId, setConnectionId] = useState(''); const [connectionDialog, setConnectionDialog] = useState(false);
  const [connections, setConnections] = useState<ProviderConnection[]>([]); const [connectionVersion,setConnectionVersion] = useState(0);
  const [agreed,setAgreed] = useState(false); const [catalog,setCatalog] = useState<string[]>([]); const [catalogQuery,setCatalogQuery] = useState('');
  const [provider, setProvider] = useState(initial);
  const [registered, setRegistered] = useState<SourceRecord[]>([]);
  const [unit, setUnit] = useState('0.00000001');
  const [symbols, setSymbols] = useState('');
  const [postfix, setPostfix] = useState(`_${initial}`);
  const [timeframe, setTimeframe] = useState('M1');
  const [timeframes, setTimeframes] = useState<string[]>([]);
  const [from, setFrom] = useState(new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10));
  const [to, setTo] = useState(new Date().toISOString().slice(0, 10));
  const [overwrite, setOverwrite] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [bridge, setBridge] = useState<{ connected: boolean; host?: string; port?: number; auth_token?: string; symbols?: string[] } | null>(null);
  useEffect(() => {setAgreed(false);setConnectionId('');setCatalog([]);setRegistered([]);},[provider]);
  useEffect(() => {let active=true;void createDomainClient('').get<ProviderConnection[]>('/connections').then(value=>{if(active) setConnections(value);}).catch(cause=>{if(active) setError(String(cause));});return()=>{active=false;};},[provider,connectionVersion]);
  useEffect(() => {
    let current = true; setTimeframes([]); setError('');
    if (targets.length) { setTimeframes([...new Set(targets.map(row => row.timeframe))]); return; }
    sourceClient.get<{ timeframes: string[]; default_timeframe: string }>(`/sources/${provider}/capabilities`).then(value => {
      if (current) { setTimeframes(value.timeframes); setTimeframe(value.default_timeframe); }
    }).catch(error => { if (current) setError(String(error)); });
    return () => { current = false; };
  }, [provider]);
  async function mt5(action: 'status' | 'connect') {
    setError(''); setBusy(true);
    try { setBridge(await sourceClient.post(`/sources/mt5/${action}`, {})); }
    catch (error) { setError(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(false); }
  }
  async function submit(download: boolean) {
    setError(''); setBusy(true);
    try {
      if (['darwinex','sq_equity','sq_futures'].includes(provider) && !agreed) throw new Error('Read and acknowledge the provider conditions first.');
      let records = registered.length ? registered : targets;
      if (!records.length) {
        const names = symbols.split(/[\s,;]+/).filter(Boolean);
        if (!names.length || new Set(names).size !== names.length) throw new Error('Enter one or more distinct provider symbols.');
        const result = await sourceClient.post<{ records: SourceRecord[] }>(`/sources/${provider}/add`, { definitions: names.map(symbol => ({ symbol: symbol + postfix, underlying: symbol, timeframe, tick_size: Number(unit), connection_id:connectionId || undefined })) });
        records = result.records; setRegistered(records);
        await refreshSourceCatalog();
      }
      if (download) await useHistoricalSources.getState().start(records, from, to, overwrite, connectionId || undefined);
      onStarted(); onClose();
    } catch (error) { setError(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(false); }
  }
  if (connectionDialog) return <ProviderConnectionsDialog provider={provider} onClose={()=>setConnectionDialog(false)} onSaved={id=>{setConnectionVersion(value=>value+1); setConnectionId(id);}}/>;
  return <div className="modal-backdrop"><div className="modal" role="dialog" aria-modal="true" aria-label={`${targets.length ? 'Download' : 'Add'} ${providers[provider] ?? provider} data`} aria-busy={busy}>
    <header><h2>{targets.length ? 'Download historical data' : `Add ${providers[provider]} data`}</h2><button aria-label="Close" disabled={busy} onClick={onClose}>×</button></header>
    <div className="modal-content">
      <div><label>Saved provider connection<select value={connectionId} onChange={event=>setConnectionId(event.target.value)}><option value="">Provider default</option>{connections.filter(row=>row.provider===provider).map(row=><option key={row.connection_id} value={row.connection_id}>{row.name}</option>)}</select></label><Button disabled={busy} onClick={()=>setConnectionDialog(true)}>Manage connections</Button></div>
      {provider === 'darwinex' && <DarwinexConsent agreed={agreed} setAgreed={setAgreed}/>}
      {provider === 'sq_equity' && <EquityDataUsageConditions/>}{provider === 'sq_futures' && <FuturesDataUsageConditions/>}
      {provider.startsWith('sq_') && <label><input type="checkbox" checked={agreed} onChange={event=>setAgreed(event.target.checked)}/>I agree to the displayed data usage conditions.</label>}
      {!targets.length && !registered.length && <>
        <Button disabled={busy} onClick={async()=>{try{setCatalog(await sourceClient.get<string[]>(`/sources/${provider}/catalog${connectionId ? `?connection_id=${encodeURIComponent(connectionId)}` : ''}`));}catch(cause){setError(String(cause));}}}>Load provider symbols</Button>
        {!!catalog.length && <><label>Filter provider symbols<TextInput value={catalogQuery} onChange={event=>setCatalogQuery(event.target.value)}/></label><select multiple aria-label="Provider instrument catalog" onChange={event=>setSymbols(Array.from(event.target.selectedOptions).map(option=>option.value).join(', '))}>{catalog.filter(symbol=>symbol.toLowerCase().includes(catalogQuery.toLowerCase())).slice(0,200).map(symbol=><option key={symbol}>{symbol}</option>)}</select><small>Showing up to 200 matching provider symbols.</small></>}

        <label>Data source <select aria-label="Data source" value={provider} disabled={busy} onChange={event => { setProvider(event.target.value); setPostfix(`_${event.target.value}`); }}>{Object.entries(providers).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
        <label>Provider symbols<textarea aria-label="Provider symbols" value={symbols} disabled={busy} placeholder={provider.startsWith('sq_') ? 'AAPL or @ES' : provider === 'yahoo' ? 'AAPL, MSFT, EURUSD=X' : 'EURUSD or BTCUSDT'} onChange={event => setSymbols(event.target.value)}/></label>
        <label>Data-name postfix<TextInput aria-label="Data-name postfix" value={postfix} disabled={busy} onChange={event => setPostfix(event.target.value)}/></label>
        <label>Timeframe<select aria-label="Timeframe" disabled={busy || !timeframes.length} value={timeframe} onChange={event => setTimeframe(event.target.value)}>{timeframes.map(tf => <option key={tf}>{tf}</option>)}</select></label>
      </>}
      {registered.length > 0 && <p>Registered: {registered.map(row => row.symbol).join(', ')}. You can start the download again without re-registering.</p>}
      {!targets.length && !registered.length && <label>Price storage unit<TextInput type="number" step="any" aria-label="Price storage unit" value={unit} onChange={event => setUnit(event.target.value)}/></label>}
      {targets.length > 0 && <p>{targets.map(row => `${row.symbol} (${row.timeframe})`).join(', ')}</p>}
      {provider === 'mt5' && <section aria-label="MT5 connection"><p>Connect the terminal EA to the local backend bridge before downloading.</p><Button disabled={busy} onClick={() => void mt5('connect')}>Start MT5 bridge</Button><Button disabled={busy} onClick={() => void mt5('status')}>Check MT5 connection</Button>{bridge && <><p>{bridge.connected ? 'MT5 connected' : 'Waiting for MT5 EA'} {bridge.host}:{bridge.port}</p>{bridge.auth_token && <label>EA authentication token<TextInput type="password" readOnly value={bridge.auth_token}/></label>}{bridge.symbols && <details><summary>Available symbols ({bridge.symbols.length})</summary><p>{bridge.symbols.slice(0, 50).join(', ')}{bridge.symbols.length > 50 ? ', …' : ''}</p></details>}</>}</section>}
      <label>From<TextInput type="date" aria-label="From" value={from} disabled={busy} onChange={event => setFrom(event.target.value)}/></label>
      <label>To<TextInput type="date" aria-label="To" value={to} disabled={busy} onChange={event => setTo(event.target.value)}/></label>
      <fieldset style={{display: 'grid', gap: '0.5rem'}}><legend>Download mode</legend><label><input type="radio" name="historical-download-mode" checked={!overwrite} disabled={busy} onChange={() => setOverwrite(false)}/>Add only missing data</label><label><input type="radio" name="historical-download-mode" checked={overwrite} disabled={busy} onChange={() => setOverwrite(true)}/>Overwrite existing data</label></fieldset>
      {provider === 'yahoo' && timeframe !== 'D1' && <p>Yahoo limits intraday history. Select recent dates; use daily bars for older history.</p>}
      {provider.startsWith('sq_') && <p>The existing SQ broker downloads daily data. Its configured sample CDN may not cover recent dates; select an available historical range (for example January 2024). Minute CDN history is not supplied by this adapter.</p>}
      {error && <div role="alert">{error}</div>}
    </div>
    <footer><Button disabled={busy} onClick={onClose}>Cancel</Button>{!targets.length && <Button disabled={busy || !timeframes.length} onClick={() => void submit(false)}>Add symbols</Button>}<Button disabled={busy || (!targets.length && !timeframes.length) || (provider === 'mt5' && !bridge?.connected)} onClick={() => void submit(true)}>{busy ? 'Submitting…' : targets.length ? 'Start download' : 'Add and download'}</Button></footer>
  </div></div>;
}
