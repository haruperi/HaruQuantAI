import { ProviderConnectionsDialog, type ProviderConnection } from './ProviderConnectionsDialog';
import { createDomainClient } from '../../../../shell/transport';
import { DarwinexConsent } from '../Darwinex/disclaimer/darwinexDisclaimerPopup';
import { EquityDataUsageConditions } from '../SQData/Equity/add/dataUsageConditionsPopup';
import { FuturesDataUsageConditions } from '../SQData/Futures/add/dataUsageConditionsPopup';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Modal, TextInput } from '../../../../common/components/ui';
import '../SQData/Equity/styles.css';
import '../SQData/Futures/styles.css';
import '../Darwinex/add/styles.css';
import '../Crypto/style.css';
import '../Yahoo/style.css';
import { useDataManagerStore } from './dataManagerStore';
import { sourceClient, refreshSourceCatalog, useHistoricalSources, type SourceRecord } from './historicalSourceStore';

const providers: Record<string, string> = { darwinex: 'Darwinex', binance: 'Binance spot', binance_coinm: 'Binance Coin-M', binance_usdtm: 'Binance USDT-M', bitfinex: 'Bitfinex', coinbase: 'Coinbase', poloniex: 'Poloniex', yahoo: 'Yahoo', sq_equity: 'SQ Equity', sq_futures: 'SQ Futures', mt5: 'MT5' };
import { HistoricalDownloadDialog } from './HistoricalDownloadDialog';
interface Props { provider: string; targets: SourceRecord[]; onClose: () => void; onStarted: () => void }
export function HistoricalSourceDialog(props: Props) {
  return props.targets.length ? <HistoricalDownloadDialog {...props}/> : <HistoricalAddDialog {...props}/>;
}
function HistoricalAddDialog({ provider: initial, targets, onClose, onStarted }: Props) {
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
  const brokerProfiles = useDataManagerStore(state => state.brokers);
  const [darwinexBroker, setDarwinexBroker] = useState('');
  const [darwinexSelected, setDarwinexSelected] = useState<string[]>([]);
  const [darwinexLoading, setDarwinexLoading] = useState(false);
  const [darwinexError, setDarwinexError] = useState('');
  const [darwinexRetry, setDarwinexRetry] = useState(0);
  const [darwinexDescending, setDarwinexDescending] = useState(false);
  const darwinexSubmitting = useRef(false);
  const darwinexAdd = provider === 'darwinex' && !targets.length;
  const cryptoAdd = ['binance', 'binance_coinm', 'binance_usdtm', 'bitfinex', 'coinbase', 'poloniex'].includes(provider) && !targets.length;
  const yahooAdd = provider === 'yahoo' && !targets.length;
  const symbolAdd = cryptoAdd || yahooAdd;
  const cryptoName = provider === 'binance' ? 'Binance' : provider === 'coinbase' ? 'Coinbase Pro' : providers[provider];
  const [symbolSelected, setSymbolSelected] = useState<string[]>([]);
  const [symbolLoading, setSymbolLoading] = useState(false);
  const [symbolError, setSymbolError] = useState('');
  const [symbolRetry, setSymbolRetry] = useState(0);
  const symbolSubmitting = useRef(false);
  useEffect(() => {
    if (!cryptoAdd) return;
    let active = true;
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 15000);
    setSymbolLoading(true); setSymbolError(''); setCatalog([]); setSymbolSelected([]);
    createDomainClient('/data', { signal: controller.signal }).get<unknown>(`/sources/${provider}/catalog${connectionId ? `?connection_id=${encodeURIComponent(connectionId)}` : ''}`)
      .then(value => {
        if (!Array.isArray(value) || value.length > 100000 || value.some(item => typeof item !== 'string' || !item.trim() || item.length > 128)) throw new Error('The provider returned an invalid symbol catalogue.');
        if (active) setCatalog([...new Set(value as string[])]);
      }).catch(cause => { if (active) setSymbolError(controller.signal.aborted ? 'Symbol catalogue request timed out. Please retry.' : cause instanceof Error ? cause.message : 'Unable to load symbols.'); })
      .finally(() => { window.clearTimeout(timer); if (active) setSymbolLoading(false); });
    return () => { active = false; window.clearTimeout(timer); controller.abort(); };
  }, [cryptoAdd, provider, connectionId, connectionVersion, symbolRetry]);
  const [searchStep, setSearchStep] = useState<'search' | 'results' | 'configure'>('search');
  const [searchText, setSearchText] = useState('');
  const [searchTicker, setSearchTicker] = useState(true);
  const [exactMatch, setExactMatch] = useState(false);
  const [searchResults, setSearchResults] = useState<string[]>([]);
  const [selectedTickers, setSelectedTickers] = useState<string[]>([]);
  const [showConditions, setShowConditions] = useState(false);
  const lookupController = useRef<AbortController | null>(null);
  const isFutures = provider === 'sq_futures';
  const sqLabel = isFutures ? 'Futures' : 'Equity';
  const sqSearch = ['sq_equity', 'sq_futures'].includes(provider) && !targets.length;
  const closeSQSearch = useCallback(() => {
    if (darwinexSubmitting.current || symbolSubmitting.current) return;
    if (showConditions) { setShowConditions(false); return; }
    lookupController.current?.abort(); lookupController.current = null; onClose();
    window.setTimeout(() => document.querySelector<HTMLButtonElement>(`[data-control-id="${provider.replace('_', '-')}"]`)?.focus(), 0);
  }, [showConditions, onClose, provider]);
  useEffect(() => () => { lookupController.current?.abort(); lookupController.current = null; }, []);
  useEffect(() => {
    lookupController.current?.abort(); lookupController.current = null; setBusy(false);
    setSearchStep('search'); setSearchResults([]); setSelectedTickers([]);
  }, [provider, connectionId]);
  useEffect(() => {
    if (!darwinexAdd) return;
    let active = true;
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 15000);
    setDarwinexLoading(true); setDarwinexError(''); setCatalog([]); setDarwinexSelected([]);
    createDomainClient('/data', { signal: controller.signal }).get<unknown>(`/sources/darwinex/catalog${connectionId ? `?connection_id=${encodeURIComponent(connectionId)}` : ''}`)
      .then(value => {
        if (!Array.isArray(value) || value.length > 100000 || value.some(symbol => typeof symbol !== 'string' || !symbol.trim() || symbol.length > 128)) throw new Error('The provider returned an invalid Darwinex catalogue.');
        if (active) setCatalog([...new Set(value as string[])]);
      }).catch(cause => { if (active) setDarwinexError(controller.signal.aborted ? 'Darwinex catalogue request timed out. Please retry.' : cause instanceof Error ? cause.message : 'Unable to load the Darwinex catalogue.'); })
      .finally(() => { window.clearTimeout(timer); if (active) setDarwinexLoading(false); });
    return () => { active = false; window.clearTimeout(timer); controller.abort(); };
  }, [darwinexAdd, connectionId, connectionVersion, darwinexRetry]);
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
  }, [provider, darwinexRetry, symbolRetry]);
  async function mt5(action: 'status' | 'connect') {
    setError(''); setBusy(true);
    try { setBridge(await sourceClient.post(`/sources/mt5/${action}`, {})); }
    catch (error) { setError(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(false); }
  }
  async function lookupSymbols() {
    setError(''); setSearchResults([]); setSelectedTickers([]);
    if (!searchTicker) { setError('Enable Search in ticker to search the provider catalogue.'); return; }
    lookupController.current?.abort();
    const controller = new AbortController();
    lookupController.current = controller;
    const deadline = window.setTimeout(() => controller.abort(), 15000);
    setBusy(true);
    try {
      const client = createDomainClient('/data', { signal: controller.signal });
      const response = await client.get<unknown>(`/sources/${provider}/catalog${connectionId ? `?connection_id=${encodeURIComponent(connectionId)}` : ''}`);
      if (!Array.isArray(response) || response.length > 100000 || response.some(value => typeof value !== 'string' || !value.trim() || value.length > 128)) {
        throw new Error(`The provider returned an invalid ${sqLabel.toLowerCase()} catalogue.`);
      }
      const terms = searchText.split(/[,;\r\n]+/).map(term => term.trim().toLowerCase()).filter(Boolean);
      const matches = [...new Set(response as string[])].filter(symbol => !terms.length || terms.some(term => exactMatch ? symbol.toLowerCase() === term : symbol.toLowerCase().includes(term)));
      if (lookupController.current !== controller) return;
      setSearchResults(matches); setSearchStep('results');
    } catch (cause) {
      if (lookupController.current === controller) setError(controller.signal.aborted ? `${sqLabel} lookup timed out. Please try again.` : cause instanceof Error ? cause.message : `${sqLabel} lookup failed.`);
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
  async function saveDarwinex() {
    if (darwinexSubmitting.current) return;
    setError('');
    if (!darwinexSelected.length) { setError('No symbols selected'); return; }
    if (!agreed) { setError('Please confirm the Darwinex data disclaimer before saving.'); return; }
    if (darwinexLoading || darwinexError || !timeframes.includes(timeframe)) { setError('Load the provider catalogue and capabilities before saving.'); return; }
    const broker = brokerProfiles.find(profile => profile.id === darwinexBroker && profile.mtUse);
    if (darwinexBroker && !broker) { setError('Choose an available broker profile.'); return; }
    if (darwinexSelected.some(symbol => !catalog.includes(symbol))) { setError('Select symbols from the current Darwinex catalogue.'); return; }
    darwinexSubmitting.current = true; setBusy(true);
    try {
      if (!registered.length) {
        const result = await sourceClient.post<{ records: SourceRecord[] }>('/sources/darwinex/add', {
          definitions: darwinexSelected.map(symbol => ({ symbol: symbol + postfix, underlying: symbol, timeframe, tick_size: Number(unit), broker: broker?.name, connection_id: connectionId || undefined })),
        });
        if (!Array.isArray(result?.records) || result.records.length !== darwinexSelected.length) throw new Error('The host did not confirm all selected datasets.');
        setRegistered(result.records);
      }
      await refreshSourceCatalog();
      if (useDataManagerStore.getState().catalogError) throw new Error('Datasets were registered, but the catalogue refresh failed. Retry refresh.');
      onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add Darwinex data.'); }
    finally { darwinexSubmitting.current = false; setBusy(false); }
  }
  async function saveSymbols() {
    if (symbolSubmitting.current) return;
    setError('');
    const names = cryptoAdd ? symbolSelected : symbols.split(/[,;\r\n]+/).map(value => value.trim()).filter(Boolean);
    if (!names.length || new Set(names).size !== names.length) { setError('Enter or select at least one distinct symbol.'); return; }
    if (cryptoAdd && !agreed) { setError('Please confirm the provider data disclaimer before saving.'); return; }
    if (!timeframes.includes(timeframe) || symbolLoading || symbolError) { setError('Load provider capabilities and symbols before saving.'); return; }
    if (cryptoAdd && names.some(name => !catalog.includes(name))) { setError('Select symbols from the current catalogue.'); return; }
    symbolSubmitting.current = true; setBusy(true);
    try {
      if (!registered.length) {
        const result = await sourceClient.post<{ records: SourceRecord[] }>(`/sources/${provider}/add`, {
          definitions: names.map(name => ({ symbol: name + postfix, underlying: name, timeframe, tick_size: Number(unit), connection_id: connectionId || undefined })),
        });
        if (!Array.isArray(result?.records) || result.records.length !== names.length) throw new Error('The host did not confirm all selected datasets.');
        setRegistered(result.records);
      }
      await refreshSourceCatalog();
      if (useDataManagerStore.getState().catalogError) throw new Error('Datasets were registered, but the catalogue refresh failed. Retry refresh.');
      onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add symbols.'); }
    finally { symbolSubmitting.current = false; setBusy(false); }
  }
  if (connectionDialog) return <ProviderConnectionsDialog provider={provider} onClose={()=>setConnectionDialog(false)} onSaved={id=>{setConnectionVersion(value=>value+1); setConnectionId(id);}}/>;
  if (symbolAdd) {
    const locked = busy || registered.length > 0;
    const matches = catalog.filter(name => name.toLowerCase().includes(catalogQuery.trim().toLowerCase())).sort();
    const visible = matches.slice(0, 500);
    const all = visible.length > 0 && visible.every(name => symbolSelected.includes(name));
    return <div className={`${cryptoAdd ? 'crypto' : 'yahoo'}-flow host-symbol-add`} onKeyDown={event => {
      if (event.key !== 'Tab') return;
      const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),summary,a[href]'));
      if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
      else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
    }}><Modal title={cryptoAdd ? `Add ${cryptoName} symbol(s)` : 'Add Yahoo data'} width={cryptoAdd ? 900 : 800} onClose={closeSQSearch} footer={<>
      {cryptoAdd && <label className="crypto-consent"><input type="checkbox" disabled={locked} checked={agreed} onChange={event => { setAgreed(event.target.checked); setError(''); }}/>I confirm that I understand the following: Data are provided for free by {cryptoName}. HaruQuantAI Data Manager is only a tool to download the data directly to the program. HaruQuantAI is not responsible for quality or availability of the data.</label>}
      <Button disabled={busy} onClick={closeSQSearch}>Close</Button><Button className="primary" disabled={busy || symbolLoading || Boolean(symbolError) || !timeframes.length} onClick={() => void saveSymbols()}>{busy ? 'Saving�' : registered.length ? 'Retry refresh' : 'Save'}</Button>
    </>}>
      {error && <p role="alert" className={cryptoAdd ? 'crypto-error' : 'yahoo-error'}>{error}</p>}
      <fieldset disabled={locked} className={cryptoAdd ? 'crypto-catalogue' : 'yahoo-add-fieldset'}><legend>{cryptoAdd ? 'Choose from available data' : 'Add data to download'}</legend>
        {cryptoAdd ? <>
          <TextInput aria-label="Filter items" placeholder="Filter items" value={catalogQuery} onChange={event => setCatalogQuery(event.target.value)}/>
          {symbolLoading && <p role="status">Loading symbols�</p>}
          {symbolError && <p role="alert">{symbolError} <Button onClick={() => setSymbolRetry(value => value + 1)}>Retry catalogue</Button></p>}
          <div className="crypto-grid"><table className="plain-table" aria-label={`${cryptoName} symbols`}><thead><tr><th><input type="checkbox" aria-label="Select all displayed symbols" checked={all} disabled={!visible.length} onChange={event => setSymbolSelected(current => event.target.checked ? [...new Set([...current, ...visible])] : current.filter(name => !visible.includes(name)))}/></th><th>Symbol</th></tr></thead><tbody>{visible.map(name => <tr key={name} className={symbolSelected.includes(name) ? 'selected' : ''}><td><input type="checkbox" aria-label={`Select symbol ${name}`} checked={symbolSelected.includes(name)} onChange={event => setSymbolSelected(current => event.target.checked ? [...current, name] : current.filter(value => value !== name))}/></td><td>{name}</td></tr>)}{!visible.length && <tr><td colSpan={2}>{symbolLoading ? 'Loading�' : 'No symbols available.'}</td></tr>}</tbody></table></div>
          <p role="status">{matches.length} matching symbols, {symbolSelected.length} selected{matches.length > 500 ? ' � Showing the first 500 matches; refine the filter for more.' : ''}</p>
          <label>Timeframe<select aria-label="Timeframe" value={timeframe} disabled={!timeframes.length} onChange={event => setTimeframe(event.target.value)}>{timeframes.map(value => <option key={value}>{value}</option>)}</select></label>
        </> : <><div className="yahoo-help"><p>Please enter a list of stocks tickers you want to add, separated by comma, semicolon or newline.</p><p>For example: AAPL, AMZN, TSLA</p></div><textarea aria-label="Yahoo symbols" maxLength={10000} value={symbols} onChange={event => setSymbols(event.target.value)}/></>}
        <label className="host-symbol-postfix">Data postfix<TextInput aria-label="Data postfix" maxLength={64} value={postfix} onChange={event => setPostfix(event.target.value)}/><small>This postfix will be optionally added to the data names created</small></label>
      </fieldset>
      <details><summary>Provider connection</summary><label>Saved provider connection<select value={connectionId} disabled={locked} onChange={event => setConnectionId(event.target.value)}><option value="">Provider default</option>{connections.filter(row => row.provider === provider).map(row => <option key={row.connection_id} value={row.connection_id}>{row.name}</option>)}</select></label><Button disabled={locked} onClick={() => setConnectionDialog(true)}>Manage connections</Button></details>
      {!timeframes.length && !busy && <Button onClick={() => setSymbolRetry(value => value + 1)}>Retry capabilities</Button>}
    </Modal></div>;
  }
  if (darwinexAdd) {
    const locked = busy || registered.length > 0;
    const rows = catalog.filter(symbol => symbol.toLowerCase().includes(catalogQuery.trim().toLowerCase())).sort((a, b) => a.localeCompare(b) * (darwinexDescending ? -1 : 1));
    const displayed = rows.slice(0, 500);
    const allSelected = displayed.length > 0 && displayed.every(symbol => darwinexSelected.includes(symbol));
    return <div className="darwinex-flow darwinex-host-add-flow" onKeyDown={event => {
      if (event.key !== 'Tab') return;
      const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),summary,a[href]'));
      if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
      else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
    }}><Modal title="Add Darwinex data" width={850} className="darwinex-host-add-modal" onClose={closeSQSearch} footer={<>
      <fieldset className="darwinex-host-consent" disabled={locked}><DarwinexConsent agreed={agreed} setAgreed={setAgreed}/></fieldset>
      <Button disabled={busy} onClick={closeSQSearch}>Close</Button><Button className="primary" disabled={busy || darwinexLoading || Boolean(darwinexError) || !timeframes.length} onClick={() => void saveDarwinex()}>{busy ? 'Saving…' : registered.length ? 'Retry refresh' : 'Save'}</Button>
    </>}>
      {error && <p role="alert" className="darwinex-error">{error}</p>}
      <fieldset className="darwinex-host-catalogue"><legend>Choose from available data</legend>
        <TextInput aria-label="Filter Darwinex symbols" placeholder="Filter items" value={catalogQuery} disabled={locked} onChange={event => setCatalogQuery(event.target.value)}/>
        {darwinexLoading && <p role="status">Loading Darwinex catalogue…</p>}
        {darwinexError && <p role="alert" className="darwinex-error">{darwinexError} <Button onClick={() => setDarwinexRetry(value => value + 1)}>Retry catalogue</Button></p>}
        <div className="darwinex-grid"><table className="plain-table" aria-label="Available Darwinex data"><thead><tr>
          <th><input type="checkbox" aria-label="Select all displayed Darwinex symbols" disabled={locked || !displayed.length} checked={allSelected} onChange={event => setDarwinexSelected(current => event.target.checked ? [...new Set([...current, ...displayed])] : current.filter(symbol => !displayed.includes(symbol)))}/></th>
          <th aria-sort={darwinexDescending ? 'descending' : 'ascending'}><button onClick={() => setDarwinexDescending(value => !value)}>Symbol</button></th><th>Available data range</th>
        </tr></thead><tbody>{displayed.map(symbol => <tr key={symbol} className={darwinexSelected.includes(symbol) ? 'selected' : ''}><td><input type="checkbox" aria-label={`Select symbol ${symbol}`} disabled={locked} checked={darwinexSelected.includes(symbol)} onChange={event => setDarwinexSelected(current => event.target.checked ? [...current, symbol] : current.filter(value => value !== symbol))}/></td><td>{symbol}</td><td>Not supplied by provider catalogue</td></tr>)}{!displayed.length && <tr><td colSpan={3}>{darwinexLoading ? 'Loading…' : darwinexError ? 'Catalogue unavailable.' : 'No Darwinex symbols available.'}</td></tr>}</tbody></table></div>
        <p role="status">{rows.length} matching symbols, {darwinexSelected.length} selected{rows.length > 500 ? ' · Showing the first 500 matches; refine the filter for more.' : ''}</p>
        <div className="darwinex-details"><label>Broker profile *<select aria-label="Broker profile" value={darwinexBroker} disabled={locked} onChange={event => { const profile = brokerProfiles.find(item => item.id === event.target.value); setDarwinexBroker(event.target.value); setPostfix(profile?.postfix ?? '_darwinex'); }}><option value="">Default</option>{brokerProfiles.filter(profile => profile.mtUse).map(profile => <option key={profile.id} value={profile.id}>{profile.name}</option>)}</select></label>
          <label>Data postfix<TextInput aria-label="Data postfix" maxLength={64} value={postfix} disabled={locked} onChange={event => setPostfix(event.target.value)}/><small>This postfix will optionally be added to the data names created.</small></label></div>
        {darwinexBroker && <p className="darwinex-host-note">The broker profile is recorded with the dataset. Timestamps remain in UTC; automatic timezone conversion and instrument mapping are not configured.</p>}
        {registered.length > 0 && <p role="status">Datasets were registered. Retry refresh to update the catalogue without registering them again.</p>}
      </fieldset>
      <details className="darwinex-host-connection"><summary>Provider connection</summary><label>Saved provider connection<select value={connectionId} disabled={locked} onChange={event => setConnectionId(event.target.value)}><option value="">Provider default</option>{connections.filter(connection => connection.provider === 'darwinex').map(connection => <option key={connection.connection_id} value={connection.connection_id}>{connection.name}</option>)}</select></label><Button disabled={locked} onClick={() => setConnectionDialog(true)}>Manage connections</Button></details>
    </Modal></div>;
  }
  if (sqSearch && searchStep !== 'configure') {
    const visibleResults = searchResults.slice(0, 200);
    return <div className={`sq-equity-search-flow${isFutures ? ' sq-futures-search-flow' : ''}`} onKeyDown={event => {
      if (event.key !== 'Tab') return;
      const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]'));
      if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
      else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
    }}><Modal title={showConditions ? 'HaruQuantAI Data Usage Conditions' : `Add SQ ${sqLabel} Data`} className="sq-equity-search-modal" width={isFutures ? 800 : 1040} onClose={closeSQSearch} footer={showConditions ? <Button onClick={closeSQSearch}>Close</Button> : <>
      <div className="sq-equity-consent"><label className="sq-equity-switch"><input type="checkbox" checked={agreed} onChange={event => setAgreed(event.target.checked)}/><span>I confirm that I agree to</span></label><button className="sq-data-link" onClick={() => setShowConditions(true)}>HaruQuantAI Data Usage Conditions</button></div>
      <div className="sq-equity-footer-actions"><button className="sq-data-link" onClick={closeSQSearch}>Close</button>{searchStep === 'results' && <Button className="primary" disabled={!agreed || !selectedTickers.length || busy} onClick={() => { setSymbols(selectedTickers.join(', ')); setError(''); setSearchStep('configure'); }}>Continue</Button>}</div>
    </>}>
      {showConditions ? isFutures ? <FuturesDataUsageConditions/> : <EquityDataUsageConditions/> : <>
        <section className="sq-equity-search-panel" aria-label={`Find ${sqLabel.toLowerCase()} data`}>
          {searchStep === 'search' ? <>
            <h3>Find data by</h3>
            <div className="sq-equity-search-fields">
              <div className={isFutures ? "sq-futures-search-row" : undefined}><label className="sq-equity-field"><span>Exchange</span><select aria-label="Exchange" disabled title="Exchange metadata is unavailable from this catalogue"><option>Any</option></select></label>{isFutures && <label className="sq-equity-switch" title="Contract-type metadata is unavailable from this catalogue"><input type="checkbox" checked={false} disabled readOnly/><span>Only continuous futures</span></label>}</div>
              <div className="sq-equity-options"><div><label className="sq-equity-switch"><input type="checkbox" checked={searchTicker} disabled={busy} onChange={event => setSearchTicker(event.target.checked)}/><span>Search in ticker</span></label><label className="sq-equity-switch"><input type="checkbox" checked={exactMatch} disabled={busy || !searchTicker} onChange={event => setExactMatch(event.target.checked)}/><span>Exact match</span></label></div><label className="sq-equity-switch" title="Company-name metadata is unavailable from this catalogue"><input type="checkbox" checked={false} disabled readOnly/><span>Search in name</span></label></div>
              <label className="sq-equity-field sq-equity-search-text"><span>Search text</span><textarea maxLength={10000} value={searchText} disabled={busy} onChange={event => setSearchText(event.target.value)}/></label>
              <div className="sq-equity-search-actions"><p className="sq-equity-help">You can enter multiple symbols separated by comma, semicolon or new line.<br/>for example: {isFutures ? 'ES, 6E, SPY' : 'AAPL, MSFT, AMZN'}</p><Button className="primary" disabled={busy} onClick={() => void lookupSymbols()}>{busy ? 'Looking up…' : 'Lookup'}</Button><p className="sq-equity-metadata-note">{isFutures ? 'Exchange, contract-type and name filters are unavailable for this catalogue.' : 'Exchange and company-name filters are unavailable for this catalogue.'}</p></div>
              <div className="sq-equity-field sq-equity-availability"><span>Data availability</span><div><p><span aria-hidden="true">{timeframes.includes('D1') ? '✓' : '—'}</span> {timeframes.includes('D1') ? 'End of Day data supported; subscription status unavailable' : 'End of Day data availability not verified'}</p><p><span aria-hidden="true">—</span> Intraday (M1) data is not supplied by this adapter</p></div></div>
            </div>
          </> : <>
            <Button onClick={() => { setSearchStep('search'); setError(''); }}>‹ Search again</Button>
            <h3>Choose {sqLabel.toLowerCase()} symbols to add</h3>
            <p role="status">Found: {searchResults.length}, selected: {selectedTickers.length}</p>
            <div className="sq-equity-result-grid"><table className="plain-table" aria-label={`${sqLabel} search results`}><thead><tr><th><input type="checkbox" aria-label="Select all displayed tickers" checked={visibleResults.length > 0 && visibleResults.every(symbol => selectedTickers.includes(symbol))} disabled={!visibleResults.length} onChange={event => setSelectedTickers(event.target.checked ? visibleResults : [])}/></th><th>Ticker</th></tr></thead><tbody>{visibleResults.map(symbol => <tr key={symbol}><td><input type="checkbox" aria-label={`Select ticker ${symbol}`} checked={selectedTickers.includes(symbol)} onChange={event => setSelectedTickers(current => event.target.checked ? [...current, symbol] : current.filter(value => value !== symbol))}/></td><td>{symbol}</td></tr>)}{!searchResults.length && <tr><td colSpan={2}>No tickers found.</td></tr>}</tbody></table></div>
            {searchResults.length > 200 && <p>Showing the first 200 matches. Refine your search to find other tickers.</p>}
          </>}
          {error && <p role="alert" className="sq-data-error">{error}</p>}
        </section>
      </>}
    </Modal></div>;
  }
  return <div className="modal-backdrop"><div className="modal" role="dialog" aria-modal="true" aria-label={`${targets.length ? 'Download' : 'Add'} ${providers[provider] ?? provider} data`} aria-busy={busy}>
    <header><h2>{targets.length ? 'Download historical data' : `Add ${providers[provider]} data`}</h2><button aria-label="Close" disabled={busy} onClick={onClose}>×</button></header>
    <div className="modal-content">
      {sqSearch && !registered.length && <Button disabled={busy} onClick={() => setSearchStep('results')}>‹ Back to search results</Button>}
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
