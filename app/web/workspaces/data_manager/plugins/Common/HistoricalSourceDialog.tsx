import { ProviderConnectionsDialog, type ProviderConnection } from './ProviderConnectionsDialog';
import { createDomainClient } from '../../../../shell/transport';
import { DarwinexConsent } from '../Darwinex/disclaimer/darwinexDisclaimerPopup';
import { EquityDataUsageConditions } from '../SQData/Equity/add/dataUsageConditionsPopup';
import { FuturesDataUsageConditions } from '../SQData/Futures/add/dataUsageConditionsPopup';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Modal, TextInput } from '../../../../common/components/ui';
import '../SQData/Equity/styles.css';
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
  const [equityStep, setEquityStep] = useState<'search' | 'results' | 'configure'>('search');
  const [searchText, setSearchText] = useState('');
  const [searchTicker, setSearchTicker] = useState(true);
  const [exactMatch, setExactMatch] = useState(false);
  const [equityResults, setEquityResults] = useState<string[]>([]);
  const [selectedEquities, setSelectedEquities] = useState<string[]>([]);
  const [showEquityConditions, setShowEquityConditions] = useState(false);
  const lookupController = useRef<AbortController | null>(null);
  const equitySearch = provider === 'sq_equity' && !targets.length;
  const closeEquitySearch = useCallback(() => {
    if (showEquityConditions) { setShowEquityConditions(false); return; }
    lookupController.current?.abort(); lookupController.current = null; onClose();
    window.setTimeout(() => document.querySelector<HTMLButtonElement>('[data-control-id="sq-equity"]')?.focus(), 0);
  }, [showEquityConditions, onClose]);
  useEffect(() => () => { lookupController.current?.abort(); lookupController.current = null; }, []);
  useEffect(() => {
    lookupController.current?.abort(); lookupController.current = null; setBusy(false);
    setEquityStep('search'); setEquityResults([]); setSelectedEquities([]);
  }, [provider, connectionId]);
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
  async function lookupEquities() {
    setError(''); setEquityResults([]); setSelectedEquities([]);
    if (!searchTicker) { setError('Enable Search in ticker to search the provider catalogue.'); return; }
    lookupController.current?.abort();
    const controller = new AbortController();
    lookupController.current = controller;
    const deadline = window.setTimeout(() => controller.abort(), 15000);
    setBusy(true);
    try {
      const client = createDomainClient('/data', { signal: controller.signal });
      const response = await client.get<unknown>(`/sources/sq_equity/catalog${connectionId ? `?connection_id=${encodeURIComponent(connectionId)}` : ''}`);
      if (!Array.isArray(response) || response.length > 100000 || response.some(value => typeof value !== 'string' || !value.trim() || value.length > 128)) {
        throw new Error('The provider returned an invalid equity catalogue.');
      }
      const terms = searchText.split(/[,;\r\n]+/).map(term => term.trim().toLowerCase()).filter(Boolean);
      const matches = [...new Set(response as string[])].filter(symbol => !terms.length || terms.some(term => exactMatch ? symbol.toLowerCase() === term : symbol.toLowerCase().includes(term)));
      if (lookupController.current !== controller) return;
      setEquityResults(matches); setEquityStep('results');
    } catch (cause) {
      if (lookupController.current === controller) setError(controller.signal.aborted ? 'Equity lookup timed out. Please try again.' : cause instanceof Error ? cause.message : 'Equity lookup failed.');
    } finally {
      window.clearTimeout(deadline);
      if (lookupController.current === controller) { lookupController.current = null; setBusy(false); }
    }
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
  if (equitySearch && equityStep !== 'configure') {
    const visibleResults = equityResults.slice(0, 200);
    return <div className="sq-equity-search-flow" onKeyDown={event => {
      if (event.key !== 'Tab') return;
      const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]'));
      if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
      else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
    }}><Modal title={showEquityConditions ? 'HaruQuantAI Data Usage Conditions' : 'Add SQ Equity Data'} className="sq-equity-search-modal" width={1040} onClose={closeEquitySearch} footer={showEquityConditions ? <Button onClick={closeEquitySearch}>Close</Button> : <>
      <div className="sq-equity-consent"><label className="sq-equity-switch"><input type="checkbox" checked={agreed} onChange={event => setAgreed(event.target.checked)}/><span>I confirm that I agree to</span></label><button className="sq-data-link" onClick={() => setShowEquityConditions(true)}>HaruQuantAI Data Usage Conditions</button></div>
      <div className="sq-equity-footer-actions"><button className="sq-data-link" onClick={closeEquitySearch}>Close</button>{equityStep === 'results' && <Button className="primary" disabled={!agreed || !selectedEquities.length || busy} onClick={() => { setSymbols(selectedEquities.join(', ')); setError(''); setEquityStep('configure'); }}>Continue</Button>}</div>
    </>}>
      {showEquityConditions ? <EquityDataUsageConditions/> : <>
        <section className="sq-equity-search-panel" aria-label="Find equity data">
          {equityStep === 'search' ? <>
            <h3>Find data by</h3>
            <div className="sq-equity-search-fields">
              <label className="sq-equity-field"><span>Exchange</span><select aria-label="Exchange" disabled title="Exchange metadata is unavailable from this catalogue"><option>Any</option></select></label>
              <div className="sq-equity-options"><div><label className="sq-equity-switch"><input type="checkbox" checked={searchTicker} disabled={busy} onChange={event => setSearchTicker(event.target.checked)}/><span>Search in ticker</span></label><label className="sq-equity-switch"><input type="checkbox" checked={exactMatch} disabled={busy || !searchTicker} onChange={event => setExactMatch(event.target.checked)}/><span>Exact match</span></label></div><label className="sq-equity-switch" title="Company-name metadata is unavailable from this catalogue"><input type="checkbox" checked={false} disabled readOnly/><span>Search in name</span></label></div>
              <label className="sq-equity-field sq-equity-search-text"><span>Search text</span><textarea maxLength={10000} value={searchText} disabled={busy} onChange={event => setSearchText(event.target.value)}/></label>
              <div className="sq-equity-search-actions"><p className="sq-equity-help">You can enter multiple symbols separated by comma, semicolon or new line.<br/>for example: AAPL, MSFT, AMZN</p><Button className="primary" disabled={busy} onClick={() => void lookupEquities()}>{busy ? 'Looking up…' : 'Lookup'}</Button><p className="sq-equity-metadata-note">Exchange and company-name filters are unavailable for this catalogue.</p></div>
              <div className="sq-equity-field sq-equity-availability"><span>Data availability</span><div><p><span aria-hidden="true">{timeframes.includes('D1') ? '✓' : '—'}</span> {timeframes.includes('D1') ? 'End of Day data supported; subscription status unavailable' : 'End of Day data availability not verified'}</p><p><span aria-hidden="true">—</span> Intraday (M1) data is not supplied by this adapter</p></div></div>
            </div>
          </> : <>
            <Button onClick={() => { setEquityStep('search'); setError(''); }}>‹ Search again</Button>
            <h3>Choose equity symbols to add</h3>
            <p role="status">Found: {equityResults.length}, selected: {selectedEquities.length}</p>
            <div className="sq-equity-result-grid"><table className="plain-table" aria-label="Equity search results"><thead><tr><th><input type="checkbox" aria-label="Select all displayed tickers" checked={visibleResults.length > 0 && visibleResults.every(symbol => selectedEquities.includes(symbol))} disabled={!visibleResults.length} onChange={event => setSelectedEquities(event.target.checked ? visibleResults : [])}/></th><th>Ticker</th></tr></thead><tbody>{visibleResults.map(symbol => <tr key={symbol}><td><input type="checkbox" aria-label={`Select ticker ${symbol}`} checked={selectedEquities.includes(symbol)} onChange={event => setSelectedEquities(current => event.target.checked ? [...current, symbol] : current.filter(value => value !== symbol))}/></td><td>{symbol}</td></tr>)}{!equityResults.length && <tr><td colSpan={2}>No tickers found.</td></tr>}</tbody></table></div>
            {equityResults.length > 200 && <p>Showing the first 200 matches. Refine your search to find other tickers.</p>}
          </>}
          {error && <p role="alert" className="sq-data-error">{error}</p>}
        </section>
      </>}
    </Modal></div>;
  }
  return <div className="modal-backdrop"><div className="modal" role="dialog" aria-modal="true" aria-label={`${targets.length ? 'Download' : 'Add'} ${providers[provider] ?? provider} data`} aria-busy={busy}>
    <header><h2>{targets.length ? 'Download historical data' : `Add ${providers[provider]} data`}</h2><button aria-label="Close" disabled={busy} onClick={onClose}>×</button></header>
    <div className="modal-content">
      {equitySearch && !registered.length && <Button disabled={busy} onClick={() => setEquityStep('results')}>‹ Back to search results</Button>}
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
