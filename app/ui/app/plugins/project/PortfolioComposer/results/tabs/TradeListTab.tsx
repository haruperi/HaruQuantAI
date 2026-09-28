import { useState } from 'react';
import { ResultsToolbar } from '../ResultsChrome';
import { SqdModal } from '../../ProjectModal';
import { ExportTradesModal } from '../ResultsModals';
import { visibleTrades, csvTrades, downloadText, type ResultDocument } from '../resultsModel';
import type { Direction, SampleType } from '../resultsFixtures';
const optionalColumns = ['Open time', 'Close time', 'Open price', 'Close price'] as const;
export function TradeListTab({ result }: {
    result: ResultDocument | null;
}) {
    const [direction, setDirection] = useState<Direction>('both');
    const [sampleType, setSampleType] = useState<SampleType>('full');
    const [dataKey, setDataKey] = useState('Main backtest');
    const [expired, setExpired] = useState(false);
    const [ascending, setAscending] = useState(true);
    const [sort, setSort] = useState<'id' | 'profit'>('id');
    const [views, setViews] = useState<Record<string, string[]>>({ Default: [...optionalColumns] });
    const [view, setView] = useState('Default');
    const [name, setName] = useState('');
    const [columns, setColumns] = useState<string[]>([...optionalColumns]);
    const [manage, setManage] = useState(false);
    const [exportOpen, setExportOpen] = useState(false);
    const trades = result ? visibleTrades(result, direction, sampleType, dataKey, expired).sort((a, b) => (ascending ? 1 : -1) * (a[sort] - b[sort])) : [];
    const visible = views[view];
    const save = () => { const key = name.trim(); setViews(v => ({ ...v, [key]: columns })); setView(key); setName(''); };
    return <div className="sqr-tab">
    <div className="sqr-toolbar-row"><ResultsToolbar dataKey={dataKey} dataItems={result?.markets} onDataChange={setDataKey} direction={direction} sampleType={sampleType} onDirectionChange={setDirection} onSampleTypeChange={setSampleType} extendedSample>
      <label>View <select aria-label="View" value={view} onChange={e => setView(e.target.value)}>{Object.keys(views).map(v => <option key={v}>{v}</option>)}</select></label>
      <button className="sqd-btn" onClick={() => { setColumns(views[view]); setManage(true); }}>Manage views</button>
      <button className="sqd-btn" disabled={!result} onClick={() => setExportOpen(true)}>Export</button>
      <label><input type="checkbox" checked={expired} onChange={e => setExpired(e.target.checked)}/> Include expired</label>
    </ResultsToolbar></div>
    <div className="sqr-content sqr-grid-content">{result ? <table className="sqr-data-table"><thead><tr><th><button onClick={() => { setSort('id'); setAscending(!ascending); }}>ID</button></th><th>Market</th><th>Direction</th>{optionalColumns.filter(c => visible.includes(c)).map(c => <th key={c}>{c}</th>)}<th><button onClick={() => { setSort('profit'); setAscending(!ascending); }}>Profit {sort === 'profit' ? (ascending ? '↑' : '↓') : ''}</button></th></tr></thead><tbody>{trades.map(t => <tr key={t.id}><td>{t.id}</td><td>{t.market}</td><td>{t.direction}</td>{visible.includes('Open time') && <td>{t.open}</td>}{visible.includes('Close time') && <td>{t.close}</td>}{visible.includes('Open price') && <td>{t.price.toFixed(5)}</td>}{visible.includes('Close price') && <td>{t.exit.toFixed(5)}</td>}<td className={t.profit < 0 ? 'negative' : 'positive'}>{t.profit.toFixed(2)}</td></tr>)}</tbody></table> : <p>No strategy selected.</p>}{result && trades.length === 0 && <p>No trades match these filters.</p>}</div>
    {manage && <SqdModal title="Manage views" onClose={() => setManage(false)} width={560}><label>Select view to edit <select aria-label="Edit view" value={view} onChange={e => { setView(e.target.value); setColumns(views[e.target.value]); }}>{Object.keys(views).map(v => <option key={v}>{v}</option>)}</select></label><p>Columns</p>{optionalColumns.map(c => <label key={c} className="sqr-export-option"><input type="checkbox" checked={columns.includes(c)} onChange={e => setColumns(old => e.target.checked ? [...old, c] : old.filter(v => v !== c))}/>{c}</label>)}<label>View name <input aria-label="View name" value={name} onChange={e => setName(e.target.value)}/></label><div className="sqr-modal-links"><button className="sqd-btn" onClick={() => setViews(v => ({ ...v, [view]: columns }))}>Save changes</button><button className="sqd-btn" disabled={!name.trim() || Object.keys(views).some(v => v.toLowerCase() === name.trim().toLowerCase())} onClick={save}>Save view</button><button className="sqd-btn" disabled={view === 'Default' || !name.trim() || !!views[name.trim()]} onClick={() => { const next = { ...views }; delete next[view]; next[name.trim()] = columns; setViews(next); setView(name.trim()); setName(''); }}>Rename view</button><button className="sqd-btn" disabled={view === 'Default'} onClick={() => { const next = { ...views }; delete next[view]; setViews(next); setView('Default'); setColumns(next.Default); }}>Delete view</button></div></SqdModal>}
    {exportOpen && <ExportTradesModal onClose={() => setExportOpen(false)} onExport={comma => { downloadText('trades.csv', csvTrades(trades, comma), 'text/csv'); setExportOpen(false); }}/>}
  </div>;
}
