import type { ComponentType } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../../components/ui';
import { timezones } from '../../../FileImport/fileImport';
import { providerLabel, sqAllowed, sqExchanges } from '../../sqData';
import { useSQEquityDataAdd, type SQAddCallbacks } from './SQEquityDataAddCtrl';
import { EquityDataUsageConditions } from './dataUsageConditionsPopup';
import '../styles.css';
export function SQEquityAddPopup(props: SQAddCallbacks) { return <SQDataAddView controller={useSQEquityDataAdd(props)} Conditions={EquityDataUsageConditions}/>; }
export function SQDataAddView({ controller, Conditions }: { controller: ReturnType<typeof useSQEquityDataAdd>; Conditions: ComponentType }) {
  const { provider, store, profile, notify, config, results, lookedUp, selected, agreed, conditions, busy, error, sort, container, subscription, cancelLookup, close, patch, lookup, add, eligible, allSelected, rows, columns, setConditions, setAgreed, setSelected, setSort, setResults, setLookedUp, setError } = controller;
  return <div className="sq-data-flow" ref={container} onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const elements = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]'));
    if (event.shiftKey && document.activeElement === elements[0]) { event.preventDefault(); elements.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === elements.at(-1)) { event.preventDefault(); elements[0]?.focus(); }
  }}><Modal key={conditions ? 'conditions' : 'main'} title={conditions ? 'HaruQuantAI Data Usage Conditions' : `Add ${providerLabel(provider)}`} width={conditions ? 700 : 800} onClose={close} footer={conditions ? <Button onClick={close}>Close</Button> : <>
    <div className="sq-data-consent"><label><input type="checkbox" checked={agreed} onChange={event => setAgreed(event.target.checked)}/> I confirm that I agree to</label> <button className="sq-data-link" data-sq-conditions onClick={() => setConditions(true)}>HaruQuantAI Data Usage Conditions</button></div>
    <Button onClick={close}>Close</Button>{results.length > 0 && <Button className="primary" disabled={busy} onClick={add}>Add</Button>}
  </>}>
    {conditions ? <Conditions/> : <>
      {(error || store.storageError) && <p className="sq-data-error" role="alert">{error || store.storageError}</p>}
      <fieldset className="sq-data-main">
        {!lookedUp ? <>
          <legend>Find data by</legend>
          <div className="sq-data-search-row"><Field label="Exchange"><select aria-label="Exchange" value={config.exchange} disabled={busy} onChange={event => patch({ exchange: event.target.value })}><option value="">All exchanges</option>{sqExchanges(provider).map(exchange => <option key={exchange}>{exchange}</option>)}</select></Field>{provider === 'futures' && <label><input type="checkbox" disabled={busy} checked={config.onlyContFutures} onChange={event => patch({ onlyContFutures: event.target.checked })}/> Only continuous futures</label>}</div>
          <div className="sq-data-search-options"><div><label><input type="checkbox" disabled={busy} checked={config.searchInTicker} onChange={event => patch({ searchInTicker: event.target.checked })}/> Search in ticker</label><label><input type="checkbox" disabled={busy || (provider === 'equity' && !config.searchInTicker)} checked={config.exact} onChange={event => patch({ exact: event.target.checked })}/> Exact match</label></div><label><input type="checkbox" disabled={busy} checked={config.searchInName} onChange={event => patch({ searchInName: event.target.checked })}/> Search in name</label></div>
          <Field label="Search text"><textarea className="text-area" maxLength={10000} disabled={busy} value={config.symbols} onChange={event => patch({ symbols: event.target.value })}/></Field>
          <p className="sq-data-help">You can enter multiple symbols separated by comma, semicolon or new line.<br/>for example: {provider === 'equity' ? 'AAPL, Microsoft, Amazon' : 'ES, 6E, SPY'}</p>
          <div><Button className="primary" disabled={busy} onClick={lookup}>{busy ? 'Looking up…' : 'Lookup'}</Button></div>
          <div className="sq-data-availability"><strong>Data availability <small>(mock)</small></strong><div>{([['eodSubscriptionActive', 'End of Day'], ['minuteSubscriptionActive', 'Intraday (M1)']] as const).map(([key, label]) => <p key={key}><span className={subscription[key] ? 'sq-data-active' : 'sq-data-inactive'} aria-hidden="true">{subscription[key] ? '✓' : '×'}</span> {label} data subscription {subscription[key] ? 'active' : 'not active'} {!subscription[key] && <button className="sq-data-link" onClick={() => notify('Data subscriptions are not configured for this HaruQuantAI workspace')}>Subscribe</button>}</p>)}
            {(!subscription.eodSubscriptionActive || !subscription.minuteSubscriptionActive) && <p><span className="sq-data-active" aria-hidden="true">✓</span> Data available without subscription: {subscription.freeSymbols.join(', ')}</p>}
          </div></div>
          {(!subscription.eodSubscriptionActive || !subscription.minuteSubscriptionActive) && <button className="sq-data-banner" onClick={() => notify('Data subscriptions are not configured for this HaruQuantAI workspace')}><strong>HaruQuantAI Data Subscription</strong><span>End of Day and Intraday market data</span><span>Learn more</span></button>}
        </> : <>
          <div><Button className="primary" onClick={() => { cancelLookup(); setResults([]); setSelected([]); setLookedUp(false); setError(''); }}>&lt; Search again</Button></div>
          <div className="sq-data-result-help"><span>Choose from the found symbols below the ones that you want to add</span><span role="status">Found: {results.length}, selected: {selected.length}</span></div>
          <div className="sq-data-grid"><table className="plain-table" aria-label={`${providerLabel(provider)} search results`}><thead><tr><th><input type="checkbox" aria-label="Select all available tickers" disabled={!eligible.length} checked={allSelected} onChange={() => setSelected(allSelected ? [] : eligible.map(row => row.ticker))}/></th>{columns.map(column => <th key={column.key} aria-sort={sort.key === column.key ? sort.descending ? 'descending' : 'ascending' : 'none'}><button onClick={() => setSort({ key: column.key, descending: sort.key === column.key && !sort.descending })}>{column.label}{sort.key === column.key ? sort.descending ? ' ▾' : ' ▴' : ''}</button></th>)}</tr></thead><tbody>
            {rows.map(row => { const allowed = sqAllowed(row, profile); return <tr key={row.ticker} aria-disabled={!allowed} title={allowed ? undefined : 'Unavailable with the current mock subscription'} className={selected.includes(row.ticker) ? 'selected' : ''}><td><input type="checkbox" aria-label={`Select ticker ${row.ticker}`} disabled={!allowed} checked={selected.includes(row.ticker)} onChange={() => setSelected(current => current.includes(row.ticker) ? current.filter(ticker => ticker !== row.ticker) : [...current, row.ticker])}/></td>{columns.map(column => <td key={column.key}>{String(row[column.key])}</td>)}</tr>; })}
            {!rows.length && <tr><td colSpan={columns.length + 1}>No tickers found.</td></tr>}
          </tbody></table></div>
          <div className="sq-data-details"><fieldset><legend>Data details</legend><Field label="Name postfix"><TextInput value={config.postfix} maxLength={100} onChange={event => patch({ postfix: event.target.value })}/></Field></fieldset><fieldset><legend>Bar type</legend>{([['start', 'Timestamp is start of bar time (MetaTrader, Dukascopy, forex data)'], ['end', 'Timestamp is end of bar time (NinjaTrader, Tradestation, futures data)']] as const).map(([value, label]) => <label key={value}><input name="sq-bar-type" type="radio" checked={config.barType === value} onChange={() => patch({ barType: value })}/> {label}</label>)}</fieldset></div>
          <fieldset className="sq-data-timezone"><legend>Data timezone</legend><label><input type="radio" name="sq-timezone" checked={config.timezoneType === 2} onChange={() => patch({ timezoneType: 2 })}/> Exchange (default)</label><div><label><input type="radio" name="sq-timezone" checked={config.timezoneType === 0} onChange={() => patch({ timezoneType: 0 })}/> add fixed shift</label><TextInput aria-label="Fixed shift hours" type="number" min={-23} max={23} step={1} disabled={config.timezoneType !== 0} value={Number.isNaN(config.timezoneShift) ? '' : config.timezoneShift} onChange={event => patch({ timezoneShift: event.target.valueAsNumber })}/><span>hours</span></div><div><label><input type="radio" name="sq-timezone" checked={config.timezoneType === 1} onChange={() => patch({ timezoneType: 1 })}/> choose timezone</label><select aria-label="Data timezone" disabled={config.timezoneType !== 1} value={config.timezone} onChange={event => patch({ timezone: event.target.value })}>{timezones.map(([value, label]) => <option key={label} value={value}>{label}</option>)}</select></div></fieldset>
        </>}
      </fieldset>
    </>}
  </Modal></div>;
}
