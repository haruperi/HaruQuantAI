import { useResultsTradelist } from './ResultsTradelistCtrl';
import { TradelistViews, useTradelistViews, optionalColumns } from '../ResultsTradelistViews/module';
import { ResultsToolbar } from '../ProjectWorkbench/results/ResultsChrome';
import { ExportTradesModal } from '../ProjectWorkbench/results/ResultsModals';
import { csvTrades, downloadText, type ResultDocument } from '../ProjectWorkbench/results/resultsModel';
export function TradeListTab({ result }: {
    result: ResultDocument | null;
}) {
    const { direction, setDirection, sampleType, setSampleType, dataKey, setDataKey, expired, setExpired, ascending, setAscending, sort, setSort, exportOpen, setExportOpen, trades } = useResultsTradelist(result);
    const viewState = useTradelistViews();
    const { views, view, setView, setColumns, setManage, visible } = viewState;
    return <div className="sqr-tab">
    <div className="sqr-toolbar-row"><ResultsToolbar dataKey={dataKey} dataItems={result?.markets} onDataChange={setDataKey} direction={direction} sampleType={sampleType} onDirectionChange={setDirection} onSampleTypeChange={setSampleType} extendedSample>
      <label>View <select aria-label="View" value={view} onChange={e => setView(e.target.value)}>{Object.keys(views).map(v => <option key={v}>{v}</option>)}</select></label>
      <button className="sqd-btn" onClick={() => { setColumns(views[view]); setManage(true); }}>Manage views</button>
      <button className="sqd-btn" disabled={!result} onClick={() => setExportOpen(true)}>Export</button>
      <label><input type="checkbox" checked={expired} onChange={e => setExpired(e.target.checked)}/> Include expired</label>
    </ResultsToolbar></div>
    <div className="sqr-content sqr-grid-content">{result ? <table className="sqr-data-table"><thead><tr><th><button onClick={() => { setSort('id'); setAscending(!ascending); }}>ID</button></th><th>Market</th><th>Direction</th>{optionalColumns.filter(c => visible.includes(c)).map(c => <th key={c}>{c}</th>)}<th><button onClick={() => { setSort('profit'); setAscending(!ascending); }}>Profit {sort === 'profit' ? (ascending ? '↑' : '↓') : ''}</button></th></tr></thead><tbody>{trades.map(t => <tr key={t.id}><td>{t.id}</td><td>{t.market}</td><td>{t.direction}</td>{visible.includes('Open time') && <td>{t.open}</td>}{visible.includes('Close time') && <td>{t.close}</td>}{visible.includes('Open price') && <td>{t.price.toFixed(5)}</td>}{visible.includes('Close price') && <td>{t.exit.toFixed(5)}</td>}<td className={t.profit < 0 ? 'negative' : 'positive'}>{t.profit.toFixed(2)}</td></tr>)}</tbody></table> : <p>No strategy selected.</p>}{result && trades.length === 0 && <p>No trades match these filters.</p>}</div>
    <TradelistViews state={viewState}/>
    {exportOpen && <ExportTradesModal onClose={() => setExportOpen(false)} onExport={comma => { downloadText('trades.csv', csvTrades(trades, comma), 'text/csv'); setExportOpen(false); }}/>}
  </div>;
}
