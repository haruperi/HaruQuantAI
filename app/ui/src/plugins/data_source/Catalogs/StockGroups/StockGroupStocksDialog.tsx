import { useRef, useState } from 'react';
import { Button, Modal } from '../../../../components/ui';
import { formatStockLines, parseStockLines, serializeStockMembersJson, stockGroupLimits, type StockGroupDefinition } from './stockGroups';
import { useStockGroups } from './stockGroupsStore';
import './stockGroups.css';

function download(filename: string, text: string) { const url = URL.createObjectURL(new Blob([text], { type: 'application/json;charset=utf-8' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url); }

export function StockGroupStocksDialog({ group, onClose, onSaved }: { group: StockGroupDefinition; onClose: () => void; onSaved: (message: string) => void }) {
  const [text, setText] = useState(formatStockLines(group.members)); const [error, setError] = useState(''); const fileRef = useRef<HTMLInputElement>(null);
  const replace = (value: string, message: string) => { try { useStockGroups.getState().replaceMembers(group.id, parseStockLines(value)); onSaved(message); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save stocks.'); } };
  const choose = () => { if (group.system) { setError("Stocks can't be imported to this group."); return; } fileRef.current?.click(); };
  const read = async (file?: File) => { if (!file) return; try { if (!/\.csv$/i.test(file.name)) throw new Error('Choose a CSV file.'); if (file.size > stockGroupLimits.csv) throw new Error('Stock list exceeds the 2 MiB limit.'); replace(await file.text(), 'Stocks were imported'); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to import stocks.'); } };
  return <div className="stock-groups-flow"><Modal title={`Edit stocks ${group.name}`} width={700} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={() => replace(text, 'Stocks were saved.')}>Save</Button></>}>
    <p className="stock-group-help">Use the textarea below to define the individual stocks in this group, separated by lines. You can optionally also add dates of addition and removal from index as the newxt two columns.</p>
    <p className="stock-group-format"><strong>Format (date format is DD.MM.YYYY):</strong><br/>Ticker;Date from (optional); Date to(optional)<br/><strong>Example:</strong><br/>AAPL<br/>TSLA;01.12.2020<br/>AMZN;15.04.2007;30.05.2015</p>
    {error && <p className="stock-group-error" role="alert">{error}</p>}
    <div className="stock-group-file-actions"><Button onClick={choose}>Import from file</Button><Button onClick={() => { download('GroupStocks.json', serializeStockMembersJson(group.members)); onClose(); }}>Export to file</Button><input ref={fileRef} hidden type="file" accept=".csv,text/csv" aria-label="Choose stocks CSV" onChange={event => void read(event.target.files?.[0])}/></div>
    <textarea className="text-input stock-group-members" aria-label="Stocks" value={text} onChange={event => setText(event.target.value)}/>
  </Modal></div>;
}
